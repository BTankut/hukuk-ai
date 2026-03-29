from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "faz29"))

from build_phase_package import build_phase_payload  # type: ignore
from faz29_lib import (  # type: ignore
    ACCEPTANCE_EXPECTED,
    BOUNDARY_EXPECTED,
    FAIL_INCONCLUSIVE,
    FAIL_UNSTABLE,
    FAIL_UPSTREAM_EQUALITY,
    PASS_DECISION,
    RETENTION_EXPECTED,
    SPILLOVER_EXPECTED,
)
from materialize_reference_pack import build_materialization_payload  # type: ignore


def _capture_truth() -> dict:
    return {
        "wp2": {
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
        "wp3": dict(BOUNDARY_EXPECTED),
        "wp4": dict(SPILLOVER_EXPECTED),
        "wp5": dict(ACCEPTANCE_EXPECTED),
        "wp6": dict(RETENTION_EXPECTED),
    }


def test_materialized_payload_freezes_exact_contract() -> None:
    payload = build_materialization_payload()

    assert payload["reference_pack"]["candidate_id"] == "RC-O"
    assert payload["reference_pack"]["forensic_reference_candidate"] == "RC-N"
    assert payload["manifest"]["candidate_status"] == "frozen_failed_repair_candidate"
    assert len(payload["frontier_records"]) == 166
    assert len(payload["repair_delta_records"]) == 14
    assert len(payload["spillover_guard_records"]) == 24


def test_phase_payload_passes_on_exact_recapture_truth() -> None:
    materialized = build_materialization_payload()
    capture = _capture_truth()
    payload = build_phase_payload(materialized=materialized, capture_a=capture, capture_b=capture)

    assert payload["official_decision"] == PASS_DECISION
    assert payload["wp_statuses"] == {
        "WP-1": "PASS",
        "WP-2": "PASS",
        "WP-3": "PASS",
        "WP-4": "PASS",
        "WP-5": "PASS",
        "WP-6": "PASS",
        "WP-7": "PASS",
    }


def test_phase_payload_maps_wp2_fail_to_upstream_drift() -> None:
    materialized = build_materialization_payload()
    capture_a = _capture_truth()
    capture_b = _capture_truth()
    capture_b["wp2"]["model_request_payload_hash_mismatch_count"] = 1
    payload = build_phase_payload(materialized=materialized, capture_a=capture_a, capture_b=capture_b)

    assert payload["wp_statuses"]["WP-2"] == "FAIL"
    assert payload["official_decision"] == FAIL_UPSTREAM_EQUALITY


def test_phase_payload_maps_exact_truth_delta_to_unstable() -> None:
    materialized = build_materialization_payload()
    capture = _capture_truth()
    capture["wp3"]["remaining_mismatch_count"] = 151
    payload = build_phase_payload(materialized=materialized, capture_a=capture, capture_b=capture)

    assert payload["wp_statuses"]["WP-3"] == "FAIL"
    assert payload["official_decision"] == FAIL_UNSTABLE


def test_phase_payload_maps_runtime_error_to_inconclusive() -> None:
    materialized = build_materialization_payload()
    capture = _capture_truth()
    capture["wp5"]["runtime_error_count"] = 1
    payload = build_phase_payload(materialized=materialized, capture_a=capture, capture_b=capture)

    assert payload["wp_statuses"]["WP-5"] == "FAIL"
    assert payload["official_decision"] == FAIL_INCONCLUSIVE
