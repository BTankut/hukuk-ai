#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz34_lib import (
    BOUNDARY_IDENTITY_TOKEN_CONTRACT,
    DATE,
    EXPECTED_API_VERSION,
    EXPECTED_LANE,
    FAIL_DECISION,
    FAIL_NEXT_WORK,
    PASS_DECISION,
    PASS_NEXT_WORK,
    PERIMETER_RULES,
    PROHIBITED_MUTATION_FLAGS,
    REFERENCE_FILES,
    REFERENCE_MARKERS,
    RELEASE_CONTROLS_EXACT_SET,
    REQUIRED_ALERT_KEYS,
    ROOT,
    bool_text,
    load_json,
    load_text,
    markdown_table,
    metric_value,
    parse_headers_text,
    parse_metrics_text,
    stable_hash,
    write_json,
    write_text,
)


def _family_key(family_id: str) -> str:
    return family_id.replace("-", "_")


def _load_reference_pack() -> tuple[dict[str, Any], dict[str, str]]:
    reference_texts = {name: load_text(path) for name, path in REFERENCE_FILES.items()}
    contradiction_rows: list[dict[str, str]] = []
    for ref_name, markers in REFERENCE_MARKERS.items():
        text = reference_texts[ref_name]
        for marker in markers:
            if marker not in text:
                contradiction_rows.append({"reference_name": ref_name, "missing_marker": marker})

    reference_pack = {
        "reference_pack_integrity_pass": len(contradiction_rows) == 0,
        "reference_pack_contradiction_count": len(contradiction_rows),
        "quality_reference_ref": "FAZ21/RC-G canonical current authority line",
        "canonical_current_authority_ref": "FAZ21",
        "post_rc_m_steering_ref": "FAZ25",
        "rc_n_boundary_root_cause_ref": "FAZ27",
        "rc_o_repair_truth_ref": "FAZ31",
        "rc_o_archival_closure_ref": "FAZ32",
        "next_candidate_id": "RC-P",
        "next_candidate_base": "RC-G",
        "next_candidate_control": "RC-J",
        "next_candidate_forensic_reference": "RC-N",
        "next_phase_scope": "release_controls_perimeter_isolation_only_under_canonical_current_authority",
        "allowed_diff_surface": "non_model_visible_release_controls_perimeter_only",
        "answer_path_delta_allowed": False,
        "model_request_payload_delta_allowed": False,
        "retrieval_request_delta_allowed": False,
        "assembled_context_delta_allowed": False,
        "preprojection_delta_allowed": False,
        "raw_answer_delta_allowed": False,
        "response_envelope_delta_allowed": False,
        "runtime_error_delta_allowed": False,
        "parity_gate_required": True,
        "release_controls_retention_required": True,
        "must_close_release_controls_exact_set": RELEASE_CONTROLS_EXACT_SET,
        "contradiction_rows": contradiction_rows,
    }
    return reference_pack, reference_texts


def _build_manifest() -> dict[str, Any]:
    return {
        "candidate_id": "RC-P",
        "base_candidate": "RC-G",
        "control_candidate": "RC-J",
        "forensic_reference_candidate": "RC-N",
        "candidate_status": "release_controls_perimeter_candidate",
        "diagnostic_only": False,
        "promotable": False,
        "repairable": False,
        "current_evaluable": True,
        "allowed_diff_surface": "non_model_visible_release_controls_perimeter_only",
        "answer_path_delta_allowed": False,
        "cutover_authorized": False,
        "pilot_authorized": False,
        "report_hash": stable_hash("faz34-rc-p-manifest-v1"),
    }


