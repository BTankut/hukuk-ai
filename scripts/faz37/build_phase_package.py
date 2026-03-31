#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz37_lib import (  # type: ignore
    COMPACT_DATE,
    CURRENT_AUTHORITY_EXPECTED,
    DATE,
    DECISION_TO_NEXT_WORK,
    FAZ35_FRONTIER_EXPECTED,
    FAZ35_RESPONSE_EXPECTED,
    FAZ35_RETENTION_EXPECTED,
    FAZ35_TARGETED_ACCEPTANCE_EXPECTED,
    FAZ36_ACCEPTANCE_EXPECTED,
    FAZ36_FRONTIER_EXPECTED,
    FAZ36_FULL_FAMILY_EXPECTED,
    FAZ36_MANIFEST_JSON,
    FAZ36_RESPONSE_EXPECTED,
    FAZ36_RETENTION_EXPECTED,
    FAIL_AUTHORITY,
    FAIL_INCONCLUSIVE,
    FAIL_UNSTABLE,
    PASS_DECISION,
    REFERENCE_FILES,
    REFERENCE_MARKERS,
    RESULT_REPORT_NAME,
    ROOT,
    bool_text,
    build_frozen_frontier_records,
    build_frozen_response_envelope_records,
    load_json,
    load_text,
    markdown_table,
    write_json,
    write_text,
)


WP2_FIELDS = [
    "control_pair_authority_match",
    "current_authority_contract_breach",
    "surface_breach_from_history_reintroduced",
    "current_canonical_authority_adopted",
    "control_pair_runtime_error_count",
    "model_request_payload_hash_mismatch_count",
    "retrieval_request_hash_mismatch_count",
    "assembled_context_hash_mismatch_count",
    "runtime_error_count",
]

WP3_FIELDS = [
    "frontier_record_count",
    "faz1_50_mismatch_count",
    "v2_95_mismatch_count",
    "v3_170_mismatch_count",
    "preprojection_hash_mismatch_count",
    "raw_answer_hash_mismatch_count",
    "response_envelope_hash_mismatch_count",
    "runtime_error_count",
    "unexplained_count",
]

WP4_FIELDS = [
    "response_envelope_subfrontier_record_count",
    "faz1_50_mismatch_count",
    "v2_95_mismatch_count",
    "v3_170_mismatch_count",
    "response_envelope_hash_mismatch_count",
    "runtime_error_count",
    "unexplained_count",
]

WP5_FIELDS = [
    "must_close_release_controls_count",
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
    "refusal_smoke_status_code",
    "restart_refusal_smoke_status_code",
    "tokenizer_usage_total",
    "estimated_usage_total",
    "token_accounting_failure_total",
    "backup_restore_missing_file_count",
    "runtime_error_count",
    "unexplained_count",
]

WP6_FIELDS = [
    "faz1_50_mismatch_count",
    "v2_95_mismatch_count",
    "v3_170_mismatch_count",
    "model_request_payload_hash_mismatch_count",
    "retrieval_request_hash_mismatch_count",
    "assembled_context_hash_mismatch_count",
    "preprojection_hash_mismatch_count",
    "raw_answer_hash_mismatch_count",
    "response_envelope_hash_mismatch_count",
    "family_metric_delta_zero",
    "runtime_error_count",
    "unexplained_count",
]

WP7_FIELDS = [
    "must_close_release_controls_pass",
    "retained_after_family_eval",
    "retained_after_restart",
    "retained_after_restore",
    "answer_path_delta_reintroduced",
    "runtime_error_count",
    "unexplained_count",
]

