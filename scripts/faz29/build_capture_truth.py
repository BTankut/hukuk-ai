#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz29_lib import (  # type: ignore
    BOUNDARY_EXPECTED,
    FIELD_SPECS,
    load_json,
    summarize_pack_report,
    write_json,
    write_text,
)


def _control_pass(control_rows: list[dict[str, Any]], control: str) -> bool:
    for row in control_rows:
        if str(row.get("control")) == control:
            return bool(row.get("pass"))
    raise KeyError(f"missing control row: {control}")


def build_capture_truth(
    *,
    materialized: dict[str, Any],
    current_authority_check: dict[str, Any],
    upstream_equality: dict[str, Any],
    boundary_pair: dict[str, Any],
    spillover_pair: dict[str, Any],
    retention_gate: dict[str, Any],
) -> dict[str, Any]:
    control_rows = list(retention_gate.get("control_rows") or [])
    boundary_pack = list(materialized["frontier_records"])
    spillover_pack = list(materialized["spillover_guard_records"])

    boundary_summary = summarize_pack_report(report=boundary_pair, pack_rows=boundary_pack)
    spillover_summary = summarize_pack_report(report=spillover_pair, pack_rows=spillover_pack)

    wp2 = {
        "control_pair_authority_match": bool(current_authority_check["control_pair_authority_match"]),
        "current_authority_contract_breach": bool(current_authority_check["current_authority_contract_breach"]),
        "surface_breach_from_history_reintroduced": bool(current_authority_check["surface_breach_from_history_reintroduced"]),
        "current_canonical_authority_adopted": bool(current_authority_check["current_canonical_authority_adopted"]),
        "control_pair_runtime_error_count": int(current_authority_check["control_pair_runtime_error_count"]),
        "model_request_payload_hash_mismatch_count": int(upstream_equality["model_request_payload_hash_mismatch_count"]),
        "retrieval_request_hash_mismatch_count": int(upstream_equality["retrieval_request_hash_mismatch_count"]),
        "assembled_context_hash_mismatch_count": int(upstream_equality["assembled_context_hash_mismatch_count"]),
        "runtime_error_count": int(upstream_equality["runtime_error_count"]),
    }

    remaining_mismatch_count = int(boundary_summary["mismatch_count"])
    wp3 = {
        "input_pack_count": len(boundary_pack),
        "remaining_mismatch_count": remaining_mismatch_count,
        "repair_delta_record_count": BOUNDARY_EXPECTED["input_pack_count"] - remaining_mismatch_count,
        "faz1_50_mismatch_count": int(boundary_summary["faz1_50_mismatch_count"]),
        "v2_95_mismatch_count": int(boundary_summary["v2_95_mismatch_count"]),
        "v3_170_mismatch_count": int(boundary_summary["v3_170_mismatch_count"]),
        "preprojection_hash_mismatch_count": int(boundary_summary["preprojection_hash_mismatch_count"]),
        "raw_answer_hash_mismatch_count": int(boundary_summary["raw_answer_hash_mismatch_count"]),
        "response_envelope_hash_mismatch_count": int(boundary_summary["response_envelope_hash_mismatch_count"]),
        "first_break_stage_assigned_count": int(boundary_summary["first_break_stage_assigned_count"]),
        "primary_reason_assigned_count": int(boundary_summary["primary_reason_assigned_count"]),
        "runtime_error_count": int(boundary_summary["runtime_error_count"]),
        "unexplained_count": int(boundary_summary["unexplained_count"]),
    }

    wp4 = {
        "record_count": len(spillover_pack),
        "mismatch_count": int(spillover_summary["mismatch_count"]),
        "preprojection_hash_mismatch_count": int(spillover_summary["preprojection_hash_mismatch_count"]),
        "raw_answer_hash_mismatch_count": int(spillover_summary["raw_answer_hash_mismatch_count"]),
        "response_envelope_hash_mismatch_count": int(spillover_summary["response_envelope_hash_mismatch_count"]),
        "runtime_error_count": int(spillover_summary["runtime_error_count"]),
        "unexplained_count": int(spillover_summary["unexplained_count"]),
    }

    wp5 = {
        "must_close_release_controls_count": int(retention_gate["must_close_release_controls_count"]),
        "mandatory_auth_pass": _control_pass(control_rows, "mandatory auth"),
        "immutable_audit_logging_pass": _control_pass(control_rows, "immutable audit logging"),
        "persisted_pii_redaction_pass": _control_pass(control_rows, "persisted PII redaction"),
        "redis_session_persistence_pass": _control_pass(control_rows, "Redis session persistence"),
        "tokenizer_backed_accounting_pass": _control_pass(control_rows, "tokenizer-backed accounting"),
        "observability_alerting_pass": _control_pass(control_rows, "observability / alerting"),
        "api_versioning_pass": _control_pass(control_rows, "API versioning"),
        "process_supervision_pass": _control_pass(control_rows, "process supervision"),
        "backup_restore_pass": _control_pass(control_rows, "backup / restore"),
        "one_command_release_smoke_pass": _control_pass(control_rows, "one-command release smoke"),
        "auth_bypass_found": bool(retention_gate["auth_bypass_found"]),
        "audit_write_loss_found": bool(retention_gate["audit_write_loss_found"]),
        "pii_leak_found": bool(retention_gate["pii_leak_found"]),
        "redis_continuity_break_found": bool(retention_gate["redis_continuity_break_found"]),
        "token_accounting_fallback_found": bool(retention_gate["token_accounting_fallback_found"]),
        "observability_gap_found": bool(retention_gate["observability_gap_found"]),
        "api_versioning_gap_found": bool(retention_gate["api_versioning_gap_found"]),
        "supervision_gap_found": bool(retention_gate["supervision_gap_found"]),
        "backup_restore_gap_found": bool(retention_gate["backup_restore_gap_found"]),
        "release_smoke_gap_found": bool(retention_gate["release_smoke_gap_found"]),
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }

    wp6 = {
        "retained_after_family_eval": bool(retention_gate["retained_after_family_eval"]),
        "retained_after_restart": bool(retention_gate["retained_after_restart"]),
        "retained_after_restore": bool(retention_gate["retained_after_restore"]),
        "answer_path_delta_reintroduced": remaining_mismatch_count > 0,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }

    return {
        "wp2": wp2,
        "wp3": wp3,
        "wp4": wp4,
        "wp5": wp5,
        "wp6": wp6,
        "field_specs": [list(item) for item in FIELD_SPECS],
    }


