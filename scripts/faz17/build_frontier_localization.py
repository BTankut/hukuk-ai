#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz17_lib import (
    AUTHORIZED_RECORD_IDS,
    LOCALIZED_ALLOWED_FIRST_STAGES,
    UPSTREAM_MISMATCH_FIELDS,
    family_sort_key,
    load_json,
    row_sort_key,
    stable_hash,
    write_json,
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
    authoritative_reports: list[dict[str, Any]],
    diagnostic_reports: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    diagnostic_by_family = {str(report.get("family_id")): report for report in diagnostic_reports}
    mismatch_rows: list[dict[str, Any]] = []
    for report in sorted(authoritative_reports, key=lambda item: family_sort_key(str(item.get("family_id")))):
        mismatch_rows.extend(report.get("mismatch_rows") or [])
    mismatch_rows = sorted((dict(row) for row in mismatch_rows), key=row_sort_key)

    diagnostic_rows = []
    replay_rows = []
    reason_rows = []
    localized_count = 0
    breach_count = 0
    upstream_breach_count = 0
    authorized_record_count = 0
    changed_record_outside_authorized_set_count = 0
    rc_j_vs_rc_m_runtime_error_count = 0
    first_divergence_assigned_count = 0
    primary_reason_assigned_count = 0
    classification_assigned_count = 0

    for row in mismatch_rows:
        family_id = str(row.get("family_id"))
        question_id = str(row.get("question_id"))
        diagnostic_report = diagnostic_by_family.get(family_id, {})
        diagnostic_auth_index, diagnostic_mismatch_index = _diagnostic_indexes(diagnostic_report)
        diagnostic_auth_row = diagnostic_auth_index.get(question_id, {})
        diagnostic_mismatch_row = diagnostic_mismatch_index.get(question_id, {})

        changed_field_set = list(diagnostic_auth_row.get("changed_field_set") or diagnostic_mismatch_row.get("changed_field_set") or [])
        changed_field_outside_contract = list(
            diagnostic_auth_row.get("changed_field_outside_contract")
            or diagnostic_mismatch_row.get("changed_field_outside_contract")
            or []
        )
        diagnostic_runtime_error = int(diagnostic_auth_row.get("runtime_error", 0)) + int(
            diagnostic_auth_row.get("reference_runtime_error", 0)
        )
        rc_j_vs_rc_m_runtime_error_count += diagnostic_runtime_error

        authorized_record = question_id in AUTHORIZED_RECORD_IDS
        if authorized_record:
            authorized_record_count += 1
        else:
            changed_record_outside_authorized_set_count += 1

        upstream_breach = any(int(row.get(field, 0)) > 0 for field in UPSTREAM_MISMATCH_FIELDS)
        if upstream_breach:
            upstream_breach_count += 1

        first_divergence_stage = row.get("first_divergence_stage")
        primary_reason = row.get("primary_reason")
        if first_divergence_stage:
            first_divergence_assigned_count += 1
        if primary_reason:
            primary_reason_assigned_count += 1

        localized = (
            authorized_record
            and first_divergence_stage in LOCALIZED_ALLOWED_FIRST_STAGES
            and not upstream_breach
            and len(changed_field_outside_contract) == 0
        )
        classification = (
            "rc_m_authoritative_output_parity_drift_localized"
            if localized
            else "output_parity_surface_breach"
        )
        classification_assigned_count += 1
        if localized:
            localized_count += 1
        else:
            breach_count += 1

        diagnostic_row = {
            "family_id": family_id,
            "question_id": question_id,
            "ordinal_index": int(row.get("ordinal_index", 0)),
            "diagnostic_runtime_error": diagnostic_runtime_error,
            "changed_field_set": changed_field_set,
            "changed_field_outside_contract": changed_field_outside_contract,
            "diagnostic_mismatch_present": question_id in diagnostic_mismatch_index,
        }
        replay_row = {
            "family_id": family_id,
            "question_id": question_id,
            "ordinal_index": int(row.get("ordinal_index", 0)),
            "first_divergence_stage": first_divergence_stage,
            "primary_reason": primary_reason,
            "authorized_record": authorized_record,
            "upstream_breach": upstream_breach,
            "classification": classification,
            "changed_field_set": changed_field_set,
            "changed_field_outside_contract": changed_field_outside_contract,
        }
        diagnostic_rows.append(diagnostic_row)
        replay_rows.append(replay_row)
        reason_rows.append(
            {
                "family_id": family_id,
                "question_id": question_id,
                "ordinal_index": int(row.get("ordinal_index", 0)),
                "first_divergence_stage": first_divergence_stage,
                "primary_reason": primary_reason,
                "classification": classification,
            }
        )

    frontier_count = len(mismatch_rows)
    unexplained_count = frontier_count - classification_assigned_count

    mismatch_table = {
        "frontier_count": frontier_count,
        "rows": mismatch_rows,
        "report_hash": stable_hash({"frontier_count": frontier_count, "rows": mismatch_rows}),
    }
    frontier_pack = {
        "frontier_count": frontier_count,
        "rows": [
            {
                "family_id": row["family_id"],
                "question_id": row["question_id"],
                "ordinal_index": row["ordinal_index"],
                "first_divergence_stage": row.get("first_divergence_stage"),
            }
            for row in mismatch_rows
        ],
        "report_hash": stable_hash(frontier_count),
    }
    diagnostic_summary = {
        "frontier_count": frontier_count,
        "authorized_record_count": authorized_record_count,
        "changed_record_outside_authorized_set_count": changed_record_outside_authorized_set_count,
        "rc_j_vs_rc_m_runtime_error_count": rc_j_vs_rc_m_runtime_error_count,
        "changed_field_outside_contract_count": sum(len(row["changed_field_outside_contract"]) for row in diagnostic_rows),
        "rows": diagnostic_rows,
    }
    frontier_replay = {
        "frontier_count": frontier_count,
        "first_divergence_assigned_count": first_divergence_assigned_count,
        "primary_reason_assigned_count": primary_reason_assigned_count,
        "classification_assigned_count": classification_assigned_count,
        "unexplained_count": unexplained_count,
        "authorized_record_count": authorized_record_count,
        "changed_record_outside_authorized_set_count": changed_record_outside_authorized_set_count,
        "upstream_breach_count": upstream_breach_count,
        "localized_authorized_downstream_drift_count": localized_count,
        "output_parity_surface_breach_count": breach_count,
        "rc_j_vs_rc_m_runtime_error_count": rc_j_vs_rc_m_runtime_error_count,
        "rows": replay_rows,
    }
    reason_table = {
        "frontier_count": frontier_count,
        "rows": reason_rows,
    }
    return mismatch_table, frontier_pack, diagnostic_summary, frontier_replay, reason_table


