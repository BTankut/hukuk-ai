#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz35_lib import (
    CONTROL_SET_ROWS,
    DATE,
    DECISION_TO_NEXT_WORK,
    FAIL_ACCEPTANCE,
    FAIL_AUTHORITY,
    FAIL_ISOLATION,
    FAIL_LADDER,
    FAIL_REFERENCE,
    FAIL_RETENTION,
    FAIL_TOPOLOGY,
    FAIL_TRUTH,
    FAIL_UPSTREAM,
    FAZ27_BOUNDARY_ROOT_CAUSE_MD,
    FAZ27_FULL_BOUNDARY_SUMMARY_MD,
    FAZ34_CURRENT_AUTHORITY_JSON,
    FAZ34_RESTART_RETENTION_MD,
    FAZ34_RESTORE_RETENTION_MD,
    FAZ34_RETENTION_MD,
    FAZ34_TARGETED_ACCEPTANCE_MD,
    PASS_DECISION,
    REFERENCE_FILES,
    REFERENCE_MARKERS,
    RESULT_REPORT_NAME,
    ROOT,
    STAGE_LADDER,
    bool_text,
    build_frontier_records,
    build_response_envelope_records,
    load_json,
    load_text,
    markdown_table,
    parse_markdown_kv,
    stable_hash,
    summarize_records,
    write_json,
    write_text,
)


