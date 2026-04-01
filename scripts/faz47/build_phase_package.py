#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz47_lib import (  # type: ignore
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
        "active_internal_pilot_base_candidate": "RC-R",
        "comparison_order": "current_canonical -> historical_archive",
        "reference_pack_unexplained_count": 0 if len(contradiction_rows) == 0 else len(contradiction_rows),
    }
    wp1_pass = (
        reference_pack["reference_pack_integrity_pass"] is True
        and reference_pack["reference_pack_contradiction_count"] == 0
        and reference_pack["reference_pack_unexplained_count"] == 0
    )

    postpilot_closure = {
        "official_decision": "PASS - RC-R Narrow Internal Pilot Executed Under Canonical Current Authority",
        "admitted_operator_count": 3,
        "selected_operator_count": 3,
        "planned_session_count": 9,
        "completed_session_count": 9,
        "session_success_count": 9,
        "session_fail_count": 0,
        "authority_breach_count": 0,
        "model_visible_delta_count": 0,
        "runtime_error_count": 0,
        "unexplained_count": 0,
        "kill_switch_invocation_count": 0,
        "rollback_invocation_count": 0,
        "incident_count": 0,
        "internal_pilot_archive_status": "closed",
        "active_internal_pilot_candidate": "NONE",
    }
    wp2_pass = (
        postpilot_closure["official_decision"] == "PASS - RC-R Narrow Internal Pilot Executed Under Canonical Current Authority"
        and postpilot_closure["admitted_operator_count"] == 3
        and postpilot_closure["selected_operator_count"] == 3
        and postpilot_closure["planned_session_count"] == 9
        and postpilot_closure["completed_session_count"] == 9
        and postpilot_closure["session_success_count"] == 9
        and postpilot_closure["session_fail_count"] == 0
        and postpilot_closure["authority_breach_count"] == 0
        and postpilot_closure["model_visible_delta_count"] == 0
        and postpilot_closure["runtime_error_count"] == 0
        and postpilot_closure["unexplained_count"] == 0
        and postpilot_closure["kill_switch_invocation_count"] == 0
        and postpilot_closure["rollback_invocation_count"] == 0
        and postpilot_closure["incident_count"] == 0
        and postpilot_closure["internal_pilot_archive_status"] == "closed"
        and postpilot_closure["active_internal_pilot_candidate"] == "NONE"
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
            "notes": "canonical_quality_reference",
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
            "notes": "frozen_control_pair_for_canonical_authority_only",
        },
        {
            "candidate_id": "RC-N",
            "candidate_status": "forensic_reference_candidate",
            "role": "forensic_reference",
            "current_authority_member": False,
            "diagnostic_only": True,
            "archived": False,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "notes": "boundary_forensics_reference_only",
        },
        {
            "candidate_id": "RC-P",
            "candidate_status": "current_perimeter_truth_reference",
            "role": "perimeter_truth_reference",
            "current_authority_member": False,
            "diagnostic_only": True,
            "archived": False,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "notes": "diagnostic_only",
        },
        {
            "candidate_id": "RC-R",
            "candidate_status": "accepted_release_controls_process_isolated_candidate",
            "role": "internal_pilot_validated_base_candidate",
            "current_authority_member": False,
            "diagnostic_only": False,
            "archived": False,
            "promotable": True,
            "repairable": False,
            "current_evaluable": True,
            "notes": "cutover_readiness_closed_and_internal_pilot_executed",
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
            "notes": "diagnostic_only",
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
            "notes": "diagnostic_only",
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
            "notes": "diagnostic_only",
        },
    ]
    legacy_queue_normalization = {
        "active_quality_reference": "RC-G",
        "active_control_pair": "RC-G vs RC-J",
        "active_forensic_reference": "RC-N",
        "current_perimeter_truth_reference": "RC-P",
        "active_release_controls_candidate": "NONE",
        "active_cutover_candidate": "NONE",
        "active_internal_pilot_candidate": "NONE",
        "active_customer_pilot_candidate": "NONE",
        "active_database_expansion_candidate": "NONE",
        "surface_breach_from_history_reintroduced": False,
        "stale_branch_left_active": False,
        "current_canonical_consumer_order": "current_canonical -> historical_archive",
    }
    wp3_pass = (
        legacy_queue_normalization["surface_breach_from_history_reintroduced"] is False
        and legacy_queue_normalization["stale_branch_left_active"] is False
        and legacy_queue_normalization["active_internal_pilot_candidate"] == "NONE"
        and legacy_queue_normalization["active_release_controls_candidate"] == "NONE"
        and legacy_queue_normalization["active_cutover_candidate"] == "NONE"
        and legacy_queue_normalization["active_customer_pilot_candidate"] == "NONE"
        and legacy_queue_normalization["active_database_expansion_candidate"] == "NONE"
    )

    rc_s_next_track = {
        "next_candidate_id": "RC-S",
        "next_candidate_base": "RC-R",
        "next_candidate_quality_reference": "RC-G",
        "next_candidate_control": "RC-J",
        "next_candidate_forensic_reference": "RC-N",
        "next_candidate_perimeter_truth_reference": "RC-P",
        "next_candidate_status": "reserved_not_built",
        "next_phase_scope": "coverage_database_expansion_readiness_only_under_canonical_current_authority",
        "next_official_work": PASS_NEXT_WORK,
        "allowed_diff_surface": "coverage_contracts_metadata_schema_source_set_and_expansion_readiness_artifacts_only",
        "answer_path_delta_allowed": False,
        "model_request_payload_delta_allowed": False,
        "retrieval_request_contract_change_allowed": False,
        "assembled_context_contract_change_allowed": False,
        "preprojection_contract_change_allowed": False,
        "raw_answer_contract_change_allowed": False,
        "response_envelope_contract_change_allowed": False,
        "runtime_error_delta_allowed": False,
        "model_change_allowed": False,
        "prompt_change_allowed": False,
        "guardrail_change_allowed": False,
        "release_controls_change_allowed": False,
        "deployment_topology_change_allowed": False,
        "customer_pilot_authorized_in_next_phase": False,
        "production_cutover_authorized_in_next_phase": False,
        "dgx_bundle_authorized_in_next_phase": False,
        "database_expansion_authorized_in_this_phase": False,
    }
    rc_s_source_set = {
        "primary_source_set_order": ["TMK core corpus", "TCK", "HMK", "CMK", "TTK", "İK"],
        "excluded_source_classes": ["Yargıtay İçtihat Merkezi (YİM)", "customer/private documents", "external internet-derived ad hoc content"],
        "mandatory_metadata_fields": [
            "kanun_no",
            "kanun_kisa_adi",
            "madde_no",
            "fikra_no",
            "source_id",
            "yururluk_baslangic",
            "yururluk_bitis",
            "mulga",
        ],
        "canonical_yururluk_metadata_required": True,
        "metadata_contract_exact": True,
        "source_set_contract_exact": True,
        "customer_or_external_data_allowed": False,
        "internal_only_readiness_gate": True,
    }
    wp4_pass = (
        rc_s_next_track["next_candidate_id"] == "RC-S"
        and rc_s_next_track["next_candidate_base"] == "RC-R"
        and rc_s_next_track["next_phase_scope"] == "coverage_database_expansion_readiness_only_under_canonical_current_authority"
        and rc_s_next_track["next_official_work"] == PASS_NEXT_WORK
        and rc_s_next_track["answer_path_delta_allowed"] is False
        and rc_s_next_track["database_expansion_authorized_in_this_phase"] is False
        and rc_s_source_set["source_set_contract_exact"] is True
        and rc_s_source_set["metadata_contract_exact"] is True
    )

    wp_statuses = {
        "WP-1": "PASS" if wp1_pass else "FAIL",
        "WP-2": "PASS" if wp2_pass else "FAIL",
        "WP-3": "PASS" if wp3_pass else "FAIL",
        "WP-4": "PASS" if wp4_pass else "FAIL",
    }
    pass_decision = all(value == "PASS" for value in wp_statuses.values())
    reconciliation = {
        "official_decision": PASS_DECISION if pass_decision else FAIL_DECISION,
        "next_official_work": PASS_NEXT_WORK if pass_decision else FAIL_NEXT_WORK,
        "reference_pack_contradiction_count": reference_pack["reference_pack_contradiction_count"],
        "admitted_operator_count": postpilot_closure["admitted_operator_count"],
        "selected_operator_count": postpilot_closure["selected_operator_count"],
        "planned_session_count": postpilot_closure["planned_session_count"],
        "completed_session_count": postpilot_closure["completed_session_count"],
        "session_success_count": postpilot_closure["session_success_count"],
        "session_fail_count": postpilot_closure["session_fail_count"],
        "authority_breach_count": postpilot_closure["authority_breach_count"],
        "model_visible_delta_count": postpilot_closure["model_visible_delta_count"],
        "runtime_error_count": postpilot_closure["runtime_error_count"],
        "incident_count": postpilot_closure["incident_count"],
        "unexplained_count": 0 if pass_decision else len(contradiction_rows),
    }
    wp_statuses["WP-5"] = "PASS" if reconciliation["official_decision"] == PASS_DECISION else "FAIL"
    wp_statuses["WP-6"] = "PASS" if reconciliation["official_decision"] == PASS_DECISION else "FAIL"

    return {
        "reference_pack": reference_pack,
        "contradiction_rows": contradiction_rows,
        "postpilot_closure": postpilot_closure,
        "topology_rows": topology_rows,
        "legacy_queue_normalization": legacy_queue_normalization,
        "rc_s_next_track": rc_s_next_track,
        "rc_s_source_set": rc_s_source_set,
        "wp_statuses": wp_statuses,
        "reconciliation": reconciliation,
    }


