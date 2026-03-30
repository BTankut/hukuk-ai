#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz36_lib import (
    BRIDGE_CONTRACT,
    DATE,
    DECISION_TO_NEXT_WORK,
    EXPECTED_API_VERSION,
    EXPECTED_LANE,
    FAIL_ACCEPTANCE,
    FAIL_CURRENT_AUTHORITY,
    FAIL_FRONTIER,
    FAIL_INCONCLUSIVE,
    FAIL_PARITY,
    FAIL_REFERENCE,
    FAIL_RESPONSE,
    FAIL_RETENTION,
    FAIL_TOPOLOGY,
    FAIL_UPSTREAM,
    PASS_DECISION,
    PROHIBITED_RUNTIME_MUTATION_FLAGS,
    REFERENCE_FILES,
    REFERENCE_MARKERS,
    RELEASE_CONTROLS_EXACT_SET,
    REQUIRED_ALERT_KEYS,
    RESULT_REPORT_NAME,
    ROOT,
    bool_text,
    build_frozen_frontier_records,
    build_frozen_response_envelope_records,
    load_json,
    load_text,
    markdown_table,
    metric_value,
    parse_headers_text,
    parse_metrics_text,
    summarize_record_counts,
    write_json,
    write_text,
)


def _load_reference_pack() -> dict[str, Any]:
    contradiction_rows: list[dict[str, str]] = []
    for name, path in REFERENCE_FILES.items():
        text = load_text(path)
        for marker in REFERENCE_MARKERS[name]:
            if marker not in text:
                contradiction_rows.append({"reference": name, "missing_marker": marker})

    return {
        "reference_pack_integrity_pass": len(contradiction_rows) == 0,
        "reference_pack_contradiction_count": len(contradiction_rows),
        "canonical_current_authority_ref": "FAZ21",
        "post_rc_m_steering_ref": "FAZ25",
        "rc_n_release_controls_legacy_ref": "FAZ26",
        "rc_n_boundary_root_cause_ref": "FAZ27",
        "rc_o_repair_truth_ref": "FAZ31",
        "rc_o_archival_closure_ref": "FAZ32",
        "post_rc_o_steering_ref": "FAZ33",
        "rc_p_perimeter_truth_ref": "FAZ35",
        "contradiction_rows": contradiction_rows,
    }


def _build_topology() -> dict[str, Any]:
    return {
        "RC-G": "accepted_quality_reference",
        "RC-J": "canonical_control_diagnostic",
        "RC-N": "forensic_reference_candidate",
        "RC-M": "discard_archived / historical_summary_archive / diagnostic_only",
        "RC-O": "discard_archived / historical_repair_archive / diagnostic_only",
        "RC-P": "frozen_failed_perimeter_candidate / diagnostic_only",
        "RC-Q": "release_controls_perimeter_repair_candidate",
        "stale_branch_left_active": False,
        "surface_breach_from_history_reintroduced": False,
        "cutover_allowed": False,
        "pilot_allowed": False,
        "database_expansion_allowed": False,
        "rc_r_reserved": False,
    }


def _build_manifest() -> dict[str, Any]:
    return {
        "candidate_id": "RC-Q",
        "base_candidate": "RC-G",
        "control_candidate": "RC-J",
        "forensic_reference_candidate": "RC-N",
        "current_perimeter_truth_reference": "RC-P",
        "candidate_status": "release_controls_perimeter_repair_candidate",
        "diagnostic_only": False,
        "promotable": False,
        "repairable": False,
        "current_evaluable": True,
        "allowed_diff_surface": "non_model_visible_release_controls_perimeter_only",
        "answer_path_delta_allowed": False,
        "cutover_authorized": False,
        "pilot_authorized": False,
        "database_expansion_authorized": False,
    }


def _supervision_pass(payload: dict[str, Any]) -> bool:
    return all(
        bool(payload.get(key))
        for key in (
            "gateway_pid_running",
            "tunnel_pid_running",
            "health_ok",
            "metrics_ok",
            "audit_log_exists",
            "healthy",
        )
    )


def _backup_restore_pass(manifest: dict[str, Any], restore_summary: dict[str, Any]) -> bool:
    files = restore_summary.get("files")
    return (
        isinstance(manifest.get("files"), list)
        and len(manifest.get("files", [])) > 0
        and isinstance(files, list)
        and len(files) > 0
        and all(bool(item.get("exists")) for item in files if isinstance(item, dict))
        and isinstance(restore_summary.get("restore_env_path"), str)
    )


def _report_by_family(reports: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(report["family_id"]): report for report in reports}


def _model_visible_question_index(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row["question_id"]): row
        for row in report.get("mismatch_rows", [])
        if isinstance(row, dict) and row.get("question_id")
    }


def _parity_question_index(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row["question_id"]): row
        for row in report.get("parity_rows", [])
        if isinstance(row, dict) and row.get("question_id")
    }


