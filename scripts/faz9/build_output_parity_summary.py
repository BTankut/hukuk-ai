#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz9_lib import load_json, write_json


def _parity_error_count(report: dict[str, Any]) -> int:
    explicit = report.get("parity_error_count")
    if isinstance(explicit, int):
        return explicit
    mismatches = report.get("mismatches")
    if not isinstance(mismatches, list):
        return 0
    return sum(
        1
        for item in mismatches
        if isinstance(item, dict) and item.get("kind") in {"missing_question", "parity_runtime_error"}
    )


def build_summary(per_family_reports: list[dict[str, Any]]) -> dict[str, Any]:
    families: list[dict[str, Any]] = []
    for report in per_family_reports:
        family = {
            "family": report.get("reference_eval_family") or report.get("candidate_eval_family") or "unknown",
            "question_count": int(report.get("question_count", 0)),
            "mismatch_count": int(report.get("mismatch_count", 0)),
            "parity_error_count": _parity_error_count(report),
            "family_metric_delta_zero": bool(report.get("family_metric_delta_zero", False)),
            "metric_delta": report.get("metric_delta", {}),
        }
        family["pass"] = (
            family["mismatch_count"] == 0
            and family["parity_error_count"] == 0
            and family["family_metric_delta_zero"]
        )
        families.append(family)

    return {
        "family_count": len(families),
        "question_count": sum(item["question_count"] for item in families),
        "parity_mismatch_count": sum(item["mismatch_count"] for item in families),
        "parity_error_count": sum(item["parity_error_count"] for item in families),
        "all_families_zero_mismatch": all(item["mismatch_count"] == 0 for item in families),
        "all_families_zero_metric_delta": all(item["family_metric_delta_zero"] for item in families),
        "all_families_zero_error": all(item["parity_error_count"] == 0 for item in families),
        "all_families_pass": all(item["pass"] for item in families),
        "families": families,
    }


def render_markdown(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- family_count = `{summary['family_count']}`",
        f"- question_count = `{summary['question_count']}`",
        f"- parity_mismatch_count = `{summary['parity_mismatch_count']}`",
        f"- parity_error_count = `{summary['parity_error_count']}`",
        f"- all_families_zero_mismatch = `{str(summary['all_families_zero_mismatch']).lower()}`",
        f"- all_families_zero_error = `{str(summary['all_families_zero_error']).lower()}`",
        f"- all_families_zero_metric_delta = `{str(summary['all_families_zero_metric_delta']).lower()}`",
        f"- all_families_pass = `{str(summary['all_families_pass']).lower()}`",
        "",
        "## Family Breakdown",
        "",
    ]
    for item in summary["families"]:
        lines.append(
            f"- `{item['family']}` mismatch `{item['mismatch_count']}` error `{item['parity_error_count']}` metric_delta_zero `{str(item['family_metric_delta_zero']).lower()}`"
        )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ9 output parity summary.")
    parser.add_argument("--parity-json", type=Path, action="append", required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--title", default="FAZ9 RC-J Output Parity Summary")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = build_summary([load_json(path) for path in args.parity_json])
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(summary, title=args.title), encoding="utf-8")
    if args.output_json:
        write_json(args.output_json, summary)
    return 0 if summary["all_families_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
