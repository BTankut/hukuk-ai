#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz9_lib import (
    PRIMARY_REASON_BY_STAGE,
    STAGE_ORDER,
    load_json,
    question_index,
    stage_hash,
    stage_map,
    stage_payload,
    top_level_payload_diff,
    write_json,
)


def build_witness_forensics(
    *,
    reference_report: dict[str, Any],
    candidate_report: dict[str, Any],
    question_id: str,
) -> dict[str, Any]:
    reference_question = question_index(reference_report).get(question_id)
    candidate_question = question_index(candidate_report).get(question_id)
    if reference_question is None or candidate_question is None:
        return {
            "question_id": question_id,
            "unexplained_count": 1,
            "first_divergence_stage": "eval_client_parsed_object",
            "primary_reason": "parity_runtime_error",
            "stage_rows": [],
            "notes": "question missing in reference or candidate report",
        }

    reference_stages = stage_map(reference_question)
    candidate_stages = stage_map(candidate_question)
    stage_rows: list[dict[str, Any]] = []
    first_divergence_stage: str | None = None
    primary_reason: str | None = None

    for stage_name in STAGE_ORDER:
        reference_stage = reference_stages.get(stage_name)
        candidate_stage = candidate_stages.get(stage_name)
        reference_hash = stage_hash(reference_stage)
        candidate_hash = stage_hash(candidate_stage)
        reference_payload = stage_payload(reference_stage)
        candidate_payload = stage_payload(candidate_stage)
        equal = reference_hash is not None and reference_hash == candidate_hash
        field_diff = [] if equal else top_level_payload_diff(reference_payload, candidate_payload)
        if first_divergence_stage is None and not equal:
            first_divergence_stage = stage_name
            primary_reason = PRIMARY_REASON_BY_STAGE[stage_name]
        stage_rows.append(
            {
                "stage": stage_name,
                "equal": equal,
                "reference_hash": reference_hash,
                "candidate_hash": candidate_hash,
                "field_diff": field_diff,
                "reference_payload": reference_payload,
                "candidate_payload": candidate_payload,
            }
        )

    if first_divergence_stage is None:
        first_divergence_stage = "none"
        primary_reason = "none"

    return {
        "question_id": question_id,
        "eval_family": reference_report.get("report_meta", {}).get("eval_family"),
        "reference_checkpoint_ref": reference_report.get("report_meta", {}).get("checkpoint_ref"),
        "candidate_checkpoint_ref": candidate_report.get("report_meta", {}).get("checkpoint_ref"),
        "unexplained_count": 0,
        "first_divergence_stage": first_divergence_stage,
        "primary_reason": primary_reason,
        "stage_rows": stage_rows,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# FAZ9 TBK-005 Witness Forensics",
        "",
        f"- question_id = `{summary['question_id']}`",
        f"- eval_family = `{summary.get('eval_family')}`",
        f"- first_divergence_stage = `{summary['first_divergence_stage']}`",
        f"- primary_reason = `{summary['primary_reason']}`",
        f"- unexplained_count = `{summary['unexplained_count']}`",
        "",
        "## Stage Replay",
        "",
        "| stage | equal | field_diff |",
        "| --- | --- | --- |",
    ]
    for row in summary["stage_rows"]:
        diff = ", ".join(row["field_diff"]) if row["field_diff"] else "-"
        lines.append(f"| {row['stage']} | {str(row['equal']).lower()} | {diff} |")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ9 TBK-005 witness forensics report.")
    parser.add_argument("--reference-report", type=Path, required=True)
    parser.add_argument("--candidate-report", type=Path, required=True)
    parser.add_argument("--question-id", default="TBK-005")
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = build_witness_forensics(
        reference_report=load_json(args.reference_report),
        candidate_report=load_json(args.candidate_report),
        question_id=args.question_id,
    )
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(summary), encoding="utf-8")
    if args.output_json:
        write_json(args.output_json, summary)
    return 0 if summary["unexplained_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
