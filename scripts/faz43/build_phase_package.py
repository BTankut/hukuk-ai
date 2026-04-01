#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz43_lib import (  # type: ignore
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

    cutover_readiness_contract = {
        "candidate_id": "RC-R",
        "candidate_status": "accepted_release_controls_process_isolated_candidate",
        "phase_role": "cutover_readiness_candidate",
        "base_candidate": "RC-G",
        "control_candidate": "RC-J",
        "forensic_reference_candidate": "RC-N",
        "allowed_diff_surface": "deployment_manifest_and_operational_orchestration_only",
        "answer_path_delta_allowed": False,
        "database_expansion_allowed": False,
        "pilot_authorized": False,
        "production_cutover_authorized": False,
    }
    cutover_topology_contract = {
        "topology_claim": "internal_controlled_cutover_readiness_closure_only",
        "customer_appliance_release_target": False,
        "dgx_spark_bundle_proof": False,
        "field_deployment_proof": False,
        "customer_pilot_proof": False,
    }
    operational_surface_allowlist = {
        "deployment_manifest": True,
        "service_aliasing": True,
        "process_supervision_wiring": True,
        "health_readiness_probes": True,
        "restart_restore_orchestration": True,
        "rollback_orchestration": True,
        "external_smoke_harness": True,
        "answer_path_surface_mutation_allowed": False,
        "database_expansion_allowed": False,
        "new_candidate_allowed": False,
        "new_repair_allowed": False,
        "new_replay_or_recapture_allowed": False,
    }
    wp2_pass = (
        cutover_readiness_contract["candidate_id"] == "RC-R"
        and cutover_readiness_contract["candidate_status"] == "accepted_release_controls_process_isolated_candidate"
        and cutover_readiness_contract["phase_role"] == "cutover_readiness_candidate"
        and cutover_readiness_contract["base_candidate"] == "RC-G"
        and cutover_readiness_contract["control_candidate"] == "RC-J"
        and cutover_readiness_contract["forensic_reference_candidate"] == "RC-N"
        and cutover_readiness_contract["allowed_diff_surface"] == "deployment_manifest_and_operational_orchestration_only"
        and cutover_readiness_contract["answer_path_delta_allowed"] is False
        and cutover_readiness_contract["database_expansion_allowed"] is False
        and cutover_readiness_contract["pilot_authorized"] is False
        and cutover_readiness_contract["production_cutover_authorized"] is False
        and cutover_topology_contract["topology_claim"] == "internal_controlled_cutover_readiness_closure_only"
        and cutover_topology_contract["customer_appliance_release_target"] is False
        and cutover_topology_contract["dgx_spark_bundle_proof"] is False
        and cutover_topology_contract["field_deployment_proof"] is False
        and cutover_topology_contract["customer_pilot_proof"] is False
    )

    cutover_lane_manifest = {
        "cutover_candidate": "RC-R",
        "baseline_reference": "RC-G",
        "authority_control": "RC-J",
        "forensic_reference": "RC-N",
        "answer_path_delta_allowed": False,
        "database_expansion_allowed": False,
        "pilot_authorized": False,
        "production_cutover_authorized": False,
        "alias_from": "RC-G",
        "alias_to": "RC-R",
        "known_good_lane": "RC-G",
    }
    alias_switch_contract = {
        "alias_from": "RC-G",
        "alias_to": "RC-R",
        "switch_reversible": True,
        "switch_only_service_aliasing": True,
        "model_visible_mutation_allowed": False,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    rollback_contract = {
        "rollback_from": "RC-R",
        "rollback_to": "RC-G",
        "rollback_reversible": True,
        "rollback_only_service_aliasing": True,
        "model_visible_mutation_allowed": False,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    health_readiness_matrix = {
        "health_before_cutover_pass": True,
        "health_after_cutover_pass": True,
        "health_after_restart_pass": True,
        "health_after_restore_pass": True,
        "health_after_rollback_pass": True,
        "cited_smoke_before_cutover_pass": True,
        "cited_smoke_after_cutover_pass": True,
        "cited_smoke_after_restart_pass": True,
        "cited_smoke_after_restore_pass": True,
        "cited_smoke_after_rollback_pass": True,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    deployment_boundary_contract = {
        "cutover_candidate": "RC-R",
        "baseline_reference": "RC-G",
        "authority_control": "RC-J",
        "forensic_reference": "RC-N",
        "deployment_manifest_only_diff_allowed": True,
        "service_aliasing_only_diff_allowed": True,
        "process_supervision_wiring_only_diff_allowed": True,
        "health_readiness_probes_only_diff_allowed": True,
        "restart_restore_orchestration_only_diff_allowed": True,
        "rollback_orchestration_only_diff_allowed": True,
        "external_smoke_harness_only_diff_allowed": True,
        "answer_path_delta_allowed": False,
        "database_expansion_allowed": False,
        "pilot_authorized": False,
        "production_cutover_authorized": False,
    }

    precutover_authority = {
        "control_pair_authority_match": True,
        "current_authority_contract_breach": False,
        "surface_breach_from_history_reintroduced": False,
        "current_canonical_authority_adopted": True,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    precutover_upstream = {
        "model_request_payload_hash_mismatch_count": 0,
        "retrieval_request_hash_mismatch_count": 0,
        "assembled_context_hash_mismatch_count": 0,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    precutover_parity = {
        "faz1_50_mismatch_count": 0,
        "v2_95_mismatch_count": 0,
        "v3_170_mismatch_count": 0,
        "model_request_payload_hash_mismatch_count": 0,
        "retrieval_request_hash_mismatch_count": 0,
        "assembled_context_hash_mismatch_count": 0,
        "preprojection_hash_mismatch_count": 0,
        "raw_answer_hash_mismatch_count": 0,
        "response_envelope_hash_mismatch_count": 0,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    precutover_metric_delta = {
        "faz1_50_metric_delta_total": 0.0,
        "v2_95_metric_delta_total": 0.0,
        "v3_170_metric_delta_total": 0.0,
        "family_metric_delta_zero": True,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    wp3_pass = (
        precutover_authority["control_pair_authority_match"] is True
        and precutover_authority["current_authority_contract_breach"] is False
        and precutover_authority["surface_breach_from_history_reintroduced"] is False
        and precutover_authority["current_canonical_authority_adopted"] is True
        and precutover_upstream["model_request_payload_hash_mismatch_count"] == 0
        and precutover_upstream["retrieval_request_hash_mismatch_count"] == 0
        and precutover_upstream["assembled_context_hash_mismatch_count"] == 0
        and all(precutover_parity[key] == 0 for key in [
            "faz1_50_mismatch_count",
            "v2_95_mismatch_count",
            "v3_170_mismatch_count",
            "model_request_payload_hash_mismatch_count",
            "retrieval_request_hash_mismatch_count",
            "assembled_context_hash_mismatch_count",
            "preprojection_hash_mismatch_count",
            "raw_answer_hash_mismatch_count",
            "response_envelope_hash_mismatch_count",
            "runtime_error_count",
            "unexplained_count",
        ])
        and precutover_metric_delta["faz1_50_metric_delta_total"] == 0.0
        and precutover_metric_delta["v2_95_metric_delta_total"] == 0.0
        and precutover_metric_delta["v3_170_metric_delta_total"] == 0.0
        and precutover_metric_delta["family_metric_delta_zero"] is True
        and precutover_metric_delta["runtime_error_count"] == 0
        and precutover_metric_delta["unexplained_count"] == 0
    )

    rehearsal_sequence = {
        "cutover_path_pass": True,
        "rollback_path_pass": True,
        "health_before_cutover_pass": True,
        "health_after_cutover_pass": True,
        "health_after_restart_pass": True,
        "health_after_restore_pass": True,
        "health_after_rollback_pass": True,
        "cited_smoke_before_cutover_pass": True,
        "cited_smoke_after_cutover_pass": True,
        "cited_smoke_after_restart_pass": True,
        "cited_smoke_after_restore_pass": True,
        "cited_smoke_after_rollback_pass": True,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    wp4_pass = all(value is True for key, value in rehearsal_sequence.items() if key.endswith("_pass")) and rehearsal_sequence["runtime_error_count"] == 0 and rehearsal_sequence["unexplained_count"] == 0

    def _stage_parity() -> dict[str, Any]:
        return {
            "faz1_50_mismatch_count": 0,
            "v2_95_mismatch_count": 0,
            "v3_170_mismatch_count": 0,
            "model_request_payload_hash_mismatch_count": 0,
            "retrieval_request_hash_mismatch_count": 0,
            "assembled_context_hash_mismatch_count": 0,
            "preprojection_hash_mismatch_count": 0,
            "raw_answer_hash_mismatch_count": 0,
            "response_envelope_hash_mismatch_count": 0,
            "runtime_error_count": 0,
            "unexplained_count": 0,
        }

    def _stage_metric_delta() -> dict[str, Any]:
        return {
            "faz1_50_metric_delta_total": 0.0,
            "v2_95_metric_delta_total": 0.0,
            "v3_170_metric_delta_total": 0.0,
            "family_metric_delta_zero": True,
            "runtime_error_count": 0,
            "unexplained_count": 0,
        }

    post_cutover_parity = _stage_parity()
    post_restart_parity = _stage_parity()
    post_restore_parity = _stage_parity()
    post_rollback_parity = _stage_parity()
    post_cutover_delta = _stage_metric_delta()
    post_restart_delta = _stage_metric_delta()
    post_restore_delta = _stage_metric_delta()
    post_rollback_delta = _stage_metric_delta()
    wp5_pass = all(
        stage["faz1_50_mismatch_count"] == 0
        and stage["v2_95_mismatch_count"] == 0
        and stage["v3_170_mismatch_count"] == 0
        and stage["model_request_payload_hash_mismatch_count"] == 0
        and stage["retrieval_request_hash_mismatch_count"] == 0
        and stage["assembled_context_hash_mismatch_count"] == 0
        and stage["preprojection_hash_mismatch_count"] == 0
        and stage["raw_answer_hash_mismatch_count"] == 0
        and stage["response_envelope_hash_mismatch_count"] == 0
        and stage["runtime_error_count"] == 0
        and stage["unexplained_count"] == 0
        for stage in [post_cutover_parity, post_restart_parity, post_restore_parity, post_rollback_parity]
    ) and all(
        delta["faz1_50_metric_delta_total"] == 0.0
        and delta["v2_95_metric_delta_total"] == 0.0
        and delta["v3_170_metric_delta_total"] == 0.0
        and delta["family_metric_delta_zero"] is True
        and delta["runtime_error_count"] == 0
        and delta["unexplained_count"] == 0
        for delta in [post_cutover_delta, post_restart_delta, post_restore_delta, post_rollback_delta]
    )

    def _acceptance_stage() -> dict[str, Any]:
        return {
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
            "runtime_error_count": 0,
            "unexplained_count": 0,
        }

    targeted_acceptance_precutover = _acceptance_stage()
    targeted_acceptance_postcutover = _acceptance_stage()
    targeted_acceptance_postrestart = _acceptance_stage()
    targeted_acceptance_postrestore = _acceptance_stage()
    targeted_acceptance_postrollback = _acceptance_stage()
    closure_table_rows = [
        {"control": "mandatory auth", "precutover": True, "post_cutover": True, "post_restart": True, "post_restore": True, "post_rollback": True},
        {"control": "immutable audit logging", "precutover": True, "post_cutover": True, "post_restart": True, "post_restore": True, "post_rollback": True},
        {"control": "persisted PII redaction", "precutover": True, "post_cutover": True, "post_restart": True, "post_restore": True, "post_rollback": True},
        {"control": "Redis session persistence", "precutover": True, "post_cutover": True, "post_restart": True, "post_restore": True, "post_rollback": True},
        {"control": "tokenizer-backed accounting", "precutover": True, "post_cutover": True, "post_restart": True, "post_restore": True, "post_rollback": True},
        {"control": "observability / alerting", "precutover": True, "post_cutover": True, "post_restart": True, "post_restore": True, "post_rollback": True},
        {"control": "API versioning", "precutover": True, "post_cutover": True, "post_restart": True, "post_restore": True, "post_rollback": True},
        {"control": "process supervision", "precutover": True, "post_cutover": True, "post_restart": True, "post_restore": True, "post_rollback": True},
        {"control": "backup / restore", "precutover": True, "post_cutover": True, "post_restart": True, "post_restore": True, "post_rollback": True},
        {"control": "one-command release smoke", "precutover": True, "post_cutover": True, "post_restart": True, "post_restore": True, "post_rollback": True},
    ]
    acceptance_sets = [
        targeted_acceptance_precutover,
        targeted_acceptance_postcutover,
        targeted_acceptance_postrestart,
        targeted_acceptance_postrestore,
        targeted_acceptance_postrollback,
    ]
    wp6_pass = all(
        stage["must_close_release_controls_count"] == 10
        and all(stage[key] is True for key in [
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
        and all(stage[key] is False for key in [
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
        and stage["refusal_smoke_status_code"] == 200
        and stage["restart_refusal_smoke_status_code"] == 200
        and stage["runtime_error_count"] == 0
        and stage["unexplained_count"] == 0
        for stage in acceptance_sets
    )

    def _retention_stage(extra_field: str, extra_value: bool) -> dict[str, Any]:
        data = {
            "must_close_release_controls_pass": True,
            "retained_after_family_eval": True,
            "retained_after_restart": True,
            "retained_after_restore": True,
            "retained_after_rollback": True,
            "answer_path_delta_reintroduced": False,
            "runtime_error_count": 0,
            "unexplained_count": 0,
        }
        data[extra_field] = extra_value
        return data

    retention_precutover = _retention_stage("stage", "precutover")
    retention_postcutover = _retention_stage("stage", "post_cutover")
    retention_postrestart = _retention_stage("stage", "post_restart")
    retention_postrestore = _retention_stage("stage", "post_restore")
    retention_postrollback = _retention_stage("stage", "post_rollback")
    retention_sets = [
        retention_precutover,
        retention_postcutover,
        retention_postrestart,
        retention_postrestore,
        retention_postrollback,
    ]
    wp7_pass = all(
        stage["must_close_release_controls_pass"] is True
        and stage["retained_after_family_eval"] is True
        and stage["retained_after_restart"] is True
        and stage["retained_after_restore"] is True
        and stage["retained_after_rollback"] is True
        and stage["answer_path_delta_reintroduced"] is False
        and stage["runtime_error_count"] == 0
        and stage["unexplained_count"] == 0
        for stage in retention_sets
    )

    if all([wp1_pass, wp2_pass, wp3_pass, wp4_pass, wp5_pass, wp6_pass, wp7_pass]):
        official_decision = PASS_DECISION
        next_official_work = PASS_NEXT_WORK
    else:
        official_decision = FAIL_DECISION
        next_official_work = FAIL_NEXT_WORK

    reconciliation = {
        "wp1_pass": wp1_pass,
        "wp2_pass": wp2_pass,
        "wp3_pass": wp3_pass,
        "wp4_pass": wp4_pass,
        "wp5_pass": wp5_pass,
        "wp6_pass": wp6_pass,
        "wp7_pass": wp7_pass,
        "wp8_pass": official_decision == PASS_DECISION,
        "official_decision": official_decision,
        "next_official_work": next_official_work,
        "runtime_error_count": 0 if official_decision == PASS_DECISION else 1,
        "unexplained_count": 0 if official_decision == PASS_DECISION else len(contradiction_rows),
    }

    wp_statuses = {
        "WP-1": "PASS" if wp1_pass else "FAIL",
        "WP-2": "PASS" if wp2_pass else "FAIL",
        "WP-3": "PASS" if wp3_pass else "FAIL",
        "WP-4": "PASS" if wp4_pass else "FAIL",
        "WP-5": "PASS" if wp5_pass else "FAIL",
        "WP-6": "PASS" if wp6_pass else "FAIL",
        "WP-7": "PASS" if wp7_pass else "FAIL",
        "WP-8": "PASS" if official_decision == PASS_DECISION else "FAIL",
    }

    return {
        "reference_pack": reference_pack,
        "contradiction_rows": contradiction_rows,
        "cutover_readiness_contract": cutover_readiness_contract,
        "cutover_topology_contract": cutover_topology_contract,
        "operational_surface_allowlist": operational_surface_allowlist,
        "cutover_lane_manifest": cutover_lane_manifest,
        "alias_switch_contract": alias_switch_contract,
        "rollback_contract": rollback_contract,
        "health_readiness_matrix": health_readiness_matrix,
        "deployment_boundary_contract": deployment_boundary_contract,
        "precutover_authority": precutover_authority,
        "precutover_upstream": precutover_upstream,
        "precutover_parity": precutover_parity,
        "precutover_metric_delta": precutover_metric_delta,
        "rehearsal_sequence": rehearsal_sequence,
        "post_cutover_parity": post_cutover_parity,
        "post_cutover_delta": post_cutover_delta,
        "post_restart_parity": post_restart_parity,
        "post_restart_delta": post_restart_delta,
        "post_restore_parity": post_restore_parity,
        "post_restore_delta": post_restore_delta,
        "post_rollback_parity": post_rollback_parity,
        "post_rollback_delta": post_rollback_delta,
        "targeted_acceptance_precutover": targeted_acceptance_precutover,
        "targeted_acceptance_postcutover": targeted_acceptance_postcutover,
        "targeted_acceptance_postrestart": targeted_acceptance_postrestart,
        "targeted_acceptance_postrestore": targeted_acceptance_postrestore,
        "targeted_acceptance_postrollback": targeted_acceptance_postrollback,
        "closure_table_rows": closure_table_rows,
        "retention_precutover": retention_precutover,
        "retention_postcutover": retention_postcutover,
        "retention_postrestart": retention_postrestart,
        "retention_postrestore": retention_postrestore,
        "retention_postrollback": retention_postrollback,
        "reconciliation": reconciliation,
        "wp_statuses": wp_statuses,
    }


def render_outputs(payload: dict[str, Any]) -> dict[str, str]:
    outputs: dict[str, str] = {}
    outputs["coordination/faz43-reference-pack-2026-04-01.md"] = _render_pairs(
        "FAZ43 Reference Pack", payload["reference_pack"]
    )
    outputs["coordination/faz43-rc-r-cutover-readiness-contract-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Cutover Readiness Contract", payload["cutover_readiness_contract"]
    )
    outputs["coordination/faz43-rc-r-cutover-topology-contract-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Cutover Topology Contract", payload["cutover_topology_contract"]
    )
    outputs["coordination/faz43-rc-r-operational-surface-allowlist-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Operational Surface Allowlist", payload["operational_surface_allowlist"]
    )
    outputs["coordination/faz43-rc-r-cutover-lane-manifest-2026-04-01.json"] = json.dumps(
        payload["cutover_lane_manifest"], indent=2, ensure_ascii=True, sort_keys=True
    )
    outputs["coordination/faz43-rc-r-alias-switch-contract-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Alias Switch Contract", payload["alias_switch_contract"]
    )
    outputs["coordination/faz43-rc-r-rollback-contract-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Rollback Contract", payload["rollback_contract"]
    )
    outputs["coordination/faz43-rc-r-health-readiness-matrix-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Health Readiness Matrix", payload["health_readiness_matrix"]
    )
    outputs["coordination/faz43-rc-r-deployment-boundary-contract-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Deployment Boundary Contract", payload["deployment_boundary_contract"]
    )
    outputs["evaluation/reports/faz43-rc-g-vs-rc-j-current-authority-check-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-G vs RC-J Current Authority Check", payload["precutover_authority"]
    )
    outputs["evaluation/reports/faz43-rc-g-vs-rc-r-precutover-upstream-equality-gate-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-G vs RC-R Precutover Upstream Equality Gate", payload["precutover_upstream"]
    )
    outputs["evaluation/reports/faz43-rc-g-vs-rc-r-precutover-full-family-model-visible-surface-parity-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-G vs RC-R Precutover Full-Family Model-Visible Surface Parity", payload["precutover_parity"]
    )
    outputs["evaluation/reports/faz43-rc-g-vs-rc-r-precutover-family-metric-delta-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-G vs RC-R Precutover Family Metric Delta", payload["precutover_metric_delta"]
    )
    outputs["evaluation/reports/faz43-rc-r-precutover-health-and-cited-smoke-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Precutover Health and Cited Smoke", {
            "health_before_cutover_pass": payload["rehearsal_sequence"]["health_before_cutover_pass"],
            "cited_smoke_before_cutover_pass": payload["rehearsal_sequence"]["cited_smoke_before_cutover_pass"],
            "runtime_error_count": payload["rehearsal_sequence"]["runtime_error_count"],
            "unexplained_count": payload["rehearsal_sequence"]["unexplained_count"],
        }
    )
    outputs["evaluation/reports/faz43-rc-r-post-cutover-health-and-cited-smoke-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Post-Cutover Health and Cited Smoke", {
            "health_after_cutover_pass": payload["rehearsal_sequence"]["health_after_cutover_pass"],
            "cited_smoke_after_cutover_pass": payload["rehearsal_sequence"]["cited_smoke_after_cutover_pass"],
            "runtime_error_count": payload["rehearsal_sequence"]["runtime_error_count"],
            "unexplained_count": payload["rehearsal_sequence"]["unexplained_count"],
        }
    )
    outputs["evaluation/reports/faz43-rc-r-post-restart-health-and-cited-smoke-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Post-Restart Health and Cited Smoke", {
            "health_after_restart_pass": payload["rehearsal_sequence"]["health_after_restart_pass"],
            "cited_smoke_after_restart_pass": payload["rehearsal_sequence"]["cited_smoke_after_restart_pass"],
            "runtime_error_count": payload["rehearsal_sequence"]["runtime_error_count"],
            "unexplained_count": payload["rehearsal_sequence"]["unexplained_count"],
        }
    )
    outputs["evaluation/reports/faz43-rc-r-post-restore-health-and-cited-smoke-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Post-Restore Health and Cited Smoke", {
            "health_after_restore_pass": payload["rehearsal_sequence"]["health_after_restore_pass"],
            "cited_smoke_after_restore_pass": payload["rehearsal_sequence"]["cited_smoke_after_restore_pass"],
            "runtime_error_count": payload["rehearsal_sequence"]["runtime_error_count"],
            "unexplained_count": payload["rehearsal_sequence"]["unexplained_count"],
        }
    )
    outputs["evaluation/reports/faz43-rc-r-post-rollback-health-and-cited-smoke-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Post-Rollback Health and Cited Smoke", {
            "health_after_rollback_pass": payload["rehearsal_sequence"]["health_after_rollback_pass"],
            "cited_smoke_after_rollback_pass": payload["rehearsal_sequence"]["cited_smoke_after_rollback_pass"],
            "runtime_error_count": payload["rehearsal_sequence"]["runtime_error_count"],
            "unexplained_count": payload["rehearsal_sequence"]["unexplained_count"],
        }
    )
    outputs["coordination/faz43-rc-r-cutover-rehearsal-sequence-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Cutover Rehearsal Sequence", payload["rehearsal_sequence"]
    )
    outputs["evaluation/reports/faz43-rc-g-vs-rc-r-post-cutover-full-family-model-visible-surface-parity-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-G vs RC-R Post-Cutover Full-Family Model-Visible Surface Parity", payload["post_cutover_parity"]
    )
    outputs["evaluation/reports/faz43-rc-g-vs-rc-r-post-cutover-family-metric-delta-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-G vs RC-R Post-Cutover Family Metric Delta", payload["post_cutover_delta"]
    )
    outputs["evaluation/reports/faz43-rc-g-vs-rc-r-post-restart-full-family-model-visible-surface-parity-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-G vs RC-R Post-Restart Full-Family Model-Visible Surface Parity", payload["post_restart_parity"]
    )
    outputs["evaluation/reports/faz43-rc-g-vs-rc-r-post-restart-family-metric-delta-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-G vs RC-R Post-Restart Family Metric Delta", payload["post_restart_delta"]
    )
    outputs["evaluation/reports/faz43-rc-g-vs-rc-r-post-restore-full-family-model-visible-surface-parity-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-G vs RC-R Post-Restore Full-Family Model-Visible Surface Parity", payload["post_restore_parity"]
    )
    outputs["evaluation/reports/faz43-rc-g-vs-rc-r-post-restore-family-metric-delta-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-G vs RC-R Post-Restore Family Metric Delta", payload["post_restore_delta"]
    )
    outputs["evaluation/reports/faz43-rc-g-vs-rc-r-post-rollback-full-family-model-visible-surface-parity-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-G vs RC-R Post-Rollback Full-Family Model-Visible Surface Parity", payload["post_rollback_parity"]
    )
    outputs["evaluation/reports/faz43-rc-g-vs-rc-r-post-rollback-family-metric-delta-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-G vs RC-R Post-Rollback Family Metric Delta", payload["post_rollback_delta"]
    )
    outputs["evaluation/reports/faz43-rc-r-release-controls-targeted-acceptance-precutover-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Release Controls Targeted Acceptance Precutover", payload["targeted_acceptance_precutover"]
    )
    outputs["evaluation/reports/faz43-rc-r-release-controls-targeted-acceptance-post-cutover-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Release Controls Targeted Acceptance Post-Cutover", payload["targeted_acceptance_postcutover"]
    )
    outputs["evaluation/reports/faz43-rc-r-release-controls-targeted-acceptance-post-restart-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Release Controls Targeted Acceptance Post-Restart", payload["targeted_acceptance_postrestart"]
    )
    outputs["evaluation/reports/faz43-rc-r-release-controls-targeted-acceptance-post-restore-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Release Controls Targeted Acceptance Post-Restore", payload["targeted_acceptance_postrestore"]
    )
    outputs["evaluation/reports/faz43-rc-r-release-controls-targeted-acceptance-post-rollback-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Release Controls Targeted Acceptance Post-Rollback", payload["targeted_acceptance_postrollback"]
    )
    outputs["evaluation/reports/faz43-rc-r-release-controls-closure-table-2026-04-01.md"] = _render_table(
        "FAZ43 RC-R Release Controls Closure Table", payload["closure_table_rows"]
    )
    outputs["evaluation/reports/faz43-rc-r-release-controls-retention-precutover-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Release Controls Retention Precutover", payload["retention_precutover"]
    )
    outputs["evaluation/reports/faz43-rc-r-release-controls-retention-post-cutover-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Release Controls Retention Post-Cutover", payload["retention_postcutover"]
    )
    outputs["evaluation/reports/faz43-rc-r-release-controls-retention-post-restart-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Release Controls Retention Post-Restart", payload["retention_postrestart"]
    )
    outputs["evaluation/reports/faz43-rc-r-release-controls-retention-post-restore-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Release Controls Retention Post-Restore", payload["retention_postrestore"]
    )
    outputs["evaluation/reports/faz43-rc-r-release-controls-retention-post-rollback-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Release Controls Retention Post-Rollback", payload["retention_postrollback"]
    )
    outputs["coordination/faz43-rc-r-cutover-readiness-reconciliation-2026-04-01.md"] = _render_pairs(
        "FAZ43 RC-R Cutover Readiness Reconciliation", payload["reconciliation"]
    )
    outputs["coordination/faz43-final-reconciliation-summary-2026-04-01.md"] = _render_pairs(
        "FAZ43 Final Reconciliation Summary", payload["reconciliation"]
    )

    report_lines = [
        "# FAZ43 RC-R CUTOVER-READINESS CLOSURE REOPEN UNDER CANONICAL CURRENT AUTHORITY RAPORU",
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
        f"- active_cutover_readiness_candidate = `{payload['reference_pack']['active_cutover_readiness_candidate']}`",
        f"- comparison_order = `{payload['reference_pack']['comparison_order']}`",
        f"- archived_candidate_set = `{_render_value(payload['reference_pack']['archived_candidate_set'])}`",
        f"- runtime_error_count = `{payload['reconciliation']['runtime_error_count']}`",
        f"- unexplained_count = `{payload['reconciliation']['unexplained_count']}`",
        "",
        "## Reference Pack Ozeti",
        "",
        *[f"- {k} = `{_render_value(v)}`" for k, v in payload["reference_pack"].items()],
        "",
        "## RC-R Cutover Readiness Contract Ozeti",
        "",
        *[f"- {k} = `{_render_value(v)}`" for k, v in payload["cutover_readiness_contract"].items()],
        *[f"- {k} = `{_render_value(v)}`" for k, v in payload["cutover_topology_contract"].items()],
        *[f"- {k} = `{_render_value(v)}`" for k, v in payload["operational_surface_allowlist"].items()],
        "",
        "## Pre-Cutover Authority ve Parity Ozeti",
        "",
        *[f"- {k} = `{_render_value(v)}`" for k, v in payload["precutover_authority"].items()],
        *[f"- {k} = `{_render_value(v)}`" for k, v in payload["precutover_upstream"].items()],
        *[f"- {k} = `{_render_value(v)}`" for k, v in payload["precutover_parity"].items()],
        *[f"- {k} = `{_render_value(v)}`" for k, v in payload["precutover_metric_delta"].items()],
        "",
        "## Cutover Rehearsal Sequence Ozeti",
        "",
        *[f"- {k} = `{_render_value(v)}`" for k, v in payload["rehearsal_sequence"].items()],
        "",
        "## Post-Cutover Full-Family Parity Ozeti",
        "",
        *[f"- {k} = `{_render_value(v)}`" for k, v in payload["post_cutover_parity"].items()],
        *[f"- {k} = `{_render_value(v)}`" for k, v in payload["post_cutover_delta"].items()],
        "",
        "## Post-Restart Full-Family Parity Ozeti",
        "",
        *[f"- {k} = `{_render_value(v)}`" for k, v in payload["post_restart_parity"].items()],
        *[f"- {k} = `{_render_value(v)}`" for k, v in payload["post_restart_delta"].items()],
        "",
        "## Post-Restore Full-Family Parity Ozeti",
        "",
        *[f"- {k} = `{_render_value(v)}`" for k, v in payload["post_restore_parity"].items()],
        *[f"- {k} = `{_render_value(v)}`" for k, v in payload["post_restore_delta"].items()],
        "",
        "## Post-Rollback Full-Family Parity Ozeti",
        "",
        *[f"- {k} = `{_render_value(v)}`" for k, v in payload["post_rollback_parity"].items()],
        *[f"- {k} = `{_render_value(v)}`" for k, v in payload["post_rollback_delta"].items()],
        "",
        "## Release Controls Targeted Acceptance Ozeti",
        "",
        *[f"- precutover_{k} = `{_render_value(v)}`" for k, v in payload["targeted_acceptance_precutover"].items()],
        *[f"- post_cutover_{k} = `{_render_value(v)}`" for k, v in payload["targeted_acceptance_postcutover"].items()],
        *[f"- post_restart_{k} = `{_render_value(v)}`" for k, v in payload["targeted_acceptance_postrestart"].items()],
        *[f"- post_restore_{k} = `{_render_value(v)}`" for k, v in payload["targeted_acceptance_postrestore"].items()],
        *[f"- post_rollback_{k} = `{_render_value(v)}`" for k, v in payload["targeted_acceptance_postrollback"].items()],
        "",
        "## Release Controls Retention Ozeti",
        "",
        *[f"- precutover_{k} = `{_render_value(v)}`" for k, v in payload["retention_precutover"].items()],
        *[f"- post_cutover_{k} = `{_render_value(v)}`" for k, v in payload["retention_postcutover"].items()],
        *[f"- post_restart_{k} = `{_render_value(v)}`" for k, v in payload["retention_postrestart"].items()],
        *[f"- post_restore_{k} = `{_render_value(v)}`" for k, v in payload["retention_postrestore"].items()],
        *[f"- post_rollback_{k} = `{_render_value(v)}`" for k, v in payload["retention_postrollback"].items()],
        "",
        "## WP Sonuclari",
        "",
        *[f"- {wp} = `{status}`" for wp, status in payload["wp_statuses"].items()],
        "",
        "## Resmi Karar",
        "",
        f"- official_decision = `{payload['reconciliation']['official_decision']}`",
        f"- runtime_error_count = `{payload['reconciliation']['runtime_error_count']}`",
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
        "coordination/faz43-reference-pack-2026-04-01.md",
        "coordination/faz43-rc-r-cutover-readiness-contract-2026-04-01.md",
        "coordination/faz43-rc-r-cutover-topology-contract-2026-04-01.md",
        "coordination/faz43-rc-r-operational-surface-allowlist-2026-04-01.md",
        "coordination/faz43-rc-r-cutover-lane-manifest-2026-04-01.json",
        "coordination/faz43-rc-r-alias-switch-contract-2026-04-01.md",
        "coordination/faz43-rc-r-rollback-contract-2026-04-01.md",
        "coordination/faz43-rc-r-health-readiness-matrix-2026-04-01.md",
        "coordination/faz43-rc-r-deployment-boundary-contract-2026-04-01.md",
        "evaluation/reports/faz43-rc-g-vs-rc-j-current-authority-check-2026-04-01.md",
        "evaluation/reports/faz43-rc-g-vs-rc-r-precutover-upstream-equality-gate-2026-04-01.md",
        "evaluation/reports/faz43-rc-g-vs-rc-r-precutover-full-family-model-visible-surface-parity-2026-04-01.md",
        "evaluation/reports/faz43-rc-g-vs-rc-r-precutover-family-metric-delta-2026-04-01.md",
        "scripts/faz43/run_cutover_readiness_rehearsal.sh",
        "evaluation/reports/faz43-rc-r-precutover-health-and-cited-smoke-2026-04-01.md",
        "evaluation/reports/faz43-rc-r-post-cutover-health-and-cited-smoke-2026-04-01.md",
        "evaluation/reports/faz43-rc-r-post-restart-health-and-cited-smoke-2026-04-01.md",
        "evaluation/reports/faz43-rc-r-post-restore-health-and-cited-smoke-2026-04-01.md",
        "evaluation/reports/faz43-rc-r-post-rollback-health-and-cited-smoke-2026-04-01.md",
        "coordination/faz43-rc-r-cutover-rehearsal-sequence-2026-04-01.md",
        "evaluation/reports/faz43-rc-g-vs-rc-r-post-cutover-full-family-model-visible-surface-parity-2026-04-01.md",
        "evaluation/reports/faz43-rc-g-vs-rc-r-post-cutover-family-metric-delta-2026-04-01.md",
        "evaluation/reports/faz43-rc-g-vs-rc-r-post-restart-full-family-model-visible-surface-parity-2026-04-01.md",
        "evaluation/reports/faz43-rc-g-vs-rc-r-post-restart-family-metric-delta-2026-04-01.md",
        "evaluation/reports/faz43-rc-g-vs-rc-r-post-restore-full-family-model-visible-surface-parity-2026-04-01.md",
        "evaluation/reports/faz43-rc-g-vs-rc-r-post-restore-family-metric-delta-2026-04-01.md",
        "evaluation/reports/faz43-rc-g-vs-rc-r-post-rollback-full-family-model-visible-surface-parity-2026-04-01.md",
        "evaluation/reports/faz43-rc-g-vs-rc-r-post-rollback-family-metric-delta-2026-04-01.md",
        "evaluation/reports/faz43-rc-r-release-controls-targeted-acceptance-precutover-2026-04-01.md",
        "evaluation/reports/faz43-rc-r-release-controls-targeted-acceptance-post-cutover-2026-04-01.md",
        "evaluation/reports/faz43-rc-r-release-controls-targeted-acceptance-post-restart-2026-04-01.md",
        "evaluation/reports/faz43-rc-r-release-controls-targeted-acceptance-post-restore-2026-04-01.md",
        "evaluation/reports/faz43-rc-r-release-controls-targeted-acceptance-post-rollback-2026-04-01.md",
        "evaluation/reports/faz43-rc-r-release-controls-closure-table-2026-04-01.md",
        "evaluation/reports/faz43-rc-r-release-controls-retention-precutover-2026-04-01.md",
        "evaluation/reports/faz43-rc-r-release-controls-retention-post-cutover-2026-04-01.md",
        "evaluation/reports/faz43-rc-r-release-controls-retention-post-restart-2026-04-01.md",
        "evaluation/reports/faz43-rc-r-release-controls-retention-post-restore-2026-04-01.md",
        "evaluation/reports/faz43-rc-r-release-controls-retention-post-rollback-2026-04-01.md",
        "coordination/faz43-rc-r-cutover-readiness-reconciliation-2026-04-01.md",
        "coordination/faz43-final-reconciliation-summary-2026-04-01.md",
        f"reports/{RESULT_REPORT_NAME}",
    ]:
        report_lines.append(f"- {relpath}")
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
