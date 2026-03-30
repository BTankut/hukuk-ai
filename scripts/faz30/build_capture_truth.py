#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz30_lib import (  # type: ignore
    INCONCLUSIVE_RECAPTURE_REF,
    STABLE_REPAIR_TRUTH_REF,
    bool_text,
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


def _matches_triplet(truth: dict[str, Any], *, faz28: bool) -> bool:
    if faz28:
        return (
            truth["persisted_pii_redaction_pass"] is False
            and truth["tokenizer_backed_accounting_pass"] is False
            and truth["one_command_release_smoke_pass"] is False
        )
    return (
        truth["persisted_pii_redaction_pass"] is False
        and truth["tokenizer_backed_accounting_pass"] is True
        and truth["api_versioning_pass"] is False
        and truth["one_command_release_smoke_pass"] is False
    )


def _matches_retention(truth: dict[str, Any], *, faz28: bool) -> bool:
    return (
        truth["retained_after_family_eval"] is False
        and truth["retained_after_restart"] is False
        and truth["retained_after_restore"] is True
        and truth["answer_path_delta_reintroduced"] is True
    )


def _build_truth_flags(*, boundary: dict[str, Any], spillover: dict[str, Any], triplet: dict[str, Any], retention: dict[str, Any]) -> dict[str, bool]:
    matches_faz28 = (
        int(boundary["record_count"]) == STABLE_REPAIR_TRUTH_REF["boundary_frontier_count"]
        and int(boundary["mismatch_count"]) == STABLE_REPAIR_TRUTH_REF["boundary_frontier_count"] - 14
        and int(boundary["faz1_50_mismatch_count"]) == STABLE_REPAIR_TRUTH_REF["faz1_50_mismatch_count"]
        and int(boundary["v2_95_mismatch_count"]) == STABLE_REPAIR_TRUTH_REF["v2_95_mismatch_count"]
        and int(boundary["v3_170_mismatch_count"]) == STABLE_REPAIR_TRUTH_REF["v3_170_mismatch_count"]
        and int(boundary["preprojection_hash_mismatch_count"]) == STABLE_REPAIR_TRUTH_REF["preprojection_hash_mismatch_count"]
        and int(boundary["raw_answer_hash_mismatch_count"]) == STABLE_REPAIR_TRUTH_REF["raw_answer_hash_mismatch_count"]
        and int(boundary["response_envelope_hash_mismatch_count"]) == STABLE_REPAIR_TRUTH_REF["response_envelope_hash_mismatch_count"]
        and int(boundary["runtime_error_count"]) == 0
        and int(spillover["record_count"]) == STABLE_REPAIR_TRUTH_REF["spillover_guard_record_count"]
        and int(spillover["mismatch_count"]) == STABLE_REPAIR_TRUTH_REF["spillover_mismatch_count"]
        and int(spillover["preprojection_hash_mismatch_count"]) == STABLE_REPAIR_TRUTH_REF["spillover_preprojection_hash_mismatch_count"]
        and int(spillover["raw_answer_hash_mismatch_count"]) == STABLE_REPAIR_TRUTH_REF["spillover_raw_answer_hash_mismatch_count"]
        and int(spillover["response_envelope_hash_mismatch_count"]) == STABLE_REPAIR_TRUTH_REF["spillover_response_envelope_hash_mismatch_count"]
        and int(spillover["runtime_error_count"]) == STABLE_REPAIR_TRUTH_REF["spillover_runtime_error_count"]
        and _matches_triplet(triplet, faz28=True)
        and _matches_retention(retention, faz28=True)
    )

    matches_faz29 = (
        int(boundary["record_count"]) == INCONCLUSIVE_RECAPTURE_REF["boundary_frontier_count"]
        and int(boundary["mismatch_count"]) == INCONCLUSIVE_RECAPTURE_REF["boundary_frontier_count"]
        and int(boundary["faz1_50_mismatch_count"]) == INCONCLUSIVE_RECAPTURE_REF["faz1_50_mismatch_count"]
        and int(boundary["v2_95_mismatch_count"]) == INCONCLUSIVE_RECAPTURE_REF["v2_95_mismatch_count"]
        and int(boundary["v3_170_mismatch_count"]) == INCONCLUSIVE_RECAPTURE_REF["v3_170_mismatch_count"]
        and int(boundary["preprojection_hash_mismatch_count"]) == INCONCLUSIVE_RECAPTURE_REF["preprojection_hash_mismatch_count"]
        and int(boundary["raw_answer_hash_mismatch_count"]) == INCONCLUSIVE_RECAPTURE_REF["raw_answer_hash_mismatch_count"]
        and int(boundary["response_envelope_hash_mismatch_count"]) == INCONCLUSIVE_RECAPTURE_REF["response_envelope_hash_mismatch_count"]
        and int(boundary["runtime_error_count"]) == INCONCLUSIVE_RECAPTURE_REF["runtime_error_count"]
        and int(spillover["record_count"]) == INCONCLUSIVE_RECAPTURE_REF["spillover_guard_record_count"]
        and int(spillover["mismatch_count"]) == INCONCLUSIVE_RECAPTURE_REF["spillover_mismatch_count"]
        and int(spillover["preprojection_hash_mismatch_count"]) == INCONCLUSIVE_RECAPTURE_REF["spillover_preprojection_hash_mismatch_count"]
        and int(spillover["raw_answer_hash_mismatch_count"]) == INCONCLUSIVE_RECAPTURE_REF["spillover_raw_answer_hash_mismatch_count"]
        and int(spillover["response_envelope_hash_mismatch_count"]) == INCONCLUSIVE_RECAPTURE_REF["spillover_response_envelope_hash_mismatch_count"]
        and int(spillover["runtime_error_count"]) == INCONCLUSIVE_RECAPTURE_REF["spillover_runtime_error_count"]
        and _matches_triplet(triplet, faz28=False)
        and _matches_retention(retention, faz28=False)
    )
    return {
        "matches_faz28_truth": matches_faz28,
        "matches_faz29_truth": matches_faz29,
        "matches_neither_new_stable_truth": not matches_faz28 and not matches_faz29,
    }


