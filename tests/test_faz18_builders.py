from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "faz18"))

from build_authoritative_adoption import build_payload as build_adoption_payload
from build_control_authority_summary import build_summary
from build_final_report_pack import decide
from build_surface_not_authorized_pack import build_payloads


def test_control_summary_marks_current_authority_unstable() -> None:
    reports = [
        {
            "family_id": "faz1-50",
            "mismatch_count": 1,
            "candidate_runtime_error_count": 0,
            "reference_runtime_error_count": 0,
            "family_metric_delta_zero": True,
            "normalized_request_hash_mismatch_count": 0,
            "model_request_payload_hash_mismatch_count": 0,
            "generation_contract_hash_mismatch_count": 0,
            "preprojection_anchor_mismatch_count": 0,
            "final_mode_mapping_hash_mismatch_count": 0,
            "blocked_reason_set_mismatch_count": 0,
            "response_envelope_hash_mismatch_count": 0,
            "mismatch_rows": [{"first_divergence_stage": "final_answer_payload_hash"}],
        },
        {
            "family_id": "v2-95",
            "mismatch_count": 0,
            "candidate_runtime_error_count": 0,
            "reference_runtime_error_count": 0,
            "family_metric_delta_zero": True,
            "normalized_request_hash_mismatch_count": 0,
            "model_request_payload_hash_mismatch_count": 0,
            "generation_contract_hash_mismatch_count": 0,
            "preprojection_anchor_mismatch_count": 0,
            "final_mode_mapping_hash_mismatch_count": 0,
            "blocked_reason_set_mismatch_count": 0,
            "response_envelope_hash_mismatch_count": 0,
            "mismatch_rows": [],
        },
        {
            "family_id": "v3-170",
            "mismatch_count": 0,
            "candidate_runtime_error_count": 0,
            "reference_runtime_error_count": 0,
            "family_metric_delta_zero": True,
            "normalized_request_hash_mismatch_count": 0,
            "model_request_payload_hash_mismatch_count": 0,
            "generation_contract_hash_mismatch_count": 0,
            "preprojection_anchor_mismatch_count": 0,
            "final_mode_mapping_hash_mismatch_count": 0,
            "blocked_reason_set_mismatch_count": 0,
            "response_envelope_hash_mismatch_count": 0,
            "mismatch_rows": [],
        },
    ]
    summary = build_summary(reports)
    assert summary["wp3_pass"] is False
    assert summary["control_pair_authority_match"] is False
    assert summary["control_pair_breach_in_f0_f12"] is False


def test_authoritative_adoption_preserves_source_metrics() -> None:
    payload = build_adoption_payload(
        source_report={"family_id": "faz1-50", "mismatch_count": 1, "runtime_error_count": 0},
        source_report_path="x.json",
        status="NOT AUTHORIZED",
        reason="WP-3 FAIL",
    )
    assert payload["status"] == "NOT AUTHORIZED"
    assert payload["mismatch_count"] == 1


def test_surface_not_authorized_pack_keeps_single_frontier_reference() -> None:
    mismatch_table, frontier_pack, frontier_replay, diagnostic, root_cause = build_payloads(
        frontier_replay={
            "frontier_count": 1,
            "first_divergence_assigned_count": 1,
            "primary_reason_assigned_count": 1,
            "classification_assigned_count": 1,
            "unexplained_count": 0,
            "output_parity_surface_breach_count": 1,
            "localized_authorized_downstream_drift_count": 0,
            "rows": [
                {
                    "family_id": "faz1-50",
                    "question_id": "TBK-027",
                    "ordinal_index": 27,
                    "first_divergence_stage": "final_answer_payload_hash",
                    "primary_reason": "response_envelope_projection_delta",
                }
            ],
        },
        diagnostic={
            "frontier_count": 1,
            "rc_j_vs_rc_m_runtime_error_count": 0,
            "changed_record_outside_authorized_set_count": 1,
            "changed_field_outside_contract_count": 0,
            "rows": [],
        },
        reason="WP-3 FAIL",
    )
    assert mismatch_table["status"] == "NOT AUTHORIZED"
    assert frontier_pack["frontier_count"] == 1
    assert frontier_replay["rows"][0]["first_divergence_stage_o"] == "final_answer_payload_hash"
    assert diagnostic["status"] == "NOT AUTHORIZED"
    assert root_cause["rows"][0]["frontier_record_id"] == "faz1-50/TBK-027/27"


def test_final_decision_maps_wp3_fail_to_current_authority_recapture() -> None:
    decision, next_work, wp3_status, wp4_status, wp5_status = decide(
        control_summary={"wp3_pass": False, "control_pair_authority_match": False, "control_pair_runtime_error_count": 0},
        authoritative_summary={"status": "NOT AUTHORIZED", "runtime_error_count": 0, "authoritative_summary_mismatch_count": 1},
        frontier_replay={"status": "NOT AUTHORIZED", "frontier_count": 1, "unexplained_count": 0},
    )
    assert decision == "NO-GO - Current Authority Unstable"
    assert next_work == "current authority recapture"
    assert (wp3_status, wp4_status, wp5_status) == ("FAIL", "NOT AUTHORIZED", "NOT AUTHORIZED")
