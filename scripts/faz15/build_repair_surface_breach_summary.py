#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz15_lib import (  # noqa: E402
    FINAL_MODE_RESIDUAL_QUESTION_ID,
    NEXT_WORK_BY_ROOT_CAUSE,
    TARGETED_QUESTION_IDS,
    load_json,
    mismatch_index,
    o_stage_to_f_stage,
    pick_dominant,
    stable_hash,
    write_json,
)


def _infer_row(
    *,
    family_id: str,
    question_id: str,
    ordinal_index: int,
    rc_g_vs_rc_l: dict[str, Any] | None,
    rc_j_vs_rc_l: dict[str, Any] | None,
    control_pair_authority_match: bool,
    context_shift_ids: set[str],
) -> dict[str, Any]:
    o_stage_left = rc_g_vs_rc_l.get("first_divergence_stage") if rc_g_vs_rc_l else None
    o_stage_right = rc_j_vs_rc_l.get("first_divergence_stage") if rc_j_vs_rc_l else None
    o_stage = o_stage_left or o_stage_right
    pair_symmetry = bool(o_stage_left and o_stage_right and o_stage_left == o_stage_right)
    pair_asymmetry = int(not pair_symmetry)

    if family_id == "faz1-50" and question_id == FINAL_MODE_RESIDUAL_QUESTION_ID and o_stage == "final_mode_mapping_hash":
        f_stage = "final_mode_mapping_hash"
        primary_reason = "final_mode_residual"
        root_cause_class = "localized_final_mode_residual"
    elif family_id == "v3-170" and question_id in context_shift_ids and o_stage in {
        "model_request_payload_hash",
        "generation_contract_hash",
        "preprojection_anchor_hash",
        "normalized_request_hash",
    }:
        f_stage = "question_batch_context_hash"
        primary_reason = "batch_context_delta"
        root_cause_class = "full_family_context_breach"
    elif not control_pair_authority_match and o_stage in {
        "normalized_request_hash",
        "model_request_payload_hash",
        "generation_contract_hash",
        "preprojection_anchor_hash",
        "cited_projection_hash",
        "citation_set_projection_hash",
    }:
        f_stage = o_stage_to_f_stage(o_stage)
        primary_reason = "request_payload_authority_breach"
        root_cause_class = "control_pair_authority_breach"
    elif pair_symmetry and control_pair_authority_match and o_stage == "model_request_payload_hash":
        f_stage = "model_request_payload_hash"
        primary_reason = "request_payload_authority_breach"
        root_cause_class = "request_payload_authority_breach_from_rc_l"
    elif pair_symmetry and control_pair_authority_match and o_stage == "generation_contract_hash":
        f_stage = "generation_contract_hash"
        primary_reason = "generation_contract_follow_on"
        root_cause_class = "request_payload_authority_breach_from_rc_l"
    elif pair_symmetry and control_pair_authority_match and o_stage == "preprojection_anchor_hash":
        f_stage = "preprojection_anchor_hash"
        primary_reason = "preprojection_follow_on"
        root_cause_class = "request_payload_authority_breach_from_rc_l"
    elif pair_symmetry and o_stage == "final_mode_mapping_hash":
        f_stage = "final_mode_mapping_hash"
        primary_reason = "final_mode_residual"
        root_cause_class = "localized_final_mode_residual"
    elif pair_symmetry and o_stage:
        f_stage = o_stage_to_f_stage(o_stage)
        primary_reason = "manifest_materialization_delta"
        root_cause_class = "rc_l_build_surface_breach"
    else:
        f_stage = o_stage_to_f_stage(o_stage)
        primary_reason = "unexplained_repair_surface_breach"
        root_cause_class = "unexplained_repair_surface_breach"

    return {
        "family_id": family_id,
        "question_id": question_id,
        "ordinal_index": ordinal_index,
        "first_divergence_stage_f": f_stage,
        "first_divergence_stage_o": o_stage,
        "primary_reason": primary_reason,
        "root_cause_class": root_cause_class,
        "pair_symmetry": int(pair_symmetry),
        "pair_asymmetry": pair_asymmetry,
        "rc_g_vs_rc_l_stage": o_stage_left,
        "rc_j_vs_rc_l_stage": o_stage_right,
    }


