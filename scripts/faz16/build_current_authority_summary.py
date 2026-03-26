#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz16_lib import UPSTREAM_EQUALITY_FIELDS, load_json, stable_hash, write_json


def build_summary(reports: list[dict[str, Any]]) -> dict[str, Any]:
    family_rows: list[dict[str, Any]] = []
    control_pair_breach_in_f0_f12 = False
    total_runtime_error_count = 0

    for report in sorted(reports, key=lambda item: str(item["family_id"])):
        mismatch_stage_histogram: dict[str, int] = {}
        for row in report.get("mismatch_rows", []):
            if not isinstance(row, dict):
                continue
            stage = row.get("first_divergence_stage")
            if not isinstance(stage, str) or not stage:
                continue
            mismatch_stage_histogram[stage] = mismatch_stage_histogram.get(stage, 0) + 1
            if stage in UPSTREAM_EQUALITY_FIELDS:
                control_pair_breach_in_f0_f12 = True

        runtime_error_count = int(report.get("reference_runtime_error_count", 0)) + int(
            report.get("candidate_runtime_error_count", 0)
        )
        total_runtime_error_count += runtime_error_count
        family_pass = (
            runtime_error_count == 0
            and bool(report.get("family_metric_delta_zero"))
            and not any(stage in UPSTREAM_EQUALITY_FIELDS for stage in mismatch_stage_histogram)
        )
        family_rows.append(
            {
                "family_id": report["family_id"],
                "mismatch_count": int(report.get("mismatch_count", 0)),
                "runtime_error_count": runtime_error_count,
                "family_metric_delta_zero": bool(report.get("family_metric_delta_zero")),
                "mismatch_stage_histogram": mismatch_stage_histogram,
                "pass": family_pass,
            }
        )

    summary = {
        "family_count": len(family_rows),
        "families": family_rows,
        "runtime_error_count": total_runtime_error_count,
        "control_pair_breach_in_f0_f12": control_pair_breach_in_f0_f12,
        "family_metric_delta_zero": all(row["family_metric_delta_zero"] for row in family_rows),
        "authority_snapshot_frozen": True,
        "wp2_pass": total_runtime_error_count == 0
        and not control_pair_breach_in_f0_f12
        and all(row["family_metric_delta_zero"] for row in family_rows),
    }
    summary["report_hash"] = stable_hash(summary)
    return summary


def render_markdown(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- family_count = `{summary['family_count']}`",
        f"- runtime_error_count = `{summary['runtime_error_count']}`",
        f"- control_pair_breach_in_f0_f12 = `{str(summary['control_pair_breach_in_f0_f12']).lower()}`",
        f"- family_metric_delta_zero = `{str(summary['family_metric_delta_zero']).lower()}`",
        f"- authority_snapshot_frozen = `{str(summary['authority_snapshot_frozen']).lower()}`",
        f"- wp2_pass = `{str(summary['wp2_pass']).lower()}`",
        "",
        "| family | pass | mismatch_count | runtime_error_count | family_metric_delta_zero | mismatch_stage_histogram |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in summary["families"]:
        lines.append(
            f"| {row['family_id']} | {str(row['pass']).lower()} | {row['mismatch_count']} | "
            f"{row['runtime_error_count']} | {str(row['family_metric_delta_zero']).lower()} | "
            f"{row['mismatch_stage_histogram']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ16 current control authority summary.")
    parser.add_argument("--report-json", type=Path, action="append", required=True)
    parser.add_argument("--summary-output-json", type=Path, required=True)
    parser.add_argument("--summary-output-md", type=Path, required=True)
    parser.add_argument("--title", default="FAZ16 RC-G vs RC-J Control Authority Current Summary")
    args = parser.parse_args()

    summary = build_summary([load_json(path) for path in args.report_json])
    write_json(args.summary_output_json, summary)
    args.summary_output_md.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output_md.write_text(render_markdown(summary, title=args.title), encoding="utf-8")
    return 0 if summary["wp2_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

