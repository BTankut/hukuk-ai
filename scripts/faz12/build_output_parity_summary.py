#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz12_lib import load_json, write_json  # noqa: E402


def build_summary(per_family_reports: list[dict[str, Any]]) -> dict[str, Any]:
    families: list[dict[str, Any]] = []
    for report in per_family_reports:
        family = {
            "family_id": report["family_id"],
            "question_count": int(report["question_count"]),
            "reference_runtime_error_count": int(report["reference_runtime_error_count"]),
            "candidate_runtime_error_count": int(report["candidate_runtime_error_count"]),
            "reference_error_rerun_row_count": int(report["reference_error_rerun_row_count"]),
            "candidate_error_rerun_row_count": int(report["candidate_error_rerun_row_count"]),
            "preprojection_anchor_mismatch_count": int(report["preprojection_anchor_mismatch_count"]),
            "cited_projection_hash_mismatch_count": int(report["cited_projection_hash_mismatch_count"]),
            "citation_set_projection_hash_mismatch_count": int(report["citation_set_projection_hash_mismatch_count"]),
            "final_mode_mapping_hash_mismatch_count": int(report["final_mode_mapping_hash_mismatch_count"]),
            "final_answer_payload_hash_mismatch_count": int(report["final_answer_payload_hash_mismatch_count"]),
            "response_envelope_hash_mismatch_count": int(report["response_envelope_hash_mismatch_count"]),
            "serialized_output_hash_mismatch_count": int(report["serialized_output_hash_mismatch_count"]),
            "answer_body_hash_mismatch_count": int(report["answer_body_hash_mismatch_count"]),
            "citation_body_hash_mismatch_count": int(report["citation_body_hash_mismatch_count"]),
            "refusal_body_hash_mismatch_count": int(report["refusal_body_hash_mismatch_count"]),
            "blocked_reason_set_mismatch_count": int(report["blocked_reason_set_mismatch_count"]),
            "family_metric_delta_zero": bool(report["family_metric_delta_zero"]),
            "metric_delta": dict(report["metric_delta"]),
            "output_parity_reopened": bool(report["output_parity_reopened"]),
            "parity_frontier_count": int(report["parity_frontier_count"]),
        }
        family["pass"] = bool(report["output_parity_reopened"])
        families.append(family)

    summary = {
        "family_count": len(families),
        "question_count": sum(item["question_count"] for item in families),
        "parity_frontier_count": sum(item["parity_frontier_count"] for item in families),
        "all_families_pass": all(item["pass"] for item in families),
        "families": families,
    }
    return summary


def render_markdown(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- family_count = `{summary['family_count']}`",
        f"- question_count = `{summary['question_count']}`",
        f"- parity_frontier_count = `{summary['parity_frontier_count']}`",
        f"- all_families_pass = `{str(summary['all_families_pass']).lower()}`",
        "",
        "| family | pass | frontier | candidate_runtime_error | metric_delta_zero |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for family in summary["families"]:
        lines.append(
            f"| {family['family_id']} | {str(family['pass']).lower()} | {family['parity_frontier_count']} | {family['candidate_runtime_error_count']} | {str(family['family_metric_delta_zero']).lower()} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ12 parity summary.")
    parser.add_argument("--parity-json", type=Path, action="append", required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--title", default="FAZ12 RC-J Output Parity Summary")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = build_summary([load_json(path) for path in args.parity_json])
    write_json(args.output_json, summary)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(summary, title=args.title), encoding="utf-8")
    return 0 if summary["all_families_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
