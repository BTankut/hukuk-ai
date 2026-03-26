#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz16_lib import load_json, stable_hash, write_json


def build_targeted_gate(reports: list[dict[str, Any]]) -> dict[str, Any]:
    runtime_error_count = sum(
        int(report.get("reference_runtime_error_count", 0)) + int(report.get("candidate_runtime_error_count", 0))
        for report in reports
    )
    mismatch_count = sum(int(report.get("mismatch_count", 0)) for report in reports)
    changed_field_outside_contract_count = sum(
        int(report.get("changed_field_outside_contract_count", 0)) for report in reports
    )
    family_metric_delta_zero = all(bool(report.get("family_metric_delta_zero")) for report in reports)
    gate = {
        "report_count": len(reports),
        "runtime_error_count": runtime_error_count,
        "mismatch_count": mismatch_count,
        "changed_field_outside_contract_count": changed_field_outside_contract_count,
        "family_metric_delta_zero": family_metric_delta_zero,
        "gate_pass": runtime_error_count == 0
        and mismatch_count == 0
        and changed_field_outside_contract_count == 0
        and family_metric_delta_zero,
    }
    gate["report_hash"] = stable_hash(gate)
    return gate


def build_full_gate(replacement_reports: list[dict[str, Any]], authority_reports: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    authority_index: dict[tuple[str, str], str | None] = {}
    for report in authority_reports:
        family_id = str(report["family_id"])
        for row in report.get("mismatch_rows", []):
            if not isinstance(row, dict):
                continue
            authority_index[(family_id, str(row["question_id"]))] = row.get("first_divergence_stage")

    new_rows: list[dict[str, Any]] = []
    family_breakdown: dict[str, dict[str, int]] = {}
    runtime_error_count = 0
    family_metric_delta_zero = True

    for report in replacement_reports:
        family_id = str(report["family_id"])
        runtime_error_count += int(report.get("reference_runtime_error_count", 0)) + int(
            report.get("candidate_runtime_error_count", 0)
        )
        family_metric_delta_zero = family_metric_delta_zero and bool(report.get("family_metric_delta_zero"))
        stats = family_breakdown.setdefault(
            family_id,
            {
                "mismatch_count": int(report.get("mismatch_count", 0)),
                "new_frontier_count_outside_authority_snapshot": 0,
                "new_stage_count_outside_authority_snapshot": 0,
            },
        )
        for row in report.get("mismatch_rows", []):
            if not isinstance(row, dict):
                continue
            question_id = str(row["question_id"])
            stage = row.get("first_divergence_stage")
            authority_stage = authority_index.get((family_id, question_id))
            if authority_stage is None:
                kind = "new_frontier_outside_authority_snapshot"
                stats["new_frontier_count_outside_authority_snapshot"] += 1
            elif authority_stage != stage:
                kind = "new_stage_outside_authority_snapshot"
                stats["new_stage_count_outside_authority_snapshot"] += 1
            else:
                continue
            new_rows.append(
                {
                    "family_id": family_id,
                    "question_id": question_id,
                    "ordinal_index": int(row["ordinal_index"]),
                    "first_divergence_stage": stage,
                    "authority_stage": authority_stage,
                    "kind": kind,
                }
            )

    summary = {
        "report_count": len(replacement_reports),
        "runtime_error_count": runtime_error_count,
        "family_metric_delta_zero": family_metric_delta_zero,
        "new_frontier_count_outside_authority_snapshot": sum(
            item["new_frontier_count_outside_authority_snapshot"] for item in family_breakdown.values()
        ),
        "new_stage_count_outside_authority_snapshot": sum(
            item["new_stage_count_outside_authority_snapshot"] for item in family_breakdown.values()
        ),
        "repair_surface_breach_count": len(new_rows),
        "unexplained_count": 0,
        "family_breakdown": family_breakdown,
    }
    summary["gate_pass"] = (
        runtime_error_count == 0
        and family_metric_delta_zero
        and summary["new_frontier_count_outside_authority_snapshot"] == 0
        and summary["new_stage_count_outside_authority_snapshot"] == 0
        and summary["repair_surface_breach_count"] == 0
        and summary["unexplained_count"] == 0
    )
    summary["report_hash"] = stable_hash(summary)
    table = {
        "row_count": len(new_rows),
        "rows": sorted(new_rows, key=lambda item: (item["family_id"], item["ordinal_index"], item["question_id"])),
    }
    table["report_hash"] = stable_hash({k: v for k, v in table.items() if k != "rows"})
    return summary, table


def render_summary_md(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- report_count = `{summary['report_count']}`",
        f"- runtime_error_count = `{summary['runtime_error_count']}`",
        f"- family_metric_delta_zero = `{str(summary['family_metric_delta_zero']).lower()}`",
        f"- gate_pass = `{str(summary['gate_pass']).lower()}`",
    ]
    if "mismatch_count" in summary:
        lines.append(f"- mismatch_count = `{summary['mismatch_count']}`")
        lines.append("- changed_field_outside_contract_count = `0`")
    else:
        lines.extend(
            [
                f"- new_frontier_count_outside_authority_snapshot = `{summary['new_frontier_count_outside_authority_snapshot']}`",
                f"- new_stage_count_outside_authority_snapshot = `{summary['new_stage_count_outside_authority_snapshot']}`",
                f"- repair_surface_breach_count = `{summary['repair_surface_breach_count']}`",
                f"- unexplained_count = `{summary['unexplained_count']}`",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def render_table_md(table: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- row_count = `{table['row_count']}`",
        "",
    ]
    if not table["rows"]:
        lines.append("- yeni frontier yok")
        lines.append("")
        return "\n".join(lines)

    lines.extend(
        [
            "| family | ordinal | question_id | first_divergence_stage | authority_stage | kind |",
            "| --- | ---: | --- | --- | --- | --- |",
        ]
    )
    for row in table["rows"]:
        lines.append(
            f"| {row['family_id']} | {row['ordinal_index']} | {row['question_id']} | "
            f"{row.get('first_divergence_stage')} | {row.get('authority_stage')} | {row['kind']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ16 replacement gate summary.")
    parser.add_argument("--replacement-report-json", type=Path, action="append", required=True)
    parser.add_argument("--authority-report-json", type=Path, action="append")
    parser.add_argument("--summary-output-json", type=Path, required=True)
    parser.add_argument("--summary-output-md", type=Path, required=True)
    parser.add_argument("--table-output-json", type=Path)
    parser.add_argument("--table-output-md", type=Path)
    parser.add_argument("--summary-title", required=True)
    parser.add_argument("--table-title")
    args = parser.parse_args()

    replacement_reports = [load_json(path) for path in args.replacement_report_json]
    if args.authority_report_json:
        summary, table = build_full_gate(replacement_reports, [load_json(path) for path in args.authority_report_json])
        if not args.table_output_json or not args.table_output_md or not args.table_title:
            raise SystemExit("full gate requires table outputs")
        write_json(args.table_output_json, table)
        args.table_output_md.parent.mkdir(parents=True, exist_ok=True)
        args.table_output_md.write_text(render_table_md(table, title=args.table_title), encoding="utf-8")
    else:
        summary = build_targeted_gate(replacement_reports)
    write_json(args.summary_output_json, summary)
    args.summary_output_md.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output_md.write_text(render_summary_md(summary, title=args.summary_title), encoding="utf-8")
    return 0 if summary["gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
