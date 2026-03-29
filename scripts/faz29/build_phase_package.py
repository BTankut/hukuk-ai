#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz29_lib import (  # type: ignore
    ACCEPTANCE_EXPECTED,
    BOUNDARY_EXPECTED,
    DATE,
    DECISION_TO_NEXT_WORK,
    FAIL_INCONCLUSIVE,
    FAIL_UNSTABLE,
    FAIL_UPSTREAM_EQUALITY,
    PASS_DECISION,
    RETENTION_EXPECTED,
    SPILLOVER_EXPECTED,
    bool_text,
    load_json,
    markdown_table,
    stable_hash,
    write_json,
    write_text,
)


ROOT = Path(__file__).resolve().parents[2]
RESULT_REPORT_NAME = (
    f"FAZ29-RC-O-RELEASE-CONTROLS-BOUNDARY-REPAIR-RECAPTURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-{DATE}.md"
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
    "input_pack_count",
    "remaining_mismatch_count",
    "repair_delta_record_count",
    "faz1_50_mismatch_count",
    "v2_95_mismatch_count",
    "v3_170_mismatch_count",
    "preprojection_hash_mismatch_count",
    "raw_answer_hash_mismatch_count",
    "response_envelope_hash_mismatch_count",
    "first_break_stage_assigned_count",
    "primary_reason_assigned_count",
    "runtime_error_count",
    "unexplained_count",
]

WP4_FIELDS = [
    "record_count",
    "mismatch_count",
    "preprojection_hash_mismatch_count",
    "raw_answer_hash_mismatch_count",
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
    "runtime_error_count",
    "unexplained_count",
]

WP6_FIELDS = [
    "retained_after_family_eval",
    "retained_after_restart",
    "retained_after_restore",
    "answer_path_delta_reintroduced",
    "runtime_error_count",
    "unexplained_count",
]

ARTEFACT_LIST = [
    f"coordination/faz29-official-implementation-plan-{DATE}.md",
    f"coordination/faz29-steering-decision-table-{DATE}.md",
    f"coordination/faz29-release-controls-reference-pack-{DATE}.md",
    f"coordination/faz29-rc-o-recapture-contract-{DATE}.md",
    f"coordination/faz29-rc-o-boundary-frontier-166-freeze-{DATE}.md",
    f"coordination/faz29-rc-o-repair-delta-14-freeze-{DATE}.md",
    f"coordination/faz29-rc-o-spillover-guard-24-freeze-{DATE}.md",
    f"coordination/faz29-rc-o-failing-control-triplet-{DATE}.md",
    f"coordination/faz29-rc-o-retention-recapture-contract-{DATE}.md",
    f"coordination/faz29-rc-o-boundary-repair-truth-reconciliation-{DATE}.md",
    f"coordination/faz29-rc-o-manifest-{DATE}.json",
    f"evaluation/reports/faz29-rc-g-vs-rc-j-current-authority-check-{DATE}.md",
    f"evaluation/reports/faz29-rc-g-vs-rc-o-upstream-equality-gate-{DATE}.md",
    f"evaluation/reports/faz29-rc-n-vs-rc-o-repair-delta-summary-{DATE}.md",
    f"evaluation/reports/faz29-rc-g-vs-rc-o-boundary-frontier-166-recapture-{DATE}.md",
    f"evaluation/reports/faz29-rc-g-vs-rc-o-spillover-guard-24-recapture-{DATE}.md",
    f"evaluation/reports/faz29-rc-o-failing-controls-triplet-recapture-{DATE}.md",
    f"evaluation/reports/faz29-rc-o-retention-recapture-{DATE}.md",
    f"evaluation/reports/faz29-rc-o-boundary-repair-truth-summary-{DATE}.md",
    f"reports/{RESULT_REPORT_NAME}",
]


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
    for key, value in section.items():
        if ("runtime_error_count" in key or key == "unexplained_count") and int(value) > 0:
            return True
    return False


