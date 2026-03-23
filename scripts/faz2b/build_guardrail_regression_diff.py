#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "api-gateway" / "src"))

from evaluation.metrics import detect_refusal  # noqa: E402
from faz2a_hardening import canonicalize_source_id  # noqa: E402

REGRESSION_CLASSES = {
    "schema_block",
    "whitelist_block",
    "temporal_block",
    "law_scope_block",
    "claim_binding_block",
    "citation_canonicalization_miss",
    "scope_parser_false_positive",
    "question_type_false_positive",
    "excerpt_match_false_negative",
    "false_refusal_after_guardrail",
    "true_guardrail_block",
}
NARROW_TYPES = {"single_article", "definition", "elements", "procedure"}


@dataclass(slots=True)
class QuestionRow:
    family: str
    question_id: str
    payload: dict[str, Any]


def _report_family(report: dict[str, Any], path: Path) -> str:
    meta = report.get("report_meta", {})
    return str(meta.get("eval_family") or path.stem)


def _load_rows(path: Path) -> dict[str, QuestionRow]:
    report = json.loads(path.read_text(encoding="utf-8"))
    family = _report_family(report, path)
    rows: dict[str, QuestionRow] = {}
    for item in report.get("per_question", []):
        rows[item["question_id"]] = QuestionRow(family=family, question_id=item["question_id"], payload=item)
    return rows


def _normalize_sources(values: list[str] | None) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        source_id = canonicalize_source_id(value)
        if not source_id or source_id in seen:
            continue
        normalized.append(source_id)
        seen.add(source_id)
    return normalized


def _first_source(values: list[str] | None) -> str | None:
    normalized = _normalize_sources(values)
    return normalized[0] if normalized else None


def _expected_mode(row: dict[str, Any]) -> str:
    return "refusal" if row.get("refusal_expected") else "answer"


def _infer_rc_a_final_mode(row: dict[str, Any]) -> str:
    if detect_refusal(str(row.get("answer_text") or "")):
        return "refusal"
    return "answer"


def _has_quality_drop(rc_a: dict[str, Any], rc_b: dict[str, Any]) -> bool:
    if _expected_mode(rc_a) == "refusal" and bool(rc_b.get("refusal_correct")):
        return False
    if float(rc_b.get("correct_source_rate", 0.0)) < float(rc_a.get("correct_source_rate", 0.0)):
        return True
    if int(bool(rc_b.get("cited_sources"))) < int(bool(rc_a.get("cited_sources"))):
        return True
    if int(bool(rc_b.get("refusal_correct"))) < int(bool(rc_a.get("refusal_correct"))):
        return True
    if int(bool(rc_b.get("is_hallucination"))) > int(bool(rc_a.get("is_hallucination"))):
        return True
    if _infer_rc_a_final_mode(rc_a) == "answer" and (rc_b.get("final_mode") in {"refusal", "blocked", "partial"}):
        return True
    return False


def _classify_regression(rc_a: dict[str, Any], rc_b: dict[str, Any]) -> str:
    final_reason = rc_b.get("final_reason")
    final_mode = rc_b.get("final_mode")
    expected_mode = _expected_mode(rc_a)
    question_type = str(((rc_b.get("trace") or {}).get("question_type")) or "")
    parsed_scope = (rc_b.get("trace") or {}).get("law_scope_signal") or {}
    assembled = _normalize_sources(((rc_b.get("trace") or {}).get("allowed_source_whitelist")) or [])
    expected_sources = _normalize_sources(rc_a.get("expected_sources"))

    if final_reason == "schema_validation_failed":
        return "schema_block"
    if final_reason == "citation_out_of_whitelist":
        return "whitelist_block"
    if final_reason in {"temporal_mismatch", "source_validity_unknown"}:
        return "temporal_block"
    if final_reason == "law_scope_mismatch":
        if expected_mode == "answer" and _infer_rc_a_final_mode(rc_a) == "answer":
            return "scope_parser_false_positive"
        return "law_scope_block"
    if final_reason == "claim_support_missing":
        if question_type not in NARROW_TYPES:
            return "question_type_false_positive"
        if expected_sources and any(source in assembled for source in expected_sources):
            return "excerpt_match_false_negative"
        return "claim_binding_block"
    if final_reason == "insufficient_supported_evidence":
        if expected_mode == "answer":
            if parsed_scope.get("scope_ambiguous") is False and parsed_scope.get("expected_law_scope"):
                return "scope_parser_false_positive"
            return "false_refusal_after_guardrail"
        return "true_guardrail_block"

    rc_a_citation = bool(rc_a.get("cited_sources"))
    rc_b_citation = bool(rc_b.get("cited_sources"))
    if final_mode in {"refusal", "blocked", "partial"} and expected_mode == "answer":
        return "false_refusal_after_guardrail"
    if rc_a_citation and not rc_b_citation:
        return "citation_canonicalization_miss"
    return "true_guardrail_block"


