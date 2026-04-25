#!/usr/bin/env python3
"""Compare two hukuk-ai benchmark run artifacts at row/trace-field level."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LEFT_RUN = REPO_ROOT / "reports/benchmark/runs/20260424T212636_phase17f_full"
DEFAULT_RIGHT_RUN = REPO_ROOT / "reports/benchmark/runs/20260425T_phase18_recovery_A0_phase17f_smoke20"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_18_recovery_phase17f_vs_currentenv_trace_diff.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_18_recovery_phase17f_vs_currentenv_trace_diff.md"

TRACE_FIELDS = [
    "source_family_claimed",
    "source_title_claimed",
    "source_identifier_claimed",
    "article_or_section_claimed",
    "selected_document_id",
    "selected_main_span_id",
    "selected_main_article",
    "selected_article",
    "selected_paragraph_or_clause",
    "primary_source_candidate",
    "supporting_source_candidate",
    "final_primary_source_reason",
    "expected_family_prior",
    "selected_family_source",
    "family_gate_status",
    "family_gate_reason",
    "document_state_binding_reason",
    "internal_document_choice_reason",
    "canonical_key_binding_applied",
    "binding_source_key",
    "selected_canonical_source_key_v2",
    "selected_canonical_document_key_v2",
    "answer_slot_coverage_score",
    "missing_fact_slots",
    "critical_answer_slots_missing",
    "final_reason",
    "grounding_status",
]
SCORE_FIELDS = [
    "score_0_10_proxy",
    "pass_fail_proxy",
    "family_match_score",
    "document_match_score",
    "article_match_score",
    "temporal_validity_score",
    "grounding_score",
    "answer_contract_score",
    "hallucinated_source_penalty",
    "auto_fail_triggered",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--left-run", type=Path, default=DEFAULT_LEFT_RUN)
    parser.add_argument("--right-run", type=Path, default=DEFAULT_RIGHT_RUN)
    parser.add_argument("--left-label", default="phase17f_original")
    parser.add_argument("--right-label", default="phase17f_code_current_env")
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--qids", nargs="*", help="Optional qid subset; accepts comma-separated values.")
    return parser.parse_args()


def normalize_qids(raw_qids: list[str] | None) -> list[str]:
    qids: list[str] = []
    for raw in raw_qids or []:
        qids.extend(part.strip() for part in raw.split(",") if part.strip())
    return qids


def read_csv_by_qid(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        return {row.get("qid", "").strip(): row for row in csv.DictReader(f) if row.get("qid", "").strip()}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def value(row: dict[str, str], field: str) -> str:
    return (row.get(field) or "").strip()


def numeric(text: str) -> float | None:
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def build_rows(args: argparse.Namespace) -> list[dict[str, str]]:
    left_answers = read_csv_by_qid(args.left_run / "candidate_answers.csv")
    right_answers = read_csv_by_qid(args.right_run / "candidate_answers.csv")
    left_scores = read_csv_by_qid(args.left_run / "scored.csv")
    right_scores = read_csv_by_qid(args.right_run / "scored.csv")
    requested_qids = normalize_qids(args.qids)
    if requested_qids:
        qids = requested_qids
    else:
        qids = sorted(set(left_answers) & set(right_answers))
    rows: list[dict[str, str]] = []
    for qid in qids:
        left_answer = left_answers.get(qid, {})
        right_answer = right_answers.get(qid, {})
        left_score = left_scores.get(qid, {})
        right_score = right_scores.get(qid, {})
        out: dict[str, str] = {
            "qid": qid,
            "left_present": str(bool(left_answer)),
            "right_present": str(bool(right_answer)),
        }
        changed_fields: list[str] = []
        for field in SCORE_FIELDS:
            left_value = value(left_score, field)
            right_value = value(right_score, field)
            out[f"left_{field}"] = left_value
            out[f"right_{field}"] = right_value
            if left_value != right_value:
                changed_fields.append(field)
        left_numeric_score = numeric(out.get("left_score_0_10_proxy", ""))
        right_numeric_score = numeric(out.get("right_score_0_10_proxy", ""))
        out["score_delta"] = (
            f"{right_numeric_score - left_numeric_score:.2f}"
            if left_numeric_score is not None and right_numeric_score is not None
            else ""
        )
        for field in TRACE_FIELDS:
            left_value = value(left_answer, field) or value(left_score, field)
            right_value = value(right_answer, field) or value(right_score, field)
            out[f"left_{field}"] = left_value
            out[f"right_{field}"] = right_value
            if left_value != right_value:
                changed_fields.append(field)
        out["changed_field_count"] = str(len(set(changed_fields)))
        out["changed_fields"] = " | ".join(sorted(set(changed_fields)))
        rows.append(out)
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "qid",
        "left_present",
        "right_present",
        *[f"left_{field}" for field in SCORE_FIELDS],
        *[f"right_{field}" for field in SCORE_FIELDS],
        "score_delta",
        *[f"left_{field}" for field in TRACE_FIELDS],
        *[f"right_{field}" for field in TRACE_FIELDS],
        "changed_field_count",
        "changed_fields",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def score_summary(run_dir: Path) -> dict[str, Any]:
    summary = read_json(run_dir / "score_summary.json")
    return summary if isinstance(summary, dict) else {}


def summary_metric(summary: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in summary:
            return summary[key]
    return "unknown"


def count_changes(rows: list[dict[str, str]]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for row in rows:
        for field in row.get("changed_fields", "").split(" | "):
            if field:
                counts[field] = counts.get(field, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def write_md(path: Path, args: argparse.Namespace, rows: list[dict[str, str]]) -> None:
    left_summary = score_summary(args.left_run)
    right_summary = score_summary(args.right_run)
    left_subset_score = sum(numeric(row.get("left_score_0_10_proxy", "")) or 0.0 for row in rows)
    right_subset_score = sum(numeric(row.get("right_score_0_10_proxy", "")) or 0.0 for row in rows)
    left_subset_pass = sum(1 for row in rows if row.get("left_pass_fail_proxy", "").upper() == "PASS")
    right_subset_pass = sum(1 for row in rows if row.get("right_pass_fail_proxy", "").upper() == "PASS")
    degraded = [
        row
        for row in rows
        if numeric(row.get("score_delta", "")) is not None and numeric(row.get("score_delta", "")) < 0
    ]
    changed_counts = count_changes(rows)
    lines = [
        "# Phase 18 Recovery Trace Diff",
        "",
        f"- left_run: `{args.left_run}`",
        f"- right_run: `{args.right_run}`",
        f"- compared_qids: {len(rows)}",
        f"- left_summary_raw_score_proxy: `{summary_metric(left_summary, 'raw_score_proxy', 'total_score', 'raw_score')}`",
        f"- right_summary_raw_score_proxy: `{summary_metric(right_summary, 'raw_score_proxy', 'total_score', 'raw_score')}`",
        f"- left_pass_proxy: `{summary_metric(left_summary, 'pass_proxy')}`",
        f"- right_pass_proxy: `{summary_metric(right_summary, 'pass_proxy')}`",
        f"- left_compared_subset_score: `{left_subset_score:.2f}`",
        f"- right_compared_subset_score: `{right_subset_score:.2f}`",
        f"- left_compared_subset_pass: `{left_subset_pass}/{len(rows)}`",
        f"- right_compared_subset_pass: `{right_subset_pass}/{len(rows)}`",
        f"- degraded_qids: {len(degraded)}",
        "",
        "## Most Changed Fields",
        "",
    ]
    for field, count in changed_counts[:20]:
        lines.append(f"- {field}: {count}")
    lines.extend(["", "## Degraded Rows", ""])
    for row in degraded[:30]:
        lines.append(
            "- "
            f"{row['qid']}: delta `{row['score_delta']}`, "
            f"family `{row.get('left_source_family_claimed', '')}` -> `{row.get('right_source_family_claimed', '')}`, "
            f"identifier `{row.get('left_source_identifier_claimed', '')}` -> `{row.get('right_source_identifier_claimed', '')}`, "
            f"selected_doc `{row.get('left_selected_document_id', '')}` -> `{row.get('right_selected_document_id', '')}`"
        )
    if not degraded:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    rows = build_rows(args)
    write_csv(args.out_csv, rows)
    write_md(args.out_md, args, rows)
    print(json.dumps({"rows": len(rows), "out_csv": str(args.out_csv), "out_md": str(args.out_md)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