def _runtime_error_assignments(report: dict[str, Any]) -> dict[str, Any]:
    stage_counts: dict[str, int] = {}
    reason_counts: dict[str, int] = {}
    assigned_stage_count = 0
    assigned_reason_count = 0

    for row in report.get("mismatch_rows", []):
        if not isinstance(row, dict) or not bool(row.get("runtime_error")):
            continue

        stage = None
        reason = None
        note = str(row.get("notes") or "")
        if "question missing in reference or candidate map" in note:
            stage = "R12_evaluator_write"
            reason = "boundary_pack_orchestration_runtime_mutation"

        if isinstance(stage, str):
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
            assigned_stage_count += 1
        if isinstance(reason, str):
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
            assigned_reason_count += 1

    dominant_stage = ""
    dominant_reason = ""
    if stage_counts:
        dominant_stage = max(stage_counts.items(), key=lambda item: (item[1], item[0]))[0]
    if reason_counts:
        dominant_reason = max(reason_counts.items(), key=lambda item: (item[1], item[0]))[0]

    return {
        "first_runtime_error_stage_assigned_count": assigned_stage_count,
        "runtime_primary_reason_assigned_count": assigned_reason_count,
        "dominant_runtime_error_stage": dominant_stage,
        "dominant_runtime_error_primary_reason": dominant_reason,
        "runtime_error_stage_counts": stage_counts,
        "runtime_primary_reason_counts": reason_counts,
    }


