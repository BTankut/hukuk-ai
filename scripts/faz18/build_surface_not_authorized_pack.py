#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz18_lib import F_STAGE_TO_O_STAGE, load_json, markdown_table, stable_hash, write_json  # noqa: E402


def build_payloads(
    *,
    frontier_replay: dict[str, Any],
    diagnostic: dict[str, Any],
    reason: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    rows = list(frontier_replay.get("rows") or [])
    mismatch_rows = []
    root_rows = []
    for row in rows:
        family_id = str(row.get("family_id"))
        question_id = str(row.get("question_id"))
        ordinal_index = int(row.get("ordinal_index", 0))
        first_stage_f = row.get("first_divergence_stage")
        first_stage_o = F_STAGE_TO_O_STAGE.get(first_stage_f)
        mismatch_rows.append(
            {
                "family_id": family_id,
                "question_id": question_id,
                "ordinal_index": ordinal_index,
                "first_divergence_stage_f": first_stage_f,
                "first_divergence_stage_o": first_stage_o,
                "primary_reason": row.get("primary_reason"),
                "status": "NOT AUTHORIZED",
            }
        )
        root_rows.append(
            {
                "frontier_record_id": f"{family_id}/{question_id}/{ordinal_index}",
                "frontier_family": family_id,
                "frontier_ordinal": ordinal_index,
                "question_id": question_id,
                "first_divergence_stage_f": first_stage_f,
                "first_divergence_stage_o": first_stage_o,
                "primary_reason": row.get("primary_reason"),
                "status": "NOT AUTHORIZED",
            }
        )

    mismatch_table = {
        "status": "NOT AUTHORIZED",
        "reason": reason,
        "frontier_count": int(frontier_replay.get("frontier_count", 0)),
        "rows": mismatch_rows,
    }
    frontier_pack = {
        "status": "NOT AUTHORIZED",
        "reason": reason,
        "frontier_count": mismatch_table["frontier_count"],
        "rows": mismatch_rows,
    }
    frontier_replay_payload = {
        "status": "NOT AUTHORIZED",
        "reason": reason,
        "frontier_count": int(frontier_replay.get("frontier_count", 0)),
        "first_divergence_assigned_count": int(frontier_replay.get("first_divergence_assigned_count", 0)),
        "primary_reason_assigned_count": int(frontier_replay.get("primary_reason_assigned_count", 0)),
        "classification_assigned_count": int(frontier_replay.get("classification_assigned_count", 0)),
        "unexplained_count": int(frontier_replay.get("unexplained_count", 0)),
        "output_parity_surface_breach_count": int(frontier_replay.get("output_parity_surface_breach_count", 0)),
        "localized_authorized_downstream_drift_count": int(
            frontier_replay.get("localized_authorized_downstream_drift_count", 0)
        ),
        "rows": mismatch_rows,
    }
    diagnostic_payload = {
        "status": "NOT AUTHORIZED",
        "reason": reason,
        "frontier_count": int(diagnostic.get("frontier_count", 0)),
        "rc_j_vs_rc_m_runtime_error_count": int(diagnostic.get("rc_j_vs_rc_m_runtime_error_count", 0)),
        "changed_record_outside_authorized_set_count": int(
            diagnostic.get("changed_record_outside_authorized_set_count", 0)
        ),
        "changed_field_outside_contract_count": int(diagnostic.get("changed_field_outside_contract_count", 0)),
        "rows": list(diagnostic.get("rows") or []),
    }
    root_cause_payload = {
        "status": "NOT AUTHORIZED",
        "reason": reason,
        "frontier_count": mismatch_table["frontier_count"],
        "rows": root_rows,
    }
    for payload in (mismatch_table, frontier_pack, frontier_replay_payload, diagnostic_payload, root_cause_payload):
        payload["report_hash"] = stable_hash(payload)
    return mismatch_table, frontier_pack, frontier_replay_payload, diagnostic_payload, root_cause_payload


def render_simple_rows(title: str, payload: dict[str, Any], columns: list[tuple[str, str]]) -> str:
    lines = [
        f"# {title}",
        "",
        f"- status = `{payload['status']}`",
        f"- reason = `{payload['reason']}`",
        f"- frontier_count = `{payload['frontier_count']}`",
        "",
    ]
    if payload.get("rows"):
        lines.extend(markdown_table(columns, payload["rows"]))
        lines.append("")
    return "\n".join(lines)


def render_frontier_replay(title: str, payload: dict[str, Any]) -> str:
    lines = [
        f"# {title}",
        "",
        f"- status = `{payload['status']}`",
        f"- reason = `{payload['reason']}`",
        f"- frontier_count = `{payload['frontier_count']}`",
        f"- first_divergence_assigned_count = `{payload['first_divergence_assigned_count']}`",
        f"- primary_reason_assigned_count = `{payload['primary_reason_assigned_count']}`",
        f"- classification_assigned_count = `{payload['classification_assigned_count']}`",
        f"- unexplained_count = `{payload['unexplained_count']}`",
        f"- output_parity_surface_breach_count = `{payload['output_parity_surface_breach_count']}`",
        f"- localized_authorized_downstream_drift_count = `{payload['localized_authorized_downstream_drift_count']}`",
        "",
    ]
    if payload.get("rows"):
        lines.extend(
            markdown_table(
                [
                    ("family_id", "family"),
                    ("question_id", "question_id"),
                    ("ordinal_index", "ordinal"),
                    ("first_divergence_stage_f", "first_divergence_stage_f"),
                    ("first_divergence_stage_o", "first_divergence_stage_o"),
                    ("primary_reason", "primary_reason"),
                ],
                payload["rows"],
            )
        )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ18 not-authorized surface pack wrappers.")
    parser.add_argument("--source-frontier-replay-json", type=Path, required=True)
    parser.add_argument("--source-diagnostic-json", type=Path, required=True)
    parser.add_argument("--reason", required=True)
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

    payloads = build_payloads(
        frontier_replay=load_json(args.source_frontier_replay_json),
        diagnostic=load_json(args.source_diagnostic_json),
        reason=args.reason,
    )
    mismatch_table, frontier_pack, frontier_replay_payload, diagnostic_payload, root_cause_payload = payloads

    write_json(args.mismatch_table_output_json, mismatch_table)
    write_json(args.frontier_pack_output_json, frontier_pack)
    write_json(args.frontier_replay_output_json, frontier_replay_payload)
    write_json(args.diagnostic_output_json, diagnostic_payload)
    write_json(args.root_cause_output_json, root_cause_payload)

    args.mismatch_table_output_md.write_text(
        render_simple_rows(
            "FAZ18 Output Parity Surface Mismatch Table",
            mismatch_table,
            [
                ("family_id", "family"),
                ("question_id", "question_id"),
                ("ordinal_index", "ordinal"),
                ("first_divergence_stage_f", "first_divergence_stage_f"),
                ("first_divergence_stage_o", "first_divergence_stage_o"),
                ("primary_reason", "primary_reason"),
            ],
        ),
        encoding="utf-8",
    )
    args.frontier_pack_output_md.write_text(
        render_simple_rows(
            "FAZ18 Output Parity Surface Frontier Pack",
            frontier_pack,
            [
                ("family_id", "family"),
                ("question_id", "question_id"),
                ("ordinal_index", "ordinal"),
                ("first_divergence_stage_f", "first_divergence_stage_f"),
            ],
        ),
        encoding="utf-8",
    )
    args.frontier_replay_output_md.write_text(
        render_frontier_replay("FAZ18 Output Parity Surface Frontier Replay", frontier_replay_payload),
        encoding="utf-8",
    )
    args.diagnostic_output_md.write_text(
        render_simple_rows(
            "FAZ18 RC-J vs RC-M Surface Diagnostic Containment",
            diagnostic_payload,
            [
                ("family_id", "family"),
                ("question_id", "question_id"),
                ("ordinal_index", "ordinal"),
                ("diagnostic_runtime_error", "diagnostic_runtime_error"),
                ("diagnostic_mismatch_present", "diagnostic_mismatch_present"),
                ("changed_field_set", "changed_field_set"),
                ("changed_field_outside_contract", "changed_field_outside_contract"),
            ],
        ),
        encoding="utf-8",
    )
    args.root_cause_output_md.write_text(
        render_simple_rows(
            "FAZ18 Output Parity Surface Root Cause Table",
            root_cause_payload,
            [
                ("frontier_record_id", "frontier_record_id"),
                ("frontier_family", "frontier_family"),
                ("question_id", "question_id"),
                ("frontier_ordinal", "frontier_ordinal"),
                ("first_divergence_stage_f", "first_divergence_stage_f"),
                ("first_divergence_stage_o", "first_divergence_stage_o"),
                ("primary_reason", "primary_reason"),
            ],
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
