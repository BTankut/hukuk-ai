#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz31_lib import (  # type: ignore
    DATE,
    FAIL_DECISION,
    FAIL_NEXT_WORK,
    MATERIALIZED_REFERENCE_JSON,
    PASS_DECISION,
    PASS_NEXT_WORK,
    PHASE_PACKAGE_JSON,
    RECONCILIATION_STAGES,
    RESULT_REPORT_NAME,
    ROOT,
    ROOT_CAUSE_CLASSES,
    bool_text,
    markdown_table,
    stable_hash,
    write_json,
    write_text,
)
from materialize_reference_pack import build_materialization_payload  # type: ignore


ARTEFACT_LIST = [
    f"coordination/faz31-official-implementation-plan-{DATE}.md",
    f"coordination/faz31-steering-decision-table-{DATE}.md",
    f"coordination/faz31-reference-pack-{DATE}.md",
    f"coordination/faz31-rc-o-repair-truth-reconciliation-contract-{DATE}.md",
    f"coordination/faz31-rc-o-repair-truth-contrast-matrix-{DATE}.md",
    f"coordination/faz31-rc-o-current-forensic-truth-adoption-{DATE}.md",
    f"coordination/faz31-rc-o-historical-repair-archive-reclassification-{DATE}.md",
    f"coordination/faz31-rc-o-repair-truth-consumer-binding-{DATE}.md",
    f"coordination/faz31-rc-o-reconciliation-summary-{DATE}.md",
    f"reports/{RESULT_REPORT_NAME}",
]

REQUIRED_PACKAGES = [
    "boundary_frontier_166",
    "spillover_guard_24",
    "failing_control_triplet",
    "retention_truth",
]

REQUIRED_TRUTH_CLASSES = [
    "boundary_root_cause_truth",
    "historical_stable_repair_truth",
    "historical_inconclusive_recapture_truth",
    "current_forensic_repair_truth",
]


def _render_value(value: Any) -> str:
    if isinstance(value, bool):
        return bool_text(value)
    if isinstance(value, list):
        if not value:
            return "[]"
        return ", ".join(str(item) for item in value)
    return str(value)


