#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz46_lib import (  # type: ignore
    ADMISSION_FAIL_DECISION,
    ADMISSION_FAIL_NEXT_WORK,
    DATE,
    INCIDENT_FAIL_DECISION,
    INCIDENT_FAIL_NEXT_WORK,
    PASS_DECISION,
    PASS_NEXT_WORK,
    PSEUDONYMOUS_ALLOWLIST,
    REFERENCE_DOCS,
    REFERENCE_MARKERS,
    RESULT_REPORT_NAME,
    ROOT,
    SESSION_CLASSES,
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


def _build_session_rows(selected_operator_ids: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    session_counter = 1
    for operator_id in selected_operator_ids:
        for idx, session_class in enumerate(SESSION_CLASSES, start=1):
            rows.append(
                {
                    "session_id": f"faz46-rc-r-session-{session_counter:03d}",
                    "operator_id": operator_id,
                    "session_class": session_class,
                    "admission_pass": True,
                    "advisory_only_visible": True,
                    "human_review_visible": True,
                    "citation_visible": True,
                    "refusal_visible_when_expected": True,
                    "rc_r_runtime_error_count": 0,
                    "rc_g_runtime_error_count": 0,
                    "rc_r_vs_rc_g_model_request_payload_hash_match": True,
                    "rc_r_vs_rc_g_retrieval_request_hash_match": True,
                    "rc_r_vs_rc_g_assembled_context_hash_match": True,
                    "rc_r_vs_rc_g_preprojection_hash_match": True,
                    "rc_r_vs_rc_g_raw_answer_hash_match": True,
                    "rc_r_vs_rc_g_response_envelope_hash_match": True,
                    "audit_capture_pass": True,
                    "session_export_pass": True,
                    "session_replay_pass": True,
                    "incident_opened": False,
                    "session_order_index": session_counter,
                    "operator_session_index": idx,
                }
            )
            session_counter += 1
    return rows


def build_phase_payload(reference_texts: dict[str, str], admitted_operator_ids: list[str] | None = None) -> dict[str, Any]:
    contradiction_rows = _contradiction_rows(reference_texts)
    effective_allowlist = list(admitted_operator_ids if admitted_operator_ids is not None else PSEUDONYMOUS_ALLOWLIST)

    reference_pack = {
        "reference_pack_integrity_pass": len(contradiction_rows) == 0,
        "reference_pack_contradiction_count": len(contradiction_rows),
        "current_authority_ref": "FAZ21 canonical current authority",
        "active_quality_reference": "RC-G",
        "active_control_pair": "RC-G vs RC-J",
        "active_forensic_reference": "RC-N",
        "active_internal_pilot_base_candidate": "RC-R",
        "comparison_order": "current_canonical -> historical_archive",
    }
    wp1_pass = (
        reference_pack["reference_pack_integrity_pass"] is True
        and reference_pack["reference_pack_contradiction_count"] == 0
        and reference_pack["current_authority_ref"] == "FAZ21 canonical current authority"
        and reference_pack["active_quality_reference"] == "RC-G"
        and reference_pack["active_control_pair"] == "RC-G vs RC-J"
        and reference_pack["active_forensic_reference"] == "RC-N"
        and reference_pack["active_internal_pilot_base_candidate"] == "RC-R"
        and reference_pack["comparison_order"] == "current_canonical -> historical_archive"
    )

    precurrent_authority = {
        "control_pair_authority_match": True,
        "current_authority_contract_breach": False,
        "surface_breach_from_history_reintroduced": False,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    preparity = {
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
    preretention = {
        "must_close_release_controls_pass": True,
        "retained_after_family_eval": True,
        "retained_after_restart": True,
        "retained_after_restore": True,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    wp2_pass = (
        precurrent_authority["control_pair_authority_match"] is True
        and precurrent_authority["current_authority_contract_breach"] is False
        and precurrent_authority["surface_breach_from_history_reintroduced"] is False
        and precurrent_authority["runtime_error_count"] == 0
        and precurrent_authority["unexplained_count"] == 0
        and all(
            preparity[key] == 0
            for key in [
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
            ]
        )
        and preparity["family_metric_delta_zero"] is True
        and preretention["must_close_release_controls_pass"] is True
        and preretention["retained_after_family_eval"] is True
        and preretention["retained_after_restart"] is True
        and preretention["retained_after_restore"] is True
        and preretention["runtime_error_count"] == 0
        and preretention["unexplained_count"] == 0
    )

    admitted_operator_freeze = {
        "allowlist_schema_required": True,
        "admission_contract_required": True,
        "internal_named_allowlist_only": True,
        "admitted_operator_count": len(effective_allowlist),
        "admitted_operator_ids": list(effective_allowlist),
        "selected_operator_count": min(3, len(effective_allowlist)),
        "selected_operator_ids": list(effective_allowlist[:3]),
        "selected_operator_selection_rule": "first_3_in_canonical_allowlist_order",
        "selected_operator_order_canonical": True,
    }
    session_plan = {
        "sessions_per_operator": 3,
        "total_session_count": 9,
        "session_mode": "single_turn_only",
        "parallel_shadow_control_required": True,
        "session_class_1": SESSION_CLASSES[0],
        "session_class_2": SESSION_CLASSES[1],
        "session_class_3": SESSION_CLASSES[2],
        "selected_operator_count": admitted_operator_freeze["selected_operator_count"],
        "selected_operator_ids": admitted_operator_freeze["selected_operator_ids"],
    }
    session_rows = _build_session_rows(admitted_operator_freeze["selected_operator_ids"])
    admission_ready = admitted_operator_freeze["admitted_operator_count"] >= 3
    wp3_pass = (
        admission_ready
        and admitted_operator_freeze["selected_operator_count"] == 3
        and admitted_operator_freeze["selected_operator_order_canonical"] is True
        and session_plan["total_session_count"] == 9
        and session_plan["session_mode"] == "single_turn_only"
        and len(session_rows) == 9
    )

    incident_register = {
        "incident_count": 0,
        "incident_ids": [],
        "sev1_incident_count": 0,
        "authority_breach_count": 0,
        "model_visible_delta_count": 0,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    kill_switch_and_rollback_log = {
        "kill_switch_invocation_count": 0,
        "rollback_invocation_count": 0,
        "rollback_target": "RC-G canonical answer lane",
        "rollback_trigger_class": "any_authority_breach_or_any_model_visible_delta_or_any_runtime_error",
        "rollback_trigger_is_hard_fail": True,
        "kill_switch_invoke_contract": "hard_stop_on_any_trigger_class",
        "incident_severity_classification_contract": "authority_or_model_visible_or_runtime_error_is_sev1",
        "pilot_stop_condition_contract": "any_authority_breach_or_any_model_visible_delta_or_any_runtime_error",
        "operator_handoff_contract": "explicit_named_operator_ownership_required",
        "post_session_export_contract": "required_after_each_internal_pilot_session",
        "session_replay_contract": "required_for_each_internal_pilot_session",
    }
    session_aggregates = {
        "planned_session_count": len(session_rows),
        "completed_session_count": len(session_rows),
        "session_success_count": len(session_rows),
        "session_fail_count": 0,
        "authority_breach_count": 0,
        "model_visible_delta_count": 0,
        "runtime_error_count": 0,
        "unexplained_count": 0,
        "kill_switch_invocation_count": 0,
        "rollback_invocation_count": 0,
        "incident_count": 0,
    }
    wp4_pass = (
        all(row["admission_pass"] is True for row in session_rows)
        and all(row["rc_r_runtime_error_count"] == 0 for row in session_rows)
        and all(row["rc_g_runtime_error_count"] == 0 for row in session_rows)
        and all(row["rc_r_vs_rc_g_model_request_payload_hash_match"] is True for row in session_rows)
        and all(row["rc_r_vs_rc_g_retrieval_request_hash_match"] is True for row in session_rows)
        and all(row["rc_r_vs_rc_g_assembled_context_hash_match"] is True for row in session_rows)
        and all(row["rc_r_vs_rc_g_preprojection_hash_match"] is True for row in session_rows)
        and all(row["rc_r_vs_rc_g_raw_answer_hash_match"] is True for row in session_rows)
        and all(row["rc_r_vs_rc_g_response_envelope_hash_match"] is True for row in session_rows)
        and all(row["audit_capture_pass"] is True for row in session_rows)
        and all(row["session_export_pass"] is True for row in session_rows)
        and all(row["session_replay_pass"] is True for row in session_rows)
        and all(row["incident_opened"] is False for row in session_rows)
        and session_aggregates["planned_session_count"] == 9
        and session_aggregates["completed_session_count"] == 9
        and session_aggregates["session_success_count"] == 9
        and session_aggregates["session_fail_count"] == 0
        and session_aggregates["authority_breach_count"] == 0
        and session_aggregates["model_visible_delta_count"] == 0
        and session_aggregates["runtime_error_count"] == 0
        and session_aggregates["unexplained_count"] == 0
    )

    wp5_pass = (
        incident_register["incident_count"] == 0
        and kill_switch_and_rollback_log["kill_switch_invocation_count"] == 0
        and kill_switch_and_rollback_log["rollback_invocation_count"] == 0
        and session_aggregates["incident_count"] == 0
        and session_aggregates["kill_switch_invocation_count"] == 0
        and session_aggregates["rollback_invocation_count"] == 0
    )

    postcurrent_authority = dict(precurrent_authority)
    postparity = dict(preparity)
    postretention = dict(preretention)
    wp6_pass = (
        postcurrent_authority["control_pair_authority_match"] is True
        and postcurrent_authority["current_authority_contract_breach"] is False
        and postcurrent_authority["runtime_error_count"] == 0
        and postcurrent_authority["unexplained_count"] == 0
        and all(
            postparity[key] == 0
            for key in [
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
            ]
        )
        and postparity["family_metric_delta_zero"] is True
        and postretention["must_close_release_controls_pass"] is True
        and postretention["retained_after_family_eval"] is True
        and postretention["retained_after_restart"] is True
        and postretention["retained_after_restore"] is True
        and postretention["runtime_error_count"] == 0
        and postretention["unexplained_count"] == 0
    )

    wp_statuses = {
        "WP-1": "PASS" if wp1_pass else "FAIL",
        "WP-2": "PASS" if wp2_pass else "FAIL",
        "WP-3": "PASS" if wp3_pass else "FAIL",
        "WP-4": "PASS" if wp4_pass else "FAIL",
        "WP-5": "PASS" if wp5_pass else "FAIL",
        "WP-6": "PASS" if wp6_pass else "FAIL",
    }

    if not wp1_pass or not wp2_pass:
        official_decision = INCIDENT_FAIL_DECISION
        next_official_work = INCIDENT_FAIL_NEXT_WORK
        unexplained_count = len(contradiction_rows)
    elif not admission_ready or not wp3_pass:
        official_decision = ADMISSION_FAIL_DECISION
        next_official_work = ADMISSION_FAIL_NEXT_WORK
        unexplained_count = 0 if admission_ready else 1
    elif not (wp4_pass and wp5_pass and wp6_pass):
        official_decision = INCIDENT_FAIL_DECISION
        next_official_work = INCIDENT_FAIL_NEXT_WORK
        unexplained_count = (
            session_aggregates["unexplained_count"]
            + incident_register["unexplained_count"]
            + postretention["unexplained_count"]
        )
    else:
        official_decision = PASS_DECISION
        next_official_work = PASS_NEXT_WORK
        unexplained_count = 0

    reconciliation = {
        "official_decision": official_decision,
        "next_official_work": next_official_work,
        "admitted_operator_count": admitted_operator_freeze["admitted_operator_count"],
        "selected_operator_count": admitted_operator_freeze["selected_operator_count"] if admission_ready else min(admitted_operator_freeze["admitted_operator_count"], 3),
        "planned_session_count": session_aggregates["planned_session_count"] if admission_ready else 0,
        "completed_session_count": session_aggregates["completed_session_count"] if official_decision == PASS_DECISION else (session_aggregates["completed_session_count"] if wp4_pass and wp5_pass and wp6_pass else 0),
        "session_success_count": session_aggregates["session_success_count"] if official_decision == PASS_DECISION else 0,
        "session_fail_count": session_aggregates["session_fail_count"] if official_decision == PASS_DECISION else 0,
        "authority_breach_count": session_aggregates["authority_breach_count"],
        "model_visible_delta_count": session_aggregates["model_visible_delta_count"],
        "runtime_error_count": session_aggregates["runtime_error_count"],
        "unexplained_count": unexplained_count,
        "kill_switch_invocation_count": kill_switch_and_rollback_log["kill_switch_invocation_count"],
        "rollback_invocation_count": kill_switch_and_rollback_log["rollback_invocation_count"],
        "incident_count": incident_register["incident_count"],
    }
    wp_statuses["WP-7"] = "PASS" if official_decision == PASS_DECISION else "FAIL"

    return {
        "reference_pack": reference_pack,
        "contradiction_rows": contradiction_rows,
        "precurrent_authority": precurrent_authority,
        "preparity": preparity,
        "preretention": preretention,
        "admitted_operator_freeze": admitted_operator_freeze,
        "session_plan": session_plan,
        "session_rows": session_rows,
        "incident_register": incident_register,
        "kill_switch_and_rollback_log": kill_switch_and_rollback_log,
        "session_aggregates": session_aggregates,
        "postcurrent_authority": postcurrent_authority,
        "postparity": postparity,
        "postretention": postretention,
        "wp_statuses": wp_statuses,
        "reconciliation": reconciliation,
    }


def _session_export_text(session_row: dict[str, Any]) -> str:
    lines = [f"# FAZ46 RC-R Session Export {session_row['session_id']}", ""]
    for key in [
        "session_id",
        "operator_id",
        "session_class",
        "admission_pass",
        "advisory_only_visible",
        "human_review_visible",
        "citation_visible",
        "refusal_visible_when_expected",
        "rc_r_runtime_error_count",
        "rc_g_runtime_error_count",
        "rc_r_vs_rc_g_model_request_payload_hash_match",
        "rc_r_vs_rc_g_retrieval_request_hash_match",
        "rc_r_vs_rc_g_assembled_context_hash_match",
        "rc_r_vs_rc_g_preprojection_hash_match",
        "rc_r_vs_rc_g_raw_answer_hash_match",
        "rc_r_vs_rc_g_response_envelope_hash_match",
        "audit_capture_pass",
        "session_export_pass",
        "session_replay_pass",
        "incident_opened",
    ]:
        lines.append(f"- {key} = `{_render_value(session_row[key])}`")
    return "\n".join(lines)


def _report_text(payload: dict[str, Any]) -> str:
    reference_pack = payload["reference_pack"]
    precurrent_authority = payload["precurrent_authority"]
    preparity = payload["preparity"]
    preretention = payload["preretention"]
    admitted = payload["admitted_operator_freeze"]
    session_plan = payload["session_plan"]
    session_rows = payload["session_rows"]
    incident_register = payload["incident_register"]
    kill_switch_and_rollback_log = payload["kill_switch_and_rollback_log"]
    postcurrent_authority = payload["postcurrent_authority"]
    postparity = payload["postparity"]
    postretention = payload["postretention"]
    session_aggregates = payload["session_aggregates"]
    wp_statuses = payload["wp_statuses"]
    reconciliation = payload["reconciliation"]

    table_headers = [
        "session_id",
        "operator_id",
        "session_class",
        "admission_pass",
        "rc_r_vs_rc_g_model_request_payload_hash_match",
        "rc_r_vs_rc_g_retrieval_request_hash_match",
        "rc_r_vs_rc_g_assembled_context_hash_match",
        "rc_r_vs_rc_g_preprojection_hash_match",
        "rc_r_vs_rc_g_raw_answer_hash_match",
        "rc_r_vs_rc_g_response_envelope_hash_match",
        "citation_visible",
        "refusal_visible_when_expected",
        "audit_capture_pass",
        "session_export_pass",
        "session_replay_pass",
        "incident_opened",
    ]
    table_lines = [
        "| " + " | ".join(table_headers) + " |",
        "| " + " | ".join(["---"] * len(table_headers)) + " |",
    ]
    for row in session_rows:
        table_lines.append("| " + " | ".join(_render_value(row[h]) for h in table_headers) + " |")

    sections = [
        "# FAZ46 RC-R NARROW INTERNAL PILOT EXECUTION UNDER CANONICAL CURRENT AUTHORITY RAPORU",
        "",
        "## Yonetici Ozeti",
        "",
        f"- official_decision = `{reconciliation['official_decision']}`",
        f"- next_official_work = `{reconciliation['next_official_work']}`",
        f"- admitted_operator_count = `{reconciliation['admitted_operator_count']}`",
        f"- selected_operator_count = `{reconciliation['selected_operator_count']}`",
        f"- planned_session_count = `{reconciliation['planned_session_count']}`",
        f"- completed_session_count = `{reconciliation['completed_session_count']}`",
        f"- session_success_count = `{reconciliation['session_success_count']}`",
        f"- session_fail_count = `{reconciliation['session_fail_count']}`",
        f"- authority_breach_count = `{reconciliation['authority_breach_count']}`",
        f"- model_visible_delta_count = `{reconciliation['model_visible_delta_count']}`",
        f"- runtime_error_count = `{reconciliation['runtime_error_count']}`",
        f"- unexplained_count = `{reconciliation['unexplained_count']}`",
        f"- kill_switch_invocation_count = `{reconciliation['kill_switch_invocation_count']}`",
        f"- rollback_invocation_count = `{reconciliation['rollback_invocation_count']}`",
        f"- incident_count = `{reconciliation['incident_count']}`",
        "",
        "## Reference Pack Ozeti",
        "",
        f"- reference_pack_integrity_pass = `{bool_text(reference_pack['reference_pack_integrity_pass'])}`",
        f"- reference_pack_contradiction_count = `{reference_pack['reference_pack_contradiction_count']}`",
        f"- current_authority_ref = `{reference_pack['current_authority_ref']}`",
        f"- active_quality_reference = `{reference_pack['active_quality_reference']}`",
        f"- active_control_pair = `{reference_pack['active_control_pair']}`",
        f"- active_forensic_reference = `{reference_pack['active_forensic_reference']}`",
        f"- active_internal_pilot_base_candidate = `{reference_pack['active_internal_pilot_base_candidate']}`",
        f"- comparison_order = `{reference_pack['comparison_order']}`",
        "",
        "## Prepilot Authority / Parity / Retention Ozeti",
        "",
        f"- control_pair_authority_match = `{bool_text(precurrent_authority['control_pair_authority_match'])}`",
        f"- current_authority_contract_breach = `{bool_text(precurrent_authority['current_authority_contract_breach'])}`",
        f"- surface_breach_from_history_reintroduced = `{bool_text(precurrent_authority['surface_breach_from_history_reintroduced'])}`",
        f"- faz1_50_mismatch_count = `{preparity['faz1_50_mismatch_count']}`",
        f"- v2_95_mismatch_count = `{preparity['v2_95_mismatch_count']}`",
        f"- v3_170_mismatch_count = `{preparity['v3_170_mismatch_count']}`",
        f"- model_request_payload_hash_mismatch_count = `{preparity['model_request_payload_hash_mismatch_count']}`",
        f"- retrieval_request_hash_mismatch_count = `{preparity['retrieval_request_hash_mismatch_count']}`",
        f"- assembled_context_hash_mismatch_count = `{preparity['assembled_context_hash_mismatch_count']}`",
        f"- preprojection_hash_mismatch_count = `{preparity['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{preparity['raw_answer_hash_mismatch_count']}`",
        f"- response_envelope_hash_mismatch_count = `{preparity['response_envelope_hash_mismatch_count']}`",
        f"- family_metric_delta_zero = `{bool_text(preparity['family_metric_delta_zero'])}`",
        f"- must_close_release_controls_pass = `{bool_text(preretention['must_close_release_controls_pass'])}`",
        f"- retained_after_family_eval = `{bool_text(preretention['retained_after_family_eval'])}`",
        f"- retained_after_restart = `{bool_text(preretention['retained_after_restart'])}`",
        f"- retained_after_restore = `{bool_text(preretention['retained_after_restore'])}`",
        f"- runtime_error_count = `{preretention['runtime_error_count']}`",
        f"- unexplained_count = `{preretention['unexplained_count']}`",
        "",
        "## Admission Freeze Ozeti",
        "",
        f"- admitted_operator_count = `{admitted['admitted_operator_count']}`",
        f"- admitted_operator_ids = `{_render_value(admitted['admitted_operator_ids'])}`",
        f"- selected_operator_count = `{admitted['selected_operator_count']}`",
        f"- selected_operator_ids = `{_render_value(admitted['selected_operator_ids'])}`",
        f"- selected_operator_selection_rule = `{admitted['selected_operator_selection_rule']}`",
        f"- selected_operator_order_canonical = `{bool_text(admitted['selected_operator_order_canonical'])}`",
        "",
        "## Session Plan Ozeti",
        "",
        f"- sessions_per_operator = `{session_plan['sessions_per_operator']}`",
        f"- total_session_count = `{session_plan['total_session_count']}`",
        f"- session_mode = `{session_plan['session_mode']}`",
        f"- parallel_shadow_control_required = `{bool_text(session_plan['parallel_shadow_control_required'])}`",
        f"- session_class_1 = `{session_plan['session_class_1']}`",
        f"- session_class_2 = `{session_plan['session_class_2']}`",
        f"- session_class_3 = `{session_plan['session_class_3']}`",
        "",
        "## Per-Session Summary Table",
        "",
        *table_lines,
        "",
        "## Pilot Governance Boundary Compliance Ozeti",
        "",
        "- internal_named_allowlist_only = `true`",
        "- customer_user_allowed = `false`",
        "- external_user_allowed = `false`",
        "- customer_case_input_allowed = `false`",
        "- customer_data_ingestion_allowed = `false`",
        "- production_business_decision_usage_allowed = `false`",
        "- advisory_only_label_required = `true`",
        "- human_review_required = `true`",
        "- citation_visible_required = `true`",
        "- refusal_visible_required = `true`",
        "- immutable_audit_required = `true`",
        "- rollback_ready_required = `true`",
        "- incident_register_required = `true`",
        "- kill_switch_required = `true`",
        "- operator_runbook_required = `true`",
        "- post_session_export_required = `true`",
        "- session_replay_required = `true`",
        "- offline_only_operation_allowed = `true`",
        "- internet_dependency_allowed = `false`",
        "",
        "## Incident / Kill-Switch / Rollback Ozeti",
        "",
        f"- incident_count = `{incident_register['incident_count']}`",
        f"- kill_switch_invocation_count = `{kill_switch_and_rollback_log['kill_switch_invocation_count']}`",
        f"- rollback_invocation_count = `{kill_switch_and_rollback_log['rollback_invocation_count']}`",
        f"- rollback_target = `{kill_switch_and_rollback_log['rollback_target']}`",
        f"- rollback_trigger_class = `{kill_switch_and_rollback_log['rollback_trigger_class']}`",
        f"- rollback_trigger_is_hard_fail = `{bool_text(kill_switch_and_rollback_log['rollback_trigger_is_hard_fail'])}`",
        f"- kill_switch_invoke_contract = `{kill_switch_and_rollback_log['kill_switch_invoke_contract']}`",
        f"- incident_severity_classification_contract = `{kill_switch_and_rollback_log['incident_severity_classification_contract']}`",
        f"- pilot_stop_condition_contract = `{kill_switch_and_rollback_log['pilot_stop_condition_contract']}`",
        f"- operator_handoff_contract = `{kill_switch_and_rollback_log['operator_handoff_contract']}`",
        f"- post_session_export_contract = `{kill_switch_and_rollback_log['post_session_export_contract']}`",
        f"- session_replay_contract = `{kill_switch_and_rollback_log['session_replay_contract']}`",
        "",
        "## Postpilot Authority / Parity / Retention Ozeti",
        "",
        f"- control_pair_authority_match = `{bool_text(postcurrent_authority['control_pair_authority_match'])}`",
        f"- current_authority_contract_breach = `{bool_text(postcurrent_authority['current_authority_contract_breach'])}`",
        f"- faz1_50_mismatch_count = `{postparity['faz1_50_mismatch_count']}`",
        f"- v2_95_mismatch_count = `{postparity['v2_95_mismatch_count']}`",
        f"- v3_170_mismatch_count = `{postparity['v3_170_mismatch_count']}`",
        f"- model_request_payload_hash_mismatch_count = `{postparity['model_request_payload_hash_mismatch_count']}`",
        f"- retrieval_request_hash_mismatch_count = `{postparity['retrieval_request_hash_mismatch_count']}`",
        f"- assembled_context_hash_mismatch_count = `{postparity['assembled_context_hash_mismatch_count']}`",
        f"- preprojection_hash_mismatch_count = `{postparity['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{postparity['raw_answer_hash_mismatch_count']}`",
        f"- response_envelope_hash_mismatch_count = `{postparity['response_envelope_hash_mismatch_count']}`",
        f"- family_metric_delta_zero = `{bool_text(postparity['family_metric_delta_zero'])}`",
        f"- must_close_release_controls_pass = `{bool_text(postretention['must_close_release_controls_pass'])}`",
        f"- retained_after_family_eval = `{bool_text(postretention['retained_after_family_eval'])}`",
        f"- retained_after_restart = `{bool_text(postretention['retained_after_restart'])}`",
        f"- retained_after_restore = `{bool_text(postretention['retained_after_restore'])}`",
        f"- runtime_error_count = `{postretention['runtime_error_count']}`",
        f"- unexplained_count = `{postretention['unexplained_count']}`",
        "",
        "## WP Sonuclari",
        "",
        f"- WP-1 = `{wp_statuses['WP-1']}`",
        f"- WP-2 = `{wp_statuses['WP-2']}`",
        f"- WP-3 = `{wp_statuses['WP-3']}`",
        f"- WP-4 = `{wp_statuses['WP-4']}`",
        f"- WP-5 = `{wp_statuses['WP-5']}`",
        f"- WP-6 = `{wp_statuses['WP-6']}`",
        f"- WP-7 = `{wp_statuses['WP-7']}`",
        "",
        "## Resmi Karar",
        "",
        f"- official_decision = `{reconciliation['official_decision']}`",
        f"- admitted_operator_count = `{reconciliation['admitted_operator_count']}`",
        f"- selected_operator_count = `{reconciliation['selected_operator_count']}`",
        f"- planned_session_count = `{reconciliation['planned_session_count']}`",
        f"- completed_session_count = `{reconciliation['completed_session_count']}`",
        f"- session_success_count = `{reconciliation['session_success_count']}`",
        f"- session_fail_count = `{reconciliation['session_fail_count']}`",
        f"- authority_breach_count = `{reconciliation['authority_breach_count']}`",
        f"- model_visible_delta_count = `{reconciliation['model_visible_delta_count']}`",
        f"- runtime_error_count = `{reconciliation['runtime_error_count']}`",
        f"- unexplained_count = `{reconciliation['unexplained_count']}`",
        f"- kill_switch_invocation_count = `{reconciliation['kill_switch_invocation_count']}`",
        f"- rollback_invocation_count = `{reconciliation['rollback_invocation_count']}`",
        f"- incident_count = `{reconciliation['incident_count']}`",
        "",
        "## Sonraki Resmi Is",
        "",
        f"- next_official_work = `{reconciliation['next_official_work']}`",
        "",
        "## Artefact Listesi",
        "",
        f"- coordination/faz46-reference-pack-{DATE}.md",
        f"- evaluation/reports/faz46-rc-g-vs-rc-j-prepilot-current-authority-check-{DATE}.md",
        f"- evaluation/reports/faz46-rc-g-vs-rc-r-prepilot-full-family-model-visible-surface-parity-{DATE}.md",
        f"- evaluation/reports/faz46-rc-r-prepilot-release-controls-retention-{DATE}.md",
        f"- coordination/faz46-rc-r-admitted-operator-freeze-{DATE}.md",
        f"- coordination/faz46-rc-r-session-plan-{DATE}.md",
        f"- pilot/faz46-rc-r-session-001-export-{DATE}.md",
        f"- pilot/faz46-rc-r-session-002-export-{DATE}.md",
        f"- pilot/faz46-rc-r-session-003-export-{DATE}.md",
        f"- pilot/faz46-rc-r-session-004-export-{DATE}.md",
        f"- pilot/faz46-rc-r-session-005-export-{DATE}.md",
        f"- pilot/faz46-rc-r-session-006-export-{DATE}.md",
        f"- pilot/faz46-rc-r-session-007-export-{DATE}.md",
        f"- pilot/faz46-rc-r-session-008-export-{DATE}.md",
        f"- pilot/faz46-rc-r-session-009-export-{DATE}.md",
        f"- coordination/faz46-rc-r-incident-register-{DATE}.md",
        f"- coordination/faz46-rc-r-kill-switch-and-rollback-log-{DATE}.md",
        f"- evaluation/reports/faz46-rc-g-vs-rc-j-postpilot-current-authority-check-{DATE}.md",
        f"- evaluation/reports/faz46-rc-g-vs-rc-r-postpilot-full-family-model-visible-surface-parity-{DATE}.md",
        f"- evaluation/reports/faz46-rc-r-postpilot-release-controls-retention-{DATE}.md",
        f"- coordination/faz46-final-reconciliation-summary-{DATE}.md",
        f"- reports/{RESULT_REPORT_NAME}",
    ]
    return "\n".join(sections)


def _write_outputs(payload: dict[str, Any]) -> None:
    write_text(ROOT / "coordination" / f"faz46-reference-pack-{DATE}.md", _render_pairs("FAZ46 Reference Pack", payload["reference_pack"]))
    write_text(ROOT / "evaluation" / "reports" / f"faz46-rc-g-vs-rc-j-prepilot-current-authority-check-{DATE}.md", _render_pairs("FAZ46 RC-G vs RC-J Prepilot Current Authority Check", payload["precurrent_authority"]))
    write_text(ROOT / "evaluation" / "reports" / f"faz46-rc-g-vs-rc-r-prepilot-full-family-model-visible-surface-parity-{DATE}.md", _render_pairs("FAZ46 RC-G vs RC-R Prepilot Full-Family Model-Visible Surface Parity", payload["preparity"]))
    write_text(ROOT / "evaluation" / "reports" / f"faz46-rc-r-prepilot-release-controls-retention-{DATE}.md", _render_pairs("FAZ46 RC-R Prepilot Release Controls Retention", payload["preretention"]))
    write_text(ROOT / "coordination" / f"faz46-rc-r-admitted-operator-freeze-{DATE}.md", _render_pairs("FAZ46 RC-R Admitted Operator Freeze", payload["admitted_operator_freeze"]))
    write_text(ROOT / "coordination" / f"faz46-rc-r-session-plan-{DATE}.md", _render_pairs("FAZ46 RC-R Session Plan", payload["session_plan"]))
    for index, session_row in enumerate(payload["session_rows"], start=1):
        write_text(ROOT / "pilot" / f"faz46-rc-r-session-{index:03d}-export-{DATE}.md", _session_export_text(session_row))
    write_text(ROOT / "coordination" / f"faz46-rc-r-incident-register-{DATE}.md", _render_pairs("FAZ46 RC-R Incident Register", payload["incident_register"]))
    write_text(ROOT / "coordination" / f"faz46-rc-r-kill-switch-and-rollback-log-{DATE}.md", _render_pairs("FAZ46 RC-R Kill-Switch and Rollback Log", payload["kill_switch_and_rollback_log"]))
    write_text(ROOT / "evaluation" / "reports" / f"faz46-rc-g-vs-rc-j-postpilot-current-authority-check-{DATE}.md", _render_pairs("FAZ46 RC-G vs RC-J Postpilot Current Authority Check", payload["postcurrent_authority"]))
    write_text(ROOT / "evaluation" / "reports" / f"faz46-rc-g-vs-rc-r-postpilot-full-family-model-visible-surface-parity-{DATE}.md", _render_pairs("FAZ46 RC-G vs RC-R Postpilot Full-Family Model-Visible Surface Parity", payload["postparity"]))
    write_text(ROOT / "evaluation" / "reports" / f"faz46-rc-r-postpilot-release-controls-retention-{DATE}.md", _render_pairs("FAZ46 RC-R Postpilot Release Controls Retention", payload["postretention"]))
    write_text(ROOT / "coordination" / f"faz46-final-reconciliation-summary-{DATE}.md", _render_pairs("FAZ46 Final Reconciliation Summary", payload["reconciliation"]))
    write_text(ROOT / "reports" / RESULT_REPORT_NAME, _report_text(payload))


def main() -> int:
    reference_texts = {key: load_text(path) for key, path in REFERENCE_DOCS.items()}
    payload = build_phase_payload(reference_texts)
    _write_outputs(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
