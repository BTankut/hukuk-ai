#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz16_lib import ALLOWED_CHANGED_FIELDS, UPSTREAM_MISMATCH_KEYS, load_json, stable_hash, write_json


def _row_has_upstream_breach(row: dict[str, Any]) -> bool:
    return any(int(row.get(key, 0)) == 1 for key in UPSTREAM_MISMATCH_KEYS)


def build_gate(reports: list[dict[str, Any]], *, allowed_question_ids: set[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    summary = {
        "report_count": len(reports),
        "question_count": 0,
        "runtime_error_count": 0,
        "mismatch_count": 0,
        "normalized_request_hash_mismatch_count": 0,
        "model_request_payload_hash_mismatch_count": 0,
        "generation_contract_hash_mismatch_count": 0,
        "preprojection_anchor_mismatch_count": 0,
        "cited_projection_hash_mismatch_count": 0,
        "citation_set_projection_hash_mismatch_count": 0,
        "final_mode_mapping_hash_mismatch_count": 0,
        "blocked_reason_set_mismatch_count": 0,
        "response_envelope_hash_mismatch_count": 0,
        "changed_field_outside_contract_count": 0,
        "changed_record_outside_authorized_set_count": 0,
        "repair_surface_breach_count": 0,
        "allowed_changed_field_set": sorted(ALLOWED_CHANGED_FIELDS),
        "allowed_changed_record_set": sorted(allowed_question_ids),
        "family_breakdown": {},
    }
    outside_fields_union: set[str] = set()

    for report in reports:
        family_id = str(report["family_id"])
        summary["question_count"] += int(report.get("question_count", 0))
        summary["runtime_error_count"] += int(report.get("runtime_error_count", 0))
        summary["mismatch_count"] += int(report.get("mismatch_count", 0))
        for key in (
            "normalized_request_hash_mismatch_count",
            "model_request_payload_hash_mismatch_count",
            "generation_contract_hash_mismatch_count",
            "preprojection_anchor_mismatch_count",
            "cited_projection_hash_mismatch_count",
            "citation_set_projection_hash_mismatch_count",
            "final_mode_mapping_hash_mismatch_count",
            "blocked_reason_set_mismatch_count",
            "response_envelope_hash_mismatch_count",
            "changed_field_outside_contract_count",
        ):
            summary[key] += int(report.get(key, 0))

        family_rows = 0
        for row in report.get("mismatch_rows", []):
            if not isinstance(row, dict):
                continue
            changed_field_set = sorted(str(item) for item in row.get("changed_field_set", []))
            outside_contract = sorted(str(item) for item in row.get("changed_field_outside_contract", []))
            outside_record = str(row.get("question_id")) not in allowed_question_ids
            breach = outside_record or bool(outside_contract) or _row_has_upstream_breach(row)
            family_rows += 1
            if outside_record:
                summary["changed_record_outside_authorized_set_count"] += 1
            if breach:
                summary["repair_surface_breach_count"] += 1
            outside_fields_union.update(outside_contract)
            rows.append(
                {
                    "family_id": family_id,
                    "question_id": str(row["question_id"]),
                    "ordinal_index": int(row["ordinal_index"]),
                    "first_divergence_stage": row.get("first_divergence_stage"),
                    "primary_reason": row.get("primary_reason"),
                    "changed_field_set": changed_field_set,
                    "changed_field_outside_contract": outside_contract,
                    "outside_authorized_record_set": outside_record,
                    "repair_surface_breach": breach,
                }
            )
        summary["family_breakdown"][family_id] = family_rows

    summary["changed_field_outside_contract"] = sorted(outside_fields_union)
    summary["gate_pass"] = (
        summary["runtime_error_count"] == 0
        and summary["normalized_request_hash_mismatch_count"] == 0
        and summary["model_request_payload_hash_mismatch_count"] == 0
        and summary["generation_contract_hash_mismatch_count"] == 0
        and summary["preprojection_anchor_mismatch_count"] == 0
        and summary["cited_projection_hash_mismatch_count"] == 0
        and summary["citation_set_projection_hash_mismatch_count"] == 0
        and summary["changed_field_outside_contract_count"] == 0
        and summary["changed_record_outside_authorized_set_count"] == 0
        and summary["repair_surface_breach_count"] == 0
    )
    summary["report_hash"] = stable_hash(summary)
    table = {
        "row_count": len(rows),
        "rows": sorted(rows, key=lambda item: (item["family_id"], item["ordinal_index"], item["question_id"])),
    }
    table["report_hash"] = stable_hash({k: v for k, v in table.items() if k != "rows"})
    return summary, table


def render_summary_md(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- report_count = `{summary['report_count']}`",
        f"- question_count = `{summary['question_count']}`",
        f"- runtime_error_count = `{summary['runtime_error_count']}`",
        f"- mismatch_count = `{summary['mismatch_count']}`",
        f"- gate_pass = `{str(summary['gate_pass']).lower()}`",
        f"- changed_field_outside_contract_count = `{summary['changed_field_outside_contract_count']}`",
        f"- changed_record_outside_authorized_set_count = `{summary['changed_record_outside_authorized_set_count']}`",
        f"- repair_surface_breach_count = `{summary['repair_surface_breach_count']}`",
        "",
    ]
    for key in (
        "normalized_request_hash_mismatch_count",
        "model_request_payload_hash_mismatch_count",
        "generation_contract_hash_mismatch_count",
        "preprojection_anchor_mismatch_count",
        "cited_projection_hash_mismatch_count",
        "citation_set_projection_hash_mismatch_count",
        "final_mode_mapping_hash_mismatch_count",
        "blocked_reason_set_mismatch_count",
        "response_envelope_hash_mismatch_count",
    ):
        lines.append(f"- `{key}` = `{summary[key]}`")
    lines.append("")
    return "\n".join(lines)


def render_table_md(table: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- row_count = `{table['row_count']}`",
        "",
        "| family | ordinal | question_id | stage | reason | changed_field_set | outside_contract | outside_authorized_record_set | repair_surface_breach |",
        "| --- | ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in table["rows"]:
        lines.append(
            f"| {row['family_id']} | {row['ordinal_index']} | {row['question_id']} | "
            f"{row.get('first_divergence_stage')} | {row.get('primary_reason')} | "
            f"{row['changed_field_set']} | {row['changed_field_outside_contract']} | "
            f"{str(row['outside_authorized_record_set']).lower()} | {str(row['repair_surface_breach']).lower()} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ16 candidate isolation gate summary.")
    parser.add_argument("--report-json", type=Path, action="append", required=True)
    parser.add_argument("--allowed-question-id", action="append", required=True)
    parser.add_argument("--summary-output-json", type=Path, required=True)
    parser.add_argument("--summary-output-md", type=Path, required=True)
    parser.add_argument("--table-output-json", type=Path, required=True)
    parser.add_argument("--table-output-md", type=Path, required=True)
    parser.add_argument("--summary-title", required=True)
    parser.add_argument("--table-title", required=True)
    args = parser.parse_args()

    summary, table = build_gate(
        [load_json(path) for path in args.report_json],
        allowed_question_ids={item.strip() for item in args.allowed_question_id if item.strip()},
    )
    write_json(args.summary_output_json, summary)
    write_json(args.table_output_json, table)
    args.summary_output_md.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output_md.write_text(render_summary_md(summary, title=args.summary_title), encoding="utf-8")
    args.table_output_md.write_text(render_table_md(table, title=args.table_title), encoding="utf-8")
    return 0 if summary["gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