def build_capture_truth(
    *,
    boundary_pair: dict[str, Any],
    spillover_pair: dict[str, Any],
    boundary_pack: list[dict[str, Any]],
    spillover_pack: list[dict[str, Any]],
    current_authority_check: dict[str, Any],
    upstream_equality: dict[str, Any],
    retention_gate: dict[str, Any],
) -> dict[str, Any]:
    control_rows = list(retention_gate.get("control_rows") or [])
    boundary_summary = summarize_pack_report(report=boundary_pair, pack_rows=boundary_pack)
    spillover_summary = summarize_pack_report(report=spillover_pair, pack_rows=spillover_pack)
    boundary_runtime = _runtime_error_assignments(boundary_pair)
    spillover_runtime = _runtime_error_assignments(spillover_pair)

    boundary_summary.update(boundary_runtime)
    spillover_summary.update(spillover_runtime)

    triplet = {
        "persisted_pii_redaction_pass": _control_pass(control_rows, "persisted PII redaction"),
        "tokenizer_backed_accounting_pass": _control_pass(control_rows, "tokenizer-backed accounting"),
        "api_versioning_pass": _control_pass(control_rows, "API versioning"),
        "one_command_release_smoke_pass": _control_pass(control_rows, "one-command release smoke"),
        "pii_leak_found": bool(retention_gate["pii_leak_found"]),
        "token_accounting_fallback_found": bool(retention_gate["token_accounting_fallback_found"]),
        "api_versioning_gap_found": bool(retention_gate["api_versioning_gap_found"]),
        "release_smoke_gap_found": bool(retention_gate["release_smoke_gap_found"]),
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }

    retention = {
        "retained_after_family_eval": bool(retention_gate["retained_after_family_eval"]),
        "retained_after_restart": bool(retention_gate["retained_after_restart"]),
        "retained_after_restore": bool(retention_gate["retained_after_restore"]),
        "answer_path_delta_reintroduced": bool(boundary_summary["mismatch_count"] > 0),
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }

    truth_flags = _build_truth_flags(
        boundary=boundary_summary,
        spillover=spillover_summary,
        triplet=triplet,
        retention=retention,
    )

    return {
        "wp2": {
            "control_pair_authority_match": bool(current_authority_check["control_pair_authority_match"]),
            "current_authority_contract_breach": bool(current_authority_check["current_authority_contract_breach"]),
            "surface_breach_from_history_reintroduced": bool(current_authority_check["surface_breach_from_history_reintroduced"]),
            "current_canonical_authority_adopted": bool(current_authority_check.get("current_canonical_authority_adopted", False)),
            "control_pair_runtime_error_count": int(current_authority_check.get("control_pair_runtime_error_count", 0)),
            "model_request_payload_hash_mismatch_count": int(upstream_equality["model_request_payload_hash_mismatch_count"]),
            "retrieval_request_hash_mismatch_count": int(upstream_equality["retrieval_request_hash_mismatch_count"]),
            "assembled_context_hash_mismatch_count": int(upstream_equality["assembled_context_hash_mismatch_count"]),
            "runtime_error_count": int(upstream_equality["runtime_error_count"]),
        },
        "boundary": boundary_summary,
        "spillover": spillover_summary,
        "failing_control_triplet": triplet,
        "retention_truth": retention,
        "truth_flags": truth_flags,
    }


def render_markdown(payload: dict[str, Any], *, title: str) -> str:
    lines = [f"# {title}", ""]
    for section in ("wp2", "boundary", "spillover", "failing_control_triplet", "retention_truth", "truth_flags"):
        lines.append(f"## {section.upper()}")
        lines.append("")
        for key, value in payload[section].items():
            rendered = bool_text(value) if isinstance(value, bool) else value
            lines.append(f"- {key} = `{rendered}`")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ30 single-capture forensic truth summary.")
    parser.add_argument("--boundary-pair-json", type=Path, required=True)
    parser.add_argument("--spillover-pair-json", type=Path, required=True)
    parser.add_argument("--boundary-pack-json", type=Path, required=True)
    parser.add_argument("--spillover-pack-json", type=Path, required=True)
    parser.add_argument("--current-authority-check-json", type=Path, required=True)
    parser.add_argument("--upstream-equality-json", type=Path, required=True)
    parser.add_argument("--retention-gate-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--title", default="FAZ30 Capture Truth")
    args = parser.parse_args()

    boundary_pack_payload = load_json(args.boundary_pack_json)
    spillover_pack_payload = load_json(args.spillover_pack_json)
    boundary_pack = list((boundary_pack_payload.get("questions") if isinstance(boundary_pack_payload, dict) else boundary_pack_payload) or [])
    spillover_pack = list((spillover_pack_payload.get("questions") if isinstance(spillover_pack_payload, dict) else spillover_pack_payload) or [])

    payload = build_capture_truth(
        boundary_pair=load_json(args.boundary_pair_json),
        spillover_pair=load_json(args.spillover_pair_json),
        boundary_pack=boundary_pack,
        spillover_pack=spillover_pack,
        current_authority_check=load_json(args.current_authority_check_json),
        upstream_equality=load_json(args.upstream_equality_json),
        retention_gate=load_json(args.retention_gate_json),
    )
    write_json(args.output_json, payload)
    if args.output_md:
        write_text(args.output_md, render_markdown(payload, title=args.title))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