def build_diff(rc_a_paths: list[Path], rc_b_paths: list[Path]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rc_a_reports: dict[str, dict[str, QuestionRow]] = {}
    rc_b_reports: dict[str, dict[str, QuestionRow]] = {}
    for path in rc_a_paths:
        rows = _load_rows(path)
        family = next(iter(rows.values())).family if rows else path.stem
        rc_a_reports[family] = rows
    for path in rc_b_paths:
        rows = _load_rows(path)
        family = next(iter(rows.values())).family if rows else path.stem
        rc_b_reports[family] = rows

    diff_rows: list[dict[str, Any]] = []
    by_family = Counter()
    by_class = Counter()

    for family, rc_a_rows in rc_a_reports.items():
        rc_b_rows = rc_b_reports[family]
        for question_id, rc_a_row in rc_a_rows.items():
            rc_b_row = rc_b_rows.get(question_id)
            if rc_b_row is None:
                continue
            rc_a = rc_a_row.payload
            rc_b = rc_b_row.payload
            if not _has_quality_drop(rc_a, rc_b):
                continue

            regression_class = _classify_regression(rc_a, rc_b)
            if regression_class not in REGRESSION_CLASSES:
                raise RuntimeError(f"Unexpected regression class: {regression_class}")

            trace = rc_b.get("trace") or {}
            answer_contract = rc_b.get("answer_contract") or {}
            diff_rows.append(
                {
                    "question_id": question_id,
                    "family": family,
                    "expected_source_id": _first_source(rc_a.get("expected_sources")),
                    "expected_mode": _expected_mode(rc_a),
                    "rc_a_final_mode": _infer_rc_a_final_mode(rc_a),
                    "rc_a_primary_source_id": _first_source(rc_a.get("cited_sources")),
                    "rc_b_final_mode": rc_b.get("final_mode"),
                    "rc_b_final_reason": rc_b.get("final_reason"),
                    "parsed_law_scope": (trace.get("law_scope_signal") or {}).get("expected_law_scope") or [],
                    "question_type": trace.get("question_type"),
                    "gate_triggered": rc_b.get("final_reason") or rc_b.get("final_mode"),
                    "regression_class": regression_class,
                    "rc_a_correct_source_rate": rc_a.get("correct_source_rate"),
                    "rc_b_correct_source_rate": rc_b.get("correct_source_rate"),
                    "rc_a_refusal_correct": rc_a.get("refusal_correct"),
                    "rc_b_refusal_correct": rc_b.get("refusal_correct"),
                    "rc_b_primary_source_id": answer_contract.get("primary_source_id"),
                }
            )
            by_family[family] += 1
            by_class[regression_class] += 1

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_regressions": len(diff_rows),
        "by_family": dict(sorted(by_family.items())),
        "by_class": dict(sorted(by_class.items())),
        "false_refusal_after_guardrail": by_class.get("false_refusal_after_guardrail", 0),
    }
    return diff_rows, summary


def render_markdown(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# FAZ 2B Guardrail Regression Diff",
        "",
        f"- generated_at: `{summary['generated_at']}`",
        f"- total_regressions: `{summary['total_regressions']}`",
        f"- false_refusal_after_guardrail: `{summary['false_refusal_after_guardrail']}`",
        "",
        "## By Family",
        "",
    ]
    if summary["by_family"]:
        for family, count in summary["by_family"].items():
            lines.append(f"- `{family}`: `{count}`")
    else:
        lines.append("- none")

    lines.extend(["", "## By Class", ""])
    if summary["by_class"]:
        for klass, count in summary["by_class"].items():
            lines.append(f"- `{klass}`: `{count}`")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Sample Rows",
            "",
            "| family | question_id | rc_a_mode | rc_b_mode | gate | regression_class |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows[:25]:
        lines.append(
            "| {family} | {question_id} | {rc_a_final_mode} | {rc_b_final_mode} | {gate_triggered} | {regression_class} |".format(
                **row
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build RC-A vs RC-B guardrail regression diff.")
    parser.add_argument("--rc-a-report", action="append", required=True, type=Path)
    parser.add_argument("--rc-b-report", action="append", required=True, type=Path)
    parser.add_argument("--output-jsonl", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    args = parser.parse_args()

    rows, summary = build_diff(args.rc_a_report, args.rc_b_report)
    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with args.output_jsonl.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(summary, rows), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
