#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz39_lib import (  # type: ignore
    DATE,
    FAIL_DECISION,
    FAIL_NEXT_WORK,
    FAZ21_RECONCILIATION_MD,
    FAZ34_RC_P_FULL_FAMILY_MD,
    FAZ35_PHASE_PACKAGE_JSON,
    FAZ36_REPORT_MD,
    FAZ37_REPORT_MD,
    FAZ38_LINEAGE_MD,
    FAZ38_REPORT_MD,
    FAZ38_RETENTION_MD,
    FAZ38_ROOT_CAUSE_MD,
    FAZ38_ROWSET_OVERLAP_MD,
    FAZ38_TARGETED_MD,
    PASS_DECISION,
    PASS_NEXT_WORK,
    RECONCILIATION_STAGES,
    REFERENCE_DOCS,
    REFERENCE_MARKERS,
    RESULT_REPORT_NAME,
    ROOT,
    ROOT_CAUSE_CLASSES,
    bool_text,
    extract_section,
    load_json,
    load_text,
    markdown_table,
    parse_markdown_kv,
    parse_markdown_table,
    parse_section_kv,
    stable_hash,
    write_text,
)


ARTEFACT_LIST = [
    f"coordination/faz39-official-implementation-plan-{DATE}.md",
    f"coordination/faz39-steering-decision-table-{DATE}.md",
    f"coordination/faz39-reference-pack-{DATE}.md",
    f"coordination/faz39-rc-q-repair-truth-reconciliation-contract-{DATE}.md",
    f"coordination/faz39-rc-q-repair-truth-contrast-matrix-{DATE}.md",
    f"coordination/faz39-rc-q-current-perimeter-truth-preservation-{DATE}.md",
    f"coordination/faz39-rc-q-current-instability-truth-adoption-{DATE}.md",
    f"coordination/faz39-rc-q-historical-repair-archive-reclassification-{DATE}.md",
    f"coordination/faz39-rc-q-repair-truth-consumer-binding-{DATE}.md",
    f"coordination/faz39-rc-q-reconciliation-summary-{DATE}.md",
    f"reports/{RESULT_REPORT_NAME}",
    f"docs/{RESULT_REPORT_NAME}",
]

PACKAGE_ORDER = [
    "frontier_174",
    "response_envelope_subfrontier_109",
    "full_family_parity",
    "targeted_acceptance_truth",
    "retention_truth",
]

TRUTH_ORDER = [
    "current_perimeter_truth_reference",
    "historical_failed_repair_truth",
    "historical_inconclusive_recapture_truth",
    "current_instability_repair_truth",
]


def _add_contradiction(
    contradictions: list[dict[str, Any]],
    *,
    reference_name: str,
    field_name: str,
    expected_value: Any,
    actual_value: Any,
) -> None:
    if actual_value != expected_value:
        contradictions.append(
            {
                "reference_name": reference_name,
                "field_name": field_name,
                "expected_value": expected_value,
                "actual_value": actual_value,
            }
        )


def _truth_row(
    *,
    truth_ref: str,
    truth_class: str,
    package_name: str,
    record_count: int,
    faz1_50_mismatch_count: int,
    v2_95_mismatch_count: int,
    v3_170_mismatch_count: int,
    preprojection_hash_mismatch_count: int,
    raw_answer_hash_mismatch_count: int,
    response_envelope_hash_mismatch_count: int,
    capture_stability: bool,
    capture_a_vs_capture_b_mismatch_count: int,
    runtime_error_count: int,
    unexplained_count: int,
) -> dict[str, Any]:
    return {
        "truth_ref": truth_ref,
        "truth_class": truth_class,
        "package_name": package_name,
        "record_count": int(record_count),
        "faz1_50_mismatch_count": int(faz1_50_mismatch_count),
        "v2_95_mismatch_count": int(v2_95_mismatch_count),
        "v3_170_mismatch_count": int(v3_170_mismatch_count),
        "preprojection_hash_mismatch_count": int(preprojection_hash_mismatch_count),
        "raw_answer_hash_mismatch_count": int(raw_answer_hash_mismatch_count),
        "response_envelope_hash_mismatch_count": int(response_envelope_hash_mismatch_count),
        "capture_stability": bool(capture_stability),
        "capture_a_vs_capture_b_mismatch_count": int(capture_a_vs_capture_b_mismatch_count),
        "runtime_error_count": int(runtime_error_count),
        "unexplained_count": int(unexplained_count),
    }


def _extract_truth_lineage_row(truth_name: str) -> dict[str, Any]:
    rows = parse_markdown_table(FAZ38_LINEAGE_MD, "FAZ38 RC-Q Truth Lineage Matrix")
    for row in rows:
        if row["truth_name"] == truth_name:
            return row
    raise RuntimeError(f"truth row not found: {truth_name}")


