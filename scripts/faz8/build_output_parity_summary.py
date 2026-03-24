#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz8_lib import load_json, write_json


def build_summary(per_family_reports: list[dict[str, Any]]) -> dict[str, Any]:
    families: list[dict[str, Any]] = []
    for report in per_family_reports:
        families.append(
            {
                "family": report.get("reference_eval_family") or report.get("candidate_eval_family"),
                "mismatch_count": int(report.get("mismatch_count", 0)),
                "family_metric_delta_zero": bool(report.get("family_metric_delta_zero", False)),
                "metric_delta": report.get("metric_delta", {}),
            }
        )
    return {
        "parity_mismatch_count": sum(item["mismatch_count"] for item in families),
        "parity_error_count": 0,
        "all_families_zero_mismatch": all(item["mismatch_count"] == 0 for item in families),
        "all_families_zero_metric_delta": all(item["family_metric_delta_zero"] for item in families),
        "families": families,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# FAZ8 RC-I Output Parity Summary",
        "",
        f"- parity_mismatch_count = `{summary['parity_mismatch_count']}`",
        f"- parity_error_count = `{summary['parity_error_count']}`",
        f"- all_families_zero_mismatch = `{str(summary['all_families_zero_mismatch']).lower()}`",
        f"- all_families_zero_metric_delta = `{str(summary['all_families_zero_metric_delta']).lower()}`",
        "",
        "## Family Breakdown",
        "",
    ]
    for item in summary["families"]:
        lines.append(
            f"- `{item['family']}` mismatch `{item['mismatch_count']}` metric_delta_zero `{str(item['family_metric_delta_zero']).lower()}`"
        )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ8 output parity summary.")
    parser.add_argument("--parity-json", type=Path, action="append", required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = build_summary([load_json(path) for path in args.parity_json])
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(summary), encoding="utf-8")
    if args.output_json:
        write_json(args.output_json, summary)
    return 0 if summary["all_families_zero_mismatch"] and summary["all_families_zero_metric_delta"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