ARTEFACT_LIST = [
    f"coordination/faz37-official-implementation-plan-{DATE}.md",
    f"coordination/faz37-steering-decision-table-{DATE}.md",
    f"coordination/faz37-release-controls-reference-pack-{DATE}.md",
    f"coordination/faz37-canonical-topology-refreeze-{DATE}.md",
    f"coordination/faz37-rc-q-recapture-contract-{DATE}.md",
    f"coordination/faz37-rc-q-frontier-174-freeze-{DATE}.md",
    f"coordination/faz37-rc-q-response-envelope-subfrontier-109-freeze-{DATE}.md",
    f"coordination/faz37-rc-q-targeted-acceptance-freeze-{DATE}.md",
    f"coordination/faz37-rc-q-full-family-parity-freeze-{DATE}.md",
    f"coordination/faz37-rc-q-retention-recapture-contract-{DATE}.md",
    f"coordination/faz37-rc-q-repair-truth-contrast-matrix-{DATE}.md",
    f"coordination/faz37-rc-q-repair-truth-reconciliation-{DATE}.md",
    f"coordination/faz37-final-reconciliation-summary-{DATE}.md",
    f"evaluation/reports/faz37-rc-g-vs-rc-j-current-authority-check-{DATE}.md",
    f"evaluation/reports/faz37-rc-g-vs-rc-q-upstream-equality-gate-{DATE}.md",
    f"evaluation/reports/faz37-rc-g-vs-rc-q-frontier-174-recapture-{DATE}.md",
    f"evaluation/reports/faz37-rc-g-vs-rc-q-response-envelope-109-recapture-{DATE}.md",
    f"evaluation/reports/faz37-rc-q-release-controls-targeted-acceptance-recapture-{DATE}.md",
    f"evaluation/reports/faz37-rc-g-vs-rc-q-full-family-model-visible-surface-parity-recapture-{DATE}.md",
    f"evaluation/reports/faz37-rc-q-release-controls-retention-recapture-{DATE}.md",
    f"evaluation/reports/faz37-rc-q-repair-truth-summary-{DATE}.md",
    f"coordination/faz37-rc-q-manifest-{DATE}.json",
    f"reports/{RESULT_REPORT_NAME}",
    f"docs/{RESULT_REPORT_NAME}",
]