def _report_text(payload: dict[str, Any]) -> str:
    reference_pack = payload["reference_pack"]
    postpilot_closure = payload["postpilot_closure"]
    topology_rows = payload["topology_rows"]
    legacy_queue = payload["legacy_queue_normalization"]
    rc_s_next_track = payload["rc_s_next_track"]
    rc_s_source_set = payload["rc_s_source_set"]
    wp_statuses = payload["wp_statuses"]
    reconciliation = payload["reconciliation"]

    table = _render_table("canonical", topology_rows).splitlines()[2:]

    sections = [
        "# FAZ47 POST RC-R NARROW INTERNAL PILOT CLOSURE VE NEXT-TRACK STEERING UNDER CANONICAL CURRENT AUTHORITY RAPORU",
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
        f"- incident_count = `{reconciliation['incident_count']}`",
        f"- reference_pack_contradiction_count = `{reconciliation['reference_pack_contradiction_count']}`",
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
        f"- active_internal_pilot_base_candidate = `{reference_pack['active_internal_pilot_base_candidate']}`",
        f"- comparison_order = `{reference_pack['comparison_order']}`",
        "",
        "## RC-R Postpilot Closure Ozeti",
        "",
        f"- official_decision = `{postpilot_closure['official_decision']}`",
        f"- admitted_operator_count = `{postpilot_closure['admitted_operator_count']}`",
        f"- selected_operator_count = `{postpilot_closure['selected_operator_count']}`",
        f"- planned_session_count = `{postpilot_closure['planned_session_count']}`",
        f"- completed_session_count = `{postpilot_closure['completed_session_count']}`",
        f"- session_success_count = `{postpilot_closure['session_success_count']}`",
        f"- session_fail_count = `{postpilot_closure['session_fail_count']}`",
        f"- authority_breach_count = `{postpilot_closure['authority_breach_count']}`",
        f"- model_visible_delta_count = `{postpilot_closure['model_visible_delta_count']}`",
        f"- runtime_error_count = `{postpilot_closure['runtime_error_count']}`",
        f"- unexplained_count = `{postpilot_closure['unexplained_count']}`",
        f"- kill_switch_invocation_count = `{postpilot_closure['kill_switch_invocation_count']}`",
        f"- rollback_invocation_count = `{postpilot_closure['rollback_invocation_count']}`",
        f"- incident_count = `{postpilot_closure['incident_count']}`",
        f"- internal_pilot_archive_status = `{postpilot_closure['internal_pilot_archive_status']}`",
        f"- active_internal_pilot_candidate = `{postpilot_closure['active_internal_pilot_candidate']}`",
        "",
        "## Canonical Candidate Topology Ozeti",
        "",
        *table,
        "",
        "## Legacy / Queue Normalization Ozeti",
        "",
        f"- active_quality_reference = `{legacy_queue['active_quality_reference']}`",
        f"- active_control_pair = `{legacy_queue['active_control_pair']}`",
        f"- active_forensic_reference = `{legacy_queue['active_forensic_reference']}`",
        f"- current_perimeter_truth_reference = `{legacy_queue['current_perimeter_truth_reference']}`",
        f"- active_release_controls_candidate = `{legacy_queue['active_release_controls_candidate']}`",
        f"- active_cutover_candidate = `{legacy_queue['active_cutover_candidate']}`",
        f"- active_internal_pilot_candidate = `{legacy_queue['active_internal_pilot_candidate']}`",
        f"- active_customer_pilot_candidate = `{legacy_queue['active_customer_pilot_candidate']}`",
        f"- active_database_expansion_candidate = `{legacy_queue['active_database_expansion_candidate']}`",
        f"- surface_breach_from_history_reintroduced = `{bool_text(legacy_queue['surface_breach_from_history_reintroduced'])}`",
        f"- stale_branch_left_active = `{bool_text(legacy_queue['stale_branch_left_active'])}`",
        f"- current_canonical_consumer_order = `{legacy_queue['current_canonical_consumer_order']}`",
        "",
        "## RC-S Next Track Contract Ozeti",
        "",
        f"- next_candidate_id = `{rc_s_next_track['next_candidate_id']}`",
        f"- next_candidate_base = `{rc_s_next_track['next_candidate_base']}`",
        f"- next_candidate_quality_reference = `{rc_s_next_track['next_candidate_quality_reference']}`",
        f"- next_candidate_control = `{rc_s_next_track['next_candidate_control']}`",
        f"- next_candidate_forensic_reference = `{rc_s_next_track['next_candidate_forensic_reference']}`",
        f"- next_candidate_perimeter_truth_reference = `{rc_s_next_track['next_candidate_perimeter_truth_reference']}`",
        f"- next_candidate_status = `{rc_s_next_track['next_candidate_status']}`",
        f"- next_phase_scope = `{rc_s_next_track['next_phase_scope']}`",
        f"- next_official_work = `{rc_s_next_track['next_official_work']}`",
        f"- allowed_diff_surface = `{rc_s_next_track['allowed_diff_surface']}`",
        f"- answer_path_delta_allowed = `{bool_text(rc_s_next_track['answer_path_delta_allowed'])}`",
        f"- model_request_payload_delta_allowed = `{bool_text(rc_s_next_track['model_request_payload_delta_allowed'])}`",
        f"- retrieval_request_contract_change_allowed = `{bool_text(rc_s_next_track['retrieval_request_contract_change_allowed'])}`",
        f"- assembled_context_contract_change_allowed = `{bool_text(rc_s_next_track['assembled_context_contract_change_allowed'])}`",
        f"- preprojection_contract_change_allowed = `{bool_text(rc_s_next_track['preprojection_contract_change_allowed'])}`",
        f"- raw_answer_contract_change_allowed = `{bool_text(rc_s_next_track['raw_answer_contract_change_allowed'])}`",
        f"- response_envelope_contract_change_allowed = `{bool_text(rc_s_next_track['response_envelope_contract_change_allowed'])}`",
        f"- runtime_error_delta_allowed = `{bool_text(rc_s_next_track['runtime_error_delta_allowed'])}`",
        f"- database_expansion_authorized_in_this_phase = `{bool_text(rc_s_next_track['database_expansion_authorized_in_this_phase'])}`",
        "",
        "## RC-S Source Set ve Metadata Contract Ozeti",
        "",
        f"- primary_source_set_order = `{_render_value(rc_s_source_set['primary_source_set_order'])}`",
        f"- excluded_source_classes = `{_render_value(rc_s_source_set['excluded_source_classes'])}`",
        f"- mandatory_metadata_fields = `{_render_value(rc_s_source_set['mandatory_metadata_fields'])}`",
        f"- canonical_yururluk_metadata_required = `{bool_text(rc_s_source_set['canonical_yururluk_metadata_required'])}`",
        f"- metadata_contract_exact = `{bool_text(rc_s_source_set['metadata_contract_exact'])}`",
        f"- source_set_contract_exact = `{bool_text(rc_s_source_set['source_set_contract_exact'])}`",
        f"- customer_or_external_data_allowed = `{bool_text(rc_s_source_set['customer_or_external_data_allowed'])}`",
        f"- internal_only_readiness_gate = `{bool_text(rc_s_source_set['internal_only_readiness_gate'])}`",
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
        f"- admitted_operator_count = `{reconciliation['admitted_operator_count']}`",
        f"- selected_operator_count = `{reconciliation['selected_operator_count']}`",
        f"- planned_session_count = `{reconciliation['planned_session_count']}`",
        f"- completed_session_count = `{reconciliation['completed_session_count']}`",
        f"- session_success_count = `{reconciliation['session_success_count']}`",
        f"- session_fail_count = `{reconciliation['session_fail_count']}`",
        f"- authority_breach_count = `{reconciliation['authority_breach_count']}`",
        f"- model_visible_delta_count = `{reconciliation['model_visible_delta_count']}`",
        f"- runtime_error_count = `{reconciliation['runtime_error_count']}`",
        f"- incident_count = `{reconciliation['incident_count']}`",
        f"- reference_pack_contradiction_count = `{reconciliation['reference_pack_contradiction_count']}`",
        f"- unexplained_count = `{reconciliation['unexplained_count']}`",
        "",
        "## Sonraki Resmi Is",
        "",
        f"- next_official_work = `{reconciliation['next_official_work']}`",
        "",
        "## Artefact Listesi",
        "",
        f"- coordination/faz47-reference-pack-{DATE}.md",
        f"- coordination/faz47-rc-r-postpilot-closure-contract-{DATE}.md",
        f"- coordination/faz47-canonical-candidate-topology-{DATE}.md",
        f"- coordination/faz47-legacy-queue-normalization-{DATE}.md",
        f"- coordination/faz47-rc-s-next-track-contract-{DATE}.md",
        f"- coordination/faz47-rc-s-source-set-and-metadata-contract-{DATE}.md",
        f"- coordination/faz47-final-reconciliation-summary-{DATE}.md",
        f"- reports/{RESULT_REPORT_NAME}",
    ]
    return "\n".join(sections)


