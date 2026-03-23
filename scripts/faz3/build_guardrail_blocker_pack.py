#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "api-gateway" / "src"))

from faz2a_hardening import canonicalize_source_id  # noqa: E402

BLOCKER_CLASSES = {"false_refusal_after_guardrail", "true_guardrail_block"}
INLINE_CITATION_RE = re.compile(r"\[Kaynak:\s*([^\]]+)\]")
LIST_ITEM_RE = re.compile(r"^\s*[-*]\s+")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.;?!])\s+")


@dataclass(frozen=True)
class EvalRow:
    family: str
    question_id: str
    payload: dict[str, Any]


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


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


def load_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


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


def normalize_claim_text(text: str) -> str:
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


def _is_heading_line(text: str) -> bool:
    normalized = normalize_whitespace(text)
    return normalized.endswith(":") and "[Kaynak:" not in normalized


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
            if normalized and not _is_heading_line(normalized):
                list_items.append(normalized)
    if list_items:
        return list_items

    flattened = " ".join(line.strip() for line in lines if line.strip())
    parts = [
        normalize_whitespace(part)
        for part in SENTENCE_SPLIT_RE.split(flattened)
        if normalize_whitespace(part)
    ]
    return [part for part in parts if not _is_heading_line(part)]


def build_claim_units(answer_text: str) -> list[dict[str, Any]]:
    return [
        {
            "claim_text": normalize_claim_text(unit),
            "normalized_citation_source_ids": extract_inline_citations(unit),
        }
        for unit in split_claim_units(answer_text)
        if normalize_claim_text(unit)
    ]


def build_kept_claim_units(answer_contract: dict[str, Any]) -> list[dict[str, Any]]:
    kept_units: list[dict[str, Any]] = []
    for item in answer_contract.get("claim_units") or []:
        if not isinstance(item, dict):
            continue
        claim_text = normalize_whitespace(str(item.get("claim_text") or ""))
        if not claim_text:
            continue
        kept_units.append(
            {
                "claim_text": claim_text,
                "source_id": canonicalize_source_id(item.get("source_id")),
                "source_excerpt": normalize_whitespace(str(item.get("source_excerpt") or "")),
            }
        )
    return kept_units


def build_blocker_pack(
    *,
    diff_rows: list[dict[str, Any]],
    rc_a_reports: dict[str, dict[str, EvalRow]],
    rc_c_reports: dict[str, dict[str, EvalRow]],
    expected_total: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_family = Counter()
    by_class = Counter()

    for diff in diff_rows:
        blocker_class = diff.get("regression_class")
        if blocker_class not in BLOCKER_CLASSES:
            continue

        family = diff["family"]
        question_id = diff["question_id"]
        rc_a_row = rc_a_reports[family][question_id].payload
        rc_c_row = rc_c_reports[family][question_id].payload
        answer_contract = (rc_c_row.get("trace") or {}).get("answer_contract") or rc_c_row.get("answer_contract") or {}
        answer_text = str(answer_contract.get("answer_text") or rc_c_row.get("answer_text") or "")

        claim_units = build_claim_units(answer_text)
        kept_claim_units = build_kept_claim_units(answer_contract)
        kept_lookup = {normalize_claim_text(item["claim_text"]) for item in kept_claim_units}
        dropped_claim_units = [
            item
            for item in claim_units
            if normalize_claim_text(item["claim_text"]) not in kept_lookup
        ]

        row = {
            "question_id": question_id,
            "family": family,
            "expected_mode": diff.get("expected_mode"),
            "expected_source_id": diff.get("expected_source_id"),
            "rc_a_final_mode": diff.get("rc_a_final_mode"),
            "rc_a_primary_source_id": diff.get("rc_a_primary_source_id"),
            "rc_c_final_mode": rc_c_row.get("final_mode"),
            "rc_c_final_reason": rc_c_row.get("final_reason") or ((rc_c_row.get("trace") or {}).get("final_reason")),
            "primary_source_id": canonicalize_source_id(answer_contract.get("primary_source_id")),
            "secondary_source_ids": normalize_sources(answer_contract.get("secondary_source_ids")),
            "normalized_citation_source_ids": normalize_sources(rc_c_row.get("cited_sources")),
            "claim_units": claim_units,
            "kept_claim_units": kept_claim_units,
            "dropped_claim_units": dropped_claim_units,
            "blocker_class": blocker_class,
            "question_text": rc_c_row.get("question_text"),
            "rc_a_answer_text": rc_a_row.get("answer_text"),
            "rc_c_answer_text": rc_c_row.get("answer_text"),
        }
        rows.append(row)
        by_family[family] += 1
        by_class[blocker_class] += 1

    if len(rows) != expected_total:
        raise RuntimeError(f"Expected {expected_total} blocker rows, found {len(rows)}")

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_records": len(rows),
        "by_family": dict(sorted(by_family.items())),
        "by_class": dict(sorted(by_class.items())),
    }
    return rows, summary


def render_markdown(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# FAZ 3 Guardrail Blocker Pack",
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
    for blocker_class, count in summary["by_class"].items():
        lines.append(f"- `{blocker_class}`: `{count}`")
    lines.extend(
        [
            "",
            "## Sample Rows",
            "",
            "| family | question_id | blocker_class | rc_c_mode | rc_c_reason | kept | dropped |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows[:25]:
        lines.append(
            "| {family} | {question_id} | {blocker_class} | {rc_c_final_mode} | {rc_c_final_reason} | {kept} | {dropped} |".format(
                family=row["family"],
                question_id=row["question_id"],
                blocker_class=row["blocker_class"],
                rc_c_final_mode=row["rc_c_final_mode"],
                rc_c_final_reason=row["rc_c_final_reason"],
                kept=len(row["kept_claim_units"]),
                dropped=len(row["dropped_claim_units"]),
            )
        )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build FAZ 3 blocker pack from RC-C regression diff and raw eval reports.")
    parser.add_argument("--regression-diff-jsonl", required=True, type=Path)
    parser.add_argument("--rc-a-report", action="append", required=True, type=Path)
    parser.add_argument("--rc-c-report", action="append", required=True, type=Path)
    parser.add_argument("--expected-total", type=int, default=77)
    parser.add_argument("--output-jsonl", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    diff_rows = load_jsonl_rows(args.regression_diff_jsonl)
    rc_a_reports = load_eval_rows(args.rc_a_report)
    rc_c_reports = load_eval_rows(args.rc_c_report)
    rows, summary = build_blocker_pack(
        diff_rows=diff_rows,
        rc_a_reports=rc_a_reports,
        rc_c_reports=rc_c_reports,
        expected_total=args.expected_total,
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