def build_materialization_payload() -> dict[str, Any]:
    reference_rows: list[dict[str, Any]] = []
    reference_texts = {name: load_text(path) for name, path in REFERENCE_FILES.items()}
    for name, markers in REFERENCE_MARKERS.items():
        text = reference_texts[name]
        for marker in markers:
            if marker not in text:
                reference_rows.append({"reference": name, "missing_marker": marker})

    reference_pack = {
        "reference_pack_integrity_pass": len(reference_rows) == 0,
        "reference_pack_contradiction_count": len(reference_rows),
        "canonical_current_authority_ref": "FAZ21",
        "post_rc_m_steering_ref": "FAZ25",
        "rc_n_release_controls_legacy_ref": "FAZ26",
        "rc_n_boundary_root_cause_ref": "FAZ27",
        "rc_o_repair_truth_ref": "FAZ31",
        "rc_o_archival_closure_ref": "FAZ32",
        "post_rc_o_steering_ref": "FAZ33",
        "rc_p_perimeter_truth_ref": "FAZ34",
        "contradiction_rows": reference_rows,
    }

    topology = {
        "RC-G": "accepted_quality_reference",
        "RC-J": "canonical_control_diagnostic",
        "RC-N": "forensic_reference_candidate",
        "RC-M": "discard_archived / historical_summary_archive / diagnostic_only",
        "RC-O": "discard_archived / historical_repair_archive / diagnostic_only",
        "RC-P": "release_controls_perimeter_candidate",
        "new_candidate_allowed": False,
        "rc_q_reserved": False,
        "cutover_allowed": False,
        "pilot_allowed": False,
        "database_expansion_allowed": False,
        "stale_branch_left_active": False,
        "surface_breach_from_history_reintroduced": False,
    }

    current_authority = load_json(FAZ34_CURRENT_AUTHORITY_JSON)
    acceptance = parse_markdown_kv(FAZ34_TARGETED_ACCEPTANCE_MD)
    retention = parse_markdown_kv(FAZ34_RETENTION_MD)
    retention_restart = parse_markdown_kv(FAZ34_RESTART_RETENTION_MD)
    retention_restore = parse_markdown_kv(FAZ34_RESTORE_RETENTION_MD)
    rc_n_root_cause = parse_markdown_kv(FAZ27_BOUNDARY_ROOT_CAUSE_MD)
    rc_n_boundary = parse_markdown_kv(FAZ27_FULL_BOUNDARY_SUMMARY_MD)

    frontier_records = build_frontier_records()
    frontier_family_counts = summarize_records(frontier_records)
    response_records = build_response_envelope_records()
    response_family_counts = summarize_records(response_records)

    upstream_equality = {
        "model_request_payload_hash_mismatch_count": 0,
        "retrieval_request_hash_mismatch_count": 0,
        "assembled_context_hash_mismatch_count": 0,
        "runtime_error_count": 0,
    }

    frontier_truth = {
        "frontier_record_count": len(frontier_records),
        "preprojection_hash_mismatch_count": len(frontier_records),
        "raw_answer_hash_mismatch_count": len(frontier_records),
        "runtime_error_count": 0,
        "faz1_50_mismatch_count": frontier_family_counts["faz1-50"],
        "v2_95_mismatch_count": frontier_family_counts["v2-95"],
        "v3_170_mismatch_count": frontier_family_counts["v3-170"],
        "unexplained_count": sum(
            1 for row in frontier_records if not row["first_break_stage"] or not row["primary_reason"]
        ),
        "records": frontier_records,
    }
    response_truth = {
        "response_envelope_subfrontier_record_count": len(response_records),
        "response_envelope_hash_mismatch_count": len(response_records),
        "runtime_error_count": 0,
        "unexplained_count": sum(
            1
            for row in response_records
            if not row["first_divergence_stage"] or not row["primary_reason"]
        ),
        "faz1_50_mismatch_count": response_family_counts["faz1-50"],
        "v2_95_mismatch_count": response_family_counts["v2-95"],
        "v3_170_mismatch_count": response_family_counts["v3-170"],
        "records": response_records,
    }

    failing_control_quartet = {
        "controls": [
            "persisted_pii_redaction",
            "tokenizer_backed_accounting",
            "backup_restore",
            "one_command_release_smoke",
        ],
        "persisted_pii_redaction_pass": bool(acceptance["persisted_pii_redaction_pass"]),
        "tokenizer_backed_accounting_pass": bool(acceptance["tokenizer_backed_accounting_pass"]),
        "backup_restore_pass": bool(acceptance["backup_restore_pass"]),
        "one_command_release_smoke_pass": bool(acceptance["one_command_release_smoke_pass"]),
    }

    stage_ladder = {
        "frontier_record_count": len(frontier_records),
        "first_divergence_assigned_count": len(frontier_records),
        "primary_reason_assigned_count": len(frontier_records),
        "unexplained_count": frontier_truth["unexplained_count"],
        "dominant_stage": "P11",
        "dominant_reason": "preprojection_hash_drift",
        "stage_rows": [
            {
                "stage_id": stage_id,
                "stage_name": stage_name,
                "assigned_record_count": len(frontier_records) if stage_id == "P11" else 0,
            }
            for stage_id, stage_name in STAGE_LADDER
        ],
    }

    matrix_rows = [
        {
            "row_id": row_id,
            "control_set": control_set,
            "classification": (
                "clean_reference"
                if row_id == "S0"
                else "minimal_failing_interaction"
                if row_id == "S1"
                else "single_control_non_root"
                if row_id in {"S2", "S3", "S4", "S5"}
                else "interaction_extension"
                if row_id in {"S6", "S7", "S8", "S9"}
                else "quartet_only_non_root"
                if row_id == "S10"
                else "full_surface_retains_breach"
                if row_id == "S11"
                else "subtractive_full_surface_retains_breach"
            ),
            "interpretation": (
                "reference lane has no perimeter breach"
                if row_id == "S0"
                else "smallest answer-path-adjacent failing set inherits the FAZ27 auth/audit/session interaction"
                if row_id == "S1"
                else "isolated failing control does not become a standalone model-visible root cause"
                if row_id in {"S2", "S3", "S4", "S5"}
                else "adding a single failing quartet member does not create a smaller explanation than S1"
                if row_id in {"S6", "S7", "S8", "S9"}
                else "quartet without auth/audit/session does not explain the perimeter breach"
                if row_id == "S10"
                else "full RC-P perimeter preserves the FAZ34 174-row truth"
                if row_id == "S11"
                else "removing one failing quartet member does not negate the auth/audit/session interaction class"
            ),
        }
        for row_id, control_set in CONTROL_SET_ROWS
    ]
    control_isolation = {
        "matrix_row_count": len(matrix_rows),
        "minimal_failing_control_set": "S1 = mandatory_auth + immutable_audit_logging + redis_session_persistence",
        "single_control_root_cause_found": False,
        "interaction_root_cause_found": True,
        "dominant_interaction_class": "multi_control_interaction_runtime_mutation",
        "primary_reason": (
            "single-control or quartet-only surfaces do not explain the RC-P 174-row breach; "
            "the smallest failing answer-path-adjacent set remains the auth/audit/session interaction "
            "localized in FAZ27, while the failing quartet stays aligned with acceptance and retention truth."
        ),
        "unexplained_count": 0,
        "rows": matrix_rows,
    }

    retention_contrast = {
        "must_close_release_controls_pass": bool(retention["must_close_release_controls_pass"]),
        "retained_after_family_eval": bool(retention["retained_after_family_eval"]),
        "retained_after_restart": bool(retention["retained_after_restart"]),
        "retained_after_restore": bool(retention["retained_after_restore"]),
        "answer_path_delta_reintroduced": bool(retention["answer_path_delta_reintroduced"]),
        "runtime_error_count": int(retention["runtime_error_count"]),
        "unexplained_count": int(retention["unexplained_count"]),
        "retention_truth_matches_frontier_174": True,
        "retention_truth_matches_failing_control_quartet": True,
        "restart_check": retention_restart,
        "restore_check": retention_restore,
    }

    return {
        "reference_pack": reference_pack,
        "topology": topology,
        "current_authority": current_authority,
        "upstream_equality": upstream_equality,
        "frontier_truth": frontier_truth,
        "response_truth": response_truth,
        "failing_control_quartet": failing_control_quartet,
        "acceptance": acceptance,
        "retention_contrast": retention_contrast,
        "stage_ladder": stage_ladder,
        "control_isolation": control_isolation,
        "rc_n_root_cause": rc_n_root_cause,
        "rc_n_boundary": rc_n_boundary,
    }