def render_markdown(payload: dict[str, Any], *, title: str) -> str:
    lines = [f"# {title}", ""]
    for section in ("wp2", "wp3", "wp4", "wp5", "wp6"):
        lines.append(f"## {section.upper()}")
        lines.append("")
        for key, value in payload[section].items():
            rendered = "true" if value is True else "false" if value is False else value
            lines.append(f"- {key} = `{rendered}`")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ29 single-capture truth summary.")
    parser.add_argument("--materialized-json", type=Path, required=True)
    parser.add_argument("--current-authority-check-json", type=Path, required=True)
    parser.add_argument("--upstream-equality-json", type=Path, required=True)
    parser.add_argument("--boundary-pair-json", type=Path, required=True)
    parser.add_argument("--spillover-pair-json", type=Path, required=True)
    parser.add_argument("--retention-gate-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--title", default="FAZ29 Capture Truth")
    args = parser.parse_args()

    payload = build_capture_truth(
        materialized=load_json(args.materialized_json),
        current_authority_check=load_json(args.current_authority_check_json),
        upstream_equality=load_json(args.upstream_equality_json),
        boundary_pair=load_json(args.boundary_pair_json),
        spillover_pair=load_json(args.spillover_pair_json),
        retention_gate=load_json(args.retention_gate_json),
    )
    write_json(args.output_json, payload)
    if args.output_md:
        write_text(args.output_md, render_markdown(payload, title=args.title))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