def build_phase_payload(*, materialized: dict[str, Any], capture_a: dict[str, Any], capture_b: dict[str, Any]) -> dict[str, Any]:
    reference_pack = materialized["reference_pack"]
    manifest = materialized["manifest"]

    wp2 = _reconcile_section(capture_a["wp2"], capture_b["wp2"], WP2_FIELDS)
    wp3 = _reconcile_section(capture_a["wp3"], capture_b["wp3"], WP3_FIELDS)
    wp4 = _reconcile_section(capture_a["wp4"], capture_b["wp4"], WP4_FIELDS)
    wp5 = _reconcile_section(capture_a["wp5"], capture_b["wp5"], WP5_FIELDS)
    wp6 = _reconcile_section(capture_a["wp6"], capture_b["wp6"], WP6_FIELDS)

    wp1_pass = (
        reference_pack["reference_pack_integrity_pass"] is True
        and reference_pack["reference_pack_contradiction_count"] == 0
        and reference_pack["quality_reference_ref"] == "FAZ6"
        and reference_pack["canonical_current_authority_ref"] == "FAZ21"
        and reference_pack["release_controls_legacy_ref"] == "FAZ26"
        and reference_pack["archival_closure_ref"] == "FAZ24"
        and manifest["candidate_id"] == "RC-O"
        and manifest["base_candidate"] == "RC-G"
        and manifest["control_candidate"] == "RC-J"
        and manifest["forensic_reference_candidate"] == "RC-N"
        and manifest["allowed_diff_surface"] == "release_controls_boundary_only"
        and manifest["answer_path_delta_allowed"] is False
        and manifest["candidate_status"] == "frozen_failed_repair_candidate"
        and manifest["promotable"] is False
        and manifest["repairable"] is False
        and manifest["current_evaluable"] is True
        and manifest["cutover_authorized"] is False
        and manifest["pilot_authorized"] is False
    )

    wp2_pass = (
        wp2["capture_stability_match"] is True
        and _section_matches(
            wp2,
            {
                "control_pair_authority_match": True,
                "current_authority_contract_breach": False,
                "surface_breach_from_history_reintroduced": False,
                "current_canonical_authority_adopted": True,
                "control_pair_runtime_error_count": 0,
                "model_request_payload_hash_mismatch_count": 0,
                "retrieval_request_hash_mismatch_count": 0,
                "assembled_context_hash_mismatch_count": 0,
                "runtime_error_count": 0,
            },
            WP2_FIELDS,
        )
    )

    wp3_exact = _section_matches(wp3, BOUNDARY_EXPECTED, WP3_FIELDS)
    wp4_exact = _section_matches(wp4, SPILLOVER_EXPECTED, WP4_FIELDS)
    wp5_exact = _section_matches(wp5, ACCEPTANCE_EXPECTED, WP5_FIELDS)
    wp6_exact = _section_matches(wp6, RETENTION_EXPECTED, WP6_FIELDS)

    wp3_inconclusive = (not wp3["capture_stability_match"]) or _section_runtime_or_unexplained(wp3)
    wp4_inconclusive = (not wp4["capture_stability_match"]) or _section_runtime_or_unexplained(wp4)
    wp5_inconclusive = (not wp5["capture_stability_match"]) or _section_runtime_or_unexplained(wp5)
    wp6_inconclusive = (not wp6["capture_stability_match"]) or _section_runtime_or_unexplained(wp6)

    wp3_pass = wp3["capture_stability_match"] is True and wp3_exact
    wp4_pass = wp4["capture_stability_match"] is True and wp4_exact
    wp5_pass = wp5["capture_stability_match"] is True and wp5_exact
    wp6_pass = wp6["capture_stability_match"] is True and wp6_exact

    if not wp1_pass:
        official_decision = FAIL_INCONCLUSIVE
    elif not wp2_pass:
        official_decision = FAIL_UPSTREAM_EQUALITY
    elif wp3_inconclusive or wp4_inconclusive or wp5_inconclusive or wp6_inconclusive:
        official_decision = FAIL_INCONCLUSIVE
    elif not (wp3_pass and wp4_pass and wp5_pass and wp6_pass):
        official_decision = FAIL_UNSTABLE
    else:
        official_decision = PASS_DECISION

    payload = {
        "reference_pack": reference_pack,
        "manifest": manifest,
        "capture_a": capture_a,
        "capture_b": capture_b,
        "wp2": wp2,
        "wp3": wp3,
        "wp4": wp4,
        "wp5": wp5,
        "wp6": wp6,
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
        "next_official_work": DECISION_TO_NEXT_WORK[official_decision],
    }
    payload["report_hash"] = stable_hash(_json_safe(payload))
    return payload


