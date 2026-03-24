#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from build_tbk005_witness_forensics import build_witness_forensics
from faz9_lib import load_json, write_json


def _parse_candidate_spec(value: str) -> tuple[str, Path]:
    label, sep, raw_path = value.partition("=")
    if not sep or not label or not raw_path:
        raise argparse.ArgumentTypeError("candidate spec must be LABEL=PATH")
    return label, Path(raw_path)


def build_ladder_summary(
    *,
    reference_report: dict[str, Any],
    candidate_reports: list[tuple[str, dict[str, Any]]],
    question_id: str,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    first_divergence_level: str | None = None
    first_divergence_stage: str | None = None
    primary_reason: str | None = None

    for label, report in candidate_reports:
        witness = build_witness_forensics(
            reference_report=reference_report,
            candidate_report=report,
            question_id=question_id,
        )
        row = {
            "ladder_level": label,
            "first_divergence_stage": witness["first_divergence_stage"],
            "primary_reason": witness["primary_reason"],
            "unexplained_count": witness["unexplained_count"],
            "parity_match": witness["first_divergence_stage"] == "none",
        }
        rows.append(row)
        if first_divergence_level is None and not row["parity_match"]:
            first_divergence_level = label
            first_divergence_stage = witness["first_divergence_stage"]
            primary_reason = witness["primary_reason"]

    return {
        "question_id": question_id,
        "ladder_row_count": len(rows),
        "first_divergence_level": first_divergence_level,
        "first_divergence_stage": first_divergence_stage,
        "primary_reason": primary_reason,
        "rows": rows,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# FAZ9 Bind Ladder Replay",
        "",
        f"- question_id = `{summary['question_id']}`",
        f"- first_divergence_level = `{summary.get('first_divergence_level')}`",
        f"- first_divergence_stage = `{summary.get('first_divergence_stage')}`",
        f"- primary_reason = `{summary.get('primary_reason')}`",
        "",
        "| ladder_level | parity_match | first_divergence_stage | primary_reason | unexplained_count |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in summary["rows"]:
        lines.append(
            f"| {row['ladder_level']} | {str(row['parity_match']).lower()} | "
            f"{row['first_divergence_stage'] or '-'} | {row['primary_reason'] or '-'} | "
            f"{row['unexplained_count']} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ9 release-control bind ladder replay.")
    parser.add_argument("--reference-report", type=Path, required=True)
    parser.add_argument("--candidate-report", type=_parse_candidate_spec, action="append", required=True)
    parser.add_argument("--question-id", default="TBK-005")
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    reference_report = load_json(args.reference_report)
    candidate_reports = [(label, load_json(path)) for label, path in args.candidate_report]
    summary = build_ladder_summary(
        reference_report=reference_report,
        candidate_reports=candidate_reports,
        question_id=args.question_id,
    )
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(summary), encoding="utf-8")
    if args.output_json:
        write_json(args.output_json, summary)
    return 0 if summary["first_divergence_level"] is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