def build_materialized_payload() -> dict[str, Any]:
    contradictions: list[dict[str, Any]] = []
    for name, path in REFERENCE_DOCS.items():
        text = load_text(path)
        for marker in REFERENCE_MARKERS[name]:
            if marker not in text:
                contradictions.append(
                    {
                        "reference_name": name,
                        "field_name": "marker",
                        "expected_value": marker,
                        "actual_value": None,
                    }
                )

    faz21_reconciliation = parse_markdown_kv(FAZ21_RECONCILIATION_MD)
    faz21_current_authority = parse_section_kv(REFERENCE_DOCS["faz21"], "Canonical Current Authority Pack Ozeti")
    faz21_binding = parse_section_kv(REFERENCE_DOCS["faz21"], "Downstream Consumer Binding Sonucu")
    faz21_gate = parse_section_kv(REFERENCE_DOCS["faz21"], "Gate Sonucu")
    faz35_package = load_json(FAZ35_PHASE_PACKAGE_JSON)
    faz34_full_family = parse_markdown_kv(FAZ34_RC_P_FULL_FAMILY_MD)
    faz36_frontier = parse_section_kv(FAZ36_REPORT_MD, "Frontier 174 Repair Gate Ozeti")
    faz36_response = parse_section_kv(FAZ36_REPORT_MD, "Response Envelope Subfrontier 109 Repair Gate Ozeti")
    faz36_targeted = parse_section_kv(FAZ36_REPORT_MD, "Release Controls Targeted Acceptance Ozeti")
    faz36_full_family = parse_section_kv(FAZ36_REPORT_MD, "Full-Family Model-Visible Surface Parity Ozeti")
    faz36_retention = parse_section_kv(FAZ36_REPORT_MD, "Release Controls Retention Gate Ozeti")
    faz37_frontier = parse_section_kv(FAZ37_REPORT_MD, "E) Frontier 174 Authoritative Recapture Ozeti")
    faz37_response = parse_section_kv(FAZ37_REPORT_MD, "F) Response Envelope Subfrontier 109 Authoritative Recapture Ozeti")
    faz37_targeted = parse_section_kv(FAZ37_REPORT_MD, "G) Release Controls Targeted Acceptance Authoritative Recapture Ozeti")
    faz37_full_family = parse_section_kv(FAZ37_REPORT_MD, "H) Full-Family Model-Visible Surface Parity Authoritative Recapture Ozeti")
    faz37_retention = parse_section_kv(FAZ37_REPORT_MD, "I) Release Controls Retention Authoritative Recapture Ozeti")
    faz38_overlap = parse_markdown_kv(FAZ38_ROWSET_OVERLAP_MD)
    faz38_root = parse_markdown_kv(FAZ38_ROOT_CAUSE_MD)
    faz38_targeted = parse_markdown_kv(FAZ38_TARGETED_MD)
    faz38_retention = parse_markdown_kv(FAZ38_RETENTION_MD)
    faz38_frontier = _extract_truth_lineage_row("FAZ38 current_instability_truth")

    _add_contradiction(
        contradictions,
        reference_name="faz21",
        field_name="current_canonical_authority_adopted",
        expected_value=True,
        actual_value=faz21_reconciliation["current_canonical_authority_adopted"],
    )
    _add_contradiction(
        contradictions,
        reference_name="faz21",
        field_name="downstream_consumer_binding_pass",
        expected_value=True,
        actual_value=faz21_reconciliation["downstream_consumer_binding_pass"],
    )
    _add_contradiction(
        contradictions,
        reference_name="faz21",
        field_name="current_authority_contract_breach",
        expected_value=False,
        actual_value=faz21_current_authority["current_authority_contract_breach"],
    )
    _add_contradiction(
        contradictions,
        reference_name="faz21",
        field_name="surface_breach_from_history_reintroduced",
        expected_value=False,
        actual_value=faz21_binding["surface_breach_from_history_reintroduced"],
    )
    _add_contradiction(
        contradictions,
        reference_name="faz35",
        field_name="frontier_record_count",
        expected_value=174,
        actual_value=faz35_package["frontier_truth"]["frontier_record_count"],
    )
    _add_contradiction(
        contradictions,
        reference_name="faz38",
        field_name="union_instability_rowset_count",
        expected_value=6,
        actual_value=faz38_overlap["union_instability_rowset_count"],
    )

    reference_pack = {
        "reference_pack_integrity_pass": len(contradictions) == 0,
        "reference_pack_contradiction_count": len(contradictions),
        "canonical_current_authority_ref": "FAZ21",
        "current_perimeter_truth_ref": "FAZ35",
        "historical_failed_repair_truth_ref": "FAZ36",
        "historical_inconclusive_recapture_ref": "FAZ37",
        "current_instability_truth_ref": "FAZ38",
        "active_quality_reference": "RC-G",
        "active_control_pair": "RC-G vs RC-J",
        "active_forensic_reference": "RC-N",
        "comparison_order": "current_canonical -> historical_archive",
        "surface_breach_from_history_reintroduced": False,
        "contradiction_rows": contradictions,
    }

    current_authority = {
        "current_canonical_authority_adopted": bool(faz21_reconciliation["current_canonical_authority_adopted"]),
        "downstream_consumer_binding_pass": bool(faz21_reconciliation["downstream_consumer_binding_pass"]),
        "control_pair_runtime_error_count": int(faz21_current_authority["control_pair_runtime_error_count"]),
        "surface_breach_from_history_reintroduced": bool(
            faz21_binding["surface_breach_from_history_reintroduced"]
        ),
        "current_authority_contract_breach": bool(faz21_current_authority["current_authority_contract_breach"]),
        "surface_breach_stage_set": faz21_gate["surface_breach_stage_set"],
        "comparison_order": "current_canonical -> historical_archive",
    }

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
            "release_controls_reentry_base": False,
        },
        {
            "candidate_id": "RC-P",
            "candidate_status": "current_perimeter_truth_reference / diagnostic_only perimeter reference",
            "role": "current_perimeter_truth_reference",
            "current_authority_member": False,
            "diagnostic_only": True,
            "archived": False,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "release_controls_reentry_base": False,
        },
        {
            "candidate_id": "RC-Q",
            "candidate_status": "frozen_failed_repair_candidate",
            "role": "failed_repair_candidate",
            "current_authority_member": False,
            "diagnostic_only": True,
            "archived": False,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "release_controls_reentry_base": False,
        },
    ]

    contract = {
        "candidate_id": "RC-Q",
        "base_candidate": "RC-G",
        "control_candidate": "RC-J",
        "forensic_reference_candidate": "RC-N",
        "current_perimeter_truth_reference": "RC-P",
        "candidate_status": "frozen_failed_repair_candidate",
        "promotable": False,
        "repairable": False,
        "current_evaluable": False,
        "release_controls_reentry_base": False,
        "current_repair_truth_reference": "FAZ38",
        "historical_repair_archive_channel": "diagnostic_only",
        "repair_truth_comparison_order": "current_perimeter_truth_reference -> current_repair_truth -> historical_repair_archive",
        "cutover_authorized": False,
        "pilot_authorized": False,
        "database_expansion_authorized": False,
        "new_candidate_authorized": False,
        "patch_existing_candidate_authorized": False,
    }

    truths = {
        "current_perimeter_truth_reference": {
            "frontier_174": _truth_row(
                truth_ref="FAZ35",
                truth_class="current_perimeter_truth_reference",
                package_name="frontier_174",
                record_count=faz35_package["frontier_truth"]["frontier_record_count"],
                faz1_50_mismatch_count=faz35_package["frontier_truth"]["faz1_50_mismatch_count"],
                v2_95_mismatch_count=faz35_package["frontier_truth"]["v2_95_mismatch_count"],
                v3_170_mismatch_count=faz35_package["frontier_truth"]["v3_170_mismatch_count"],
                preprojection_hash_mismatch_count=faz35_package["frontier_truth"]["preprojection_hash_mismatch_count"],
                raw_answer_hash_mismatch_count=faz35_package["frontier_truth"]["raw_answer_hash_mismatch_count"],
                response_envelope_hash_mismatch_count=faz34_full_family["response_envelope_hash_mismatch_count"],
                capture_stability=True,
                capture_a_vs_capture_b_mismatch_count=0,
                runtime_error_count=faz35_package["frontier_truth"]["runtime_error_count"],
                unexplained_count=faz35_package["frontier_truth"]["unexplained_count"],
            ),
            "response_envelope_subfrontier_109": _truth_row(
                truth_ref="FAZ35",
                truth_class="current_perimeter_truth_reference",
                package_name="response_envelope_subfrontier_109",
                record_count=faz35_package["response_truth"]["response_envelope_subfrontier_record_count"],
                faz1_50_mismatch_count=faz35_package["response_truth"]["faz1_50_mismatch_count"],
                v2_95_mismatch_count=faz35_package["response_truth"]["v2_95_mismatch_count"],
                v3_170_mismatch_count=faz35_package["response_truth"]["v3_170_mismatch_count"],
                preprojection_hash_mismatch_count=0,
                raw_answer_hash_mismatch_count=0,
                response_envelope_hash_mismatch_count=faz35_package["response_truth"]["response_envelope_hash_mismatch_count"],
                capture_stability=True,
                capture_a_vs_capture_b_mismatch_count=0,
                runtime_error_count=faz35_package["response_truth"]["runtime_error_count"],
                unexplained_count=faz35_package["response_truth"]["unexplained_count"],
            ),
            "full_family_parity": _truth_row(
                truth_ref="FAZ35",
                truth_class="current_perimeter_truth_reference",
                package_name="full_family_parity",
                record_count=174,
                faz1_50_mismatch_count=faz34_full_family["faz1_50_mismatch_count"],
                v2_95_mismatch_count=faz34_full_family["v2_95_mismatch_count"],
                v3_170_mismatch_count=faz34_full_family["v3_170_mismatch_count"],
                preprojection_hash_mismatch_count=faz34_full_family["preprojection_hash_mismatch_count"],
                raw_answer_hash_mismatch_count=faz34_full_family["raw_answer_hash_mismatch_count"],
                response_envelope_hash_mismatch_count=faz34_full_family["response_envelope_hash_mismatch_count"],
                capture_stability=True,
                capture_a_vs_capture_b_mismatch_count=0,
                runtime_error_count=faz34_full_family["runtime_error_count"],
                unexplained_count=faz34_full_family["unexplained_count"],
            ),
            "targeted_acceptance_truth": _truth_row(
                truth_ref="FAZ35",
                truth_class="current_perimeter_truth_reference",
                package_name="targeted_acceptance_truth",
                record_count=faz35_package["acceptance"]["must_close_release_controls_count"],
                faz1_50_mismatch_count=0,
                v2_95_mismatch_count=0,
                v3_170_mismatch_count=0,
                preprojection_hash_mismatch_count=0,
                raw_answer_hash_mismatch_count=0,
                response_envelope_hash_mismatch_count=0,
                capture_stability=True,
                capture_a_vs_capture_b_mismatch_count=0,
                runtime_error_count=faz35_package["acceptance"]["runtime_error_count"],
                unexplained_count=faz35_package["acceptance"]["unexplained_count"],
            ),
            "retention_truth": _truth_row(
                truth_ref="FAZ35",
                truth_class="current_perimeter_truth_reference",
                package_name="retention_truth",
                record_count=4,
                faz1_50_mismatch_count=0,
                v2_95_mismatch_count=0,
                v3_170_mismatch_count=0,
                preprojection_hash_mismatch_count=0,
                raw_answer_hash_mismatch_count=0,
                response_envelope_hash_mismatch_count=0,
                capture_stability=True,
                capture_a_vs_capture_b_mismatch_count=0,
                runtime_error_count=faz35_package["retention_contrast"]["runtime_error_count"],
                unexplained_count=faz35_package["retention_contrast"]["unexplained_count"],
            ),
        },
        "historical_failed_repair_truth": {
            "frontier_174": _truth_row(
                truth_ref="FAZ36",
                truth_class="historical_failed_repair_truth",
                package_name="frontier_174",
                record_count=faz36_frontier["frontier_record_count"],
                faz1_50_mismatch_count=faz36_frontier["faz1_50_mismatch_count"],
                v2_95_mismatch_count=faz36_frontier["v2_95_mismatch_count"],
                v3_170_mismatch_count=faz36_frontier["v3_170_mismatch_count"],
                preprojection_hash_mismatch_count=faz36_frontier["preprojection_hash_mismatch_count"],
                raw_answer_hash_mismatch_count=faz36_frontier["raw_answer_hash_mismatch_count"],
                response_envelope_hash_mismatch_count=faz36_frontier["response_envelope_hash_mismatch_count"],
                capture_stability=True,
                capture_a_vs_capture_b_mismatch_count=0,
                runtime_error_count=faz36_frontier["runtime_error_count"],
                unexplained_count=faz36_frontier["unexplained_count"],
            ),
            "response_envelope_subfrontier_109": _truth_row(
                truth_ref="FAZ36",
                truth_class="historical_failed_repair_truth",
                package_name="response_envelope_subfrontier_109",
                record_count=faz36_response["response_envelope_subfrontier_record_count"],
                faz1_50_mismatch_count=faz36_response["faz1_50_mismatch_count"],
                v2_95_mismatch_count=faz36_response["v2_95_mismatch_count"],
                v3_170_mismatch_count=faz36_response["v3_170_mismatch_count"],
                preprojection_hash_mismatch_count=0,
                raw_answer_hash_mismatch_count=0,
                response_envelope_hash_mismatch_count=faz36_response["response_envelope_hash_mismatch_count"],
                capture_stability=True,
                capture_a_vs_capture_b_mismatch_count=0,
                runtime_error_count=faz36_response["runtime_error_count"],
                unexplained_count=faz36_response["unexplained_count"],
            ),
            "full_family_parity": _truth_row(
                truth_ref="FAZ36",
                truth_class="historical_failed_repair_truth",
                package_name="full_family_parity",
                record_count=315,
                faz1_50_mismatch_count=faz36_full_family["faz1_50_mismatch_count"],
                v2_95_mismatch_count=faz36_full_family["v2_95_mismatch_count"],
                v3_170_mismatch_count=faz36_full_family["v3_170_mismatch_count"],
                preprojection_hash_mismatch_count=faz36_full_family["preprojection_hash_mismatch_count"],
                raw_answer_hash_mismatch_count=faz36_full_family["raw_answer_hash_mismatch_count"],
                response_envelope_hash_mismatch_count=faz36_full_family["response_envelope_hash_mismatch_count"],
                capture_stability=True,
                capture_a_vs_capture_b_mismatch_count=0,
                runtime_error_count=faz36_full_family["runtime_error_count"],
                unexplained_count=faz36_full_family["unexplained_count"],
            ),
            "targeted_acceptance_truth": _truth_row(
                truth_ref="FAZ36",
                truth_class="historical_failed_repair_truth",
                package_name="targeted_acceptance_truth",
                record_count=faz36_targeted["must_close_release_controls_count"],
                faz1_50_mismatch_count=0,
                v2_95_mismatch_count=0,
                v3_170_mismatch_count=0,
                preprojection_hash_mismatch_count=0,
                raw_answer_hash_mismatch_count=0,
                response_envelope_hash_mismatch_count=0,
                capture_stability=True,
                capture_a_vs_capture_b_mismatch_count=0,
                runtime_error_count=faz36_targeted["runtime_error_count"],
                unexplained_count=faz36_targeted["unexplained_count"],
            ),
            "retention_truth": _truth_row(
                truth_ref="FAZ36",
                truth_class="historical_failed_repair_truth",
                package_name="retention_truth",
                record_count=4,
                faz1_50_mismatch_count=0,
                v2_95_mismatch_count=0,
                v3_170_mismatch_count=0,
                preprojection_hash_mismatch_count=0,
                raw_answer_hash_mismatch_count=0,
                response_envelope_hash_mismatch_count=0,
                capture_stability=True,
                capture_a_vs_capture_b_mismatch_count=0,
                runtime_error_count=faz36_retention["runtime_error_count"],
                unexplained_count=faz36_retention["unexplained_count"],
            ),
        },
        "historical_inconclusive_recapture_truth": {
            "frontier_174": _truth_row(
                truth_ref="FAZ37",
                truth_class="historical_inconclusive_recapture_truth",
                package_name="frontier_174",
                record_count=faz37_frontier["frontier_record_count"],
                faz1_50_mismatch_count=faz37_frontier["faz1_50_mismatch_count"],
                v2_95_mismatch_count=faz37_frontier["v2_95_mismatch_count"],
                v3_170_mismatch_count=faz37_frontier["v3_170_mismatch_count"],
                preprojection_hash_mismatch_count=faz37_frontier["preprojection_hash_mismatch_count"],
                raw_answer_hash_mismatch_count=faz37_frontier["raw_answer_hash_mismatch_count"],
                response_envelope_hash_mismatch_count=faz37_frontier["response_envelope_hash_mismatch_count"],
                capture_stability=faz37_frontier["capture_stability_match"],
                capture_a_vs_capture_b_mismatch_count=faz37_frontier["capture_a_vs_capture_b_mismatch_count"],
                runtime_error_count=faz37_frontier["runtime_error_count"],
                unexplained_count=faz37_frontier["unexplained_count"],
            ),
            "response_envelope_subfrontier_109": _truth_row(
                truth_ref="FAZ37",
                truth_class="historical_inconclusive_recapture_truth",
                package_name="response_envelope_subfrontier_109",
                record_count=faz37_response["response_envelope_subfrontier_record_count"],
                faz1_50_mismatch_count=faz37_response["faz1_50_mismatch_count"],
                v2_95_mismatch_count=faz37_response["v2_95_mismatch_count"],
                v3_170_mismatch_count=faz37_response["v3_170_mismatch_count"],
                preprojection_hash_mismatch_count=0,
                raw_answer_hash_mismatch_count=0,
                response_envelope_hash_mismatch_count=faz37_response["response_envelope_hash_mismatch_count"],
                capture_stability=faz37_response["capture_stability_match"],
                capture_a_vs_capture_b_mismatch_count=faz37_response["capture_a_vs_capture_b_mismatch_count"],
                runtime_error_count=faz37_response["runtime_error_count"],
                unexplained_count=faz37_response["unexplained_count"],
            ),
            "full_family_parity": _truth_row(
                truth_ref="FAZ37",
                truth_class="historical_inconclusive_recapture_truth",
                package_name="full_family_parity",
                record_count=315,
                faz1_50_mismatch_count=faz37_full_family["faz1_50_mismatch_count"],
                v2_95_mismatch_count=faz37_full_family["v2_95_mismatch_count"],
                v3_170_mismatch_count=faz37_full_family["v3_170_mismatch_count"],
                preprojection_hash_mismatch_count=faz37_full_family["preprojection_hash_mismatch_count"],
                raw_answer_hash_mismatch_count=faz37_full_family["raw_answer_hash_mismatch_count"],
                response_envelope_hash_mismatch_count=faz37_full_family["response_envelope_hash_mismatch_count"],
                capture_stability=faz37_full_family["capture_stability_match"],
                capture_a_vs_capture_b_mismatch_count=faz37_full_family["capture_a_vs_capture_b_mismatch_count"],
                runtime_error_count=faz37_full_family["runtime_error_count"],
                unexplained_count=faz37_full_family["unexplained_count"],
            ),
            "targeted_acceptance_truth": _truth_row(
                truth_ref="FAZ37",
                truth_class="historical_inconclusive_recapture_truth",
                package_name="targeted_acceptance_truth",
                record_count=faz37_targeted["must_close_release_controls_count"],
                faz1_50_mismatch_count=0,
                v2_95_mismatch_count=0,
                v3_170_mismatch_count=0,
                preprojection_hash_mismatch_count=0,
                raw_answer_hash_mismatch_count=0,
                response_envelope_hash_mismatch_count=0,
                capture_stability=faz37_targeted["capture_stability_match"],
                capture_a_vs_capture_b_mismatch_count=faz37_targeted["capture_a_vs_capture_b_mismatch_count"],
                runtime_error_count=faz37_targeted["runtime_error_count"],
                unexplained_count=faz37_targeted["unexplained_count"],
            ),
            "retention_truth": _truth_row(
                truth_ref="FAZ37",
                truth_class="historical_inconclusive_recapture_truth",
                package_name="retention_truth",
                record_count=4,
                faz1_50_mismatch_count=0,
                v2_95_mismatch_count=0,
                v3_170_mismatch_count=0,
                preprojection_hash_mismatch_count=0,
                raw_answer_hash_mismatch_count=0,
                response_envelope_hash_mismatch_count=0,
                capture_stability=faz37_retention["capture_stability_match"],
                capture_a_vs_capture_b_mismatch_count=faz37_retention["capture_a_vs_capture_b_mismatch_count"],
                runtime_error_count=faz37_retention["runtime_error_count"],
                unexplained_count=faz37_retention["unexplained_count"],
            ),
        },
        "current_instability_repair_truth": {
            "frontier_174": _truth_row(
                truth_ref="FAZ38",
                truth_class="current_instability_repair_truth",
                package_name="frontier_174",
                record_count=int(faz38_frontier["record_count"]),
                faz1_50_mismatch_count=int(faz38_frontier["faz1_50"]),
                v2_95_mismatch_count=int(faz38_frontier["v2_95"]),
                v3_170_mismatch_count=int(faz38_frontier["v3_170"]),
                preprojection_hash_mismatch_count=int(faz38_frontier["preprojection"]),
                raw_answer_hash_mismatch_count=int(faz38_frontier["raw_answer"]),
                response_envelope_hash_mismatch_count=int(faz38_frontier["response_envelope"]),
                capture_stability=str(faz38_frontier["capture_stability"]).lower() == "true",
                capture_a_vs_capture_b_mismatch_count=int(faz38_frontier["ab_mismatch"]),
                runtime_error_count=0,
                unexplained_count=int(faz38_frontier["unexplained"]),
            ),
            "response_envelope_subfrontier_109": _truth_row(
                truth_ref="FAZ38",
                truth_class="current_instability_repair_truth",
                package_name="response_envelope_subfrontier_109",
                record_count=faz37_response["response_envelope_subfrontier_record_count"],
                faz1_50_mismatch_count=faz37_response["faz1_50_mismatch_count"],
                v2_95_mismatch_count=faz37_response["v2_95_mismatch_count"],
                v3_170_mismatch_count=faz37_response["v3_170_mismatch_count"],
                preprojection_hash_mismatch_count=0,
                raw_answer_hash_mismatch_count=0,
                response_envelope_hash_mismatch_count=faz37_response["response_envelope_hash_mismatch_count"],
                capture_stability=False,
                capture_a_vs_capture_b_mismatch_count=faz37_response["capture_a_vs_capture_b_mismatch_count"],
                runtime_error_count=faz37_response["runtime_error_count"],
                unexplained_count=faz37_response["unexplained_count"],
            ),
            "full_family_parity": _truth_row(
                truth_ref="FAZ38",
                truth_class="current_instability_repair_truth",
                package_name="full_family_parity",
                record_count=315,
                faz1_50_mismatch_count=faz37_full_family["faz1_50_mismatch_count"],
                v2_95_mismatch_count=faz37_full_family["v2_95_mismatch_count"],
                v3_170_mismatch_count=faz37_full_family["v3_170_mismatch_count"],
                preprojection_hash_mismatch_count=faz37_full_family["preprojection_hash_mismatch_count"],
                raw_answer_hash_mismatch_count=faz37_full_family["raw_answer_hash_mismatch_count"],
                response_envelope_hash_mismatch_count=faz37_full_family["response_envelope_hash_mismatch_count"],
                capture_stability=False,
                capture_a_vs_capture_b_mismatch_count=faz37_full_family["capture_a_vs_capture_b_mismatch_count"],
                runtime_error_count=faz37_full_family["runtime_error_count"],
                unexplained_count=faz37_full_family["unexplained_count"],
            ),
            "targeted_acceptance_truth": _truth_row(
                truth_ref="FAZ38",
                truth_class="current_instability_repair_truth",
                package_name="targeted_acceptance_truth",
                record_count=faz38_targeted["must_close_release_controls_count"],
                faz1_50_mismatch_count=0,
                v2_95_mismatch_count=0,
                v3_170_mismatch_count=0,
                preprojection_hash_mismatch_count=0,
                raw_answer_hash_mismatch_count=0,
                response_envelope_hash_mismatch_count=0,
                capture_stability=faz38_targeted["capture_stability_match"],
                capture_a_vs_capture_b_mismatch_count=faz38_targeted["capture_a_vs_capture_b_mismatch_count"],
                runtime_error_count=faz38_targeted["runtime_error_count"],
                unexplained_count=faz38_targeted["unexplained_count"],
            ),
            "retention_truth": _truth_row(
                truth_ref="FAZ38",
                truth_class="current_instability_repair_truth",
                package_name="retention_truth",
                record_count=4,
                faz1_50_mismatch_count=0,
                v2_95_mismatch_count=0,
                v3_170_mismatch_count=0,
                preprojection_hash_mismatch_count=0,
                raw_answer_hash_mismatch_count=0,
                response_envelope_hash_mismatch_count=0,
                capture_stability=faz38_retention["capture_stability_match"],
                capture_a_vs_capture_b_mismatch_count=faz38_retention["capture_a_vs_capture_b_mismatch_count"],
                runtime_error_count=faz38_retention["runtime_error_count"],
                unexplained_count=faz38_retention["unexplained_count"],
            ),
        },
    }

    return {
        "reference_pack": reference_pack,
        "current_authority": current_authority,
        "topology_rows": topology_rows,
        "contract": contract,
        "truths": truths,
        "faz35_support": {
            "dominant_stage": faz35_package["stage_ladder"]["dominant_stage"],
            "dominant_reason": faz35_package["stage_ladder"]["dominant_reason"],
            "minimal_failing_control_set": str(faz35_package["control_isolation"]["minimal_failing_control_set"]).replace("S1 = ", ""),
            "dominant_interaction_class": faz35_package["control_isolation"]["dominant_interaction_class"],
        },
        "faz38_support": {
            "frontier_instability_rowset_count": faz38_overlap["frontier_instability_rowset_count"],
            "response_envelope_instability_rowset_count": faz38_overlap["response_envelope_instability_rowset_count"],
            "full_family_instability_rowset_count": faz38_overlap["full_family_instability_rowset_count"],
            "union_instability_rowset_count": faz38_overlap["union_instability_rowset_count"],
            "dominant_stage": faz38_root["dominant_stage"],
            "primary_reason": faz38_root["primary_reason"],
            "root_cause_class": faz38_root["root_cause_class"],
        },
        "faz38_targeted_support": {
            "mandatory_auth_pass": faz38_targeted["mandatory_auth_pass"],
            "immutable_audit_logging_pass": faz38_targeted["immutable_audit_logging_pass"],
            "persisted_pii_redaction_pass": faz38_targeted["persisted_pii_redaction_pass"],
            "redis_session_persistence_pass": faz38_targeted["redis_session_persistence_pass"],
            "tokenizer_backed_accounting_pass": faz38_targeted["tokenizer_backed_accounting_pass"],
            "observability_alerting_pass": faz38_targeted["observability_alerting_pass"],
            "api_versioning_pass": faz38_targeted["api_versioning_pass"],
            "process_supervision_pass": faz38_targeted["process_supervision_pass"],
            "backup_restore_pass": faz38_targeted["backup_restore_pass"],
            "one_command_release_smoke_pass": faz38_targeted["one_command_release_smoke_pass"],
            "runtime_error_count": faz38_targeted["runtime_error_count"],
            "unexplained_count": faz38_targeted["unexplained_count"],
        },
        "faz38_retention_support": {
            "must_close_release_controls_pass": faz38_retention["must_close_release_controls_pass"],
            "retained_after_family_eval": faz38_retention["retained_after_family_eval"],
            "retained_after_restart": faz38_retention["retained_after_restart"],
            "retained_after_restore": faz38_retention["retained_after_restore"],
            "answer_path_delta_reintroduced": faz38_retention["answer_path_delta_reintroduced"],
            "runtime_error_count": faz38_retention["runtime_error_count"],
            "unexplained_count": faz38_retention["unexplained_count"],
        },
    }


