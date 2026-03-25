#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz14_lib import load_json, stable_hash, write_json  # noqa: E402


def build_summary(reports: list[dict[str, Any]]) -> dict[str, Any]:
    families = []
    for report in reports:
        families.append(
            {
                "family_id": report["family_id"],
                "output_parity_repair_cleared": bool(report["output_parity_repair_cleared"]),
                "mismatch_count": int(report["mismatch_count"]),
                "runtime_error_count": int(report["runtime_error_count"]),
                "family_metric_delta_zero": bool(report["family_metric_delta_zero"]),
                "metric_delta": dict(report["metric_delta"]),
            }
        )
    summary = {
        "family_count": len(families),
        "families": families,
        "all_families_pass": all(item["output_parity_repair_cleared"] for item in families),
    }
    summary["report_hash"] = stable_hash(summary)
    return summary


def render_markdown(summary: dict[str, Any], *, title: str) -> str:
    lines = [f"# {title}", "", f"- family_count = `{summary['family_count']}`", f"- all_families_pass = `{str(summary['all_families_pass']).lower()}`", "", "| family | cleared | mismatch_count | metric_delta_zero | runtime_error_count |", "| --- | --- | ---: | --- | ---: |"]
    for family in summary["families"]:
        lines.append(
            f"| {family['family_id']} | {str(family['output_parity_repair_cleared']).lower()} | {family['mismatch_count']} | "
            f"{str(family['family_metric_delta_zero']).lower()} | {family['runtime_error_count']} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ14 output repair summary.")
    parser.add_argument("--report-json", type=Path, action="append", required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--title", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = build_summary([load_json(path) for path in args.report_json])
    write_json(args.output_json, summary)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(summary, title=args.title), encoding="utf-8")
    return 0 if summary["all_families_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
