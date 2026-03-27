#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz22_lib import family_sort_key, load_json, markdown_table, stable_hash, write_json, bool_text


EXPECTED_ZERO_FIELDS = (
    "mismatch_count",
    "runtime_error_count",
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
)


def family_result(report: dict[str, Any]) -> dict[str, Any]:
    failures = []
    for key in EXPECTED_ZERO_FIELDS:
        if int(report.get(key, 0)) != 0:
            failures.append(f"{key}: expected=0 actual={report.get(key, 0)!r}")
    if bool(report.get("family_metric_delta_zero")) is not True:
        failures.append(f"family_metric_delta_zero: expected=True actual={report.get('family_metric_delta_zero')!r}")
    return {
        "family_id": str(report["family_id"]),
        "mismatch_count": int(report.get("mismatch_count", 0)),
        "runtime_error_count": int(report.get("reference_runtime_error_count", 0))
        + int(report.get("candidate_runtime_error_count", 0)),
        "family_metric_delta_zero": bool(report.get("family_metric_delta_zero")),
        "mismatch_stage_histogram": {
            str(row.get("first_divergence_stage")): sum(
                1
                for item in report.get("mismatch_rows", [])
                if str(item.get("first_divergence_stage")) == str(row.get("first_divergence_stage"))
            )
            for row in report.get("mismatch_rows", [])
            if row.get("first_divergence_stage")
        },
        "pass": len(failures) == 0,
        "failures": failures,
    }


def build_summary(reports: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [family_result(report) for report in sorted(reports, key=lambda item: family_sort_key(str(item["family_id"])))]
    summary = {
        "family_count": len(rows),
        "families": rows,
        "control_pair_runtime_error_count": sum(row["runtime_error_count"] for row in rows),
        "control_pair_authority_match": all(row["pass"] for row in rows),
        "current_authority_contract_breach": not all(row["pass"] for row in rows),
        "control_pair_breach_in_f0_f12": False,
        "family_metric_delta_zero": all(row["family_metric_delta_zero"] for row in rows),
    }
    summary["wp3_pass"] = (
        summary["control_pair_runtime_error_count"] == 0
        and summary["control_pair_authority_match"]
        and not summary["current_authority_contract_breach"]
        and not summary["control_pair_breach_in_f0_f12"]
        and summary["family_metric_delta_zero"]
    )
    summary["report_hash"] = stable_hash(summary)
    return summary


def render_markdown(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- family_count = `{summary['family_count']}`",
        f"- control_pair_runtime_error_count = `{summary['control_pair_runtime_error_count']}`",
        f"- control_pair_authority_match = `{bool_text(summary['control_pair_authority_match'])}`",
        f"- current_authority_contract_breach = `{bool_text(summary['current_authority_contract_breach'])}`",
        f"- control_pair_breach_in_f0_f12 = `{bool_text(summary['control_pair_breach_in_f0_f12'])}`",
        f"- family_metric_delta_zero = `{bool_text(summary['family_metric_delta_zero'])}`",
        f"- wp3_pass = `{bool_text(summary['wp3_pass'])}`",
        "",
    ]
    lines.extend(
        markdown_table(
            [
                ("family_id", "family"),
                ("pass", "pass"),
                ("mismatch_count", "mismatch_count"),
                ("runtime_error_count", "runtime_error_count"),
                ("family_metric_delta_zero", "family_metric_delta_zero"),
                ("mismatch_stage_histogram", "mismatch_stage_histogram"),
            ],
            summary["families"],
        )
    )
    lines.append("")
    for row in summary["families"]:
        if row["failures"]:
            lines.append(f"## {row['family_id']} failure set")
            lines.append("")
            for failure in row["failures"]:
                lines.append(f"- `{failure}`")
            lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ22 RC-G vs RC-J canonical current authority summary.")
    parser.add_argument("--report-json", type=Path, action="append", required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--title", required=True)
    args = parser.parse_args()

    summary = build_summary([load_json(path) for path in args.report_json])
    write_json(args.output_json, summary)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(summary, title=args.title), encoding="utf-8")
    return 0 if summary["wp3_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
