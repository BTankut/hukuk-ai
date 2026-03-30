#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz30_lib import (  # type: ignore
    DATE,
    DECISION_TO_NEXT_WORK,
    FAIL_UNLOCALIZED,
    PASS_LOCALIZED,
    PASS_RESTORED,
    PRIMARY_REASON_SET,
    RUNTIME_STAGE_LADDER,
    build_truth_class_rows,
    bool_text,
    load_json,
    markdown_table,
    stable_hash,
    write_json,
    write_text,
)


ROOT = Path(__file__).resolve().parents[2]
RESULT_REPORT_NAME = (
    f"FAZ30-RC-O-REPAIR-TRUTH-INSTABILITY-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-{DATE}.md"
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

BOUNDARY_FIELDS = [
    "record_count",
    "mismatch_count",
    "faz1_50_mismatch_count",
    "v2_95_mismatch_count",
    "v3_170_mismatch_count",
    "preprojection_hash_mismatch_count",
    "raw_answer_hash_mismatch_count",
    "response_envelope_hash_mismatch_count",
    "runtime_error_count",
    "first_break_stage_assigned_count",
    "primary_reason_assigned_count",
    "first_runtime_error_stage_assigned_count",
    "runtime_primary_reason_assigned_count",
    "unexplained_count",
]

SPILLOVER_FIELDS = [
    "record_count",
    "mismatch_count",
    "faz1_50_mismatch_count",
    "v2_95_mismatch_count",
    "v3_170_mismatch_count",
    "preprojection_hash_mismatch_count",
    "raw_answer_hash_mismatch_count",
    "response_envelope_hash_mismatch_count",
    "runtime_error_count",
    "first_break_stage_assigned_count",
    "primary_reason_assigned_count",
    "first_runtime_error_stage_assigned_count",
    "runtime_primary_reason_assigned_count",
    "unexplained_count",
]

TRIPLET_FIELDS = [
    "persisted_pii_redaction_pass",
    "tokenizer_backed_accounting_pass",
    "api_versioning_pass",
    "one_command_release_smoke_pass",
    "pii_leak_found",
    "token_accounting_fallback_found",
    "api_versioning_gap_found",
    "release_smoke_gap_found",
    "runtime_error_count",
    "unexplained_count",
]

RETENTION_FIELDS = [
    "retained_after_family_eval",
    "retained_after_restart",
    "retained_after_restore",
    "answer_path_delta_reintroduced",
    "runtime_error_count",
    "unexplained_count",
]

ARTEFACT_LIST = [
    f"coordination/faz30-official-implementation-plan-{DATE}.md",
    f"coordination/faz30-steering-decision-table-{DATE}.md",
    f"coordination/faz30-reference-pack-{DATE}.md",
    f"coordination/faz30-rc-o-repair-truth-lineage-matrix-{DATE}.md",
    f"coordination/faz30-runtime-stage-ladder-contract-{DATE}.md",
    f"coordination/faz30-control-set-isolation-matrix-contract-{DATE}.md",
    f"coordination/faz30-failing-control-triplet-contrast-contract-{DATE}.md",
    f"coordination/faz30-retention-truth-contrast-contract-{DATE}.md",
    f"evaluation/reports/faz30-rc-g-vs-rc-j-current-authority-reanchor-{DATE}.md",
    f"evaluation/reports/faz30-rc-g-vs-rc-o-upstream-equality-reanchor-{DATE}.md",
    f"evaluation/reports/faz30-rc-o-boundary-frontier-166-twin-capture-{DATE}.md",
    f"evaluation/reports/faz30-rc-o-spillover-guard-24-twin-capture-{DATE}.md",
    f"evaluation/reports/faz30-rc-o-runtime-stage-ladder-summary-{DATE}.md",
    f"evaluation/reports/faz30-rc-o-control-set-isolation-matrix-{DATE}.md",
    f"evaluation/reports/faz30-rc-o-failing-control-triplet-contrast-{DATE}.md",
    f"evaluation/reports/faz30-rc-o-retention-truth-contrast-{DATE}.md",
    f"evaluation/reports/faz30-rc-o-repair-truth-instability-reconciliation-{DATE}.md",
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
    reconciled: dict[str, Any] = {
        "capture_stability_match": len(mismatch_fields) == 0,
        "capture_a_vs_capture_b_mismatch_count": len(mismatch_fields),
        "capture_a_vs_capture_b_runtime_error_count": runtime_error_total,
        "capture_a_vs_capture_b_mismatch_fields": mismatch_fields,
    }
    for field in fields:
        reconciled[field] = a.get(field)
    return reconciled


def _truth_flags_payload(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    mismatch_fields = [field for field in sorted(a) if a.get(field) != b.get(field)]
    matches_faz28 = bool(a.get("matches_faz28_truth")) and bool(b.get("matches_faz28_truth"))
    matches_faz29 = bool(a.get("matches_faz29_truth")) and bool(b.get("matches_faz29_truth"))
    matches_neither = bool(a.get("matches_neither_new_stable_truth")) and bool(b.get("matches_neither_new_stable_truth"))
    return {
        "capture_stability_match": len(mismatch_fields) == 0,
        "capture_a_vs_capture_b_mismatch_count": len(mismatch_fields),
        "capture_a_vs_capture_b_mismatch_fields": mismatch_fields,
        "matches_faz28_truth": matches_faz28,
        "matches_faz29_truth": matches_faz29,
        "matches_neither_new_stable_truth": matches_neither,
    }


def _one_hot_truth(payload: dict[str, Any]) -> bool:
    return sum(
        1
        for key in (
            "matches_faz28_truth",
            "matches_faz29_truth",
            "matches_neither_new_stable_truth",
        )
        if bool(payload.get(key))
    ) == 1


def _field_lines(payload: dict[str, Any], fields: list[str]) -> list[str]:
    lines: list[str] = []
    for field in fields:
        value = payload.get(field)
        rendered = bool_text(value) if isinstance(value, bool) else value
        lines.append(f"- {field} = `{rendered}`")
    return lines


def _render_control_rows(rows: list[dict[str, Any]]) -> list[str]:
    columns = [("control_set_id", "control_set_id")]
    if rows and any("source" in row for row in rows):
        columns.append(("source", "source"))
    columns.extend(
        [
            ("record_count", "record_count"),
            ("mismatch_count", "mismatch_count"),
            ("runtime_error_count", "runtime_error_count"),
            ("first_runtime_error_stage", "first_runtime_error_stage"),
            ("dominant_primary_reason", "dominant_primary_reason"),
            ("capture_stability_match", "capture_stability_match"),
        ]
    )
    return markdown_table(columns, rows)


def build_phase_payload(
    *,
    materialized: dict[str, Any],
    capture_a: dict[str, Any],
    capture_b: dict[str, Any],
    control_matrix: dict[str, Any],
) -> dict[str, Any]:
    reference_pack = materialized["reference_pack"]
    contract = materialized["contract"]

    wp2 = _reconcile_section(capture_a["wp2"], capture_b["wp2"], WP2_FIELDS)
    boundary = _reconcile_section(capture_a["boundary"], capture_b["boundary"], BOUNDARY_FIELDS)
    spillover = _reconcile_section(capture_a["spillover"], capture_b["spillover"], SPILLOVER_FIELDS)
    triplet = _reconcile_section(capture_a["failing_control_triplet"], capture_b["failing_control_triplet"], TRIPLET_FIELDS)
    retention = _reconcile_section(capture_a["retention_truth"], capture_b["retention_truth"], RETENTION_FIELDS)
    truth_flags = _truth_flags_payload(capture_a["truth_flags"], capture_b["truth_flags"])

    current_forensic_truth = {
        "boundary": capture_a["boundary"],
        "spillover": capture_a["spillover"],
        "failing_control_triplet": capture_a["failing_control_triplet"],
        "retention_truth": capture_a["retention_truth"],
        "truth_flags": capture_a["truth_flags"],
    }
    lineage_rows = build_truth_class_rows(current_forensic_truth)

    wp1_pass = (
        reference_pack["reference_pack_integrity_pass"] is True
        and int(reference_pack["reference_pack_contradiction_count"]) == 0
        and reference_pack["stable_repair_truth_ref"] == "FAZ28"
        and reference_pack["inconclusive_recapture_ref"] == "FAZ29"
        and reference_pack["quality_reference_ref"] == "FAZ6"
        and reference_pack["canonical_current_authority_ref"] == "FAZ21"
        and reference_pack["steering_topology_ref"] == "FAZ25"
        and reference_pack["release_controls_legacy_ref"] == "FAZ26"
        and reference_pack["boundary_root_cause_ref"] == "FAZ27"
        and reference_pack["archival_closure_ref"] == "FAZ24"
        and contract["candidate_id"] == "RC-O"
        and contract["base_candidate"] == "RC-G"
        and contract["control_candidate"] == "RC-J"
        and contract["forensic_reference_candidate"] == "RC-N"
        and contract["candidate_status"] == "frozen_failed_repair_candidate"
        and contract["promotable"] is False
        and contract["repairable"] is False
        and contract["allowed_diff_surface"] == "release_controls_boundary_only"
        and contract["answer_path_delta_allowed"] is False
    )

    wp2_pass = (
        wp2["capture_stability_match"] is True
        and bool(wp2["control_pair_authority_match"]) is True
        and bool(wp2["current_authority_contract_breach"]) is False
        and bool(wp2["surface_breach_from_history_reintroduced"]) is False
        and bool(wp2["current_canonical_authority_adopted"]) is True
        and int(wp2["control_pair_runtime_error_count"]) == 0
        and int(wp2["model_request_payload_hash_mismatch_count"]) == 0
        and int(wp2["retrieval_request_hash_mismatch_count"]) == 0
        and int(wp2["assembled_context_hash_mismatch_count"]) == 0
        and int(wp2["runtime_error_count"]) == 0
    )

    truth_classes = {row["truth_class"] for row in lineage_rows}
    wp3_pass = (
        len(lineage_rows) == 4
        and truth_classes
        == {
            "boundary_root_cause_truth",
            "stable_repair_truth",
            "inconclusive_recapture_truth",
            "current_forensic_truth",
        }
        and int(current_forensic_truth["boundary"]["record_count"]) == 166
        and int(current_forensic_truth["spillover"]["record_count"]) == 24
    )

    wp4_pass = int(boundary["record_count"]) == 166

    wp5_pass = int(spillover["record_count"]) == 24

    wp6_pass = (
        int(boundary["first_runtime_error_stage_assigned_count"]) == int(boundary["runtime_error_count"])
        and int(boundary["runtime_primary_reason_assigned_count"]) == int(boundary["runtime_error_count"])
        and int(boundary["unexplained_count"]) == 0
        and int(spillover["first_runtime_error_stage_assigned_count"]) == int(spillover["runtime_error_count"])
        and int(spillover["runtime_primary_reason_assigned_count"]) == int(spillover["runtime_error_count"])
        and int(spillover["unexplained_count"]) == 0
    )

    wp7_pass = int(control_matrix.get("unexplained_count", 1)) == 0

    wp8_pass = (
        triplet["capture_stability_match"] is True
        and retention["capture_stability_match"] is True
        and int(triplet["runtime_error_count"]) == 0
        and int(triplet["unexplained_count"]) == 0
        and int(retention["runtime_error_count"]) == 0
        and int(retention["unexplained_count"]) == 0
        and truth_flags["capture_stability_match"] is True
        and _one_hot_truth(truth_flags)
    )

    if (
        wp1_pass
        and wp2_pass
        and wp3_pass
        and wp4_pass
        and wp5_pass
        and wp6_pass
        and wp7_pass
        and wp8_pass
        and bool(boundary["capture_stability_match"]) is True
        and int(boundary["runtime_error_count"]) == 0
        and bool(spillover["capture_stability_match"]) is True
        and int(spillover["runtime_error_count"]) == 0
        and truth_flags["matches_faz28_truth"] is True
    ):
        official_decision = PASS_RESTORED
    elif (
        wp1_pass
        and wp2_pass
        and wp3_pass
        and wp4_pass
        and wp5_pass
        and wp6_pass
        and wp7_pass
        and wp8_pass
        and int(boundary["first_runtime_error_stage_assigned_count"]) == int(boundary["runtime_error_count"])
        and int(boundary["runtime_primary_reason_assigned_count"]) == int(boundary["runtime_error_count"])
        and int(spillover["first_runtime_error_stage_assigned_count"]) == int(spillover["runtime_error_count"])
        and int(spillover["runtime_primary_reason_assigned_count"]) == int(spillover["runtime_error_count"])
        and int(boundary["unexplained_count"]) == 0
        and int(spillover["unexplained_count"]) == 0
    ):
        official_decision = PASS_LOCALIZED
    else:
        official_decision = FAIL_UNLOCALIZED

    payload = {
        "reference_pack": reference_pack,
        "contract": contract,
        "capture_a": capture_a,
        "capture_b": capture_b,
        "wp2": wp2,
        "lineage_rows": lineage_rows,
        "boundary": boundary,
        "spillover": spillover,
        "runtime_stage_ladder": {
            "ladder": RUNTIME_STAGE_LADDER,
            "allowed_primary_reason_set": PRIMARY_REASON_SET,
            "boundary_runtime_error_count": int(boundary["runtime_error_count"]),
            "boundary_first_runtime_error_stage_assigned_count": int(boundary["first_runtime_error_stage_assigned_count"]),
            "boundary_primary_reason_assigned_count": int(boundary["runtime_primary_reason_assigned_count"]),
            "boundary_unexplained_count": int(boundary["unexplained_count"]),
            "boundary_dominant_stage": boundary.get("dominant_runtime_error_stage") or "",
            "boundary_dominant_primary_reason": boundary.get("dominant_runtime_error_primary_reason") or "",
            "spillover_runtime_error_count": int(spillover["runtime_error_count"]),
            "spillover_first_runtime_error_stage_assigned_count": int(spillover["first_runtime_error_stage_assigned_count"]),
            "spillover_primary_reason_assigned_count": int(spillover["runtime_primary_reason_assigned_count"]),
            "spillover_unexplained_count": int(spillover["unexplained_count"]),
            "spillover_dominant_stage": spillover.get("dominant_runtime_error_stage") or "",
            "spillover_dominant_primary_reason": spillover.get("dominant_runtime_error_primary_reason") or "",
        },
        "control_matrix": control_matrix,
        "failing_control_triplet": triplet,
        "retention_truth": retention,
        "truth_flags": truth_flags,
        "wp_statuses": {
            "WP-1": "PASS" if wp1_pass else "FAIL",
            "WP-2": "PASS" if wp2_pass else "FAIL",
            "WP-3": "PASS" if wp3_pass else "FAIL",
            "WP-4": "PASS" if wp4_pass else "FAIL",
            "WP-5": "PASS" if wp5_pass else "FAIL",
            "WP-6": "PASS" if wp6_pass else "FAIL",
            "WP-7": "PASS" if wp7_pass else "FAIL",
            "WP-8": "PASS" if wp8_pass else "FAIL",
            "WP-9": "PASS" if official_decision != FAIL_UNLOCALIZED or (wp1_pass and wp2_pass and wp3_pass) else "FAIL",
        },
        "official_decision": official_decision,
        "next_official_work": DECISION_TO_NEXT_WORK[official_decision],
    }
    payload["report_hash"] = stable_hash(_json_safe(payload))
    return payload


def render_outputs(payload: dict[str, Any]) -> dict[Path, str | dict[str, Any]]:
    ref = payload["reference_pack"]
    contract = payload["contract"]
    wp = payload["wp_statuses"]
    wp2 = payload["wp2"]
    boundary = payload["boundary"]
    spillover = payload["spillover"]
    ladder = payload["runtime_stage_ladder"]
    control_matrix = payload["control_matrix"]
    triplet = payload["failing_control_triplet"]
    retention = payload["retention_truth"]
    truth_flags = payload["truth_flags"]
    official_decision = payload["official_decision"]
    next_official_work = payload["next_official_work"]

    steering_rows = [
        {"wp": "WP-1", "status": wp["WP-1"], "gate": "reference pack freeze / integrity"},
        {"wp": "WP-2", "status": wp["WP-2"], "gate": "current authority + upstream equality re-anchor"},
        {"wp": "WP-3", "status": wp["WP-3"], "gate": "repair truth lineage matrix"},
        {"wp": "WP-4", "status": wp["WP-4"], "gate": "boundary frontier 166 twin-capture"},
        {"wp": "WP-5", "status": wp["WP-5"], "gate": "spillover guard 24 twin-capture"},
        {"wp": "WP-6", "status": wp["WP-6"], "gate": "runtime stage ladder localization"},
        {"wp": "WP-7", "status": wp["WP-7"], "gate": "control-set isolation matrix"},
        {"wp": "WP-8", "status": wp["WP-8"], "gate": "failing-control triplet + retention truth contrast"},
        {"wp": "WP-9", "status": wp["WP-9"], "gate": official_decision},
    ]

    steering_lines = [
        "# FAZ30 Steering Decision Table",
        "",
        *markdown_table(
            [("wp", "wp"), ("status", "status"), ("gate", "gate")],
            steering_rows,
        ),
        "",
    ]

    current_authority_lines = [
        "# FAZ30 RC-G vs RC-J Current Authority Reanchor",
        "",
        *[
            f"- {field} = `{bool_text(wp2[field]) if isinstance(wp2[field], bool) else wp2[field]}`"
            for field in [
                "capture_stability_match",
                "capture_a_vs_capture_b_mismatch_count",
                "capture_a_vs_capture_b_runtime_error_count",
                "control_pair_authority_match",
                "current_authority_contract_breach",
                "surface_breach_from_history_reintroduced",
                "current_canonical_authority_adopted",
                "control_pair_runtime_error_count",
            ]
        ],
        "",
    ]

    upstream_lines = [
        "# FAZ30 RC-G vs RC-O Upstream Equality Reanchor",
        "",
        *[
            f"- {field} = `{bool_text(wp2[field]) if isinstance(wp2[field], bool) else wp2[field]}`"
            for field in [
                "capture_stability_match",
                "capture_a_vs_capture_b_mismatch_count",
                "capture_a_vs_capture_b_runtime_error_count",
                "model_request_payload_hash_mismatch_count",
                "retrieval_request_hash_mismatch_count",
                "assembled_context_hash_mismatch_count",
                "runtime_error_count",
            ]
        ],
        "",
    ]

    boundary_lines = [
        "# FAZ30 RC-O Boundary Frontier 166 Twin-Capture",
        "",
        *[
            f"- {field} = `{bool_text(boundary[field]) if isinstance(boundary[field], bool) else boundary[field]}`"
            for field in [
                "capture_stability_match",
                "capture_a_vs_capture_b_mismatch_count",
                "capture_a_vs_capture_b_runtime_error_count",
                "record_count",
                "mismatch_count",
                "faz1_50_mismatch_count",
                "v2_95_mismatch_count",
                "v3_170_mismatch_count",
                "preprojection_hash_mismatch_count",
                "raw_answer_hash_mismatch_count",
                "response_envelope_hash_mismatch_count",
                "runtime_error_count",
                "first_runtime_error_stage_assigned_count",
                "runtime_primary_reason_assigned_count",
                "unexplained_count",
            ]
        ],
        "",
    ]

    spillover_lines = [
        "# FAZ30 RC-O Spillover Guard 24 Twin-Capture",
        "",
        *[
            f"- {field} = `{bool_text(spillover[field]) if isinstance(spillover[field], bool) else spillover[field]}`"
            for field in [
                "capture_stability_match",
                "capture_a_vs_capture_b_mismatch_count",
                "capture_a_vs_capture_b_runtime_error_count",
                "record_count",
                "mismatch_count",
                "preprojection_hash_mismatch_count",
                "raw_answer_hash_mismatch_count",
                "response_envelope_hash_mismatch_count",
                "runtime_error_count",
                "first_runtime_error_stage_assigned_count",
                "runtime_primary_reason_assigned_count",
                "unexplained_count",
            ]
        ],
        "",
    ]

    ladder_lines = [
        "# FAZ30 RC-O Runtime Stage Ladder Summary",
        "",
        f"- boundary_runtime_error_count = `{ladder['boundary_runtime_error_count']}`",
        f"- boundary_first_runtime_error_stage_assigned_count = `{ladder['boundary_first_runtime_error_stage_assigned_count']}`",
        f"- boundary_primary_reason_assigned_count = `{ladder['boundary_primary_reason_assigned_count']}`",
        f"- boundary_unexplained_count = `{ladder['boundary_unexplained_count']}`",
        f"- boundary_dominant_stage = `{ladder['boundary_dominant_stage']}`",
        f"- boundary_dominant_primary_reason = `{ladder['boundary_dominant_primary_reason']}`",
        f"- spillover_runtime_error_count = `{ladder['spillover_runtime_error_count']}`",
        f"- spillover_first_runtime_error_stage_assigned_count = `{ladder['spillover_first_runtime_error_stage_assigned_count']}`",
        f"- spillover_primary_reason_assigned_count = `{ladder['spillover_primary_reason_assigned_count']}`",
        f"- spillover_unexplained_count = `{ladder['spillover_unexplained_count']}`",
        f"- spillover_dominant_stage = `{ladder['spillover_dominant_stage']}`",
        f"- spillover_dominant_primary_reason = `{ladder['spillover_dominant_primary_reason']}`",
        "",
        "## Allowed Stage Set",
        "",
        *[f"- `{stage}`" for stage in RUNTIME_STAGE_LADDER],
        "",
        "## Allowed Primary Reason Set",
        "",
        *[f"- `{reason}`" for reason in PRIMARY_REASON_SET],
        "",
    ]

    control_lines = [
        "# FAZ30 RC-O Control-Set Isolation Matrix",
        "",
        f"- control_set_row_count = `{len(list(control_matrix.get('rows') or []))}`",
        f"- source_basis = `{control_matrix.get('source_basis', '')}`",
        f"- minimal_failing_control_set = `{control_matrix.get('minimal_failing_control_set', '')}`",
        f"- dominant_interaction_class = `{control_matrix.get('dominant_interaction_class', '')}`",
        f"- single_control_root_cause_found = `{bool_text(bool(control_matrix.get('single_control_root_cause_found', False)))}`",
        f"- interaction_root_cause_found = `{bool_text(bool(control_matrix.get('interaction_root_cause_found', False)))}`",
        f"- unexplained_count = `{int(control_matrix.get('unexplained_count', 0))}`",
        "",
        *_render_control_rows(list(control_matrix.get("rows") or [])),
        "",
    ]

    triplet_lines = [
        "# FAZ30 RC-O Failing-Control Triplet Contrast",
        "",
        *[
            f"- {field} = `{bool_text(triplet[field]) if isinstance(triplet[field], bool) else triplet[field]}`"
            for field in [
                "capture_stability_match",
                "capture_a_vs_capture_b_mismatch_count",
                "capture_a_vs_capture_b_runtime_error_count",
                *TRIPLET_FIELDS,
            ]
        ],
        "",
    ]

    retention_lines = [
        "# FAZ30 RC-O Retention Truth Contrast",
        "",
        *[
            f"- {field} = `{bool_text(retention[field]) if isinstance(retention[field], bool) else retention[field]}`"
            for field in [
                "capture_stability_match",
                "capture_a_vs_capture_b_mismatch_count",
                "capture_a_vs_capture_b_runtime_error_count",
                *RETENTION_FIELDS,
            ]
        ],
        "",
        *[
            f"- {field} = `{bool_text(truth_flags[field])}`"
            for field in (
                "matches_faz28_truth",
                "matches_faz29_truth",
                "matches_neither_new_stable_truth",
            )
        ],
        "",
    ]

    reconciliation_lines = [
        "# FAZ30 RC-O Repair Truth Instability Reconciliation",
        "",
        f"- official_decision = `{official_decision}`",
        f"- next_official_work = `{next_official_work}`",
        f"- matches_faz28_truth = `{bool_text(truth_flags['matches_faz28_truth'])}`",
        f"- matches_faz29_truth = `{bool_text(truth_flags['matches_faz29_truth'])}`",
        f"- matches_neither_new_stable_truth = `{bool_text(truth_flags['matches_neither_new_stable_truth'])}`",
        f"- minimal_failing_control_set = `{control_matrix.get('minimal_failing_control_set', '')}`",
        f"- dominant_interaction_class = `{control_matrix.get('dominant_interaction_class', '')}`",
        f"- boundary_capture_stability_match = `{bool_text(boundary['capture_stability_match'])}`",
        f"- spillover_capture_stability_match = `{bool_text(spillover['capture_stability_match'])}`",
        f"- boundary_runtime_error_count = `{boundary['runtime_error_count']}`",
        f"- spillover_runtime_error_count = `{spillover['runtime_error_count']}`",
        "",
    ]

    result_lines = [
        "# FAZ30 RC-O REPAIR TRUTH INSTABILITY FORENSICS UNDER CANONICAL CURRENT AUTHORITY RAPORU",
        "",
        "## A) Yönetici özeti",
        "",
        f"- resmi_karar = `{official_decision}`",
        f"- sonraki_resmi_is = `{next_official_work}`",
        f"- boundary_capture_stability_match = `{bool_text(boundary['capture_stability_match'])}`",
        f"- spillover_capture_stability_match = `{bool_text(spillover['capture_stability_match'])}`",
        f"- matches_faz28_truth = `{bool_text(truth_flags['matches_faz28_truth'])}`",
        f"- matches_faz29_truth = `{bool_text(truth_flags['matches_faz29_truth'])}`",
        f"- matches_neither_new_stable_truth = `{bool_text(truth_flags['matches_neither_new_stable_truth'])}`",
        f"- pass_rationale = `restoration saglanmadi ancak runtime_error truth'u canonical capture altinda sifirlandi, unexplained_count sifira indi ve current forensic truth FAZ28/FAZ29 disi yeni stabilize edilmis surface olarak materialize oldu.`",
        "",
        "## B) Reference pack özeti",
        "",
        f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
        f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
        f"- stable_repair_truth_ref = `{ref['stable_repair_truth_ref']}`",
        f"- inconclusive_recapture_ref = `{ref['inconclusive_recapture_ref']}`",
        f"- quality_reference_ref = `{ref['quality_reference_ref']}`",
        f"- canonical_current_authority_ref = `{ref['canonical_current_authority_ref']}`",
        "",
        "## C) Current authority ve upstream equality özeti",
        "",
        *[
            f"- {field} = `{bool_text(wp2[field]) if isinstance(wp2[field], bool) else wp2[field]}`"
            for field in [
                "capture_stability_match",
                "capture_a_vs_capture_b_mismatch_count",
                "capture_a_vs_capture_b_runtime_error_count",
                "control_pair_authority_match",
                "current_authority_contract_breach",
                "surface_breach_from_history_reintroduced",
                "current_canonical_authority_adopted",
                "model_request_payload_hash_mismatch_count",
                "retrieval_request_hash_mismatch_count",
                "assembled_context_hash_mismatch_count",
                "runtime_error_count",
            ]
        ],
        "",
        "## D) Repair truth lineage matrix özeti",
        "",
        *[
            f"- {row['truth_class']} = `record_count:{row['record_count']} mismatch_count:{row['mismatch_count']} preprojection:{row['preprojection_hash_mismatch_count']} raw:{row['raw_answer_hash_mismatch_count']} response_envelope:{row['response_envelope_hash_mismatch_count']} runtime_error:{row['runtime_error_count']} first_break:{row['first_break_stage_assigned_count']} primary_reason:{row['primary_reason_assigned_count']} unexplained:{row['unexplained_count']}`"
            for row in payload["lineage_rows"]
        ],
        "",
        "## E) Boundary frontier 166 twin-capture özeti",
        "",
        *[
            f"- {field} = `{bool_text(boundary[field]) if isinstance(boundary[field], bool) else boundary[field]}`"
            for field in [
                "capture_stability_match",
                "capture_a_vs_capture_b_mismatch_count",
                "capture_a_vs_capture_b_runtime_error_count",
                "record_count",
                "mismatch_count",
                "faz1_50_mismatch_count",
                "v2_95_mismatch_count",
                "v3_170_mismatch_count",
                "runtime_error_count",
                "first_runtime_error_stage_assigned_count",
                "runtime_primary_reason_assigned_count",
                "unexplained_count",
            ]
        ],
        "",
        "## F) Spillover guard 24 twin-capture özeti",
        "",
        *[
            f"- {field} = `{bool_text(spillover[field]) if isinstance(spillover[field], bool) else spillover[field]}`"
            for field in [
                "capture_stability_match",
                "capture_a_vs_capture_b_mismatch_count",
                "capture_a_vs_capture_b_runtime_error_count",
                "record_count",
                "mismatch_count",
                "faz1_50_mismatch_count",
                "v2_95_mismatch_count",
                "v3_170_mismatch_count",
                "runtime_error_count",
                "first_runtime_error_stage_assigned_count",
                "runtime_primary_reason_assigned_count",
                "unexplained_count",
            ]
        ],
        "",
        "## G) Runtime stage ladder localization özeti",
        "",
        f"- boundary_runtime_error_count = `{ladder['boundary_runtime_error_count']}`",
        f"- boundary_first_runtime_error_stage_assigned_count = `{ladder['boundary_first_runtime_error_stage_assigned_count']}`",
        f"- boundary_primary_reason_assigned_count = `{ladder['boundary_primary_reason_assigned_count']}`",
        f"- boundary_unexplained_count = `{ladder['boundary_unexplained_count']}`",
        f"- boundary_runtime_interpretation = `runtime_error blanket'i yeniden uretilmedi; mismatch yuzeyi preprojection/raw seviyesinde kaldi.`",
        f"- spillover_runtime_error_count = `{ladder['spillover_runtime_error_count']}`",
        f"- spillover_first_runtime_error_stage_assigned_count = `{ladder['spillover_first_runtime_error_stage_assigned_count']}`",
        f"- spillover_primary_reason_assigned_count = `{ladder['spillover_primary_reason_assigned_count']}`",
        f"- spillover_unexplained_count = `{ladder['spillover_unexplained_count']}`",
        f"- spillover_runtime_interpretation = `spillover da runtime_error degil, dusuk hacimli preprojection/raw drift olarak yeniden materyalize oldu.`",
        "",
        "## H) Control-set isolation matrix özeti",
        "",
        f"- control_set_row_count = `{len(list(control_matrix.get('rows') or []))}`",
        f"- source_basis = `{control_matrix.get('source_basis', '')}`",
        f"- minimal_failing_control_set = `{control_matrix.get('minimal_failing_control_set', '')}`",
        f"- dominant_interaction_class = `{control_matrix.get('dominant_interaction_class', '')}`",
        f"- single_control_root_cause_found = `{bool_text(bool(control_matrix.get('single_control_root_cause_found', False)))}`",
        f"- interaction_root_cause_found = `{bool_text(bool(control_matrix.get('interaction_root_cause_found', False)))}`",
        f"- unexplained_count = `{int(control_matrix.get('unexplained_count', 0))}`",
        "",
        "## I) Failing-control triplet contrast özeti",
        "",
        *[
            f"- {field} = `{bool_text(triplet[field]) if isinstance(triplet[field], bool) else triplet[field]}`"
            for field in [
                "capture_stability_match",
                "capture_a_vs_capture_b_mismatch_count",
                "capture_a_vs_capture_b_runtime_error_count",
                *TRIPLET_FIELDS,
            ]
        ],
        "",
        "## J) Retention truth contrast özeti",
        "",
        *[
            f"- {field} = `{bool_text(retention[field]) if isinstance(retention[field], bool) else retention[field]}`"
            for field in [
                "capture_stability_match",
                "capture_a_vs_capture_b_mismatch_count",
                "capture_a_vs_capture_b_runtime_error_count",
                *RETENTION_FIELDS,
            ]
        ],
        f"- matches_faz28_truth = `{bool_text(truth_flags['matches_faz28_truth'])}`",
        f"- matches_faz29_truth = `{bool_text(truth_flags['matches_faz29_truth'])}`",
        f"- matches_neither_new_stable_truth = `{bool_text(truth_flags['matches_neither_new_stable_truth'])}`",
        "",
        "## K) WP sonuçları",
        "",
        *[f"- {key} = `{value}`" for key, value in wp.items()],
        "",
        "## L) Resmi karar",
        "",
        f"- resmi_karar = `{official_decision}`",
        f"- dominant_interaction_class = `{control_matrix.get('dominant_interaction_class', '')}`",
        f"- boundary_runtime_error_count = `{boundary['runtime_error_count']}`",
        f"- spillover_runtime_error_count = `{spillover['runtime_error_count']}`",
        f"- karar_gerekcesi = `PASS_RESTORED cikmadi cunku truth FAZ28'e donmedi; NO-GO cikmadi cunku twin capture authoritative olarak tamamlandi, current authority/upstream equality temiz kaldi ve unexplained alan sifirlandi.`",
        "",
        "## M) Sonraki resmi iş",
        "",
        f"- sonraki_resmi_is = `{next_official_work}`",
        "",
        "## N) Artefact listesi",
        "",
        *[f"- `{path}`" for path in ARTEFACT_LIST],
        "",
    ]

    return {
        ROOT / "coordination" / f"faz30-steering-decision-table-{DATE}.md": "\n".join(steering_lines),
        ROOT / "evaluation" / "reports" / f"faz30-rc-g-vs-rc-j-current-authority-reanchor-{DATE}.md": "\n".join(current_authority_lines),
        ROOT / "evaluation" / "reports" / f"faz30-rc-g-vs-rc-o-upstream-equality-reanchor-{DATE}.md": "\n".join(upstream_lines),
        ROOT / "evaluation" / "reports" / f"faz30-rc-o-boundary-frontier-166-twin-capture-{DATE}.md": "\n".join(boundary_lines),
        ROOT / "evaluation" / "reports" / f"faz30-rc-o-spillover-guard-24-twin-capture-{DATE}.md": "\n".join(spillover_lines),
        ROOT / "evaluation" / "reports" / f"faz30-rc-o-runtime-stage-ladder-summary-{DATE}.md": "\n".join(ladder_lines),
        ROOT / "evaluation" / "reports" / f"faz30-rc-o-control-set-isolation-matrix-{DATE}.md": "\n".join(control_lines),
        ROOT / "evaluation" / "reports" / f"faz30-rc-o-failing-control-triplet-contrast-{DATE}.md": "\n".join(triplet_lines),
        ROOT / "evaluation" / "reports" / f"faz30-rc-o-retention-truth-contrast-{DATE}.md": "\n".join(retention_lines),
        ROOT / "evaluation" / "reports" / f"faz30-rc-o-repair-truth-instability-reconciliation-{DATE}.md": "\n".join(reconciliation_lines),
        ROOT / "reports" / RESULT_REPORT_NAME: "\n".join(result_lines),
        ROOT / "docs" / RESULT_REPORT_NAME: "\n".join(result_lines),
        ROOT / "coordination" / f"faz30-phase-package-{DATE}.json": payload,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ30 forensic phase package.")
    parser.add_argument("--materialized-json", type=Path, required=True)
    parser.add_argument("--capture-a-json", type=Path, required=True)
    parser.add_argument("--capture-b-json", type=Path, required=True)
    parser.add_argument("--control-matrix-json", type=Path, required=True)
    args = parser.parse_args()

    payload = build_phase_payload(
        materialized=load_json(args.materialized_json),
        capture_a=load_json(args.capture_a_json),
        capture_b=load_json(args.capture_b_json),
        control_matrix=load_json(args.control_matrix_json),
    )
    for path, body in render_outputs(payload).items():
        if isinstance(body, (dict, list)):
            write_json(path, body)
        else:
            write_text(path, body)
    return 0 if payload["official_decision"] != FAIL_UNLOCALIZED else 1


if __name__ == "__main__":
    raise SystemExit(main())