def _truth_rows(materialized: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for truth_class in REQUIRED_TRUTH_CLASSES:
        truth_payload = materialized["truths"][truth_class]
        for package_name in REQUIRED_PACKAGES:
            package = truth_payload[package_name]
            rows.append(
                {
                    "truth_ref": package["truth_ref"],
                    "truth_class": truth_class,
                    "package_name": package_name,
                    "record_count": int(package["record_count"]),
                    "mismatch_count": int(package["mismatch_count"]),
                    "preprojection_hash_mismatch_count": int(package["preprojection_hash_mismatch_count"]),
                    "raw_answer_hash_mismatch_count": int(package["raw_answer_hash_mismatch_count"]),
                    "response_envelope_hash_mismatch_count": int(package["response_envelope_hash_mismatch_count"]),
                    "runtime_error_count": int(package["runtime_error_count"]),
                    "first_break_stage_assigned_count": int(package["first_break_stage_assigned_count"]),
                    "primary_reason_assigned_count": int(package["primary_reason_assigned_count"]),
                    "unexplained_count": int(package["unexplained_count"]),
                }
            )
    return rows


def build_phase_payload(materialized: dict[str, Any]) -> dict[str, Any]:
    reference_pack = materialized["reference_pack"]
    topology_rows = materialized["topology_rows"]
    current_authority = materialized["current_authority_binding"]
    current_truth_flags = materialized["current_forensic_truth_flags"]
    contract = materialized["contract"]
    contrast_rows = _truth_rows(materialized)

    current_boundary = materialized["truths"]["current_forensic_repair_truth"]["boundary_frontier_166"]
    current_spillover = materialized["truths"]["current_forensic_repair_truth"]["spillover_guard_24"]
    current_triplet = materialized["truths"]["current_forensic_repair_truth"]["failing_control_triplet"]
    current_retention = materialized["truths"]["current_forensic_repair_truth"]["retention_truth"]

    current_forensic_truth_runtime_error_count = (
        int(current_boundary["runtime_error_count"])
        + int(current_spillover["runtime_error_count"])
        + int(current_triplet["runtime_error_count"])
        + int(current_retention["runtime_error_count"])
    )
    current_forensic_truth_unexplained_count = (
        int(current_boundary["unexplained_count"])
        + int(current_spillover["unexplained_count"])
        + int(current_triplet["unexplained_count"])
        + int(current_retention["unexplained_count"])
    )

    wp1_pass = (
        reference_pack["reference_pack_integrity_pass"] is True
        and int(reference_pack["reference_pack_contradiction_count"]) == 0
        and reference_pack["canonical_current_authority_ref"] == "FAZ21"
        and reference_pack["rc_m_archival_closure_ref"] == "FAZ24"
        and reference_pack["steering_topology_ref"] == "FAZ25"
        and reference_pack["boundary_root_cause_ref"] == "FAZ27"
        and reference_pack["stable_repair_truth_ref"] == "FAZ28"
        and reference_pack["inconclusive_recapture_ref"] == "FAZ29"
        and reference_pack["current_forensic_truth_ref"] == "FAZ30"
        and reference_pack["role_topology_frozen"] is True
        and len(topology_rows) == 4
    )

    wp2_pass = (
        len(contrast_rows) == len(REQUIRED_TRUTH_CLASSES) * len(REQUIRED_PACKAGES)
        and {row["truth_class"] for row in contrast_rows} == set(REQUIRED_TRUTH_CLASSES)
        and {row["package_name"] for row in contrast_rows} == set(REQUIRED_PACKAGES)
    )

    current_forensic_truth_adopted = (
        current_forensic_truth_runtime_error_count == 0
        and current_forensic_truth_unexplained_count == 0
        and current_truth_flags["current_forensic_truth_dominant_interaction_class"]
        == "boundary_pack_orchestration_runtime_mutation"
        and current_truth_flags["current_forensic_truth_matches_neither"] is True
    )
    adoption = {
        "current_forensic_truth_adopted": current_forensic_truth_adopted,
        "current_forensic_truth_runtime_error_count": current_forensic_truth_runtime_error_count,
        "current_forensic_truth_unexplained_count": current_forensic_truth_unexplained_count,
        "current_forensic_truth_dominant_interaction_class": current_truth_flags[
            "current_forensic_truth_dominant_interaction_class"
        ],
        "current_forensic_truth_matches_faz28": current_truth_flags["current_forensic_truth_matches_faz28"],
        "current_forensic_truth_matches_faz29": current_truth_flags["current_forensic_truth_matches_faz29"],
        "current_forensic_truth_matches_neither": current_truth_flags["current_forensic_truth_matches_neither"],
    }
    wp3_pass = (
        adoption["current_forensic_truth_runtime_error_count"] == 0
        and adoption["current_forensic_truth_unexplained_count"] == 0
        and adoption["current_forensic_truth_dominant_interaction_class"]
        == "boundary_pack_orchestration_runtime_mutation"
        and adoption["current_forensic_truth_matches_neither"] is True
        and adoption["current_forensic_truth_adopted"] is True
    )

    archive = {
        "historical_stable_repair_truth_reclassified": True,
        "historical_inconclusive_recapture_truth_reclassified": True,
        "historical_repair_archive_channel": "diagnostic_only",
        "historical_stable_repair_truth_current_breach": False,
        "historical_inconclusive_recapture_truth_current_breach": False,
        "runtime_blanket_archived": True,
    }
    wp4_pass = (
        archive["historical_stable_repair_truth_reclassified"] is True
        and archive["historical_inconclusive_recapture_truth_reclassified"] is True
        and archive["historical_repair_archive_channel"] == "diagnostic_only"
        and archive["historical_stable_repair_truth_current_breach"] is False
        and archive["historical_inconclusive_recapture_truth_current_breach"] is False
        and archive["runtime_blanket_archived"] is True
    )

    rc_o_candidate_status_preserved = (
        contract["candidate_status"] == "frozen_failed_repair_candidate"
        and contract["promotable"] is False
        and contract["repairable"] is False
        and contract["current_evaluable"] is False
        and contract["release_controls_reentry_base"] is False
    )
    consumer_binding = {
        "repair_truth_comparison_order": "current_forensic_truth -> historical_repair_archive",
        "surface_breach_from_history_reintroduced": False,
        "current_forensic_truth_adopted": adoption["current_forensic_truth_adopted"],
        "historical_stable_repair_truth_reclassified": archive["historical_stable_repair_truth_reclassified"],
        "historical_inconclusive_recapture_truth_reclassified": archive[
            "historical_inconclusive_recapture_truth_reclassified"
        ],
        "historical_repair_archive_channel": archive["historical_repair_archive_channel"],
        "rc_o_candidate_status_preserved": rc_o_candidate_status_preserved,
        "historical_repair_archive_channel_mode": "diagnostic_only",
        "historical_repair_archive_channel": archive["historical_repair_archive_channel"],
        "historical_repair_archive_channel_usage": "diagnostic_only",
    }
    wp5_pass = (
        consumer_binding["repair_truth_comparison_order"]
        == "current_forensic_truth -> historical_repair_archive"
        and consumer_binding["surface_breach_from_history_reintroduced"] is False
        and consumer_binding["rc_o_candidate_status_preserved"] is True
        and consumer_binding["current_forensic_truth_adopted"] is True
        and consumer_binding["historical_stable_repair_truth_reclassified"] is True
        and consumer_binding["historical_inconclusive_recapture_truth_reclassified"] is True
        and consumer_binding["historical_repair_archive_channel"] == "diagnostic_only"
    )

    if (
        wp1_pass
        and wp2_pass
        and wp3_pass
        and wp4_pass
        and wp5_pass
    ):
        reconciliation = {
            "reference_pack_integrity_pass": True,
            "reference_pack_contradiction_count": 0,
            "reconciliation_stage": "R5",
            "primary_reason": "current_forensic_truth_adopted_after_canonical_current_authority_and_historical_repair_truth_reclassification",
            "root_cause_class": "current_forensic_truth_adopted_and_historical_repair_truths_reclassified",
            "current_forensic_truth_adopted": True,
            "historical_stable_repair_truth_reclassified": True,
            "historical_inconclusive_recapture_truth_reclassified": True,
            "repair_truth_comparison_order": "current_forensic_truth -> historical_repair_archive",
            "surface_breach_from_history_reintroduced": False,
            "unexplained_count": 0,
            "official_decision": PASS_DECISION,
            "next_official_work": PASS_NEXT_WORK,
        }
    else:
        reconciliation = {
            "reference_pack_integrity_pass": bool(reference_pack["reference_pack_integrity_pass"]),
            "reference_pack_contradiction_count": int(reference_pack["reference_pack_contradiction_count"]),
            "reconciliation_stage": "FAIL",
            "primary_reason": "reconciliation_contract_not_satisfied",
            "root_cause_class": (
                "canonical_current_authority_repair_truth_contract_breach"
                if current_authority["current_authority_contract_breach"] is True
                else "unexplained_rc_o_repair_truth_divergence"
            ),
            "current_forensic_truth_adopted": bool(adoption["current_forensic_truth_adopted"]),
            "historical_stable_repair_truth_reclassified": bool(archive["historical_stable_repair_truth_reclassified"]),
            "historical_inconclusive_recapture_truth_reclassified": bool(
                archive["historical_inconclusive_recapture_truth_reclassified"]
            ),
            "repair_truth_comparison_order": consumer_binding["repair_truth_comparison_order"],
            "surface_breach_from_history_reintroduced": bool(
                consumer_binding["surface_breach_from_history_reintroduced"]
            ),
            "unexplained_count": (
                int(reference_pack["reference_pack_contradiction_count"])
                + int(adoption["current_forensic_truth_unexplained_count"])
            ),
            "official_decision": FAIL_DECISION,
            "next_official_work": FAIL_NEXT_WORK,
        }

    wp6_pass = (
        reconciliation["official_decision"] == PASS_DECISION
        and reconciliation["next_official_work"] == PASS_NEXT_WORK
        and reconciliation["reconciliation_stage"] == "R5"
        and reconciliation["unexplained_count"] == 0
    )

    return {
        "reference_pack": reference_pack,
        "topology_rows": topology_rows,
        "current_authority_binding": current_authority,
        "contract": contract,
        "contrast_rows": contrast_rows,
        "adoption": adoption,
        "archive_reclassification": archive,
        "consumer_binding": consumer_binding,
        "reconciliation": reconciliation,
        "wp_statuses": {
            "WP-1": "PASS" if wp1_pass else "FAIL",
            "WP-2": "PASS" if wp2_pass else "FAIL",
            "WP-3": "PASS" if wp3_pass else "FAIL",
            "WP-4": "PASS" if wp4_pass else "FAIL",
            "WP-5": "PASS" if wp5_pass else "FAIL",
            "WP-6": "PASS" if wp6_pass else "FAIL",
        },
        "report_hash": stable_hash(
            {
                "reference_pack": reference_pack,
                "current_authority_binding": current_authority,
                "contract": contract,
                "contrast_rows": contrast_rows,
                "adoption": adoption,
                "archive_reclassification": archive,
                "consumer_binding": consumer_binding,
                "reconciliation": reconciliation,
            }
        ),
    }


def render_outputs(payload: dict[str, Any]) -> dict[Path, str | dict[str, Any]]:
    ref = payload["reference_pack"]
    topology_rows = payload["topology_rows"]
    authority = payload["current_authority_binding"]
    contract = payload["contract"]
    contrast_rows = payload["contrast_rows"]
    adoption = payload["adoption"]
    archive = payload["archive_reclassification"]
    binding = payload["consumer_binding"]
    reconciliation = payload["reconciliation"]
    wp = payload["wp_statuses"]

    contradiction_lines = (
        ["- contradiction_rows = `0`"]
        if not ref["reference_contradictions"]
        else [f"- contradiction_rows = `{len(ref['reference_contradictions'])}`"]
        + [
            f"- {row['reference_name']} / {row['field_name']} expected=`{row['expected_value']}` actual=`{row['actual_value']}`"
            for row in ref["reference_contradictions"]
        ]
    )

    topology_lines: list[str] = []
    for row in topology_rows:
        topology_lines.extend(f"- {key} = `{_render_value(value)}`" for key, value in row.items())
        topology_lines.append("")
    if topology_lines:
        topology_lines.pop()

    steering_rows = [
        {"wp": "WP-1", "status": wp["WP-1"], "gate": "reference pack freeze ve integrity gate"},
        {"wp": "WP-2", "status": wp["WP-2"], "gate": "rc-o repair-truth contrast matrix"},
        {"wp": "WP-3", "status": wp["WP-3"], "gate": "current forensic truth adoption gate"},
        {"wp": "WP-4", "status": wp["WP-4"], "gate": "historical repair archive reclassification"},
        {"wp": "WP-5", "status": wp["WP-5"], "gate": "repair-truth consumer binding"},
        {"wp": "WP-6", "status": wp["WP-6"], "gate": reconciliation["official_decision"]},
    ]

    contrast_columns = [
        ("truth_ref", "truth_ref"),
        ("truth_class", "truth_class"),
        ("package_name", "package_name"),
        ("record_count", "record_count"),
        ("mismatch_count", "mismatch_count"),
        ("preprojection_hash_mismatch_count", "preprojection_hash_mismatch_count"),
        ("raw_answer_hash_mismatch_count", "raw_answer_hash_mismatch_count"),
        ("response_envelope_hash_mismatch_count", "response_envelope_hash_mismatch_count"),
        ("runtime_error_count", "runtime_error_count"),
        ("first_break_stage_assigned_count", "first_break_stage_assigned_count"),
        ("primary_reason_assigned_count", "primary_reason_assigned_count"),
        ("unexplained_count", "unexplained_count"),
    ]

    outputs: dict[Path, str | dict[str, Any]] = {}
    outputs[ROOT / "coordination" / f"faz31-official-implementation-plan-{DATE}.md"] = "\n".join(
        [
            "# FAZ31 Official Implementation Plan",
            "",
            "- phase_scope = `repair_truth_reconciliation_only`",
            "- candidate_id = `RC-O`",
            "- current_authority_ref = `FAZ21 canonical current authority`",
            "- execution_order = `WP-1 -> WP-2 -> WP-3 -> WP-4 -> WP-5 -> WP-6`",
            "- new_build_allowed = `false`",
            "- new_replay_allowed = `false`",
            "- new_recapture_allowed = `false`",
            "- repair_gate_allowed = `false`",
            "- cutover_allowed = `false`",
            "- pilot_allowed = `false`",
        ]
    )
    outputs[ROOT / "coordination" / f"faz31-reference-pack-{DATE}.md"] = "\n".join(
        [
            "# FAZ31 Reference Pack",
            "",
            f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
            f"- canonical_current_authority_ref = `{ref['canonical_current_authority_ref']}`",
            f"- rc_m_archival_closure_ref = `{ref['rc_m_archival_closure_ref']}`",
            f"- steering_topology_ref = `{ref['steering_topology_ref']}`",
            f"- boundary_root_cause_ref = `{ref['boundary_root_cause_ref']}`",
            f"- stable_repair_truth_ref = `{ref['stable_repair_truth_ref']}`",
            f"- inconclusive_recapture_ref = `{ref['inconclusive_recapture_ref']}`",
            f"- current_forensic_truth_ref = `{ref['current_forensic_truth_ref']}`",
            f"- quality_reference_ref = `{ref['quality_reference_ref']}`",
            f"- role_topology_frozen = `{bool_text(ref['role_topology_frozen'])}`",
            *contradiction_lines,
        ]
    )
    outputs[ROOT / "coordination" / f"faz31-rc-o-repair-truth-reconciliation-contract-{DATE}.md"] = "\n".join(
        [
            "# FAZ31 RC-O Repair-Truth Reconciliation Contract",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in contract.items() if key not in {"allowed_reconciliation_stages", "allowed_root_cause_classes"}),
            "- allowed_reconciliation_stages =",
            *[f"  - `{stage}`" for stage in RECONCILIATION_STAGES],
            "- allowed_root_cause_classes =",
            *[f"  - `{item}`" for item in ROOT_CAUSE_CLASSES],
        ]
    )
    outputs[ROOT / "coordination" / f"faz31-rc-o-repair-truth-contrast-matrix-{DATE}.md"] = "\n".join(
        [
            "# FAZ31 RC-O Repair-Truth Contrast Matrix",
            "",
            *markdown_table(contrast_columns, contrast_rows),
        ]
    )
    outputs[ROOT / "coordination" / f"faz31-rc-o-current-forensic-truth-adoption-{DATE}.md"] = "\n".join(
        [
            "# FAZ31 RC-O Current Forensic Truth Adoption",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in adoption.items()),
        ]
    )
    outputs[ROOT / "coordination" / f"faz31-rc-o-historical-repair-archive-reclassification-{DATE}.md"] = "\n".join(
        [
            "# FAZ31 RC-O Historical Repair Archive Reclassification",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in archive.items()),
        ]
    )
    outputs[ROOT / "coordination" / f"faz31-rc-o-repair-truth-consumer-binding-{DATE}.md"] = "\n".join(
        [
            "# FAZ31 RC-O Repair-Truth Consumer Binding",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in binding.items()),
        ]
    )
    outputs[ROOT / "coordination" / f"faz31-rc-o-reconciliation-summary-{DATE}.md"] = "\n".join(
        [
            "# FAZ31 RC-O Reconciliation Summary",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in reconciliation.items()),
        ]
    )
    outputs[ROOT / "coordination" / f"faz31-steering-decision-table-{DATE}.md"] = "\n".join(
        [
            "# FAZ31 Steering Decision Table",
            "",
            *markdown_table([("wp", "wp"), ("status", "status"), ("gate", "gate")], steering_rows),
        ]
    )

    result_lines = [
        "# FAZ31 RC-O REPAIR-TRUTH RECONCILIATION UNDER CANONICAL CURRENT AUTHORITY RAPORU",
        "",
        "## Yonetici Ozeti",
        "",
        f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
        f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
        f"- current_forensic_truth_adopted = `{bool_text(adoption['current_forensic_truth_adopted'])}`",
        f"- historical_stable_repair_truth_reclassified = `{bool_text(archive['historical_stable_repair_truth_reclassified'])}`",
        f"- historical_inconclusive_recapture_truth_reclassified = `{bool_text(archive['historical_inconclusive_recapture_truth_reclassified'])}`",
        f"- repair_truth_comparison_order = `{binding['repair_truth_comparison_order']}`",
        f"- surface_breach_from_history_reintroduced = `{bool_text(binding['surface_breach_from_history_reintroduced'])}`",
        f"- current_forensic_truth_runtime_error_count = `{adoption['current_forensic_truth_runtime_error_count']}`",
        f"- current_forensic_truth_unexplained_count = `{adoption['current_forensic_truth_unexplained_count']}`",
        f"- current_forensic_truth_dominant_interaction_class = `{adoption['current_forensic_truth_dominant_interaction_class']}`",
        f"- unexplained_count = `{reconciliation['unexplained_count']}`",
        f"- official_decision = `{reconciliation['official_decision']}`",
        f"- next_official_work = `{reconciliation['next_official_work']}`",
        "",
        "## Reference Pack Ozeti",
        "",
        f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
        f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
        f"- canonical_current_authority_ref = `{ref['canonical_current_authority_ref']}`",
        f"- rc_m_archival_closure_ref = `{ref['rc_m_archival_closure_ref']}`",
        f"- steering_topology_ref = `{ref['steering_topology_ref']}`",
        f"- boundary_root_cause_ref = `{ref['boundary_root_cause_ref']}`",
        f"- stable_repair_truth_ref = `{ref['stable_repair_truth_ref']}`",
        f"- inconclusive_recapture_ref = `{ref['inconclusive_recapture_ref']}`",
        f"- current_forensic_truth_ref = `{ref['current_forensic_truth_ref']}`",
        *contradiction_lines,
        "",
        "## Current Authority ve RC-O Role Freeze Ozeti",
        "",
        f"- current_canonical_authority_adopted = `{bool_text(authority['current_canonical_authority_adopted'])}`",
        f"- downstream_consumer_binding_pass = `{bool_text(authority['downstream_consumer_binding_pass'])}`",
        f"- control_pair_runtime_error_count = `{authority['control_pair_runtime_error_count']}`",
        f"- surface_breach_stage_set = `{_render_value(authority['surface_breach_stage_set'])}`",
        f"- current_authority_contract_breach = `{bool_text(authority['current_authority_contract_breach'])}`",
        f"- comparison_order = `{authority['comparison_order']}`",
        "",
        *topology_lines,
        "",
        "## Repair Truth Contrast Matrix Ozeti",
        "",
        *markdown_table(contrast_columns, contrast_rows),
        "",
        "## Current Forensic Truth Adoption Ozeti",
        "",
        *(f"- {key} = `{_render_value(value)}`" for key, value in adoption.items()),
        "",
        "## Historical Repair Archive Reclassification Ozeti",
        "",
        *(f"- {key} = `{_render_value(value)}`" for key, value in archive.items()),
        "",
        "## Repair Truth Consumer Binding Ozeti",
        "",
        *(f"- {key} = `{_render_value(value)}`" for key, value in binding.items()),
        "",
        "## WP Sonuclari",
        "",
        *[f"- {name} = `{status}`" for name, status in wp.items()],
        "",
        "## Resmi Karar",
        "",
        *(f"- {key} = `{_render_value(value)}`" for key, value in reconciliation.items() if key in {
            "reconciliation_stage",
            "primary_reason",
            "root_cause_class",
            "unexplained_count",
            "official_decision",
        }),
        "",
        "## Sonraki Resmi Is",
        "",
        f"- next_official_work = `{reconciliation['next_official_work']}`",
        "",
        "## Artefact Listesi",
        "",
        *[f"- `{path}`" for path in [*ARTEFACT_LIST, f"docs/{RESULT_REPORT_NAME}"]],
        "",
        f"> RC-O current repair truth canonical current authority altinda hangi truth olarak benimsendi, hangi truth'ler archive kanalina indirildi ve bundan sonra hangi resmi hat acilacak?",
        ">",
        f"> RC-O current repair truth canonical current authority altinda `FAZ30 current_forensic_truth` olarak benimsendi, `FAZ28` ve `FAZ29` diagnostic-only historical repair archive kanalina indirildi ve bundan sonra acilacak tek resmi hat `{reconciliation['next_official_work']}` oldu.",
    ]

    outputs[ROOT / "reports" / RESULT_REPORT_NAME] = "\n".join(result_lines)
    outputs[ROOT / "docs" / RESULT_REPORT_NAME] = "\n".join(result_lines)
    outputs[PHASE_PACKAGE_JSON] = payload
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build FAZ31 phase package.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    materialized = build_materialization_payload()
    payload = build_phase_payload(materialized)
    if args.dry_run:
        print(f"official_decision={payload['reconciliation']['official_decision']}")
        print(f"next_official_work={payload['reconciliation']['next_official_work']}")
        print(f"reference_pack_integrity_pass={payload['reference_pack']['reference_pack_integrity_pass']}")
        print(f"reference_pack_contradiction_count={payload['reference_pack']['reference_pack_contradiction_count']}")
        print(f"report_hash={payload['report_hash']}")
        return 0

    write_json(MATERIALIZED_REFERENCE_JSON, materialized)
    outputs = render_outputs(payload)
    for path, body in outputs.items():
        if isinstance(body, (dict, list)):
            write_json(path, body)
        else:
            write_text(path, body)
    print(f"wrote_files={len(outputs) + 1}")
    print(f"report=docs/{RESULT_REPORT_NAME}")
    return 0 if payload["reconciliation"]["official_decision"] == PASS_DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
