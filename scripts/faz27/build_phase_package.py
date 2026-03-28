#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz27_lib import (  # type: ignore
    CONTROL_ROWS,
    DATE,
    DECISION_TO_NEXT_WORK,
    FAIL_BOUNDARY_TRUTH_DRIFT,
    FAIL_INCONCLUSIVE,
    FAIL_UPSTREAM_CONTRACT,
    PASS_DECISION,
    bool_text,
    load_json,
    markdown_table,
    write_json,
    write_text,
)


ROOT = Path(__file__).resolve().parents[2]


CONTROL_TO_ROOT_CAUSE = {
    "mandatory auth": "auth_runtime_mutation",
    "immutable audit logging": "audit_runtime_mutation",
    "persisted PII redaction": "pii_redaction_runtime_mutation",
    "Redis session persistence": "session_runtime_mutation",
    "tokenizer-backed accounting": "token_accounting_runtime_mutation",
    "observability / alerting": "observability_runtime_mutation",
    "API versioning": "api_version_runtime_mutation",
    "process supervision": "supervision_runtime_mutation",
}


def _control_rows_index() -> dict[str, dict[str, Any]]:
    return {row["control_name"]: dict(row) for row in CONTROL_ROWS}


def _normalize_single_or_matrix_payload(
    *,
    payload: dict[str, Any] | None,
    effective_control_set: list[str],
    scenario: str,
    control_name: str | None = None,
) -> dict[str, Any]:
    if payload is None:
        return {"effective_control_set": effective_control_set, "rows": []}
    if isinstance(payload.get("rows"), list):
        return {
            "effective_control_set": list(payload.get("effective_control_set") or effective_control_set),
            "rows": list(payload.get("rows") or []),
        }
    if control_name is None:
        control_name = effective_control_set[0] if effective_control_set else ""
    return {
        "effective_control_set": effective_control_set,
        "rows": [
            {
                "control_name": control_name,
                "scenario": scenario,
                "preprojection_hash_mismatch_count": int(payload["preprojection_hash_mismatch_count"]),
                "raw_answer_hash_mismatch_count": int(payload["raw_answer_hash_mismatch_count"]),
                "response_envelope_hash_mismatch_count": int(payload["response_envelope_hash_mismatch_count"]),
                "runtime_error_count": int(payload["runtime_error_count"]),
            }
        ],
    }


