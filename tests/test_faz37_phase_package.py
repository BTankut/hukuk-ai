from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "faz37"))

from build_phase_package import build_materialized_payload, build_phase_payload  # type: ignore
from faz37_lib import (  # type: ignore
    CURRENT_AUTHORITY_EXPECTED,
    FAIL_AUTHORITY,
    FAIL_INCONCLUSIVE,
    FAIL_UNSTABLE,
    FAZ36_ACCEPTANCE_EXPECTED,
    FAZ36_FRONTIER_EXPECTED,
    FAZ36_FULL_FAMILY_EXPECTED,
    FAZ36_RESPONSE_EXPECTED,
    FAZ36_RETENTION_EXPECTED,
    PASS_DECISION,
)


def _capture_truth() -> dict:
    return {
        "wp2": {
            **CURRENT_AUTHORITY_EXPECTED,
            "control_pair_runtime_error_count": 0,
        },
        "wp3": dict(FAZ36_FRONTIER_EXPECTED),
        "wp4": dict(FAZ36_RESPONSE_EXPECTED),
        "wp5": dict(FAZ36_ACCEPTANCE_EXPECTED),
        "wp6": dict(FAZ36_FULL_FAMILY_EXPECTED),
        "wp7": dict(FAZ36_RETENTION_EXPECTED),
    }


def test_materialized_payload_freezes_exact_contract() -> None:
    payload = build_materialized_payload()

    assert payload["reference_pack"]["rc_q_failed_repair_truth_ref"] == "FAZ36"
    assert payload["manifest"]["candidate_id"] == "RC-Q"
    assert payload["manifest"]["current_evaluable"] is True
    assert len(payload["frontier_records"]) == 174
    assert len(payload["response_records"]) == 109


def test_phase_payload_passes_on_exact_recapture_truth() -> None:
    capture = _capture_truth()
    payload = build_phase_payload(capture_a=capture, capture_b=capture)

    assert payload["official_decision"] == PASS_DECISION
    assert payload["wp_statuses"] == {
        "WP-1": "PASS",
        "WP-2": "PASS",
        "WP-3": "PASS",
        "WP-4": "PASS",
        "WP-5": "PASS",
        "WP-6": "PASS",
        "WP-7": "PASS",
        "WP-8": "PASS",
    }


def test_phase_payload_maps_wp2_fail_to_authority_drift() -> None:
    capture_a = _capture_truth()
    capture_b = _capture_truth()
    capture_b["wp2"]["model_request_payload_hash_mismatch_count"] = 1
    payload = build_phase_payload(capture_a=capture_a, capture_b=capture_b)

    assert payload["wp_statuses"]["WP-2"] == "FAIL"
    assert payload["official_decision"] == FAIL_AUTHORITY


def test_phase_payload_maps_ab_instability_to_inconclusive() -> None:
    capture_a = _capture_truth()
    capture_b = _capture_truth()
    capture_b["wp3"]["preprojection_hash_mismatch_count"] = 150
    payload = build_phase_payload(capture_a=capture_a, capture_b=capture_b)

    assert payload["wp_statuses"]["WP-3"] == "FAIL"
    assert payload["official_decision"] == FAIL_INCONCLUSIVE


def test_phase_payload_maps_stable_delta_to_unstable() -> None:
    capture = _capture_truth()
    capture["wp3"]["preprojection_hash_mismatch_count"] = 150
    payload = build_phase_payload(capture_a=capture, capture_b=capture)

    assert payload["wp_statuses"]["WP-3"] == "FAIL"
    assert payload["official_decision"] == FAIL_UNSTABLE
