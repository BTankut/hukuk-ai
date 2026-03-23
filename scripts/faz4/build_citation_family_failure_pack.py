#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "api-gateway" / "src"))

from faz2a_hardening import (  # noqa: E402
    canonicalize_source_id,
    extract_law_code_from_source_id,
    resolve_target_date,
)

INLINE_CITATION_RE = re.compile(r"\[Kaynak:\s*([^\]]+)\]")
LIST_ITEM_RE = re.compile(r"^\s*[-*]\s+")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.;?!])\s+")
DEFAULT_TODAY = date(2026, 3, 23)
FAILURE_CLASSES = {
    "citation_under_emission",
    "wrong_primary_source_with_supported_answer",
    "residual_false_refusal",
    "residual_unsupported_answer",
}


@dataclass(frozen=True)
class EvalRow:
    family: str
    question_id: str
    payload: dict[str, Any]


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_sources(values: list[str] | None) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        source_id = canonicalize_source_id(value)
        if not source_id or source_id in seen:
            continue
        normalized.append(source_id)
        seen.add(source_id)
    return normalized


def report_family(report: dict[str, Any], path: Path) -> str:
    report_meta = report.get("report_meta") or {}
    return str(report_meta.get("eval_family") or path.stem)


def load_eval_rows(paths: list[Path]) -> dict[str, dict[str, EvalRow]]:
    reports: dict[str, dict[str, EvalRow]] = {}
    for path in paths:
        report = json.loads(path.read_text(encoding="utf-8"))
        family = report_family(report, path)
        rows: dict[str, EvalRow] = {}
        for item in report.get("per_question", []):
            rows[item["question_id"]] = EvalRow(family=family, question_id=item["question_id"], payload=item)
        reports[family] = rows
    return reports


def load_question_maps(paths: list[Path]) -> dict[str, dict[str, dict[str, Any]]]:
    output: dict[str, dict[str, dict[str, Any]]] = {}
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        questions = payload["questions"] if isinstance(payload, dict) else payload
        family = path.stem.replace("test_questions_", "").replace("test_questions", "faz1-50")
        if family == "v2_95":
            family = "v2-95"
        if family == "v3_170":
            family = "v3-170"
        output[family] = {item["id"]: item for item in questions}
    return output


def split_claim_units(answer_text: str) -> list[str]:
    raw = str(answer_text or "")
    if not raw.strip():
        return []

    lines = [line.rstrip() for line in raw.splitlines()]
    list_items: list[str] = []
    for line in lines:
        if not line.strip():
            continue
        if LIST_ITEM_RE.match(line):
            item = LIST_ITEM_RE.sub("", line, count=1)
            normalized = normalize_whitespace(item)
            if normalized and not normalized.endswith(":"):
                list_items.append(normalized)
    if list_items:
        return list_items

    flattened = " ".join(line.strip() for line in lines if line.strip())
    parts = [
        normalize_whitespace(part)
        for part in SENTENCE_SPLIT_RE.split(flattened)
        if normalize_whitespace(part)
    ]
    merged_parts: list[str] = []
    for part in parts:
        if part.startswith("[Kaynak:") and merged_parts:
            merged_parts[-1] = normalize_whitespace(f"{merged_parts[-1]} {part}")
            continue
        merged_parts.append(part)
    return [part for part in merged_parts if not part.endswith(":")]


def strip_inline_citations(text: str) -> str:
    return normalize_whitespace(INLINE_CITATION_RE.sub("", text or ""))


def extract_inline_citations(text: str) -> list[str]:
    citations: list[str] = []
    seen: set[str] = set()
    for raw in INLINE_CITATION_RE.findall(text or ""):
        source_id = canonicalize_source_id(raw)
        if not source_id or source_id in seen:
            continue
        citations.append(source_id)
        seen.add(source_id)
    return citations


def _parse_optional_date(value: Any) -> date | None:
    if value in {None, ""}:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _passes_temporal_surface(evidence: dict[str, Any], *, target_date: date) -> bool:
    start = _parse_optional_date(evidence.get("yururluk_baslangic"))
    end = _parse_optional_date(evidence.get("yururluk_bitis"))
    mulga = evidence.get("mulga")
    if mulga is True:
        return False
    if start and target_date < start:
        return False
    if end and target_date > end:
        return False
    return True


def _passes_law_scope_surface(source_id: str, *, law_scope_signal: dict[str, Any]) -> bool:
    scope_class = (law_scope_signal or {}).get("scope_class")
    expected = (law_scope_signal or {}).get("expected_law_scope") or []
    if scope_class != "single_law_high_conf" or not expected:
        return True
    return extract_law_code_from_source_id(source_id) == expected[0]