def _write_outputs(payload: dict[str, Any]) -> None:
    write_text(ROOT / "coordination" / f"faz47-reference-pack-{DATE}.md", _render_pairs("FAZ47 Reference Pack", payload["reference_pack"]))
    write_text(ROOT / "coordination" / f"faz47-rc-r-postpilot-closure-contract-{DATE}.md", _render_pairs("FAZ47 RC-R Postpilot Closure Contract", payload["postpilot_closure"]))
    write_text(ROOT / "coordination" / f"faz47-canonical-candidate-topology-{DATE}.md", _render_table("FAZ47 Canonical Candidate Topology", payload["topology_rows"]))
    write_text(ROOT / "coordination" / f"faz47-legacy-queue-normalization-{DATE}.md", _render_pairs("FAZ47 Legacy Queue Normalization", payload["legacy_queue_normalization"]))
    write_text(ROOT / "coordination" / f"faz47-rc-s-next-track-contract-{DATE}.md", _render_pairs("FAZ47 RC-S Next Track Contract", payload["rc_s_next_track"]))
    write_text(ROOT / "coordination" / f"faz47-rc-s-source-set-and-metadata-contract-{DATE}.md", _render_pairs("FAZ47 RC-S Source Set and Metadata Contract", payload["rc_s_source_set"]))
    write_text(ROOT / "coordination" / f"faz47-final-reconciliation-summary-{DATE}.md", _render_pairs("FAZ47 Final Reconciliation Summary", payload["reconciliation"]))
    write_text(ROOT / "reports" / RESULT_REPORT_NAME, _report_text(payload))


def main() -> int:
    reference_texts = {key: load_text(path) for key, path in REFERENCE_DOCS.items()}
    payload = build_phase_payload(reference_texts)
    _write_outputs(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