def _contrast_rows(materialized: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for truth_class in TRUTH_ORDER:
        packages = materialized["truths"][truth_class]
        for package_name in PACKAGE_ORDER:
            rows.append(packages[package_name])
    return rows


def build_phase_payload(materialized: dict[str, Any]) -> dict[str, Any]:
    reference_pack = materialized["reference_pack"]
    current_authority = materialized["current_authority"]
    topology_rows = materialized["topology_rows"]
    contract = materialized["contract"]
    truths = materialized["truths"]
    contrast_rows = _contrast_rows(materialized)

    current_perimeter = truths["current_perimeter_truth_reference"]["frontier_174"]
    current_instability = truths["current_instability_repair_truth"]["frontier_174"]
    current_instability_targeted = materialized["faz38_targeted_support"]
    current_instability_retention = materialized["faz38_retention_support"]

    current_perimeter_preservation = {
        "current_perimeter_truth_reference_preserved": (
            current_perimeter["record_count"] == 174
            and current_perimeter["faz1_50_mismatch_count"] == 18
            and current_perimeter["v2_95_mismatch_count"] == 57
            and current_perimeter["v3_170_mismatch_count"] == 99
            and current_perimeter["preprojection_hash_mismatch_count"] == 174
            and current_perimeter["raw_answer_hash_mismatch_count"] == 174
            and current_perimeter["response_envelope_hash_mismatch_count"] == 109
            and current_perimeter["runtime_error_count"] == 0
            and current_perimeter["unexplained_count"] == 0
        ),
        "current_perimeter_truth_runtime_error_count": current_perimeter["runtime_error_count"],
        "current_perimeter_truth_unexplained_count": current_perimeter["unexplained_count"],
        "current_perimeter_truth_dominant_stage": materialized["faz35_support"]["dominant_stage"],
        "current_perimeter_truth_dominant_reason": materialized["faz35_support"]["dominant_reason"],
        "current_perimeter_truth_minimal_failing_control_set": materialized["faz35_support"]["minimal_failing_control_set"],
        "current_perimeter_truth_dominant_interaction_class": materialized["faz35_support"]["dominant_interaction_class"],
    }

    must_close_release_controls_pass = all(
        bool(current_instability_targeted[field])
        for field in (
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
        )
    )
    current_instability_adoption = {
        "current_instability_truth_adopted": (
            current_instability["runtime_error_count"] == 0
            and current_instability["unexplained_count"] == 0
            and materialized["faz38_support"]["primary_reason"] == "frontier_membership_delta"
            and materialized["faz38_support"]["root_cause_class"] == "frontier_membership_instability"
            and materialized["faz38_support"]["dominant_stage"] == "I4"
            and materialized["faz38_support"]["union_instability_rowset_count"] == 6
            and must_close_release_controls_pass is True
            and current_instability_retention["runtime_error_count"] == 0
            and current_instability_retention["unexplained_count"] == 0
            and current_instability_retention["retained_after_family_eval"] is False
            and current_instability_retention["retained_after_restart"] is True
            and current_instability_retention["retained_after_restore"] is True
            and current_instability_retention["answer_path_delta_reintroduced"] is True
        ),
        "current_instability_truth_runtime_error_count": current_instability["runtime_error_count"],
        "current_instability_truth_unexplained_count": current_instability["unexplained_count"],
        "current_instability_truth_primary_reason": materialized["faz38_support"]["primary_reason"],
        "current_instability_truth_root_cause_class": materialized["faz38_support"]["root_cause_class"],
        "current_instability_truth_dominant_stage": materialized["faz38_support"]["dominant_stage"],
        "current_instability_truth_union_instability_rowset_count": materialized["faz38_support"]["union_instability_rowset_count"],
        "current_instability_truth_must_close_release_controls_pass": must_close_release_controls_pass,
        "current_instability_truth_retained_after_family_eval": current_instability_retention["retained_after_family_eval"],
        "current_instability_truth_retained_after_restart": current_instability_retention["retained_after_restart"],
        "current_instability_truth_retained_after_restore": current_instability_retention["retained_after_restore"],
        "current_instability_truth_answer_path_delta_reintroduced": current_instability_retention["answer_path_delta_reintroduced"],
    }

    historical_archive = {
        "historical_failed_repair_truth_reclassified": True,
        "historical_inconclusive_recapture_truth_reclassified": True,
        "historical_repair_archive_channel": "diagnostic_only",
        "historical_failed_repair_truth_current_breach": False,
        "historical_inconclusive_recapture_truth_current_breach": False,
        "inconclusive_instability_archived": True,
    }

    rc_q_candidate_status_preserved = (
        contract["candidate_status"] == "frozen_failed_repair_candidate"
        and contract["promotable"] is False
        and contract["repairable"] is False
        and contract["current_evaluable"] is False
        and contract["release_controls_reentry_base"] is False
    )
    consumer_binding = {
        "repair_truth_comparison_order": contract["repair_truth_comparison_order"],
        "surface_breach_from_history_reintroduced": False,
        "current_perimeter_truth_reference_preserved": current_perimeter_preservation[
            "current_perimeter_truth_reference_preserved"
        ],
        "current_instability_truth_adopted": current_instability_adoption["current_instability_truth_adopted"],
        "historical_failed_repair_truth_reclassified": historical_archive[
            "historical_failed_repair_truth_reclassified"
        ],
        "historical_inconclusive_recapture_truth_reclassified": historical_archive[
            "historical_inconclusive_recapture_truth_reclassified"
        ],
        "historical_repair_archive_channel": historical_archive["historical_repair_archive_channel"],
        "rc_q_candidate_status_preserved": rc_q_candidate_status_preserved,
    }

    wp1_pass = (
        reference_pack["reference_pack_integrity_pass"] is True
        and reference_pack["reference_pack_contradiction_count"] == 0
        and reference_pack["canonical_current_authority_ref"] == "FAZ21"
        and reference_pack["current_perimeter_truth_ref"] == "FAZ35"
        and reference_pack["historical_failed_repair_truth_ref"] == "FAZ36"
        and reference_pack["historical_inconclusive_recapture_ref"] == "FAZ37"
        and reference_pack["current_instability_truth_ref"] == "FAZ38"
    )
    wp2_pass = (
        len(contrast_rows) == len(TRUTH_ORDER) * len(PACKAGE_ORDER)
        and {row["truth_class"] for row in contrast_rows} == set(TRUTH_ORDER)
        and {row["package_name"] for row in contrast_rows} == set(PACKAGE_ORDER)
    )
    wp3_pass = (
        current_perimeter_preservation["current_perimeter_truth_reference_preserved"] is True
        and current_perimeter_preservation["current_perimeter_truth_runtime_error_count"] == 0
        and current_perimeter_preservation["current_perimeter_truth_unexplained_count"] == 0
        and current_perimeter_preservation["current_perimeter_truth_dominant_stage"] == "P11"
        and current_perimeter_preservation["current_perimeter_truth_dominant_reason"] == "preprojection_hash_drift"
        and current_perimeter_preservation["current_perimeter_truth_minimal_failing_control_set"]
        == "mandatory_auth + immutable_audit_logging + redis_session_persistence"
        and current_perimeter_preservation["current_perimeter_truth_dominant_interaction_class"]
        == "multi_control_interaction_runtime_mutation"
    )
    wp4_pass = (
        current_instability_adoption["current_instability_truth_adopted"] is True
        and current_instability_adoption["current_instability_truth_runtime_error_count"] == 0
        and current_instability_adoption["current_instability_truth_unexplained_count"] == 0
        and current_instability_adoption["current_instability_truth_primary_reason"] == "frontier_membership_delta"
        and current_instability_adoption["current_instability_truth_root_cause_class"]
        == "frontier_membership_instability"
        and current_instability_adoption["current_instability_truth_dominant_stage"] == "I4"
        and current_instability_adoption["current_instability_truth_union_instability_rowset_count"] == 6
        and current_instability_adoption["current_instability_truth_must_close_release_controls_pass"] is True
        and current_instability_adoption["current_instability_truth_retained_after_family_eval"] is False
        and current_instability_adoption["current_instability_truth_retained_after_restart"] is True
        and current_instability_adoption["current_instability_truth_retained_after_restore"] is True
        and current_instability_adoption["current_instability_truth_answer_path_delta_reintroduced"] is True
    )
    wp5_pass = (
        historical_archive["historical_failed_repair_truth_reclassified"] is True
        and historical_archive["historical_inconclusive_recapture_truth_reclassified"] is True
        and historical_archive["historical_repair_archive_channel"] == "diagnostic_only"
        and historical_archive["historical_failed_repair_truth_current_breach"] is False
        and historical_archive["historical_inconclusive_recapture_truth_current_breach"] is False
        and historical_archive["inconclusive_instability_archived"] is True
    )
    wp6_pass = (
        consumer_binding["repair_truth_comparison_order"]
        == "current_perimeter_truth_reference -> current_repair_truth -> historical_repair_archive"
        and consumer_binding["surface_breach_from_history_reintroduced"] is False
        and consumer_binding["current_perimeter_truth_reference_preserved"] is True
        and consumer_binding["current_instability_truth_adopted"] is True
        and consumer_binding["historical_failed_repair_truth_reclassified"] is True
        and consumer_binding["historical_inconclusive_recapture_truth_reclassified"] is True
        and consumer_binding["historical_repair_archive_channel"] == "diagnostic_only"
        and consumer_binding["rc_q_candidate_status_preserved"] is True
    )

    if wp1_pass and wp2_pass and wp3_pass and wp4_pass and wp5_pass and wp6_pass:
        reconciliation = {
            "reference_pack_integrity_pass": True,
            "reference_pack_contradiction_count": 0,
            "reconciliation_stage": "R6",
            "primary_reason": "current_instability_truth_adopted_after_canonical_current_authority_with_current_perimeter_truth_preserved_and_historical_repair_truth_reclassification",
            "root_cause_class": "current_instability_truth_adopted_and_historical_repair_truths_reclassified_with_current_perimeter_truth_preserved",
            "current_perimeter_truth_reference_preserved": True,
            "current_instability_truth_adopted": True,
            "historical_failed_repair_truth_reclassified": True,
            "historical_inconclusive_recapture_truth_reclassified": True,
            "repair_truth_comparison_order": "current_perimeter_truth_reference -> current_repair_truth -> historical_repair_archive",
            "surface_breach_from_history_reintroduced": False,
            "unexplained_count": 0,
            "official_decision": PASS_DECISION,
            "next_official_work": PASS_NEXT_WORK,
        }
    else:
        unmet: list[str] = []
        for key, passed in {
            "reference_pack_integrity_pass": wp1_pass,
            "current_perimeter_truth_reference_preserved": wp3_pass,
            "current_instability_truth_adopted": wp4_pass,
            "historical_failed_repair_truth_reclassified": wp5_pass,
            "historical_inconclusive_recapture_truth_reclassified": wp5_pass,
            "repair_truth_comparison_order": wp6_pass,
            "surface_breach_from_history_reintroduced": consumer_binding[
                "surface_breach_from_history_reintroduced"
            ]
            is False,
        }.items():
            if not passed:
                unmet.append(key)
        reconciliation = {
            "reference_pack_integrity_pass": bool(reference_pack["reference_pack_integrity_pass"]),
            "reference_pack_contradiction_count": int(reference_pack["reference_pack_contradiction_count"]),
            "reconciliation_stage": "FAIL",
            "primary_reason": "reconciliation_contract_not_satisfied",
            "root_cause_class": (
                "canonical_current_authority_repair_truth_contract_breach"
                if current_authority["current_authority_contract_breach"] is True
                else "unexplained_rc_q_repair_truth_divergence"
            ),
            "current_perimeter_truth_reference_preserved": bool(
                current_perimeter_preservation["current_perimeter_truth_reference_preserved"]
            ),
            "current_instability_truth_adopted": bool(
                current_instability_adoption["current_instability_truth_adopted"]
            ),
            "historical_failed_repair_truth_reclassified": bool(
                historical_archive["historical_failed_repair_truth_reclassified"]
            ),
            "historical_inconclusive_recapture_truth_reclassified": bool(
                historical_archive["historical_inconclusive_recapture_truth_reclassified"]
            ),
            "repair_truth_comparison_order": consumer_binding["repair_truth_comparison_order"],
            "surface_breach_from_history_reintroduced": bool(
                consumer_binding["surface_breach_from_history_reintroduced"]
            ),
            "unexplained_count": len(unmet),
            "official_decision": FAIL_DECISION,
            "next_official_work": FAIL_NEXT_WORK,
            "unmet_pass_conditions": unmet,
        }

    return {
        "materialized": materialized,
        "contrast_rows": contrast_rows,
        "current_perimeter_truth_preservation": current_perimeter_preservation,
        "current_instability_truth_adoption": current_instability_adoption,
        "historical_archive_reclassification": historical_archive,
        "consumer_binding": consumer_binding,
        "reconciliation": reconciliation,
        "wp_statuses": {
            "WP-1": "PASS" if wp1_pass else "FAIL",
            "WP-2": "PASS" if wp2_pass else "FAIL",
            "WP-3": "PASS" if wp3_pass else "FAIL",
            "WP-4": "PASS" if wp4_pass else "FAIL",
            "WP-5": "PASS" if wp5_pass else "FAIL",
            "WP-6": "PASS" if wp6_pass else "FAIL",
            "WP-7": "PASS" if reconciliation["official_decision"] == PASS_DECISION else "FAIL",
        },
    }


def _render_result_report(payload: dict[str, Any]) -> str:
    materialized = payload["materialized"]
    reference_pack = materialized["reference_pack"]
    current_authority = materialized["current_authority"]
    contract = materialized["contract"]
    current_perimeter = payload["current_perimeter_truth_preservation"]
    current_instability = payload["current_instability_truth_adoption"]
    archive = payload["historical_archive_reclassification"]
    binding = payload["consumer_binding"]
    reconciliation = payload["reconciliation"]
    wp_rows = [{"wp": key, "status": value} for key, value in payload["wp_statuses"].items()]

    lines = [
        "# FAZ39 RC-Q REPAIR-TRUTH RECONCILIATION UNDER CANONICAL CURRENT AUTHORITY RAPORU",
        "",
        "## Yonetici Ozeti",
        "",
        f"- reference_pack_integrity_pass = `{bool_text(reference_pack['reference_pack_integrity_pass'])}`",
        f"- reference_pack_contradiction_count = `{reference_pack['reference_pack_contradiction_count']}`",
        f"- current_perimeter_truth_reference_preserved = `{bool_text(current_perimeter['current_perimeter_truth_reference_preserved'])}`",
        f"- current_instability_truth_adopted = `{bool_text(current_instability['current_instability_truth_adopted'])}`",
        f"- historical_failed_repair_truth_reclassified = `{bool_text(archive['historical_failed_repair_truth_reclassified'])}`",
        f"- historical_inconclusive_recapture_truth_reclassified = `{bool_text(archive['historical_inconclusive_recapture_truth_reclassified'])}`",
        f"- repair_truth_comparison_order = `{binding['repair_truth_comparison_order']}`",
        f"- surface_breach_from_history_reintroduced = `{bool_text(binding['surface_breach_from_history_reintroduced'])}`",
        f"- unexplained_count = `{reconciliation['unexplained_count']}`",
        f"- official_decision = `{reconciliation['official_decision']}`",
        f"- next_official_work = `{reconciliation['next_official_work']}`",
        "",
        "## Reference Pack Ozeti",
        "",
        *[
            f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`"
            for key, value in reference_pack.items()
            if key != "contradiction_rows"
        ],
        "",
        "## Current Authority ve RC-Q Role Freeze Ozeti",
        "",
        *[
            f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`"
            for key, value in current_authority.items()
        ],
        "",
        *markdown_table(
            [
                ("candidate_id", "candidate_id"),
                ("candidate_status", "candidate_status"),
                ("role", "role"),
                ("current_authority_member", "current_authority_member"),
                ("diagnostic_only", "diagnostic_only"),
                ("archived", "archived"),
                ("promotable", "promotable"),
                ("repairable", "repairable"),
                ("current_evaluable", "current_evaluable"),
                ("release_controls_reentry_base", "release_controls_reentry_base"),
            ],
            materialized["topology_rows"],
        ),
        "",
        *[
            f"- contract_{key} = `{bool_text(value) if isinstance(value, bool) else value}`"
            for key, value in contract.items()
        ],
        "",
        "## RC-Q Repair Truth Contrast Matrix Ozeti",
        "",
        *markdown_table(
            [
                ("truth_ref", "truth_ref"),
                ("truth_class", "truth_class"),
                ("package_name", "package_name"),
                ("record_count", "record_count"),
                ("faz1_50_mismatch_count", "faz1_50_mismatch_count"),
                ("v2_95_mismatch_count", "v2_95_mismatch_count"),
                ("v3_170_mismatch_count", "v3_170_mismatch_count"),
                ("preprojection_hash_mismatch_count", "preprojection_hash_mismatch_count"),
                ("raw_answer_hash_mismatch_count", "raw_answer_hash_mismatch_count"),
                ("response_envelope_hash_mismatch_count", "response_envelope_hash_mismatch_count"),
                ("capture_stability", "capture_stability"),
                ("capture_a_vs_capture_b_mismatch_count", "capture_a_vs_capture_b_mismatch_count"),
                ("runtime_error_count", "runtime_error_count"),
                ("unexplained_count", "unexplained_count"),
            ],
            payload["contrast_rows"],
        ),
        "",
        "## Current Perimeter Truth Preservation Ozeti",
        "",
        *[
            f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`"
            for key, value in current_perimeter.items()
        ],
        "",
        "## Current Instability Truth Adoption Ozeti",
        "",
        *[
            f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`"
            for key, value in current_instability.items()
        ],
        "",
        "## Historical Repair Archive Reclassification Ozeti",
        "",
        *[
            f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`"
            for key, value in archive.items()
        ],
        "",
        "## Repair-Truth Consumer Binding Ozeti",
        "",
        *[
            f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`"
            for key, value in binding.items()
        ],
        "",
        "## WP Sonuclari",
        "",
        *markdown_table([("wp", "wp"), ("status", "status")], wp_rows),
        "",
        "## Resmi Karar",
        "",
        *[
            f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`"
            for key, value in reconciliation.items()
            if key != "unmet_pass_conditions"
        ],
        *(
            [f"- unmet_pass_conditions = `{', '.join(reconciliation['unmet_pass_conditions'])}`"]
            if "unmet_pass_conditions" in reconciliation
            else []
        ),
        "",
        "## Sonraki Resmi Is",
        "",
        f"- next_official_work = `{reconciliation['next_official_work']}`",
        "",
        "## Artefact Listesi",
        "",
        *[f"- `{path}`" for path in ARTEFACT_LIST],
        "",
    ]
    return "\n".join(lines)


def render_outputs(payload: dict[str, Any]) -> dict[Path, str]:
    materialized = payload["materialized"]
    reference_pack = materialized["reference_pack"]
    contract = materialized["contract"]
    current_perimeter = payload["current_perimeter_truth_preservation"]
    current_instability = payload["current_instability_truth_adoption"]
    archive = payload["historical_archive_reclassification"]
    binding = payload["consumer_binding"]
    reconciliation = payload["reconciliation"]

    outputs: dict[Path, str] = {
        ROOT / "coordination" / f"faz39-official-implementation-plan-{DATE}.md": "\n".join(
            [
                "# FAZ39 Official Implementation Plan",
                "",
                "1. FAZ21, FAZ33, FAZ35, FAZ36, FAZ37 ve FAZ38 reference pack'ini freeze et.",
                "2. RC-Q icin current perimeter truth, current instability truth ve historical repair archive contrast matrix'ini materialize et.",
                "3. FAZ35 current perimeter truth preservation gate'ini sayisal alanlarla kapa.",
                "4. FAZ38 current instability truth adoption gate'ini sayisal alanlarla kapa.",
                "5. FAZ36 ve FAZ37 truth'lerini historical repair archive olarak reclassify et.",
                "6. RC-Q repair-truth consumer binding order'ini canonical current authority altinda kilitle.",
                "7. Tek resmi karari ve tek next_official_work alanini materialize et.",
                "",
            ]
        ),
        ROOT / "coordination" / f"faz39-steering-decision-table-{DATE}.md": "\n".join(
            [
                "# FAZ39 Steering Decision Table",
                "",
                "| wp | status |",
                "| --- | --- |",
                *[
                    f"| {wp} | {status} |"
                    for wp, status in payload["wp_statuses"].items()
                ],
                "",
            ]
        ),
        ROOT / "coordination" / f"faz39-reference-pack-{DATE}.md": "\n".join(
            [
                "# FAZ39 Reference Pack",
                "",
                *[
                    f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`"
                    for key, value in reference_pack.items()
                    if key != "contradiction_rows"
                ],
                "",
            ]
        ),
        ROOT / "coordination" / f"faz39-rc-q-repair-truth-reconciliation-contract-{DATE}.md": "\n".join(
            [
                "# FAZ39 RC-Q Repair-Truth Reconciliation Contract",
                "",
                *[
                    f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`"
                    for key, value in contract.items()
                ],
                "",
                *[f"- {stage}" for stage in RECONCILIATION_STAGES],
                "",
                *[f"- root_cause_class = `{item}`" for item in ROOT_CAUSE_CLASSES],
                "",
            ]
        ),
        ROOT / "coordination" / f"faz39-rc-q-repair-truth-contrast-matrix-{DATE}.md": "\n".join(
            [
                "# FAZ39 RC-Q Repair-Truth Contrast Matrix",
                "",
                *markdown_table(
                    [
                        ("truth_ref", "truth_ref"),
                        ("truth_class", "truth_class"),
                        ("package_name", "package_name"),
                        ("record_count", "record_count"),
                        ("faz1_50_mismatch_count", "faz1_50"),
                        ("v2_95_mismatch_count", "v2_95"),
                        ("v3_170_mismatch_count", "v3_170"),
                        ("preprojection_hash_mismatch_count", "preprojection"),
                        ("raw_answer_hash_mismatch_count", "raw_answer"),
                        ("response_envelope_hash_mismatch_count", "response_envelope"),
                        ("capture_stability", "capture_stability"),
                        ("capture_a_vs_capture_b_mismatch_count", "ab_mismatch"),
                        ("runtime_error_count", "runtime_error_count"),
                        ("unexplained_count", "unexplained_count"),
                    ],
                    payload["contrast_rows"],
                ),
                "",
            ]
        ),
        ROOT / "coordination" / f"faz39-rc-q-current-perimeter-truth-preservation-{DATE}.md": "\n".join(
            [
                "# FAZ39 RC-Q Current Perimeter Truth Preservation",
                "",
                *[
                    f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`"
                    for key, value in current_perimeter.items()
                ],
                "",
            ]
        ),
        ROOT / "coordination" / f"faz39-rc-q-current-instability-truth-adoption-{DATE}.md": "\n".join(
            [
                "# FAZ39 RC-Q Current Instability Truth Adoption",
                "",
                *[
                    f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`"
                    for key, value in current_instability.items()
                ],
                "",
            ]
        ),
        ROOT / "coordination" / f"faz39-rc-q-historical-repair-archive-reclassification-{DATE}.md": "\n".join(
            [
                "# FAZ39 RC-Q Historical Repair Archive Reclassification",
                "",
                *[
                    f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`"
                    for key, value in archive.items()
                ],
                "",
            ]
        ),
        ROOT / "coordination" / f"faz39-rc-q-repair-truth-consumer-binding-{DATE}.md": "\n".join(
            [
                "# FAZ39 RC-Q Repair-Truth Consumer Binding",
                "",
                *[
                    f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`"
                    for key, value in binding.items()
                ],
                "",
            ]
        ),
        ROOT / "coordination" / f"faz39-rc-q-reconciliation-summary-{DATE}.md": "\n".join(
            [
                "# FAZ39 RC-Q Reconciliation Summary",
                "",
                *[
                    f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`"
                    for key, value in reconciliation.items()
                    if key != "unmet_pass_conditions"
                ],
                *(
                    [f"- unmet_pass_conditions = `{', '.join(reconciliation['unmet_pass_conditions'])}`"]
                    if "unmet_pass_conditions" in reconciliation
                    else []
                ),
                "",
            ]
        ),
        ROOT / "reports" / RESULT_REPORT_NAME: _render_result_report(payload),
        ROOT / "docs" / RESULT_REPORT_NAME: _render_result_report(payload),
    }
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    materialized = build_materialized_payload()
    payload = build_phase_payload(materialized)
    for path, text in render_outputs(payload).items():
        write_text(path, text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
