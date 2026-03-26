#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz18_lib import (  # noqa: E402
    EXPECTED_CONTROL_BY_FAMILY,
    UPSTREAM_F0_F12_STAGES,
    bool_text,
    family_sort_key,
    load_json,
    markdown_table,
    stable_hash,
    write_json,
)


def family_result(report: dict[str, Any]) -> dict[str, Any]:
    family_id = str(report["family_id"])
    expected = EXPECTED_CONTROL_BY_FAMILY[family_id]
    failures: list[str] = []
    for key, expected_value in expected.items():
        actual = report.get(key)
        if actual != expected_value:
            failures.append(f"{key}: expected={expected_value!r} actual={actual!r}")

    mismatch_stage_histogram: dict[str, int] = {}
    breach_in_f0_f12 = False
    for row in report.get("mismatch_rows") or []:
        stage = str(row.get("first_divergence_stage") or "")
        if not stage:
            continue
        mismatch_stage_histogram[stage] = mismatch_stage_histogram.get(stage, 0) + 1
        if stage in UPSTREAM_F0_F12_STAGES:
            breach_in_f0_f12 = True

    runtime_error_count = int(report.get("candidate_runtime_error_count", 0)) + int(
        report.get("reference_runtime_error_count", 0)
    )
    return {
        "family_id": family_id,
        "mismatch_count": int(report.get("mismatch_count", 0)),
        "runtime_error_count": runtime_error_count,
        "family_metric_delta_zero": bool(report.get("family_metric_delta_zero")),
        "mismatch_stage_histogram": mismatch_stage_histogram,
        "pass": len(failures) == 0,
        "failures": failures,
        "breach_in_f0_f12": breach_in_f0_f12,
    }


def build_summary(reports: list[dict[str, Any]]) -> dict[str, Any]:
    family_rows = [family_result(report) for report in sorted(reports, key=lambda item: family_sort_key(str(item["family_id"])))]
    payload = {
        "family_count": len(family_rows),
        "control_pair_runtime_error_count": sum(row["runtime_error_count"] for row in family_rows),
        "control_pair_authority_match": all(row["pass"] for row in family_rows),
        "control_pair_breach_in_f0_f12": any(row["breach_in_f0_f12"] for row in family_rows),
        "family_metric_delta_zero": all(row["family_metric_delta_zero"] for row in family_rows),
        "families": family_rows,
    }
    payload["wp3_pass"] = (
        payload["control_pair_runtime_error_count"] == 0
        and payload["control_pair_authority_match"]
        and not payload["control_pair_breach_in_f0_f12"]
        and payload["family_metric_delta_zero"]
    )
    payload["report_hash"] = stable_hash(payload)
    return payload


def render_markdown(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- family_count = `{summary['family_count']}`",
        f"- control_pair_runtime_error_count = `{summary['control_pair_runtime_error_count']}`",
        f"- control_pair_authority_match = `{bool_text(summary['control_pair_authority_match'])}`",
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
    parser = argparse.ArgumentParser(description="Build FAZ18 RC-G vs RC-J control authority summary.")
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
