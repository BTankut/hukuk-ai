#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz22_lib import markdown_table, stable_hash, write_json


def build_payloads(*, frontier_count: int, reason: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    mismatch_table = {
        "status": "NOT AUTHORIZED",
        "reason": reason,
        "frontier_count": frontier_count,
        "rows": [],
    }
    frontier_pack = {
        "status": "NOT AUTHORIZED",
        "reason": reason,
        "frontier_count": frontier_count,
        "rows": [],
    }
    frontier_replay = {
        "status": "NOT AUTHORIZED",
        "reason": reason,
        "frontier_count": frontier_count,
        "first_divergence_assigned_count": 0,
        "primary_reason_assigned_count": 0,
        "root_cause_class_assigned_count": 0,
        "unexplained_count": 0,
        "rc_j_vs_rc_m_runtime_error_count": 0,
        "wp5_pass": False,
        "rows": [],
    }
    diagnostic = {
        "status": "NOT AUTHORIZED",
        "reason": reason,
        "frontier_count": frontier_count,
        "rc_j_vs_rc_m_runtime_error_count": 0,
        "rows": [],
    }
    root_cause = {
        "status": "NOT AUTHORIZED",
        "reason": reason,
        "frontier_count": frontier_count,
        "unexplained_count": 0,
        "rows": [],
    }
    for payload in (mismatch_table, frontier_pack, frontier_replay, diagnostic, root_cause):
        payload["report_hash"] = stable_hash(payload)
    return mismatch_table, frontier_pack, frontier_replay, diagnostic, root_cause


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
        f"- root_cause_class_assigned_count = `{payload['root_cause_class_assigned_count']}`",
        f"- unexplained_count = `{payload['unexplained_count']}`",
        f"- rc_j_vs_rc_m_runtime_error_count = `{payload['rc_j_vs_rc_m_runtime_error_count']}`",
        f"- wp5_pass = `false`",
        "",
    ]
    if payload.get("rows"):
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ22 not-authorized surface pack wrappers.")
    parser.add_argument("--frontier-count", type=int, default=0)
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

    mismatch_table, frontier_pack, frontier_replay, diagnostic, root_cause = build_payloads(
        frontier_count=args.frontier_count,
        reason=args.reason,
    )

    write_json(args.mismatch_table_output_json, mismatch_table)
    write_json(args.frontier_pack_output_json, frontier_pack)
    write_json(args.frontier_replay_output_json, frontier_replay)
    write_json(args.diagnostic_output_json, diagnostic)
    write_json(args.root_cause_output_json, root_cause)

    args.mismatch_table_output_md.write_text(
        render_simple_rows(
            "FAZ22 Output Parity Surface Mismatch Table",
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
            "FAZ22 Output Parity Surface Frontier Pack",
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
        render_frontier_replay("FAZ22 Output Parity Surface Frontier Replay", frontier_replay),
        encoding="utf-8",
    )
    args.diagnostic_output_md.write_text(
        render_simple_rows(
            "FAZ22 RC-J vs RC-M Surface Diagnostic Containment",
            diagnostic,
            [
                ("family_id", "family"),
                ("question_id", "question_id"),
                ("ordinal_index", "ordinal"),
                ("diagnostic_runtime_error", "diagnostic_runtime_error"),
                ("diagnostic_mismatch_present", "diagnostic_mismatch_present"),
            ],
        ),
        encoding="utf-8",
    )
    args.root_cause_output_md.write_text(
        render_simple_rows(
            "FAZ22 Output Parity Surface Root Cause Table",
            root_cause,
            [
                ("frontier_record_id", "frontier_record_id"),
                ("frontier_family", "frontier_family"),
                ("frontier_question_id", "frontier_question_id"),
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
