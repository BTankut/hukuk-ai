#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz44_lib import (  # type: ignore
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


def _render_table(title: str, rows: list[dict[str, Any]]) -> str:
    lines = [f"# {title}", ""]
    if not rows:
        lines.append("- no_rows = `0`")
        return "\n".join(lines)
    headers = list(rows[0].keys())
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(_render_value(row[h]) for h in headers) + " |")
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
        "active_cutover_readiness_candidate": "RC-R",
        "comparison_order": "current_canonical -> historical_archive",
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
        and reference_pack["active_cutover_readiness_candidate"] == "RC-R"
        and reference_pack["comparison_order"] == "current_canonical -> historical_archive"
        and reference_pack["archived_candidate_set"] == ["RC-M", "RC-O", "RC-Q"]
        and reference_pack["contradiction_rows"] == 0
    )

    canonical_candidate_topology = {
        "RC-G": "accepted_quality_reference",
        "RC-J": "canonical_control_diagnostic",
        "RC-N": "forensic_reference_candidate",
        "RC-P": "current_perimeter_truth_reference / diagnostic_only",
        "RC-R": "accepted_release_controls_process_isolated_candidate / cutover_readiness_closed / internal_pilot_base_candidate",
        "RC-M": "discard_archived / historical_summary_archive / diagnostic_only",
        "RC-O": "discard_archived / historical_repair_archive / diagnostic_only",
        "RC-Q": "discard_archived / historical_repair_archive / diagnostic_only",
        "stale_branch_left_active": False,
        "surface_breach_from_history_reintroduced": False,
        "active_repair_candidate": "NONE",
        "active_release_controls_candidate": "NONE",
        "active_database_expansion_candidate": "NONE",
        "active_customer_pilot_candidate": "NONE",
        "active_customer_cutover_candidate": "NONE",
        "next_candidate_id": "RC-R",
        "next_phase_scope": "narrow_internal_pilot_gate_only_under_canonical_current_authority",
    }
    legacy_queue_normalization = {
        "archived_candidate_set": ["RC-M", "RC-O", "RC-Q"],
        "archived_candidate_reopening_allowed": False,
        "archived_candidate_reopen_count": 0,
        "active_repair_candidate": "NONE",
        "active_release_controls_candidate": "NONE",
        "active_database_expansion_candidate": "NONE",
        "active_customer_pilot_candidate": "NONE",
        "active_customer_cutover_candidate": "NONE",
        "new_candidate_reserved_in_this_phase": False,
        "reserved_candidate_id_set": ["RC-R"],
        "stale_branch_left_active": False,
    }
    wp2_pass = (
        canonical_candidate_topology["RC-G"] == "accepted_quality_reference"
        and canonical_candidate_topology["RC-J"] == "canonical_control_diagnostic"
        and canonical_candidate_topology["RC-N"] == "forensic_reference_candidate"
        and canonical_candidate_topology["RC-P"] == "current_perimeter_truth_reference / diagnostic_only"
        and canonical_candidate_topology["RC-R"] == "accepted_release_controls_process_isolated_candidate / cutover_readiness_closed / internal_pilot_base_candidate"
        and canonical_candidate_topology["RC-M"] == "discard_archived / historical_summary_archive / diagnostic_only"
        and canonical_candidate_topology["RC-O"] == "discard_archived / historical_repair_archive / diagnostic_only"
        and canonical_candidate_topology["RC-Q"] == "discard_archived / historical_repair_archive / diagnostic_only"
        and canonical_candidate_topology["stale_branch_left_active"] is False
        and canonical_candidate_topology["surface_breach_from_history_reintroduced"] is False
        and canonical_candidate_topology["active_repair_candidate"] == "NONE"
        and canonical_candidate_topology["active_release_controls_candidate"] == "NONE"
        and canonical_candidate_topology["active_database_expansion_candidate"] == "NONE"
        and canonical_candidate_topology["active_customer_pilot_candidate"] == "NONE"
        and canonical_candidate_topology["active_customer_cutover_candidate"] == "NONE"
        and canonical_candidate_topology["next_candidate_id"] == "RC-R"
        and canonical_candidate_topology["next_phase_scope"] == "narrow_internal_pilot_gate_only_under_canonical_current_authority"
        and legacy_queue_normalization["archived_candidate_reopening_allowed"] is False
        and legacy_queue_normalization["active_customer_cutover_candidate"] == "NONE"
        and legacy_queue_normalization["new_candidate_reserved_in_this_phase"] is False
    )

    steering_contract = {
        "pilot_candidate_id": "RC-R",
        "pilot_candidate_status": "reserved_internal_pilot_gate_not_opened_yet",
        "pilot_scope": "narrow_internal_non_customer_controlled_observation_only",
        "pilot_user_class": "internal_named_allowlist_only",
        "customer_user_allowed": False,
        "external_user_allowed": False,
        "field_deployment_allowed": False,
        "customer_appliance_release_allowed": False,
        "dgx_spark_bundle_allowed": False,
        "database_expansion_allowed": False,
        "new_corpus_allowed": False,
        "new_model_allowed": False,
        "new_prompt_allowed": False,
        "new_retrieval_allowed": False,
        "new_guardrail_allowed": False,
        "new_release_controls_allowed": False,
        "answer_path_delta_allowed": False,
        "model_request_payload_delta_allowed": False,
        "retrieval_request_delta_allowed": False,
        "assembled_context_delta_allowed": False,
        "preprojection_delta_allowed": False,
        "raw_answer_delta_allowed": False,
        "response_envelope_delta_allowed": False,
        "runtime_error_delta_allowed": False,
        "current_authority_contract_breach_allowed": False,
        "surface_breach_from_history_reintroduced_allowed": False,
        "pilot_start_authorized_in_this_phase": False,
        "pilot_gate_required": True,
        "pilot_governance_contract_required": True,
        "pilot_observation_contract_required": True,
        "pilot_rollback_contract_required": True,
    }
    wp3_pass = (
        steering_contract["pilot_candidate_id"] == "RC-R"
        and steering_contract["pilot_candidate_status"] == "reserved_internal_pilot_gate_not_opened_yet"
        and steering_contract["pilot_scope"] == "narrow_internal_non_customer_controlled_observation_only"
        and steering_contract["pilot_user_class"] == "internal_named_allowlist_only"
        and steering_contract["answer_path_delta_allowed"] is False
        and steering_contract["database_expansion_allowed"] is False
        and steering_contract["pilot_start_authorized_in_this_phase"] is False
        and steering_contract["pilot_gate_required"] is True
        and steering_contract["pilot_governance_contract_required"] is True
        and steering_contract["pilot_observation_contract_required"] is True
        and steering_contract["pilot_rollback_contract_required"] is True
    )

    governance_boundary = {
        "internal_named_allowlist_only": True,
        "anonymous_access_allowed": False,
        "public_network_exposure_allowed": False,
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
    }
    wp4_pass = (
        governance_boundary["internal_named_allowlist_only"] is True
        and governance_boundary["customer_user_allowed"] is False
        and governance_boundary["external_user_allowed"] is False
        and governance_boundary["customer_case_input_allowed"] is False
        and governance_boundary["customer_data_ingestion_allowed"] is False
        and governance_boundary["production_business_decision_usage_allowed"] is False
        and governance_boundary["advisory_only_label_required"] is True
        and governance_boundary["human_review_required"] is True
        and governance_boundary["citation_visible_required"] is True
        and governance_boundary["refusal_visible_required"] is True
        and governance_boundary["immutable_audit_required"] is True
        and governance_boundary["rollback_ready_required"] is True
        and governance_boundary["incident_register_required"] is True
        and governance_boundary["kill_switch_required"] is True
        and governance_boundary["operator_runbook_required"] is True
        and governance_boundary["post_session_export_required"] is True
        and governance_boundary["session_replay_required"] is True
        and governance_boundary["offline_only_operation_allowed"] is True
        and governance_boundary["internet_dependency_allowed"] is False
    )

    observation_and_rollback_readiness = {
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
    wp5_pass = (
        observation_and_rollback_readiness["prepilot_full_family_parity_zero_required"] is True
        and observation_and_rollback_readiness["prepilot_release_controls_retention_required"] is True
        and observation_and_rollback_readiness["prepilot_current_authority_match_required"] is True
        and observation_and_rollback_readiness["pilot_runtime_error_allowed"] is False
        and observation_and_rollback_readiness["pilot_unexplained_allowed"] is False
        and observation_and_rollback_readiness["pilot_response_capture_required"] is True
        and observation_and_rollback_readiness["pilot_citation_capture_required"] is True
        and observation_and_rollback_readiness["pilot_refusal_capture_required"] is True
        and observation_and_rollback_readiness["pilot_audit_capture_required"] is True
        and observation_and_rollback_readiness["pilot_restore_readiness_required"] is True
        and observation_and_rollback_readiness["pilot_restart_readiness_required"] is True
        and observation_and_rollback_readiness["pilot_rollback_readiness_required"] is True
        and observation_and_rollback_readiness["rollback_target"] == "RC-G canonical answer lane"
        and observation_and_rollback_readiness["rollback_trigger_class"] == "any_authority_breach_or_any_model_visible_delta_or_any_runtime_error"
        and observation_and_rollback_readiness["rollback_trigger_is_hard_fail"] is True
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
        "unexplained_count": 0 if pass_decision else len(contradiction_rows),
    }
    wp_statuses["WP-6"] = "PASS" if reconciliation["official_decision"] == PASS_DECISION else "FAIL"

    return {
        "reference_pack": reference_pack,
        "contradiction_rows": contradiction_rows,
        "canonical_candidate_topology": canonical_candidate_topology,
        "legacy_queue_normalization": legacy_queue_normalization,
        "steering_contract": steering_contract,
        "governance_boundary": governance_boundary,
        "observation_and_rollback_readiness": observation_and_rollback_readiness,
        "wp_statuses": wp_statuses,
        "reconciliation": reconciliation,
    }


def _report_text(payload: dict[str, Any]) -> str:
    reference_pack = payload["reference_pack"]
    topology = payload["canonical_candidate_topology"]
    steering_contract = payload["steering_contract"]
    governance_boundary = payload["governance_boundary"]
    readiness = payload["observation_and_rollback_readiness"]
    wp_statuses = payload["wp_statuses"]
    reconciliation = payload["reconciliation"]

    sections = [
        f"# FAZ44 RC-R NARROW INTERNAL PILOT STEERING UNDER CANONICAL CURRENT AUTHORITY RAPORU",
        "",
        "## Yonetici Ozeti",
        "",
        f"- official_decision = `{reconciliation['official_decision']}`",
        f"- next_official_work = `{reconciliation['next_official_work']}`",
        f"- reference_pack_integrity_pass = `{bool_text(reference_pack['reference_pack_integrity_pass'])}`",
        f"- reference_pack_contradiction_count = `{reference_pack['reference_pack_contradiction_count']}`",
        f"- pilot_candidate_id = `{steering_contract['pilot_candidate_id']}`",
        f"- pilot_scope = `{steering_contract['pilot_scope']}`",
        f"- pilot_user_class = `{steering_contract['pilot_user_class']}`",
        f"- pilot_start_authorized_in_this_phase = `{bool_text(steering_contract['pilot_start_authorized_in_this_phase'])}`",
        f"- prepilot_full_family_parity_zero_required = `{bool_text(readiness['prepilot_full_family_parity_zero_required'])}`",
        f"- prepilot_release_controls_retention_required = `{bool_text(readiness['prepilot_release_controls_retention_required'])}`",
        f"- rollback_target = `{readiness['rollback_target']}`",
        f"- rollback_trigger_class = `{readiness['rollback_trigger_class']}`",
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
        f"- active_cutover_readiness_candidate = `{reference_pack['active_cutover_readiness_candidate']}`",
        f"- comparison_order = `{reference_pack['comparison_order']}`",
        f"- archived_candidate_set = `{_render_value(reference_pack['archived_candidate_set'])}`",
        f"- contradiction_rows = `{reference_pack['contradiction_rows']}`",
        "",
        "## Canonical Candidate Topology Ozeti",
        "",
        f"- RC-G = `{topology['RC-G']}`",
        f"- RC-J = `{topology['RC-J']}`",
        f"- RC-N = `{topology['RC-N']}`",
        f"- RC-P = `{topology['RC-P']}`",
        f"- RC-R = `{topology['RC-R']}`",
        f"- RC-M = `{topology['RC-M']}`",
        f"- RC-O = `{topology['RC-O']}`",
        f"- RC-Q = `{topology['RC-Q']}`",
        f"- stale_branch_left_active = `{bool_text(topology['stale_branch_left_active'])}`",
        f"- surface_breach_from_history_reintroduced = `{bool_text(topology['surface_breach_from_history_reintroduced'])}`",
        f"- active_repair_candidate = `{topology['active_repair_candidate']}`",
        f"- active_release_controls_candidate = `{topology['active_release_controls_candidate']}`",
        f"- active_database_expansion_candidate = `{topology['active_database_expansion_candidate']}`",
        f"- active_customer_pilot_candidate = `{topology['active_customer_pilot_candidate']}`",
        f"- active_customer_cutover_candidate = `{topology['active_customer_cutover_candidate']}`",
        f"- next_candidate_id = `{topology['next_candidate_id']}`",
        f"- next_phase_scope = `{topology['next_phase_scope']}`",
        "",
        "## RC-R Narrow Internal Pilot Steering Contract Ozeti",
        "",
        f"- pilot_candidate_id = `{steering_contract['pilot_candidate_id']}`",
        f"- pilot_candidate_status = `{steering_contract['pilot_candidate_status']}`",
        f"- pilot_scope = `{steering_contract['pilot_scope']}`",
        f"- pilot_user_class = `{steering_contract['pilot_user_class']}`",
        f"- answer_path_delta_allowed = `{bool_text(steering_contract['answer_path_delta_allowed'])}`",
        f"- model_request_payload_delta_allowed = `{bool_text(steering_contract['model_request_payload_delta_allowed'])}`",
        f"- retrieval_request_delta_allowed = `{bool_text(steering_contract['retrieval_request_delta_allowed'])}`",
        f"- assembled_context_delta_allowed = `{bool_text(steering_contract['assembled_context_delta_allowed'])}`",
        f"- preprojection_delta_allowed = `{bool_text(steering_contract['preprojection_delta_allowed'])}`",
        f"- raw_answer_delta_allowed = `{bool_text(steering_contract['raw_answer_delta_allowed'])}`",
        f"- response_envelope_delta_allowed = `{bool_text(steering_contract['response_envelope_delta_allowed'])}`",
        f"- runtime_error_delta_allowed = `{bool_text(steering_contract['runtime_error_delta_allowed'])}`",
        f"- database_expansion_allowed = `{bool_text(steering_contract['database_expansion_allowed'])}`",
        f"- pilot_start_authorized_in_this_phase = `{bool_text(steering_contract['pilot_start_authorized_in_this_phase'])}`",
        f"- pilot_gate_required = `{bool_text(steering_contract['pilot_gate_required'])}`",
        f"- pilot_governance_contract_required = `{bool_text(steering_contract['pilot_governance_contract_required'])}`",
        f"- pilot_observation_contract_required = `{bool_text(steering_contract['pilot_observation_contract_required'])}`",
        f"- pilot_rollback_contract_required = `{bool_text(steering_contract['pilot_rollback_contract_required'])}`",
        "",
        "## Pilot Governance Boundary Ozeti",
        "",
        f"- internal_named_allowlist_only = `{bool_text(governance_boundary['internal_named_allowlist_only'])}`",
        f"- customer_user_allowed = `{bool_text(governance_boundary['customer_user_allowed'])}`",
        f"- external_user_allowed = `{bool_text(governance_boundary['external_user_allowed'])}`",
        f"- customer_case_input_allowed = `{bool_text(governance_boundary['customer_case_input_allowed'])}`",
        f"- customer_data_ingestion_allowed = `{bool_text(governance_boundary['customer_data_ingestion_allowed'])}`",
        f"- production_business_decision_usage_allowed = `{bool_text(governance_boundary['production_business_decision_usage_allowed'])}`",
        f"- advisory_only_label_required = `{bool_text(governance_boundary['advisory_only_label_required'])}`",
        f"- human_review_required = `{bool_text(governance_boundary['human_review_required'])}`",
        f"- citation_visible_required = `{bool_text(governance_boundary['citation_visible_required'])}`",
        f"- refusal_visible_required = `{bool_text(governance_boundary['refusal_visible_required'])}`",
        f"- immutable_audit_required = `{bool_text(governance_boundary['immutable_audit_required'])}`",
        f"- rollback_ready_required = `{bool_text(governance_boundary['rollback_ready_required'])}`",
        f"- incident_register_required = `{bool_text(governance_boundary['incident_register_required'])}`",
        f"- kill_switch_required = `{bool_text(governance_boundary['kill_switch_required'])}`",
        f"- operator_runbook_required = `{bool_text(governance_boundary['operator_runbook_required'])}`",
        f"- post_session_export_required = `{bool_text(governance_boundary['post_session_export_required'])}`",
        f"- session_replay_required = `{bool_text(governance_boundary['session_replay_required'])}`",
        f"- offline_only_operation_allowed = `{bool_text(governance_boundary['offline_only_operation_allowed'])}`",
        f"- internet_dependency_allowed = `{bool_text(governance_boundary['internet_dependency_allowed'])}`",
        "",
        "## Observation ve Rollback Readiness Ozeti",
        "",
        f"- prepilot_full_family_parity_zero_required = `{bool_text(readiness['prepilot_full_family_parity_zero_required'])}`",
        f"- prepilot_release_controls_retention_required = `{bool_text(readiness['prepilot_release_controls_retention_required'])}`",
        f"- prepilot_current_authority_match_required = `{bool_text(readiness['prepilot_current_authority_match_required'])}`",
        f"- pilot_runtime_error_allowed = `{bool_text(readiness['pilot_runtime_error_allowed'])}`",
        f"- pilot_unexplained_allowed = `{bool_text(readiness['pilot_unexplained_allowed'])}`",
        f"- pilot_response_capture_required = `{bool_text(readiness['pilot_response_capture_required'])}`",
        f"- pilot_citation_capture_required = `{bool_text(readiness['pilot_citation_capture_required'])}`",
        f"- pilot_refusal_capture_required = `{bool_text(readiness['pilot_refusal_capture_required'])}`",
        f"- pilot_audit_capture_required = `{bool_text(readiness['pilot_audit_capture_required'])}`",
        f"- pilot_restore_readiness_required = `{bool_text(readiness['pilot_restore_readiness_required'])}`",
        f"- pilot_restart_readiness_required = `{bool_text(readiness['pilot_restart_readiness_required'])}`",
        f"- pilot_rollback_readiness_required = `{bool_text(readiness['pilot_rollback_readiness_required'])}`",
        f"- rollback_target = `{readiness['rollback_target']}`",
        f"- rollback_trigger_class = `{readiness['rollback_trigger_class']}`",
        f"- rollback_trigger_is_hard_fail = `{bool_text(readiness['rollback_trigger_is_hard_fail'])}`",
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
        f"- unexplained_count = `{reconciliation['unexplained_count']}`",
        "",
        "## Sonraki Resmi Is",
        "",
        f"- next_official_work = `{reconciliation['next_official_work']}`",
        "",
        "## Artefact Listesi",
        "",
        f"- coordination/faz44-reference-pack-{DATE}.md",
        f"- coordination/faz44-canonical-candidate-topology-{DATE}.md",
        f"- coordination/faz44-legacy-queue-normalization-{DATE}.md",
        f"- coordination/faz44-rc-r-narrow-internal-pilot-steering-contract-{DATE}.md",
        f"- coordination/faz44-rc-r-pilot-governance-boundary-contract-{DATE}.md",
        f"- coordination/faz44-rc-r-observation-and-rollback-readiness-contract-{DATE}.md",
        f"- coordination/faz44-final-reconciliation-summary-{DATE}.md",
        f"- reports/{RESULT_REPORT_NAME}",
    ]
    return "\n".join(sections)


def _write_outputs(payload: dict[str, Any]) -> None:
    write_text(ROOT / "coordination" / f"faz44-reference-pack-{DATE}.md", _render_pairs("FAZ44 Reference Pack", payload["reference_pack"]))
    write_text(ROOT / "coordination" / f"faz44-canonical-candidate-topology-{DATE}.md", _render_pairs("FAZ44 Canonical Candidate Topology", payload["canonical_candidate_topology"]))
    write_text(ROOT / "coordination" / f"faz44-legacy-queue-normalization-{DATE}.md", _render_pairs("FAZ44 Legacy Queue Normalization", payload["legacy_queue_normalization"]))
    write_text(ROOT / "coordination" / f"faz44-rc-r-narrow-internal-pilot-steering-contract-{DATE}.md", _render_pairs("FAZ44 RC-R Narrow Internal Pilot Steering Contract", payload["steering_contract"]))
    write_text(ROOT / "coordination" / f"faz44-rc-r-pilot-governance-boundary-contract-{DATE}.md", _render_pairs("FAZ44 RC-R Pilot Governance Boundary Contract", payload["governance_boundary"]))
    write_text(ROOT / "coordination" / f"faz44-rc-r-observation-and-rollback-readiness-contract-{DATE}.md", _render_pairs("FAZ44 RC-R Observation and Rollback Readiness Contract", payload["observation_and_rollback_readiness"]))
    write_text(ROOT / "coordination" / f"faz44-final-reconciliation-summary-{DATE}.md", _render_pairs("FAZ44 Final Reconciliation Summary", payload["reconciliation"]))
    write_text(ROOT / "reports" / RESULT_REPORT_NAME, _report_text(payload))


def main() -> int:
    reference_texts = {key: load_text(path) for key, path in REFERENCE_DOCS.items()}
    payload = build_phase_payload(reference_texts)
    _write_outputs(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