def build_outputs(
    *,
    rc_g_vs_rc_l_reports: list[dict[str, Any]],
    rc_j_vs_rc_l_reports: list[dict[str, Any]],
    control_summary: dict[str, Any],
    context_contrast: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    rc_g_index: dict[tuple[str, str], dict[str, Any]] = {}
    rc_j_index: dict[tuple[str, str], dict[str, Any]] = {}
    for report in rc_g_vs_rc_l_reports:
        rc_g_index.update(mismatch_index(report))
    for report in rc_j_vs_rc_l_reports:
        rc_j_index.update(mismatch_index(report))

    expected_frontier_count = len(rc_g_index)
    context_shift_ids = {
        row["question_id"]
        for row in context_contrast.get("rows", [])
        if isinstance(row, dict) and row.get("stage_shift")
    }
    control_pair_authority_match = bool(control_summary.get("control_pair_authority_match"))

    union_keys = sorted(set(rc_g_index) | set(rc_j_index), key=lambda item: (item[0], item[1]))
    rows = []
    stage_histogram_f: Counter[str] = Counter()
    stage_histogram_o: Counter[str] = Counter()
    reason_histogram: Counter[str] = Counter()
    root_cause_histogram: Counter[str] = Counter()
    pair_symmetry_count = 0
    pair_asymmetry_count = 0
    unexplained_count = 0

    for family_id, question_id in union_keys:
        base = rc_g_index.get((family_id, question_id)) or rc_j_index.get((family_id, question_id))
        row = _infer_row(
            family_id=family_id,
            question_id=question_id,
            ordinal_index=int(base["ordinal_index"]),
            rc_g_vs_rc_l=rc_g_index.get((family_id, question_id)),
            rc_j_vs_rc_l=rc_j_index.get((family_id, question_id)),
            control_pair_authority_match=control_pair_authority_match,
            context_shift_ids=context_shift_ids,
        )
        rows.append(row)
        if row["first_divergence_stage_f"]:
            stage_histogram_f[row["first_divergence_stage_f"]] += 1
        if row["first_divergence_stage_o"]:
            stage_histogram_o[row["first_divergence_stage_o"]] += 1
        if row["primary_reason"]:
            reason_histogram[row["primary_reason"]] += 1
        if row["root_cause_class"]:
            root_cause_histogram[row["root_cause_class"]] += 1
        if row["pair_symmetry"]:
            pair_symmetry_count += 1
        else:
            pair_asymmetry_count += 1
        if row["root_cause_class"] == "unexplained_repair_surface_breach":
            unexplained_count += 1

    dominant_root_cause_class = pick_dominant(dict(root_cause_histogram))
    summary = {
        "frontier_count": len(rows),
        "expected_frontier_count": expected_frontier_count,
        "frontier_count_matches_reference": len(rows) == expected_frontier_count,
        "rc_g_vs_rc_l_first_divergence_assigned_count": sum(1 for row in rows if row["rc_g_vs_rc_l_stage"]),
        "rc_j_vs_rc_l_first_divergence_assigned_count": sum(1 for row in rows if row["rc_j_vs_rc_l_stage"]),
        "primary_reason_assigned_count": sum(1 for row in rows if row["primary_reason"]),
        "root_cause_class_assigned_count": sum(1 for row in rows if row["root_cause_class"]),
        "pair_symmetry_count": pair_symmetry_count,
        "pair_asymmetry_count": pair_asymmetry_count,
        "unexplained_count": unexplained_count,
        "dominant_root_cause_class": dominant_root_cause_class,
        "stage_histogram_f": dict(stage_histogram_f),
        "stage_histogram_o": dict(stage_histogram_o),
        "reason_histogram": dict(reason_histogram),
        "root_cause_histogram": dict(root_cause_histogram),
        "rows": rows,
    }
    summary["report_hash"] = stable_hash({k: v for k, v in summary.items() if k != "rows"})

    first_divergence_table = {
        "frontier_count": len(rows),
        "rows": rows,
    }
    first_divergence_table["report_hash"] = stable_hash({k: v for k, v in first_divergence_table.items() if k != "rows"})

    root_cause_mapping = {
        "frontier_count": len(rows),
        "rows": rows,
        "dominant_root_cause_class": dominant_root_cause_class,
    }
    root_cause_mapping["report_hash"] = stable_hash({k: v for k, v in root_cause_mapping.items() if k != "rows"})

    if unexplained_count == 0 and summary["root_cause_class_assigned_count"] == len(rows):
        official_decision = "PASS - Repair Surface Breach Localized"
    else:
        official_decision = "NO-GO - Unexplained Repair Surface Breach"
    next_official_work = NEXT_WORK_BY_ROOT_CAUSE.get(dominant_root_cause_class, "manual steering required")
    reconciliation = {
        "control_pair_authority_match": control_pair_authority_match,
        "targeted_vs_full_family_context_shift_detected": bool(
            context_contrast.get("targeted_vs_full_family_context_shift_detected")
        ),
        "frontier_count": len(rows),
        "unexplained_count": unexplained_count,
        "dominant_root_cause_class": dominant_root_cause_class,
        "official_decision": official_decision,
        "next_official_work": next_official_work,
    }
    reconciliation["report_hash"] = stable_hash(reconciliation)
    return summary, first_divergence_table, root_cause_mapping, reconciliation


def _render_rows(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| family | ordinal | question_id | rc_g_vs_rc_l_stage | rc_j_vs_rc_l_stage | first_divergence_stage_f | first_divergence_stage_o | primary_reason | root_cause_class |",
        "| --- | ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['family_id']} | {row['ordinal_index']} | {row['question_id']} | "
            f"{row['rc_g_vs_rc_l_stage']} | {row['rc_j_vs_rc_l_stage']} | "
            f"{row['first_divergence_stage_f']} | {row['first_divergence_stage_o']} | "
            f"{row['primary_reason']} | {row['root_cause_class']} |"
        )
    lines.append("")
    return lines


def render_summary_md(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- frontier_count = `{summary['frontier_count']}`",
        f"- expected_frontier_count = `{summary['expected_frontier_count']}`",
        f"- frontier_count_matches_reference = `{str(summary['frontier_count_matches_reference']).lower()}`",
        f"- rc_g_vs_rc_l_first_divergence_assigned_count = `{summary['rc_g_vs_rc_l_first_divergence_assigned_count']}`",
        f"- rc_j_vs_rc_l_first_divergence_assigned_count = `{summary['rc_j_vs_rc_l_first_divergence_assigned_count']}`",
        f"- primary_reason_assigned_count = `{summary['primary_reason_assigned_count']}`",
        f"- root_cause_class_assigned_count = `{summary['root_cause_class_assigned_count']}`",
        f"- pair_symmetry_count = `{summary['pair_symmetry_count']}`",
        f"- pair_asymmetry_count = `{summary['pair_asymmetry_count']}`",
        f"- unexplained_count = `{summary['unexplained_count']}`",
        f"- dominant_root_cause_class = `{summary['dominant_root_cause_class']}`",
        "",
        "## F Stage Histogram",
        "",
    ]
    for key, value in sorted(summary["stage_histogram_f"].items()):
        lines.append(f"- `{key}` = `{value}`")
    lines.extend(["", "## O Stage Histogram", ""])
    for key, value in sorted(summary["stage_histogram_o"].items()):
        lines.append(f"- `{key}` = `{value}`")
    lines.extend(["", "## Reason Histogram", ""])
    for key, value in sorted(summary["reason_histogram"].items()):
        lines.append(f"- `{key}` = `{value}`")
    lines.extend(["", "## Root Cause Histogram", ""])
    for key, value in sorted(summary["root_cause_histogram"].items()):
        lines.append(f"- `{key}` = `{value}`")
    lines.append("")
    return "\n".join(lines)


def render_table_md(table: dict[str, Any], *, title: str) -> str:
    return "\n".join([f"# {title}", ""] + _render_rows(table["rows"]))


def render_mapping_md(mapping: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- frontier_count = `{mapping['frontier_count']}`",
        f"- dominant_root_cause_class = `{mapping['dominant_root_cause_class']}`",
        "",
    ]
    lines.extend(_render_rows(mapping["rows"]))
    return "\n".join(lines)


def render_reconciliation_md(reconciliation: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- control_pair_authority_match = `{str(reconciliation['control_pair_authority_match']).lower()}`",
        f"- targeted_vs_full_family_context_shift_detected = `{str(reconciliation['targeted_vs_full_family_context_shift_detected']).lower()}`",
        f"- frontier_count = `{reconciliation['frontier_count']}`",
        f"- unexplained_count = `{reconciliation['unexplained_count']}`",
        f"- dominant_root_cause_class = `{reconciliation['dominant_root_cause_class']}`",
        f"- official_decision = `{reconciliation['official_decision']}`",
        f"- next_official_work = `{reconciliation['next_official_work']}`",
        "",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ15 repair surface breach summary.")
    parser.add_argument("--rc-g-vs-rc-l-report-json", type=Path, action="append", required=True)
    parser.add_argument("--rc-j-vs-rc-l-report-json", type=Path, action="append", required=True)
    parser.add_argument("--control-summary-json", type=Path, required=True)
    parser.add_argument("--context-contrast-json", type=Path, required=True)
    parser.add_argument("--summary-output-json", type=Path, required=True)
    parser.add_argument("--summary-output-md", type=Path, required=True)
    parser.add_argument("--table-output-json", type=Path, required=True)
    parser.add_argument("--table-output-md", type=Path, required=True)
    parser.add_argument("--mapping-output-json", type=Path, required=True)
    parser.add_argument("--mapping-output-md", type=Path, required=True)
    parser.add_argument("--reconciliation-output-json", type=Path, required=True)
    parser.add_argument("--reconciliation-output-md", type=Path, required=True)
    parser.add_argument("--summary-title", required=True)
    parser.add_argument("--table-title", required=True)
    parser.add_argument("--mapping-title", required=True)
    parser.add_argument("--reconciliation-title", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary, table, mapping, reconciliation = build_outputs(
        rc_g_vs_rc_l_reports=[load_json(path) for path in args.rc_g_vs_rc_l_report_json],
        rc_j_vs_rc_l_reports=[load_json(path) for path in args.rc_j_vs_rc_l_report_json],
        control_summary=load_json(args.control_summary_json),
        context_contrast=load_json(args.context_contrast_json),
    )
    write_json(args.summary_output_json, summary)
    write_json(args.table_output_json, table)
    write_json(args.mapping_output_json, mapping)
    write_json(args.reconciliation_output_json, reconciliation)
    args.summary_output_md.write_text(render_summary_md(summary, title=args.summary_title), encoding="utf-8")
    args.table_output_md.write_text(render_table_md(table, title=args.table_title), encoding="utf-8")
    args.mapping_output_md.write_text(render_mapping_md(mapping, title=args.mapping_title), encoding="utf-8")
    args.reconciliation_output_md.write_text(
        render_reconciliation_md(reconciliation, title=args.reconciliation_title),
        encoding="utf-8",
    )
    return 0 if reconciliation["official_decision"] == "PASS - Repair Surface Breach Localized" else 1


if __name__ == "__main__":
    raise SystemExit(main())