def _render_rows_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> list[str]:
    header = "| " + " | ".join(label for _, label in columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(key, "")) for key, _ in columns) + " |")
    return [header, divider, *body]


def render_mismatch_table(payload: dict[str, Any], *, title: str) -> str:
    lines = [f"# {title}", "", f"- frontier_count = `{payload['frontier_count']}`", ""]
    lines.extend(
        _render_rows_table(
            payload["rows"],
            [
                ("family_id", "family"),
                ("question_id", "question_id"),
                ("ordinal_index", "ordinal"),
                ("first_divergence_stage", "first_divergence_stage"),
                ("primary_reason", "primary_reason"),
            ],
        )
    )
    lines.append("")
    return "\n".join(lines)


def render_frontier_pack(payload: dict[str, Any], *, title: str) -> str:
    lines = [f"# {title}", "", f"- frontier_count = `{payload['frontier_count']}`", ""]
    for row in payload["rows"]:
        lines.append(
            f"- `{row['family_id']} / {row['question_id']}` stage `{row.get('first_divergence_stage')}`"
        )
    lines.append("")
    return "\n".join(lines)


def render_diagnostic_summary(payload: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- frontier_count = `{payload['frontier_count']}`",
        f"- rc_j_vs_rc_m_runtime_error_count = `{payload['rc_j_vs_rc_m_runtime_error_count']}`",
        f"- changed_record_outside_authorized_set_count = `{payload['changed_record_outside_authorized_set_count']}`",
        f"- changed_field_outside_contract_count = `{payload['changed_field_outside_contract_count']}`",
        "",
    ]
    lines.extend(
        _render_rows_table(
            payload["rows"],
            [
                ("family_id", "family"),
                ("question_id", "question_id"),
                ("ordinal_index", "ordinal"),
                ("diagnostic_runtime_error", "diagnostic_runtime_error"),
                ("diagnostic_mismatch_present", "diagnostic_mismatch_present"),
                ("changed_field_set", "changed_field_set"),
                ("changed_field_outside_contract", "changed_field_outside_contract"),
            ],
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
        f"- classification_assigned_count = `{payload['classification_assigned_count']}`",
        f"- unexplained_count = `{payload['unexplained_count']}`",
        f"- authorized_record_count = `{payload['authorized_record_count']}`",
        f"- changed_record_outside_authorized_set_count = `{payload['changed_record_outside_authorized_set_count']}`",
        f"- upstream_breach_count = `{payload['upstream_breach_count']}`",
        f"- localized_authorized_downstream_drift_count = `{payload['localized_authorized_downstream_drift_count']}`",
        f"- output_parity_surface_breach_count = `{payload['output_parity_surface_breach_count']}`",
        f"- rc_j_vs_rc_m_runtime_error_count = `{payload['rc_j_vs_rc_m_runtime_error_count']}`",
        "",
    ]
    lines.extend(
        _render_rows_table(
            payload["rows"],
            [
                ("family_id", "family"),
                ("question_id", "question_id"),
                ("ordinal_index", "ordinal"),
                ("first_divergence_stage", "first_divergence_stage"),
                ("primary_reason", "primary_reason"),
                ("classification", "classification"),
            ],
        )
    )
    lines.append("")
    return "\n".join(lines)


def render_reason_table(payload: dict[str, Any], *, title: str) -> str:
    lines = [f"# {title}", "", f"- frontier_count = `{payload['frontier_count']}`", ""]
    lines.extend(
        _render_rows_table(
            payload["rows"],
            [
                ("family_id", "family"),
                ("question_id", "question_id"),
                ("ordinal_index", "ordinal"),
                ("first_divergence_stage", "first_divergence_stage"),
                ("primary_reason", "primary_reason"),
                ("classification", "classification"),
            ],
        )
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ17 frontier localization and diagnostic containment.")
    parser.add_argument("--authoritative-report-json", type=Path, action="append", required=True)
    parser.add_argument("--diagnostic-report-json", type=Path, action="append", required=True)
    parser.add_argument("--mismatch-table-output-json", type=Path, required=True)
    parser.add_argument("--mismatch-table-output-md", type=Path, required=True)
    parser.add_argument("--frontier-pack-output-json", type=Path, required=True)
    parser.add_argument("--frontier-pack-output-md", type=Path, required=True)
    parser.add_argument("--diagnostic-output-json", type=Path, required=True)
    parser.add_argument("--diagnostic-output-md", type=Path, required=True)
    parser.add_argument("--frontier-replay-output-json", type=Path, required=True)
    parser.add_argument("--frontier-replay-output-md", type=Path, required=True)
    parser.add_argument("--reason-table-output-json", type=Path, required=True)
    parser.add_argument("--reason-table-output-md", type=Path, required=True)
    args = parser.parse_args()

    payloads = build_payload(
        [load_json(path) for path in args.authoritative_report_json],
        [load_json(path) for path in args.diagnostic_report_json],
    )
    mismatch_table, frontier_pack, diagnostic_summary, frontier_replay, reason_table = payloads

    write_json(args.mismatch_table_output_json, mismatch_table)
    write_json(args.frontier_pack_output_json, frontier_pack)
    write_json(args.diagnostic_output_json, diagnostic_summary)
    write_json(args.frontier_replay_output_json, frontier_replay)
    write_json(args.reason_table_output_json, reason_table)

    args.mismatch_table_output_md.write_text(
        render_mismatch_table(mismatch_table, title="FAZ17 Output Parity Authoritative Mismatch Table"),
        encoding="utf-8",
    )
    args.frontier_pack_output_md.write_text(
        render_frontier_pack(frontier_pack, title="FAZ17 Output Parity Authoritative Frontier Pack"),
        encoding="utf-8",
    )
    args.diagnostic_output_md.write_text(
        render_diagnostic_summary(
            diagnostic_summary,
            title="FAZ17 RC-J vs RC-M Frontier Diagnostic Containment",
        ),
        encoding="utf-8",
    )
    args.frontier_replay_output_md.write_text(
        render_frontier_replay(
            frontier_replay,
            title="FAZ17 Output Parity Authoritative Frontier Replay",
        ),
        encoding="utf-8",
    )
    args.reason_table_output_md.write_text(
        render_reason_table(reason_table, title="FAZ17 Output Parity Authoritative Reason Table"),
        encoding="utf-8",
    )
    return 0 if frontier_replay["unexplained_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
