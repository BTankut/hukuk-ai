#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz22_lib import (
    AUTHORIZED_OUTPUT_SURFACE_STAGES,
    F_STAGE_CODE,
    F_TO_O_STAGE,
    UPSTREAM_F0_F12_FIELDS,
    family_sort_key,
    load_json,
    markdown_table,
    stable_hash,
    stage_label,
    write_json,
    bool_text,
)


def _sort_row(row: dict[str, Any]) -> tuple[int, int, str]:
    return (
        family_sort_key(str(row.get("family_id")))[0],
        int(row.get("ordinal_index", 999999)),
        str(row.get("question_id", "")),
    )


def _diagnostic_indexes(report: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    authoritative = {
        str(row.get("question_id")): row
        for row in report.get("authoritative_rows") or []
        if isinstance(row, dict) and row.get("question_id")
    }
    mismatches = {
        str(row.get("question_id")): row
        for row in report.get("mismatch_rows") or []
        if isinstance(row, dict) and row.get("question_id")
    }
    return authoritative, mismatches


def build_payload(
    *,
    control_summary: dict[str, Any],
    authoritative_reports: list[dict[str, Any]],
    diagnostic_reports: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    mismatch_rows = []
    for report in sorted(authoritative_reports, key=lambda item: family_sort_key(str(item.get("family_id")))):
        mismatch_rows.extend(report.get("mismatch_rows") or [])
    mismatch_rows = sorted((dict(row) for row in mismatch_rows), key=_sort_row)

    diagnostic_by_family = {str(report.get("family_id")): report for report in diagnostic_reports}

    frontier_rows = []
    diagnostic_rows = []
    root_cause_rows = []
    first_divergence_assigned_count = 0
    primary_reason_assigned_count = 0
    root_cause_class_assigned_count = 0
    rc_j_vs_rc_m_runtime_error_count = 0

    canonical_current_authority_contract_breach = not bool(control_summary.get("wp3_pass"))

    for row in mismatch_rows:
        family_id = str(row.get("family_id"))
        question_id = str(row.get("question_id"))
        stage_name = str(row.get("first_divergence_stage") or "")
        reason = str(row.get("primary_reason") or "")
        f_stage = stage_label(stage_name, F_STAGE_CODE)
        o_stage = stage_label(stage_name, F_TO_O_STAGE)
        stage_outside_authorized_output_surface = stage_name not in AUTHORIZED_OUTPUT_SURFACE_STAGES
        surface_breach_regression = any(int(row.get(field.replace("_count", ""), 0)) > 0 for field in ())
        if stage_name in {name for name, code in F_STAGE_CODE.items() if code in {f"F{i}" for i in range(13)}}:
            surface_breach_regression = True

        if canonical_current_authority_contract_breach:
            root_cause_class = "canonical_current_authority_contract_breach"
        elif surface_breach_regression:
            root_cause_class = "surface_breach_regression"
        elif stage_outside_authorized_output_surface:
            root_cause_class = "stage_outside_authorized_output_surface"
        elif stage_name:
            root_cause_class = "authorized_output_surface_delta"
        else:
            root_cause_class = "unexplained_output_parity_surface_breach"

        diag_report = diagnostic_by_family.get(family_id, {})
        diag_auth, diag_mismatch = _diagnostic_indexes(diag_report)
        diag_auth_row = diag_auth.get(question_id, {})
        diag_mismatch_row = diag_mismatch.get(question_id, {})
        diagnostic_runtime_error = int(diag_auth_row.get("runtime_error", 0)) + int(
            diag_auth_row.get("reference_runtime_error", 0)
        )
        rc_j_vs_rc_m_runtime_error_count += diagnostic_runtime_error

        frontier_record_id = f"{family_id}/{question_id}"
        first_divergence_assigned_count += int(bool(f_stage))
        primary_reason_assigned_count += int(bool(reason))
        root_cause_class_assigned_count += int(bool(root_cause_class))

        frontier_rows.append(
            {
                "frontier_record_id": frontier_record_id,
                "frontier_family": family_id,
                "frontier_ordinal": int(row.get("ordinal_index", 0)),
                "frontier_question_id": question_id,
                "first_divergence_stage_f": f_stage,
                "first_divergence_stage_o": o_stage,
                "primary_reason": reason,
                "root_cause_class": root_cause_class,
                "stage_outside_authorized_output_surface": stage_outside_authorized_output_surface,
                "surface_breach_regression": surface_breach_regression,
                "canonical_current_authority_contract_breach": canonical_current_authority_contract_breach,
            }
        )
        diagnostic_rows.append(
            {
                "family_id": family_id,
                "question_id": question_id,
                "ordinal_index": int(row.get("ordinal_index", 0)),
                "diagnostic_runtime_error": diagnostic_runtime_error,
                "diagnostic_mismatch_present": question_id in diag_mismatch,
                "diagnostic_first_divergence_stage": diag_mismatch_row.get("first_divergence_stage"),
                "changed_field_set": diag_auth_row.get("changed_field_set", []),
                "changed_field_outside_contract": diag_auth_row.get("changed_field_outside_contract", []),
            }
        )
        root_cause_rows.append(frontier_rows[-1])

    frontier_count = len(frontier_rows)
    unexplained_count = frontier_count - min(
        frontier_count, first_divergence_assigned_count, primary_reason_assigned_count, root_cause_class_assigned_count
    )

    mismatch_table = {
        "frontier_count": frontier_count,
        "rows": mismatch_rows,
        "report_hash": stable_hash({"frontier_count": frontier_count, "rows": mismatch_rows}),
    }
    frontier_pack = {
        "frontier_count": frontier_count,
        "rows": frontier_rows,
        "report_hash": stable_hash({"frontier_count": frontier_count, "rows": frontier_rows}),
    }
    frontier_replay = {
        "frontier_count": frontier_count,
        "first_divergence_assigned_count": first_divergence_assigned_count,
        "primary_reason_assigned_count": primary_reason_assigned_count,
        "root_cause_class_assigned_count": root_cause_class_assigned_count,
        "unexplained_count": unexplained_count,
        "rc_j_vs_rc_m_runtime_error_count": rc_j_vs_rc_m_runtime_error_count,
        "rows": frontier_rows,
        "wp5_pass": (
            frontier_count == 1
            and first_divergence_assigned_count == 1
            and primary_reason_assigned_count == 1
            and root_cause_class_assigned_count == 1
            and unexplained_count == 0
            and rc_j_vs_rc_m_runtime_error_count == 0
        ),
    }
    diagnostic_summary = {
        "frontier_count": frontier_count,
        "rc_j_vs_rc_m_runtime_error_count": rc_j_vs_rc_m_runtime_error_count,
        "rows": diagnostic_rows,
        "report_hash": stable_hash({"frontier_count": frontier_count, "rows": diagnostic_rows}),
    }
    root_cause_table = {
        "frontier_count": frontier_count,
        "unexplained_count": unexplained_count,
        "rows": root_cause_rows,
        "report_hash": stable_hash({"frontier_count": frontier_count, "rows": root_cause_rows}),
    }
    return mismatch_table, frontier_pack, frontier_replay, diagnostic_summary, root_cause_table


def render_mismatch_table(payload: dict[str, Any], *, title: str) -> str:
    lines = [f"# {title}", "", f"- frontier_count = `{payload['frontier_count']}`", ""]
    lines.extend(
        markdown_table(
            [
                ("family_id", "family"),
                ("question_id", "question_id"),
                ("ordinal_index", "ordinal"),
                ("first_divergence_stage", "first_divergence_stage"),
                ("primary_reason", "primary_reason"),
            ],
            payload["rows"],
        )
    )
    lines.append("")
    return "\n".join(lines)


def render_frontier_pack(payload: dict[str, Any], *, title: str) -> str:
    lines = [f"# {title}", "", f"- frontier_count = `{payload['frontier_count']}`", ""]
    lines.extend(
        markdown_table(
            [
                ("frontier_record_id", "frontier_record_id"),
                ("frontier_family", "frontier_family"),
                ("frontier_question_id", "frontier_question_id"),
                ("frontier_ordinal", "frontier_ordinal"),
                ("first_divergence_stage_f", "first_divergence_stage_f"),
                ("first_divergence_stage_o", "first_divergence_stage_o"),
            ],
            payload["rows"],
        )
    )
    lines.append("")
    return "\n".join(lines)


def render_frontier_replay(payload: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- frontier_count = `{payload['frontier_count']}`",
        f"- first_divergence_assigned_count = `{payload['first_divergence_assigned_count']}`",
        f"- primary_reason_assigned_count = `{payload['primary_reason_assigned_count']}`",
        f"- root_cause_class_assigned_count = `{payload['root_cause_class_assigned_count']}`",
        f"- unexplained_count = `{payload['unexplained_count']}`",
        f"- rc_j_vs_rc_m_runtime_error_count = `{payload['rc_j_vs_rc_m_runtime_error_count']}`",
        f"- wp5_pass = `{bool_text(payload['wp5_pass'])}`",
        "",
    ]
    lines.extend(
        markdown_table(
            [
                ("frontier_record_id", "frontier_record_id"),
                ("first_divergence_stage_f", "first_divergence_stage_f"),
                ("first_divergence_stage_o", "first_divergence_stage_o"),
                ("primary_reason", "primary_reason"),
                ("root_cause_class", "root_cause_class"),
            ],
            payload["rows"],
        )
    )
    lines.append("")
    return "\n".join(lines)


def render_diagnostic_summary(payload: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- frontier_count = `{payload['frontier_count']}`",
        f"- rc_j_vs_rc_m_runtime_error_count = `{payload['rc_j_vs_rc_m_runtime_error_count']}`",
        "",
    ]
    lines.extend(
        markdown_table(
            [
                ("family_id", "family"),
                ("question_id", "question_id"),
                ("ordinal_index", "ordinal"),
                ("diagnostic_runtime_error", "diagnostic_runtime_error"),
                ("diagnostic_mismatch_present", "diagnostic_mismatch_present"),
                ("diagnostic_first_divergence_stage", "diagnostic_first_divergence_stage"),
            ],
            payload["rows"],
        )
    )
    lines.append("")
    return "\n".join(lines)


def render_root_cause_table(payload: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- frontier_count = `{payload['frontier_count']}`",
        f"- unexplained_count = `{payload['unexplained_count']}`",
        "",
    ]
    lines.extend(
        markdown_table(
            [
                ("frontier_record_id", "frontier_record_id"),
                ("first_divergence_stage_f", "first_divergence_stage_f"),
                ("first_divergence_stage_o", "first_divergence_stage_o"),
                ("primary_reason", "primary_reason"),
                ("root_cause_class", "root_cause_class"),
                ("stage_outside_authorized_output_surface", "stage_outside_authorized_output_surface"),
                ("surface_breach_regression", "surface_breach_regression"),
                ("canonical_current_authority_contract_breach", "canonical_current_authority_contract_breach"),
            ],
            payload["rows"],
        )
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ22 output parity surface frontier and root cause package.")
    parser.add_argument("--control-summary-json", type=Path, required=True)
    parser.add_argument("--authoritative-report-json", type=Path, action="append", required=True)
    parser.add_argument("--diagnostic-report-json", type=Path, action="append", required=True)
    parser.add_argument("--mismatch-table-output-json", type=Path, required=True)
    parser.add_argument("--mismatch-table-output-md", type=Path, required=True)
    parser.add_argument("--frontier-pack-output-json", type=Path, required=True)
    parser.add_argument("--frontier-pack-output-md", type=Path, required=True)
    parser.add_argument("--frontier-replay-output-json", type=Path, required=True)
    parser.add_argument("--frontier-replay-output-md", type=Path, required=True)
    parser.add_argument("--diagnostic-output-json", type=Path, required=True)
    parser.add_argument("--diagnostic-output-md", type=Path, required=True)
    parser.add_argument("--root-cause-output-json", type=Path, required=True)
    parser.add_argument("--root-cause-output-md", type=Path, required=True)
    args = parser.parse_args()

    payloads = build_payload(
        control_summary=load_json(args.control_summary_json),
        authoritative_reports=[load_json(path) for path in args.authoritative_report_json],
        diagnostic_reports=[load_json(path) for path in args.diagnostic_report_json],
    )
    mismatch_table, frontier_pack, frontier_replay, diagnostic_summary, root_cause_table = payloads

    write_json(args.mismatch_table_output_json, mismatch_table)
    args.mismatch_table_output_md.write_text(
        render_mismatch_table(mismatch_table, title="FAZ22 Output Parity Surface Mismatch Table"),
        encoding="utf-8",
    )
    write_json(args.frontier_pack_output_json, frontier_pack)
    args.frontier_pack_output_md.write_text(
        render_frontier_pack(frontier_pack, title="FAZ22 Output Parity Surface Frontier Pack"),
        encoding="utf-8",
    )
    write_json(args.frontier_replay_output_json, frontier_replay)
    args.frontier_replay_output_md.write_text(
        render_frontier_replay(frontier_replay, title="FAZ22 Output Parity Surface Frontier Replay"),
        encoding="utf-8",
    )
    write_json(args.diagnostic_output_json, diagnostic_summary)
    args.diagnostic_output_md.write_text(
        render_diagnostic_summary(diagnostic_summary, title="FAZ22 RC-J vs RC-M Surface Diagnostic Containment"),
        encoding="utf-8",
    )
    write_json(args.root_cause_output_json, root_cause_table)
    args.root_cause_output_md.write_text(
        render_root_cause_table(root_cause_table, title="FAZ22 Output Parity Surface Root Cause Table"),
        encoding="utf-8",
    )
    return 0 if frontier_replay["wp5_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