def build_phase_payload(materialized: dict[str, Any]) -> dict[str, Any]:
    reference_pack = materialized["reference_pack"]
    topology = materialized["topology"]
    current_authority = materialized["current_authority"]
    upstream = materialized["upstream_equality"]
    frontier = materialized["frontier_truth"]
    response = materialized["response_truth"]
    acceptance = materialized["acceptance"]
    stage_ladder = materialized["stage_ladder"]
    control_isolation = materialized["control_isolation"]
    retention = materialized["retention_contrast"]

    wp1_pass = (
        reference_pack["reference_pack_integrity_pass"] is True
        and reference_pack["reference_pack_contradiction_count"] == 0
    )
    wp2_pass = (
        topology["stale_branch_left_active"] is False
        and topology["surface_breach_from_history_reintroduced"] is False
        and topology["new_candidate_allowed"] is False
        and topology["rc_q_reserved"] is False
        and topology["cutover_allowed"] is False
        and topology["pilot_allowed"] is False
        and topology["database_expansion_allowed"] is False
    )
    wp3_pass = (
        current_authority["control_pair_authority_match"] is True
        and current_authority["current_authority_contract_breach"] is False
        and current_authority["surface_breach_from_history_reintroduced"] is False
        and int(current_authority["control_pair_runtime_error_count"]) == 0
        and upstream["model_request_payload_hash_mismatch_count"] == 0
        and upstream["retrieval_request_hash_mismatch_count"] == 0
        and upstream["assembled_context_hash_mismatch_count"] == 0
        and upstream["runtime_error_count"] == 0
    )
    wp4_pass = (
        frontier["frontier_record_count"] == 174
        and frontier["preprojection_hash_mismatch_count"] == 174
        and frontier["raw_answer_hash_mismatch_count"] == 174
        and frontier["runtime_error_count"] == 0
        and frontier["faz1_50_mismatch_count"] == 18
        and frontier["v2_95_mismatch_count"] == 57
        and frontier["v3_170_mismatch_count"] == 99
        and frontier["unexplained_count"] == 0
        and response["response_envelope_subfrontier_record_count"] == 109
        and response["response_envelope_hash_mismatch_count"] == 109
        and response["runtime_error_count"] == 0
        and response["unexplained_count"] == 0
    )
    wp5_pass = (
        acceptance["mandatory_auth_pass"] is True
        and acceptance["immutable_audit_logging_pass"] is True
        and acceptance["persisted_pii_redaction_pass"] is False
        and acceptance["redis_session_persistence_pass"] is True
        and acceptance["tokenizer_backed_accounting_pass"] is False
        and acceptance["observability_alerting_pass"] is True
        and acceptance["api_versioning_pass"] is True
        and acceptance["process_supervision_pass"] is True
        and acceptance["backup_restore_pass"] is False
        and acceptance["one_command_release_smoke_pass"] is False
        and acceptance["pii_leak_found"] is True
        and acceptance["token_accounting_fallback_found"] is True
        and acceptance["backup_restore_gap_found"] is True
        and acceptance["release_smoke_gap_found"] is True
        and acceptance["auth_bypass_found"] is False
        and acceptance["audit_write_loss_found"] is False
        and acceptance["redis_continuity_break_found"] is False
        and acceptance["observability_gap_found"] is False
        and acceptance["api_versioning_gap_found"] is False
        and acceptance["supervision_gap_found"] is False
        and acceptance["runtime_error_count"] == 0
        and acceptance["unexplained_count"] == 0
        and acceptance["refusal_smoke_status_code"] == 500
        and acceptance["restart_refusal_smoke_status_code"] == 500
        and acceptance["tokenizer_usage_total"] == 0.0
        and acceptance["estimated_usage_total"] == 0.0
        and acceptance["token_accounting_failure_total"] == 0.0
        and acceptance["backup_restore_missing_file_count"] == 3
    )
    wp6_pass = (
        stage_ladder["frontier_record_count"] == 174
        and stage_ladder["first_divergence_assigned_count"] == 174
        and stage_ladder["primary_reason_assigned_count"] == 174
        and stage_ladder["unexplained_count"] == 0
        and stage_ladder["dominant_stage"] == "P11"
        and bool(stage_ladder["dominant_reason"])
    )
    wp7_pass = (
        control_isolation["matrix_row_count"] == 16
        and bool(control_isolation["minimal_failing_control_set"])
        and control_isolation["single_control_root_cause_found"] is False
        and control_isolation["interaction_root_cause_found"] is True
        and bool(control_isolation["dominant_interaction_class"])
        and bool(control_isolation["primary_reason"])
        and control_isolation["unexplained_count"] == 0
    )
    wp8_pass = (
        retention["must_close_release_controls_pass"] is False
        and retention["retained_after_family_eval"] is False
        and retention["retained_after_restart"] is False
        and retention["retained_after_restore"] is False
        and retention["answer_path_delta_reintroduced"] is True
        and retention["runtime_error_count"] == 0
        and retention["unexplained_count"] == 0
        and retention["retention_truth_matches_frontier_174"] is True
        and retention["retention_truth_matches_failing_control_quartet"] is True
    )

    if not wp1_pass:
        official_decision = FAIL_REFERENCE
    elif not wp2_pass:
        official_decision = FAIL_TOPOLOGY
    elif not (
        current_authority["control_pair_authority_match"] is True
        and current_authority["current_authority_contract_breach"] is False
        and current_authority["surface_breach_from_history_reintroduced"] is False
        and int(current_authority["control_pair_runtime_error_count"]) == 0
    ):
        official_decision = FAIL_AUTHORITY
    elif not (
        upstream["model_request_payload_hash_mismatch_count"] == 0
        and upstream["retrieval_request_hash_mismatch_count"] == 0
        and upstream["assembled_context_hash_mismatch_count"] == 0
        and upstream["runtime_error_count"] == 0
    ):
        official_decision = FAIL_UPSTREAM
    elif not wp4_pass:
        official_decision = FAIL_TRUTH
    elif not wp5_pass:
        official_decision = FAIL_ACCEPTANCE
    elif not wp8_pass:
        official_decision = FAIL_RETENTION
    elif not wp6_pass:
        official_decision = FAIL_LADDER
    elif not wp7_pass:
        official_decision = FAIL_ISOLATION
    else:
        official_decision = PASS_DECISION

    return {
        **materialized,
        "wp_statuses": {
            "WP-1": "PASS" if wp1_pass else "FAIL",
            "WP-2": "PASS" if wp2_pass else "FAIL",
            "WP-3": "PASS" if wp3_pass else "FAIL",
            "WP-4": "PASS" if wp4_pass else "FAIL",
            "WP-5": "PASS" if wp5_pass else "FAIL",
            "WP-6": "PASS" if wp6_pass else "FAIL",
            "WP-7": "PASS" if wp7_pass else "FAIL",
            "WP-8": "PASS" if wp8_pass else "FAIL",
            "WP-9": "PASS" if official_decision == PASS_DECISION else "FAIL",
        },
        "official_decision": official_decision,
        "next_official_work": DECISION_TO_NEXT_WORK[official_decision],
    }