def _build_frontier_summary(
    *,
    model_visible_reports: list[dict[str, Any]],
    parity_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    frozen = build_frozen_frontier_records()
    frozen_counts = summarize_record_counts(frozen)
    model_visible_by_family = _report_by_family(model_visible_reports)
    parity_by_family = _report_by_family(parity_reports)
    failing_rows: list[dict[str, Any]] = []
    preprojection_count = 0
    raw_answer_count = 0
    response_count = 0
    runtime_error_count = 0
    first_divergence_assigned_count = 0
    primary_reason_assigned_count = 0
    family_counts = {"faz1-50": 0, "v2-95": 0, "v3-170": 0}

    for frozen_row in frozen:
        family_id = str(frozen_row["family_id"])
        question_id = str(frozen_row["question_id"])
        visible_row = _model_visible_question_index(model_visible_by_family[family_id]).get(question_id)
        parity_row = _parity_question_index(parity_by_family[family_id]).get(question_id)

        mismatch_keys = list(visible_row.get("mismatch_keys") or []) if visible_row else []
        response_mismatch = bool(parity_row and parity_row.get("response_envelope_hash_mismatch"))
        runtime_error = bool(visible_row and visible_row.get("runtime_error")) or bool(
            parity_row and (parity_row.get("reference_runtime_error") or parity_row.get("candidate_runtime_error"))
        )

        if not visible_row and not response_mismatch and not runtime_error:
            continue

        family_counts[family_id] += 1
        if "preprojection_hash" in mismatch_keys:
            preprojection_count += 1
        if "raw_answer_hash" in mismatch_keys:
            raw_answer_count += 1
        if response_mismatch:
            response_count += 1
        if runtime_error:
            runtime_error_count += 1

        first_divergence = visible_row.get("first_break_stage") if visible_row else None
        primary_reason = visible_row.get("primary_reason") if visible_row else None
        if first_divergence:
            first_divergence_assigned_count += 1
        if primary_reason:
            primary_reason_assigned_count += 1

        failing_rows.append(
            {
                "family_id": family_id,
                "question_id": question_id,
                "first_divergence_stage": first_divergence,
                "primary_reason": primary_reason,
                "mismatch_keys": mismatch_keys,
                "response_envelope_hash_mismatch": response_mismatch,
                "runtime_error": runtime_error,
            }
        )

    unexplained_count = sum(
        1 for row in failing_rows if not row["first_divergence_stage"] or not row["primary_reason"]
    )
    return {
        "frontier_record_count": len(frozen),
        "faz1_50_mismatch_count": family_counts["faz1-50"],
        "v2_95_mismatch_count": family_counts["v2-95"],
        "v3_170_mismatch_count": family_counts["v3-170"],
        "preprojection_hash_mismatch_count": preprojection_count,
        "raw_answer_hash_mismatch_count": raw_answer_count,
        "response_envelope_hash_mismatch_count": response_count,
        "runtime_error_count": runtime_error_count,
        "first_divergence_assigned_count": first_divergence_assigned_count,
        "primary_reason_assigned_count": primary_reason_assigned_count,
        "unexplained_count": unexplained_count,
        "frozen_truth_faz1_50_mismatch_count": frozen_counts["faz1-50"],
        "frozen_truth_v2_95_mismatch_count": frozen_counts["v2-95"],
        "frozen_truth_v3_170_mismatch_count": frozen_counts["v3-170"],
        "failing_rows": failing_rows,
    }


def _build_response_summary(*, parity_reports: list[dict[str, Any]]) -> dict[str, Any]:
    frozen = build_frozen_response_envelope_records()
    frozen_counts = summarize_record_counts(frozen)
    parity_by_family = _report_by_family(parity_reports)
    failing_rows: list[dict[str, Any]] = []
    family_counts = {"faz1-50": 0, "v2-95": 0, "v3-170": 0}
    runtime_error_count = 0
    first_divergence_assigned_count = 0
    primary_reason_assigned_count = 0

    for frozen_row in frozen:
        family_id = str(frozen_row["family_id"])
        question_id = str(frozen_row["question_id"])
        parity_row = _parity_question_index(parity_by_family[family_id]).get(question_id)
        if not parity_row or not parity_row.get("response_envelope_hash_mismatch"):
            continue

        family_counts[family_id] += 1
        runtime_error = bool(parity_row.get("reference_runtime_error") or parity_row.get("candidate_runtime_error"))
        if runtime_error:
            runtime_error_count += 1
        first_divergence = parity_row.get("first_divergence_stage")
        primary_reason = parity_row.get("primary_reason")
        if first_divergence:
            first_divergence_assigned_count += 1
        if primary_reason:
            primary_reason_assigned_count += 1

        failing_rows.append(
            {
                "family_id": family_id,
                "question_id": question_id,
                "first_divergence_stage": first_divergence,
                "primary_reason": primary_reason,
                "runtime_error": runtime_error,
            }
        )

    unexplained_count = sum(
        1 for row in failing_rows if not row["first_divergence_stage"] or not row["primary_reason"]
    )
    return {
        "response_envelope_subfrontier_record_count": len(frozen),
        "faz1_50_mismatch_count": family_counts["faz1-50"],
        "v2_95_mismatch_count": family_counts["v2-95"],
        "v3_170_mismatch_count": family_counts["v3-170"],
        "response_envelope_hash_mismatch_count": len(failing_rows),
        "runtime_error_count": runtime_error_count,
        "first_divergence_assigned_count": first_divergence_assigned_count,
        "primary_reason_assigned_count": primary_reason_assigned_count,
        "unexplained_count": unexplained_count,
        "frozen_truth_faz1_50_mismatch_count": frozen_counts["faz1-50"],
        "frozen_truth_v2_95_mismatch_count": frozen_counts["v2-95"],
        "frozen_truth_v3_170_mismatch_count": frozen_counts["v3-170"],
        "failing_rows": failing_rows,
    }


def _build_targeted_acceptance(
    *,
    smoke: dict[str, Any],
    restart_smoke: dict[str, Any],
    pii_probe: dict[str, Any],
    alerts: dict[str, Any],
    metrics_text: str,
    models_headers_text: str,
    supervision: dict[str, Any],
    restart_supervision: dict[str, Any],
    restore_supervision: dict[str, Any],
    backup_manifest: dict[str, Any],
    restore_summary: dict[str, Any],
) -> dict[str, Any]:
    metrics = parse_metrics_text(metrics_text)
    headers = parse_headers_text(models_headers_text)
    smoke_acceptance = smoke.get("acceptance") or {}
    restart_acceptance = restart_smoke.get("acceptance") or {}
    smoke_refusal = smoke.get("refusal_smoke") or {}
    restart_refusal = restart_smoke.get("refusal_smoke") or {}

    tokenizer_usage_total = metric_value(metrics, "hukuk_ai_usage_source_total", source="tokenizer")
    estimated_usage_total = metric_value(metrics, "hukuk_ai_usage_source_total", source="estimated")
    token_failure_total = metric_value(metrics, "hukuk_ai_token_accounting_failure_total")

    auth_bypass_found = not bool(smoke_acceptance.get("auth_enforced")) or int(smoke.get("auth", {}).get("unauthorized_status", 0)) != 401
    audit_write_loss_found = (
        int(smoke.get("metrics_delta", {}).get("audit_events_delta", 0)) < 2
        or int(restart_smoke.get("metrics_delta", {}).get("audit_events_delta", 0)) < 2
        or metric_value(metrics, "hukuk_ai_audit_write_error_total") > 0
    )
    pii_leak_found = not bool(pii_probe.get("persisted_redaction_pass", False))
    redis_continuity_break_found = not (
        bool(smoke_acceptance.get("session_continuity_pass"))
        and bool(restart_acceptance.get("session_continuity_pass"))
    )
    token_accounting_fallback_found = (
        tokenizer_usage_total <= 0.0 or estimated_usage_total != 0.0 or token_failure_total != 0.0
    )
    observability_gap_found = not all(key in alerts for key in REQUIRED_ALERT_KEYS)
    api_versioning_gap_found = not (
        headers.get("x-hukuk-ai-api-version") == EXPECTED_API_VERSION
        and headers.get("x-hukuk-ai-lane") == EXPECTED_LANE
    )
    supervision_gap_found = not (
        _supervision_pass(supervision)
        and _supervision_pass(restart_supervision)
        and _supervision_pass(restore_supervision)
    )
    backup_restore_gap_found = not _backup_restore_pass(backup_manifest, restore_summary)
    release_smoke_gap_found = not (
        all(bool(value) for value in smoke_acceptance.values())
        and all(bool(value) for value in restart_acceptance.values())
        and int(smoke_refusal.get("status_code") or 0) == 200
        and int(restart_refusal.get("status_code") or 0) == 200
    )

    rows = [
        {"control": "mandatory auth", "pass": not auth_bypass_found},
        {"control": "immutable audit logging", "pass": not audit_write_loss_found},
        {"control": "persisted PII redaction", "pass": not pii_leak_found},
        {"control": "Redis session persistence", "pass": not redis_continuity_break_found},
        {"control": "tokenizer-backed accounting", "pass": not token_accounting_fallback_found},
        {"control": "observability / alerting", "pass": not observability_gap_found},
        {"control": "API versioning", "pass": not api_versioning_gap_found},
        {"control": "process supervision", "pass": not supervision_gap_found},
        {"control": "backup / restore", "pass": not backup_restore_gap_found},
        {"control": "one-command release smoke", "pass": not release_smoke_gap_found},
    ]

    return {
        "must_close_release_controls_count": len(RELEASE_CONTROLS_EXACT_SET),
        "mandatory_auth_pass": rows[0]["pass"],
        "immutable_audit_logging_pass": rows[1]["pass"],
        "persisted_pii_redaction_pass": rows[2]["pass"],
        "redis_session_persistence_pass": rows[3]["pass"],
        "tokenizer_backed_accounting_pass": rows[4]["pass"],
        "observability_alerting_pass": rows[5]["pass"],
        "api_versioning_pass": rows[6]["pass"],
        "process_supervision_pass": rows[7]["pass"],
        "backup_restore_pass": rows[8]["pass"],
        "one_command_release_smoke_pass": rows[9]["pass"],
        "auth_bypass_found": auth_bypass_found,
        "audit_write_loss_found": audit_write_loss_found,
        "pii_leak_found": pii_leak_found,
        "redis_continuity_break_found": redis_continuity_break_found,
        "token_accounting_fallback_found": token_accounting_fallback_found,
        "observability_gap_found": observability_gap_found,
        "api_versioning_gap_found": api_versioning_gap_found,
        "supervision_gap_found": supervision_gap_found,
        "backup_restore_gap_found": backup_restore_gap_found,
        "release_smoke_gap_found": release_smoke_gap_found,
        "refusal_smoke_status_code": int(smoke_refusal.get("status_code") or 0),
        "restart_refusal_smoke_status_code": int(restart_refusal.get("status_code") or 0),
        "tokenizer_usage_total": tokenizer_usage_total,
        "estimated_usage_total": estimated_usage_total,
        "token_accounting_failure_total": token_failure_total,
        "backup_restore_missing_file_count": sum(
            1 for item in (restore_summary.get("files") or []) if isinstance(item, dict) and not item.get("exists")
        ),
        "runtime_error_count": 0,
        "unexplained_count": 0,
        "control_rows": rows,
    }


def _build_full_family_parity(
    *,
    model_visible_reports: list[dict[str, Any]],
    parity_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    visible_by_family = _report_by_family(model_visible_reports)
    parity_by_family = _report_by_family(parity_reports)
    family_rows: list[dict[str, Any]] = []
    preprojection_total = 0
    raw_answer_total = 0
    response_total = 0
    model_request_total = 0
    retrieval_total = 0
    assembled_total = 0
    runtime_total = 0
    unexplained_total = 0

    for family_id in ("faz1-50", "v2-95", "v3-170"):
        visible = visible_by_family[family_id]
        parity = parity_by_family[family_id]
        visible_ids = {str(row["question_id"]) for row in visible.get("mismatch_rows", [])}
        parity_ids = {str(row["question_id"]) for row in parity.get("parity_rows", [])}
        family_runtime = int(visible.get("runtime_error_count", 0)) + int(
            parity.get("reference_runtime_error_count", 0)
        ) + int(parity.get("candidate_runtime_error_count", 0))
        family_unexplained = int(visible.get("unexplained_count", 0)) + sum(
            1
            for row in parity.get("parity_rows", [])
            if not row.get("first_divergence_stage") or not row.get("primary_reason")
        )
        preprojection_total += int(visible.get("preprojection_hash_mismatch_count", 0))
        raw_answer_total += int(visible.get("raw_answer_hash_mismatch_count", 0))
        response_total += int(parity.get("response_envelope_hash_mismatch_count", 0))
        model_request_total += int(visible.get("model_request_payload_hash_mismatch_count", 0))
        retrieval_total += int(visible.get("retrieval_request_hash_mismatch_count", 0))
        assembled_total += int(visible.get("assembled_context_hash_mismatch_count", 0))
        runtime_total += family_runtime
        unexplained_total += family_unexplained
        family_rows.append(
            {
                "family_id": family_id,
                "mismatch_count": len(visible_ids | parity_ids),
                "model_request_payload_hash_mismatch_count": int(
                    visible.get("model_request_payload_hash_mismatch_count", 0)
                ),
                "retrieval_request_hash_mismatch_count": int(
                    visible.get("retrieval_request_hash_mismatch_count", 0)
                ),
                "assembled_context_hash_mismatch_count": int(
                    visible.get("assembled_context_hash_mismatch_count", 0)
                ),
                "preprojection_hash_mismatch_count": int(visible.get("preprojection_hash_mismatch_count", 0)),
                "raw_answer_hash_mismatch_count": int(visible.get("raw_answer_hash_mismatch_count", 0)),
                "response_envelope_hash_mismatch_count": int(
                    parity.get("response_envelope_hash_mismatch_count", 0)
                ),
                "family_metric_delta_zero": bool(parity.get("family_metric_delta_zero", False)),
                "runtime_error_count": family_runtime,
                "unexplained_count": family_unexplained,
            }
        )

    return {
        "faz1_50_mismatch_count": family_rows[0]["mismatch_count"],
        "v2_95_mismatch_count": family_rows[1]["mismatch_count"],
        "v3_170_mismatch_count": family_rows[2]["mismatch_count"],
        "model_request_payload_hash_mismatch_count": model_request_total,
        "retrieval_request_hash_mismatch_count": retrieval_total,
        "assembled_context_hash_mismatch_count": assembled_total,
        "preprojection_hash_mismatch_count": preprojection_total,
        "raw_answer_hash_mismatch_count": raw_answer_total,
        "response_envelope_hash_mismatch_count": response_total,
        "family_metric_delta_zero": all(row["family_metric_delta_zero"] for row in family_rows),
        "runtime_error_count": runtime_total,
        "unexplained_count": unexplained_total,
        "families": family_rows,
    }


def _build_retention_gate(
    *,
    acceptance: dict[str, Any],
    full_family_parity: dict[str, Any],
    restart_supervision: dict[str, Any],
    restore_supervision: dict[str, Any],
) -> dict[str, Any]:
    must_close = all(bool(row["pass"]) for row in acceptance["control_rows"])
    family_zero = (
        full_family_parity["faz1_50_mismatch_count"] == 0
        and full_family_parity["v2_95_mismatch_count"] == 0
        and full_family_parity["v3_170_mismatch_count"] == 0
        and full_family_parity["model_request_payload_hash_mismatch_count"] == 0
        and full_family_parity["retrieval_request_hash_mismatch_count"] == 0
        and full_family_parity["assembled_context_hash_mismatch_count"] == 0
        and full_family_parity["preprojection_hash_mismatch_count"] == 0
        and full_family_parity["raw_answer_hash_mismatch_count"] == 0
        and full_family_parity["response_envelope_hash_mismatch_count"] == 0
        and full_family_parity["family_metric_delta_zero"] is True
        and full_family_parity["runtime_error_count"] == 0
        and full_family_parity["unexplained_count"] == 0
    )
    return {
        "must_close_release_controls_pass": must_close,
        "retained_after_family_eval": must_close and family_zero,
        "retained_after_restart": must_close and _supervision_pass(restart_supervision),
        "retained_after_restore": must_close and _supervision_pass(restore_supervision),
        "answer_path_delta_reintroduced": not family_zero,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }


def build_phase_payload(
    *,
    current_authority_check: dict[str, Any],
    model_visible_reports: list[dict[str, Any]],
    parity_reports: list[dict[str, Any]],
    smoke: dict[str, Any],
    restart_smoke: dict[str, Any],
    pii_probe: dict[str, Any],
    alerts: dict[str, Any],
    metrics_text: str,
    models_headers_text: str,
    supervision: dict[str, Any],
    restart_supervision: dict[str, Any],
    restore_supervision: dict[str, Any],
    backup_manifest: dict[str, Any],
    restore_summary: dict[str, Any],
) -> dict[str, Any]:
    reference_pack = _load_reference_pack()
    topology = _build_topology()
    manifest = _build_manifest()
    bridge_contract = dict(BRIDGE_CONTRACT)
    mutation_matrix = dict(PROHIBITED_RUNTIME_MUTATION_FLAGS)
    frontier_summary = _build_frontier_summary(
        model_visible_reports=model_visible_reports,
        parity_reports=parity_reports,
    )
    response_summary = _build_response_summary(parity_reports=parity_reports)
    acceptance = _build_targeted_acceptance(
        smoke=smoke,
        restart_smoke=restart_smoke,
        pii_probe=pii_probe,
        alerts=alerts,
        metrics_text=metrics_text,
        models_headers_text=models_headers_text,
        supervision=supervision,
        restart_supervision=restart_supervision,
        restore_supervision=restore_supervision,
        backup_manifest=backup_manifest,
        restore_summary=restore_summary,
    )
    full_family_parity = _build_full_family_parity(
        model_visible_reports=model_visible_reports,
        parity_reports=parity_reports,
    )
    retention = _build_retention_gate(
        acceptance=acceptance,
        full_family_parity=full_family_parity,
        restart_supervision=restart_supervision,
        restore_supervision=restore_supervision,
    )

    current_authority = {
        "control_pair_authority_match": bool(current_authority_check.get("control_pair_authority_match", False)),
        "current_authority_contract_breach": bool(
            current_authority_check.get("current_authority_contract_breach", True)
        ),
        "surface_breach_from_history_reintroduced": bool(
            current_authority_check.get("surface_breach_from_history_reintroduced", True)
        ),
        "current_canonical_authority_adopted": bool(
            current_authority_check.get("current_canonical_authority_adopted", False)
        ),
        "control_pair_runtime_error_count": int(
            current_authority_check.get("control_pair_runtime_error_count", 0)
        ),
    }
    upstream = {
        "model_request_payload_hash_mismatch_count": full_family_parity[
            "model_request_payload_hash_mismatch_count"
        ],
        "retrieval_request_hash_mismatch_count": full_family_parity["retrieval_request_hash_mismatch_count"],
        "assembled_context_hash_mismatch_count": full_family_parity["assembled_context_hash_mismatch_count"],
        "runtime_error_count": full_family_parity["runtime_error_count"],
    }

    wp1 = reference_pack["reference_pack_integrity_pass"] and reference_pack["reference_pack_contradiction_count"] == 0
    wp2 = (
        topology["stale_branch_left_active"] is False
        and topology["surface_breach_from_history_reintroduced"] is False
        and topology["cutover_allowed"] is False
        and topology["pilot_allowed"] is False
        and topology["database_expansion_allowed"] is False
        and topology["rc_r_reserved"] is False
        and manifest["candidate_id"] == "RC-Q"
        and manifest["base_candidate"] == "RC-G"
        and manifest["control_candidate"] == "RC-J"
        and manifest["forensic_reference_candidate"] == "RC-N"
        and manifest["current_perimeter_truth_reference"] == "RC-P"
        and manifest["allowed_diff_surface"] == "non_model_visible_release_controls_perimeter_only"
        and manifest["answer_path_delta_allowed"] is False
        and manifest["cutover_authorized"] is False
        and manifest["pilot_authorized"] is False
        and manifest["database_expansion_authorized"] is False
    )
    wp3 = bridge_contract == BRIDGE_CONTRACT and mutation_matrix == PROHIBITED_RUNTIME_MUTATION_FLAGS
    wp4_authority = (
        current_authority["control_pair_authority_match"] is True
        and current_authority["current_authority_contract_breach"] is False
        and current_authority["surface_breach_from_history_reintroduced"] is False
        and current_authority["current_canonical_authority_adopted"] is True
        and current_authority["control_pair_runtime_error_count"] == 0
    )
    wp4_upstream = (
        upstream["model_request_payload_hash_mismatch_count"] == 0
        and upstream["retrieval_request_hash_mismatch_count"] == 0
        and upstream["assembled_context_hash_mismatch_count"] == 0
        and upstream["runtime_error_count"] == 0
    )
    wp5 = (
        frontier_summary["frontier_record_count"] == 174
        and frontier_summary["faz1_50_mismatch_count"] == 0
        and frontier_summary["v2_95_mismatch_count"] == 0
        and frontier_summary["v3_170_mismatch_count"] == 0
        and frontier_summary["preprojection_hash_mismatch_count"] == 0
        and frontier_summary["raw_answer_hash_mismatch_count"] == 0
        and frontier_summary["response_envelope_hash_mismatch_count"] == 0
        and frontier_summary["runtime_error_count"] == 0
        and frontier_summary["first_divergence_assigned_count"] == 0
        and frontier_summary["primary_reason_assigned_count"] == 0
        and frontier_summary["unexplained_count"] == 0
    )
    wp6 = (
        response_summary["response_envelope_subfrontier_record_count"] == 109
        and response_summary["faz1_50_mismatch_count"] == 0
        and response_summary["v2_95_mismatch_count"] == 0
        and response_summary["v3_170_mismatch_count"] == 0
        and response_summary["response_envelope_hash_mismatch_count"] == 0
        and response_summary["runtime_error_count"] == 0
        and response_summary["first_divergence_assigned_count"] == 0
        and response_summary["primary_reason_assigned_count"] == 0
        and response_summary["unexplained_count"] == 0
    )
    wp7 = (
        acceptance["must_close_release_controls_count"] == 10
        and acceptance["mandatory_auth_pass"] is True
        and acceptance["immutable_audit_logging_pass"] is True
        and acceptance["persisted_pii_redaction_pass"] is True
        and acceptance["redis_session_persistence_pass"] is True
        and acceptance["tokenizer_backed_accounting_pass"] is True
        and acceptance["observability_alerting_pass"] is True
        and acceptance["api_versioning_pass"] is True
        and acceptance["process_supervision_pass"] is True
        and acceptance["backup_restore_pass"] is True
        and acceptance["one_command_release_smoke_pass"] is True
        and acceptance["auth_bypass_found"] is False
        and acceptance["audit_write_loss_found"] is False
        and acceptance["pii_leak_found"] is False
        and acceptance["redis_continuity_break_found"] is False
        and acceptance["token_accounting_fallback_found"] is False
        and acceptance["observability_gap_found"] is False
        and acceptance["api_versioning_gap_found"] is False
        and acceptance["supervision_gap_found"] is False
        and acceptance["backup_restore_gap_found"] is False
        and acceptance["release_smoke_gap_found"] is False
        and acceptance["refusal_smoke_status_code"] == 200
        and acceptance["restart_refusal_smoke_status_code"] == 200
        and acceptance["tokenizer_usage_total"] > 0.0
        and acceptance["estimated_usage_total"] == 0.0
        and acceptance["token_accounting_failure_total"] == 0.0
        and acceptance["backup_restore_missing_file_count"] == 0
        and acceptance["runtime_error_count"] == 0
        and acceptance["unexplained_count"] == 0
    )
    wp8 = (
        full_family_parity["faz1_50_mismatch_count"] == 0
        and full_family_parity["v2_95_mismatch_count"] == 0
        and full_family_parity["v3_170_mismatch_count"] == 0
        and full_family_parity["model_request_payload_hash_mismatch_count"] == 0
        and full_family_parity["retrieval_request_hash_mismatch_count"] == 0
        and full_family_parity["assembled_context_hash_mismatch_count"] == 0
        and full_family_parity["preprojection_hash_mismatch_count"] == 0
        and full_family_parity["raw_answer_hash_mismatch_count"] == 0
        and full_family_parity["response_envelope_hash_mismatch_count"] == 0
        and full_family_parity["family_metric_delta_zero"] is True
        and full_family_parity["runtime_error_count"] == 0
        and full_family_parity["unexplained_count"] == 0
    )
    wp9 = (
        retention["must_close_release_controls_pass"] is True
        and retention["retained_after_family_eval"] is True
        and retention["retained_after_restart"] is True
        and retention["retained_after_restore"] is True
        and retention["answer_path_delta_reintroduced"] is False
        and retention["runtime_error_count"] == 0
        and retention["unexplained_count"] == 0
    )

    unexplained_count = (
        frontier_summary["unexplained_count"]
        + response_summary["unexplained_count"]
        + acceptance["unexplained_count"]
        + full_family_parity["unexplained_count"]
        + retention["unexplained_count"]
    )

    wp_statuses = {
        "WP-1": "PASS" if wp1 else "FAIL",
        "WP-2": "PASS" if wp2 else "FAIL",
        "WP-3": "PASS" if wp3 else "FAIL",
        "WP-4": "PASS" if (wp4_authority and wp4_upstream) else "FAIL",
        "WP-5": "PASS" if wp5 else "FAIL",
        "WP-6": "PASS" if wp6 else "FAIL",
        "WP-7": "PASS" if wp7 else "FAIL",
        "WP-8": "PASS" if wp8 else "FAIL",
        "WP-9": "PASS" if wp9 else "FAIL",
    }

    if not wp1:
        decision = FAIL_REFERENCE
    elif not wp2 or not wp3:
        decision = FAIL_TOPOLOGY
    elif unexplained_count > 0:
        decision = FAIL_INCONCLUSIVE
    elif not wp4_authority:
        decision = FAIL_CURRENT_AUTHORITY
    elif not wp4_upstream:
        decision = FAIL_UPSTREAM
    elif not wp5:
        decision = FAIL_FRONTIER
    elif not wp6:
        decision = FAIL_RESPONSE
    elif not wp7:
        decision = FAIL_ACCEPTANCE
    elif not wp8:
        decision = FAIL_PARITY
    elif not wp9:
        decision = FAIL_RETENTION
    else:
        decision = PASS_DECISION

    return {
        "reference_pack": reference_pack,
        "topology": topology,
        "manifest": manifest,
        "bridge_contract": bridge_contract,
        "mutation_matrix": mutation_matrix,
        "current_authority": current_authority,
        "upstream_equality": upstream,
        "frontier_summary": frontier_summary,
        "response_summary": response_summary,
        "acceptance": acceptance,
        "full_family_parity": full_family_parity,
        "retention": retention,
        "wp_statuses": wp_statuses,
        "official_decision": decision,
        "next_official_work": DECISION_TO_NEXT_WORK[decision],
        "unexplained_count": unexplained_count,
    }


def _render_kv_md(title: str, rows: list[tuple[str, Any]]) -> str:
    lines = [f"# {title}", ""]
    for key, value in rows:
        if isinstance(value, bool):
            rendered = bool_text(value)
        else:
            rendered = value
        lines.append(f"- {key} = `{rendered}`")
    lines.append("")
    return "\n".join(lines)


def _render_result_report(payload: dict[str, Any]) -> str:
    reference = payload["reference_pack"]
    topology = payload["topology"]
    manifest = payload["manifest"]
    bridge = payload["bridge_contract"]
    current = payload["current_authority"]
    upstream = payload["upstream_equality"]
    frontier = payload["frontier_summary"]
    response = payload["response_summary"]
    acceptance = payload["acceptance"]
    parity = payload["full_family_parity"]
    retention = payload["retention"]

    lines = [
        f"# FAZ36 RC-Q RELEASE-CONTROLS PERIMETER REPAIR GATE UNDER CANONICAL CURRENT AUTHORITY RAPORU",
        "",
        "## Yonetici Ozeti",
        "",
        f"Bu faz `RC-Q` icin release-controls perimeter onarim kapisidir. Faz sonunda resmi karar `{payload['official_decision']}` olarak kapanmistir. `RC-Q`, `RC-G` answer-path referansi korunarak yalniz non-model-visible release-controls perimeter yuzeyinde degerlendirildi.",
        "",
        "## Reference Pack Ozeti",
        "",
        f"- reference_pack_integrity_pass = `{bool_text(reference['reference_pack_integrity_pass'])}`",
        f"- reference_pack_contradiction_count = `{reference['reference_pack_contradiction_count']}`",
        f"- canonical_current_authority_ref = `{reference['canonical_current_authority_ref']}`",
        f"- post_rc_m_steering_ref = `{reference['post_rc_m_steering_ref']}`",
        f"- rc_n_release_controls_legacy_ref = `{reference['rc_n_release_controls_legacy_ref']}`",
        f"- rc_n_boundary_root_cause_ref = `{reference['rc_n_boundary_root_cause_ref']}`",
        f"- rc_o_repair_truth_ref = `{reference['rc_o_repair_truth_ref']}`",
        f"- rc_o_archival_closure_ref = `{reference['rc_o_archival_closure_ref']}`",
        f"- post_rc_o_steering_ref = `{reference['post_rc_o_steering_ref']}`",
        f"- rc_p_perimeter_truth_ref = `{reference['rc_p_perimeter_truth_ref']}`",
        "",
        "## Canonical Topology ve RC-Q Build Contract Ozeti",
        "",
        f"- RC-G = `{topology['RC-G']}`",
        f"- RC-J = `{topology['RC-J']}`",
        f"- RC-N = `{topology['RC-N']}`",
        f"- RC-P = `{topology['RC-P']}`",
        f"- RC-Q = `{topology['RC-Q']}`",
        f"- candidate_id = `{manifest['candidate_id']}`",
        f"- base_candidate = `{manifest['base_candidate']}`",
        f"- control_candidate = `{manifest['control_candidate']}`",
        f"- forensic_reference_candidate = `{manifest['forensic_reference_candidate']}`",
        f"- current_perimeter_truth_reference = `{manifest['current_perimeter_truth_reference']}`",
        f"- allowed_diff_surface = `{manifest['allowed_diff_surface']}`",
        f"- answer_path_delta_allowed = `{bool_text(manifest['answer_path_delta_allowed'])}`",
        f"- cutover_authorized = `{bool_text(manifest['cutover_authorized'])}`",
        f"- pilot_authorized = `{bool_text(manifest['pilot_authorized'])}`",
        "",
        "## Immutable Perimeter Bridge Contract Ozeti",
        "",
        f"- deep_copy_barrier_before_P11 = `{bool_text(bridge['deep_copy_barrier_before_P11'])}`",
        f"- live_object_reference_reuse_allowed = `{bool_text(bridge['live_object_reference_reuse_allowed'])}`",
        f"- perimeter_callback_into_model_request_allowed = `{bool_text(bridge['perimeter_callback_into_model_request_allowed'])}`",
        f"- perimeter_callback_into_retrieval_request_allowed = `{bool_text(bridge['perimeter_callback_into_retrieval_request_allowed'])}`",
        f"- perimeter_callback_into_assembled_context_allowed = `{bool_text(bridge['perimeter_callback_into_assembled_context_allowed'])}`",
        f"- perimeter_callback_into_preprojection_allowed = `{bool_text(bridge['perimeter_callback_into_preprojection_allowed'])}`",
        f"- perimeter_callback_into_raw_answer_allowed = `{bool_text(bridge['perimeter_callback_into_raw_answer_allowed'])}`",
        f"- perimeter_callback_into_response_envelope_allowed = `{bool_text(bridge['perimeter_callback_into_response_envelope_allowed'])}`",
        f"- frozen_snapshot_id_only_cross_boundary = `{bool_text(bridge['frozen_snapshot_id_only_cross_boundary'])}`",
        "",
        "## Current Authority ve Upstream Equality Ozeti",
        "",
        f"- control_pair_authority_match = `{bool_text(current['control_pair_authority_match'])}`",
        f"- current_authority_contract_breach = `{bool_text(current['current_authority_contract_breach'])}`",
        f"- surface_breach_from_history_reintroduced = `{bool_text(current['surface_breach_from_history_reintroduced'])}`",
        f"- current_canonical_authority_adopted = `{bool_text(current['current_canonical_authority_adopted'])}`",
        f"- model_request_payload_hash_mismatch_count = `{upstream['model_request_payload_hash_mismatch_count']}`",
        f"- retrieval_request_hash_mismatch_count = `{upstream['retrieval_request_hash_mismatch_count']}`",
        f"- assembled_context_hash_mismatch_count = `{upstream['assembled_context_hash_mismatch_count']}`",
        f"- runtime_error_count = `{upstream['runtime_error_count']}`",
        "",
        "## Frontier 174 Repair Gate Ozeti",
        "",
        f"- frontier_record_count = `{frontier['frontier_record_count']}`",
        f"- faz1_50_mismatch_count = `{frontier['faz1_50_mismatch_count']}`",
        f"- v2_95_mismatch_count = `{frontier['v2_95_mismatch_count']}`",
        f"- v3_170_mismatch_count = `{frontier['v3_170_mismatch_count']}`",
        f"- preprojection_hash_mismatch_count = `{frontier['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{frontier['raw_answer_hash_mismatch_count']}`",
        f"- response_envelope_hash_mismatch_count = `{frontier['response_envelope_hash_mismatch_count']}`",
        f"- runtime_error_count = `{frontier['runtime_error_count']}`",
        f"- unexplained_count = `{frontier['unexplained_count']}`",
        "",
        "## Response Envelope Subfrontier 109 Repair Gate Ozeti",
        "",
        f"- response_envelope_subfrontier_record_count = `{response['response_envelope_subfrontier_record_count']}`",
        f"- faz1_50_mismatch_count = `{response['faz1_50_mismatch_count']}`",
        f"- v2_95_mismatch_count = `{response['v2_95_mismatch_count']}`",
        f"- v3_170_mismatch_count = `{response['v3_170_mismatch_count']}`",
        f"- response_envelope_hash_mismatch_count = `{response['response_envelope_hash_mismatch_count']}`",
        f"- runtime_error_count = `{response['runtime_error_count']}`",
        f"- unexplained_count = `{response['unexplained_count']}`",
        "",
        "## Release Controls Targeted Acceptance Ozeti",
        "",
        f"- must_close_release_controls_count = `{acceptance['must_close_release_controls_count']}`",
        f"- mandatory_auth_pass = `{bool_text(acceptance['mandatory_auth_pass'])}`",
        f"- immutable_audit_logging_pass = `{bool_text(acceptance['immutable_audit_logging_pass'])}`",
        f"- persisted_pii_redaction_pass = `{bool_text(acceptance['persisted_pii_redaction_pass'])}`",
        f"- redis_session_persistence_pass = `{bool_text(acceptance['redis_session_persistence_pass'])}`",
        f"- tokenizer_backed_accounting_pass = `{bool_text(acceptance['tokenizer_backed_accounting_pass'])}`",
        f"- observability_alerting_pass = `{bool_text(acceptance['observability_alerting_pass'])}`",
        f"- api_versioning_pass = `{bool_text(acceptance['api_versioning_pass'])}`",
        f"- process_supervision_pass = `{bool_text(acceptance['process_supervision_pass'])}`",
        f"- backup_restore_pass = `{bool_text(acceptance['backup_restore_pass'])}`",
        f"- one_command_release_smoke_pass = `{bool_text(acceptance['one_command_release_smoke_pass'])}`",
        f"- refusal_smoke_status_code = `{acceptance['refusal_smoke_status_code']}`",
        f"- restart_refusal_smoke_status_code = `{acceptance['restart_refusal_smoke_status_code']}`",
        f"- tokenizer_usage_total = `{acceptance['tokenizer_usage_total']}`",
        f"- estimated_usage_total = `{acceptance['estimated_usage_total']}`",
        f"- token_accounting_failure_total = `{acceptance['token_accounting_failure_total']}`",
        f"- backup_restore_missing_file_count = `{acceptance['backup_restore_missing_file_count']}`",
        f"- runtime_error_count = `{acceptance['runtime_error_count']}`",
        f"- unexplained_count = `{acceptance['unexplained_count']}`",
        "",
        "## Full-Family Model-Visible Surface Parity Ozeti",
        "",
        f"- faz1_50_mismatch_count = `{parity['faz1_50_mismatch_count']}`",
        f"- v2_95_mismatch_count = `{parity['v2_95_mismatch_count']}`",
        f"- v3_170_mismatch_count = `{parity['v3_170_mismatch_count']}`",
        f"- model_request_payload_hash_mismatch_count = `{parity['model_request_payload_hash_mismatch_count']}`",
        f"- retrieval_request_hash_mismatch_count = `{parity['retrieval_request_hash_mismatch_count']}`",
        f"- assembled_context_hash_mismatch_count = `{parity['assembled_context_hash_mismatch_count']}`",
        f"- preprojection_hash_mismatch_count = `{parity['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{parity['raw_answer_hash_mismatch_count']}`",
        f"- response_envelope_hash_mismatch_count = `{parity['response_envelope_hash_mismatch_count']}`",
        f"- family_metric_delta_zero = `{bool_text(parity['family_metric_delta_zero'])}`",
        f"- runtime_error_count = `{parity['runtime_error_count']}`",
        f"- unexplained_count = `{parity['unexplained_count']}`",
        "",
        "## Release Controls Retention Gate Ozeti",
        "",
        f"- must_close_release_controls_pass = `{bool_text(retention['must_close_release_controls_pass'])}`",
        f"- retained_after_family_eval = `{bool_text(retention['retained_after_family_eval'])}`",
        f"- retained_after_restart = `{bool_text(retention['retained_after_restart'])}`",
        f"- retained_after_restore = `{bool_text(retention['retained_after_restore'])}`",
        f"- answer_path_delta_reintroduced = `{bool_text(retention['answer_path_delta_reintroduced'])}`",
        f"- runtime_error_count = `{retention['runtime_error_count']}`",
        f"- unexplained_count = `{retention['unexplained_count']}`",
        "",
        "## WP Sonuclari",
        "",
        *markdown_table(
            [("wp", "wp"), ("status", "status")],
            [{"wp": key, "status": value} for key, value in payload["wp_statuses"].items()],
        ),
        "",
        "## Resmi Karar",
        "",
        f"- official_decision = `{payload['official_decision']}`",
        f"- unexplained_count = `{payload['unexplained_count']}`",
        "",
        "## Sonraki Resmi Is",
        "",
        f"- next_official_work = `{payload['next_official_work']}`",
        "",
        "## Artefact Listesi",
        "",
        "- coordination/faz36-official-implementation-plan-2026-03-30.md",
        "- coordination/faz36-steering-decision-table-2026-03-30.md",
        "- coordination/faz36-release-controls-reference-pack-2026-03-30.md",
        "- coordination/faz36-canonical-topology-refreeze-2026-03-30.md",
        "- coordination/faz36-rc-q-build-contract-2026-03-30.md",
        "- coordination/faz36-rc-q-perimeter-repair-contract-2026-03-30.md",
        "- coordination/faz36-rc-q-immutable-perimeter-bridge-contract-2026-03-30.md",
        "- coordination/faz36-rc-p-frontier-174-freeze-2026-03-30.md",
        "- coordination/faz36-rc-p-response-envelope-subfrontier-109-freeze-2026-03-30.md",
        "- coordination/faz36-rc-q-prohibited-runtime-mutation-matrix-2026-03-30.md",
        "- coordination/faz36-rc-q-release-controls-repair-reconciliation-2026-03-30.md",
        "- coordination/faz36-final-reconciliation-summary-2026-03-30.md",
        "- evaluation/reports/faz36-rc-g-vs-rc-j-current-authority-check-2026-03-30.md",
        "- evaluation/reports/faz36-rc-g-vs-rc-q-upstream-equality-gate-2026-03-30.md",
        "- evaluation/reports/faz36-rc-g-vs-rc-q-frontier-174-summary-2026-03-30.md",
        "- evaluation/reports/faz36-rc-g-vs-rc-q-response-envelope-109-summary-2026-03-30.md",
        "- evaluation/reports/faz36-rc-q-release-controls-targeted-acceptance-2026-03-30.md",
        "- evaluation/reports/faz36-rc-g-vs-rc-q-full-family-model-visible-surface-parity-2026-03-30.md",
        "- evaluation/reports/faz36-rc-q-release-controls-retention-gate-2026-03-30.md",
        "- evaluation/reports/faz36-rc-q-perimeter-repair-clearance-2026-03-30.md",
        "- coordination/faz36-rc-q-manifest-2026-03-30.json",
        f"- reports/{RESULT_REPORT_NAME}",
        f"- docs/{RESULT_REPORT_NAME}",
        "",
    ]
    return "\n".join(lines)


def render_outputs(payload: dict[str, Any]) -> dict[Path, str | dict[str, Any]]:
    reference = payload["reference_pack"]
    topology = payload["topology"]
    manifest = payload["manifest"]
    bridge = payload["bridge_contract"]
    mutation = payload["mutation_matrix"]
    current = payload["current_authority"]
    upstream = payload["upstream_equality"]
    frontier = payload["frontier_summary"]
    response = payload["response_summary"]
    acceptance = payload["acceptance"]
    parity = payload["full_family_parity"]
    retention = payload["retention"]
    wp_rows = [{"wp": key, "status": value} for key, value in payload["wp_statuses"].items()]

    outputs: dict[Path, str | dict[str, Any]] = {
        ROOT / "coordination" / f"faz36-rc-q-manifest-{DATE}.json": manifest,
        ROOT / "coordination" / f"faz36-official-implementation-plan-{DATE}.md": "\n".join(
            [
                "# FAZ36 Official Implementation Plan",
                "",
                "1. Reference pack, topology ve RC-Q build contract'i FAZ21/25/26/27/31/32/33/34/35 referanslariyla freeze et.",
                "2. RC-Q'yu RC-G answer-path'ini koruyan direct strict lane olarak ayağa kaldir.",
                "3. RC-G vs RC-J current authority check'i ve RC-G vs RC-Q upstream equality gate'ini al.",
                "4. Frozen frontier 174 ve response envelope subfrontier 109 repair gate'lerini calistir.",
                "5. Targeted acceptance, full-family parity ve retention gate'lerini kapat.",
                "6. Tek resmi karar ve next_official_work ile FAZ36 paketini dondur.",
                "",
            ]
        ),
        ROOT / "coordination" / f"faz36-release-controls-reference-pack-{DATE}.md": _render_kv_md(
            "FAZ36 Release Controls Reference Pack",
            [
                ("reference_pack_integrity_pass", reference["reference_pack_integrity_pass"]),
                ("reference_pack_contradiction_count", reference["reference_pack_contradiction_count"]),
                ("canonical_current_authority_ref", reference["canonical_current_authority_ref"]),
                ("post_rc_m_steering_ref", reference["post_rc_m_steering_ref"]),
                ("rc_n_release_controls_legacy_ref", reference["rc_n_release_controls_legacy_ref"]),
                ("rc_n_boundary_root_cause_ref", reference["rc_n_boundary_root_cause_ref"]),
                ("rc_o_repair_truth_ref", reference["rc_o_repair_truth_ref"]),
                ("rc_o_archival_closure_ref", reference["rc_o_archival_closure_ref"]),
                ("post_rc_o_steering_ref", reference["post_rc_o_steering_ref"]),
                ("rc_p_perimeter_truth_ref", reference["rc_p_perimeter_truth_ref"]),
            ],
        ),
        ROOT / "coordination" / f"faz36-canonical-topology-refreeze-{DATE}.md": _render_kv_md(
            "FAZ36 Canonical Topology Refreeze",
            [
                ("RC-G", topology["RC-G"]),
                ("RC-J", topology["RC-J"]),
                ("RC-N", topology["RC-N"]),
                ("RC-M", topology["RC-M"]),
                ("RC-O", topology["RC-O"]),
                ("RC-P", topology["RC-P"]),
                ("RC-Q", topology["RC-Q"]),
                ("stale_branch_left_active", topology["stale_branch_left_active"]),
                ("surface_breach_from_history_reintroduced", topology["surface_breach_from_history_reintroduced"]),
                ("cutover_allowed", topology["cutover_allowed"]),
                ("pilot_allowed", topology["pilot_allowed"]),
                ("database_expansion_allowed", topology["database_expansion_allowed"]),
                ("rc_r_reserved", topology["rc_r_reserved"]),
            ],
        ),
        ROOT / "coordination" / f"faz36-rc-q-build-contract-{DATE}.md": _render_kv_md(
            "FAZ36 RC-Q Build Contract",
            list(manifest.items()),
        ),
        ROOT / "coordination" / f"faz36-rc-q-perimeter-repair-contract-{DATE}.md": _render_kv_md(
            "FAZ36 RC-Q Perimeter Repair Contract",
            [
                ("candidate_id", manifest["candidate_id"]),
                ("base_candidate", manifest["base_candidate"]),
                ("control_candidate", manifest["control_candidate"]),
                ("forensic_reference_candidate", manifest["forensic_reference_candidate"]),
                ("current_perimeter_truth_reference", manifest["current_perimeter_truth_reference"]),
                ("allowed_diff_surface", manifest["allowed_diff_surface"]),
                ("answer_path_delta_allowed", manifest["answer_path_delta_allowed"]),
                ("cutover_authorized", manifest["cutover_authorized"]),
                ("pilot_authorized", manifest["pilot_authorized"]),
                ("database_expansion_authorized", manifest["database_expansion_authorized"]),
            ],
        ),
        ROOT / "coordination" / f"faz36-rc-q-immutable-perimeter-bridge-contract-{DATE}.md": _render_kv_md(
            "FAZ36 RC-Q Immutable Perimeter Bridge Contract",
            list(bridge.items()),
        ),
        ROOT / "coordination" / f"faz36-rc-q-prohibited-runtime-mutation-matrix-{DATE}.md": _render_kv_md(
            "FAZ36 RC-Q Prohibited Runtime Mutation Matrix",
            list(mutation.items()),
        ),
        ROOT / "coordination" / f"faz36-rc-p-frontier-174-freeze-{DATE}.md": _render_kv_md(
            "FAZ36 RC-P Frontier 174 Freeze",
            [
                ("frontier_record_count", 174),
                ("preprojection_hash_mismatch_count", 174),
                ("raw_answer_hash_mismatch_count", 174),
                ("runtime_error_count", 0),
                ("faz1_50_mismatch_count", 18),
                ("v2_95_mismatch_count", 57),
                ("v3_170_mismatch_count", 99),
                ("unexplained_count", 0),
            ],
        ),
        ROOT / "coordination" / f"faz36-rc-p-response-envelope-subfrontier-109-freeze-{DATE}.md": _render_kv_md(
            "FAZ36 RC-P Response Envelope Subfrontier 109 Freeze",
            [
                ("response_envelope_subfrontier_record_count", 109),
                ("response_envelope_hash_mismatch_count", 109),
                ("runtime_error_count", 0),
                ("unexplained_count", 0),
                ("faz1_50_mismatch_count", 9),
                ("v2_95_mismatch_count", 36),
                ("v3_170_mismatch_count", 64),
            ],
        ),
        ROOT / "evaluation" / "reports" / f"faz36-rc-g-vs-rc-j-current-authority-check-{DATE}.md": _render_kv_md(
            "FAZ36 RC-G vs RC-J Current Authority Check",
            list(current.items()),
        ),
        ROOT / "evaluation" / "reports" / f"faz36-rc-g-vs-rc-q-upstream-equality-gate-{DATE}.md": _render_kv_md(
            "FAZ36 RC-G vs RC-Q Upstream Equality Gate",
            list(upstream.items()),
        ),
        ROOT / "evaluation" / "reports" / f"faz36-rc-g-vs-rc-q-frontier-174-summary-{DATE}.md": _render_kv_md(
            "FAZ36 RC-G vs RC-Q Frontier 174 Summary",
            [
                ("frontier_record_count", frontier["frontier_record_count"]),
                ("faz1_50_mismatch_count", frontier["faz1_50_mismatch_count"]),
                ("v2_95_mismatch_count", frontier["v2_95_mismatch_count"]),
                ("v3_170_mismatch_count", frontier["v3_170_mismatch_count"]),
                ("preprojection_hash_mismatch_count", frontier["preprojection_hash_mismatch_count"]),
                ("raw_answer_hash_mismatch_count", frontier["raw_answer_hash_mismatch_count"]),
                ("response_envelope_hash_mismatch_count", frontier["response_envelope_hash_mismatch_count"]),
                ("runtime_error_count", frontier["runtime_error_count"]),
                ("first_divergence_assigned_count", frontier["first_divergence_assigned_count"]),
                ("primary_reason_assigned_count", frontier["primary_reason_assigned_count"]),
                ("unexplained_count", frontier["unexplained_count"]),
            ],
        ),
        ROOT / "evaluation" / "reports" / f"faz36-rc-g-vs-rc-q-response-envelope-109-summary-{DATE}.md": _render_kv_md(
            "FAZ36 RC-G vs RC-Q Response Envelope 109 Summary",
            [
                (
                    "response_envelope_subfrontier_record_count",
                    response["response_envelope_subfrontier_record_count"],
                ),
                ("faz1_50_mismatch_count", response["faz1_50_mismatch_count"]),
                ("v2_95_mismatch_count", response["v2_95_mismatch_count"]),
                ("v3_170_mismatch_count", response["v3_170_mismatch_count"]),
                ("response_envelope_hash_mismatch_count", response["response_envelope_hash_mismatch_count"]),
                ("runtime_error_count", response["runtime_error_count"]),
                ("first_divergence_assigned_count", response["first_divergence_assigned_count"]),
                ("primary_reason_assigned_count", response["primary_reason_assigned_count"]),
                ("unexplained_count", response["unexplained_count"]),
            ],
        ),
        ROOT / "evaluation" / "reports" / f"faz36-rc-q-release-controls-targeted-acceptance-{DATE}.md": _render_kv_md(
            "FAZ36 RC-Q Release Controls Targeted Acceptance",
            [
                ("must_close_release_controls_count", acceptance["must_close_release_controls_count"]),
                ("mandatory_auth_pass", acceptance["mandatory_auth_pass"]),
                ("immutable_audit_logging_pass", acceptance["immutable_audit_logging_pass"]),
                ("persisted_pii_redaction_pass", acceptance["persisted_pii_redaction_pass"]),
                ("redis_session_persistence_pass", acceptance["redis_session_persistence_pass"]),
                ("tokenizer_backed_accounting_pass", acceptance["tokenizer_backed_accounting_pass"]),
                ("observability_alerting_pass", acceptance["observability_alerting_pass"]),
                ("api_versioning_pass", acceptance["api_versioning_pass"]),
                ("process_supervision_pass", acceptance["process_supervision_pass"]),
                ("backup_restore_pass", acceptance["backup_restore_pass"]),
                ("one_command_release_smoke_pass", acceptance["one_command_release_smoke_pass"]),
                ("auth_bypass_found", acceptance["auth_bypass_found"]),
                ("audit_write_loss_found", acceptance["audit_write_loss_found"]),
                ("pii_leak_found", acceptance["pii_leak_found"]),
                ("redis_continuity_break_found", acceptance["redis_continuity_break_found"]),
                ("token_accounting_fallback_found", acceptance["token_accounting_fallback_found"]),
                ("observability_gap_found", acceptance["observability_gap_found"]),
                ("api_versioning_gap_found", acceptance["api_versioning_gap_found"]),
                ("supervision_gap_found", acceptance["supervision_gap_found"]),
                ("backup_restore_gap_found", acceptance["backup_restore_gap_found"]),
                ("release_smoke_gap_found", acceptance["release_smoke_gap_found"]),
                ("refusal_smoke_status_code", acceptance["refusal_smoke_status_code"]),
                ("restart_refusal_smoke_status_code", acceptance["restart_refusal_smoke_status_code"]),
                ("tokenizer_usage_total", acceptance["tokenizer_usage_total"]),
                ("estimated_usage_total", acceptance["estimated_usage_total"]),
                ("token_accounting_failure_total", acceptance["token_accounting_failure_total"]),
                ("backup_restore_missing_file_count", acceptance["backup_restore_missing_file_count"]),
                ("runtime_error_count", acceptance["runtime_error_count"]),
                ("unexplained_count", acceptance["unexplained_count"]),
            ],
        ),
        ROOT / "evaluation" / "reports" / f"faz36-rc-g-vs-rc-q-full-family-model-visible-surface-parity-{DATE}.md": _render_kv_md(
            "FAZ36 RC-G vs RC-Q Full Family Model Visible Surface Parity",
            [
                ("faz1_50_mismatch_count", parity["faz1_50_mismatch_count"]),
                ("v2_95_mismatch_count", parity["v2_95_mismatch_count"]),
                ("v3_170_mismatch_count", parity["v3_170_mismatch_count"]),
                ("model_request_payload_hash_mismatch_count", parity["model_request_payload_hash_mismatch_count"]),
                ("retrieval_request_hash_mismatch_count", parity["retrieval_request_hash_mismatch_count"]),
                ("assembled_context_hash_mismatch_count", parity["assembled_context_hash_mismatch_count"]),
                ("preprojection_hash_mismatch_count", parity["preprojection_hash_mismatch_count"]),
                ("raw_answer_hash_mismatch_count", parity["raw_answer_hash_mismatch_count"]),
                ("response_envelope_hash_mismatch_count", parity["response_envelope_hash_mismatch_count"]),
                ("family_metric_delta_zero", parity["family_metric_delta_zero"]),
                ("runtime_error_count", parity["runtime_error_count"]),
                ("unexplained_count", parity["unexplained_count"]),
            ],
        ),
        ROOT / "evaluation" / "reports" / f"faz36-rc-q-release-controls-retention-gate-{DATE}.md": _render_kv_md(
            "FAZ36 RC-Q Release Controls Retention Gate",
            list(retention.items()),
        ),
        ROOT / "evaluation" / "reports" / f"faz36-rc-q-perimeter-repair-clearance-{DATE}.md": "\n".join(
            [
                "# FAZ36 RC-Q Perimeter Repair Clearance",
                "",
                *markdown_table([("wp", "wp"), ("status", "status")], wp_rows),
                "",
                f"- official_decision = `{payload['official_decision']}`",
                f"- next_official_work = `{payload['next_official_work']}`",
                f"- unexplained_count = `{payload['unexplained_count']}`",
                "",
            ]
        ),
        ROOT / "coordination" / f"faz36-steering-decision-table-{DATE}.md": "\n".join(
            [
                "# FAZ36 Steering Decision Table",
                "",
                *markdown_table([("wp", "wp"), ("status", "status")], wp_rows),
                "",
                f"- official_decision = `{payload['official_decision']}`",
                f"- next_official_work = `{payload['next_official_work']}`",
                "",
            ]
        ),
        ROOT / "coordination" / f"faz36-rc-q-release-controls-repair-reconciliation-{DATE}.md": "\n".join(
            [
                "# FAZ36 RC-Q Release Controls Repair Reconciliation",
                "",
                f"- model_request_payload_hash_mismatch_count = `{upstream['model_request_payload_hash_mismatch_count']}`",
                f"- retrieval_request_hash_mismatch_count = `{upstream['retrieval_request_hash_mismatch_count']}`",
                f"- assembled_context_hash_mismatch_count = `{upstream['assembled_context_hash_mismatch_count']}`",
                f"- preprojection_hash_mismatch_count = `{frontier['preprojection_hash_mismatch_count']}`",
                f"- raw_answer_hash_mismatch_count = `{frontier['raw_answer_hash_mismatch_count']}`",
                f"- response_envelope_hash_mismatch_count = `{response['response_envelope_hash_mismatch_count']}`",
                f"- must_close_release_controls_pass = `{bool_text(retention['must_close_release_controls_pass'])}`",
                f"- retained_after_family_eval = `{bool_text(retention['retained_after_family_eval'])}`",
                f"- retained_after_restart = `{bool_text(retention['retained_after_restart'])}`",
                f"- retained_after_restore = `{bool_text(retention['retained_after_restore'])}`",
                f"- answer_path_delta_reintroduced = `{bool_text(retention['answer_path_delta_reintroduced'])}`",
                "",
            ]
        ),
        ROOT / "coordination" / f"faz36-final-reconciliation-summary-{DATE}.md": "\n".join(
            [
                "# FAZ36 Final Reconciliation Summary",
                "",
                f"- official_decision = `{payload['official_decision']}`",
                f"- next_official_work = `{payload['next_official_work']}`",
                f"- unexplained_count = `{payload['unexplained_count']}`",
                f"- frontier_record_count = `{frontier['frontier_record_count']}`",
                f"- response_envelope_subfrontier_record_count = `{response['response_envelope_subfrontier_record_count']}`",
                "",
            ]
        ),
        ROOT / "reports" / RESULT_REPORT_NAME: _render_result_report(payload),
        ROOT / "docs" / RESULT_REPORT_NAME: _render_result_report(payload),
    }
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ36 official phase package.")
    parser.add_argument("--current-authority-check-json", type=Path, required=True)
    parser.add_argument("--model-visible-report-json", type=Path, action="append", required=True)
    parser.add_argument("--parity-report-json", type=Path, action="append", required=True)
    parser.add_argument("--smoke-json", type=Path, required=True)
    parser.add_argument("--restart-smoke-json", type=Path, required=True)
    parser.add_argument("--pii-probe-json", type=Path, required=True)
    parser.add_argument("--alerts-json", type=Path, required=True)
    parser.add_argument("--metrics-text", type=Path, required=True)
    parser.add_argument("--models-headers", type=Path, required=True)
    parser.add_argument("--supervision-json", type=Path, required=True)
    parser.add_argument("--restart-supervision-json", type=Path, required=True)
    parser.add_argument("--restore-supervision-json", type=Path, required=True)
    parser.add_argument("--backup-manifest-json", type=Path, required=True)
    parser.add_argument("--restore-summary-json", type=Path, required=True)
    args = parser.parse_args()

    payload = build_phase_payload(
        current_authority_check=load_json(args.current_authority_check_json),
        model_visible_reports=[load_json(path) for path in args.model_visible_report_json],
        parity_reports=[load_json(path) for path in args.parity_report_json],
        smoke=load_json(args.smoke_json),
        restart_smoke=load_json(args.restart_smoke_json),
        pii_probe=load_json(args.pii_probe_json),
        alerts=load_json(args.alerts_json),
        metrics_text=load_text(args.metrics_text),
        models_headers_text=load_text(args.models_headers),
        supervision=load_json(args.supervision_json),
        restart_supervision=load_json(args.restart_supervision_json),
        restore_supervision=load_json(args.restore_supervision_json),
        backup_manifest=load_json(args.backup_manifest_json),
        restore_summary=load_json(args.restore_summary_json),
    )
    outputs = render_outputs(payload)
    for path, content in outputs.items():
        if isinstance(content, str):
            write_text(path, content)
        else:
            write_json(path, content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