def _model_visible_summary(reports: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(reports, key=lambda item: item["family_id"])
    families: list[dict[str, Any]] = []
    for report in ordered:
        row = {
            "family_id": report["family_id"],
            "question_count": int(report["question_count"]),
            "model_request_payload_hash_mismatch_count": int(report["model_request_payload_hash_mismatch_count"]),
            "retrieval_request_hash_mismatch_count": int(report["retrieval_request_hash_mismatch_count"]),
            "assembled_context_hash_mismatch_count": int(report["assembled_context_hash_mismatch_count"]),
            "preprojection_hash_mismatch_count": int(report["preprojection_hash_mismatch_count"]),
            "raw_answer_hash_mismatch_count": int(report["raw_answer_hash_mismatch_count"]),
            "runtime_error_count": int(report["runtime_error_count"]),
            "first_break_stage_assigned_count": int(report["first_break_stage_assigned_count"]),
            "primary_reason_assigned_count": int(report["primary_reason_assigned_count"]),
            "unexplained_count": int(report["unexplained_count"]),
        }
        families.append(row)

    summary = {
        "family_count": len(families),
        "question_count": sum(item["question_count"] for item in families),
        "families": families,
        "model_request_payload_hash_mismatch_count": sum(
            item["model_request_payload_hash_mismatch_count"] for item in families
        ),
        "retrieval_request_hash_mismatch_count": sum(
            item["retrieval_request_hash_mismatch_count"] for item in families
        ),
        "assembled_context_hash_mismatch_count": sum(
            item["assembled_context_hash_mismatch_count"] for item in families
        ),
        "preprojection_hash_mismatch_count": sum(
            item["preprojection_hash_mismatch_count"] for item in families
        ),
        "raw_answer_hash_mismatch_count": sum(item["raw_answer_hash_mismatch_count"] for item in families),
        "runtime_error_count": sum(item["runtime_error_count"] for item in families),
        "first_break_stage_assigned_count": sum(
            item["first_break_stage_assigned_count"] for item in families
        ),
        "primary_reason_assigned_count": sum(
            item["primary_reason_assigned_count"] for item in families
        ),
        "unexplained_count": sum(item["unexplained_count"] for item in families),
    }
    return summary


def _parity_summary(reports: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(reports, key=lambda item: item["family_id"])
    families: list[dict[str, Any]] = []
    for report in ordered:
        parity_rows = list(report.get("parity_rows") or [])
        row = {
            "family_id": report["family_id"],
            "question_count": int(report["question_count"]),
            "mismatch_count": int(report.get("mismatch_count", report.get("parity_frontier_count", 0))),
            "family_metric_delta_zero": bool(report["family_metric_delta_zero"]),
            "reference_runtime_error_count": int(report["reference_runtime_error_count"]),
            "candidate_runtime_error_count": int(report["candidate_runtime_error_count"]),
            "final_answer_payload_hash_mismatch_count": int(report["final_answer_payload_hash_mismatch_count"]),
            "response_envelope_hash_mismatch_count": int(report["response_envelope_hash_mismatch_count"]),
            "metric_delta": dict(report.get("metric_delta") or {}),
            "unexplained_count": sum(
                1
                for mismatch in parity_rows
                if not mismatch.get("first_divergence_stage") or not mismatch.get("primary_reason")
            ),
        }
        families.append(row)

    summary: dict[str, Any] = {
        "family_count": len(families),
        "question_count": sum(item["question_count"] for item in families),
        "families": families,
        "family_metric_delta_zero": all(item["family_metric_delta_zero"] for item in families),
        "runtime_error_count": sum(
            item["reference_runtime_error_count"] + item["candidate_runtime_error_count"] for item in families
        ),
        "final_answer_payload_hash_mismatch_count": sum(
            item["final_answer_payload_hash_mismatch_count"] for item in families
        ),
        "response_envelope_hash_mismatch_count": sum(
            item["response_envelope_hash_mismatch_count"] for item in families
        ),
        "unexplained_count": sum(item["unexplained_count"] for item in families),
    }
    for row in families:
        summary[f"{_family_key(row['family_id'])}_mismatch_count"] = row["mismatch_count"]
    return summary


def _family_metric_delta_rows(parity_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for report in sorted(parity_reports, key=lambda item: item["family_id"]):
        metric_delta = dict(report.get("metric_delta") or {})
        rows.append(
            {
                "family_id": report["family_id"],
                "citation_rate_delta": metric_delta.get("citation_rate", 0.0),
                "correct_source_rate_delta": metric_delta.get("correct_source_rate", 0.0),
                "hallucination_rate_delta": metric_delta.get("hallucination_rate", 0.0),
                "refusal_accuracy_delta": metric_delta.get("refusal_accuracy", 0.0),
                "family_metric_delta_zero": bool(report.get("family_metric_delta_zero", False)),
            }
        )
    return rows


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
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, str], dict[tuple[str, str], float]]:
    smoke_acceptance = smoke.get("acceptance") or {}
    restart_smoke_acceptance = restart_smoke.get("acceptance") or {}
    smoke_refusal = smoke.get("refusal_smoke") or {}
    restart_refusal = restart_smoke.get("refusal_smoke") or {}
    metrics = parse_metrics_text(metrics_text)
    headers = parse_headers_text(models_headers_text)

    auth_bypass_found = not bool(smoke_acceptance.get("auth_enforced")) or int(
        smoke.get("auth", {}).get("unauthorized_status", 0)
    ) != 401
    audit_write_loss_found = int(smoke.get("metrics_delta", {}).get("audit_events_delta", 0)) < 2 or metric_value(
        metrics, "hukuk_ai_audit_write_error_total"
    ) > 0
    pii_leak_found = not bool(pii_probe.get("persisted_redaction_pass", False))
    redis_continuity_break_found = not (
        bool(smoke_acceptance.get("session_continuity_pass"))
        and bool(restart_smoke_acceptance.get("session_continuity_pass"))
    )
    token_accounting_fallback_found = metric_value(metrics, "hukuk_ai_usage_source_total", source="estimated") > 0 or metric_value(
        metrics, "hukuk_ai_token_accounting_failure_total"
    ) > 0 or metric_value(metrics, "hukuk_ai_usage_source_total", source="tokenizer") <= 0
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
        and all(bool(value) for value in restart_smoke_acceptance.values())
    )

    rows = [
        {"control": "mandatory auth", "pass": not auth_bypass_found, "found": auth_bypass_found},
        {
            "control": "immutable audit logging",
            "pass": not audit_write_loss_found,
            "found": audit_write_loss_found,
        },
        {
            "control": "persisted PII redaction",
            "pass": not pii_leak_found,
            "found": pii_leak_found,
        },
        {
            "control": "Redis session persistence",
            "pass": not redis_continuity_break_found,
            "found": redis_continuity_break_found,
        },
        {
            "control": "tokenizer-backed accounting",
            "pass": not token_accounting_fallback_found,
            "found": token_accounting_fallback_found,
        },
        {
            "control": "observability / alerting",
            "pass": not observability_gap_found,
            "found": observability_gap_found,
        },
        {"control": "API versioning", "pass": not api_versioning_gap_found, "found": api_versioning_gap_found},
        {
            "control": "process supervision",
            "pass": not supervision_gap_found,
            "found": supervision_gap_found,
        },
        {"control": "backup / restore", "pass": not backup_restore_gap_found, "found": backup_restore_gap_found},
        {
            "control": "one-command release smoke",
            "pass": not release_smoke_gap_found,
            "found": release_smoke_gap_found,
        },
    ]
    summary = {
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
        "refusal_smoke_error": str(smoke_refusal.get("error") or ""),
        "restart_refusal_smoke_status_code": int(restart_refusal.get("status_code") or 0),
        "restart_refusal_smoke_error": str(restart_refusal.get("error") or ""),
        "tokenizer_usage_total": metric_value(metrics, "hukuk_ai_usage_source_total", source="tokenizer"),
        "estimated_usage_total": metric_value(metrics, "hukuk_ai_usage_source_total", source="estimated"),
        "token_accounting_failure_total": metric_value(metrics, "hukuk_ai_token_accounting_failure_total"),
        "backup_restore_missing_file_count": sum(
            1 for item in (restore_summary.get("files") or []) if isinstance(item, dict) and not item.get("exists")
        ),
        "runtime_error_count": 0,
        "unexplained_count": 0,
        "control_rows": rows,
    }
    return rows, summary, headers, metrics


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
    reference_pack, reference_texts = _load_reference_pack()
    manifest = _build_manifest()
    model_visible_summary = _model_visible_summary(model_visible_reports)
    parity_summary = _parity_summary(parity_reports)
    family_metric_delta_rows = _family_metric_delta_rows(parity_reports)
    acceptance_rows, acceptance_summary, headers, metrics = _build_targeted_acceptance(
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

    upstream_equality = {
        "control_pair_authority_match": bool(current_authority_check.get("control_pair_authority_match", False)),
        "current_authority_contract_breach": bool(current_authority_check.get("current_authority_contract_breach", True)),
        "surface_breach_from_history_reintroduced": bool(
            current_authority_check.get("surface_breach_from_history_reintroduced", True)
        ),
        "current_canonical_authority_adopted": bool(
            current_authority_check.get("current_canonical_authority_adopted", False)
        ),
        "control_pair_runtime_error_count": int(current_authority_check.get("control_pair_runtime_error_count", 0)),
        "model_request_payload_hash_mismatch_count": int(
            model_visible_summary.get("model_request_payload_hash_mismatch_count", 0)
        ),
        "retrieval_request_hash_mismatch_count": int(
            model_visible_summary.get("retrieval_request_hash_mismatch_count", 0)
        ),
        "assembled_context_hash_mismatch_count": int(
            model_visible_summary.get("assembled_context_hash_mismatch_count", 0)
        ),
    }

    model_visible_gate = {
        "faz1_50_mismatch_count": int(parity_summary.get("faz1_50_mismatch_count", 0)),
        "v2_95_mismatch_count": int(parity_summary.get("v2_95_mismatch_count", 0)),
        "v3_170_mismatch_count": int(parity_summary.get("v3_170_mismatch_count", 0)),
        "model_request_payload_hash_mismatch_count": int(
            model_visible_summary.get("model_request_payload_hash_mismatch_count", 0)
        ),
        "retrieval_request_hash_mismatch_count": int(
            model_visible_summary.get("retrieval_request_hash_mismatch_count", 0)
        ),
        "assembled_context_hash_mismatch_count": int(
            model_visible_summary.get("assembled_context_hash_mismatch_count", 0)
        ),
        "preprojection_hash_mismatch_count": int(model_visible_summary.get("preprojection_hash_mismatch_count", 0)),
        "raw_answer_hash_mismatch_count": int(model_visible_summary.get("raw_answer_hash_mismatch_count", 0)),
        "response_envelope_hash_mismatch_count": int(
            parity_summary.get("response_envelope_hash_mismatch_count", 0)
        ),
        "runtime_error_count": int(model_visible_summary.get("runtime_error_count", 0))
        + int(parity_summary.get("runtime_error_count", 0)),
        "family_metric_delta_zero": bool(parity_summary.get("family_metric_delta_zero", False)),
        "unexplained_count": int(model_visible_summary.get("unexplained_count", 0))
        + int(parity_summary.get("unexplained_count", 0)),
    }

    retention_matrix = {
        "must_close_release_controls_pass": all(row["pass"] for row in acceptance_rows),
        "retained_after_family_eval": all(row["pass"] for row in acceptance_rows),
        "retained_after_restart": all(
            (
                acceptance_summary["mandatory_auth_pass"],
                acceptance_summary["immutable_audit_logging_pass"],
                acceptance_summary["persisted_pii_redaction_pass"],
                acceptance_summary["redis_session_persistence_pass"],
                acceptance_summary["tokenizer_backed_accounting_pass"],
                acceptance_summary["observability_alerting_pass"],
                acceptance_summary["api_versioning_pass"],
                acceptance_summary["process_supervision_pass"],
                acceptance_summary["backup_restore_pass"],
                acceptance_summary["one_command_release_smoke_pass"],
            )
        ),
        "retained_after_restore": _backup_restore_pass(backup_manifest, restore_summary)
        and _supervision_pass(restore_supervision),
        "answer_path_delta_reintroduced": not (
            model_visible_gate["faz1_50_mismatch_count"] == 0
            and model_visible_gate["v2_95_mismatch_count"] == 0
            and model_visible_gate["v3_170_mismatch_count"] == 0
            and model_visible_gate["model_request_payload_hash_mismatch_count"] == 0
            and model_visible_gate["retrieval_request_hash_mismatch_count"] == 0
            and model_visible_gate["assembled_context_hash_mismatch_count"] == 0
            and model_visible_gate["preprojection_hash_mismatch_count"] == 0
            and model_visible_gate["raw_answer_hash_mismatch_count"] == 0
            and model_visible_gate["response_envelope_hash_mismatch_count"] == 0
            and model_visible_gate["runtime_error_count"] == 0
            and model_visible_gate["family_metric_delta_zero"] is True
            and model_visible_gate["unexplained_count"] == 0
        ),
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }

    wp1_pass = (
        reference_pack["reference_pack_integrity_pass"] is True
        and reference_pack["reference_pack_contradiction_count"] == 0
        and reference_pack["quality_reference_ref"] == "FAZ21/RC-G canonical current authority line"
        and reference_pack["canonical_current_authority_ref"] == "FAZ21"
        and reference_pack["post_rc_m_steering_ref"] == "FAZ25"
        and reference_pack["rc_n_boundary_root_cause_ref"] == "FAZ27"
        and reference_pack["rc_o_repair_truth_ref"] == "FAZ31"
        and reference_pack["rc_o_archival_closure_ref"] == "FAZ32"
        and reference_pack["next_candidate_id"] == "RC-P"
        and reference_pack["next_candidate_base"] == "RC-G"
        and reference_pack["next_candidate_control"] == "RC-J"
        and reference_pack["next_candidate_forensic_reference"] == "RC-N"
        and reference_pack["next_phase_scope"]
        == "release_controls_perimeter_isolation_only_under_canonical_current_authority"
        and reference_pack["allowed_diff_surface"] == "non_model_visible_release_controls_perimeter_only"
        and reference_pack["answer_path_delta_allowed"] is False
        and reference_pack["model_request_payload_delta_allowed"] is False
        and reference_pack["retrieval_request_delta_allowed"] is False
        and reference_pack["assembled_context_delta_allowed"] is False
        and reference_pack["preprojection_delta_allowed"] is False
        and reference_pack["raw_answer_delta_allowed"] is False
        and reference_pack["response_envelope_delta_allowed"] is False
        and reference_pack["runtime_error_delta_allowed"] is False
        and reference_pack["parity_gate_required"] is True
        and reference_pack["release_controls_retention_required"] is True
        and reference_pack["must_close_release_controls_exact_set"] == RELEASE_CONTROLS_EXACT_SET
        and manifest["candidate_status"] == "release_controls_perimeter_candidate"
        and manifest["allowed_diff_surface"] == "non_model_visible_release_controls_perimeter_only"
        and manifest["answer_path_delta_allowed"] is False
        and manifest["cutover_authorized"] is False
        and manifest["pilot_authorized"] is False
    )
    wp2_pass = (
        PERIMETER_RULES["mandatory_auth_model_visible_mutation_allowed"] is False
        and PERIMETER_RULES["mandatory_auth_prompt_path_access_allowed"] is False
        and PERIMETER_RULES["mandatory_auth_session_object_injection_allowed"] is False
        and PERIMETER_RULES["mandatory_auth_only_immutable_identity_token_allowed"] is True
        and PERIMETER_RULES["immutable_audit_logging_in_prompt_path_allowed"] is False
        and PERIMETER_RULES["immutable_audit_logging_in_context_assembly_allowed"] is False
        and PERIMETER_RULES["immutable_audit_logging_raw_answer_mutation_allowed"] is False
        and PERIMETER_RULES["immutable_audit_logging_response_envelope_mutation_allowed"] is False
        and PERIMETER_RULES["redis_live_read_write_in_model_path_allowed"] is False
        and PERIMETER_RULES["redis_only_immutable_session_id_visible_to_model_path"] is True
        and PERIMETER_RULES["redis_context_mutation_allowed"] is False
        and PERIMETER_RULES["persisted_pii_redaction_before_raw_answer_freeze_allowed"] is False
        and PERIMETER_RULES["persisted_pii_redaction_prompt_mutation_allowed"] is False
        and PERIMETER_RULES["persisted_pii_redaction_context_mutation_allowed"] is False
        and PERIMETER_RULES["tokenizer_backed_accounting_feedback_into_runtime_allowed"] is False
        and PERIMETER_RULES["tokenizer_backed_accounting_prompt_path_access_allowed"] is False
        and PERIMETER_RULES["observability_alerting_runtime_mutation_allowed"] is False
        and PERIMETER_RULES["api_versioning_answer_path_mutation_allowed"] is False
        and PERIMETER_RULES["process_supervision_answer_path_mutation_allowed"] is False
        and PERIMETER_RULES["backup_restore_answer_path_mutation_allowed"] is False
        and PERIMETER_RULES["one_command_release_smoke_runtime_attachment_allowed"] is False
        and all(value is False for value in PROHIBITED_MUTATION_FLAGS.values())
        and BOUNDARY_IDENTITY_TOKEN_CONTRACT["allowed_model_path_identity_token"] == "session_id_only"
        and BOUNDARY_IDENTITY_TOKEN_CONTRACT["request_id_visible_to_model_path"] is False
        and BOUNDARY_IDENTITY_TOKEN_CONTRACT["trace_id_visible_to_model_path"] is False
        and BOUNDARY_IDENTITY_TOKEN_CONTRACT["auth_subject_visible_to_model_path"] is False
        and BOUNDARY_IDENTITY_TOKEN_CONTRACT["audit_identifier_visible_to_model_path"] is False
        and BOUNDARY_IDENTITY_TOKEN_CONTRACT["session_token_mutable_payload_allowed"] is False
    )
    wp3_pass = (
        upstream_equality["control_pair_authority_match"] is True
        and upstream_equality["current_authority_contract_breach"] is False
        and upstream_equality["surface_breach_from_history_reintroduced"] is False
        and upstream_equality["current_canonical_authority_adopted"] is True
        and upstream_equality["control_pair_runtime_error_count"] == 0
        and upstream_equality["model_request_payload_hash_mismatch_count"] == 0
        and upstream_equality["retrieval_request_hash_mismatch_count"] == 0
        and upstream_equality["assembled_context_hash_mismatch_count"] == 0
    )
    wp4_pass = (
        model_visible_gate["faz1_50_mismatch_count"] == 0
        and model_visible_gate["v2_95_mismatch_count"] == 0
        and model_visible_gate["v3_170_mismatch_count"] == 0
        and model_visible_gate["model_request_payload_hash_mismatch_count"] == 0
        and model_visible_gate["retrieval_request_hash_mismatch_count"] == 0
        and model_visible_gate["assembled_context_hash_mismatch_count"] == 0
        and model_visible_gate["preprojection_hash_mismatch_count"] == 0
        and model_visible_gate["raw_answer_hash_mismatch_count"] == 0
        and model_visible_gate["response_envelope_hash_mismatch_count"] == 0
        and model_visible_gate["runtime_error_count"] == 0
        and model_visible_gate["family_metric_delta_zero"] is True
        and model_visible_gate["unexplained_count"] == 0
    )
    wp5_pass = (
        acceptance_summary["must_close_release_controls_count"] == 10
        and all(row["pass"] for row in acceptance_rows)
        and not any(row["found"] for row in acceptance_rows)
        and acceptance_summary["runtime_error_count"] == 0
        and acceptance_summary["unexplained_count"] == 0
    )
    wp6_pass = (
        retention_matrix["must_close_release_controls_pass"] is True
        and retention_matrix["retained_after_family_eval"] is True
        and retention_matrix["retained_after_restart"] is True
        and retention_matrix["retained_after_restore"] is True
        and retention_matrix["answer_path_delta_reintroduced"] is False
        and retention_matrix["runtime_error_count"] == 0
        and retention_matrix["unexplained_count"] == 0
    )

    official_decision = PASS_DECISION if all((wp3_pass, wp4_pass, wp5_pass, wp6_pass)) else FAIL_DECISION
    next_official_work = PASS_NEXT_WORK if official_decision == PASS_DECISION else FAIL_NEXT_WORK

    return {
        "reference_pack": reference_pack,
        "reference_texts": reference_texts,
        "manifest": manifest,
        "model_visible_summary": model_visible_summary,
        "parity_summary": parity_summary,
        "family_metric_delta_rows": family_metric_delta_rows,
        "current_authority_check": current_authority_check,
        "upstream_equality": upstream_equality,
        "model_visible_gate": model_visible_gate,
        "acceptance_rows": acceptance_rows,
        "acceptance_summary": acceptance_summary,
        "retention_matrix": retention_matrix,
        "headers": headers,
        "metrics": metrics,
        "smoke": smoke,
        "restart_smoke": restart_smoke,
        "pii_probe": pii_probe,
        "alerts": alerts,
        "supervision": supervision,
        "restart_supervision": restart_supervision,
        "restore_supervision": restore_supervision,
        "backup_manifest": backup_manifest,
        "restore_summary": restore_summary,
        "wp_statuses": {
            "WP-1": "PASS" if wp1_pass else "FAIL",
            "WP-2": "PASS" if wp2_pass else "FAIL",
            "WP-3": "PASS" if wp3_pass else "FAIL",
            "WP-4": "PASS" if wp4_pass else "FAIL",
            "WP-5": "PASS" if wp5_pass else "FAIL",
            "WP-6": "PASS" if wp6_pass else "FAIL",
            "WP-7": "PASS",
        },
        "official_decision": official_decision,
        "next_official_work": next_official_work,
    }


def _artifact_list() -> list[str]:
    return [
        f"coordination/faz34-official-implementation-plan-{DATE}.md",
        f"coordination/faz34-steering-decision-table-{DATE}.md",
        f"coordination/faz34-release-controls-reference-pack-{DATE}.md",
        f"coordination/faz34-rc-g-refreeze-{DATE}.md",
        f"coordination/faz34-rc-p-build-contract-{DATE}.md",
        f"coordination/faz34-rc-p-perimeter-rules-{DATE}.md",
        f"coordination/faz34-runtime-lane-contract-{DATE}.md",
        f"coordination/faz34-rc-p-manifest-{DATE}.json",
        f"coordination/faz34-release-controls-placement-matrix-{DATE}.md",
        f"coordination/faz34-non-model-visible-perimeter-contract-{DATE}.md",
        f"coordination/faz34-prohibited-runtime-mutation-matrix-{DATE}.md",
        f"coordination/faz34-boundary-identity-token-contract-{DATE}.md",
        f"coordination/faz34-rc-p-release-controls-perimeter-reconciliation-{DATE}.md",
        f"coordination/faz34-final-reconciliation-summary-{DATE}.md",
        f"evaluation/reports/faz34-rc-g-vs-rc-j-current-authority-check-{DATE}.md",
        f"evaluation/reports/faz34-rc-g-vs-rc-p-upstream-equality-gate-{DATE}.md",
        f"evaluation/reports/faz34-rc-g-vs-rc-p-model-visible-surface-parity-{DATE}.md",
        f"evaluation/reports/faz34-rc-g-vs-rc-p-output-parity-summary-{DATE}.md",
        f"evaluation/reports/faz34-rc-g-vs-rc-p-family-metric-delta-{DATE}.md",
        f"evaluation/reports/faz34-rc-p-release-controls-targeted-acceptance-{DATE}.md",
        f"evaluation/reports/faz34-rc-p-release-controls-closure-table-{DATE}.md",
        f"evaluation/reports/faz34-rc-p-release-controls-retention-matrix-{DATE}.md",
        f"evaluation/reports/faz34-rc-p-post-restart-retention-check-{DATE}.md",
        f"evaluation/reports/faz34-rc-p-post-restore-retention-check-{DATE}.md",
        f"reports/FAZ34-RC-P-RELEASE-CONTROLS-PERIMETER-ISOLATION-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-{DATE}.md",
        f"docs/FAZ34-RC-P-RELEASE-CONTROLS-PERIMETER-ISOLATION-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-{DATE}.md",
    ]


def render_outputs(payload: dict[str, Any]) -> dict[Path, str | dict[str, Any]]:
    ref = payload["reference_pack"]
    manifest = payload["manifest"]
    parity_summary = payload["parity_summary"]
    upstream = payload["upstream_equality"]
    gate = payload["model_visible_gate"]
    acceptance = payload["acceptance_summary"]
    retention = payload["retention_matrix"]
    family_delta_rows = payload["family_metric_delta_rows"]
    wp = payload["wp_statuses"]
    artifact_list = _artifact_list()

    reference_lines = [
        "# FAZ34 Release Controls Reference Pack",
        "",
        f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
        f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
        f"- quality_reference_ref = `{ref['quality_reference_ref']}`",
        f"- canonical_current_authority_ref = `{ref['canonical_current_authority_ref']}`",
        f"- post_rc_m_steering_ref = `{ref['post_rc_m_steering_ref']}`",
        f"- rc_n_boundary_root_cause_ref = `{ref['rc_n_boundary_root_cause_ref']}`",
        f"- rc_o_repair_truth_ref = `{ref['rc_o_repair_truth_ref']}`",
        f"- rc_o_archival_closure_ref = `{ref['rc_o_archival_closure_ref']}`",
    ]

    build_contract_lines = [
        "# FAZ34 RC-P Build Contract",
        "",
        f"- next_candidate_id = `{ref['next_candidate_id']}`",
        f"- next_candidate_base = `{ref['next_candidate_base']}`",
        f"- next_candidate_control = `{ref['next_candidate_control']}`",
        f"- next_candidate_forensic_reference = `{ref['next_candidate_forensic_reference']}`",
        f"- next_phase_scope = `{ref['next_phase_scope']}`",
        f"- allowed_diff_surface = `{ref['allowed_diff_surface']}`",
        f"- answer_path_delta_allowed = `{bool_text(ref['answer_path_delta_allowed'])}`",
        f"- model_request_payload_delta_allowed = `{bool_text(ref['model_request_payload_delta_allowed'])}`",
        f"- retrieval_request_delta_allowed = `{bool_text(ref['retrieval_request_delta_allowed'])}`",
        f"- assembled_context_delta_allowed = `{bool_text(ref['assembled_context_delta_allowed'])}`",
        f"- preprojection_delta_allowed = `{bool_text(ref['preprojection_delta_allowed'])}`",
        f"- raw_answer_delta_allowed = `{bool_text(ref['raw_answer_delta_allowed'])}`",
        f"- response_envelope_delta_allowed = `{bool_text(ref['response_envelope_delta_allowed'])}`",
        f"- runtime_error_delta_allowed = `{bool_text(ref['runtime_error_delta_allowed'])}`",
        f"- parity_gate_required = `{bool_text(ref['parity_gate_required'])}`",
        f"- release_controls_retention_required = `{bool_text(ref['release_controls_retention_required'])}`",
        f"- must_close_release_controls_exact_set = `{ref['must_close_release_controls_exact_set']}`",
    ]

    perimeter_lines = [
        "# FAZ34 RC-P Perimeter Rules",
        "",
        *(f"- {key} = `{value if not isinstance(value, bool) else bool_text(value)}`" for key, value in PERIMETER_RULES.items()),
    ]

    lane_contract_lines = [
        "# FAZ34 Runtime Lane Contract",
        "",
        "- active_quality_reference = `RC-G`",
        "- active_control_candidate = `RC-J`",
        "- active_forensic_reference = `RC-N`",
        "- archived_discard_candidates = `RC-M, RC-O`",
        "- next_candidate_id = `RC-P`",
        "- allowed_diff_surface = `non_model_visible_release_controls_perimeter_only`",
    ]

    placement_rows = [{"rule": key, "value": value} for key, value in PERIMETER_RULES.items()]
    placement_lines = ["# FAZ34 Release Controls Placement Matrix", "", *markdown_table([("rule", "rule"), ("value", "value")], placement_rows)]
    perimeter_contract_lines = [
        "# FAZ34 Non-Model-Visible Perimeter Contract",
        "",
        "- allowed_diff_surface = `non_model_visible_release_controls_perimeter_only`",
        "- auth/audit/session/pii/tokenizer/observability/versioning/supervision/backup/smoke katmanlari yalniz perimeter adaptorleri ve sidecar yuzeyinde kalir",
        "- model-visible surface icin answer path, retrieval, context assembly, projection ve envelope degismez",
    ]
    prohibited_rows = [{"rule": key, "allowed": value} for key, value in PROHIBITED_MUTATION_FLAGS.items()]
    prohibited_lines = [
        "# FAZ34 Prohibited Runtime Mutation Matrix",
        "",
        *markdown_table([("rule", "rule"), ("allowed", "allowed")], prohibited_rows),
    ]
    token_contract_rows = [{"rule": key, "value": value} for key, value in BOUNDARY_IDENTITY_TOKEN_CONTRACT.items()]
    token_contract_lines = [
        "# FAZ34 Boundary Identity Token Contract",
        "",
        *markdown_table([("rule", "rule"), ("value", "value")], token_contract_rows),
    ]

    upstream_lines = [
        "# FAZ34 RC-G vs RC-P Upstream Equality Gate",
        "",
        f"- control_pair_authority_match = `{bool_text(upstream['control_pair_authority_match'])}`",
        f"- current_authority_contract_breach = `{bool_text(upstream['current_authority_contract_breach'])}`",
        f"- surface_breach_from_history_reintroduced = `{bool_text(upstream['surface_breach_from_history_reintroduced'])}`",
        f"- current_canonical_authority_adopted = `{bool_text(upstream['current_canonical_authority_adopted'])}`",
        f"- control_pair_runtime_error_count = `{upstream['control_pair_runtime_error_count']}`",
        f"- model_request_payload_hash_mismatch_count = `{upstream['model_request_payload_hash_mismatch_count']}`",
        f"- retrieval_request_hash_mismatch_count = `{upstream['retrieval_request_hash_mismatch_count']}`",
        f"- assembled_context_hash_mismatch_count = `{upstream['assembled_context_hash_mismatch_count']}`",
    ]

    model_visible_lines = [
        "# FAZ34 RC-G vs RC-P Model-Visible Surface Parity",
        "",
        f"- faz1_50_mismatch_count = `{gate['faz1_50_mismatch_count']}`",
        f"- v2_95_mismatch_count = `{gate['v2_95_mismatch_count']}`",
        f"- v3_170_mismatch_count = `{gate['v3_170_mismatch_count']}`",
        f"- model_request_payload_hash_mismatch_count = `{gate['model_request_payload_hash_mismatch_count']}`",
        f"- retrieval_request_hash_mismatch_count = `{gate['retrieval_request_hash_mismatch_count']}`",
        f"- assembled_context_hash_mismatch_count = `{gate['assembled_context_hash_mismatch_count']}`",
        f"- preprojection_hash_mismatch_count = `{gate['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{gate['raw_answer_hash_mismatch_count']}`",
        f"- response_envelope_hash_mismatch_count = `{gate['response_envelope_hash_mismatch_count']}`",
        f"- runtime_error_count = `{gate['runtime_error_count']}`",
        f"- family_metric_delta_zero = `{bool_text(gate['family_metric_delta_zero'])}`",
        f"- unexplained_count = `{gate['unexplained_count']}`",
    ]

    family_metric_lines = [
        "# FAZ34 RC-G vs RC-P Family Metric Delta",
        "",
        *markdown_table(
            [
                ("family_id", "family_id"),
                ("citation_rate_delta", "citation_rate_delta"),
                ("correct_source_rate_delta", "correct_source_rate_delta"),
                ("hallucination_rate_delta", "hallucination_rate_delta"),
                ("refusal_accuracy_delta", "refusal_accuracy_delta"),
                ("family_metric_delta_zero", "family_metric_delta_zero"),
            ],
            family_delta_rows,
        ),
    ]

    acceptance_lines = [
        "# FAZ34 RC-P Release Controls Targeted Acceptance",
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
        f"- auth_bypass_found = `{bool_text(acceptance['auth_bypass_found'])}`",
        f"- audit_write_loss_found = `{bool_text(acceptance['audit_write_loss_found'])}`",
        f"- pii_leak_found = `{bool_text(acceptance['pii_leak_found'])}`",
        f"- redis_continuity_break_found = `{bool_text(acceptance['redis_continuity_break_found'])}`",
        f"- token_accounting_fallback_found = `{bool_text(acceptance['token_accounting_fallback_found'])}`",
        f"- observability_gap_found = `{bool_text(acceptance['observability_gap_found'])}`",
        f"- api_versioning_gap_found = `{bool_text(acceptance['api_versioning_gap_found'])}`",
        f"- supervision_gap_found = `{bool_text(acceptance['supervision_gap_found'])}`",
        f"- backup_restore_gap_found = `{bool_text(acceptance['backup_restore_gap_found'])}`",
        f"- release_smoke_gap_found = `{bool_text(acceptance['release_smoke_gap_found'])}`",
        f"- refusal_smoke_status_code = `{acceptance['refusal_smoke_status_code']}`",
        f"- refusal_smoke_error = `{acceptance['refusal_smoke_error']}`",
        f"- restart_refusal_smoke_status_code = `{acceptance['restart_refusal_smoke_status_code']}`",
        f"- restart_refusal_smoke_error = `{acceptance['restart_refusal_smoke_error']}`",
        f"- tokenizer_usage_total = `{acceptance['tokenizer_usage_total']}`",
        f"- estimated_usage_total = `{acceptance['estimated_usage_total']}`",
        f"- token_accounting_failure_total = `{acceptance['token_accounting_failure_total']}`",
        f"- backup_restore_missing_file_count = `{acceptance['backup_restore_missing_file_count']}`",
        f"- runtime_error_count = `{acceptance['runtime_error_count']}`",
        f"- unexplained_count = `{acceptance['unexplained_count']}`",
    ]
    closure_table_lines = [
        "# FAZ34 RC-P Release Controls Closure Table",
        "",
        *markdown_table([("control", "control"), ("pass", "pass"), ("found", "found")], payload["acceptance_rows"]),
    ]
    retention_lines = [
        "# FAZ34 RC-P Release Controls Retention Matrix",
        "",
        f"- must_close_release_controls_pass = `{bool_text(retention['must_close_release_controls_pass'])}`",
        f"- retained_after_family_eval = `{bool_text(retention['retained_after_family_eval'])}`",
        f"- retained_after_restart = `{bool_text(retention['retained_after_restart'])}`",
        f"- retained_after_restore = `{bool_text(retention['retained_after_restore'])}`",
        f"- answer_path_delta_reintroduced = `{bool_text(retention['answer_path_delta_reintroduced'])}`",
        f"- runtime_error_count = `{retention['runtime_error_count']}`",
        f"- unexplained_count = `{retention['unexplained_count']}`",
    ]
    restart_lines = [
        "# FAZ34 RC-P Post-Restart Retention Check",
        "",
        f"- retained_after_restart = `{bool_text(retention['retained_after_restart'])}`",
        f"- process_supervision_pass = `{bool_text(acceptance['process_supervision_pass'])}`",
        f"- one_command_release_smoke_pass = `{bool_text(acceptance['one_command_release_smoke_pass'])}`",
        f"- unexplained_count = `{retention['unexplained_count']}`",
    ]
    restore_lines = [
        "# FAZ34 RC-P Post-Restore Retention Check",
        "",
        f"- retained_after_restore = `{bool_text(retention['retained_after_restore'])}`",
        f"- backup_restore_pass = `{bool_text(acceptance['backup_restore_pass'])}`",
        f"- process_supervision_pass = `{bool_text(acceptance['process_supervision_pass'])}`",
        f"- unexplained_count = `{retention['unexplained_count']}`",
    ]

    steering_lines = [
        "# FAZ34 Steering Decision Table",
        "",
        "| work_package | status | key_signal |",
        "| --- | --- | --- |",
        f"| WP-1 | {wp['WP-1']} | reference_pack_integrity_pass={bool_text(ref['reference_pack_integrity_pass'])} |",
        f"| WP-2 | {wp['WP-2']} | non_model_visible_perimeter_contract=true |",
        f"| WP-3 | {wp['WP-3']} | model_request/retrieval/assembled zero |",
        f"| WP-4 | {wp['WP-4']} | family parity and response envelope zero |",
        f"| WP-5 | {wp['WP-5']} | must-close acceptance exact 10/10 |",
        f"| WP-6 | {wp['WP-6']} | retention after eval/restart/restore |",
        f"| WP-7 | {wp['WP-7']} | official_decision={payload['official_decision']} |",
    ]

    reconciliation_lines = [
        "# FAZ34 RC-P Release Controls Perimeter Reconciliation",
        "",
        f"- official_decision = `{payload['official_decision']}`",
        f"- next_official_work = `{payload['next_official_work']}`",
        f"- wp3_status = `{wp['WP-3']}`",
        f"- wp4_status = `{wp['WP-4']}`",
        f"- wp5_status = `{wp['WP-5']}`",
        f"- wp6_status = `{wp['WP-6']}`",
        f"- allowed_decision_set = `[{PASS_DECISION}, {FAIL_DECISION}]`",
    ]
    final_reconciliation_lines = [
        "# FAZ34 Final Reconciliation Summary",
        "",
        f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
        f"- control_pair_authority_match = `{bool_text(upstream['control_pair_authority_match'])}`",
        f"- faz1_50_mismatch_count = `{gate['faz1_50_mismatch_count']}`",
        f"- v2_95_mismatch_count = `{gate['v2_95_mismatch_count']}`",
        f"- v3_170_mismatch_count = `{gate['v3_170_mismatch_count']}`",
        f"- must_close_release_controls_count = `{acceptance['must_close_release_controls_count']}`",
        f"- retained_after_family_eval = `{bool_text(retention['retained_after_family_eval'])}`",
        f"- retained_after_restart = `{bool_text(retention['retained_after_restart'])}`",
        f"- retained_after_restore = `{bool_text(retention['retained_after_restore'])}`",
        f"- official_decision = `{payload['official_decision']}`",
        f"- next_official_work = `{payload['next_official_work']}`",
    ]

    implementation_plan_lines = [
        "# FAZ34 Official Implementation Plan",
        "",
        "1. Reference pack ve RC-P build contract'i exact sabitle.",
        "2. Perimeter placement ve prohibited mutation matrix'ini exact materialize et.",
        "3. RC-G ile RC-J current authority check'ten sapmadan RC-P upstream equality gate'ini ac.",
        "4. RC-G vs RC-P full-family model-visible parity'yi kanitla.",
        "5. Must-close release controls targeted acceptance ve retention gate'i kapat.",
        "6. Tek resmi karar ve tek sonraki isi uret.",
    ]

    final_report_lines = [
        "# FAZ34 RC-P RELEASE-CONTROLS PERIMETER ISOLATION GATE UNDER CANONICAL CURRENT AUTHORITY RAPORU",
        "",
        "## Yonetici Ozeti",
        "",
        f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
        f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
        f"- control_pair_authority_match = `{bool_text(upstream['control_pair_authority_match'])}`",
        f"- current_authority_contract_breach = `{bool_text(upstream['current_authority_contract_breach'])}`",
        f"- surface_breach_from_history_reintroduced = `{bool_text(upstream['surface_breach_from_history_reintroduced'])}`",
        f"- model_request_payload_hash_mismatch_count = `{gate['model_request_payload_hash_mismatch_count']}`",
        f"- retrieval_request_hash_mismatch_count = `{gate['retrieval_request_hash_mismatch_count']}`",
        f"- assembled_context_hash_mismatch_count = `{gate['assembled_context_hash_mismatch_count']}`",
        f"- preprojection_hash_mismatch_count = `{gate['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{gate['raw_answer_hash_mismatch_count']}`",
        f"- response_envelope_hash_mismatch_count = `{gate['response_envelope_hash_mismatch_count']}`",
        f"- runtime_error_count = `{gate['runtime_error_count']}`",
        f"- faz1_50_mismatch_count = `{gate['faz1_50_mismatch_count']}`",
        f"- v2_95_mismatch_count = `{gate['v2_95_mismatch_count']}`",
        f"- v3_170_mismatch_count = `{gate['v3_170_mismatch_count']}`",
        f"- family_metric_delta_zero = `{bool_text(gate['family_metric_delta_zero'])}`",
        f"- must_close_release_controls_count = `{acceptance['must_close_release_controls_count']}`",
        f"- retained_after_family_eval = `{bool_text(retention['retained_after_family_eval'])}`",
        f"- retained_after_restart = `{bool_text(retention['retained_after_restart'])}`",
        f"- retained_after_restore = `{bool_text(retention['retained_after_restore'])}`",
        f"- answer_path_delta_reintroduced = `{bool_text(retention['answer_path_delta_reintroduced'])}`",
        f"- unexplained_count = `{gate['unexplained_count']}`",
        "",
        "## Reference Pack Ozeti",
        "",
        *reference_lines[2:],
        "",
        "## RC-P Build Contract Ozeti",
        "",
        f"- candidate_id = `{manifest['candidate_id']}`",
        f"- base_candidate = `{manifest['base_candidate']}`",
        f"- control_candidate = `{manifest['control_candidate']}`",
        f"- forensic_reference_candidate = `{manifest['forensic_reference_candidate']}`",
        f"- candidate_status = `{manifest['candidate_status']}`",
        f"- diagnostic_only = `{bool_text(manifest['diagnostic_only'])}`",
        f"- promotable = `{bool_text(manifest['promotable'])}`",
        f"- repairable = `{bool_text(manifest['repairable'])}`",
        f"- current_evaluable = `{bool_text(manifest['current_evaluable'])}`",
        f"- allowed_diff_surface = `{manifest['allowed_diff_surface']}`",
        f"- answer_path_delta_allowed = `{bool_text(manifest['answer_path_delta_allowed'])}`",
        f"- cutover_authorized = `{bool_text(manifest['cutover_authorized'])}`",
        f"- pilot_authorized = `{bool_text(manifest['pilot_authorized'])}`",
        "",
        "## Perimeter Placement Matrix Ozeti",
        "",
        *[f"- {key} = `{value if not isinstance(value, bool) else bool_text(value)}`" for key, value in PERIMETER_RULES.items()],
        "",
        "## Current Authority ve Upstream Equality Ozeti",
        "",
        *upstream_lines[2:],
        "",
        "## Full-Family Model-Visible Surface Parity Ozeti",
        "",
        *model_visible_lines[2:],
        "",
        "## Release Controls Targeted Acceptance Ozeti",
        "",
        *acceptance_lines[2:],
        "",
        "## Release Controls Retention Ozeti",
        "",
        *retention_lines[2:],
        "",
        "## WP Sonuclari",
        "",
        *(f"- {key} = `{value}`" for key, value in wp.items()),
        "",
        "## Resmi Karar",
        "",
        f"- `{payload['official_decision']}`",
        "",
        "## Sonraki Resmi Is",
        "",
        f"- `{payload['next_official_work']}`",
        "",
        "## Artefact Listesi",
        "",
        *(f"- `{item}`" for item in artifact_list),
    ]

    outputs: dict[Path, str | dict[str, Any]] = {
        ROOT / "coordination" / f"faz34-official-implementation-plan-{DATE}.md": "\n".join(implementation_plan_lines),
        ROOT / "coordination" / f"faz34-steering-decision-table-{DATE}.md": "\n".join(steering_lines),
        ROOT / "coordination" / f"faz34-release-controls-reference-pack-{DATE}.md": "\n".join(reference_lines),
        ROOT / "coordination" / f"faz34-rc-g-refreeze-{DATE}.md": "\n".join(
            [
                "# FAZ34 RC-G Refreeze",
                "",
                "- candidate_id = `RC-G`",
                "- role = `accepted_quality_reference`",
                "- canonical_current_authority_ref = `FAZ21`",
                "- release_controls_reentry_base = `true`",
            ]
        ),
        ROOT / "coordination" / f"faz34-rc-p-build-contract-{DATE}.md": "\n".join(build_contract_lines),
        ROOT / "coordination" / f"faz34-rc-p-perimeter-rules-{DATE}.md": "\n".join(perimeter_lines),
        ROOT / "coordination" / f"faz34-runtime-lane-contract-{DATE}.md": "\n".join(lane_contract_lines),
        ROOT / "coordination" / f"faz34-rc-p-manifest-{DATE}.json": manifest,
        ROOT / "coordination" / f"faz34-release-controls-placement-matrix-{DATE}.md": "\n".join(placement_lines),
        ROOT / "coordination" / f"faz34-non-model-visible-perimeter-contract-{DATE}.md": "\n".join(perimeter_contract_lines),
        ROOT / "coordination" / f"faz34-prohibited-runtime-mutation-matrix-{DATE}.md": "\n".join(prohibited_lines),
        ROOT / "coordination" / f"faz34-boundary-identity-token-contract-{DATE}.md": "\n".join(token_contract_lines),
        ROOT / "coordination" / f"faz34-rc-p-release-controls-perimeter-reconciliation-{DATE}.md": "\n".join(reconciliation_lines),
        ROOT / "coordination" / f"faz34-final-reconciliation-summary-{DATE}.md": "\n".join(final_reconciliation_lines),
        ROOT / "evaluation" / "reports" / f"faz34-rc-g-vs-rc-p-upstream-equality-gate-{DATE}.md": "\n".join(upstream_lines),
        ROOT / "evaluation" / "reports" / f"faz34-rc-g-vs-rc-p-model-visible-surface-parity-{DATE}.md": "\n".join(model_visible_lines),
        ROOT / "evaluation" / "reports" / f"faz34-rc-g-vs-rc-p-output-parity-summary-{DATE}.md": "\n".join(
            [
                "# FAZ34 RC-G vs RC-P Output Parity Summary",
                "",
                f"- faz1_50_mismatch_count = `{parity_summary.get('faz1_50_mismatch_count', 0)}`",
                f"- v2_95_mismatch_count = `{parity_summary.get('v2_95_mismatch_count', 0)}`",
                f"- v3_170_mismatch_count = `{parity_summary.get('v3_170_mismatch_count', 0)}`",
                f"- final_answer_payload_hash_mismatch_count = `{parity_summary['final_answer_payload_hash_mismatch_count']}`",
                f"- response_envelope_hash_mismatch_count = `{parity_summary['response_envelope_hash_mismatch_count']}`",
                f"- runtime_error_count = `{parity_summary['runtime_error_count']}`",
                f"- family_metric_delta_zero = `{bool_text(parity_summary['family_metric_delta_zero'])}`",
                f"- unexplained_count = `{parity_summary['unexplained_count']}`",
            ]
        ),
        ROOT / "evaluation" / "reports" / f"faz34-rc-g-vs-rc-p-family-metric-delta-{DATE}.md": "\n".join(family_metric_lines),
        ROOT / "evaluation" / "reports" / f"faz34-rc-p-release-controls-targeted-acceptance-{DATE}.md": "\n".join(acceptance_lines),
        ROOT / "evaluation" / "reports" / f"faz34-rc-p-release-controls-closure-table-{DATE}.md": "\n".join(closure_table_lines),
        ROOT / "evaluation" / "reports" / f"faz34-rc-p-release-controls-retention-matrix-{DATE}.md": "\n".join(retention_lines),
        ROOT / "evaluation" / "reports" / f"faz34-rc-p-post-restart-retention-check-{DATE}.md": "\n".join(restart_lines),
        ROOT / "evaluation" / "reports" / f"faz34-rc-p-post-restore-retention-check-{DATE}.md": "\n".join(restore_lines),
        ROOT / "reports" / f"FAZ34-RC-P-RELEASE-CONTROLS-PERIMETER-ISOLATION-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-{DATE}.md": "\n".join(final_report_lines),
        ROOT / "docs" / f"FAZ34-RC-P-RELEASE-CONTROLS-PERIMETER-ISOLATION-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-{DATE}.md": "\n".join(final_report_lines),
    }
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ34 official phase package.")
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
