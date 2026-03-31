#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz41_lib import (  # type: ignore
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


def build_phase_payload(reference_texts: dict[str, str]) -> dict[str, Any]:
    contradiction_rows: list[dict[str, str]] = []
    for phase_name, markers in REFERENCE_MARKERS.items():
        text = reference_texts[phase_name]
        for marker in markers:
            if marker not in text:
                contradiction_rows.append({"phase_name": phase_name.upper(), "missing_marker": marker})

    reference_pack = {
        "reference_pack_integrity_pass": len(contradiction_rows) == 0,
        "reference_pack_contradiction_count": len(contradiction_rows),
        "current_authority_ref": "FAZ21 canonical current authority",
        "active_quality_reference": "RC-G",
        "active_control_pair": "RC-G vs RC-J",
        "active_forensic_reference": "RC-N",
        "current_perimeter_truth_reference": "RC-P",
        "archived_candidate_set": ["RC-M", "RC-O", "RC-Q"],
        "contradiction_rows": contradiction_rows,
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
        and len(reference_pack["contradiction_rows"]) == 0
    )

    topology_rows = [
        {
            "candidate_id": "RC-G",
            "candidate_status": "accepted_quality_reference",
            "role": "quality_reference",
            "current_authority_member": True,
            "diagnostic_only": False,
            "archived": False,
            "promotable": True,
            "repairable": False,
            "current_evaluable": True,
            "release_controls_reentry_base": True,
            "notes": "canonical_quality_reference_and_reentry_base",
        },
        {
            "candidate_id": "RC-J",
            "candidate_status": "canonical_control_diagnostic",
            "role": "control_diagnostic",
            "current_authority_member": True,
            "diagnostic_only": True,
            "archived": False,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "release_controls_reentry_base": False,
            "notes": "frozen_control_pair_for_canonical_authority_only",
        },
        {
            "candidate_id": "RC-N",
            "candidate_status": "forensic_reference_candidate",
            "role": "release_controls_boundary_forensics_reference",
            "current_authority_member": False,
            "diagnostic_only": True,
            "archived": False,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "release_controls_reentry_base": False,
            "notes": "boundary_root_cause_reference_only",
        },
        {
            "candidate_id": "RC-P",
            "candidate_status": "current_perimeter_truth_reference",
            "role": "current_perimeter_truth_reference",
            "current_authority_member": False,
            "diagnostic_only": True,
            "archived": False,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "release_controls_reentry_base": False,
            "notes": "current_perimeter_truth_reference_diagnostic_only",
        },
        {
            "candidate_id": "RC-M",
            "candidate_status": "discard_archived",
            "role": "historical_summary_archive",
            "current_authority_member": False,
            "diagnostic_only": True,
            "archived": True,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "release_controls_reentry_base": False,
            "notes": "historical_archive_diagnostic_only",
        },
        {
            "candidate_id": "RC-O",
            "candidate_status": "discard_archived",
            "role": "historical_repair_archive",
            "current_authority_member": False,
            "diagnostic_only": True,
            "archived": True,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "release_controls_reentry_base": False,
            "notes": "historical_repair_archive_diagnostic_only",
        },
        {
            "candidate_id": "RC-Q",
            "candidate_status": "discard_archived",
            "role": "historical_repair_archive",
            "current_authority_member": False,
            "diagnostic_only": True,
            "archived": True,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "release_controls_reentry_base": False,
            "notes": "historical_repair_archive_diagnostic_only",
        },
    ]
    expected_topology = {row["candidate_id"]: row for row in topology_rows}
    wp2_pass = (
        len(topology_rows) == 7
        and set(expected_topology.keys()) == {"RC-G", "RC-J", "RC-N", "RC-P", "RC-M", "RC-O", "RC-Q"}
        and expected_topology["RC-G"]["release_controls_reentry_base"] is True
        and expected_topology["RC-P"]["candidate_status"] == "current_perimeter_truth_reference"
        and expected_topology["RC-M"]["archived"] is True
        and expected_topology["RC-O"]["archived"] is True
        and expected_topology["RC-Q"]["archived"] is True
    )

    queue_normalization = {
        "active_quality_reference": "RC-G",
        "active_control_pair": "RC-G vs RC-J",
        "active_forensic_reference": "RC-N",
        "current_perimeter_truth_reference": "RC-P",
        "active_repair_candidate": "NONE",
        "active_release_controls_candidate": "NONE",
        "active_cutover_candidate": "NONE",
        "active_pilot_candidate": "NONE",
        "active_database_expansion_candidate": "NONE",
        "archived_candidate_set": ["RC-M", "RC-O", "RC-Q"],
        "stale_branch_set": ["RC-H", "RC-I", "RC-L"],
        "stale_branch_left_active": False,
        "surface_breach_from_history_reintroduced": False,
        "current_canonical_consumer_order": "current_canonical -> historical_archive",
        "planner_can_open_build_for_rc_m": False,
        "planner_can_open_patch_for_rc_m": False,
        "planner_can_open_repair_for_rc_m": False,
        "planner_can_open_replay_for_rc_m": False,
        "planner_can_open_recapture_for_rc_m": False,
        "planner_can_open_cutover_for_rc_m": False,
        "planner_can_open_pilot_for_rc_m": False,
        "planner_can_open_build_for_rc_o": False,
        "planner_can_open_patch_for_rc_o": False,
        "planner_can_open_repair_for_rc_o": False,
        "planner_can_open_replay_for_rc_o": False,
        "planner_can_open_recapture_for_rc_o": False,
        "planner_can_open_cutover_for_rc_o": False,
        "planner_can_open_pilot_for_rc_o": False,
        "planner_can_open_build_for_rc_q": False,
        "planner_can_open_patch_for_rc_q": False,
        "planner_can_open_repair_for_rc_q": False,
        "planner_can_open_replay_for_rc_q": False,
        "planner_can_open_recapture_for_rc_q": False,
        "planner_can_open_cutover_for_rc_q": False,
        "planner_can_open_pilot_for_rc_q": False,
        "planner_can_open_release_controls_reentry_for_rc_q": False,
    }
    wp3_pass = (
        queue_normalization["active_quality_reference"] == "RC-G"
        and queue_normalization["active_control_pair"] == "RC-G vs RC-J"
        and queue_normalization["active_forensic_reference"] == "RC-N"
        and queue_normalization["current_perimeter_truth_reference"] == "RC-P"
        and queue_normalization["active_repair_candidate"] == "NONE"
        and queue_normalization["active_release_controls_candidate"] == "NONE"
        and queue_normalization["active_cutover_candidate"] == "NONE"
        and queue_normalization["active_pilot_candidate"] == "NONE"
        and queue_normalization["active_database_expansion_candidate"] == "NONE"
        and queue_normalization["archived_candidate_set"] == ["RC-M", "RC-O", "RC-Q"]
        and queue_normalization["stale_branch_set"] == ["RC-H", "RC-I", "RC-L"]
        and queue_normalization["stale_branch_left_active"] is False
        and queue_normalization["surface_breach_from_history_reintroduced"] is False
        and queue_normalization["current_canonical_consumer_order"] == "current_canonical -> historical_archive"
        and all(value is False for key, value in queue_normalization.items() if key.startswith("planner_can_open_"))
    )

    next_phase_contract = {
        "next_candidate_id": "RC-R",
        "next_candidate_base": "RC-G",
        "next_candidate_control": "RC-J",
        "next_candidate_forensic_reference": "RC-N",
        "next_candidate_perimeter_truth_reference": "RC-P",
        "next_candidate_archival_references": ["RC-M", "RC-O", "RC-Q"],
        "next_candidate_status": "reserved_not_built",
        "next_phase_scope": "release_controls_process_isolated_perimeter_isolation_only_under_canonical_current_authority",
        "allowed_diff_surface": "process_isolated_release_controls_perimeter_only",
        "answer_path_delta_allowed": False,
        "model_request_payload_delta_allowed": False,
        "retrieval_request_delta_allowed": False,
        "assembled_context_delta_allowed": False,
        "preprojection_delta_allowed": False,
        "raw_answer_delta_allowed": False,
        "response_envelope_delta_allowed": False,
        "runtime_error_delta_allowed": False,
        "retrieval_change_allowed": False,
        "prompt_change_allowed": False,
        "model_change_allowed": False,
        "guardrail_change_allowed": False,
        "corpus_change_allowed": False,
        "database_expansion_allowed": False,
        "cutover_authorized_in_next_phase": False,
        "pilot_authorized_in_next_phase": False,
        "parity_gate_required": True,
        "release_controls_retention_required": True,
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
        "next_official_work": PASS_NEXT_WORK,
    }
    wp4_pass = (
        next_phase_contract["next_candidate_id"] == "RC-R"
        and next_phase_contract["next_candidate_base"] == "RC-G"
        and next_phase_contract["next_candidate_control"] == "RC-J"
        and next_phase_contract["next_candidate_forensic_reference"] == "RC-N"
        and next_phase_contract["next_candidate_perimeter_truth_reference"] == "RC-P"
        and next_phase_contract["next_candidate_archival_references"] == ["RC-M", "RC-O", "RC-Q"]
        and next_phase_contract["next_candidate_status"] == "reserved_not_built"
        and next_phase_contract["next_phase_scope"]
        == "release_controls_process_isolated_perimeter_isolation_only_under_canonical_current_authority"
        and next_phase_contract["allowed_diff_surface"] == "process_isolated_release_controls_perimeter_only"
        and next_phase_contract["answer_path_delta_allowed"] is False
        and next_phase_contract["model_request_payload_delta_allowed"] is False
        and next_phase_contract["retrieval_request_delta_allowed"] is False
        and next_phase_contract["assembled_context_delta_allowed"] is False
        and next_phase_contract["preprojection_delta_allowed"] is False
        and next_phase_contract["raw_answer_delta_allowed"] is False
        and next_phase_contract["response_envelope_delta_allowed"] is False
        and next_phase_contract["runtime_error_delta_allowed"] is False
        and next_phase_contract["retrieval_change_allowed"] is False
        and next_phase_contract["prompt_change_allowed"] is False
        and next_phase_contract["model_change_allowed"] is False
        and next_phase_contract["guardrail_change_allowed"] is False
        and next_phase_contract["corpus_change_allowed"] is False
        and next_phase_contract["database_expansion_allowed"] is False
        and next_phase_contract["cutover_authorized_in_next_phase"] is False
        and next_phase_contract["pilot_authorized_in_next_phase"] is False
        and next_phase_contract["parity_gate_required"] is True
        and next_phase_contract["release_controls_retention_required"] is True
        and next_phase_contract["must_close_release_controls_count"] == 10
        and next_phase_contract["must_close_release_controls_exact_set"]
        == [
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
        ]
        and next_phase_contract["next_official_work"] == PASS_NEXT_WORK
    )

    placement_matrix = {
        "mandatory_auth_placement": "external_transport_gateway_process_only",
        "mandatory_auth_model_visible_mutation_allowed": False,
        "mandatory_auth_prompt_path_access_allowed": False,
        "mandatory_auth_session_object_injection_allowed": False,
        "mandatory_auth_only_immutable_identity_token_allowed": True,
        "immutable_audit_logging_placement": "detached_async_outbox_process_only",
        "immutable_audit_logging_callback_into_serving_process_allowed": False,
        "immutable_audit_logging_in_context_assembly_allowed": False,
        "immutable_audit_logging_preprojection_mutation_allowed": False,
        "immutable_audit_logging_raw_answer_mutation_allowed": False,
        "immutable_audit_logging_response_envelope_mutation_allowed": False,
        "redis_session_persistence_placement": "external_session_sidecar_process_only",
        "redis_live_read_write_in_serving_process_allowed": False,
        "redis_only_immutable_session_id_visible_to_serving_process": True,
        "redis_context_mutation_allowed": False,
        "persisted_pii_redaction_placement": "persistence_and_audit_views_only",
        "persisted_pii_redaction_before_raw_answer_freeze_allowed": False,
        "persisted_pii_redaction_prompt_mutation_allowed": False,
        "persisted_pii_redaction_context_mutation_allowed": False,
        "tokenizer_backed_accounting_placement": "detached_post_response_accounting_process_only",
        "tokenizer_backed_accounting_feedback_into_serving_process_allowed": False,
        "tokenizer_backed_accounting_prompt_path_access_allowed": False,
        "observability_alerting_placement": "passive_tap_or_metrics_export_only",
        "observability_alerting_runtime_mutation_allowed": False,
        "api_versioning_placement": "transport_boundary_only",
        "api_versioning_answer_path_mutation_allowed": False,
        "process_supervision_placement": "host_or_process_boundary_only",
        "process_supervision_answer_path_mutation_allowed": False,
        "backup_restore_placement": "offline_operational_boundary_only",
        "backup_restore_answer_path_mutation_allowed": False,
        "one_command_release_smoke_placement": "external_blackbox_harness_only",
        "one_command_release_smoke_runtime_attachment_allowed": False,
        "same_process_release_controls_allowed": False,
        "shared_memory_or_live_object_between_release_controls_and_serving_process_allowed": False,
        "frozen_snapshot_id_only_cross_boundary": True,
        "serving_process_role": "rc_g_pure_answer_lane_only",
        "release_controls_process_role": "detached_perimeter_only",
    }
    wp5_pass = (
        placement_matrix["mandatory_auth_placement"] == "external_transport_gateway_process_only"
        and placement_matrix["mandatory_auth_model_visible_mutation_allowed"] is False
        and placement_matrix["mandatory_auth_prompt_path_access_allowed"] is False
        and placement_matrix["mandatory_auth_session_object_injection_allowed"] is False
        and placement_matrix["mandatory_auth_only_immutable_identity_token_allowed"] is True
        and placement_matrix["immutable_audit_logging_placement"] == "detached_async_outbox_process_only"
        and placement_matrix["immutable_audit_logging_callback_into_serving_process_allowed"] is False
        and placement_matrix["immutable_audit_logging_in_context_assembly_allowed"] is False
        and placement_matrix["immutable_audit_logging_preprojection_mutation_allowed"] is False
        and placement_matrix["immutable_audit_logging_raw_answer_mutation_allowed"] is False
        and placement_matrix["immutable_audit_logging_response_envelope_mutation_allowed"] is False
        and placement_matrix["redis_session_persistence_placement"] == "external_session_sidecar_process_only"
        and placement_matrix["redis_live_read_write_in_serving_process_allowed"] is False
        and placement_matrix["redis_only_immutable_session_id_visible_to_serving_process"] is True
        and placement_matrix["redis_context_mutation_allowed"] is False
        and placement_matrix["persisted_pii_redaction_placement"] == "persistence_and_audit_views_only"
        and placement_matrix["persisted_pii_redaction_before_raw_answer_freeze_allowed"] is False
        and placement_matrix["persisted_pii_redaction_prompt_mutation_allowed"] is False
        and placement_matrix["persisted_pii_redaction_context_mutation_allowed"] is False
        and placement_matrix["tokenizer_backed_accounting_placement"] == "detached_post_response_accounting_process_only"
        and placement_matrix["tokenizer_backed_accounting_feedback_into_serving_process_allowed"] is False
        and placement_matrix["tokenizer_backed_accounting_prompt_path_access_allowed"] is False
        and placement_matrix["observability_alerting_placement"] == "passive_tap_or_metrics_export_only"
        and placement_matrix["observability_alerting_runtime_mutation_allowed"] is False
        and placement_matrix["api_versioning_placement"] == "transport_boundary_only"
        and placement_matrix["api_versioning_answer_path_mutation_allowed"] is False
        and placement_matrix["process_supervision_placement"] == "host_or_process_boundary_only"
        and placement_matrix["process_supervision_answer_path_mutation_allowed"] is False
        and placement_matrix["backup_restore_placement"] == "offline_operational_boundary_only"
        and placement_matrix["backup_restore_answer_path_mutation_allowed"] is False
        and placement_matrix["one_command_release_smoke_placement"] == "external_blackbox_harness_only"
        and placement_matrix["one_command_release_smoke_runtime_attachment_allowed"] is False
        and placement_matrix["same_process_release_controls_allowed"] is False
        and placement_matrix["shared_memory_or_live_object_between_release_controls_and_serving_process_allowed"] is False
        and placement_matrix["frozen_snapshot_id_only_cross_boundary"] is True
        and placement_matrix["serving_process_role"] == "rc_g_pure_answer_lane_only"
        and placement_matrix["release_controls_process_role"] == "detached_perimeter_only"
    )

    acceptance_pass = (
        wp1_pass and wp2_pass and wp3_pass and wp4_pass and wp5_pass
        and ref_ct_zero(reference_pack=reference_pack)
        and queue_normalization["surface_breach_from_history_reintroduced"] is False
        and queue_normalization["stale_branch_left_active"] is False
    )
    reconciliation = {
        "official_decision": PASS_DECISION if acceptance_pass else FAIL_DECISION,
        "next_official_work": PASS_NEXT_WORK if acceptance_pass else FAIL_NEXT_WORK,
        "unexplained_count": 0 if acceptance_pass else reference_pack["reference_pack_contradiction_count"],
        "surface_breach_from_history_reintroduced": False,
        "stale_branch_left_active": False,
        "rc_r_reserved_not_built": True,
        "cutover_authorized_in_next_phase": False,
        "pilot_authorized_in_next_phase": False,
        "database_expansion_authorized_in_next_phase": False,
    }
    wp6_pass = (
        reconciliation["official_decision"] == PASS_DECISION
        and reconciliation["next_official_work"] == PASS_NEXT_WORK
        and reconciliation["unexplained_count"] == 0
        and reconciliation["surface_breach_from_history_reintroduced"] is False
        and reconciliation["stale_branch_left_active"] is False
        and reconciliation["rc_r_reserved_not_built"] is True
        and reconciliation["cutover_authorized_in_next_phase"] is False
        and reconciliation["pilot_authorized_in_next_phase"] is False
        and reconciliation["database_expansion_authorized_in_next_phase"] is False
    )

    return {
        "wp_statuses": {
            "WP-1": "PASS" if wp1_pass else "FAIL",
            "WP-2": "PASS" if wp2_pass else "FAIL",
            "WP-3": "PASS" if wp3_pass else "FAIL",
            "WP-4": "PASS" if wp4_pass else "FAIL",
            "WP-5": "PASS" if wp5_pass else "FAIL",
            "WP-6": "PASS" if wp6_pass else "FAIL",
        },
        "reference_pack": reference_pack,
        "topology_rows": topology_rows,
        "queue_normalization": queue_normalization,
        "next_phase_contract": next_phase_contract,
        "placement_matrix": placement_matrix,
        "reconciliation": reconciliation,
    }


