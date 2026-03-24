#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz10_lib import (
    PRIMARY_REASONS,
    TRACE_STAGE_ORDER,
    load_json,
    question_index,
    runtime_trace,
    stage_map,
    top_level_payload_diff,
    write_json,
)

LEVEL_ORDER = ["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7"]


def _stage_hash(stage_row: dict[str, Any] | None) -> str | None:
    if not isinstance(stage_row, dict):
        return None
    value = stage_row.get("hash")
    return value if isinstance(value, str) else None


def _runtime_error_row(*, question_id: str, topology_level: str, notes: str) -> dict[str, Any]:
    return {
        "question_id": question_id,
        "topology_level": topology_level,
        "first_break_stage": None,
        "primary_reason": "parity_runtime_error",
        "mismatch_stage_count": 0,
        "notes": notes,
    }


def _first_break_reason(*, topology_level: str, first_break_stage: str | None) -> str:
    if topology_level in PRIMARY_REASONS:
        return PRIMARY_REASONS[topology_level]
    if first_break_stage == "response_envelope":
        return "response_envelope_mapping_drift"
    if first_break_stage in {"eval_client_parsed_object", "normalized_parity_object"}:
        return "eval_client_parse_drift"
    if first_break_stage == "raw_answer_object":
        return "raw_answer_object_hash_drift"
    return "parity_runtime_error"


def build_ladder_replay(
    *,
    question_ids: list[str],
    reference_reports: dict[str, dict[str, Any]],
    candidate_reports: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    replay_rows: list[dict[str, Any]] = []
    first_break_rows: list[dict[str, Any]] = []
    reconciliation_rows: list[dict[str, Any]] = []
    reason_histogram: Counter[str] = Counter()

    for question_id in question_ids:
        assigned = False
        per_level_rows: list[dict[str, Any]] = []
        for level in LEVEL_ORDER:
            reference_question = question_index(reference_reports[level]).get(question_id)
            candidate_question = question_index(candidate_reports[level]).get(question_id)
            if reference_question is None or candidate_question is None:
                row = _runtime_error_row(
                    question_id=question_id,
                    topology_level=level,
                    notes="question missing in reference or candidate report",
                )
                per_level_rows.append(row)
                if not assigned:
                    first_break_rows.append(row)
                    reconciliation_rows.append(
                        {
                            "question_id": question_id,
                            "first_break_topology": level,
                            "first_break_stage": None,
                            "primary_reason": "parity_runtime_error",
                        }
                    )
                    reason_histogram["parity_runtime_error"] += 1
                    assigned = True
                continue

            reference_trace = runtime_trace(reference_question)
            candidate_trace = runtime_trace(candidate_question)
            if not reference_trace or not candidate_trace:
                row = _runtime_error_row(
                    question_id=question_id,
                    topology_level=level,
                    notes="v3_runtime_parity_trace missing in reference or candidate report",
                )
                per_level_rows.append(row)
                if not assigned:
                    first_break_rows.append(row)
                    reconciliation_rows.append(
                        {
                            "question_id": question_id,
                            "first_break_topology": level,
                            "first_break_stage": None,
                            "primary_reason": "parity_runtime_error",
                        }
                    )
                    reason_histogram["parity_runtime_error"] += 1
                    assigned = True
                continue

            reference_stages = stage_map(reference_question)
            candidate_stages = stage_map(candidate_question)
            mismatch_stages: list[str] = []
            stage_field_diffs: dict[str, list[str]] = {}
            for stage_name in TRACE_STAGE_ORDER:
                reference_stage = reference_stages.get(stage_name)
                candidate_stage = candidate_stages.get(stage_name)
                if _stage_hash(reference_stage) != _stage_hash(candidate_stage):
                    mismatch_stages.append(stage_name)
                    reference_payload = reference_stage.get("payload") if isinstance(reference_stage, dict) else {}
                    candidate_payload = candidate_stage.get("payload") if isinstance(candidate_stage, dict) else {}
                    stage_field_diffs[stage_name] = top_level_payload_diff(
                        reference_payload if isinstance(reference_payload, dict) else {},
                        candidate_payload if isinstance(candidate_payload, dict) else {},
                    )

            row = {
                "question_id": question_id,
                "topology_level": level,
                "first_break_stage": mismatch_stages[0] if mismatch_stages else None,
                "primary_reason": None,
                "mismatch_stage_count": len(mismatch_stages),
                "mismatch_stages": mismatch_stages,
                "stage_field_diffs": stage_field_diffs,
                "notes": None,
            }
            per_level_rows.append(row)
            if mismatch_stages and not assigned:
                primary_reason = _first_break_reason(
                    topology_level=level,
                    first_break_stage=mismatch_stages[0],
                )
                first_break_rows.append(
                    {
                        **row,
                        "primary_reason": primary_reason,
                    }
                )
                reconciliation_rows.append(
                    {
                        "question_id": question_id,
                        "first_break_topology": level,
                        "first_break_stage": mismatch_stages[0],
                        "primary_reason": primary_reason,
                    }
                )
                reason_histogram[primary_reason] += 1
                assigned = True

        if not assigned:
            first_break_rows.append(
                {
                    "question_id": question_id,
                    "topology_level": None,
                    "first_break_stage": None,
                    "primary_reason": None,
                    "mismatch_stage_count": 0,
                    "notes": "no_drift_observed_in_ladder",
                }
            )
            reconciliation_rows.append(
                {
                    "question_id": question_id,
                    "first_break_topology": None,
                    "first_break_stage": None,
                    "primary_reason": None,
                }
            )

        replay_rows.extend(per_level_rows)

    summary = {
        "tracked_count": len(question_ids),
        "first_break_assigned_count": sum(1 for row in reconciliation_rows if row["first_break_topology"] is not None),
        "primary_reason_assigned_count": sum(1 for row in reconciliation_rows if row["primary_reason"] is not None),
        "unexplained_count": sum(1 for row in reconciliation_rows if row["primary_reason"] is None),
        "reason_histogram": dict(sorted(reason_histogram.items())),
        "replay_rows": replay_rows,
        "first_break_rows": first_break_rows,
        "reconciliation_rows": reconciliation_rows,
    }
    return summary


def render_replay_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# FAZ10 V3-32 Topology Ladder Replay",
        "",
        f"- tracked_count = `{summary['tracked_count']}`",
        f"- first_break_assigned_count = `{summary['first_break_assigned_count']}`",
        f"- primary_reason_assigned_count = `{summary['primary_reason_assigned_count']}`",
        f"- unexplained_count = `{summary['unexplained_count']}`",
        "",
        "## Reason Histogram",
        "",
    ]
    histogram = summary["reason_histogram"]
    if not histogram:
        lines.append("- histogram yok")
    else:
        for reason, count in histogram.items():
            lines.append(f"- `{reason}` = `{count}`")
    lines.extend(["", "## First Break Sample", ""])
    for row in summary["first_break_rows"][:20]:
        lines.append(
            f"- `{row['question_id']}` `{row.get('topology_level')}` `{row.get('first_break_stage')}` `{row.get('primary_reason')}`"
        )
    lines.append("")
    return "\n".join(lines)


