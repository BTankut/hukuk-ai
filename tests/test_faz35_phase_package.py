from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "faz35"))

from build_phase_package import build_materialization_payload, build_phase_payload  # type: ignore
from faz35_lib import FAIL_REFERENCE, PASS_DECISION  # type: ignore


def test_materialization_preserves_faz34_frontier_truth() -> None:
    payload = build_materialization_payload()
    frontier = payload["frontier_truth"]
    response = payload["response_truth"]
    acceptance = payload["acceptance"]

    assert frontier["frontier_record_count"] == 174
    assert frontier["faz1_50_mismatch_count"] == 18
    assert frontier["v2_95_mismatch_count"] == 57
    assert frontier["v3_170_mismatch_count"] == 99
    assert frontier["preprojection_hash_mismatch_count"] == 174
    assert frontier["raw_answer_hash_mismatch_count"] == 174
    assert frontier["unexplained_count"] == 0
    assert response["response_envelope_subfrontier_record_count"] == 109
    assert response["response_envelope_hash_mismatch_count"] == 109
    assert acceptance["refusal_smoke_status_code"] == 500
    assert acceptance["backup_restore_missing_file_count"] == 3


def test_phase_payload_passes_with_authoritative_truth() -> None:
    payload = build_phase_payload(build_materialization_payload())
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
        "WP-9": "PASS",
    }
    assert payload["control_isolation"]["minimal_failing_control_set"].startswith("S1 =")
    assert payload["stage_ladder"]["dominant_stage"] == "P11"


def test_phase_payload_fails_on_reference_pack_contradiction() -> None:
    materialized = build_materialization_payload()
    materialized["reference_pack"]["reference_pack_integrity_pass"] = False
    materialized["reference_pack"]["reference_pack_contradiction_count"] = 1

    payload = build_phase_payload(materialized)
    assert payload["wp_statuses"]["WP-1"] == "FAIL"
    assert payload["official_decision"] == FAIL_REFERENCE