def _section_lines(title: str, payload: dict[str, Any], fields: list[str]) -> list[str]:
    lines = [f"## {title}", ""]
    lines.append(f"- capture_stability_match = `{bool_text(payload['capture_stability_match'])}`")
    lines.append(f"- capture_a_vs_capture_b_mismatch_count = `{payload['capture_a_vs_capture_b_mismatch_count']}`")
    lines.append(
        f"- capture_a_vs_capture_b_runtime_error_count = `{payload['capture_a_vs_capture_b_runtime_error_count']}`"
    )
    for field in fields:
        value = payload[field]
        rendered = bool_text(value) if isinstance(value, bool) else value
        lines.append(f"- {field} = `{rendered}`")
    lines.append("")
    return lines


def render_outputs(payload: dict[str, Any]) -> dict[Path, str | dict[str, Any]]:
    ref = payload["reference_pack"]
    manifest = payload["manifest"]
    wp2 = payload["wp2"]
    wp3 = payload["wp3"]
    wp4 = payload["wp4"]
    wp5 = payload["wp5"]
    wp6 = payload["wp6"]
    wp = payload["wp_statuses"]
    official_decision = payload["official_decision"]
    next_official_work = payload["next_official_work"]

    steering_rows = [
        {"wp": "WP-1", "status": wp["WP-1"], "blocking_decision": FAIL_INCONCLUSIVE},
        {"wp": "WP-2", "status": wp["WP-2"], "blocking_decision": FAIL_UPSTREAM_EQUALITY},
        {"wp": "WP-3", "status": wp["WP-3"], "blocking_decision": FAIL_UNSTABLE},
        {"wp": "WP-4", "status": wp["WP-4"], "blocking_decision": FAIL_UNSTABLE},
        {"wp": "WP-5", "status": wp["WP-5"], "blocking_decision": FAIL_UNSTABLE},
        {"wp": "WP-6", "status": wp["WP-6"], "blocking_decision": FAIL_UNSTABLE},
        {"wp": "WP-7", "status": wp["WP-7"], "blocking_decision": official_decision},
    ]

    steering_lines = [
        "# FAZ29 Steering Decision Table",
        "",
        *markdown_table(
            [("wp", "wp"), ("status", "status"), ("blocking_decision", "blocking_decision")],
            steering_rows,
        ),
        "",
    ]

    reconciliation_lines = [
        "# FAZ29 RC-O Boundary Repair Truth Reconciliation",
        "",
        f"- resmi_karar = `{official_decision}`",
        f"- sonraki_resmi_is = `{next_official_work}`",
        f"- wp2_capture_stability_match = `{bool_text(wp2['capture_stability_match'])}`",
        f"- wp3_capture_stability_match = `{bool_text(wp3['capture_stability_match'])}`",
        f"- wp4_capture_stability_match = `{bool_text(wp4['capture_stability_match'])}`",
        f"- wp5_capture_stability_match = `{bool_text(wp5['capture_stability_match'])}`",
        f"- wp6_capture_stability_match = `{bool_text(wp6['capture_stability_match'])}`",
        "",
    ]

    current_authority_lines = [
        "# FAZ29 RC-G vs RC-J Current Authority Check",
        "",
        f"- capture_stability_match = `{bool_text(wp2['capture_stability_match'])}`",
        f"- capture_a_vs_capture_b_mismatch_count = `{wp2['capture_a_vs_capture_b_mismatch_count']}`",
        f"- capture_a_vs_capture_b_runtime_error_count = `{wp2['capture_a_vs_capture_b_runtime_error_count']}`",
        f"- control_pair_authority_match = `{bool_text(wp2['control_pair_authority_match'])}`",
        f"- current_authority_contract_breach = `{bool_text(wp2['current_authority_contract_breach'])}`",
        f"- surface_breach_from_history_reintroduced = `{bool_text(wp2['surface_breach_from_history_reintroduced'])}`",
        f"- current_canonical_authority_adopted = `{bool_text(wp2['current_canonical_authority_adopted'])}`",
        f"- control_pair_runtime_error_count = `{wp2['control_pair_runtime_error_count']}`",
        "",
    ]

    upstream_lines = [
        "# FAZ29 RC-G vs RC-O Upstream Equality Gate",
        "",
        f"- capture_stability_match = `{bool_text(wp2['capture_stability_match'])}`",
        f"- capture_a_vs_capture_b_mismatch_count = `{wp2['capture_a_vs_capture_b_mismatch_count']}`",
        f"- capture_a_vs_capture_b_runtime_error_count = `{wp2['capture_a_vs_capture_b_runtime_error_count']}`",
        f"- model_request_payload_hash_mismatch_count = `{wp2['model_request_payload_hash_mismatch_count']}`",
        f"- retrieval_request_hash_mismatch_count = `{wp2['retrieval_request_hash_mismatch_count']}`",
        f"- assembled_context_hash_mismatch_count = `{wp2['assembled_context_hash_mismatch_count']}`",
        f"- runtime_error_count = `{wp2['runtime_error_count']}`",
        "",
    ]

    repair_delta_lines = [
        "# FAZ29 RC-N vs RC-O Repair Delta Summary",
        "",
        f"- capture_stability_match = `{bool_text(wp3['capture_stability_match'])}`",
        f"- capture_a_vs_capture_b_mismatch_count = `{wp3['capture_a_vs_capture_b_mismatch_count']}`",
        f"- capture_a_vs_capture_b_runtime_error_count = `{wp3['capture_a_vs_capture_b_runtime_error_count']}`",
        f"- input_pack_count = `{wp3['input_pack_count']}`",
        f"- remaining_mismatch_count = `{wp3['remaining_mismatch_count']}`",
        f"- repair_delta_record_count = `{wp3['repair_delta_record_count']}`",
        "",
    ]

    boundary_lines = [
        "# FAZ29 RC-G vs RC-O Boundary Frontier 166 Recapture",
        "",
        *[f"- {field} = `{bool_text(wp3[field]) if isinstance(wp3[field], bool) else wp3[field]}`" for field in ["capture_stability_match", "capture_a_vs_capture_b_mismatch_count", "capture_a_vs_capture_b_runtime_error_count", *WP3_FIELDS]],
        "",
    ]

    spillover_lines = [
        "# FAZ29 RC-G vs RC-O Spillover Guard 24 Recapture",
        "",
        *[f"- {field} = `{bool_text(wp4[field]) if isinstance(wp4[field], bool) else wp4[field]}`" for field in ["capture_stability_match", "capture_a_vs_capture_b_mismatch_count", "capture_a_vs_capture_b_runtime_error_count", *WP4_FIELDS]],
        "",
    ]

    acceptance_lines = [
        "# FAZ29 RC-O Failing Controls Triplet Recapture",
        "",
        *[
            f"- {field} = `{bool_text(wp5[field]) if isinstance(wp5[field], bool) else wp5[field]}`"
            for field in ["capture_stability_match", "capture_a_vs_capture_b_mismatch_count", "capture_a_vs_capture_b_runtime_error_count", *WP5_FIELDS]
        ],
        "",
    ]

    retention_lines = [
        "# FAZ29 RC-O Retention Recapture",
        "",
        *[
            f"- {field} = `{bool_text(wp6[field]) if isinstance(wp6[field], bool) else wp6[field]}`"
            for field in ["capture_stability_match", "capture_a_vs_capture_b_mismatch_count", "capture_a_vs_capture_b_runtime_error_count", *WP6_FIELDS]
        ],
        "",
    ]

    truth_summary_lines = [
        "# FAZ29 RC-O Boundary Repair Truth Summary",
        "",
        f"- resmi_karar = `{official_decision}`",
        f"- sonraki_resmi_is = `{next_official_work}`",
        f"- wp2_pass = `{bool_text(wp['WP-2'] == 'PASS')}`",
        f"- wp3_pass = `{bool_text(wp['WP-3'] == 'PASS')}`",
        f"- wp4_pass = `{bool_text(wp['WP-4'] == 'PASS')}`",
        f"- wp5_pass = `{bool_text(wp['WP-5'] == 'PASS')}`",
        f"- wp6_pass = `{bool_text(wp['WP-6'] == 'PASS')}`",
        "",
    ]

    result_lines = [
        "# FAZ29 RC-O RELEASE-CONTROLS BOUNDARY REPAIR RECAPTURE UNDER CANONICAL CURRENT AUTHORITY RAPORU",
        "",
        "## A) Yönetici özeti",
        "",
        f"- resmi_karar = `{official_decision}`",
        f"- sonraki_resmi_is = `{next_official_work}`",
        "",
        "## B) Reference pack özeti",
        "",
        f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
        f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
        f"- quality_reference_ref = `{ref['quality_reference_ref']}`",
        f"- canonical_current_authority_ref = `{ref['canonical_current_authority_ref']}`",
        f"- release_controls_legacy_ref = `{ref['release_controls_legacy_ref']}`",
        f"- archival_closure_ref = `{ref['archival_closure_ref']}`",
        "",
        "## C) RC-O recapture contract özeti",
        "",
        f"- candidate_id = `{manifest['candidate_id']}`",
        f"- base_candidate = `{manifest['base_candidate']}`",
        f"- control_candidate = `{manifest['control_candidate']}`",
        f"- forensic_reference_candidate = `{manifest['forensic_reference_candidate']}`",
        f"- allowed_diff_surface = `{manifest['allowed_diff_surface']}`",
        f"- answer_path_delta_allowed = `{bool_text(manifest['answer_path_delta_allowed'])}`",
        f"- candidate_status = `{manifest['candidate_status']}`",
        "",
        "## D) Current authority ve upstream equality authoritative recapture özeti",
        "",
        *[
            f"- {field} = `{bool_text(wp2[field]) if isinstance(wp2[field], bool) else wp2[field]}`"
            for field in ["capture_stability_match", "capture_a_vs_capture_b_mismatch_count", "capture_a_vs_capture_b_runtime_error_count", *WP2_FIELDS]
        ],
        "",
        "## E) Boundary frontier 166 ve repair delta 14 özeti",
        "",
        *[
            f"- {field} = `{bool_text(wp3[field]) if isinstance(wp3[field], bool) else wp3[field]}`"
            for field in ["capture_stability_match", "capture_a_vs_capture_b_mismatch_count", "capture_a_vs_capture_b_runtime_error_count", *WP3_FIELDS]
        ],
        "",
        "## F) Spillover guard 24 authoritative recapture özeti",
        "",
        *[
            f"- {field} = `{bool_text(wp4[field]) if isinstance(wp4[field], bool) else wp4[field]}`"
            for field in ["capture_stability_match", "capture_a_vs_capture_b_mismatch_count", "capture_a_vs_capture_b_runtime_error_count", *WP4_FIELDS]
        ],
        "",
        "## G) Failing-control triplet ve targeted acceptance authoritative recapture özeti",
        "",
        *[
            f"- {field} = `{bool_text(wp5[field]) if isinstance(wp5[field], bool) else wp5[field]}`"
            for field in ["capture_stability_match", "capture_a_vs_capture_b_mismatch_count", "capture_a_vs_capture_b_runtime_error_count", *WP5_FIELDS]
        ],
        "",
        "## H) Retention truth authoritative recapture özeti",
        "",
        *[
            f"- {field} = `{bool_text(wp6[field]) if isinstance(wp6[field], bool) else wp6[field]}`"
            for field in ["capture_stability_match", "capture_a_vs_capture_b_mismatch_count", "capture_a_vs_capture_b_runtime_error_count", *WP6_FIELDS]
        ],
        "",
        "## I) WP sonuçları",
        "",
        *[f"- {key} = `{value}`" for key, value in wp.items()],
        "",
        "## J) Artefact listesi",
        "",
        *[f"- `{path}`" for path in ARTEFACT_LIST],
        "",
    ]

    outputs: dict[Path, str | dict[str, Any]] = {
        ROOT / "coordination" / f"faz29-steering-decision-table-{DATE}.md": "\n".join(steering_lines),
        ROOT / "coordination" / f"faz29-rc-o-boundary-repair-truth-reconciliation-{DATE}.md": "\n".join(reconciliation_lines),
        ROOT / "evaluation" / "reports" / f"faz29-rc-g-vs-rc-j-current-authority-check-{DATE}.md": "\n".join(current_authority_lines),
        ROOT / "evaluation" / "reports" / f"faz29-rc-g-vs-rc-o-upstream-equality-gate-{DATE}.md": "\n".join(upstream_lines),
        ROOT / "evaluation" / "reports" / f"faz29-rc-n-vs-rc-o-repair-delta-summary-{DATE}.md": "\n".join(repair_delta_lines),
        ROOT / "evaluation" / "reports" / f"faz29-rc-g-vs-rc-o-boundary-frontier-166-recapture-{DATE}.md": "\n".join(boundary_lines),
        ROOT / "evaluation" / "reports" / f"faz29-rc-g-vs-rc-o-spillover-guard-24-recapture-{DATE}.md": "\n".join(spillover_lines),
        ROOT / "evaluation" / "reports" / f"faz29-rc-o-failing-controls-triplet-recapture-{DATE}.md": "\n".join(acceptance_lines),
        ROOT / "evaluation" / "reports" / f"faz29-rc-o-retention-recapture-{DATE}.md": "\n".join(retention_lines),
        ROOT / "evaluation" / "reports" / f"faz29-rc-o-boundary-repair-truth-summary-{DATE}.md": "\n".join(truth_summary_lines),
        ROOT / "reports" / RESULT_REPORT_NAME: "\n".join(result_lines),
        ROOT / "docs" / RESULT_REPORT_NAME: "\n".join(result_lines),
        ROOT / "coordination" / f"faz29-phase-package-{DATE}.json": payload,
    }
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ29 authoritative phase package.")
    parser.add_argument("--materialized-json", type=Path, required=True)
    parser.add_argument("--capture-a-json", type=Path, required=True)
    parser.add_argument("--capture-b-json", type=Path, required=True)
    args = parser.parse_args()

    payload = build_phase_payload(
        materialized=load_json(args.materialized_json),
        capture_a=load_json(args.capture_a_json),
        capture_b=load_json(args.capture_b_json),
    )
    for path, body in render_outputs(payload).items():
        if isinstance(body, (dict, list)):
            write_json(path, body)
        else:
            write_text(path, body)
    return 0 if payload["official_decision"] == PASS_DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
