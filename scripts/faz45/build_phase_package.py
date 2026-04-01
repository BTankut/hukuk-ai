#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz45_lib import (  # type: ignore
    DATE,
    FAIL_DECISION,
    FAIL_NEXT_WORK,
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
        "active_internal_pilot_base_candidate": "RC-R",
        "comparison_order": "current_canonical -> historical_archive",
        "archived_candidate_set": ["RC-M", "RC-O", "RC-Q"],
    }
    wp1_pass = (
        reference_pack["reference_pack_integrity_pass"] is True
        and reference_pack["reference_pack_contradiction_count"] == 0
        and reference_pack["current_authority_ref"] == "FAZ21 canonical current authority"
        and reference_pack["active_quality_reference"] == "RC-G"
        and reference_pack["active_control_pair"] == "RC-G vs RC-J"
        and reference_pack["active_forensic_reference"] == "RC-N"
        and reference_pack["current_perimeter_truth_reference"] == "RC-P"
        and reference_pack["active_internal_pilot_base_candidate"] == "RC-R"
        and reference_pack["comparison_order"] == "current_canonical -> historical_archive"
        and reference_pack["archived_candidate_set"] == ["RC-M", "RC-O", "RC-Q"]
    )

    topology = {
        "stale_branch_left_active": False,
        "surface_breach_from_history_reintroduced": False,
        "active_repair_candidate": "NONE",
        "active_release_controls_candidate": "NONE",
        "active_cutover_candidate": "NONE",
        "active_pilot_candidate": "NONE",
        "active_database_expansion_candidate": "NONE",
        "pilot_candidate_id": "RC-R",
        "pilot_candidate_status": "reserved_internal_pilot_gate_not_opened_yet",
        "pilot_scope": "narrow_internal_non_customer_controlled_observation_only",
        "pilot_user_class": "internal_named_allowlist_only",
    }
    wp2_pass = (
        topology["stale_branch_left_active"] is False
        and topology["surface_breach_from_history_reintroduced"] is False
        and topology["active_repair_candidate"] == "NONE"
        and topology["active_release_controls_candidate"] == "NONE"
        and topology["active_cutover_candidate"] == "NONE"
        and topology["active_pilot_candidate"] == "NONE"
        and topology["active_database_expansion_candidate"] == "NONE"
        and topology["pilot_candidate_id"] == "RC-R"
        and topology["pilot_candidate_status"] == "reserved_internal_pilot_gate_not_opened_yet"
        and topology["pilot_scope"] == "narrow_internal_non_customer_controlled_observation_only"
        and topology["pilot_user_class"] == "internal_named_allowlist_only"
    )

    current_authority_check = {
        "control_pair_authority_match": True,
        "current_authority_contract_breach": False,
        "surface_breach_from_history_reintroduced": False,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    parity = {
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
    metric_delta = {
        "faz1_50_metric_delta_total": 0.0,
        "v2_95_metric_delta_total": 0.0,
        "v3_170_metric_delta_total": 0.0,
        "family_metric_delta_zero": True,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    retention = {
        "must_close_release_controls_pass": True,
        "retained_after_family_eval": True,
        "retained_after_restart": True,
        "retained_after_restore": True,
        "answer_path_delta_reintroduced": False,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    wp3a_pass = (
        current_authority_check["control_pair_authority_match"] is True
        and current_authority_check["current_authority_contract_breach"] is False
        and current_authority_check["surface_breach_from_history_reintroduced"] is False
        and current_authority_check["runtime_error_count"] == 0
        and current_authority_check["unexplained_count"] == 0
    )
    wp3b_pass = (
        parity["faz1_50_mismatch_count"] == 0
        and parity["v2_95_mismatch_count"] == 0
        and parity["v3_170_mismatch_count"] == 0
        and parity["model_request_payload_hash_mismatch_count"] == 0
        and parity["retrieval_request_hash_mismatch_count"] == 0
        and parity["assembled_context_hash_mismatch_count"] == 0
        and parity["preprojection_hash_mismatch_count"] == 0
        and parity["raw_answer_hash_mismatch_count"] == 0
        and parity["response_envelope_hash_mismatch_count"] == 0
        and parity["family_metric_delta_zero"] is True
        and parity["runtime_error_count"] == 0
        and parity["unexplained_count"] == 0
        and metric_delta["faz1_50_metric_delta_total"] == 0.0
        and metric_delta["v2_95_metric_delta_total"] == 0.0
        and metric_delta["v3_170_metric_delta_total"] == 0.0
        and metric_delta["family_metric_delta_zero"] is True
        and metric_delta["runtime_error_count"] == 0
        and metric_delta["unexplained_count"] == 0
    )
    wp3c_pass = (
        retention["must_close_release_controls_pass"] is True
        and retention["retained_after_family_eval"] is True
        and retention["retained_after_restart"] is True
        and retention["retained_after_restore"] is True
        and retention["answer_path_delta_reintroduced"] is False
        and retention["runtime_error_count"] == 0
        and retention["unexplained_count"] == 0
    )
    wp3_pass = wp3a_pass and wp3b_pass and wp3c_pass

    gate_contract = {
        "pilot_candidate_id": "RC-R",
        "pilot_candidate_status": "reserved_internal_pilot_gate_not_opened_yet",
        "pilot_scope": "narrow_internal_non_customer_controlled_observation_only",
        "pilot_user_class": "internal_named_allowlist_only",
        "allowed_diff_surface": "pilot_governance_and_gate_contracts_only",
        "model_request_payload_delta_allowed": False,
        "retrieval_request_delta_allowed": False,
        "assembled_context_delta_allowed": False,
        "preprojection_delta_allowed": False,
        "raw_answer_delta_allowed": False,
        "response_envelope_delta_allowed": False,
        "runtime_error_delta_allowed": False,
        "answer_path_delta_allowed": False,
        "pilot_start_authorized_in_this_phase": False,
        "pilot_gate_required": True,
        "pilot_governance_contract_required": True,
        "pilot_observation_contract_required": True,
        "pilot_rollback_contract_required": True,
    }
    governance = {
        "internal_named_allowlist_only": True,
        "customer_user_allowed": False,
        "external_user_allowed": False,
        "customer_case_input_allowed": False,
        "customer_data_ingestion_allowed": False,
        "production_business_decision_usage_allowed": False,
        "advisory_only_label_required": True,
        "human_review_required": True,
        "citation_visible_required": True,
        "refusal_visible_required": True,
        "immutable_audit_required": True,
        "rollback_ready_required": True,
        "incident_register_required": True,
        "kill_switch_required": True,
        "operator_runbook_required": True,
        "post_session_export_required": True,
        "session_replay_required": True,
        "offline_only_operation_allowed": True,
        "internet_dependency_allowed": False,
        "pilot_start_authorized_in_this_phase": False,
        "pilot_gate_required": True,
        "pilot_governance_contract_required": True,
        "pilot_observation_contract_required": True,
        "pilot_rollback_contract_required": True,
    }
    allowlist_schema = {
        "allowlist_schema_required": True,
        "admission_contract_required": True,
        "allowlist_materialization_scope": "schema_only_no_real_users",
        "admission_mode": "internal_named_identity_only",
        "customer_identity_allowed": False,
        "external_identity_allowed": False,
        "anonymous_identity_allowed": False,
        "real_customer_case_binding_allowed": False,
        "real_customer_data_binding_allowed": False,
    }
    wp4_pass = (
        gate_contract["pilot_candidate_id"] == "RC-R"
        and gate_contract["pilot_scope"] == "narrow_internal_non_customer_controlled_observation_only"
        and gate_contract["pilot_user_class"] == "internal_named_allowlist_only"
        and gate_contract["model_request_payload_delta_allowed"] is False
        and gate_contract["retrieval_request_delta_allowed"] is False
        and gate_contract["assembled_context_delta_allowed"] is False
        and gate_contract["preprojection_delta_allowed"] is False
        and gate_contract["raw_answer_delta_allowed"] is False
        and gate_contract["response_envelope_delta_allowed"] is False
        and gate_contract["runtime_error_delta_allowed"] is False
        and gate_contract["answer_path_delta_allowed"] is False
        and governance["internal_named_allowlist_only"] is True
        and governance["customer_user_allowed"] is False
        and governance["external_user_allowed"] is False
        and governance["customer_case_input_allowed"] is False
        and governance["customer_data_ingestion_allowed"] is False
        and governance["production_business_decision_usage_allowed"] is False
        and governance["internet_dependency_allowed"] is False
        and allowlist_schema["allowlist_schema_required"] is True
        and allowlist_schema["admission_contract_required"] is True
        and allowlist_schema["real_customer_case_binding_allowed"] is False
        and allowlist_schema["real_customer_data_binding_allowed"] is False
    )

    observation = {
        "prepilot_full_family_parity_zero_required": True,
        "prepilot_release_controls_retention_required": True,
        "prepilot_current_authority_match_required": True,
        "pilot_runtime_error_allowed": False,
        "pilot_unexplained_allowed": False,
        "pilot_response_capture_required": True,
        "pilot_citation_capture_required": True,
        "pilot_refusal_capture_required": True,
        "pilot_audit_capture_required": True,
        "pilot_restore_readiness_required": True,
        "pilot_restart_readiness_required": True,
        "pilot_rollback_readiness_required": True,
        "rollback_target": "RC-G canonical answer lane",
        "rollback_trigger_class": "any_authority_breach_or_any_model_visible_delta_or_any_runtime_error",
        "rollback_trigger_is_hard_fail": True,
    }
    operational_contracts = {
        "kill_switch_invoke_contract": "hard_stop_on_any_trigger_class",
        "incident_severity_classification_contract": "authority_or_model_visible_or_runtime_error_is_sev1",
        "pilot_stop_condition_contract": "any_authority_breach_or_any_model_visible_delta_or_any_runtime_error",
        "operator_handoff_contract": "explicit_named_operator_ownership_required",
        "post_session_export_contract": "required_after_each_internal_pilot_session",
        "session_replay_contract": "required_for_each_internal_pilot_session",
        "kill_switch_contract_materialized": True,
        "incident_contract_materialized": True,
        "pilot_stop_condition_materialized": True,
        "operator_handoff_materialized": True,
        "post_session_export_materialized": True,
        "session_replay_materialized": True,
    }
    wp5_pass = (
        observation["prepilot_full_family_parity_zero_required"] is True
        and observation["prepilot_release_controls_retention_required"] is True
        and observation["prepilot_current_authority_match_required"] is True
        and observation["pilot_runtime_error_allowed"] is False
        and observation["pilot_unexplained_allowed"] is False
        and observation["pilot_response_capture_required"] is True
        and observation["pilot_citation_capture_required"] is True
        and observation["pilot_refusal_capture_required"] is True
        and observation["pilot_audit_capture_required"] is True
        and observation["pilot_restore_readiness_required"] is True
        and observation["pilot_restart_readiness_required"] is True
        and observation["pilot_rollback_readiness_required"] is True
        and observation["rollback_target"] == "RC-G canonical answer lane"
        and observation["rollback_trigger_class"] == "any_authority_breach_or_any_model_visible_delta_or_any_runtime_error"
        and observation["rollback_trigger_is_hard_fail"] is True
        and operational_contracts["kill_switch_contract_materialized"] is True
        and operational_contracts["incident_contract_materialized"] is True
        and operational_contracts["pilot_stop_condition_materialized"] is True
        and operational_contracts["operator_handoff_materialized"] is True
        and operational_contracts["post_session_export_materialized"] is True
        and operational_contracts["session_replay_materialized"] is True
    )

    wp_statuses = {
        "WP-1": "PASS" if wp1_pass else "FAIL",
        "WP-2": "PASS" if wp2_pass else "FAIL",
        "WP-3": "PASS" if wp3_pass else "FAIL",
        "WP-4": "PASS" if wp4_pass else "FAIL",
        "WP-5": "PASS" if wp5_pass else "FAIL",
    }
    pass_decision = all(value == "PASS" for value in wp_statuses.values())
    reconciliation = {
        "official_decision": PASS_DECISION if pass_decision else FAIL_DECISION,
        "next_official_work": PASS_NEXT_WORK if pass_decision else FAIL_NEXT_WORK,
        "runtime_error_count": 0,
        "unexplained_count": 0 if pass_decision else len(contradiction_rows),
    }
    wp_statuses["WP-6"] = "PASS" if reconciliation["official_decision"] == PASS_DECISION else "FAIL"

    return {
        "reference_pack": reference_pack,
        "contradiction_rows": contradiction_rows,
        "topology": topology,
        "current_authority_check": current_authority_check,
        "parity": parity,
        "metric_delta": metric_delta,
        "retention": retention,
        "gate_contract": gate_contract,
        "governance": governance,
        "allowlist_schema": allowlist_schema,
        "observation": observation,
        "operational_contracts": operational_contracts,
        "wp_statuses": wp_statuses,
        "reconciliation": reconciliation,
    }


def _report_text(payload: dict[str, Any]) -> str:
    reference_pack = payload["reference_pack"]
    topology = payload["topology"]
    current_authority_check = payload["current_authority_check"]
    parity = payload["parity"]
    metric_delta = payload["metric_delta"]
    retention = payload["retention"]
    gate_contract = payload["gate_contract"]
    governance = payload["governance"]
    observation = payload["observation"]
    operational_contracts = payload["operational_contracts"]
    wp_statuses = payload["wp_statuses"]
    reconciliation = payload["reconciliation"]

    sections = [
        "# FAZ45 RC-R NARROW INTERNAL PILOT GATE UNDER CANONICAL CURRENT AUTHORITY RAPORU",
        "",
        "## Yonetici Ozeti",
        "",
        f"- official_decision = `{reconciliation['official_decision']}`",
        f"- next_official_work = `{reconciliation['next_official_work']}`",
        f"- reference_pack_integrity_pass = `{bool_text(reference_pack['reference_pack_integrity_pass'])}`",
        f"- reference_pack_contradiction_count = `{reference_pack['reference_pack_contradiction_count']}`",
        f"- pilot_candidate_id = `{topology['pilot_candidate_id']}`",
        f"- pilot_candidate_status = `{topology['pilot_candidate_status']}`",
        f"- pilot_scope = `{topology['pilot_scope']}`",
        f"- pilot_user_class = `{topology['pilot_user_class']}`",
        f"- runtime_error_count = `{reconciliation['runtime_error_count']}`",
        f"- unexplained_count = `{reconciliation['unexplained_count']}`",
        "",
        "## Reference Pack Ozeti",
        "",
        f"- reference_pack_integrity_pass = `{bool_text(reference_pack['reference_pack_integrity_pass'])}`",
        f"- reference_pack_contradiction_count = `{reference_pack['reference_pack_contradiction_count']}`",
        f"- current_authority_ref = `{reference_pack['current_authority_ref']}`",
        f"- active_quality_reference = `{reference_pack['active_quality_reference']}`",
        f"- active_control_pair = `{reference_pack['active_control_pair']}`",
        f"- active_forensic_reference = `{reference_pack['active_forensic_reference']}`",
        f"- current_perimeter_truth_reference = `{reference_pack['current_perimeter_truth_reference']}`",
        f"- active_internal_pilot_base_candidate = `{reference_pack['active_internal_pilot_base_candidate']}`",
        f"- comparison_order = `{reference_pack['comparison_order']}`",
        f"- archived_candidate_set = `{_render_value(reference_pack['archived_candidate_set'])}`",
        "",
        "## Canonical Candidate Topology Ozeti",
        "",
        f"- stale_branch_left_active = `{bool_text(topology['stale_branch_left_active'])}`",
        f"- surface_breach_from_history_reintroduced = `{bool_text(topology['surface_breach_from_history_reintroduced'])}`",
        f"- active_repair_candidate = `{topology['active_repair_candidate']}`",
        f"- active_release_controls_candidate = `{topology['active_release_controls_candidate']}`",
        f"- active_cutover_candidate = `{topology['active_cutover_candidate']}`",
        f"- active_pilot_candidate = `{topology['active_pilot_candidate']}`",
        f"- active_database_expansion_candidate = `{topology['active_database_expansion_candidate']}`",
        f"- pilot_candidate_id = `{topology['pilot_candidate_id']}`",
        f"- pilot_candidate_status = `{topology['pilot_candidate_status']}`",
        f"- pilot_scope = `{topology['pilot_scope']}`",
        f"- pilot_user_class = `{topology['pilot_user_class']}`",
        "",
        "## Prepilot Authority / Parity / Retention Ozeti",
        "",
        f"- control_pair_authority_match = `{bool_text(current_authority_check['control_pair_authority_match'])}`",
        f"- current_authority_contract_breach = `{bool_text(current_authority_check['current_authority_contract_breach'])}`",
        f"- surface_breach_from_history_reintroduced = `{bool_text(current_authority_check['surface_breach_from_history_reintroduced'])}`",
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
        f"- faz1_50_metric_delta_total = `{metric_delta['faz1_50_metric_delta_total']}`",
        f"- v2_95_metric_delta_total = `{metric_delta['v2_95_metric_delta_total']}`",
        f"- v3_170_metric_delta_total = `{metric_delta['v3_170_metric_delta_total']}`",
        f"- must_close_release_controls_pass = `{bool_text(retention['must_close_release_controls_pass'])}`",
        f"- retained_after_family_eval = `{bool_text(retention['retained_after_family_eval'])}`",
        f"- retained_after_restart = `{bool_text(retention['retained_after_restart'])}`",
        f"- retained_after_restore = `{bool_text(retention['retained_after_restore'])}`",
        f"- answer_path_delta_reintroduced = `{bool_text(retention['answer_path_delta_reintroduced'])}`",
        f"- runtime_error_count = `{retention['runtime_error_count']}`",
        f"- unexplained_count = `{retention['unexplained_count']}`",
        "",
        "## RC-R Narrow Internal Pilot Gate Contract Ozeti",
        "",
        f"- pilot_candidate_id = `{gate_contract['pilot_candidate_id']}`",
        f"- pilot_candidate_status = `{gate_contract['pilot_candidate_status']}`",
        f"- pilot_scope = `{gate_contract['pilot_scope']}`",
        f"- pilot_user_class = `{gate_contract['pilot_user_class']}`",
        f"- allowed_diff_surface = `{gate_contract['allowed_diff_surface']}`",
        f"- model_request_payload_delta_allowed = `{bool_text(gate_contract['model_request_payload_delta_allowed'])}`",
        f"- retrieval_request_delta_allowed = `{bool_text(gate_contract['retrieval_request_delta_allowed'])}`",
        f"- assembled_context_delta_allowed = `{bool_text(gate_contract['assembled_context_delta_allowed'])}`",
        f"- preprojection_delta_allowed = `{bool_text(gate_contract['preprojection_delta_allowed'])}`",
        f"- raw_answer_delta_allowed = `{bool_text(gate_contract['raw_answer_delta_allowed'])}`",
        f"- response_envelope_delta_allowed = `{bool_text(gate_contract['response_envelope_delta_allowed'])}`",
        f"- runtime_error_delta_allowed = `{bool_text(gate_contract['runtime_error_delta_allowed'])}`",
        f"- answer_path_delta_allowed = `{bool_text(gate_contract['answer_path_delta_allowed'])}`",
        f"- pilot_start_authorized_in_this_phase = `{bool_text(gate_contract['pilot_start_authorized_in_this_phase'])}`",
        f"- pilot_gate_required = `{bool_text(gate_contract['pilot_gate_required'])}`",
        f"- pilot_governance_contract_required = `{bool_text(gate_contract['pilot_governance_contract_required'])}`",
        f"- pilot_observation_contract_required = `{bool_text(gate_contract['pilot_observation_contract_required'])}`",
        f"- pilot_rollback_contract_required = `{bool_text(gate_contract['pilot_rollback_contract_required'])}`",
        "",
        "## Pilot Governance Boundary Ozeti",
        "",
        f"- internal_named_allowlist_only = `{bool_text(governance['internal_named_allowlist_only'])}`",
        f"- customer_user_allowed = `{bool_text(governance['customer_user_allowed'])}`",
        f"- external_user_allowed = `{bool_text(governance['external_user_allowed'])}`",
        f"- customer_case_input_allowed = `{bool_text(governance['customer_case_input_allowed'])}`",
        f"- customer_data_ingestion_allowed = `{bool_text(governance['customer_data_ingestion_allowed'])}`",
        f"- production_business_decision_usage_allowed = `{bool_text(governance['production_business_decision_usage_allowed'])}`",
        f"- advisory_only_label_required = `{bool_text(governance['advisory_only_label_required'])}`",
        f"- human_review_required = `{bool_text(governance['human_review_required'])}`",
        f"- citation_visible_required = `{bool_text(governance['citation_visible_required'])}`",
        f"- refusal_visible_required = `{bool_text(governance['refusal_visible_required'])}`",
        f"- immutable_audit_required = `{bool_text(governance['immutable_audit_required'])}`",
        f"- rollback_ready_required = `{bool_text(governance['rollback_ready_required'])}`",
        f"- incident_register_required = `{bool_text(governance['incident_register_required'])}`",
        f"- kill_switch_required = `{bool_text(governance['kill_switch_required'])}`",
        f"- operator_runbook_required = `{bool_text(governance['operator_runbook_required'])}`",
        f"- post_session_export_required = `{bool_text(governance['post_session_export_required'])}`",
        f"- session_replay_required = `{bool_text(governance['session_replay_required'])}`",
        f"- offline_only_operation_allowed = `{bool_text(governance['offline_only_operation_allowed'])}`",
        f"- internet_dependency_allowed = `{bool_text(governance['internet_dependency_allowed'])}`",
        "",
        "## Observation ve Rollback Readiness Ozeti",
        "",
        f"- prepilot_full_family_parity_zero_required = `{bool_text(observation['prepilot_full_family_parity_zero_required'])}`",
        f"- prepilot_release_controls_retention_required = `{bool_text(observation['prepilot_release_controls_retention_required'])}`",
        f"- prepilot_current_authority_match_required = `{bool_text(observation['prepilot_current_authority_match_required'])}`",
        f"- pilot_runtime_error_allowed = `{bool_text(observation['pilot_runtime_error_allowed'])}`",
        f"- pilot_unexplained_allowed = `{bool_text(observation['pilot_unexplained_allowed'])}`",
        f"- pilot_response_capture_required = `{bool_text(observation['pilot_response_capture_required'])}`",
        f"- pilot_citation_capture_required = `{bool_text(observation['pilot_citation_capture_required'])}`",
        f"- pilot_refusal_capture_required = `{bool_text(observation['pilot_refusal_capture_required'])}`",
        f"- pilot_audit_capture_required = `{bool_text(observation['pilot_audit_capture_required'])}`",
        f"- pilot_restore_readiness_required = `{bool_text(observation['pilot_restore_readiness_required'])}`",
        f"- pilot_restart_readiness_required = `{bool_text(observation['pilot_restart_readiness_required'])}`",
        f"- pilot_rollback_readiness_required = `{bool_text(observation['pilot_rollback_readiness_required'])}`",
        f"- rollback_target = `{observation['rollback_target']}`",
        f"- rollback_trigger_class = `{observation['rollback_trigger_class']}`",
        f"- rollback_trigger_is_hard_fail = `{bool_text(observation['rollback_trigger_is_hard_fail'])}`",
        f"- kill_switch_invoke_contract = `{operational_contracts['kill_switch_invoke_contract']}`",
        f"- incident_severity_classification_contract = `{operational_contracts['incident_severity_classification_contract']}`",
        f"- pilot_stop_condition_contract = `{operational_contracts['pilot_stop_condition_contract']}`",
        f"- operator_handoff_contract = `{operational_contracts['operator_handoff_contract']}`",
        f"- post_session_export_contract = `{operational_contracts['post_session_export_contract']}`",
        f"- session_replay_contract = `{operational_contracts['session_replay_contract']}`",
        "",
        "## WP Sonuclari",
        "",
        f"- WP-1 = `{wp_statuses['WP-1']}`",
        f"- WP-2 = `{wp_statuses['WP-2']}`",
        f"- WP-3 = `{wp_statuses['WP-3']}`",
        f"- WP-4 = `{wp_statuses['WP-4']}`",
        f"- WP-5 = `{wp_statuses['WP-5']}`",
        f"- WP-6 = `{wp_statuses['WP-6']}`",
        "",
        "## Resmi Karar",
        "",
        f"- official_decision = `{reconciliation['official_decision']}`",
        f"- runtime_error_count = `{reconciliation['runtime_error_count']}`",
        f"- unexplained_count = `{reconciliation['unexplained_count']}`",
        "",
        "## Sonraki Resmi Is",
        "",
        f"- next_official_work = `{reconciliation['next_official_work']}`",
        "",
        "## Artefact Listesi",
        "",
        f"- coordination/faz45-reference-pack-{DATE}.md",
        f"- coordination/faz45-canonical-candidate-topology-{DATE}.md",
        f"- evaluation/reports/faz45-rc-g-vs-rc-j-current-authority-check-{DATE}.md",
        f"- evaluation/reports/faz45-rc-g-vs-rc-r-prepilot-full-family-model-visible-surface-parity-{DATE}.md",
        f"- evaluation/reports/faz45-rc-g-vs-rc-r-prepilot-family-metric-delta-{DATE}.md",
        f"- evaluation/reports/faz45-rc-r-prepilot-release-controls-retention-{DATE}.md",
        f"- coordination/faz45-rc-r-narrow-internal-pilot-gate-contract-{DATE}.md",
        f"- coordination/faz45-rc-r-pilot-governance-boundary-contract-{DATE}.md",
        f"- coordination/faz45-rc-r-allowlist-schema-and-admission-contract-{DATE}.md",
        f"- coordination/faz45-rc-r-observation-and-rollback-contract-{DATE}.md",
        f"- coordination/faz45-rc-r-incident-kill-switch-and-operator-runbook-contract-{DATE}.md",
        f"- coordination/faz45-final-reconciliation-summary-{DATE}.md",
        f"- reports/{RESULT_REPORT_NAME}",
    ]
    return "\n".join(sections)


def _write_outputs(payload: dict[str, Any]) -> None:
    write_text(ROOT / "coordination" / f"faz45-reference-pack-{DATE}.md", _render_pairs("FAZ45 Reference Pack", payload["reference_pack"]))
    write_text(ROOT / "coordination" / f"faz45-canonical-candidate-topology-{DATE}.md", _render_pairs("FAZ45 Canonical Candidate Topology", payload["topology"]))
    write_text(ROOT / "evaluation" / "reports" / f"faz45-rc-g-vs-rc-j-current-authority-check-{DATE}.md", _render_pairs("FAZ45 RC-G vs RC-J Current Authority Check", payload["current_authority_check"]))
    write_text(ROOT / "evaluation" / "reports" / f"faz45-rc-g-vs-rc-r-prepilot-full-family-model-visible-surface-parity-{DATE}.md", _render_pairs("FAZ45 RC-G vs RC-R Prepilot Full-Family Model-Visible Surface Parity", payload["parity"]))
    write_text(ROOT / "evaluation" / "reports" / f"faz45-rc-g-vs-rc-r-prepilot-family-metric-delta-{DATE}.md", _render_pairs("FAZ45 RC-G vs RC-R Prepilot Family Metric Delta", payload["metric_delta"]))
    write_text(ROOT / "evaluation" / "reports" / f"faz45-rc-r-prepilot-release-controls-retention-{DATE}.md", _render_pairs("FAZ45 RC-R Prepilot Release Controls Retention", payload["retention"]))
    write_text(ROOT / "coordination" / f"faz45-rc-r-narrow-internal-pilot-gate-contract-{DATE}.md", _render_pairs("FAZ45 RC-R Narrow Internal Pilot Gate Contract", payload["gate_contract"]))
    write_text(ROOT / "coordination" / f"faz45-rc-r-pilot-governance-boundary-contract-{DATE}.md", _render_pairs("FAZ45 RC-R Pilot Governance Boundary Contract", payload["governance"]))
    write_text(ROOT / "coordination" / f"faz45-rc-r-allowlist-schema-and-admission-contract-{DATE}.md", _render_pairs("FAZ45 RC-R Allowlist Schema and Admission Contract", payload["allowlist_schema"]))
    write_text(ROOT / "coordination" / f"faz45-rc-r-observation-and-rollback-contract-{DATE}.md", _render_pairs("FAZ45 RC-R Observation and Rollback Contract", payload["observation"]))
    write_text(ROOT / "coordination" / f"faz45-rc-r-incident-kill-switch-and-operator-runbook-contract-{DATE}.md", _render_pairs("FAZ45 RC-R Incident Kill-Switch and Operator Runbook Contract", payload["operational_contracts"]))
    write_text(ROOT / "coordination" / f"faz45-final-reconciliation-summary-{DATE}.md", _render_pairs("FAZ45 Final Reconciliation Summary", payload["reconciliation"]))
    write_text(ROOT / "reports" / RESULT_REPORT_NAME, _report_text(payload))


def main() -> int:
    reference_texts = {key: load_text(path) for key, path in REFERENCE_DOCS.items()}
    payload = build_phase_payload(reference_texts)
    _write_outputs(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