def build_materialized_payload() -> dict[str, Any]:
    contradiction_rows: list[dict[str, str]] = []
    for name, path in REFERENCE_FILES.items():
        text = load_text(path)
        for marker in REFERENCE_MARKERS[name]:
            if marker not in text:
                contradiction_rows.append({"reference": name, "missing_marker": marker})

    manifest = {
        "candidate_id": "RC-Q",
        "base_candidate": "RC-G",
        "control_candidate": "RC-J",
        "forensic_reference_candidate": "RC-N",
        "current_perimeter_truth_reference": "RC-P",
        "allowed_diff_surface": "non_model_visible_release_controls_perimeter_only",
        "answer_path_delta_allowed": False,
        "cutover_authorized": False,
        "pilot_authorized": False,
        "database_expansion_authorized": False,
        "promotable": False,
        "repairable": False,
        "current_evaluable": True,
        "candidate_status": "frozen_failed_repair_candidate + current_evaluable_for_recapture_only",
    }

    reference_pack = {
        "reference_pack_integrity_pass": len(contradiction_rows) == 0,
        "reference_pack_contradiction_count": len(contradiction_rows),
        "canonical_current_authority_ref": "FAZ21",
        "post_rc_m_steering_ref": "FAZ25",
        "rc_n_release_controls_legacy_ref": "FAZ26",
        "rc_n_boundary_root_cause_ref": "FAZ27",
        "rc_o_repair_truth_ref": "FAZ31",
        "rc_o_archival_closure_ref": "FAZ32",
        "post_rc_o_steering_ref": "FAZ33",
        "rc_p_perimeter_truth_ref": "FAZ35",
        "rc_q_failed_repair_truth_ref": "FAZ36",
        "contradiction_rows": contradiction_rows,
    }

    topology = {
        "RC-G": "accepted_quality_reference",
        "RC-J": "canonical_control_diagnostic",
        "RC-N": "forensic_reference_candidate",
        "RC-M": "discard_archived / historical_summary_archive / diagnostic_only",
        "RC-O": "discard_archived / historical_repair_archive / diagnostic_only",
        "RC-P": "frozen_failed_perimeter_candidate / diagnostic_only",
        "RC-Q": "frozen_failed_repair_candidate / current_evaluable_for_recapture_only",
        "comparison_order": "current_canonical -> historical_archive",
        "surface_breach_from_history_reintroduced": False,
        "cutover_allowed": False,
        "pilot_allowed": False,
        "database_expansion_allowed": False,
    }

    recapture_contract = {
        "candidate_id": "RC-Q",
        "base_candidate": "RC-G",
        "control_candidate": "RC-J",
        "forensic_reference_candidate": "RC-N",
        "current_perimeter_truth_reference": "RC-P",
        "allowed_diff_surface": "non_model_visible_release_controls_perimeter_only",
        "answer_path_delta_allowed": False,
        "cutover_authorized": False,
        "pilot_authorized": False,
        "database_expansion_authorized": False,
        "new_candidate_authorized": False,
        "patch_existing_candidate_authorized": False,
        "twin_capture_required": True,
        "runtime_override_allowed": False,
    }

    return {
        "reference_pack": reference_pack,
        "topology": topology,
        "manifest": manifest,
        "recapture_contract": recapture_contract,
        "frontier_records": build_frozen_frontier_records(),
        "response_records": build_frozen_response_envelope_records(),
        "frozen_manifest_source": load_json(FAZ36_MANIFEST_JSON),
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _reconcile_section(a: dict[str, Any], b: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    mismatch_fields = [field for field in fields if a.get(field) != b.get(field)]
    runtime_error_total = sum(
        int(a.get(field, 0)) + int(b.get(field, 0))
        for field in fields
        if "runtime_error_count" in field
    )
    reconciled = {
        "capture_stability_match": len(mismatch_fields) == 0 and runtime_error_total == 0,
        "capture_a_vs_capture_b_mismatch_count": len(mismatch_fields),
        "capture_a_vs_capture_b_runtime_error_count": runtime_error_total,
        "capture_a_vs_capture_b_mismatch_fields": mismatch_fields,
    }
    for field in fields:
        reconciled[field] = a.get(field)
    return reconciled


def _section_matches(section: dict[str, Any], expected: dict[str, Any], fields: list[str]) -> bool:
    return all(section.get(field) == expected.get(field) for field in fields)


def _section_runtime_or_unexplained(section: dict[str, Any]) -> bool:
    return any(
        ("runtime_error_count" in key or key == "unexplained_count") and int(value) > 0
        for key, value in section.items()
        if isinstance(value, (int, float, bool))
    )


def _matches_faz35(payload: dict[str, Any]) -> bool:
    wp3 = payload["wp3"]
    wp4 = payload["wp4"]
    wp5 = payload["wp5"]
    wp7 = payload["wp7"]
    return (
        _section_matches(wp3, FAZ35_FRONTIER_EXPECTED, WP3_FIELDS)
        and _section_matches(wp4, FAZ35_RESPONSE_EXPECTED, WP4_FIELDS)
        and _section_matches(wp5, FAZ35_TARGETED_ACCEPTANCE_EXPECTED, WP5_FIELDS)
        and _section_matches(wp7, FAZ35_RETENTION_EXPECTED, WP7_FIELDS)
    )


def _matches_faz36(payload: dict[str, Any]) -> bool:
    return (
        _section_matches(payload["wp3"], FAZ36_FRONTIER_EXPECTED, WP3_FIELDS)
        and _section_matches(payload["wp4"], FAZ36_RESPONSE_EXPECTED, WP4_FIELDS)
        and _section_matches(payload["wp5"], FAZ36_ACCEPTANCE_EXPECTED, WP5_FIELDS)
        and _section_matches(payload["wp6"], FAZ36_FULL_FAMILY_EXPECTED, WP6_FIELDS)
        and _section_matches(payload["wp7"], FAZ36_RETENTION_EXPECTED, WP7_FIELDS)
    )


def build_phase_payload(*, capture_a: dict[str, Any], capture_b: dict[str, Any]) -> dict[str, Any]:
    materialized = build_materialized_payload()
    reference_pack = materialized["reference_pack"]
    topology = materialized["topology"]
    manifest = materialized["manifest"]
    contract = materialized["recapture_contract"]

    wp2 = _reconcile_section(capture_a["wp2"], capture_b["wp2"], WP2_FIELDS)
    wp3 = _reconcile_section(capture_a["wp3"], capture_b["wp3"], WP3_FIELDS)
    wp4 = _reconcile_section(capture_a["wp4"], capture_b["wp4"], WP4_FIELDS)
    wp5 = _reconcile_section(capture_a["wp5"], capture_b["wp5"], WP5_FIELDS)
    wp6 = _reconcile_section(capture_a["wp6"], capture_b["wp6"], WP6_FIELDS)
    wp7 = _reconcile_section(capture_a["wp7"], capture_b["wp7"], WP7_FIELDS)

    wp1_pass = (
        reference_pack["reference_pack_integrity_pass"] is True
        and reference_pack["reference_pack_contradiction_count"] == 0
        and reference_pack["canonical_current_authority_ref"] == "FAZ21"
        and reference_pack["post_rc_m_steering_ref"] == "FAZ25"
        and reference_pack["rc_n_release_controls_legacy_ref"] == "FAZ26"
        and reference_pack["rc_n_boundary_root_cause_ref"] == "FAZ27"
        and reference_pack["rc_o_repair_truth_ref"] == "FAZ31"
        and reference_pack["rc_o_archival_closure_ref"] == "FAZ32"
        and reference_pack["post_rc_o_steering_ref"] == "FAZ33"
        and reference_pack["rc_p_perimeter_truth_ref"] == "FAZ35"
        and reference_pack["rc_q_failed_repair_truth_ref"] == "FAZ36"
        and manifest["candidate_id"] == "RC-Q"
        and manifest["base_candidate"] == "RC-G"
        and manifest["control_candidate"] == "RC-J"
        and manifest["forensic_reference_candidate"] == "RC-N"
        and manifest["current_perimeter_truth_reference"] == "RC-P"
        and manifest["allowed_diff_surface"] == "non_model_visible_release_controls_perimeter_only"
        and manifest["answer_path_delta_allowed"] is False
        and manifest["promotable"] is False
        and manifest["repairable"] is False
        and manifest["current_evaluable"] is True
        and manifest["cutover_authorized"] is False
        and manifest["pilot_authorized"] is False
        and manifest["database_expansion_authorized"] is False
    )

    wp2_pass = wp2["capture_stability_match"] is True and _section_matches(
        wp2,
        {
            **CURRENT_AUTHORITY_EXPECTED,
            "control_pair_runtime_error_count": 0,
        },
        WP2_FIELDS,
    )

    wp3_exact = _section_matches(wp3, FAZ36_FRONTIER_EXPECTED, WP3_FIELDS)
    wp4_exact = _section_matches(wp4, FAZ36_RESPONSE_EXPECTED, WP4_FIELDS)
    wp5_exact = _section_matches(wp5, FAZ36_ACCEPTANCE_EXPECTED, WP5_FIELDS)
    wp6_exact = _section_matches(wp6, FAZ36_FULL_FAMILY_EXPECTED, WP6_FIELDS)
    wp7_exact = _section_matches(wp7, FAZ36_RETENTION_EXPECTED, WP7_FIELDS)

    wp3_inconclusive = (not wp3["capture_stability_match"]) or _section_runtime_or_unexplained(wp3)
    wp4_inconclusive = (not wp4["capture_stability_match"]) or _section_runtime_or_unexplained(wp4)
    wp5_inconclusive = (not wp5["capture_stability_match"]) or _section_runtime_or_unexplained(wp5)
    wp6_inconclusive = (not wp6["capture_stability_match"]) or _section_runtime_or_unexplained(wp6)
    wp7_inconclusive = (not wp7["capture_stability_match"]) or _section_runtime_or_unexplained(wp7)

    wp3_pass = wp3["capture_stability_match"] is True and wp3_exact
    wp4_pass = wp4["capture_stability_match"] is True and wp4_exact
    wp5_pass = wp5["capture_stability_match"] is True and wp5_exact
    wp6_pass = wp6["capture_stability_match"] is True and wp6_exact
    wp7_pass = wp7["capture_stability_match"] is True and wp7_exact

    stable_truth = not any((wp3_inconclusive, wp4_inconclusive, wp5_inconclusive, wp6_inconclusive, wp7_inconclusive))
    exact_faz36_truth = wp3_pass and wp4_pass and wp5_pass and wp6_pass and wp7_pass

    if not wp1_pass:
        official_decision = FAIL_INCONCLUSIVE
    elif not wp2_pass:
        official_decision = FAIL_AUTHORITY
    elif not stable_truth:
        official_decision = FAIL_INCONCLUSIVE
    elif not exact_faz36_truth:
        official_decision = FAIL_UNSTABLE
    else:
        official_decision = PASS_DECISION

    contrast = {
        "matches_faz35_perimeter_truth": _matches_faz35(
            {"wp3": wp3, "wp4": wp4, "wp5": wp5, "wp7": wp7}
        ),
        "matches_faz36_failed_repair_truth": exact_faz36_truth,
        "matches_neither": False,
        "primary_reason": "",
        "root_cause_class": "",
        "unexplained_count": int(wp3["unexplained_count"])
        + int(wp4["unexplained_count"])
        + int(wp5["unexplained_count"])
        + int(wp6["unexplained_count"])
        + int(wp7["unexplained_count"]),
    }
    contrast["matches_neither"] = not contrast["matches_faz35_perimeter_truth"] and not contrast[
        "matches_faz36_failed_repair_truth"
    ]
    if official_decision == PASS_DECISION:
        contrast["primary_reason"] = "exact_faz36_failed_repair_truth_recaptured"
        contrast["root_cause_class"] = "rc_q_failed_repair_truth_stable"
    elif official_decision == FAIL_AUTHORITY:
        contrast["primary_reason"] = "current_authority_or_upstream_equality_drift"
        contrast["root_cause_class"] = "current_authority_or_upstream_equality_drift"
    elif official_decision == FAIL_INCONCLUSIVE:
        contrast["primary_reason"] = "truth_unstable_between_captures_or_runtime_or_unexplained"
        contrast["root_cause_class"] = "rc_q_recapture_inconclusive"
    elif contrast["matches_faz35_perimeter_truth"]:
        contrast["primary_reason"] = "reverted_to_faz35_perimeter_truth"
        contrast["root_cause_class"] = "rc_q_repair_truth_regressed_to_perimeter_truth"
    else:
        contrast["primary_reason"] = "current_repair_truth_differs_from_faz35_and_faz36"
        contrast["root_cause_class"] = "rc_q_repair_truth_unstable"

    return {
        "materialized": materialized,
        "capture_a": capture_a,
        "capture_b": capture_b,
        "wp2": wp2,
        "wp3": wp3,
        "wp4": wp4,
        "wp5": wp5,
        "wp6": wp6,
        "wp7": wp7,
        "contrast": contrast,
        "wp_statuses": {
            "WP-1": "PASS" if wp1_pass else "FAIL",
            "WP-2": "PASS" if wp2_pass else "FAIL",
            "WP-3": "PASS" if wp3_pass else "FAIL",
            "WP-4": "PASS" if wp4_pass else "FAIL",
            "WP-5": "PASS" if wp5_pass else "FAIL",
            "WP-6": "PASS" if wp6_pass else "FAIL",
            "WP-7": "PASS" if wp7_pass else "FAIL",
            "WP-8": "PASS" if contrast["unexplained_count"] == 0 else "FAIL",
        },
        "official_decision": official_decision,
        "next_official_work": DECISION_TO_NEXT_WORK[official_decision],
    }


def _render_kv_md(title: str, rows: list[tuple[str, Any]]) -> str:
    lines = [f"# {title}", ""]
    for key, value in rows:
        rendered = bool_text(value) if isinstance(value, bool) else value
        lines.append(f"- {key} = `{rendered}`")
    lines.append("")
    return "\n".join(lines)


def _authoritative_rows(section: dict[str, Any], fields: list[str]) -> list[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = [
        ("capture_stability_match", section["capture_stability_match"]),
        ("capture_a_vs_capture_b_mismatch_count", section["capture_a_vs_capture_b_mismatch_count"]),
        ("capture_a_vs_capture_b_runtime_error_count", section["capture_a_vs_capture_b_runtime_error_count"]),
    ]
    rows.extend((field, section[field]) for field in fields)
    return rows


def _render_result_report(payload: dict[str, Any]) -> str:
    reference = payload["materialized"]["reference_pack"]
    manifest = payload["materialized"]["manifest"]
    contract = payload["materialized"]["recapture_contract"]
    wp2 = payload["wp2"]
    wp3 = payload["wp3"]
    wp4 = payload["wp4"]
    wp5 = payload["wp5"]
    wp6 = payload["wp6"]
    wp7 = payload["wp7"]
    contrast = payload["contrast"]
    wp_rows = [{"wp": key, "status": value} for key, value in payload["wp_statuses"].items()]

    lines = [
        f"# FAZ37 RC-Q RELEASE-CONTROLS PERIMETER REPAIR RECAPTURE UNDER CANONICAL CURRENT AUTHORITY RAPORU",
        "",
        "## A) Yonetici Ozeti",
        "",
        f"- official_decision = `{payload['official_decision']}`",
        f"- next_official_work = `{payload['next_official_work']}`",
        f"- wp2_pass = `{bool_text(payload['wp_statuses']['WP-2'] == 'PASS')}`",
        f"- wp3_pass = `{bool_text(payload['wp_statuses']['WP-3'] == 'PASS')}`",
        f"- wp4_pass = `{bool_text(payload['wp_statuses']['WP-4'] == 'PASS')}`",
        f"- wp5_pass = `{bool_text(payload['wp_statuses']['WP-5'] == 'PASS')}`",
        f"- wp6_pass = `{bool_text(payload['wp_statuses']['WP-6'] == 'PASS')}`",
        f"- wp7_pass = `{bool_text(payload['wp_statuses']['WP-7'] == 'PASS')}`",
        "",
        "## B) Reference Pack Ozeti",
        "",
        *[f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`" for key, value in reference.items() if key != "contradiction_rows"],
        "",
        "## C) RC-Q Recapture Contract Ozeti",
        "",
        *[f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`" for key, value in contract.items()],
        "",
        "## D) Current Authority ve Upstream Equality Authoritative Recapture Ozeti",
        "",
        *[f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`" for key, value in _authoritative_rows(wp2, WP2_FIELDS)],
        "",
        "## E) Frontier 174 Authoritative Recapture Ozeti",
        "",
        *[f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`" for key, value in _authoritative_rows(wp3, WP3_FIELDS)],
        "",
        "## F) Response Envelope Subfrontier 109 Authoritative Recapture Ozeti",
        "",
        *[f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`" for key, value in _authoritative_rows(wp4, WP4_FIELDS)],
        "",
        "## G) Release Controls Targeted Acceptance Authoritative Recapture Ozeti",
        "",
        *[f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`" for key, value in _authoritative_rows(wp5, WP5_FIELDS)],
        "",
        "## H) Full-Family Model-Visible Surface Parity Authoritative Recapture Ozeti",
        "",
        *[f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`" for key, value in _authoritative_rows(wp6, WP6_FIELDS)],
        "",
        "## I) Release Controls Retention Authoritative Recapture Ozeti",
        "",
        *[f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`" for key, value in _authoritative_rows(wp7, WP7_FIELDS)],
        "",
        "## J) Repair Truth Contrast Matrix Ozeti",
        "",
        f"- matches_faz35_perimeter_truth = `{bool_text(contrast['matches_faz35_perimeter_truth'])}`",
        f"- matches_faz36_failed_repair_truth = `{bool_text(contrast['matches_faz36_failed_repair_truth'])}`",
        f"- matches_neither = `{bool_text(contrast['matches_neither'])}`",
        f"- primary_reason = `{contrast['primary_reason']}`",
        f"- root_cause_class = `{contrast['root_cause_class']}`",
        f"- unexplained_count = `{contrast['unexplained_count']}`",
        "",
        "## K) WP Sonuclari",
        "",
        *markdown_table([("wp", "wp"), ("status", "status")], wp_rows),
        "",
        "## L) Resmi Karar",
        "",
        f"- official_decision = `{payload['official_decision']}`",
        "",
        "## M) Sonraki Resmi Is",
        "",
        f"- next_official_work = `{payload['next_official_work']}`",
        "",
        "## N) Artefact Listesi",
        "",
        *[f"- `{item}`" for item in ARTEFACT_LIST],
        "",
    ]
    return "\n".join(lines)


def render_outputs(payload: dict[str, Any]) -> dict[Path, str | dict[str, Any]]:
    materialized = payload["materialized"]
    reference = materialized["reference_pack"]
    topology = materialized["topology"]
    manifest = materialized["manifest"]
    contract = materialized["recapture_contract"]
    wp2 = payload["wp2"]
    wp3 = payload["wp3"]
    wp4 = payload["wp4"]
    wp5 = payload["wp5"]
    wp6 = payload["wp6"]
    wp7 = payload["wp7"]
    contrast = payload["contrast"]
    wp_rows = [{"wp": key, "status": value} for key, value in payload["wp_statuses"].items()]

    outputs: dict[Path, str | dict[str, Any]] = {
        ROOT / "coordination" / f"faz37-rc-q-manifest-{DATE}.json": _json_safe(manifest),
        ROOT / "coordination" / f"faz37-official-implementation-plan-{DATE}.md": "\n".join(
            [
                "# FAZ37 Official Implementation Plan",
                "",
                "1. FAZ21/25/26/27/31/32/33/35/36 referans pack’ini freeze et.",
                "2. RC-Q frozen contract’i ile twin-capture recapture akisini kur.",
                "3. Her capture icin RC-G reference lane ve RC-Q candidate lane first-run eval/smoke setini topla.",
                "4. WP-2..WP-7 truth setini capture_a ve capture_b uzerinden authoritative reconcile et.",
                "5. FAZ35 perimeter truth ve FAZ36 failed repair truth ile contrast/reconciliation uret.",
                "6. Tek resmi karar ve tek next_official_work ile FAZ37 paketini kapat.",
                "",
            ]
        ),
        ROOT / "coordination" / f"faz37-release-controls-reference-pack-{DATE}.md": _render_kv_md(
            "FAZ37 Release Controls Reference Pack",
            [(key, value) for key, value in reference.items() if key != "contradiction_rows"],
        ),
        ROOT / "coordination" / f"faz37-canonical-topology-refreeze-{DATE}.md": _render_kv_md(
            "FAZ37 Canonical Topology Refreeze",
            list(topology.items()),
        ),
        ROOT / "coordination" / f"faz37-rc-q-recapture-contract-{DATE}.md": _render_kv_md(
            "FAZ37 RC-Q Recapture Contract",
            list(contract.items()),
        ),
        ROOT / "coordination" / f"faz37-rc-q-frontier-174-freeze-{DATE}.md": _render_kv_md(
            "FAZ37 RC-Q Frontier 174 Freeze",
            list(FAZ36_FRONTIER_EXPECTED.items()),
        ),
        ROOT / "coordination" / f"faz37-rc-q-response-envelope-subfrontier-109-freeze-{DATE}.md": _render_kv_md(
            "FAZ37 RC-Q Response Envelope Subfrontier 109 Freeze",
            list(FAZ36_RESPONSE_EXPECTED.items()),
        ),
        ROOT / "coordination" / f"faz37-rc-q-targeted-acceptance-freeze-{DATE}.md": _render_kv_md(
            "FAZ37 RC-Q Targeted Acceptance Freeze",
            list(FAZ36_ACCEPTANCE_EXPECTED.items()),
        ),
        ROOT / "coordination" / f"faz37-rc-q-full-family-parity-freeze-{DATE}.md": _render_kv_md(
            "FAZ37 RC-Q Full Family Parity Freeze",
            list(FAZ36_FULL_FAMILY_EXPECTED.items()),
        ),
        ROOT / "coordination" / f"faz37-rc-q-retention-recapture-contract-{DATE}.md": _render_kv_md(
            "FAZ37 RC-Q Retention Recapture Contract",
            list(FAZ36_RETENTION_EXPECTED.items()),
        ),
        ROOT / "coordination" / f"faz37-rc-q-repair-truth-contrast-matrix-{DATE}.md": _render_kv_md(
            "FAZ37 RC-Q Repair Truth Contrast Matrix",
            list(contrast.items()),
        ),
        ROOT / "coordination" / f"faz37-rc-q-repair-truth-reconciliation-{DATE}.md": "\n".join(
            [
                "# FAZ37 RC-Q Repair Truth Reconciliation",
                "",
                f"- wp2_capture_stability_match = `{bool_text(wp2['capture_stability_match'])}`",
                f"- wp3_capture_stability_match = `{bool_text(wp3['capture_stability_match'])}`",
                f"- wp4_capture_stability_match = `{bool_text(wp4['capture_stability_match'])}`",
                f"- wp5_capture_stability_match = `{bool_text(wp5['capture_stability_match'])}`",
                f"- wp6_capture_stability_match = `{bool_text(wp6['capture_stability_match'])}`",
                f"- wp7_capture_stability_match = `{bool_text(wp7['capture_stability_match'])}`",
                f"- matches_faz35_perimeter_truth = `{bool_text(contrast['matches_faz35_perimeter_truth'])}`",
                f"- matches_faz36_failed_repair_truth = `{bool_text(contrast['matches_faz36_failed_repair_truth'])}`",
                f"- matches_neither = `{bool_text(contrast['matches_neither'])}`",
                f"- primary_reason = `{contrast['primary_reason']}`",
                f"- root_cause_class = `{contrast['root_cause_class']}`",
                "",
            ]
        ),
        ROOT / "coordination" / f"faz37-final-reconciliation-summary-{DATE}.md": "\n".join(
            [
                "# FAZ37 Final Reconciliation Summary",
                "",
                f"- official_decision = `{payload['official_decision']}`",
                f"- next_official_work = `{payload['next_official_work']}`",
                f"- frontier_record_count = `{wp3['frontier_record_count']}`",
                f"- response_envelope_subfrontier_record_count = `{wp4['response_envelope_subfrontier_record_count']}`",
                f"- must_close_release_controls_pass = `{bool_text(wp7['must_close_release_controls_pass'])}`",
                f"- retention_reintroduced = `{bool_text(wp7['answer_path_delta_reintroduced'])}`",
                "",
            ]
        ),
        ROOT / "coordination" / f"faz37-steering-decision-table-{DATE}.md": "\n".join(
            [
                "# FAZ37 Steering Decision Table",
                "",
                *markdown_table([("wp", "wp"), ("status", "status")], wp_rows),
                "",
                f"- official_decision = `{payload['official_decision']}`",
                f"- next_official_work = `{payload['next_official_work']}`",
                "",
            ]
        ),
        ROOT / "evaluation" / "reports" / f"faz37-rc-g-vs-rc-j-current-authority-check-{DATE}.md": _render_kv_md(
            "FAZ37 RC-G vs RC-J Current Authority Check",
            _authoritative_rows(wp2, WP2_FIELDS),
        ),
        ROOT / "evaluation" / "reports" / f"faz37-rc-g-vs-rc-q-upstream-equality-gate-{DATE}.md": _render_kv_md(
            "FAZ37 RC-G vs RC-Q Upstream Equality Gate",
            _authoritative_rows(wp2, WP2_FIELDS),
        ),
        ROOT / "evaluation" / "reports" / f"faz37-rc-g-vs-rc-q-frontier-174-recapture-{DATE}.md": _render_kv_md(
            "FAZ37 RC-G vs RC-Q Frontier 174 Recapture",
            _authoritative_rows(wp3, WP3_FIELDS),
        ),
        ROOT / "evaluation" / "reports" / f"faz37-rc-g-vs-rc-q-response-envelope-109-recapture-{DATE}.md": _render_kv_md(
            "FAZ37 RC-G vs RC-Q Response Envelope 109 Recapture",
            _authoritative_rows(wp4, WP4_FIELDS),
        ),
        ROOT / "evaluation" / "reports" / f"faz37-rc-q-release-controls-targeted-acceptance-recapture-{DATE}.md": _render_kv_md(
            "FAZ37 RC-Q Release Controls Targeted Acceptance Recapture",
            _authoritative_rows(wp5, WP5_FIELDS),
        ),
        ROOT / "evaluation" / "reports" / f"faz37-rc-g-vs-rc-q-full-family-model-visible-surface-parity-recapture-{DATE}.md": _render_kv_md(
            "FAZ37 RC-G vs RC-Q Full-Family Model Visible Surface Parity Recapture",
            _authoritative_rows(wp6, WP6_FIELDS),
        ),
        ROOT / "evaluation" / "reports" / f"faz37-rc-q-release-controls-retention-recapture-{DATE}.md": _render_kv_md(
            "FAZ37 RC-Q Release Controls Retention Recapture",
            _authoritative_rows(wp7, WP7_FIELDS),
        ),
        ROOT / "evaluation" / "reports" / f"faz37-rc-q-repair-truth-summary-{DATE}.md": "\n".join(
            [
                "# FAZ37 RC-Q Repair Truth Summary",
                "",
                f"- matches_faz35_perimeter_truth = `{bool_text(contrast['matches_faz35_perimeter_truth'])}`",
                f"- matches_faz36_failed_repair_truth = `{bool_text(contrast['matches_faz36_failed_repair_truth'])}`",
                f"- matches_neither = `{bool_text(contrast['matches_neither'])}`",
                f"- primary_reason = `{contrast['primary_reason']}`",
                f"- root_cause_class = `{contrast['root_cause_class']}`",
                f"- unexplained_count = `{contrast['unexplained_count']}`",
                f"- official_decision = `{payload['official_decision']}`",
                f"- next_official_work = `{payload['next_official_work']}`",
                "",
            ]
        ),
        ROOT / "reports" / RESULT_REPORT_NAME: _render_result_report(payload),
        ROOT / "docs" / RESULT_REPORT_NAME: _render_result_report(payload),
    }
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ37 official phase package.")
    parser.add_argument("--capture-a-json", type=Path, required=True)
    parser.add_argument("--capture-b-json", type=Path, required=True)
    args = parser.parse_args()

    payload = build_phase_payload(
        capture_a=load_json(args.capture_a_json),
        capture_b=load_json(args.capture_b_json),
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