def _build_supported_projection(
    *,
    answer_text: str,
    question_raw: str,
    assembled_evidence: list[dict[str, Any]],
    allowed_source_whitelist: list[str],
    law_scope_signal: dict[str, Any],
) -> dict[str, Any]:
    whitelist = {
        canonicalize_source_id(source_id)
        for source_id in allowed_source_whitelist
        if canonicalize_source_id(source_id)
    }
    target_date, _ = resolve_target_date(question_raw, today=DEFAULT_TODAY)
    evidence_by_source: dict[str, dict[str, Any]] = {}
    retrieval_rank_by_source: dict[str, int] = {}
    for index, evidence in enumerate(assembled_evidence):
        source_id = canonicalize_source_id(evidence.get("source_id") or evidence.get("citation"))
        if not source_id:
            continue
        evidence_by_source[source_id] = evidence
        retrieval_rank_by_source.setdefault(source_id, index)

    kept_claim_units: list[dict[str, Any]] = []
    dropped_claim_units: list[dict[str, Any]] = []
    supported_source_ids: list[str] = []
    supported_claim_count: Counter[str] = Counter()

    for unit_text in split_claim_units(answer_text):
        raw_citations = extract_inline_citations(unit_text)
        supported_for_unit: list[str] = []
        for source_id in raw_citations:
            if source_id not in whitelist:
                continue
            evidence = evidence_by_source.get(source_id)
            if evidence is None:
                continue
            if not _passes_temporal_surface(evidence, target_date=target_date):
                continue
            if not _passes_law_scope_surface(source_id, law_scope_signal=law_scope_signal):
                continue
            if source_id not in supported_for_unit:
                supported_for_unit.append(source_id)

        claim_text = strip_inline_citations(unit_text)
        if supported_for_unit:
            kept_claim_units.append(
                {
                    "claim_text": claim_text,
                    "supported_source_ids": supported_for_unit,
                }
            )
            for source_id in supported_for_unit:
                if source_id not in supported_source_ids:
                    supported_source_ids.append(source_id)
                supported_claim_count[source_id] += 1
        else:
            dropped_claim_units.append(
                {
                    "claim_text": claim_text,
                    "raw_citation_source_ids": raw_citations,
                }
            )

    return {
        "kept_claim_units": kept_claim_units,
        "dropped_claim_units": dropped_claim_units,
        "supported_source_ids": supported_source_ids,
        "supported_claim_count": dict(supported_claim_count),
        "retrieval_rank_by_source": retrieval_rank_by_source,
    }


def expected_primary_source_id(question: dict[str, Any], rc_a_row: dict[str, Any]) -> str | None:
    expected_sources = normalize_sources(question.get("expected_sources"))
    if expected_sources:
        return expected_sources[0]
    contract = rc_a_row.get("answer_contract") or {}
    primary = canonicalize_source_id(contract.get("primary_source_id"))
    if primary:
        return primary
    cited_sources = normalize_sources(rc_a_row.get("cited_sources"))
    if cited_sources:
        return cited_sources[0]
    return None