def build_phase_payload(
    *,
    materialized: dict[str, Any],
    ladder: dict[str, Any],
    additive_report: dict[str, Any] | None,
    subtractive_report: dict[str, Any] | None,
    interaction_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    reference_pack = materialized["reference_pack"]
    current_authority = materialized["current_authority_gate"]
    upstream_equality = materialized["upstream_equality_gate"]
    boundary_summary = materialized["boundary_summary"]
    retention = materialized["retention_matrix"]
    frontier_freeze = materialized["frontier_freeze"]
    control_index = _control_rows_index()

    authoritative_boundary_truth_pass = (
        boundary_summary["faz1_50_mismatch_count"] == 16
        and boundary_summary["v2_95_mismatch_count"] == 56
        and boundary_summary["v3_170_mismatch_count"] == 94
        and boundary_summary["model_request_payload_hash_mismatch_count"] == 0
        and boundary_summary["retrieval_request_hash_mismatch_count"] == 0
        and boundary_summary["assembled_context_hash_mismatch_count"] == 0
        and boundary_summary["preprojection_hash_mismatch_count"] == 166
        and boundary_summary["raw_answer_hash_mismatch_count"] == 166
        and boundary_summary["first_break_stage_assigned_count"] == 166
        and boundary_summary["primary_reason_assigned_count"] == 166
        and boundary_summary["unexplained_count"] == 0
        and boundary_summary["frontier_total"] == 166
    )

    wp1_pass = (
        reference_pack["reference_pack_integrity_pass"] is True
        and reference_pack["reference_pack_contradiction_count"] == 0
    )
    wp2_pass = (
        current_authority["control_pair_authority_match"] is True
        and current_authority["current_authority_contract_breach"] is False
        and current_authority["surface_breach_from_history_reintroduced"] is False
        and current_authority["current_canonical_authority_adopted"] is True
        and current_authority["control_pair_runtime_error_count"] == 0
        and upstream_equality["model_request_payload_hash_mismatch_count"] == 0
        and upstream_equality["retrieval_request_hash_mismatch_count"] == 0
        and upstream_equality["assembled_context_hash_mismatch_count"] == 0
        and upstream_equality["runtime_error_count"] == 0
    )
    wp3_pass = authoritative_boundary_truth_pass
    wp4_pass = (
        ladder["first_break_control"] is not None
        and ladder["first_break_step"] is not None
        and ladder["first_break_stage"] is not None
        and int(ladder["first_break_count"]) > 0
        and int(ladder["unexplained_count"]) == 0
    )

    effective_control_set = list(ladder.get("effective_control_set", []))
    single_control_root_cause_found = bool(ladder.get("single_control_root_cause_found"))
    interaction_root_cause_found = bool(ladder.get("interaction_root_cause_found"))
    root_cause_class = ""
    primary_reason = ""
    if effective_control_set:
        if len(effective_control_set) == 1:
            root_cause_class = CONTROL_TO_ROOT_CAUSE.get(effective_control_set[0], "")
            primary_reason = f"{effective_control_set[0]} first breaks at {ladder['first_break_stage']}"
        elif interaction_payload and interaction_payload.get("root_cause_class"):
            root_cause_class = str(interaction_payload["root_cause_class"])
            primary_reason = str(interaction_payload.get("primary_reason") or "")

    wp5_unexplained_count = 0
    if not effective_control_set or not root_cause_class or not primary_reason:
        wp5_unexplained_count = 1
    wp5_pass = wp5_unexplained_count == 0

    operational_rows = []
    unexplained_control_count = 0
    retention_rows = {row["control"]: bool(row["pass"]) for row in retention["control_rows"]}
    for row in CONTROL_ROWS:
        control_name = row["control_name"]
        answer_path_touch_observed = control_name in effective_control_set
        primary_reason_value = ""
        if control_name in effective_control_set:
            primary_reason_value = f"effective_control_first_break={ladder['first_break_stage']}"
        elif control_name == "persisted PII redaction" and retention["pii_leak_found"]:
            primary_reason_value = "persisted_redaction_retention_open"
        elif control_name == "one-command release smoke" and retention["release_smoke_gap_found"]:
            primary_reason_value = "release_smoke_refusal_probe_gap"
        elif control_name == "tokenizer-backed accounting" and retention["token_accounting_fallback_found"]:
            primary_reason_value = "token_accounting_retention_open"
        elif control_name == "backup / restore" and retention["backup_restore_gap_found"]:
            primary_reason_value = "backup_restore_retention_open"
        else:
            primary_reason_value = "no_incremental_answer_path_delta_observed"

        if not primary_reason_value:
            unexplained_control_count += 1

        operational_rows.append(
            {
                "control_name": control_name,
                "control_class": row["control_class"],
                "should_touch_answer_path": bool(row["should_touch_answer_path"]),
                "answer_path_touch_observed": answer_path_touch_observed,
                "closure_status": "pass" if retention_rows.get(control_name, True) else "fail",
                "retained_after_family_eval": retention["retained_after_family_eval"],
                "retained_after_restart": retention["retained_after_restart"],
                "retained_after_restore": retention["retained_after_restore"],
                "primary_reason": primary_reason_value,
            }
        )

    wp6_pass = (
        retention["must_close_release_controls_count"] == 10
        and unexplained_control_count == 0
    )

    if not wp2_pass:
        official_decision = FAIL_UPSTREAM_CONTRACT
    elif not wp3_pass:
        official_decision = FAIL_BOUNDARY_TRUTH_DRIFT
    elif not wp4_pass or not wp5_pass or not wp6_pass:
        official_decision = FAIL_INCONCLUSIVE
    else:
        official_decision = PASS_DECISION
    next_official_work = DECISION_TO_NEXT_WORK[official_decision]

    additive_payload = _normalize_single_or_matrix_payload(
        payload=additive_report,
        effective_control_set=effective_control_set,
        scenario="single_control_additive_from_rc_g",
    )

    subtractive_payload = _normalize_single_or_matrix_payload(
        payload=subtractive_report,
        effective_control_set=effective_control_set,
        scenario="single_control_subtractive_from_rc_n",
    )

    interaction_payload = interaction_payload or {
        "effective_control_set": effective_control_set,
        "rows": [],
        "pairwise_interaction_only_for_effective_controls": True,
        "root_cause_class": root_cause_class,
        "primary_reason": primary_reason,
        "unexplained_count": 0,
    }

    boundary_root_cause_summary = {
        "first_break_control": ladder["first_break_control"],
        "first_break_step": ladder["first_break_step"],
        "first_break_stage": ladder["first_break_stage"],
        "first_break_count": ladder["first_break_count"],
        "dominant_control": ladder["dominant_control"],
        "dominant_stage": ladder["dominant_stage"],
        "effective_control_set": effective_control_set,
        "single_control_root_cause_found": single_control_root_cause_found,
        "interaction_root_cause_found": interaction_root_cause_found,
        "root_cause_class": root_cause_class,
        "primary_reason": primary_reason,
        "unexplained_count": int(ladder["unexplained_count"]) + wp5_unexplained_count,
    }

    return {
        "reference_pack": reference_pack,
        "current_authority_gate": current_authority,
        "upstream_equality_gate": upstream_equality,
        "boundary_summary": boundary_summary,
        "frontier_freeze": frontier_freeze,
        "ladder": ladder,
        "boundary_root_cause_summary": boundary_root_cause_summary,
        "additive_payload": additive_payload,
        "subtractive_payload": subtractive_payload,
        "interaction_payload": interaction_payload,
        "operational_rows": operational_rows,
        "retention_matrix": retention,
        "wp_statuses": {
            "WP-1": "PASS" if wp1_pass else "FAIL",
            "WP-2": "PASS" if wp2_pass else "FAIL",
            "WP-3": "PASS" if wp3_pass else "FAIL",
            "WP-4": "PASS" if wp4_pass else "FAIL",
            "WP-5": "PASS" if wp5_pass else "FAIL",
            "WP-6": "PASS" if wp6_pass else "FAIL",
            "WP-7": "PASS" if official_decision == PASS_DECISION else "FAIL",
        },
        "official_decision": official_decision,
        "next_official_work": next_official_work,
        "unexplained_control_count": unexplained_control_count,
    }


def render_outputs(payload: dict[str, Any]) -> dict[Path, str | dict[str, Any]]:
    reference_pack = payload["reference_pack"]
    current = payload["current_authority_gate"]
    upstream = payload["upstream_equality_gate"]
    boundary = payload["boundary_summary"]
    ladder = payload["ladder"]
    root = payload["boundary_root_cause_summary"]
    retention = payload["retention_matrix"]
    operational_rows = payload["operational_rows"]
    wp = payload["wp_statuses"]

    additive = payload["additive_payload"]
    subtractive = payload["subtractive_payload"]
    interaction = payload["interaction_payload"]

    additive_lines = [
        "# FAZ27 RC-N Control Additive Matrix",
        "",
        f"- effective_control_set = `{', '.join(additive['effective_control_set'])}`",
        "",
        *markdown_table(
            [
                ("control_name", "control_name"),
                ("scenario", "scenario"),
                ("preprojection_hash_mismatch_count", "preprojection"),
                ("raw_answer_hash_mismatch_count", "raw_answer"),
                ("response_envelope_hash_mismatch_count", "response_envelope"),
                ("runtime_error_count", "runtime_error"),
            ],
            additive["rows"],
        ),
        "",
    ]

    subtractive_lines = [
        "# FAZ27 RC-N Control Subtractive Matrix",
        "",
        f"- effective_control_set = `{', '.join(subtractive['effective_control_set'])}`",
        "",
        *markdown_table(
            [
                ("control_name", "control_name"),
                ("scenario", "scenario"),
                ("preprojection_hash_mismatch_count", "preprojection"),
                ("raw_answer_hash_mismatch_count", "raw_answer"),
                ("response_envelope_hash_mismatch_count", "response_envelope"),
                ("runtime_error_count", "runtime_error"),
            ],
            subtractive["rows"],
        ),
        "",
    ]

    interaction_lines = [
        "# FAZ27 RC-N Control Interaction Matrix",
        "",
        f"- effective_control_set = `{', '.join(interaction['effective_control_set'])}`",
        f"- pairwise_interaction_only_for_effective_controls = `{'true' if interaction['pairwise_interaction_only_for_effective_controls'] else 'false'}`",
        f"- root_cause_class = `{interaction['root_cause_class']}`",
        f"- primary_reason = `{interaction['primary_reason']}`",
        f"- unexplained_count = `{interaction['unexplained_count']}`",
        "",
        *markdown_table(
            [
                ("control_pair", "control_pair"),
                ("preprojection_hash_mismatch_count", "preprojection"),
                ("raw_answer_hash_mismatch_count", "raw_answer"),
                ("response_envelope_hash_mismatch_count", "response_envelope"),
                ("runtime_error_count", "runtime_error"),
            ],
            interaction["rows"],
        ),
        "",
    ]

    operational_lines = [
        "# FAZ27 RC-N Operational Controls Audit",
        "",
        f"- must_close_release_controls_count = `{retention['must_close_release_controls_count']}`",
        f"- unexplained_control_count = `{payload['unexplained_control_count']}`",
        "",
        *markdown_table(
            [
                ("control_name", "control_name"),
                ("control_class", "control_class"),
                ("should_touch_answer_path", "should_touch_answer_path"),
                ("answer_path_touch_observed", "answer_path_touch_observed"),
                ("closure_status", "closure_status"),
                ("primary_reason", "primary_reason"),
            ],
            operational_rows,
        ),
        "",
    ]

    root_cause_lines = [
        "# FAZ27 RC-N Boundary Root Cause Summary",
        "",
        f"- first_break_control = `{root['first_break_control']}`",
        f"- first_break_step = `{root['first_break_step']}`",
        f"- first_break_stage = `{root['first_break_stage']}`",
        f"- first_break_count = `{root['first_break_count']}`",
        f"- dominant_control = `{root['dominant_control']}`",
        f"- dominant_stage = `{root['dominant_stage']}`",
        f"- effective_control_set = `{', '.join(root['effective_control_set'])}`",
        f"- single_control_root_cause_found = `{bool_text(root['single_control_root_cause_found'])}`",
        f"- interaction_root_cause_found = `{bool_text(root['interaction_root_cause_found'])}`",
        f"- root_cause_class = `{root['root_cause_class']}`",
        f"- primary_reason = `{root['primary_reason']}`",
        f"- unexplained_count = `{root['unexplained_count']}`",
        "",
    ]

    reconciliation_lines = [
        "# FAZ27 RC-N Boundary Reconciliation",
        "",
        f"- reference_pack_integrity_pass = `{bool_text(reference_pack['reference_pack_integrity_pass'])}`",
        f"- current_authority_contract_breach = `{bool_text(current['current_authority_contract_breach'])}`",
        f"- model_request_payload_hash_mismatch_count = `{upstream['model_request_payload_hash_mismatch_count']}`",
        f"- retrieval_request_hash_mismatch_count = `{upstream['retrieval_request_hash_mismatch_count']}`",
        f"- assembled_context_hash_mismatch_count = `{upstream['assembled_context_hash_mismatch_count']}`",
        f"- frontier_total = `{boundary['frontier_total']}`",
        f"- first_break_control = `{root['first_break_control']}`",
        f"- root_cause_class = `{root['root_cause_class']}`",
        f"- official_decision = `{payload['official_decision']}`",
        "",
    ]

    steering_lines = [
        "# FAZ27 Steering Decision Table",
        "",
        *markdown_table([("wp", "wp"), ("status", "status")], [{"wp": key, "status": value} for key, value in wp.items()]),
        "",
        f"- resmi_karar = `{payload['official_decision']}`",
        f"- sonraki_resmi_is = `{payload['next_official_work']}`",
        "",
    ]

    report_lines = [
        "# FAZ27 RC-N Release Controls Boundary Forensics Under Canonical Current Authority Raporu",
        "",
        "## Yonetici Ozeti",
        "",
        f"- resmi_karar = `{payload['official_decision']}`",
        f"- sonraki_resmi_is = `{payload['next_official_work']}`",
        "",
        "## Reference Pack Ozeti",
        "",
        f"- reference_pack_integrity_pass = `{bool_text(reference_pack['reference_pack_integrity_pass'])}`",
        f"- reference_pack_contradiction_count = `{reference_pack['reference_pack_contradiction_count']}`",
        f"- quality_reference_ref = `{reference_pack['quality_reference_ref']}`",
        f"- canonical_current_authority_ref = `{reference_pack['canonical_current_authority_ref']}`",
        f"- release_controls_legacy_ref = `{reference_pack['release_controls_legacy_ref']}`",
        f"- archival_closure_ref = `{reference_pack['archival_closure_ref']}`",
        "",
        "## RC-N Build Contract Ozeti",
        "",
        f"- candidate_id = `{reference_pack['candidate_id']}`",
        f"- base_candidate = `{reference_pack['base_candidate']}`",
        f"- control_candidate = `{reference_pack['control_candidate']}`",
        f"- allowed_diff_surface = `{reference_pack['allowed_diff_surface']}`",
        f"- answer_path_delta_allowed = `{bool_text(reference_pack['answer_path_delta_allowed'])}`",
        "",
        "## Current Authority ve Upstream Equality Ozeti",
        "",
        f"- control_pair_authority_match = `{bool_text(current['control_pair_authority_match'])}`",
        f"- current_authority_contract_breach = `{bool_text(current['current_authority_contract_breach'])}`",
        f"- surface_breach_from_history_reintroduced = `{bool_text(current['surface_breach_from_history_reintroduced'])}`",
        f"- current_canonical_authority_adopted = `{bool_text(current['current_canonical_authority_adopted'])}`",
        f"- control_pair_runtime_error_count = `{current['control_pair_runtime_error_count']}`",
        f"- model_request_payload_hash_mismatch_count = `{upstream['model_request_payload_hash_mismatch_count']}`",
        f"- retrieval_request_hash_mismatch_count = `{upstream['retrieval_request_hash_mismatch_count']}`",
        f"- assembled_context_hash_mismatch_count = `{upstream['assembled_context_hash_mismatch_count']}`",
        "",
        "## Full-Family Boundary Summary",
        "",
        f"- faz1_50_mismatch_count = `{boundary['faz1_50_mismatch_count']}`",
        f"- v2_95_mismatch_count = `{boundary['v2_95_mismatch_count']}`",
        f"- v3_170_mismatch_count = `{boundary['v3_170_mismatch_count']}`",
        f"- preprojection_hash_mismatch_count = `{boundary['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{boundary['raw_answer_hash_mismatch_count']}`",
        f"- response_envelope_hash_mismatch_count = `{boundary['response_envelope_hash_mismatch_count']}`",
        f"- first_break_stage_assigned_count = `{boundary['first_break_stage_assigned_count']}`",
        f"- primary_reason_assigned_count = `{boundary['primary_reason_assigned_count']}`",
        f"- unexplained_count = `{boundary['unexplained_count']}`",
        f"- frontier_total = `{boundary['frontier_total']}`",
        "",
        "## Runtime-Boundary Bind Ladder Ozeti",
        "",
        f"- first_break_control = `{root['first_break_control']}`",
        f"- first_break_step = `{root['first_break_step']}`",
        f"- first_break_stage = `{root['first_break_stage']}`",
        f"- first_break_count = `{root['first_break_count']}`",
        f"- dominant_control = `{root['dominant_control']}`",
        f"- dominant_stage = `{root['dominant_stage']}`",
        "",
        "## Additive / Subtractive / Interaction Isolation Ozeti",
        "",
        f"- effective_control_set = `{', '.join(root['effective_control_set'])}`",
        f"- single_control_root_cause_found = `{bool_text(root['single_control_root_cause_found'])}`",
        f"- interaction_root_cause_found = `{bool_text(root['interaction_root_cause_found'])}`",
        f"- root_cause_class = `{root['root_cause_class']}`",
        f"- primary_reason = `{root['primary_reason']}`",
        f"- unexplained_count = `{root['unexplained_count']}`",
        "",
        "## Operational Controls Audit Ozeti",
        "",
        f"- must_close_release_controls_count = `{retention['must_close_release_controls_count']}`",
        f"- unexplained_control_count = `{payload['unexplained_control_count']}`",
        "",
        "## Release Controls Retention Ozeti",
        "",
        f"- must_close_release_controls_pass = `{bool_text(retention['must_close_release_controls_pass'])}`",
        f"- must_close_release_controls_count = `{retention['must_close_release_controls_count']}`",
        f"- retained_after_family_eval = `{bool_text(retention['retained_after_family_eval'])}`",
        f"- retained_after_restart = `{bool_text(retention['retained_after_restart'])}`",
        f"- retained_after_restore = `{bool_text(retention['retained_after_restore'])}`",
        f"- pii_leak_found = `{bool_text(retention['pii_leak_found'])}`",
        f"- token_accounting_fallback_found = `{bool_text(retention['token_accounting_fallback_found'])}`",
        f"- release_smoke_gap_found = `{bool_text(retention['release_smoke_gap_found'])}`",
        f"- auth_bypass_found = `{bool_text(retention['auth_bypass_found'])}`",
        f"- audit_write_loss_found = `{bool_text(retention['audit_write_loss_found'])}`",
        f"- redis_continuity_break_found = `{bool_text(retention['redis_continuity_break_found'])}`",
        f"- observability_gap_found = `{bool_text(retention['observability_gap_found'])}`",
        f"- api_versioning_gap_found = `{bool_text(retention['api_versioning_gap_found'])}`",
        f"- supervision_gap_found = `{bool_text(retention['supervision_gap_found'])}`",
        f"- backup_restore_gap_found = `{bool_text(retention['backup_restore_gap_found'])}`",
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
        f"- coordination/faz27-official-implementation-plan-{DATE}.md",
        f"- coordination/faz27-steering-decision-table-{DATE}.md",
        f"- coordination/faz27-rc-n-boundary-forensics-contract-{DATE}.md",
        f"- coordination/faz27-rc-n-release-controls-classification-{DATE}.md",
        f"- coordination/faz27-rc-n-runtime-boundary-bind-order-{DATE}.md",
        f"- coordination/faz27-rc-n-boundary-frontier-freeze-{DATE}.md",
        f"- coordination/faz27-rc-n-boundary-reconciliation-{DATE}.md",
        f"- evaluation/reports/faz27-rc-g-vs-rc-j-current-authority-check-{DATE}.md",
        f"- evaluation/reports/faz27-rc-g-vs-rc-n-upstream-equality-gate-{DATE}.md",
        f"- evaluation/reports/faz27-rc-g-vs-rc-n-full-family-boundary-summary-{DATE}.md",
        f"- evaluation/reports/faz27-rc-n-runtime-boundary-bind-ladder-{DATE}.md",
        f"- evaluation/reports/faz27-rc-n-control-additive-matrix-{DATE}.md",
        f"- evaluation/reports/faz27-rc-n-control-subtractive-matrix-{DATE}.md",
        f"- evaluation/reports/faz27-rc-n-control-interaction-matrix-{DATE}.md",
        f"- evaluation/reports/faz27-rc-n-operational-controls-audit-{DATE}.md",
        f"- evaluation/reports/faz27-rc-n-release-controls-retention-matrix-{DATE}.md",
        f"- evaluation/reports/faz27-rc-n-boundary-root-cause-summary-{DATE}.md",
        f"- reports/FAZ27-RC-N-RELEASE-CONTROLS-BOUNDARY-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-{DATE}.md",
        "",
    ]

    return {
        ROOT / "coordination" / f"faz27-steering-decision-table-{DATE}.md": "\n".join(steering_lines),
        ROOT / "coordination" / f"faz27-rc-n-boundary-reconciliation-{DATE}.md": "\n".join(reconciliation_lines),
        ROOT / "evaluation" / "reports" / f"faz27-rc-n-control-additive-matrix-{DATE}.md": "\n".join(additive_lines),
        ROOT / "evaluation" / "reports" / f"faz27-rc-n-control-subtractive-matrix-{DATE}.md": "\n".join(subtractive_lines),
        ROOT / "evaluation" / "reports" / f"faz27-rc-n-control-interaction-matrix-{DATE}.md": "\n".join(interaction_lines),
        ROOT / "evaluation" / "reports" / f"faz27-rc-n-operational-controls-audit-{DATE}.md": "\n".join(operational_lines),
        ROOT / "evaluation" / "reports" / f"faz27-rc-n-boundary-root-cause-summary-{DATE}.md": "\n".join(root_cause_lines),
        ROOT / "reports" / f"FAZ27-RC-N-RELEASE-CONTROLS-BOUNDARY-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-{DATE}.md": "\n".join(report_lines),
        ROOT / "coordination" / f"faz27-steering-decision-table-{DATE}.json": payload,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ27 phase package.")
    parser.add_argument("--materialized-json", type=Path, required=True)
    parser.add_argument("--ladder-json", type=Path, required=True)
    parser.add_argument("--additive-report-json", type=Path)
    parser.add_argument("--subtractive-report-json", type=Path)
    parser.add_argument("--interaction-json", type=Path)
    args = parser.parse_args()

    payload = build_phase_payload(
        materialized=load_json(args.materialized_json),
        ladder=load_json(args.ladder_json),
        additive_report=load_json(args.additive_report_json) if args.additive_report_json else None,
        subtractive_report=load_json(args.subtractive_report_json) if args.subtractive_report_json else None,
        interaction_payload=load_json(args.interaction_json) if args.interaction_json else None,
    )
    outputs = render_outputs(payload)
    for path, content in outputs.items():
        if isinstance(content, dict):
            write_json(path, content)
        else:
            write_text(path, content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
