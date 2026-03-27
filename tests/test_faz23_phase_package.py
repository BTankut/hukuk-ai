from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "faz23"))

from build_phase_package import build_phase_payload  # type: ignore


def _consumer_rows(history_channel: str = "diagnostic_only", reintroduced: bool = False) -> dict:
    return {
        "rows": [
            {
                "consumer_name": "current_authority_gate",
                "comparison_order": "current_canonical -> historical_archive",
                "current_channel": "authoritative",
                "history_channel": history_channel,
                "surface_breach_from_history_reintroduced": reintroduced,
                "primary_reference": "canonical_current_authority_ref",
                "secondary_reference": "historical_archive_ref",
                "notes": "test",
            }
        ]
    }


def test_faz23_payload_pass_path() -> None:
    payload = build_phase_payload(
        faz16_summary={
            "runtime_error_count": 0,
            "repair_surface_breach_count": 0,
            "new_frontier_count_outside_authority_snapshot": 0,
            "new_stage_count_outside_authority_snapshot": 0,
            "gate_pass": True,
        },
        faz17_summary={
            "runtime_error_count": 0,
            "authoritative_summary_mismatch_count": 1,
        },
        faz17_frontier={
            "frontier_count": 1,
            "output_parity_surface_breach_count": 1,
            "localized_authorized_downstream_drift_count": 0,
        },
        faz21_reference_pack={
            "reference_name": "canonical_current_authority_ref",
            "source_reference": "faz19",
            "control_pair_runtime_error_count": 0,
            "surface_breach_stage_set": [],
            "current_authority_contract_breach": False,
        },
        faz21_reconciliation={
            "current_canonical_authority_adopted": True,
            "historical_archive_reclassified": True,
            "downstream_consumer_binding_pass": True,
        },
        faz21_binding=_consumer_rows(),
        faz22_summary={
            "runtime_error_count": 0,
            "authoritative_summary_mismatch_count": 0,
            "output_parity_surface_breach_count": 0,
            "localized_authorized_downstream_drift_count": 0,
            "frontier_candidate_count": 0,
        },
        faz22_reconciliation={
            "authoritative_summary_mismatch_count": 0,
            "frontier_count": 0,
            "current_authority_contract_breach": False,
            "wp5_status": "NOT AUTHORIZED",
        },
    )

    assert (
        payload["official_decision"]
        == "PASS - RC-M Authoritative Summary Truth Reconciled Under Canonical Current Authority"
    )
    assert payload["next_official_work"] == "rc-m discard archival closure under canonical current authority"
    assert payload["reconciliation"]["reconciliation_stage"] == "R4"
    assert payload["reconciliation"]["root_cause_class"] == "historical_summary_truth_reclassified_to_archive"
    assert payload["reconciliation"]["unexplained_count"] == 0


def test_faz23_payload_fails_on_reference_contradiction() -> None:
    payload = build_phase_payload(
        faz16_summary={
            "runtime_error_count": 1,
            "repair_surface_breach_count": 0,
            "new_frontier_count_outside_authority_snapshot": 0,
            "new_stage_count_outside_authority_snapshot": 0,
            "gate_pass": True,
        },
        faz17_summary={
            "runtime_error_count": 0,
            "authoritative_summary_mismatch_count": 1,
        },
        faz17_frontier={
            "frontier_count": 1,
            "output_parity_surface_breach_count": 1,
            "localized_authorized_downstream_drift_count": 0,
        },
        faz21_reference_pack={
            "reference_name": "canonical_current_authority_ref",
            "source_reference": "faz19",
            "control_pair_runtime_error_count": 0,
            "surface_breach_stage_set": [],
            "current_authority_contract_breach": False,
        },
        faz21_reconciliation={
            "current_canonical_authority_adopted": True,
            "historical_archive_reclassified": True,
            "downstream_consumer_binding_pass": True,
        },
        faz21_binding=_consumer_rows(),
        faz22_summary={
            "runtime_error_count": 0,
            "authoritative_summary_mismatch_count": 0,
            "output_parity_surface_breach_count": 0,
            "localized_authorized_downstream_drift_count": 0,
            "frontier_candidate_count": 0,
        },
        faz22_reconciliation={
            "authoritative_summary_mismatch_count": 0,
            "frontier_count": 0,
            "current_authority_contract_breach": False,
            "wp5_status": "NOT AUTHORIZED",
        },
    )

    assert payload["reconciliation"]["reference_pack_integrity_pass"] is False
    assert payload["reconciliation"]["wp3_status"] == "FAIL"
    assert payload["official_decision"] == "NO-GO - Canonical Current Authority Summary Contract Breach"


def test_faz23_payload_fails_when_consumer_binding_breaks() -> None:
    payload = build_phase_payload(
        faz16_summary={
            "runtime_error_count": 0,
            "repair_surface_breach_count": 0,
            "new_frontier_count_outside_authority_snapshot": 0,
            "new_stage_count_outside_authority_snapshot": 0,
            "gate_pass": True,
        },
        faz17_summary={
            "runtime_error_count": 0,
            "authoritative_summary_mismatch_count": 1,
        },
        faz17_frontier={
            "frontier_count": 1,
            "output_parity_surface_breach_count": 1,
            "localized_authorized_downstream_drift_count": 0,
        },
        faz21_reference_pack={
            "reference_name": "canonical_current_authority_ref",
            "source_reference": "faz19",
            "control_pair_runtime_error_count": 0,
            "surface_breach_stage_set": [],
            "current_authority_contract_breach": False,
        },
        faz21_reconciliation={
            "current_canonical_authority_adopted": True,
            "historical_archive_reclassified": True,
            "downstream_consumer_binding_pass": True,
        },
        faz21_binding=_consumer_rows(history_channel="authoritative"),
        faz22_summary={
            "runtime_error_count": 0,
            "authoritative_summary_mismatch_count": 0,
            "output_parity_surface_breach_count": 0,
            "localized_authorized_downstream_drift_count": 0,
            "frontier_candidate_count": 0,
        },
        faz22_reconciliation={
            "authoritative_summary_mismatch_count": 0,
            "frontier_count": 0,
            "current_authority_contract_breach": False,
            "wp5_status": "NOT AUTHORIZED",
        },
    )

    assert payload["reconciliation"]["wp3_status"] == "FAIL"
    assert payload["reconciliation"]["wp4_status"] == "NOT AUTHORIZED"
    assert payload["reconciliation"]["wp5_status"] == "NOT AUTHORIZED"
    assert payload["official_decision"] == "NO-GO - Canonical Current Authority Summary Contract Breach"