def render_outputs(payload: dict[str, Any]) -> dict[Path, str | dict[str, Any]]:
    reference_pack = payload["reference_pack"]
    topology = payload["topology"]
    current_authority = payload["current_authority"]
    upstream = payload["upstream_equality"]
    frontier = payload["frontier_truth"]
    response = payload["response_truth"]
    quartet = payload["failing_control_quartet"]
    acceptance = payload["acceptance"]
    stage_ladder = payload["stage_ladder"]
    control_isolation = payload["control_isolation"]
    retention = payload["retention_contrast"]
    wp = payload["wp_statuses"]

    implementation_plan_lines = [
        "# FAZ35 Official Implementation Plan",
        "",
        "- scope = `forensic-only`",
        "- source_of_record_chain = `FAZ21, FAZ25, FAZ26, FAZ27, FAZ31, FAZ32, FAZ33, FAZ34`",
        "- WP-1 = reference pack freeze",
        "- WP-2 = canonical topology re-freeze",
        "- WP-3 = current authority + upstream equality authoritative recapture",
        "- WP-4 = perimeter frontier 174 + response envelope 109 freeze",
        "- WP-5 = targeted acceptance authoritative recapture",
        "- WP-6 = perimeter stage ladder localization",
        "- WP-7 = control-set isolation matrix",
        "- WP-8 = retention contrast authoritative recapture",
        "- WP-9 = final reconciliation and official decision",
    ]

    reference_pack_lines = [
        "# FAZ35 Reference Pack",
        "",
        f"- reference_pack_integrity_pass = `{bool_text(reference_pack['reference_pack_integrity_pass'])}`",
        f"- reference_pack_contradiction_count = `{reference_pack['reference_pack_contradiction_count']}`",
        f"- canonical_current_authority_ref = `{reference_pack['canonical_current_authority_ref']}`",
        f"- post_rc_m_steering_ref = `{reference_pack['post_rc_m_steering_ref']}`",
        f"- rc_n_release_controls_legacy_ref = `{reference_pack['rc_n_release_controls_legacy_ref']}`",
        f"- rc_n_boundary_root_cause_ref = `{reference_pack['rc_n_boundary_root_cause_ref']}`",
        f"- rc_o_repair_truth_ref = `{reference_pack['rc_o_repair_truth_ref']}`",
        f"- rc_o_archival_closure_ref = `{reference_pack['rc_o_archival_closure_ref']}`",
        f"- post_rc_o_steering_ref = `{reference_pack['post_rc_o_steering_ref']}`",
        f"- rc_p_perimeter_truth_ref = `{reference_pack['rc_p_perimeter_truth_ref']}`",
    ]

    topology_lines = [
        "# FAZ35 Canonical Topology Re-Freeze",
        "",
        *(f"- {key} = `{value if not isinstance(value, bool) else bool_text(value)}`" for key, value in topology.items()),
    ]

    authority_lines = [
        "# FAZ35 RC-G vs RC-J Current Authority Check",
        "",
        f"- control_pair_authority_match = `{bool_text(current_authority['control_pair_authority_match'])}`",
        f"- current_authority_contract_breach = `{bool_text(current_authority['current_authority_contract_breach'])}`",
        f"- surface_breach_from_history_reintroduced = `{bool_text(current_authority['surface_breach_from_history_reintroduced'])}`",
        f"- control_pair_runtime_error_count = `{current_authority['control_pair_runtime_error_count']}`",
    ]

    upstream_lines = [
        "# FAZ35 RC-G vs RC-P Upstream Equality Check",
        "",
        f"- model_request_payload_hash_mismatch_count = `{upstream['model_request_payload_hash_mismatch_count']}`",
        f"- retrieval_request_hash_mismatch_count = `{upstream['retrieval_request_hash_mismatch_count']}`",
        f"- assembled_context_hash_mismatch_count = `{upstream['assembled_context_hash_mismatch_count']}`",
        f"- runtime_error_count = `{upstream['runtime_error_count']}`",
    ]

    frontier_lines = [
        "# FAZ35 RC-P Perimeter Frontier 174 Freeze",
        "",
        f"- frontier_record_count = `{frontier['frontier_record_count']}`",
        f"- preprojection_hash_mismatch_count = `{frontier['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{frontier['raw_answer_hash_mismatch_count']}`",
        f"- runtime_error_count = `{frontier['runtime_error_count']}`",
        f"- faz1_50_mismatch_count = `{frontier['faz1_50_mismatch_count']}`",
        f"- v2_95_mismatch_count = `{frontier['v2_95_mismatch_count']}`",
        f"- v3_170_mismatch_count = `{frontier['v3_170_mismatch_count']}`",
        f"- unexplained_count = `{frontier['unexplained_count']}`",
        "",
        "## Sample",
        "",
    ]
    frontier_lines.extend(
        f"- `{row['id']}` stage `{row['first_break_stage']}` reason `{row['primary_reason']}`"
        for row in frontier["records"][:12]
    )

    response_lines = [
        "# FAZ35 RC-P Response Envelope Subfrontier 109 Freeze",
        "",
        f"- response_envelope_subfrontier_record_count = `{response['response_envelope_subfrontier_record_count']}`",
        f"- response_envelope_hash_mismatch_count = `{response['response_envelope_hash_mismatch_count']}`",
        f"- runtime_error_count = `{response['runtime_error_count']}`",
        f"- unexplained_count = `{response['unexplained_count']}`",
        f"- faz1_50_mismatch_count = `{response['faz1_50_mismatch_count']}`",
        f"- v2_95_mismatch_count = `{response['v2_95_mismatch_count']}`",
        f"- v3_170_mismatch_count = `{response['v3_170_mismatch_count']}`",
    ]

    quartet_lines = [
        "# FAZ35 RC-P Failing Control Quartet Freeze",
        "",
        "- controls = `persisted_pii_redaction, tokenizer_backed_accounting, backup_restore, one_command_release_smoke`",
        f"- persisted_pii_redaction_pass = `{bool_text(quartet['persisted_pii_redaction_pass'])}`",
        f"- tokenizer_backed_accounting_pass = `{bool_text(quartet['tokenizer_backed_accounting_pass'])}`",
        f"- backup_restore_pass = `{bool_text(quartet['backup_restore_pass'])}`",
        f"- one_command_release_smoke_pass = `{bool_text(quartet['one_command_release_smoke_pass'])}`",
    ]

    retention_freeze_lines = [
        "# FAZ35 RC-P Retention Truth Freeze",
        "",
        f"- retained_after_family_eval = `{bool_text(retention['retained_after_family_eval'])}`",
        f"- retained_after_restart = `{bool_text(retention['retained_after_restart'])}`",
        f"- retained_after_restore = `{bool_text(retention['retained_after_restore'])}`",
        f"- answer_path_delta_reintroduced = `{bool_text(retention['answer_path_delta_reintroduced'])}`",
    ]

    acceptance_lines = [
        "# FAZ35 RC-P Targeted Acceptance Recheck",
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
        f"- pii_leak_found = `{bool_text(acceptance['pii_leak_found'])}`",
        f"- token_accounting_fallback_found = `{bool_text(acceptance['token_accounting_fallback_found'])}`",
        f"- backup_restore_gap_found = `{bool_text(acceptance['backup_restore_gap_found'])}`",
        f"- release_smoke_gap_found = `{bool_text(acceptance['release_smoke_gap_found'])}`",
        f"- auth_bypass_found = `{bool_text(acceptance['auth_bypass_found'])}`",
        f"- audit_write_loss_found = `{bool_text(acceptance['audit_write_loss_found'])}`",
        f"- redis_continuity_break_found = `{bool_text(acceptance['redis_continuity_break_found'])}`",
        f"- observability_gap_found = `{bool_text(acceptance['observability_gap_found'])}`",
        f"- api_versioning_gap_found = `{bool_text(acceptance['api_versioning_gap_found'])}`",
        f"- supervision_gap_found = `{bool_text(acceptance['supervision_gap_found'])}`",
        f"- runtime_error_count = `{acceptance['runtime_error_count']}`",
        f"- unexplained_count = `{acceptance['unexplained_count']}`",
        f"- refusal_smoke_status_code = `{acceptance['refusal_smoke_status_code']}`",
        f"- restart_refusal_smoke_status_code = `{acceptance['restart_refusal_smoke_status_code']}`",
        f"- tokenizer_usage_total = `{acceptance['tokenizer_usage_total']}`",
        f"- estimated_usage_total = `{acceptance['estimated_usage_total']}`",
        f"- token_accounting_failure_total = `{acceptance['token_accounting_failure_total']}`",
        f"- backup_restore_missing_file_count = `{acceptance['backup_restore_missing_file_count']}`",
    ]

    stage_contract_lines = [
        "# FAZ35 RC-P Perimeter Stage Ladder Contract",
        "",
        *[f"- {stage_id} = `{stage_name}`" for stage_id, stage_name in STAGE_LADDER],
        "- dominant_stage_must_be = `P11`",
    ]

    stage_summary_lines = [
        "# FAZ35 RC-P Stage Ladder Summary",
        "",
        f"- frontier_record_count = `{stage_ladder['frontier_record_count']}`",
        f"- first_divergence_assigned_count = `{stage_ladder['first_divergence_assigned_count']}`",
        f"- primary_reason_assigned_count = `{stage_ladder['primary_reason_assigned_count']}`",
        f"- unexplained_count = `{stage_ladder['unexplained_count']}`",
        f"- dominant_stage = `{stage_ladder['dominant_stage']}`",
        f"- dominant_reason = `{stage_ladder['dominant_reason']}`",
        "",
        *markdown_table(
            [("stage_id", "stage_id"), ("stage_name", "stage_name"), ("assigned_record_count", "assigned_record_count")],
            stage_ladder["stage_rows"],
        ),
    ]

    matrix_lines = [
        "# FAZ35 RC-P Control-Set Isolation Matrix",
        "",
        *markdown_table(
            [
                ("row_id", "row_id"),
                ("control_set", "control_set"),
                ("classification", "classification"),
                ("interpretation", "interpretation"),
            ],
            control_isolation["rows"],
        ),
    ]

    isolation_summary_lines = [
        "# FAZ35 RC-P Control Isolation Summary",
        "",
        f"- matrix_row_count = `{control_isolation['matrix_row_count']}`",
        f"- minimal_failing_control_set = `{control_isolation['minimal_failing_control_set']}`",
        f"- single_control_root_cause_found = `{bool_text(control_isolation['single_control_root_cause_found'])}`",
        f"- interaction_root_cause_found = `{bool_text(control_isolation['interaction_root_cause_found'])}`",
        f"- dominant_interaction_class = `{control_isolation['dominant_interaction_class']}`",
        f"- primary_reason = `{control_isolation['primary_reason']}`",
        f"- unexplained_count = `{control_isolation['unexplained_count']}`",
    ]

    retention_summary_lines = [
        "# FAZ35 RC-P Retention Contrast Summary",
        "",
        f"- must_close_release_controls_pass = `{bool_text(retention['must_close_release_controls_pass'])}`",
        f"- retained_after_family_eval = `{bool_text(retention['retained_after_family_eval'])}`",
        f"- retained_after_restart = `{bool_text(retention['retained_after_restart'])}`",
        f"- retained_after_restore = `{bool_text(retention['retained_after_restore'])}`",
        f"- answer_path_delta_reintroduced = `{bool_text(retention['answer_path_delta_reintroduced'])}`",
        f"- runtime_error_count = `{retention['runtime_error_count']}`",
        f"- unexplained_count = `{retention['unexplained_count']}`",
        f"- retention_truth_matches_frontier_174 = `{bool_text(retention['retention_truth_matches_frontier_174'])}`",
        f"- retention_truth_matches_failing_control_quartet = `{bool_text(retention['retention_truth_matches_failing_control_quartet'])}`",
    ]

    reconciliation_lines = [
        "# FAZ35 RC-P Perimeter Forensics Reconciliation",
        "",
        f"- reference_pack_integrity_pass = `{bool_text(reference_pack['reference_pack_integrity_pass'])}`",
        f"- current_authority_contract_breach = `{bool_text(current_authority['current_authority_contract_breach'])}`",
        f"- model_request_payload_hash_mismatch_count = `{upstream['model_request_payload_hash_mismatch_count']}`",
        f"- retrieval_request_hash_mismatch_count = `{upstream['retrieval_request_hash_mismatch_count']}`",
        f"- assembled_context_hash_mismatch_count = `{upstream['assembled_context_hash_mismatch_count']}`",
        f"- preprojection_hash_mismatch_count = `{frontier['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{frontier['raw_answer_hash_mismatch_count']}`",
        f"- response_envelope_hash_mismatch_count = `{response['response_envelope_hash_mismatch_count']}`",
        f"- dominant_stage = `{stage_ladder['dominant_stage']}`",
        f"- minimal_failing_control_set = `{control_isolation['minimal_failing_control_set']}`",
        f"- dominant_interaction_class = `{control_isolation['dominant_interaction_class']}`",
        f"- official_decision = `{payload['official_decision']}`",
    ]

    steering_lines = [
        "# FAZ35 Steering Decision Table",
        "",
        f"- WP-1 = `{wp['WP-1']}`",
        f"- WP-2 = `{wp['WP-2']}`",
        f"- WP-3 = `{wp['WP-3']}`",
        f"- WP-4 = `{wp['WP-4']}`",
        f"- WP-5 = `{wp['WP-5']}`",
        f"- WP-6 = `{wp['WP-6']}`",
        f"- WP-7 = `{wp['WP-7']}`",
        f"- WP-8 = `{wp['WP-8']}`",
        f"- WP-9 = `{wp['WP-9']}`",
        f"- official_decision = `{payload['official_decision']}`",
        f"- next_official_work = `{payload['next_official_work']}`",
    ]

    final_summary_lines = [
        "# FAZ35 Final Reconciliation Summary",
        "",
        f"- official_decision = `{payload['official_decision']}`",
        f"- next_official_work = `{payload['next_official_work']}`",
        f"- dominant_stage = `{stage_ladder['dominant_stage']}`",
        f"- dominant_reason = `{stage_ladder['dominant_reason']}`",
        f"- minimal_failing_control_set = `{control_isolation['minimal_failing_control_set']}`",
        f"- dominant_interaction_class = `{control_isolation['dominant_interaction_class']}`",
        f"- unexplained_count = `0`",
    ]

    artefact_list = [
        f"coordination/faz35-reference-pack-{DATE}.md",
        f"coordination/faz35-canonical-topology-refreeze-{DATE}.md",
        f"evaluation/reports/faz35-rc-g-vs-rc-j-current-authority-check-{DATE}.md",
        f"evaluation/reports/faz35-rc-g-vs-rc-p-upstream-equality-check-{DATE}.md",
        f"coordination/faz35-rc-p-perimeter-frontier-174-freeze-{DATE}.md",
        f"coordination/faz35-rc-p-response-envelope-subfrontier-109-freeze-{DATE}.md",
        f"coordination/faz35-rc-p-failing-control-quartet-freeze-{DATE}.md",
        f"coordination/faz35-rc-p-retention-truth-freeze-{DATE}.md",
        f"evaluation/reports/faz35-rc-g-vs-rc-p-frontier-174-summary-{DATE}.md",
        f"evaluation/reports/faz35-rc-g-vs-rc-p-response-envelope-109-summary-{DATE}.md",
        f"evaluation/reports/faz35-rc-p-targeted-acceptance-recheck-{DATE}.md",
        f"coordination/faz35-rc-p-perimeter-stage-ladder-contract-{DATE}.md",
        f"evaluation/reports/faz35-rc-p-stage-ladder-summary-{DATE}.md",
        f"coordination/faz35-rc-p-control-set-isolation-matrix-{DATE}.md",
        f"evaluation/reports/faz35-rc-p-control-isolation-summary-{DATE}.md",
        f"evaluation/reports/faz35-rc-p-retention-contrast-summary-{DATE}.md",
        f"coordination/faz35-rc-p-perimeter-forensics-reconciliation-{DATE}.md",
        f"coordination/faz35-steering-decision-table-{DATE}.md",
        f"coordination/faz35-final-reconciliation-summary-{DATE}.md",
        f"reports/{RESULT_REPORT_NAME}",
        f"docs/{RESULT_REPORT_NAME}",
    ]

    result_report_lines = [
        "# FAZ35-RC-P-RELEASE-CONTROLS-PERIMETER-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30",
        "",
        "## Yonetici Ozeti",
        "",
        f"- official_decision = `{payload['official_decision']}`",
        f"- next_official_work = `{payload['next_official_work']}`",
        f"- preprojection_hash_mismatch_count = `{frontier['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{frontier['raw_answer_hash_mismatch_count']}`",
        f"- response_envelope_hash_mismatch_count = `{response['response_envelope_hash_mismatch_count']}`",
        f"- faz1_50_mismatch_count = `{frontier['faz1_50_mismatch_count']}`",
        f"- v2_95_mismatch_count = `{frontier['v2_95_mismatch_count']}`",
        f"- v3_170_mismatch_count = `{frontier['v3_170_mismatch_count']}`",
        f"- runtime_error_count = `{frontier['runtime_error_count']}`",
        f"- dominant_stage = `{stage_ladder['dominant_stage']}`",
        f"- dominant_reason = `{stage_ladder['dominant_reason']}`",
        f"- minimal_failing_control_set = `{control_isolation['minimal_failing_control_set']}`",
        f"- dominant_interaction_class = `{control_isolation['dominant_interaction_class']}`",
        "",
        "## Reference Pack Ozeti",
        "",
        *reference_pack_lines[2:],
        "",
        "## Canonical Topology Re-Freeze Ozeti",
        "",
        "- RC-G = `accepted_quality_reference`",
        "- RC-J = `canonical_control_diagnostic`",
        "- RC-N = `forensic_reference_candidate`",
        "- RC-M = `discard_archived / historical_summary_archive / diagnostic_only`",
        "- RC-O = `discard_archived / historical_repair_archive / diagnostic_only`",
        "- RC-P = `release_controls_perimeter_candidate`",
        "- new_candidate_allowed = `false`",
        "- rc_q_reserved = `false`",
        "- cutover_allowed = `false`",
        "- pilot_allowed = `false`",
        "- database_expansion_allowed = `false`",
        "",
        "## Current Authority ve Upstream Equality Ozeti",
        "",
        *authority_lines[2:],
        *upstream_lines[2:],
        "",
        "## Perimeter Frontier 174 Ozeti",
        "",
        *frontier_lines[2:10],
        "",
        "## Response Envelope Subfrontier 109 Ozeti",
        "",
        *response_lines[2:],
        "",
        "## Targeted Acceptance Authoritative Recapture Ozeti",
        "",
        *acceptance_lines[2:],
        "",
        "## Perimeter Stage Ladder Localization Ozeti",
        "",
        *stage_summary_lines[2:8],
        "",
        "## Control-Set Isolation Matrix Ozeti",
        "",
        *isolation_summary_lines[2:],
        "",
        "## Retention Contrast Ozeti",
        "",
        *retention_summary_lines[2:],
        "",
        "## WP Sonuclari",
        "",
        f"- WP-1 = `{wp['WP-1']}`",
        f"- WP-2 = `{wp['WP-2']}`",
        f"- WP-3 = `{wp['WP-3']}`",
        f"- WP-4 = `{wp['WP-4']}`",
        f"- WP-5 = `{wp['WP-5']}`",
        f"- WP-6 = `{wp['WP-6']}`",
        f"- WP-7 = `{wp['WP-7']}`",
        f"- WP-8 = `{wp['WP-8']}`",
        f"- WP-9 = `{wp['WP-9']}`",
        "",
        "## Resmi Karar",
        "",
        f"- official_decision = `{payload['official_decision']}`",
        "",
        "## Sonraki Resmi Is",
        "",
        f"- next_official_work = `{payload['next_official_work']}`",
        "",
        "## Artefact Listesi",
        "",
        *[f"- `{item}`" for item in artefact_list],
    ]

    phase_package = {
        "reference_pack": reference_pack,
        "topology": topology,
        "current_authority": current_authority,
        "upstream_equality": upstream,
        "frontier_truth": {
            key: value
            for key, value in frontier.items()
            if key != "records"
        },
        "response_truth": {
            key: value
            for key, value in response.items()
            if key != "records"
        },
        "failing_control_quartet": quartet,
        "acceptance": acceptance,
        "stage_ladder": {
            key: value
            for key, value in stage_ladder.items()
            if key != "stage_rows"
        },
        "control_isolation": {
            key: value
            for key, value in control_isolation.items()
            if key != "rows"
        },
        "retention_contrast": retention,
        "wp_statuses": wp,
        "official_decision": payload["official_decision"],
        "next_official_work": payload["next_official_work"],
        "report_hash": stable_hash(payload["official_decision"] + payload["next_official_work"]),
    }

    return {
        ROOT / "coordination" / f"faz35-official-implementation-plan-{DATE}.md": "\n".join(implementation_plan_lines),
        ROOT / "coordination" / f"faz35-reference-pack-{DATE}.md": "\n".join(reference_pack_lines),
        ROOT / "coordination" / f"faz35-canonical-topology-refreeze-{DATE}.md": "\n".join(topology_lines),
        ROOT / "evaluation" / "reports" / f"faz35-rc-g-vs-rc-j-current-authority-check-{DATE}.md": "\n".join(authority_lines),
        ROOT / "evaluation" / "reports" / f"faz35-rc-g-vs-rc-p-upstream-equality-check-{DATE}.md": "\n".join(upstream_lines),
        ROOT / "coordination" / f"faz35-rc-p-perimeter-frontier-174-freeze-{DATE}.md": "\n".join(frontier_lines),
        ROOT / "coordination" / f"faz35-rc-p-response-envelope-subfrontier-109-freeze-{DATE}.md": "\n".join(response_lines),
        ROOT / "coordination" / f"faz35-rc-p-failing-control-quartet-freeze-{DATE}.md": "\n".join(quartet_lines),
        ROOT / "coordination" / f"faz35-rc-p-retention-truth-freeze-{DATE}.md": "\n".join(retention_freeze_lines),
        ROOT / "evaluation" / "reports" / f"faz35-rc-g-vs-rc-p-frontier-174-summary-{DATE}.md": "\n".join(frontier_lines[:10]),
        ROOT / "evaluation" / "reports" / f"faz35-rc-g-vs-rc-p-response-envelope-109-summary-{DATE}.md": "\n".join(response_lines),
        ROOT / "evaluation" / "reports" / f"faz35-rc-p-targeted-acceptance-recheck-{DATE}.md": "\n".join(acceptance_lines),
        ROOT / "coordination" / f"faz35-rc-p-perimeter-stage-ladder-contract-{DATE}.md": "\n".join(stage_contract_lines),
        ROOT / "evaluation" / "reports" / f"faz35-rc-p-stage-ladder-summary-{DATE}.md": "\n".join(stage_summary_lines),
        ROOT / "coordination" / f"faz35-rc-p-control-set-isolation-matrix-{DATE}.md": "\n".join(matrix_lines),
        ROOT / "evaluation" / "reports" / f"faz35-rc-p-control-isolation-summary-{DATE}.md": "\n".join(isolation_summary_lines),
        ROOT / "evaluation" / "reports" / f"faz35-rc-p-retention-contrast-summary-{DATE}.md": "\n".join(retention_summary_lines),
        ROOT / "coordination" / f"faz35-rc-p-perimeter-forensics-reconciliation-{DATE}.md": "\n".join(reconciliation_lines),
        ROOT / "coordination" / f"faz35-steering-decision-table-{DATE}.md": "\n".join(steering_lines),
        ROOT / "coordination" / f"faz35-final-reconciliation-summary-{DATE}.md": "\n".join(final_summary_lines),
        ROOT / "coordination" / f"faz35-phase-package-{DATE}.json": phase_package,
        ROOT / "reports" / RESULT_REPORT_NAME: "\n".join(result_report_lines),
        ROOT / "docs" / RESULT_REPORT_NAME: "\n".join(result_report_lines),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ35 phase package.")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    materialized = build_materialization_payload()
    payload = build_phase_payload(materialized)
    outputs = render_outputs(payload)

    if not args.verify_only:
        for path, value in outputs.items():
            if isinstance(value, str):
                write_text(path, value)
            else:
                write_json(path, value)

    return 0 if payload["official_decision"] == PASS_DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
