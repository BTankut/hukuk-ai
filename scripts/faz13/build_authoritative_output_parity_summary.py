#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz13_lib import load_json, write_json  # noqa: E402


SUMMARY_KEYS = (
    "normalized_request_hash_mismatch_count",
    "model_request_payload_hash_mismatch_count",
    "generation_contract_hash_mismatch_count",
    "preprojection_anchor_mismatch_count",
    "cited_projection_hash_mismatch_count",
    "citation_set_projection_hash_mismatch_count",
    "final_mode_mapping_hash_mismatch_count",
    "blocked_reason_set_mismatch_count",
    "final_answer_payload_hash_mismatch_count",
    "response_envelope_hash_mismatch_count",
    "serialized_output_hash_mismatch_count",
    "mismatch_count",
)


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
            "family_metric_delta_zero": bool(report["family_metric_delta_zero"]),
            "metric_delta": dict(report["metric_delta"]),
            "output_parity_authority_cleared": bool(report["output_parity_authority_cleared"]),
        }
        for key in SUMMARY_KEYS:
            family[key] = int(report[key])
        families.append(family)

    summary = {
        "family_count": len(families),
        "question_count": sum(item["question_count"] for item in families),
        "mismatch_count": sum(item["mismatch_count"] for item in families),
        "all_families_pass": all(item["output_parity_authority_cleared"] for item in families),
        "families": families,
    }
    return summary


def render_markdown(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- family_count = `{summary['family_count']}`",
        f"- question_count = `{summary['question_count']}`",
        f"- mismatch_count = `{summary['mismatch_count']}`",
        f"- all_families_pass = `{str(summary['all_families_pass']).lower()}`",
        "",
        "| family | pass | mismatch | metric_delta_zero | candidate_runtime_error |",
        "| --- | --- | ---: | --- | ---: |",
    ]
    for family in summary["families"]:
        lines.append(
            f"| {family['family_id']} | {str(family['output_parity_authority_cleared']).lower()} | {family['mismatch_count']} | {str(family['family_metric_delta_zero']).lower()} | {family['candidate_runtime_error_count']} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ13 authoritative output parity summary.")
    parser.add_argument("--parity-json", type=Path, action="append", required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--title", default="FAZ13 RC-J Output Parity Authoritative Summary")
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
