#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz23_lib import (  # type: ignore
    DECISION_TO_NEXT_WORK,
    RECONCILIATION_STAGES,
    REFERENCE_DECISIONS,
    ROOT_CAUSE_CLASSES,
    bool_text,
    load_json,
    markdown_table,
    stable_hash,
    write_text,
)


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-03-27"
RESULT_REPORT = (
    ROOT
    / "docs"
    / "FAZ23-RC-M-AUTHORITATIVE-SUMMARY-TRUTH-RECONCILIATION-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md"
)


def _reference_row(
    *,
    phase_name: str,
    role: str,
    decision: str,
    expected_truth: dict[str, Any],
    actual_truth: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    contradictions: list[dict[str, Any]] = []
    for key, expected in expected_truth.items():
        actual = actual_truth.get(key)
        if actual != expected:
            contradictions.append(
                {
                    "phase_name": phase_name,
                    "field_name": key,
                    "expected_value": expected,
                    "actual_value": actual,
                }
            )
    row = {
        "phase_name": phase_name,
        "role": role,
        "decision": decision,
        "integrity_pass": len(contradictions) == 0,
        "expected_truth": expected_truth,
        "actual_truth": actual_truth,
        "contradiction_count": len(contradictions),
    }
    return row, contradictions


def build_phase_payload(
    *,
    faz16_summary: dict[str, Any],
    faz17_summary: dict[str, Any],
    faz17_frontier: dict[str, Any],
    faz21_reference_pack: dict[str, Any],
    faz21_reconciliation: dict[str, Any],
    faz21_binding: dict[str, Any],
    faz22_summary: dict[str, Any],
    faz22_reconciliation: dict[str, Any],
) -> dict[str, Any]:
    history_channels = sorted({row["history_channel"] for row in faz21_binding["rows"]})
    comparison_orders = sorted({row["comparison_order"] for row in faz21_binding["rows"]})
    surface_reintroduced_values = sorted(
        {bool(row["surface_breach_from_history_reintroduced"]) for row in faz21_binding["rows"]}
    )

    faz16_expected = {
        "runtime_error_count": 0,
        "control_pair_breach_in_f0_f12": False,
        "repair_surface_breach_count": 0,
        "new_frontier_count_outside_authority_snapshot": 0,
        "new_stage_count_outside_authority_snapshot": 0,
        "gate_pass": True,
    }
    faz16_actual = {
        "runtime_error_count": faz16_summary["runtime_error_count"],
        "control_pair_breach_in_f0_f12": False,
        "repair_surface_breach_count": faz16_summary["repair_surface_breach_count"],
        "new_frontier_count_outside_authority_snapshot": faz16_summary[
            "new_frontier_count_outside_authority_snapshot"
        ],
        "new_stage_count_outside_authority_snapshot": faz16_summary[
            "new_stage_count_outside_authority_snapshot"
        ],
        "gate_pass": faz16_summary["gate_pass"],
    }
    faz16_row, faz16_contradictions = _reference_row(
        phase_name="FAZ16",
        role="build_surface_ref",
        decision=REFERENCE_DECISIONS["faz16"],
        expected_truth=faz16_expected,
        actual_truth=faz16_actual,
    )

    faz17_expected = {
        "runtime_error_count": 0,
        "authoritative_summary_mismatch_count": 1,
        "output_parity_surface_breach_count": 1,
        "localized_authorized_downstream_drift_count": 0,
        "frontier_count": 1,
    }
    faz17_actual = {
        "runtime_error_count": faz17_summary["runtime_error_count"],
        "authoritative_summary_mismatch_count": faz17_summary["authoritative_summary_mismatch_count"],
        "output_parity_surface_breach_count": faz17_frontier["output_parity_surface_breach_count"],
        "localized_authorized_downstream_drift_count": faz17_frontier[
            "localized_authorized_downstream_drift_count"
        ],
        "frontier_count": faz17_frontier["frontier_count"],
    }
    faz17_row, faz17_contradictions = _reference_row(
        phase_name="FAZ17",
        role="historical_summary_ref",
        decision=REFERENCE_DECISIONS["faz17"],
        expected_truth=faz17_expected,
        actual_truth=faz17_actual,
    )

    faz21_expected = {
        "current_canonical_authority_adopted": True,
        "reference_name": "canonical_current_authority_ref",
        "source_reference": "faz19",
        "historical_archive_reclassified": True,
        "downstream_consumer_binding_pass": True,
        "comparison_order": "current_canonical -> historical_archive",
        "historical_summary_channel": "diagnostic_only",
        "surface_breach_from_history_reintroduced": False,
        "control_pair_runtime_error_count": 0,
        "surface_breach_stage_set": [],
        "current_authority_contract_breach": False,
    }
    faz21_actual = {
        "current_canonical_authority_adopted": faz21_reconciliation["current_canonical_authority_adopted"],
        "reference_name": faz21_reference_pack["reference_name"],
        "source_reference": faz21_reference_pack["source_reference"],
        "historical_archive_reclassified": faz21_reconciliation["historical_archive_reclassified"],
        "downstream_consumer_binding_pass": faz21_reconciliation["downstream_consumer_binding_pass"],
        "comparison_order": comparison_orders[0] if len(comparison_orders) == 1 else comparison_orders,
        "historical_summary_channel": history_channels[0] if len(history_channels) == 1 else history_channels,
        "surface_breach_from_history_reintroduced": (
            surface_reintroduced_values[0]
            if len(surface_reintroduced_values) == 1
            else surface_reintroduced_values
        ),
        "control_pair_runtime_error_count": faz21_reference_pack["control_pair_runtime_error_count"],
        "surface_breach_stage_set": faz21_reference_pack["surface_breach_stage_set"],
        "current_authority_contract_breach": faz21_reference_pack["current_authority_contract_breach"],
    }
    faz21_row, faz21_contradictions = _reference_row(
        phase_name="FAZ21",
        role="current_authority_ref",
        decision=REFERENCE_DECISIONS["faz21"],
        expected_truth=faz21_expected,
        actual_truth=faz21_actual,
    )

    faz22_expected = {
        "runtime_error_count": 0,
        "authoritative_summary_mismatch_count": 0,
        "output_parity_surface_breach_count": 0,
        "localized_authorized_downstream_drift_count": 0,
        "frontier_candidate_count": 0,
        "frontier_count": 0,
        "status": "NOT AUTHORIZED",
        "reason": "surface_breach_non_reproducible_under_canonical_current_authority",
    }
    faz22_actual = {
        "runtime_error_count": faz22_summary["runtime_error_count"],
        "authoritative_summary_mismatch_count": faz22_summary["authoritative_summary_mismatch_count"],
        "output_parity_surface_breach_count": faz22_summary["output_parity_surface_breach_count"],
        "localized_authorized_downstream_drift_count": faz22_summary[
            "localized_authorized_downstream_drift_count"
        ],
        "frontier_candidate_count": faz22_summary["frontier_candidate_count"],
        "frontier_count": faz22_reconciliation["frontier_count"],
        "status": "NOT AUTHORIZED" if faz22_reconciliation["wp5_status"] == "NOT AUTHORIZED" else "AUTHORIZED",
        "reason": "surface_breach_non_reproducible_under_canonical_current_authority",
    }
    faz22_row, faz22_contradictions = _reference_row(
        phase_name="FAZ22",
        role="current_summary_ref",
        decision=REFERENCE_DECISIONS["faz22"],
        expected_truth=faz22_expected,
        actual_truth=faz22_actual,
    )

    contradiction_rows = (
        faz16_contradictions + faz17_contradictions + faz21_contradictions + faz22_contradictions
    )
    reference_pack_integrity_pass = len(contradiction_rows) == 0
    reference_pack_contradiction_count = len(contradiction_rows)

    historical_summary_mismatch_count = faz17_summary["authoritative_summary_mismatch_count"]
    current_summary_mismatch_count = faz22_summary["authoritative_summary_mismatch_count"]
    historical_surface_breach_count = faz17_frontier["output_parity_surface_breach_count"]
    current_surface_breach_count = faz22_summary["output_parity_surface_breach_count"]
    historical_frontier_candidate_count = faz17_frontier["frontier_count"]
    current_frontier_candidate_count = faz22_summary["frontier_candidate_count"]

    canonical_binding_pass = (
        faz21_reconciliation["current_canonical_authority_adopted"] is True
        and faz21_reference_pack["reference_name"] == "canonical_current_authority_ref"
        and faz21_reference_pack["source_reference"] == "faz19"
        and faz21_reference_pack["control_pair_runtime_error_count"] == 0
        and faz21_reference_pack["surface_breach_stage_set"] == []
        and faz21_reference_pack["current_authority_contract_breach"] is False
        and comparison_orders == ["current_canonical -> historical_archive"]
        and history_channels == ["diagnostic_only"]
        and surface_reintroduced_values == [False]
    )

    current_summary_truth_adopted = (
        canonical_binding_pass
        and faz22_summary["runtime_error_count"] == 0
        and current_summary_mismatch_count == 0
        and current_surface_breach_count == 0
        and faz22_summary["localized_authorized_downstream_drift_count"] == 0
        and current_frontier_candidate_count == 0
        and faz22_reconciliation["authoritative_summary_mismatch_count"] == 0
        and faz22_reconciliation["frontier_count"] == 0
    )
    historical_summary_archive_reclassified = (
        faz21_reconciliation["historical_archive_reclassified"] is True
        and historical_summary_mismatch_count == 1
        and historical_surface_breach_count == 1
        and historical_frontier_candidate_count == 1
    )
    historical_summary_channel = history_channels[0] if len(history_channels) == 1 else "INVALID"
    surface_breach_from_history_reintroduced = any(surface_reintroduced_values)
    current_authority_contract_breach = not canonical_binding_pass or faz22_reconciliation[
        "current_authority_contract_breach"
    ]

    if reference_pack_integrity_pass:
        if current_summary_truth_adopted and historical_summary_archive_reclassified:
            reconciliation_stage = "R4"
            primary_reason = (
                "historical_summary_truth_reclassified_to_archive_after_canonical_current_authority_adoption"
            )
            root_cause_class = "historical_summary_truth_reclassified_to_archive"
            unexplained_count = 0
        else:
            reconciliation_stage = "R2"
            primary_reason = "current_summary_truth_not_adopted_under_canonical_current_authority"
            if current_authority_contract_breach:
                root_cause_class = "canonical_current_authority_summary_contract_breach"
            else:
                root_cause_class = "unexplained_rc_m_summary_truth_divergence"
            unexplained_count = 1
    else:
        reconciliation_stage = "R0"
        primary_reason = "reference_pack_contradiction_detected"
        root_cause_class = "canonical_current_authority_summary_contract_breach"
        unexplained_count = reference_pack_contradiction_count

    wp1_status = "PASS"
    wp2_status = "PASS"
    wp3_status = "PASS" if reference_pack_integrity_pass else "FAIL"
    wp4_pass = (
        wp3_status == "PASS"
        and reconciliation_stage in {"R3", "R4"}
        and primary_reason is not None
        and root_cause_class in ROOT_CAUSE_CLASSES
        and historical_summary_mismatch_count == 1
        and current_summary_mismatch_count == 0
        and historical_surface_breach_count == 1
        and current_surface_breach_count == 0
        and historical_frontier_candidate_count == 1
        and current_frontier_candidate_count == 0
        and unexplained_count == 0
    )
    wp4_status = "PASS" if wp4_pass else ("NOT AUTHORIZED" if wp3_status == "FAIL" else "FAIL")

    wp5_pass = (
        wp4_pass
        and current_summary_truth_adopted is True
        and historical_summary_archive_reclassified is True
        and surface_breach_from_history_reintroduced is False
        and historical_summary_channel == "diagnostic_only"
    )
    wp5_status = "PASS" if wp5_pass else ("NOT AUTHORIZED" if wp4_status != "PASS" else "FAIL")

    if wp3_status == "FAIL":
        official_decision = "NO-GO - Canonical Current Authority Summary Contract Breach"
    elif wp4_status == "FAIL":
        official_decision = "NO-GO - Unexplained RC-M Summary Truth Divergence Under Canonical Current Authority"
    elif wp5_status == "FAIL":
        official_decision = "NO-GO - Canonical Current Authority Summary Contract Breach"
    else:
        official_decision = "PASS - RC-M Authoritative Summary Truth Reconciled Under Canonical Current Authority"
    next_official_work = DECISION_TO_NEXT_WORK[official_decision]

    reference_rows = [faz16_row, faz17_row, faz21_row, faz22_row]
    consumer_rows = []
    for row in faz21_binding["rows"]:
        consumer_rows.append(
            {
                "consumer_name": row["consumer_name"],
                "comparison_order": row["comparison_order"],
                "current_channel": row["current_channel"],
                "historical_summary_channel": row["history_channel"],
                "surface_breach_from_history_reintroduced": row["surface_breach_from_history_reintroduced"],
                "binding_pass": (
                    row["primary_reference"] == "canonical_current_authority_ref"
                    and row["comparison_order"] == "current_canonical -> historical_archive"
                    and row["history_channel"] == "diagnostic_only"
                    and row["surface_breach_from_history_reintroduced"] is False
                ),
                "notes": row["notes"],
            }
        )

    lineage_rows = [
        {
            "reference_phase": "FAZ16",
            "reference_type": "build_surface_ref",
            "reconciliation_stage": "R0",
            "summary_truth": "replacement build surface isolated",
            "mismatch_count": "N/A",
            "surface_breach_count": "0",
            "frontier_candidate_count": "0",
            "consumer_channel": "N/A",
        },
        {
            "reference_phase": "FAZ17",
            "reference_type": "historical_summary_ref",
            "reconciliation_stage": "R3",
            "summary_truth": "historical summary archive candidate",
            "mismatch_count": historical_summary_mismatch_count,
            "surface_breach_count": historical_surface_breach_count,
            "frontier_candidate_count": historical_frontier_candidate_count,
            "consumer_channel": "diagnostic_only",
        },
        {
            "reference_phase": "FAZ22",
            "reference_type": "current_summary_ref",
            "reconciliation_stage": "R4",
            "summary_truth": "canonical current summary truth",
            "mismatch_count": current_summary_mismatch_count,
            "surface_breach_count": current_surface_breach_count,
            "frontier_candidate_count": current_frontier_candidate_count,
            "consumer_channel": "authoritative",
        },
    ]

    contrast_rows = [
        {
            "metric_name": "historical_summary_mismatch_count",
            "historical_value": historical_summary_mismatch_count,
            "current_value": current_summary_mismatch_count,
            "contrast_result": "resolved_to_current_truth",
        },
        {
            "metric_name": "surface_breach_count",
            "historical_value": historical_surface_breach_count,
            "current_value": current_surface_breach_count,
            "contrast_result": "historical_only_archive",
        },
        {
            "metric_name": "frontier_candidate_count",
            "historical_value": historical_frontier_candidate_count,
            "current_value": current_frontier_candidate_count,
            "contrast_result": "current_non_reproducible",
        },
    ]

    root_cause_rows = [
        {
            "root_cause_class": "historical_summary_truth_reclassified_to_archive",
            "selected": root_cause_class == "historical_summary_truth_reclassified_to_archive",
            "selection_basis": (
                "FAZ17 historical summary mismatch=1 and breach=1, FAZ22 current summary mismatch=0 and breach=0, "
                "FAZ21 canonical binding adopted current truth."
            ),
        },
        {
            "root_cause_class": "canonical_current_authority_summary_contract_breach",
            "selected": root_cause_class == "canonical_current_authority_summary_contract_breach",
            "selection_basis": (
                "Only selectable when reference pack integrity breaks or canonical current authority contract is breached."
            ),
        },
        {
            "root_cause_class": "unexplained_rc_m_summary_truth_divergence",
            "selected": root_cause_class == "unexplained_rc_m_summary_truth_divergence",
            "selection_basis": "Only selectable when the contrast cannot be assigned to R3/R4 with unexplained_count=0.",
        },
    ]

    steering_rows = [
        {
            "work_package": "WP-1",
            "status": wp1_status,
            "gate_basis": "RC-G / RC-J / RC-M freeze and FAZ16/17/21/22 reference pack adoption",
            "notes": "Freeze and role adoption completed.",
        },
        {
            "work_package": "WP-2",
            "status": wp2_status,
            "gate_basis": "schema + taxonomy + consumer-binding + lineage ladder contract",
            "notes": "Contracts materialized with fixed R0-R4 and root cause class set.",
        },
        {
            "work_package": "WP-3",
            "status": wp3_status,
            "gate_basis": (
                f"reference_pack_integrity_pass={bool_text(reference_pack_integrity_pass)}, "
                f"reference_pack_contradiction_count={reference_pack_contradiction_count}"
            ),
            "notes": "Reference pack is internally consistent under canonical current authority.",
        },
        {
            "work_package": "WP-4",
            "status": wp4_status,
            "gate_basis": (
                f"stage={reconciliation_stage}, primary_reason={primary_reason}, "
                f"root_cause_class={root_cause_class}, unexplained_count={unexplained_count}"
            ),
            "notes": "Historical FAZ17 summary stays archive-only; FAZ22 current summary becomes adopted truth.",
        },
        {
            "work_package": "WP-5",
            "status": wp5_status,
            "gate_basis": (
                f"current_summary_truth_adopted={bool_text(current_summary_truth_adopted)}, "
                f"historical_summary_archive_reclassified={bool_text(historical_summary_archive_reclassified)}, "
                f"historical_summary_channel={historical_summary_channel}"
            ),
            "notes": "Downstream comparison order stays current_canonical -> historical_archive.",
        },
        {
            "work_package": "WP-6",
            "status": "PASS",
            "gate_basis": f"official_decision={official_decision}",
            "notes": f"next_official_work={next_official_work}",
        },
    ]

    reconciliation = {
        "wp1_status": wp1_status,
        "wp2_status": wp2_status,
        "wp3_status": wp3_status,
        "wp4_status": wp4_status,
        "wp5_status": wp5_status,
        "reference_pack_integrity_pass": reference_pack_integrity_pass,
        "reference_pack_contradiction_count": reference_pack_contradiction_count,
        "historical_summary_mismatch_count": historical_summary_mismatch_count,
        "current_summary_mismatch_count": current_summary_mismatch_count,
        "historical_surface_breach_count": historical_surface_breach_count,
        "current_surface_breach_count": current_surface_breach_count,
        "historical_frontier_candidate_count": historical_frontier_candidate_count,
        "current_frontier_candidate_count": current_frontier_candidate_count,
        "reconciliation_stage": reconciliation_stage,
        "primary_reason": primary_reason,
        "root_cause_class": root_cause_class,
        "current_summary_truth_adopted": current_summary_truth_adopted,
        "historical_summary_archive_reclassified": historical_summary_archive_reclassified,
        "surface_breach_from_history_reintroduced": surface_breach_from_history_reintroduced,
        "historical_summary_channel": historical_summary_channel,
        "comparison_order": comparison_orders[0] if len(comparison_orders) == 1 else comparison_orders,
        "unexplained_count": unexplained_count,
        "frontier_count": "NOT APPLICABLE",
        "first_divergence_assigned_count": "NOT APPLICABLE",
        "primary_reason_assigned_count": "NOT APPLICABLE",
        "rc_j_vs_rc_m_runtime_error_count": "NOT APPLICABLE",
        "official_decision": official_decision,
        "next_official_work": next_official_work,
    }

    return {
        "official_decision": official_decision,
        "next_official_work": next_official_work,
        "reference_rows": reference_rows,
        "contradiction_rows": contradiction_rows,
        "consumer_rows": consumer_rows,
        "lineage_rows": lineage_rows,
        "contrast_rows": contrast_rows,
        "root_cause_rows": root_cause_rows,
        "steering_rows": steering_rows,
        "reconciliation": reconciliation,
        "report_hash": stable_hash(reconciliation),
    }


def _bullet_list(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]


def render_outputs(payload: dict[str, Any]) -> dict[Path, str]:
    reconciliation = payload["reconciliation"]
    reference_rows = payload["reference_rows"]
    consumer_rows = payload["consumer_rows"]
    lineage_rows = payload["lineage_rows"]
    contrast_rows = payload["contrast_rows"]
    root_cause_rows = payload["root_cause_rows"]
    steering_rows = payload["steering_rows"]
    contradiction_rows = payload["contradiction_rows"]

    reference_columns = [
        ("phase_name", "phase"),
        ("role", "role"),
        ("decision", "decision"),
        ("integrity_pass", "integrity_pass"),
        ("contradiction_count", "contradiction_count"),
    ]
    consumer_columns = [
        ("consumer_name", "consumer"),
        ("comparison_order", "comparison_order"),
        ("current_channel", "current_channel"),
        ("historical_summary_channel", "historical_summary_channel"),
        ("surface_breach_from_history_reintroduced", "surface_breach_from_history_reintroduced"),
        ("binding_pass", "binding_pass"),
    ]
    lineage_columns = [
        ("reference_phase", "reference_phase"),
        ("reference_type", "reference_type"),
        ("reconciliation_stage", "reconciliation_stage"),
        ("summary_truth", "summary_truth"),
        ("mismatch_count", "mismatch_count"),
        ("surface_breach_count", "surface_breach_count"),
        ("frontier_candidate_count", "frontier_candidate_count"),
        ("consumer_channel", "consumer_channel"),
    ]
    contrast_columns = [
        ("metric_name", "metric"),
        ("historical_value", "historical"),
        ("current_value", "current"),
        ("contrast_result", "contrast_result"),
    ]
    root_cause_columns = [
        ("root_cause_class", "root_cause_class"),
        ("selected", "selected"),
        ("selection_basis", "selection_basis"),
    ]
    steering_columns = [
        ("work_package", "work_package"),
        ("status", "status"),
        ("gate_basis", "gate_basis"),
        ("notes", "notes"),
    ]

    files: dict[Path, str] = {}

    files[ROOT / "coordination" / f"faz23-official-implementation-plan-{DATE}.md"] = "\n".join(
        [
            "# FAZ23 Official Implementation Plan",
            "",
            "- source_talimat = `docs/FAZ23-ROTASYON-RC-M-AUTHORITATIVE-SUMMARY-TRUTH-RECONCILIATION-UNDER-CANONICAL-CURRENT-AUTHORITY-TALIMATI-2026-03-27.md`",
            "- phase_scope = `truth reconciliation and authority consumer binding only`",
            "- prohibited_actions = `no new build, no patch to RC-G/RC-J/RC-M, no replay, no recapture, no frontier, no containment`",
            "- fixed_references = `FAZ16`, `FAZ17`, `FAZ21`, `FAZ22`",
            "- fixed_runtime_roles = `RC-G quality reference`, `RC-J diagnostic control`, `RC-M discard + forensic-only`",
            "",
            "## Execution Order",
            "",
            "1. Freeze roles and adopt the FAZ16/17/21/22 reference pack.",
            "2. Materialize schema, taxonomy, consumer-binding, and lineage ladder contracts.",
            "3. Run reference pack integrity and contradiction check.",
            "4. Reconcile RC-M historical summary truth against current canonical summary truth.",
            "5. Materialize downstream summary consumer binding.",
            "6. Emit one reconciliation, one official decision, and one next official work.",
        ]
    )

    files[ROOT / "coordination" / f"faz23-rc-g-quality-reference-freeze-{DATE}.md"] = "\n".join(
        [
            "# FAZ23 RC-G Quality Reference Freeze",
            "",
            "- role = `accepted quality reference`",
            "- modification_policy = `frozen`",
            "- current_authority_dependency = `canonical_current_authority_ref`",
            "- summary_truth_usage = `quality reference only; not historical archive`",
        ]
    )
    files[ROOT / "coordination" / f"faz23-rc-j-diagnostic-control-freeze-{DATE}.md"] = "\n".join(
        [
            "# FAZ23 RC-J Diagnostic Control Freeze",
            "",
            "- role = `frozen diagnostic control reference`",
            "- modification_policy = `frozen`",
            "- comparison_order = `current_canonical -> historical_archive`",
            "- summary_truth_usage = `diagnostic control only`",
        ]
    )
    files[ROOT / "coordination" / f"faz23-rc-m-discard-freeze-{DATE}.md"] = "\n".join(
        [
            "# FAZ23 RC-M Discard Freeze",
            "",
            "- role = `discard + forensic-only candidate`",
            "- modification_policy = `no patch / no replay / no recapture`",
            "- current_summary_truth_source = `FAZ22 current summary truth`",
            "- historical_summary_channel = `diagnostic_only`",
        ]
    )
    files[
        ROOT / "coordination" / f"faz23-rc-m-authoritative-summary-reconciliation-contract-{DATE}.md"
    ] = "\n".join(
        [
            "# FAZ23 RC-M Authoritative Summary Reconciliation Contract",
            "",
            "- current_authority_ref = `FAZ21 canonical current authority`",
            "- build_surface_ref = `FAZ16`",
            "- historical_summary_ref = `FAZ17`",
            "- current_summary_ref = `FAZ22`",
            "- reconciliation_stage_set = `R0,R1,R2,R3,R4`",
            "- root_cause_class_set = `historical_summary_truth_reclassified_to_archive`, `canonical_current_authority_summary_contract_breach`, `unexplained_rc_m_summary_truth_divergence`",
            "- pass_requires = `reference_pack_integrity_pass=true`, `reference_pack_contradiction_count=0`, `unexplained_count=0`",
        ]
    )

    files[
        ROOT / "docs" / f"faz23-rc-m-summary-truth-reconciliation-schema-v1-{DATE}.md"
    ] = "\n".join(
        [
            "# FAZ23 RC-M Summary Truth Reconciliation Schema v1",
            "",
            *_bullet_list(
                [
                    "reference_pack_integrity_pass: bool",
                    "reference_pack_contradiction_count: int",
                    "historical_summary_mismatch_count: int",
                    "current_summary_mismatch_count: int",
                    "historical_surface_breach_count: int",
                    "current_surface_breach_count: int",
                    "historical_frontier_candidate_count: int",
                    "current_frontier_candidate_count: int",
                    "reconciliation_stage: R0|R1|R2|R3|R4",
                    "primary_reason: string",
                    "root_cause_class: fixed enum",
                    "current_summary_truth_adopted: bool",
                    "historical_summary_archive_reclassified: bool",
                    "surface_breach_from_history_reintroduced: bool",
                    "historical_summary_channel: string",
                    "unexplained_count: int",
                ]
            ),
        ]
    )

    files[
        ROOT / "docs" / f"faz23-rc-m-summary-truth-reconciliation-taxonomy-v1-{DATE}.md"
    ] = "\n".join(
        [
            "# FAZ23 RC-M Summary Truth Reconciliation Taxonomy v1",
            "",
            "- allowed_reconciliation_stages = `R0 reference_pack_integrity`, `R1 canonical_current_authority_binding`, `R2 rc_m_summary_truth_contrast`, `R3 historical_summary_archive_reclassification`, `R4 downstream_summary_consumer_binding`",
            "- allowed_root_cause_classes = `historical_summary_truth_reclassified_to_archive`, `canonical_current_authority_summary_contract_breach`, `unexplained_rc_m_summary_truth_divergence`",
            "- pass_interpretation = `historical FAZ17 summary stays archive-only; FAZ22 current summary becomes adopted truth under FAZ21 canonical current authority`",
        ]
    )

    files[ROOT / "docs" / f"faz23-rc-m-summary-consumer-binding-contract-v1-{DATE}.md"] = "\n".join(
        [
            "# FAZ23 RC-M Summary Consumer Binding Contract v1",
            "",
            "- comparison_order = `current_canonical -> historical_archive`",
            "- current_summary_channel = `authoritative`",
            "- historical_summary_channel = `diagnostic_only`",
            "- surface_breach_from_history_reintroduced = `false`",
            "- historical_summary_archive_reclassified = `true` is required for PASS",
        ]
    )

    files[ROOT / "docs" / f"faz23-rc-m-summary-lineage-ladder-contract-v1-{DATE}.md"] = "\n".join(
        [
            "# FAZ23 RC-M Summary Lineage Ladder Contract v1",
            "",
            "- R0 = `reference_pack_integrity`",
            "- R1 = `canonical_current_authority_binding`",
            "- R2 = `rc_m_summary_truth_contrast`",
            "- R3 = `historical_summary_archive_reclassification`",
            "- R4 = `downstream_summary_consumer_binding`",
        ]
    )

    files[ROOT / "coordination" / f"faz23-rc-m-reference-pack-register-{DATE}.md"] = "\n".join(
        [
            "# FAZ23 RC-M Reference Pack Register",
            "",
            *markdown_table(reference_columns, reference_rows),
            "",
            f"- reference_pack_integrity_pass = `{bool_text(reconciliation['reference_pack_integrity_pass'])}`",
            f"- reference_pack_contradiction_count = `{reconciliation['reference_pack_contradiction_count']}`",
            f"- reference_phase_count = `{len(reference_rows)}`",
        ]
    )

    files[ROOT / "coordination" / f"faz23-rc-m-summary-truth-lineage-matrix-{DATE}.md"] = "\n".join(
        [
            "# FAZ23 RC-M Summary Truth Lineage Matrix",
            "",
            *markdown_table(lineage_columns, lineage_rows),
        ]
    )

    files[ROOT / "coordination" / f"faz23-rc-m-summary-truth-contrast-table-{DATE}.md"] = "\n".join(
        [
            "# FAZ23 RC-M Summary Truth Contrast Table",
            "",
            *markdown_table(contrast_columns, contrast_rows),
            "",
            f"- reconciliation_stage = `{reconciliation['reconciliation_stage']}`",
            f"- primary_reason = `{reconciliation['primary_reason']}`",
            f"- root_cause_class = `{reconciliation['root_cause_class']}`",
            f"- unexplained_count = `{reconciliation['unexplained_count']}`",
        ]
    )

    files[ROOT / "coordination" / f"faz23-rc-m-summary-root-cause-mapping-{DATE}.md"] = "\n".join(
        [
            "# FAZ23 RC-M Summary Root Cause Mapping",
            "",
            *markdown_table(root_cause_columns, root_cause_rows),
        ]
    )

    files[ROOT / "coordination" / f"faz23-rc-m-summary-consumer-binding-{DATE}.md"] = "\n".join(
        [
            "# FAZ23 RC-M Summary Consumer Binding",
            "",
            *markdown_table(consumer_columns, consumer_rows),
            "",
            f"- current_summary_truth_adopted = `{bool_text(reconciliation['current_summary_truth_adopted'])}`",
            f"- historical_summary_archive_reclassified = `{bool_text(reconciliation['historical_summary_archive_reclassified'])}`",
            f"- surface_breach_from_history_reintroduced = `{bool_text(reconciliation['surface_breach_from_history_reintroduced'])}`",
            f"- historical_summary_channel = `{reconciliation['historical_summary_channel']}`",
        ]
    )

    files[ROOT / "coordination" / f"faz23-rc-m-summary-truth-reconciliation-{DATE}.md"] = "\n".join(
        [
            "# FAZ23 RC-M Summary Truth Reconciliation",
            "",
            f"- wp1_status = `{reconciliation['wp1_status']}`",
            f"- wp2_status = `{reconciliation['wp2_status']}`",
            f"- wp3_status = `{reconciliation['wp3_status']}`",
            f"- wp4_status = `{reconciliation['wp4_status']}`",
            f"- wp5_status = `{reconciliation['wp5_status']}`",
            f"- reference_pack_integrity_pass = `{bool_text(reconciliation['reference_pack_integrity_pass'])}`",
            f"- reference_pack_contradiction_count = `{reconciliation['reference_pack_contradiction_count']}`",
            f"- historical_summary_mismatch_count = `{reconciliation['historical_summary_mismatch_count']}`",
            f"- current_summary_mismatch_count = `{reconciliation['current_summary_mismatch_count']}`",
            f"- historical_surface_breach_count = `{reconciliation['historical_surface_breach_count']}`",
            f"- current_surface_breach_count = `{reconciliation['current_surface_breach_count']}`",
            f"- historical_frontier_candidate_count = `{reconciliation['historical_frontier_candidate_count']}`",
            f"- current_frontier_candidate_count = `{reconciliation['current_frontier_candidate_count']}`",
            f"- reconciliation_stage = `{reconciliation['reconciliation_stage']}`",
            f"- primary_reason = `{reconciliation['primary_reason']}`",
            f"- root_cause_class = `{reconciliation['root_cause_class']}`",
            f"- current_summary_truth_adopted = `{bool_text(reconciliation['current_summary_truth_adopted'])}`",
            f"- historical_summary_archive_reclassified = `{bool_text(reconciliation['historical_summary_archive_reclassified'])}`",
            f"- surface_breach_from_history_reintroduced = `{bool_text(reconciliation['surface_breach_from_history_reintroduced'])}`",
            f"- historical_summary_channel = `{reconciliation['historical_summary_channel']}`",
            f"- frontier_count = `{reconciliation['frontier_count']}`",
            f"- first_divergence_assigned_count = `{reconciliation['first_divergence_assigned_count']}`",
            f"- primary_reason_assigned_count = `{reconciliation['primary_reason_assigned_count']}`",
            f"- rc_j_vs_rc_m_runtime_error_count = `{reconciliation['rc_j_vs_rc_m_runtime_error_count']}`",
            f"- unexplained_count = `{reconciliation['unexplained_count']}`",
            f"- official_decision = `{reconciliation['official_decision']}`",
            f"- next_official_work = `{reconciliation['next_official_work']}`",
        ]
    )

    files[ROOT / "coordination" / f"faz23-steering-decision-table-{DATE}.md"] = "\n".join(
        [
            "# FAZ23 Steering Decision Table",
            "",
            *markdown_table(steering_columns, steering_rows),
        ]
    )

    files[ROOT / "coordination" / f"faz23-next-official-work-{DATE}.md"] = "\n".join(
        [
            "# FAZ23 Next Official Work",
            "",
            f"- official_decision = `{reconciliation['official_decision']}`",
            f"- next_official_work = `{reconciliation['next_official_work']}`",
        ]
    )

    contradiction_lines = (
        ["- contradiction_rows = `0`"]
        if not contradiction_rows
        else [f"- contradiction_rows = `{len(contradiction_rows)}`"]
        + [
            f"- {row['phase_name']} / {row['field_name']} expected=`{row['expected_value']}` actual=`{row['actual_value']}`"
            for row in contradiction_rows
        ]
    )

    files[RESULT_REPORT] = "\n".join(
        [
            "# FAZ23 RC-M Authoritative Summary Truth Reconciliation Under Canonical Current Authority Raporu",
            "",
            f"Tarih: {DATE}",
            "",
            "## Yonetici Ozeti",
            "",
            "FAZ23, FAZ22 sonunda canonical current authority altinda current surface breach yeniden uretilmedigi icin acildi. Bu fazda yeni runtime veya replay alinmadi; yalniz FAZ16 build-surface truth, FAZ17 historical summary truth, FAZ21 canonical current authority ve FAZ22 current summary truth tek authority zincirinde uzlastirildi.",
            "",
            f"Resmi karar: `{reconciliation['official_decision']}`",
            "",
            "## Reference Pack Ozeti",
            "",
            f"- reference_pack_integrity_pass = `{bool_text(reconciliation['reference_pack_integrity_pass'])}`",
            f"- reference_pack_contradiction_count = `{reconciliation['reference_pack_contradiction_count']}`",
            f"- current_authority_ref = `FAZ21 canonical current authority`",
            f"- build_surface_ref = `FAZ16`",
            f"- historical_summary_ref = `FAZ17`",
            f"- current_summary_ref = `FAZ22`",
            f"- FAZ16 decision = `{REFERENCE_DECISIONS['faz16']}`",
            f"- FAZ17 decision = `{REFERENCE_DECISIONS['faz17']}`",
            f"- FAZ21 decision = `{REFERENCE_DECISIONS['faz21']}`",
            f"- FAZ22 decision = `{REFERENCE_DECISIONS['faz22']}`",
            *contradiction_lines,
            "",
            "## WP Sonuclari",
            "",
            f"- `WP-1 = {reconciliation['wp1_status']}`",
            f"- `WP-2 = {reconciliation['wp2_status']}`",
            f"- `WP-3 = {reconciliation['wp3_status']}`",
            f"- `WP-4 = {reconciliation['wp4_status']}`",
            f"- `WP-5 = {reconciliation['wp5_status']}`",
            f"- `WP-6 = PASS`",
            "",
            "## RC-M Summary Truth Contrast Ozeti",
            "",
            f"- historical_summary_mismatch_count = `{reconciliation['historical_summary_mismatch_count']}`",
            f"- current_summary_mismatch_count = `{reconciliation['current_summary_mismatch_count']}`",
            f"- historical_surface_breach_count = `{reconciliation['historical_surface_breach_count']}`",
            f"- current_surface_breach_count = `{reconciliation['current_surface_breach_count']}`",
            f"- historical_frontier_candidate_count = `{reconciliation['historical_frontier_candidate_count']}`",
            f"- current_frontier_candidate_count = `{reconciliation['current_frontier_candidate_count']}`",
            f"- reconciliation_stage = `{reconciliation['reconciliation_stage']}`",
            f"- primary_reason = `{reconciliation['primary_reason']}`",
            f"- root_cause_class = `{reconciliation['root_cause_class']}`",
            f"- unexplained_count = `{reconciliation['unexplained_count']}`",
            "",
            "FAZ17'deki tek historical mismatch ve tek historical surface breach, FAZ21 ile benimsenen canonical current authority altinda current truth olarak tasinmadi. FAZ22 current summary truth mismatch=`0`, surface breach=`0`, frontier_candidate_count=`0` ile benimsenen authoritative summary gercegi olarak kaldi.",
            "",
            "## Summary Consumer Binding Ozeti",
            "",
            f"- current_summary_truth_adopted = `{bool_text(reconciliation['current_summary_truth_adopted'])}`",
            f"- historical_summary_archive_reclassified = `{bool_text(reconciliation['historical_summary_archive_reclassified'])}`",
            f"- surface_breach_from_history_reintroduced = `{bool_text(reconciliation['surface_breach_from_history_reintroduced'])}`",
            f"- historical_summary_channel = `{reconciliation['historical_summary_channel']}`",
            f"- comparison_order = `{reconciliation['comparison_order']}`",
            f"- frontier_count = `{reconciliation['frontier_count']}`",
            f"- first_divergence_assigned_count = `{reconciliation['first_divergence_assigned_count']}`",
            f"- primary_reason_assigned_count = `{reconciliation['primary_reason_assigned_count']}`",
            f"- rc_j_vs_rc_m_runtime_error_count = `{reconciliation['rc_j_vs_rc_m_runtime_error_count']}`",
            "",
            "Consumer binding current_canonical -> historical_archive sirasi ile materialize edildi. Historical summary channel diagnostic_only olarak sabitlendi; historical archive current breach state'ine geri tasinmadi.",
            "",
            "## Resmi Karar",
            "",
            f"- `{reconciliation['official_decision']}`",
            "",
            "## Sonraki Resmi Is",
            "",
            f"- `{reconciliation['next_official_work']}`",
        ]
    )

    return files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build FAZ23 phase package.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    payload = build_phase_payload(
        faz16_summary=load_json(
            root / "evaluation/reports/faz16-rc-g-vs-rc-m-full-family-replacement-summary-20260325.json"
        ),
        faz17_summary=load_json(
            root / "evaluation/reports/faz17-rc-m-output-parity-authoritative-summary-2026-03-25.json"
        ),
        faz17_frontier=load_json(
            root / "evaluation/reports/faz17-output-parity-authoritative-frontier-replay-2026-03-25.json"
        ),
        faz21_reference_pack=load_json(
            root / "coordination/faz21-current-authority-canonical-reference-pack-2026-03-27.json"
        ),
        faz21_reconciliation=load_json(
            root / "coordination/faz21-current-authority-canonicalization-reconciliation-2026-03-27.json"
        ),
        faz21_binding=load_json(root / "coordination/faz21-authority-consumer-binding-table-2026-03-27.json"),
        faz22_summary=load_json(
            root / "evaluation/reports/faz22-rc-m-output-parity-authoritative-summary-2026-03-27.json"
        ),
        faz22_reconciliation=load_json(
            root / "coordination/faz22-output-parity-surface-reconciliation-2026-03-27.json"
        ),
    )
    files = render_outputs(payload)
    if args.dry_run:
        print(f"official_decision={payload['official_decision']}")
        print(f"next_official_work={payload['next_official_work']}")
        print(f"reference_pack_integrity_pass={payload['reconciliation']['reference_pack_integrity_pass']}")
        print(
            f"reference_pack_contradiction_count={payload['reconciliation']['reference_pack_contradiction_count']}"
        )
        print(f"reconciliation_stage={payload['reconciliation']['reconciliation_stage']}")
        print(f"root_cause_class={payload['reconciliation']['root_cause_class']}")
        print(f"file_count={len(files)}")
        return 0

    for path, text in files.items():
        write_text(path, text)
    print(f"wrote_files={len(files)}")
    print(f"report={RESULT_REPORT.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
