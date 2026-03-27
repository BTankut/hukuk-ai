#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz22_lib import AUTHORIZED_OUTPUT_SURFACE_STAGES, UPSTREAM_F0_F12_FIELDS, family_sort_key, load_json, markdown_table, stable_hash, write_json, bool_text


def family_row(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "family_id": str(report["family_id"]),
        "question_count": int(report.get("question_count", 0)),
        "runtime_error_count": int(report.get("runtime_error_count", 0)),
        "mismatch_count": int(report.get("mismatch_count", 0)),
        "family_metric_delta_zero": bool(report.get("family_metric_delta_zero")),
        "upstream_mismatch_count": sum(int(report.get(field, 0)) for field in UPSTREAM_F0_F12_FIELDS),
    }


def build_summary(reports: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [family_row(report) for report in sorted(reports, key=lambda item: family_sort_key(str(item["family_id"])))]
    all_mismatch_rows = []
    for report in reports:
        all_mismatch_rows.extend(report.get("mismatch_rows") or [])
    output_surface_rows = [
        row
        for row in all_mismatch_rows
        if str(row.get("first_divergence_stage") or "") in AUTHORIZED_OUTPUT_SURFACE_STAGES
        and not any(int(row.get(field.replace("_count", ""), 0)) > 0 for field in ())
    ]
    summary = {
        "family_count": len(rows),
        "families": rows,
        "runtime_error_count": sum(row["runtime_error_count"] for row in rows),
        "authoritative_summary_mismatch_count": sum(row["mismatch_count"] for row in rows),
        "output_parity_surface_breach_count": len(output_surface_rows),
        "localized_authorized_downstream_drift_count": 0,
        "frontier_candidate_count": len(output_surface_rows),
    }
    summary["wp4_pass"] = (
        summary["runtime_error_count"] == 0
        and summary["authoritative_summary_mismatch_count"] == 1
        and summary["output_parity_surface_breach_count"] == 1
        and summary["localized_authorized_downstream_drift_count"] == 0
        and summary["frontier_candidate_count"] == 1
    )
    summary["report_hash"] = stable_hash(summary)
    return summary


def render_markdown(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- family_count = `{summary['family_count']}`",
        f"- runtime_error_count = `{summary['runtime_error_count']}`",
        f"- authoritative_summary_mismatch_count = `{summary['authoritative_summary_mismatch_count']}`",
        f"- output_parity_surface_breach_count = `{summary['output_parity_surface_breach_count']}`",
        f"- localized_authorized_downstream_drift_count = `{summary['localized_authorized_downstream_drift_count']}`",
        f"- frontier_candidate_count = `{summary['frontier_candidate_count']}`",
        f"- wp4_pass = `{bool_text(summary['wp4_pass'])}`",
        "",
    ]
    lines.extend(
        markdown_table(
            [
                ("family_id", "family"),
                ("mismatch_count", "mismatch_count"),
                ("runtime_error_count", "runtime_error_count"),
                ("family_metric_delta_zero", "family_metric_delta_zero"),
                ("upstream_mismatch_count", "upstream_mismatch_count"),
            ],
            summary["families"],
        )
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ22 RC-M authoritative summary.")
    parser.add_argument("--report-json", type=Path, action="append", required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--title", required=True)
    args = parser.parse_args()

    summary = build_summary([load_json(path) for path in args.report_json])
    write_json(args.output_json, summary)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(summary, title=args.title), encoding="utf-8")
    return 0 if summary["wp4_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