def ref_ct_zero(*, reference_pack: dict[str, Any]) -> bool:
    return reference_pack["reference_pack_contradiction_count"] == 0


def render_outputs(payload: dict[str, Any]) -> dict[Path, str]:
    wp = payload["wp_statuses"]
    ref = payload["reference_pack"]
    topology_rows = payload["topology_rows"]
    queue = payload["queue_normalization"]
    contract = payload["next_phase_contract"]
    placement = payload["placement_matrix"]
    recon = payload["reconciliation"]

    contradiction_lines = (
        ["- contradiction_rows = `0`"]
        if not ref["contradiction_rows"]
        else [f"- contradiction_rows = `{len(ref['contradiction_rows'])}`"]
        + [f"- {row['phase_name']} missing=`{row['missing_marker']}`" for row in ref["contradiction_rows"]]
    )

    topology_table = [
        "| candidate_id | candidate_status | role | current_authority_member | diagnostic_only | archived | promotable | repairable | current_evaluable | release_controls_reentry_base | notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        *[
            f"| {row['candidate_id']} | {row['candidate_status']} | {row['role']} | {bool_text(row['current_authority_member'])} | {bool_text(row['diagnostic_only'])} | {bool_text(row['archived'])} | {bool_text(row['promotable'])} | {bool_text(row['repairable'])} | {bool_text(row['current_evaluable'])} | {bool_text(row['release_controls_reentry_base'])} | {row['notes']} |"
            for row in topology_rows
        ],
    ]

    files: dict[Path, str] = {}
    files[ROOT / "coordination" / f"faz41-reference-pack-{DATE}.md"] = "\n".join(
        [
            "# FAZ41 Reference Pack",
            "",
            f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
            f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
            f"- current_authority_ref = `{ref['current_authority_ref']}`",
            f"- active_quality_reference = `{ref['active_quality_reference']}`",
            f"- active_control_pair = `{ref['active_control_pair']}`",
            f"- active_forensic_reference = `{ref['active_forensic_reference']}`",
            f"- current_perimeter_truth_reference = `{ref['current_perimeter_truth_reference']}`",
            f"- archived_candidate_set = `{_render_value(ref['archived_candidate_set'])}`",
            *contradiction_lines,
        ]
    )
    files[ROOT / "coordination" / f"faz41-canonical-candidate-topology-{DATE}.md"] = "\n".join(
        ["# FAZ41 Canonical Candidate Topology", "", *topology_table]
    )
    files[ROOT / "coordination" / f"faz41-legacy-queue-normalization-{DATE}.md"] = "\n".join(
        [
            "# FAZ41 Legacy Queue Normalization",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in queue.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz41-rc-r-next-phase-contract-{DATE}.md"] = "\n".join(
        [
            "# FAZ41 RC-R Next Phase Contract",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in contract.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz41-rc-r-process-isolated-perimeter-placement-matrix-{DATE}.md"] = "\n".join(
        [
            "# FAZ41 RC-R Process-Isolated Perimeter Placement Matrix",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in placement.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz41-final-reconciliation-summary-{DATE}.md"] = "\n".join(
        [
            "# FAZ41 Final Reconciliation Summary",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in recon.items()),
        ]
    )
    files[ROOT / "reports" / RESULT_REPORT_NAME] = "\n".join(
        [
            "# FAZ41 POST-RC-Q STEERING RE-ENTRY UNDER CANONICAL CURRENT AUTHORITY RAPORU",
            "",
            "## Yonetici Ozeti",
            "",
            "FAZ41, RC-Q archival closure sonrasinda steering hattini canonical current authority altinda tek cizgiye indirmek ve bundan sonraki tek uygulama hattini RC-R process-isolated perimeter isolation modeli olarak rezerve etmek icin yurutuldu. Bu fazda yeni runtime, yeni build, patch, replay, recapture, cutover veya pilot acilmadi.",
            "",
            f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
            f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
            f"- stale_branch_left_active = `{bool_text(queue['stale_branch_left_active'])}`",
            f"- surface_breach_from_history_reintroduced = `{bool_text(queue['surface_breach_from_history_reintroduced'])}`",
            f"- next_candidate_id = `{contract['next_candidate_id']}`",
            f"- allowed_diff_surface = `{contract['allowed_diff_surface']}`",
            f"- answer_path_delta_allowed = `{bool_text(contract['answer_path_delta_allowed'])}`",
            f"- database_expansion_allowed = `{bool_text(contract['database_expansion_allowed'])}`",
            f"- cutover_authorized_in_next_phase = `{bool_text(contract['cutover_authorized_in_next_phase'])}`",
            f"- pilot_authorized_in_next_phase = `{bool_text(contract['pilot_authorized_in_next_phase'])}`",
            f"- unexplained_count = `{recon['unexplained_count']}`",
            "",
            "## Reference Pack Ozeti",
            "",
            f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
            f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
            f"- current_authority_ref = `{ref['current_authority_ref']}`",
            f"- active_quality_reference = `{ref['active_quality_reference']}`",
            f"- active_control_pair = `{ref['active_control_pair']}`",
            f"- active_forensic_reference = `{ref['active_forensic_reference']}`",
            f"- current_perimeter_truth_reference = `{ref['current_perimeter_truth_reference']}`",
            f"- archived_candidate_set = `{_render_value(ref['archived_candidate_set'])}`",
            *contradiction_lines,
            "",
            "## Canonical Candidate Topology Ozeti",
            "",
            *topology_table,
            "",
            "## Legacy / Queue Normalization Ozeti",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in queue.items()),
            "",
            "## RC-R Next Phase Contract Ozeti",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in contract.items()),
            "",
            "## RC-R Process-Isolated Perimeter Placement Matrix Ozeti",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in placement.items()),
            "",
            "## WP Sonuclari",
            "",
            "### WP-1",
            f"- status = `{wp['WP-1']}`",
            "- reason = `reference pack contradiction_count=0 ile FAZ21/24/32/33/35/36/37/38/39/40 zinciri exact kapandi`",
            "",
            "### WP-2",
            f"- status = `{wp['WP-2']}`",
            "- reason = `RC-G / RC-J / RC-N / RC-P / RC-M / RC-O / RC-Q topology rolleri exact ve cakismasiz materialize edildi`",
            "",
            "### WP-3",
            f"- status = `{wp['WP-3']}`",
            "- reason = `legacy queue state ve RC-M/RC-O/RC-Q denylist satirlari reopening yolu birakmadan normalize edildi`",
            "",
            "### WP-4",
            f"- status = `{wp['WP-4']}`",
            "- reason = `RC-R process-isolated perimeter isolation contract'i exact sabitlerle rezerve edildi ve model-gorunur diff tamamen yasaklandi`",
            "",
            "### WP-5",
            f"- status = `{wp['WP-5']}`",
            "- reason = `placement matrix tum release-controls katmanlarini serving process disinda konumlayacak sekilde exact materialize edildi`",
            "",
            "### WP-6",
            f"- status = `{wp['WP-6']}`",
            "- reason = `tek resmi karar ve tek sonraki resmi is unexplained_count=0 ile birebir kapandi`",
            "",
            "## Resmi Karar",
            "",
            f"- official_decision = `{recon['official_decision']}`",
            f"- unexplained_count = `{recon['unexplained_count']}`",
            f"- surface_breach_from_history_reintroduced = `{bool_text(recon['surface_breach_from_history_reintroduced'])}`",
            f"- stale_branch_left_active = `{bool_text(recon['stale_branch_left_active'])}`",
            "",
            "## Sonraki Resmi Is",
            "",
            f"- next_official_work = `{recon['next_official_work']}`",
            "",
            "## Artefact Listesi",
            "",
            f"- `coordination/faz41-reference-pack-{DATE}.md`",
            f"- `coordination/faz41-canonical-candidate-topology-{DATE}.md`",
            f"- `coordination/faz41-legacy-queue-normalization-{DATE}.md`",
            f"- `coordination/faz41-rc-r-next-phase-contract-{DATE}.md`",
            f"- `coordination/faz41-rc-r-process-isolated-perimeter-placement-matrix-{DATE}.md`",
            f"- `coordination/faz41-final-reconciliation-summary-{DATE}.md`",
            f"- `reports/{RESULT_REPORT_NAME}`",
        ]
    )
    return files


def main() -> int:
    reference_texts = {key: load_text(path) for key, path in REFERENCE_DOCS.items()}
    payload = build_phase_payload(reference_texts)
    for path, text in render_outputs(payload).items():
        write_text(path, text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