def render_first_break_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# FAZ10 V3-32 First Break Table",
        "",
        "| question_id | first_break_topology | first_break_stage | primary_reason |",
        "| --- | --- | --- | --- |",
    ]
    for row in summary["reconciliation_rows"]:
        lines.append(
            f"| {row['question_id']} | {row['first_break_topology'] or '-'} | {row['first_break_stage'] or '-'} | {row['primary_reason'] or '-'} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_reconciliation_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# FAZ10 V3-32 Reconciliation Table",
        "",
        f"- tracked_count = `{summary['tracked_count']}`",
        f"- first_break_assigned_count = `{summary['first_break_assigned_count']}`",
        f"- primary_reason_assigned_count = `{summary['primary_reason_assigned_count']}`",
        f"- unexplained_count = `{summary['unexplained_count']}`",
        "",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ10 v3 topology ladder replay summary.")
    parser.add_argument("--frontier-summary-json", type=Path, required=True)
    parser.add_argument("--reference-report-prefix", required=True, help="Prefix with {level} placeholder")
    parser.add_argument("--candidate-report-prefix", required=True, help="Prefix with {level} placeholder")
    parser.add_argument("--output-replay-md", type=Path, required=True)
    parser.add_argument("--output-first-break-md", type=Path, required=True)
    parser.add_argument("--output-reconciliation-md", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    frontier_summary = load_json(args.frontier_summary_json)
    reference_reports = {
        level: load_json(Path(args.reference_report_prefix.format(level=level.lower())))
        for level in LEVEL_ORDER
    }
    candidate_reports = {
        level: load_json(Path(args.candidate_report_prefix.format(level=level.lower())))
        for level in LEVEL_ORDER
    }
    summary = build_ladder_replay(
        question_ids=frontier_summary["question_ids"],
        reference_reports=reference_reports,
        candidate_reports=candidate_reports,
    )
    args.output_replay_md.write_text(render_replay_markdown(summary), encoding="utf-8")
    args.output_first_break_md.write_text(render_first_break_markdown(summary), encoding="utf-8")
    args.output_reconciliation_md.write_text(render_reconciliation_markdown(summary), encoding="utf-8")
    if args.output_json:
        write_json(args.output_json, summary)
    return 0 if summary["unexplained_count"] == 0 and summary["tracked_count"] == summary["first_break_assigned_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
