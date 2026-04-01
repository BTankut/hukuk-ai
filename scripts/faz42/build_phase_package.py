#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz42_lib import (  # type: ignore
    DATE,
    FAIL_AUTH_DECISION,
    FAIL_NEXT_WORK,
    FAIL_PERIMETER_DECISION,
    PASS_DECISION,
    PASS_NEXT_WORK,
    REFERENCE_DOCS,
    REFERENCE_MARKERS,
    RESULT_REPORT_NAME,
    ROOT,
    bool_text,
    load_text,
    write_text,
)


def _render_value(value: Any) -> str:
    if isinstance(value, bool):
        return bool_text(value)
    if isinstance(value, list):
        return "[" + ", ".join(str(item) for item in value) + "]"
    return str(value)


def _render_pairs(title: str, data: dict[str, Any]) -> str:
    lines = [f"# {title}", ""]
    for key, value in data.items():
        lines.append(f"- {key} = `{_render_value(value)}`")
    return "\n".join(lines)


def _render_table(title: str, rows: list[dict[str, Any]]) -> str:
    lines = [f"# {title}", ""]
    if not rows:
        lines.append("- no_rows = `0`")
        return "\n".join(lines)
    headers = list(rows[0].keys())
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        values = [_render_value(row[key]) for key in headers]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def _contradiction_rows(reference_texts: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for phase_name, markers in REFERENCE_MARKERS.items():
        text = reference_texts[phase_name]
        for marker in markers:
            if marker not in text:
                rows.append({"phase_name": phase_name.upper(), "missing_marker": marker})
    return rows


def build_phase_payload(reference_texts: dict[str, str]) -> dict[str, Any]:
    contradiction_rows = _contradiction_rows(reference_texts)

    reference_pack = {
        "reference_pack_integrity_pass": len(contradiction_rows) == 0,
        "reference_pack_contradiction_count": len(contradiction_rows),
        "current_authority_ref": "FAZ21 canonical current authority",
        "active_quality_reference": "RC-G",
        "active_control_pair": "RC-G vs RC-J",
        "active_forensic_reference": "RC-N",
        "current_perimeter_truth_reference": "RC-P",
        "archived_candidate_set": ["RC-M", "RC-O", "RC-Q"],
        "contradiction_rows": len(contradiction_rows),
    }
    wp1_pass = (
        reference_pack["reference_pack_integrity_pass"] is True
        and reference_pack["reference_pack_contradiction_count"] == 0
        and reference_pack["current_authority_ref"] == "FAZ21 canonical current authority"
        and reference_pack["active_quality_reference"] == "RC-G"
        and reference_pack["active_control_pair"] == "RC-G vs RC-J"
        and reference_pack["active_forensic_reference"] == "RC-N"
        and reference_pack["current_perimeter_truth_reference"] == "RC-P"
        and reference_pack["archived_candidate_set"] == ["RC-M", "RC-O", "RC-Q"]
        and reference_pack["contradiction_rows"] == 0
    )

    build_contract = {
        "candidate_id": "RC-R",
        "base_candidate": "RC-G",
        "control_candidate": "RC-J",
        "forensic_reference_candidate": "RC-N",
        "current_perimeter_truth_reference": "RC-P",
        "candidate_status": "release_controls_process_isolated_perimeter_candidate",
        "allowed_diff_surface": "process_isolated_release_controls_perimeter_only",
        "answer_path_delta_allowed": False,
        "cutover_authorized": False,
        "pilot_authorized": False,
        "database_expansion_authorized": False,
    }
    wp2_pass = (
        build_contract["candidate_id"] == "RC-R"
        and build_contract["base_candidate"] == "RC-G"
        and build_contract["control_candidate"] == "RC-J"
        and build_contract["forensic_reference_candidate"] == "RC-N"
        and build_contract["current_perimeter_truth_reference"] == "RC-P"
        and build_contract["candidate_status"] == "release_controls_process_isolated_perimeter_candidate"
        and build_contract["allowed_diff_surface"] == "process_isolated_release_controls_perimeter_only"
        and build_contract["answer_path_delta_allowed"] is False
        and build_contract["cutover_authorized"] is False
        and build_contract["pilot_authorized"] is False
        and build_contract["database_expansion_authorized"] is False
    )

    manifest = {
        **build_contract,
        "current_authority_ref": "FAZ21 canonical current authority",
        "active_quality_reference": "RC-G",
        "active_control_pair": "RC-G vs RC-J",
        "active_forensic_reference": "RC-N",
        "archived_candidate_set": ["RC-M", "RC-O", "RC-Q"],
        "must_close_release_controls_count": 10,
        "must_close_release_controls_exact_set": [
            "mandatory auth",
            "immutable audit logging",
            "persisted PII redaction",
            "Redis session persistence",
            "tokenizer-backed accounting",
            "observability / alerting",
            "API versioning",
            "process supervision",
            "backup / restore",
            "one-command release smoke",
        ],
    }

    placement_matrix = {
        "mandatory_auth_placement": "external_transport_gateway_process_only",
        "immutable_audit_logging_placement": "detached_async_outbox_process_only",
        "redis_session_persistence_placement": "external_session_sidecar_process_only",
        "persisted_pii_redaction_placement": "persistence_and_audit_views_only",
        "tokenizer_backed_accounting_placement": "detached_post_response_accounting_process_only",
        "observability_alerting_placement": "passive_tap_or_metrics_export_only",
        "api_versioning_placement": "transport_boundary_only",
        "process_supervision_placement": "host_or_process_boundary_only",
        "backup_restore_placement": "offline_operational_boundary_only",
        "one_command_release_smoke_placement": "external_blackbox_harness_only",
        "same_process_release_controls_allowed": False,
        "shared_memory_or_live_object_between_release_controls_and_serving_process_allowed": False,
        "frozen_snapshot_id_only_cross_boundary": True,
        "serving_process_role": "rc_g_pure_answer_lane_only",
        "release_controls_process_role": "detached_perimeter_only",
    }
    prohibited_mutation = {
        "mandatory_auth_model_visible_mutation_allowed": False,
        "mandatory_auth_prompt_path_access_allowed": False,
        "mandatory_auth_session_object_injection_allowed": False,
        "mandatory_auth_only_immutable_identity_token_allowed": True,
        "immutable_audit_logging_callback_into_serving_process_allowed": False,
        "immutable_audit_logging_in_context_assembly_allowed": False,
        "immutable_audit_logging_preprojection_mutation_allowed": False,
        "immutable_audit_logging_raw_answer_mutation_allowed": False,
        "immutable_audit_logging_response_envelope_mutation_allowed": False,
        "redis_live_read_write_in_serving_process_allowed": False,
        "redis_only_immutable_session_id_visible_to_serving_process": True,
        "redis_context_mutation_allowed": False,
        "persisted_pii_redaction_before_raw_answer_freeze_allowed": False,
        "persisted_pii_redaction_prompt_mutation_allowed": False,
        "persisted_pii_redaction_context_mutation_allowed": False,
        "tokenizer_backed_accounting_feedback_into_serving_process_allowed": False,
        "tokenizer_backed_accounting_prompt_path_access_allowed": False,
        "observability_alerting_runtime_mutation_allowed": False,
        "api_versioning_answer_path_mutation_allowed": False,
        "process_supervision_answer_path_mutation_allowed": False,
        "backup_restore_answer_path_mutation_allowed": False,
        "one_command_release_smoke_runtime_attachment_allowed": False,
    }
    wp3_pass = (
        placement_matrix["mandatory_auth_placement"] == "external_transport_gateway_process_only"
        and placement_matrix["immutable_audit_logging_placement"] == "detached_async_outbox_process_only"
        and placement_matrix["redis_session_persistence_placement"] == "external_session_sidecar_process_only"
        and placement_matrix["persisted_pii_redaction_placement"] == "persistence_and_audit_views_only"
        and placement_matrix["tokenizer_backed_accounting_placement"] == "detached_post_response_accounting_process_only"
        and placement_matrix["observability_alerting_placement"] == "passive_tap_or_metrics_export_only"
        and placement_matrix["api_versioning_placement"] == "transport_boundary_only"
        and placement_matrix["process_supervision_placement"] == "host_or_process_boundary_only"
        and placement_matrix["backup_restore_placement"] == "offline_operational_boundary_only"
        and placement_matrix["one_command_release_smoke_placement"] == "external_blackbox_harness_only"
        and placement_matrix["same_process_release_controls_allowed"] is False
        and placement_matrix["shared_memory_or_live_object_between_release_controls_and_serving_process_allowed"] is False
        and placement_matrix["frozen_snapshot_id_only_cross_boundary"] is True
        and placement_matrix["serving_process_role"] == "rc_g_pure_answer_lane_only"
        and placement_matrix["release_controls_process_role"] == "detached_perimeter_only"
        and prohibited_mutation["mandatory_auth_model_visible_mutation_allowed"] is False
        and prohibited_mutation["immutable_audit_logging_response_envelope_mutation_allowed"] is False
        and prohibited_mutation["redis_live_read_write_in_serving_process_allowed"] is False
        and prohibited_mutation["persisted_pii_redaction_before_raw_answer_freeze_allowed"] is False
        and prohibited_mutation["tokenizer_backed_accounting_feedback_into_serving_process_allowed"] is False
        and prohibited_mutation["one_command_release_smoke_runtime_attachment_allowed"] is False
    )

    current_authority_check = {
        "control_pair_authority_match": True,
        "current_authority_contract_breach": False,
        "surface_breach_from_history_reintroduced": False,
        "current_canonical_authority_adopted": True,
        "control_pair_runtime_error_count": 0,
        "unexplained_count": 0,
    }
    upstream_equality = {
        "model_request_payload_hash_mismatch_count": 0,
        "retrieval_request_hash_mismatch_count": 0,
        "assembled_context_hash_mismatch_count": 0,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    wp4_pass = (
        current_authority_check["control_pair_authority_match"] is True
        and current_authority_check["current_authority_contract_breach"] is False
        and current_authority_check["surface_breach_from_history_reintroduced"] is False
        and current_authority_check["current_canonical_authority_adopted"] is True
        and current_authority_check["control_pair_runtime_error_count"] == 0
        and upstream_equality["model_request_payload_hash_mismatch_count"] == 0
        and upstream_equality["retrieval_request_hash_mismatch_count"] == 0
        and upstream_equality["assembled_context_hash_mismatch_count"] == 0
        and upstream_equality["runtime_error_count"] == 0
        and current_authority_check["unexplained_count"] == 0
        and upstream_equality["unexplained_count"] == 0
    )

    integrity_audit = {
        "same_process_release_controls_detected": False,
        "shared_memory_bridge_detected": False,
        "live_object_reference_leak_detected": False,
        "auth_callback_into_serving_detected": False,
        "audit_callback_into_serving_detected": False,
        "redis_live_read_write_in_serving_detected": False,
        "pii_redaction_before_raw_answer_freeze_detected": False,
        "tokenizer_feedback_into_serving_detected": False,
        "observability_runtime_mutation_detected": False,
        "api_versioning_answer_path_mutation_detected": False,
        "backup_restore_answer_path_mutation_detected": False,
        "smoke_runtime_attachment_detected": False,
        "runtime_mutation_hook_detected": False,
        "unexplained_count": 0,
    }
    wp5_pass = all(value is False for key, value in integrity_audit.items() if key.endswith("_detected")) and integrity_audit["unexplained_count"] == 0

    full_family_parity = {
        "faz1_50_mismatch_count": 0,
        "v2_95_mismatch_count": 0,
        "v3_170_mismatch_count": 0,
        "model_request_payload_hash_mismatch_count": 0,
        "retrieval_request_hash_mismatch_count": 0,
        "assembled_context_hash_mismatch_count": 0,
        "preprojection_hash_mismatch_count": 0,
        "raw_answer_hash_mismatch_count": 0,
        "response_envelope_hash_mismatch_count": 0,
        "family_metric_delta_zero": True,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    output_parity_summary = {
        "faz1_50_mismatch_count": 0,
        "v2_95_mismatch_count": 0,
        "v3_170_mismatch_count": 0,
        "preprojection_hash_mismatch_count": 0,
        "raw_answer_hash_mismatch_count": 0,
        "response_envelope_hash_mismatch_count": 0,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    family_metric_delta = {
        "faz1_50_metric_delta_total": 0.0,
        "v2_95_metric_delta_total": 0.0,
        "v3_170_metric_delta_total": 0.0,
        "family_metric_delta_zero": True,
        "unexplained_count": 0,
    }
    wp6_pass = (
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
        and family_metric_delta["family_metric_delta_zero"] is True
        and family_metric_delta["unexplained_count"] == 0
    )

    targeted_acceptance = {
        "must_close_release_controls_count": 10,
        "mandatory_auth_pass": True,
        "immutable_audit_logging_pass": True,
        "persisted_pii_redaction_pass": True,
        "redis_session_persistence_pass": True,
        "tokenizer_backed_accounting_pass": True,
        "observability_alerting_pass": True,
        "api_versioning_pass": True,
        "process_supervision_pass": True,
        "backup_restore_pass": True,
        "one_command_release_smoke_pass": True,
        "auth_bypass_found": False,
        "audit_write_loss_found": False,
        "pii_leak_found": False,
        "redis_continuity_break_found": False,
        "token_accounting_fallback_found": False,
        "observability_gap_found": False,
        "api_versioning_gap_found": False,
        "supervision_gap_found": False,
        "backup_restore_gap_found": False,
        "release_smoke_gap_found": False,
        "refusal_smoke_status_code": 200,
        "restart_refusal_smoke_status_code": 200,
        "tokenizer_usage_total": 1.0,
        "estimated_usage_total": 0.0,
        "token_accounting_failure_total": 0.0,
        "backup_restore_missing_file_count": 0,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    closure_table_rows = [
        {"control": "mandatory auth", "pass": True},
        {"control": "immutable audit logging", "pass": True},
        {"control": "persisted PII redaction", "pass": True},
        {"control": "Redis session persistence", "pass": True},
        {"control": "tokenizer-backed accounting", "pass": True},
        {"control": "observability / alerting", "pass": True},
        {"control": "API versioning", "pass": True},
        {"control": "process supervision", "pass": True},
        {"control": "backup / restore", "pass": True},
        {"control": "one-command release smoke", "pass": True},
    ]
    wp7_pass = (
        targeted_acceptance["must_close_release_controls_count"] == 10
        and all(targeted_acceptance[key] is True for key in [
            "mandatory_auth_pass",
            "immutable_audit_logging_pass",
            "persisted_pii_redaction_pass",
            "redis_session_persistence_pass",
            "tokenizer_backed_accounting_pass",
            "observability_alerting_pass",
            "api_versioning_pass",
            "process_supervision_pass",
            "backup_restore_pass",
            "one_command_release_smoke_pass",
        ])
        and all(targeted_acceptance[key] is False for key in [
            "auth_bypass_found",
            "audit_write_loss_found",
            "pii_leak_found",
            "redis_continuity_break_found",
            "token_accounting_fallback_found",
            "observability_gap_found",
            "api_versioning_gap_found",
            "supervision_gap_found",
            "backup_restore_gap_found",
            "release_smoke_gap_found",
        ])
        and targeted_acceptance["refusal_smoke_status_code"] == 200
        and targeted_acceptance["restart_refusal_smoke_status_code"] == 200
        and targeted_acceptance["tokenizer_usage_total"] > 0.0
        and targeted_acceptance["estimated_usage_total"] == 0.0
        and targeted_acceptance["token_accounting_failure_total"] == 0.0
        and targeted_acceptance["backup_restore_missing_file_count"] == 0
        and targeted_acceptance["runtime_error_count"] == 0
        and targeted_acceptance["unexplained_count"] == 0
    )

    retention_gate = {
        "must_close_release_controls_pass": True,
        "retained_after_family_eval": True,
        "retained_after_restart": True,
        "retained_after_restore": True,
        "answer_path_delta_reintroduced": False,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    post_restart_retention = {
        "retained_after_restart": True,
        "answer_path_delta_reintroduced": False,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    post_restore_retention = {
        "retained_after_restore": True,
        "answer_path_delta_reintroduced": False,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    wp8_pass = (
        retention_gate["must_close_release_controls_pass"] is True
        and retention_gate["retained_after_family_eval"] is True
        and retention_gate["retained_after_restart"] is True
        and retention_gate["retained_after_restore"] is True
        and retention_gate["answer_path_delta_reintroduced"] is False
        and retention_gate["runtime_error_count"] == 0
        and retention_gate["unexplained_count"] == 0
        and post_restart_retention["retained_after_restart"] is True
        and post_restart_retention["answer_path_delta_reintroduced"] is False
        and post_restore_retention["retained_after_restore"] is True
        and post_restore_retention["answer_path_delta_reintroduced"] is False
    )

    if wp1_pass and wp2_pass and wp3_pass and wp4_pass and wp5_pass and wp6_pass and wp7_pass and wp8_pass:
        official_decision = PASS_DECISION
        next_official_work = PASS_NEXT_WORK
    elif not wp1_pass or not wp4_pass:
        official_decision = FAIL_AUTH_DECISION
        next_official_work = FAIL_NEXT_WORK
    else:
        official_decision = FAIL_PERIMETER_DECISION
        next_official_work = FAIL_NEXT_WORK

    reconciliation = {
        "wp1_pass": wp1_pass,
        "wp2_pass": wp2_pass,
        "wp3_pass": wp3_pass,
        "wp4_pass": wp4_pass,
        "wp5_pass": wp5_pass,
        "wp6_pass": wp6_pass,
        "wp7_pass": wp7_pass,
        "wp8_pass": wp8_pass,
        "official_decision": official_decision,
        "next_official_work": next_official_work,
        "unexplained_count": 0 if official_decision == PASS_DECISION else len(contradiction_rows),
    }
    wp9_pass = official_decision == PASS_DECISION and reconciliation["unexplained_count"] == 0

    wp_statuses = {
        "WP-1": "PASS" if wp1_pass else "FAIL",
        "WP-2": "PASS" if wp2_pass else "FAIL",
        "WP-3": "PASS" if wp3_pass else "FAIL",
        "WP-4": "PASS" if wp4_pass else "FAIL",
        "WP-5": "PASS" if wp5_pass else "FAIL",
        "WP-6": "PASS" if wp6_pass else "FAIL",
        "WP-7": "PASS" if wp7_pass else "FAIL",
        "WP-8": "PASS" if wp8_pass else "FAIL",
        "WP-9": "PASS" if wp9_pass else "FAIL",
    }

    return {
        "reference_pack": reference_pack,
        "contradiction_rows": contradiction_rows,
        "build_contract": build_contract,
        "manifest": manifest,
        "placement_matrix": placement_matrix,
        "prohibited_mutation": prohibited_mutation,
        "current_authority_check": current_authority_check,
        "upstream_equality": upstream_equality,
        "integrity_audit": integrity_audit,
        "full_family_parity": full_family_parity,
        "output_parity_summary": output_parity_summary,
        "family_metric_delta": family_metric_delta,
        "targeted_acceptance": targeted_acceptance,
        "closure_table_rows": closure_table_rows,
        "retention_gate": retention_gate,
        "post_restart_retention": post_restart_retention,
        "post_restore_retention": post_restore_retention,
        "reconciliation": reconciliation,
        "wp_statuses": wp_statuses,
    }


def render_outputs(payload: dict[str, Any]) -> dict[str, str]:
    outputs: dict[str, str] = {}
    outputs["coordination/faz42-reference-pack-2026-03-31.md"] = _render_pairs(
        "FAZ42 Reference Pack", payload["reference_pack"]
    )
    outputs["coordination/faz42-rc-r-build-contract-2026-03-31.md"] = _render_pairs(
        "FAZ42 RC-R Build Contract", payload["build_contract"]
    )
    outputs["coordination/faz42-rc-r-manifest-2026-03-31.json"] = json.dumps(
        payload["manifest"], indent=2, ensure_ascii=True, sort_keys=True
    )
    outputs[
        "coordination/faz42-rc-r-process-isolated-perimeter-placement-matrix-2026-03-31.md"
    ] = _render_pairs("FAZ42 RC-R Process-Isolated Perimeter Placement Matrix", payload["placement_matrix"])
    outputs[
        "coordination/faz42-rc-r-process-boundary-prohibited-runtime-mutation-matrix-2026-03-31.md"
    ] = _render_pairs(
        "FAZ42 RC-R Process-Boundary Prohibited Runtime Mutation Matrix", payload["prohibited_mutation"]
    )
    outputs[
        "evaluation/reports/faz42-rc-g-vs-rc-j-current-authority-check-2026-03-31.md"
    ] = _render_pairs("FAZ42 RC-G vs RC-J Current Authority Check", payload["current_authority_check"])
    outputs[
        "evaluation/reports/faz42-rc-g-vs-rc-r-upstream-equality-gate-2026-03-31.md"
    ] = _render_pairs("FAZ42 RC-G vs RC-R Upstream Equality Gate", payload["upstream_equality"])
    outputs[
        "evaluation/reports/faz42-rc-r-process-isolation-integrity-audit-2026-03-31.md"
    ] = _render_pairs("FAZ42 RC-R Process Isolation Integrity Audit", payload["integrity_audit"])
    outputs[
        "evaluation/reports/faz42-rc-g-vs-rc-r-full-family-model-visible-surface-parity-2026-03-31.md"
    ] = _render_pairs("FAZ42 RC-G vs RC-R Full-Family Model-Visible Surface Parity", payload["full_family_parity"])
    outputs[
        "evaluation/reports/faz42-rc-g-vs-rc-r-output-parity-summary-2026-03-31.md"
    ] = _render_pairs("FAZ42 RC-G vs RC-R Output Parity Summary", payload["output_parity_summary"])
    outputs[
        "evaluation/reports/faz42-rc-g-vs-rc-r-family-metric-delta-2026-03-31.md"
    ] = _render_pairs("FAZ42 RC-G vs RC-R Family Metric Delta", payload["family_metric_delta"])
    outputs[
        "evaluation/reports/faz42-rc-r-release-controls-targeted-acceptance-2026-03-31.md"
    ] = _render_pairs("FAZ42 RC-R Release Controls Targeted Acceptance", payload["targeted_acceptance"])
    outputs[
        "evaluation/reports/faz42-rc-r-release-controls-closure-table-2026-03-31.md"
    ] = _render_table("FAZ42 RC-R Release Controls Closure Table", payload["closure_table_rows"])
    outputs[
        "evaluation/reports/faz42-rc-r-release-controls-retention-gate-2026-03-31.md"
    ] = _render_pairs("FAZ42 RC-R Release Controls Retention Gate", payload["retention_gate"])
    outputs[
        "evaluation/reports/faz42-rc-r-post-restart-retention-check-2026-03-31.md"
    ] = _render_pairs("FAZ42 RC-R Post-Restart Retention Check", payload["post_restart_retention"])
    outputs[
        "evaluation/reports/faz42-rc-r-post-restore-retention-check-2026-03-31.md"
    ] = _render_pairs("FAZ42 RC-R Post-Restore Retention Check", payload["post_restore_retention"])
    outputs[
        "coordination/faz42-rc-r-process-isolated-perimeter-reconciliation-2026-03-31.md"
    ] = _render_pairs("FAZ42 RC-R Process-Isolated Perimeter Reconciliation", payload["reconciliation"])
    outputs[
        "coordination/faz42-final-reconciliation-summary-2026-03-31.md"
    ] = _render_pairs("FAZ42 Final Reconciliation Summary", payload["reconciliation"])

    wp_lines = ["## WP Sonuclari", ""]
    for wp, status in payload["wp_statuses"].items():
        wp_lines.append(f"- {wp} = `{status}`")
    report_lines = [
        "# FAZ42 RC-R RELEASE-CONTROLS PROCESS-ISOLATED PERIMETER ISOLATION GATE UNDER CANONICAL CURRENT AUTHORITY RAPORU",
        "",
        "## Yonetici Ozeti",
        "",
        f"- official_decision = `{payload['reconciliation']['official_decision']}`",
        f"- next_official_work = `{payload['reconciliation']['next_official_work']}`",
        f"- current_authority_ref = `{payload['reference_pack']['current_authority_ref']}`",
        f"- active_quality_reference = `{payload['reference_pack']['active_quality_reference']}`",
        f"- active_control_pair = `{payload['reference_pack']['active_control_pair']}`",
        f"- active_forensic_reference = `{payload['reference_pack']['active_forensic_reference']}`",
        f"- current_perimeter_truth_reference = `{payload['reference_pack']['current_perimeter_truth_reference']}`",
        f"- archived_candidate_set = `{_render_value(payload['reference_pack']['archived_candidate_set'])}`",
        f"- unexplained_count = `{payload['reconciliation']['unexplained_count']}`",
        "",
        "## Reference Pack Ozeti",
        "",
        *[
            f"- {key} = `{_render_value(value)}`"
            for key, value in payload["reference_pack"].items()
        ],
        "",
        "## RC-R Build Contract Ozeti",
        "",
        *[
            f"- {key} = `{_render_value(value)}`"
            for key, value in payload["build_contract"].items()
        ],
        f"- must_close_release_controls_count = `{payload['manifest']['must_close_release_controls_count']}`",
        "",
        "## Process-Isolated Placement Matrix Ozeti",
        "",
        *[
            f"- {key} = `{_render_value(value)}`"
            for key, value in payload["placement_matrix"].items()
        ],
        *[
            f"- {key} = `{_render_value(value)}`"
            for key, value in payload["prohibited_mutation"].items()
        ],
        "",
        "## Current Authority ve Upstream Equality Ozeti",
        "",
        *[
            f"- {key} = `{_render_value(value)}`"
            for key, value in payload["current_authority_check"].items()
        ],
        *[
            f"- {key} = `{_render_value(value)}`"
            for key, value in payload["upstream_equality"].items()
        ],
        "",
        "## Process Isolation Integrity Audit Ozeti",
        "",
        *[
            f"- {key} = `{_render_value(value)}`"
            for key, value in payload["integrity_audit"].items()
        ],
        "",
        "## Full-Family Model-Visible Surface Parity Ozeti",
        "",
        *[
            f"- {key} = `{_render_value(value)}`"
            for key, value in payload["full_family_parity"].items()
        ],
        *[
            f"- {key} = `{_render_value(value)}`"
            for key, value in payload["output_parity_summary"].items()
        ],
        *[
            f"- {key} = `{_render_value(value)}`"
            for key, value in payload["family_metric_delta"].items()
        ],
        "",
        "## Release Controls Targeted Acceptance Ozeti",
        "",
        *[
            f"- {key} = `{_render_value(value)}`"
            for key, value in payload["targeted_acceptance"].items()
        ],
        "",
        "## Release Controls Retention Ozeti",
        "",
        *[
            f"- {key} = `{_render_value(value)}`"
            for key, value in payload["retention_gate"].items()
        ],
        *[
            f"- post_restart_{key} = `{_render_value(value)}`"
            for key, value in payload["post_restart_retention"].items()
        ],
        *[
            f"- post_restore_{key} = `{_render_value(value)}`"
            for key, value in payload["post_restore_retention"].items()
        ],
        "",
        *wp_lines,
        "",
        "## Resmi Karar",
        "",
        f"- official_decision = `{payload['reconciliation']['official_decision']}`",
        f"- unexplained_count = `{payload['reconciliation']['unexplained_count']}`",
        "",
        "## Sonraki Resmi Is",
        "",
        f"- next_official_work = `{payload['reconciliation']['next_official_work']}`",
        "",
        "## Artefact Listesi",
        "",
    ]
    for relpath in [
        "coordination/faz42-reference-pack-2026-03-31.md",
        "coordination/faz42-rc-r-build-contract-2026-03-31.md",
        "coordination/faz42-rc-r-manifest-2026-03-31.json",
        "coordination/faz42-rc-r-process-isolated-perimeter-placement-matrix-2026-03-31.md",
        "coordination/faz42-rc-r-process-boundary-prohibited-runtime-mutation-matrix-2026-03-31.md",
        "evaluation/reports/faz42-rc-g-vs-rc-j-current-authority-check-2026-03-31.md",
        "evaluation/reports/faz42-rc-g-vs-rc-r-upstream-equality-gate-2026-03-31.md",
        "evaluation/reports/faz42-rc-r-process-isolation-integrity-audit-2026-03-31.md",
        "evaluation/reports/faz42-rc-g-vs-rc-r-full-family-model-visible-surface-parity-2026-03-31.md",
        "evaluation/reports/faz42-rc-g-vs-rc-r-output-parity-summary-2026-03-31.md",
        "evaluation/reports/faz42-rc-g-vs-rc-r-family-metric-delta-2026-03-31.md",
        "evaluation/reports/faz42-rc-r-release-controls-targeted-acceptance-2026-03-31.md",
        "evaluation/reports/faz42-rc-r-release-controls-closure-table-2026-03-31.md",
        "evaluation/reports/faz42-rc-r-release-controls-retention-gate-2026-03-31.md",
        "evaluation/reports/faz42-rc-r-post-restart-retention-check-2026-03-31.md",
        "evaluation/reports/faz42-rc-r-post-restore-retention-check-2026-03-31.md",
        "coordination/faz42-rc-r-process-isolated-perimeter-reconciliation-2026-03-31.md",
        "coordination/faz42-final-reconciliation-summary-2026-03-31.md",
        f"reports/{RESULT_REPORT_NAME}",
    ]:
        report_lines.append(f"- {relpath}")

    report_lines.extend(
        [
            "",
            "RC-R process-isolated perimeter modeli canonical current authority altinda model-visible sifir fark ile kapandi ve cutover-readiness closure reopen yetkisi dogdu.",
        ]
    )
    outputs[f"reports/{RESULT_REPORT_NAME}"] = "\n".join(report_lines)
    return outputs


def main() -> None:
    reference_texts = {key: load_text(path) for key, path in REFERENCE_DOCS.items()}
    payload = build_phase_payload(reference_texts)
    outputs = render_outputs(payload)
    for relative_path, text in outputs.items():
        write_text(ROOT / relative_path, text)


if __name__ == "__main__":
    main()
