#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz17_lib import family_sort_key, load_json, stable_hash, write_json


def build_summary(reports: list[dict[str, Any]]) -> dict[str, Any]:
    family_rows = []
    for report in sorted(reports, key=lambda item: family_sort_key(str(item.get("family_id")))):
        family_rows.append(
            {
                "family_id": str(report.get("family_id")),
                "question_count": int(report.get("question_count", 0)),
                "runtime_error_count": int(report.get("runtime_error_count", 0)),
                "mismatch_count": int(report.get("mismatch_count", 0)),
                "family_metric_delta_zero": bool(report.get("family_metric_delta_zero")),
                "gate_pass": bool(report.get("gate_pass")),
            }
        )

    summary = {
        "family_count": len(family_rows),
        "families": family_rows,
        "runtime_error_count": sum(row["runtime_error_count"] for row in family_rows),
        "authoritative_summary_mismatch_count": sum(row["mismatch_count"] for row in family_rows),
        "wp3_pass": all(row["gate_pass"] for row in family_rows),
    }
    summary["report_hash"] = stable_hash(summary)
    return summary


def render_markdown(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- family_count = `{summary['family_count']}`",
        f"- runtime_error_count = `{summary['runtime_error_count']}`",
        f"- authoritative_summary_mismatch_count = `{summary['authoritative_summary_mismatch_count']}`",
        f"- wp3_pass = `{str(summary['wp3_pass']).lower()}`",
        "",
        "| family | gate_pass | mismatch_count | runtime_error_count | family_metric_delta_zero |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in summary["families"]:
        lines.append(
            f"| {row['family_id']} | {str(row['gate_pass']).lower()} | {row['mismatch_count']} | "
            f"{row['runtime_error_count']} | {str(row['family_metric_delta_zero']).lower()} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ17 authoritative parity summary.")
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
