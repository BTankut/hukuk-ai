#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz37_lib import (  # type: ignore
    RELEASE_CONTROLS_EXACT_SET,
    REQUIRED_ALERT_KEYS,
    build_frozen_frontier_records,
    build_frozen_response_envelope_records,
    bool_text,
    load_json,
    load_text,
    metric_value,
    parse_headers_text,
    parse_metrics_text,
    summarize_record_counts,
    write_json,
    write_text,
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

    auth_bypass_found = not bool(smoke_acceptance.get("auth_enforced")) or int(
        smoke.get("auth", {}).get("unauthorized_status", 0)
    ) != 401
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
        headers.get("x-hukuk-ai-api-version") == "2026-03-30-rc-q"
        and headers.get("x-hukuk-ai-lane") == "rc_q"
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
            1
            for item in (restore_summary.get("files") or [])
            if isinstance(item, dict) and not item.get("exists")
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


def build_capture_truth(
    *,
    current_authority_check: dict[str, Any],
    upstream_equality: dict[str, Any],
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
    frontier = _build_frontier_summary(model_visible_reports=model_visible_reports, parity_reports=parity_reports)
    response = _build_response_summary(parity_reports=parity_reports)
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
    full_family = _build_full_family_parity(
        model_visible_reports=model_visible_reports,
        parity_reports=parity_reports,
    )
    retention = _build_retention_gate(
        acceptance=acceptance,
        full_family_parity=full_family,
        restart_supervision=restart_supervision,
        restore_supervision=restore_supervision,
    )

    wp2 = {
        "control_pair_authority_match": bool(current_authority_check["control_pair_authority_match"]),
        "current_authority_contract_breach": bool(current_authority_check["current_authority_contract_breach"]),
        "surface_breach_from_history_reintroduced": bool(
            current_authority_check["surface_breach_from_history_reintroduced"]
        ),
        "current_canonical_authority_adopted": bool(current_authority_check["current_canonical_authority_adopted"]),
        "control_pair_runtime_error_count": int(current_authority_check["control_pair_runtime_error_count"]),
        "model_request_payload_hash_mismatch_count": int(
            upstream_equality["model_request_payload_hash_mismatch_count"]
        ),
        "retrieval_request_hash_mismatch_count": int(upstream_equality["retrieval_request_hash_mismatch_count"]),
        "assembled_context_hash_mismatch_count": int(upstream_equality["assembled_context_hash_mismatch_count"]),
        "runtime_error_count": int(upstream_equality["runtime_error_count"]),
    }

    wp3 = {
        "frontier_record_count": int(frontier["frontier_record_count"]),
        "faz1_50_mismatch_count": int(frontier["faz1_50_mismatch_count"]),
        "v2_95_mismatch_count": int(frontier["v2_95_mismatch_count"]),
        "v3_170_mismatch_count": int(frontier["v3_170_mismatch_count"]),
        "preprojection_hash_mismatch_count": int(frontier["preprojection_hash_mismatch_count"]),
        "raw_answer_hash_mismatch_count": int(frontier["raw_answer_hash_mismatch_count"]),
        "response_envelope_hash_mismatch_count": int(frontier["response_envelope_hash_mismatch_count"]),
        "runtime_error_count": int(frontier["runtime_error_count"]),
        "unexplained_count": int(frontier["unexplained_count"]),
    }

    wp4 = {
        "response_envelope_subfrontier_record_count": int(response["response_envelope_subfrontier_record_count"]),
        "faz1_50_mismatch_count": int(response["faz1_50_mismatch_count"]),
        "v2_95_mismatch_count": int(response["v2_95_mismatch_count"]),
        "v3_170_mismatch_count": int(response["v3_170_mismatch_count"]),
        "response_envelope_hash_mismatch_count": int(response["response_envelope_hash_mismatch_count"]),
        "runtime_error_count": int(response["runtime_error_count"]),
        "unexplained_count": int(response["unexplained_count"]),
    }

    wp5 = {
        "must_close_release_controls_count": int(acceptance["must_close_release_controls_count"]),
        "mandatory_auth_pass": bool(acceptance["mandatory_auth_pass"]),
        "immutable_audit_logging_pass": bool(acceptance["immutable_audit_logging_pass"]),
        "persisted_pii_redaction_pass": bool(acceptance["persisted_pii_redaction_pass"]),
        "redis_session_persistence_pass": bool(acceptance["redis_session_persistence_pass"]),
        "tokenizer_backed_accounting_pass": bool(acceptance["tokenizer_backed_accounting_pass"]),
        "observability_alerting_pass": bool(acceptance["observability_alerting_pass"]),
        "api_versioning_pass": bool(acceptance["api_versioning_pass"]),
        "process_supervision_pass": bool(acceptance["process_supervision_pass"]),
        "backup_restore_pass": bool(acceptance["backup_restore_pass"]),
        "one_command_release_smoke_pass": bool(acceptance["one_command_release_smoke_pass"]),
        "refusal_smoke_status_code": int(acceptance["refusal_smoke_status_code"]),
        "restart_refusal_smoke_status_code": int(acceptance["restart_refusal_smoke_status_code"]),
        "tokenizer_usage_total": float(acceptance["tokenizer_usage_total"]),
        "estimated_usage_total": float(acceptance["estimated_usage_total"]),
        "token_accounting_failure_total": float(acceptance["token_accounting_failure_total"]),
        "backup_restore_missing_file_count": int(acceptance["backup_restore_missing_file_count"]),
        "runtime_error_count": int(acceptance["runtime_error_count"]),
        "unexplained_count": int(acceptance["unexplained_count"]),
    }

    wp6 = {
        "faz1_50_mismatch_count": int(full_family["faz1_50_mismatch_count"]),
        "v2_95_mismatch_count": int(full_family["v2_95_mismatch_count"]),
        "v3_170_mismatch_count": int(full_family["v3_170_mismatch_count"]),
        "model_request_payload_hash_mismatch_count": int(
            full_family["model_request_payload_hash_mismatch_count"]
        ),
        "retrieval_request_hash_mismatch_count": int(full_family["retrieval_request_hash_mismatch_count"]),
        "assembled_context_hash_mismatch_count": int(full_family["assembled_context_hash_mismatch_count"]),
        "preprojection_hash_mismatch_count": int(full_family["preprojection_hash_mismatch_count"]),
        "raw_answer_hash_mismatch_count": int(full_family["raw_answer_hash_mismatch_count"]),
        "response_envelope_hash_mismatch_count": int(full_family["response_envelope_hash_mismatch_count"]),
        "family_metric_delta_zero": bool(full_family["family_metric_delta_zero"]),
        "runtime_error_count": int(full_family["runtime_error_count"]),
        "unexplained_count": int(full_family["unexplained_count"]),
    }

    wp7 = {
        "must_close_release_controls_pass": bool(retention["must_close_release_controls_pass"]),
        "retained_after_family_eval": bool(retention["retained_after_family_eval"]),
        "retained_after_restart": bool(retention["retained_after_restart"]),
        "retained_after_restore": bool(retention["retained_after_restore"]),
        "answer_path_delta_reintroduced": bool(retention["answer_path_delta_reintroduced"]),
        "runtime_error_count": int(retention["runtime_error_count"]),
        "unexplained_count": int(retention["unexplained_count"]),
    }

    return {"wp2": wp2, "wp3": wp3, "wp4": wp4, "wp5": wp5, "wp6": wp6, "wp7": wp7}


def render_markdown(payload: dict[str, Any], *, title: str) -> str:
    lines = [f"# {title}", ""]
    for section in ("wp2", "wp3", "wp4", "wp5", "wp6", "wp7"):
        lines.append(f"## {section.upper()}")
        lines.append("")
        for key, value in payload[section].items():
            rendered = bool_text(value) if isinstance(value, bool) else value
            lines.append(f"- {key} = `{rendered}`")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ37 single-capture recapture truth.")
    parser.add_argument("--current-authority-check-json", type=Path, required=True)
    parser.add_argument("--upstream-equality-json", type=Path, required=True)
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
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--title", default="FAZ37 Capture Truth")
    args = parser.parse_args()

    payload = build_capture_truth(
        current_authority_check=load_json(args.current_authority_check_json),
        upstream_equality=load_json(args.upstream_equality_json),
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
    write_json(args.output_json, payload)
    if args.output_md:
        write_text(args.output_md, render_markdown(payload, title=args.title))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
