#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz26_lib import load_json, write_json


def _family_label(family_id: str) -> str:
    return family_id.replace("-", "_")


def build_summary(reports: list[dict[str, Any]]) -> dict[str, Any]:
    family_rows = []
    total_runtime_error_count = 0
    total_unexplained_count = 0
    for report in reports:
        unexplained = sum(
            1
            for row in report.get("mismatch_rows", [])
            if not row.get("first_divergence_stage") or not row.get("primary_reason")
        )
        runtime_error_count = int(report.get("reference_runtime_error_count", 0)) + int(
            report.get("candidate_runtime_error_count", 0)
        )
        total_runtime_error_count += runtime_error_count
        total_unexplained_count += unexplained
        family_rows.append(
            {
                "family_id": str(report["family_id"]),
                "mismatch_count": int(report.get("mismatch_count", 0)),
                "family_metric_delta_zero": bool(report.get("family_metric_delta_zero", False)),
                "runtime_error_count": runtime_error_count,
                "unexplained_count": unexplained,
            }
        )

    summary: dict[str, Any] = {
        "family_count": len(family_rows),
        "family_metric_delta_zero": all(row["family_metric_delta_zero"] for row in family_rows),
        "runtime_error_count": total_runtime_error_count,
        "unexplained_count": total_unexplained_count,
        "families": family_rows,
    }
    for row in family_rows:
        summary[f"{_family_label(row['family_id'])}_mismatch_count"] = row["mismatch_count"]
    return summary


def render_markdown(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- faz1_50_mismatch_count = `{summary.get('faz1_50_mismatch_count', 0)}`",
        f"- v2_95_mismatch_count = `{summary.get('v2_95_mismatch_count', 0)}`",
        f"- v3_170_mismatch_count = `{summary.get('v3_170_mismatch_count', 0)}`",
        f"- family_metric_delta_zero = `{'true' if summary['family_metric_delta_zero'] else 'false'}`",
        f"- runtime_error_count = `{summary['runtime_error_count']}`",
        f"- unexplained_count = `{summary['unexplained_count']}`",
        "",
        "| family | mismatch_count | family_metric_delta_zero | runtime_error_count | unexplained_count |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in summary["families"]:
        lines.append(
            f"| {row['family_id']} | {row['mismatch_count']} | {'true' if row['family_metric_delta_zero'] else 'false'} | {row['runtime_error_count']} | {row['unexplained_count']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ26 output parity summary.")
    parser.add_argument("--report-json", type=Path, action="append", required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--title", required=True)
    args = parser.parse_args()

    summary = build_summary([load_json(path) for path in args.report_json])
    write_json(args.output_json, summary)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(summary, title=args.title), encoding="utf-8")
    return 0 if (
        summary.get("faz1_50_mismatch_count", 0) == 0
        and summary.get("v2_95_mismatch_count", 0) == 0
        and summary.get("v3_170_mismatch_count", 0) == 0
        and summary["family_metric_delta_zero"] is True
        and summary["runtime_error_count"] == 0
        and summary["unexplained_count"] == 0
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
