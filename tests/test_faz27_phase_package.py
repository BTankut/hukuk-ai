from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "faz27"))

from build_phase_package import build_phase_payload  # type: ignore
from faz27_lib import FAIL_BOUNDARY_TRUTH_DRIFT, PASS_DECISION  # type: ignore
from materialize_reference_pack import build_materialization_payload  # type: ignore


def _single_control_ladder() -> dict:
    return {
        "rows": [],
        "first_break_control": "mandatory auth",
        "first_break_step": "B1",
        "first_break_stage": "preprojection_hash",
        "first_break_count": 166,
        "dominant_control": "mandatory auth",
        "dominant_stage": "preprojection_hash",
        "effective_control_set": ["mandatory auth"],
        "single_control_root_cause_found": True,
        "interaction_root_cause_found": False,
        "unexplained_count": 0,
    }


def _single_control_pair() -> dict:
    return {
        "preprojection_hash_mismatch_count": 166,
        "raw_answer_hash_mismatch_count": 166,
        "response_envelope_hash_mismatch_count": 0,
        "runtime_error_count": 0,
    }


def test_materialized_reference_pack_preserves_166_row_boundary_truth() -> None:
    payload = build_materialization_payload()
    boundary = payload["boundary_summary"]
    frontier = payload["frontier_freeze"]

    assert boundary["faz1_50_mismatch_count"] == 16
    assert boundary["v2_95_mismatch_count"] == 56
    assert boundary["v3_170_mismatch_count"] == 94
    assert boundary["preprojection_hash_mismatch_count"] == 166
    assert boundary["raw_answer_hash_mismatch_count"] == 166
    assert boundary["frontier_total"] == 166
    assert frontier["frontier_total"] == 166
    assert frontier["records"][0]["id"].startswith("faz1-50::")
    assert frontier["records"][-1]["id"].startswith("v3-170::")


def test_phase_payload_passes_when_boundary_truth_and_single_control_hold() -> None:
    materialized = build_materialization_payload()
    payload = build_phase_payload(
        materialized=materialized,
        ladder=_single_control_ladder(),
        additive_report=_single_control_pair(),
        subtractive_report=_single_control_pair(),
        interaction_payload=None,
    )

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


def test_phase_payload_fails_when_authoritative_boundary_truth_drifts() -> None:
    materialized = build_materialization_payload()
    materialized["boundary_summary"]["frontier_total"] = 112
    payload = build_phase_payload(
        materialized=materialized,
        ladder=_single_control_ladder(),
        additive_report=_single_control_pair(),
        subtractive_report=_single_control_pair(),
        interaction_payload=None,
    )

    assert payload["wp_statuses"]["WP-3"] == "FAIL"
    assert payload["official_decision"] == FAIL_BOUNDARY_TRUTH_DRIFT