def quality_loss_reasons(*, expected_mode: str, rc_row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if expected_mode == "answer":
        if not bool(rc_row.get("has_citation")):
            reasons.append("citation_miss")
        if float(rc_row.get("correct_source_rate") or 0.0) < 1.0:
            reasons.append("correct_source_miss")
    if bool(rc_row.get("refusal_correct")) is False:
        reasons.append("refusal_miss")
    return reasons


def classify_failure(
    *,
    expected_mode: str,
    expected_primary_source_id: str | None,
    rc_final_mode: str | None,
    rc_primary_source_id: str | None,
    supported_source_ids: list[str],
) -> str:
    if expected_mode == "answer" and rc_final_mode == "refusal":
        return "residual_false_refusal"
    if expected_mode == "refusal" and rc_final_mode in {"answer", "partial"}:
        return "residual_unsupported_answer"
    if rc_final_mode in {"answer", "partial"} and not supported_source_ids:
        return "residual_unsupported_answer"
    if (
        rc_final_mode in {"answer", "partial"}
        and expected_primary_source_id
        and rc_primary_source_id != expected_primary_source_id
    ):
        return "wrong_primary_source_with_supported_answer"
    return "citation_under_emission"


def build_failure_pack(
    *,
    question_maps: dict[str, dict[str, dict[str, Any]]],
    rc_a_reports: dict[str, dict[str, EvalRow]],
    rc_d_reports: dict[str, dict[str, EvalRow]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_family = Counter()
    by_class = Counter()

    for family, question_map in question_maps.items():
        for question_id, question in question_map.items():
            rc_a_row = rc_a_reports[family][question_id].payload
            rc_d_row = rc_d_reports[family][question_id].payload
            expected_mode = "refusal" if question.get("refusal_expected") else "answer"
            reasons = quality_loss_reasons(expected_mode=expected_mode, rc_row=rc_d_row)
            if not reasons:
                continue

            trace = rc_d_row.get("trace") or {}
            analysis_answer_text = (
                rc_d_row.get("answer_text")
                if rc_d_row.get("final_mode") in {"answer", "partial"}
                else rc_a_row.get("answer_text")
            )
            projection = _build_supported_projection(
                answer_text=str(analysis_answer_text or ""),
                question_raw=str(trace.get("question_raw") or rc_d_row.get("question_text") or question.get("question") or ""),
                assembled_evidence=list(
                    trace.get("assembled_evidence")
                    or ((trace.get("context_assembly") or {}).get("assembled_evidence"))
                    or []
                ),
                allowed_source_whitelist=list(
                    trace.get("allowed_source_whitelist")
                    or ((trace.get("context_assembly") or {}).get("allowed_source_whitelist"))
                    or []
                ),
                law_scope_signal=trace.get("law_scope_signal") or {},
            )
            expected_sources = normalize_sources(question.get("expected_sources"))
            expected_primary = expected_primary_source_id(question, rc_a_row)
            rc_primary = canonicalize_source_id(
                ((rc_d_row.get("answer_contract") or {}).get("primary_source_id"))
                or (rc_d_row.get("cited_sources") or [None])[0]
            )
            rc_emitted = normalize_sources(rc_d_row.get("cited_sources"))
            failure_class = classify_failure(
                expected_mode=expected_mode,
                expected_primary_source_id=expected_primary,
                rc_final_mode=rc_d_row.get("final_mode"),
                rc_primary_source_id=rc_primary,
                supported_source_ids=projection["supported_source_ids"],
            )
            if failure_class not in FAILURE_CLASSES:
                raise RuntimeError(f"Unexpected failure class {failure_class}")

            row = {
                "question_id": question_id,
                "family": family,
                "expected_mode": expected_mode,
                "expected_primary_source_id": expected_primary,
                "expected_citation_source_ids": expected_sources,
                "rc_d_final_mode": rc_d_row.get("final_mode"),
                "rc_d_primary_source_id": rc_primary,
                "rc_d_emitted_source_ids": rc_emitted,
                "rc_d_supported_source_ids": projection["supported_source_ids"],
                "rc_d_kept_claim_units": projection["kept_claim_units"],
                "rc_d_dropped_claim_units": projection["dropped_claim_units"],
                "failure_class": failure_class,
                "quality_loss_reasons": reasons,
            }
            rows.append(row)
            by_family[family] += 1
            by_class[failure_class] += 1

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_records": len(rows),
        "by_family": dict(sorted(by_family.items())),
        "by_class": dict(sorted(by_class.items())),
    }
    return rows, summary


def render_markdown(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# FAZ 4 Citation Family Failure Pack",
        "",
        f"- generated_at: `{summary['generated_at']}`",
        f"- total_records: `{summary['total_records']}`",
        "",
        "## By Family",
        "",
    ]
    for family, count in summary["by_family"].items():
        lines.append(f"- `{family}`: `{count}`")
    lines.extend(["", "## By Class", ""])
    for failure_class, count in summary["by_class"].items():
        lines.append(f"- `{failure_class}`: `{count}`")
    lines.extend(
        [
            "",
            "## Sample Rows",
            "",
            "| family | question_id | rc_d_mode | expected_primary | rc_d_primary | class | reasons |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows[:30]:
        lines.append(
            f"| {row['family']} | {row['question_id']} | {row['rc_d_final_mode']} | {row['expected_primary_source_id']} | {row['rc_d_primary_source_id']} | {row['failure_class']} | {', '.join(row['quality_loss_reasons'])} |"
        )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build FAZ4 RC-D family quality loss pack.")
    parser.add_argument("--faz1-questions", type=Path, required=True)
    parser.add_argument("--v2-questions", type=Path, required=True)
    parser.add_argument("--v3-questions", type=Path, required=True)
    parser.add_argument("--faz1-rc-a", type=Path, required=True)
    parser.add_argument("--v2-rc-a", type=Path, required=True)
    parser.add_argument("--v3-rc-a", type=Path, required=True)
    parser.add_argument("--faz1-rc-d", type=Path, required=True)
    parser.add_argument("--v2-rc-d", type=Path, required=True)
    parser.add_argument("--v3-rc-d", type=Path, required=True)
    parser.add_argument("--output-jsonl", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    question_maps = load_question_maps([args.faz1_questions, args.v2_questions, args.v3_questions])
    rc_a_reports = load_eval_rows([args.faz1_rc_a, args.v2_rc_a, args.v3_rc_a])
    rc_d_reports = load_eval_rows([args.faz1_rc_d, args.v2_rc_d, args.v3_rc_d])
    rows, summary = build_failure_pack(
        question_maps=question_maps,
        rc_a_reports=rc_a_reports,
        rc_d_reports=rc_d_reports,
    )

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    with args.output_jsonl.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    args.output_md.write_text(render_markdown(summary, rows), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
