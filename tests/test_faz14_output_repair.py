from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "faz14"))

from build_targeted_repair_gate import build_gate


def test_targeted_gate_passes_when_targeted_report_is_clean_and_diff_stays_in_contract() -> None:
    targeted = {
        "family_id": "v3-170",
        "normalized_request_hash_mismatch_count": 0,
        "model_request_payload_hash_mismatch_count": 0,
        "generation_contract_hash_mismatch_count": 0,
        "preprojection_anchor_mismatch_count": 0,
        "cited_projection_hash_mismatch_count": 0,
        "citation_set_projection_hash_mismatch_count": 0,
        "final_mode_mapping_hash_mismatch_count": 0,
        "blocked_reason_set_mismatch_count": 0,
        "final_answer_payload_hash_mismatch_count": 0,
        "response_envelope_hash_mismatch_count": 0,
        "serialized_output_hash_mismatch_count": 0,
        "answer_body_hash_mismatch_count": 0,
        "citation_body_hash_mismatch_count": 0,
        "refusal_body_hash_mismatch_count": 0,
        "runtime_error_count": 0,
        "mismatch_count": 0,
    }
    diff = {
        "mismatch_rows": [
            {
                "final_mode_mapping_hash_mismatch": 1,
                "blocked_reason_set_mismatch": 1,
                "response_envelope_hash_mismatch": 1,
            }
        ]
    }

    gate = build_gate(targeted_report=targeted, diff_report=diff)

    assert gate["allowed_changed_field_set"] == [
        "blocked_reason_set_hash",
        "final_mode_mapping_hash",
        "response_envelope_hash",
    ]
    assert gate["changed_field_outside_contract_count"] == 0
    assert gate["targeted_pass"] is True


def test_targeted_gate_fails_when_diff_leaks_outside_contract() -> None:
    targeted = {
        "family_id": "v3-170",
        "normalized_request_hash_mismatch_count": 0,
        "model_request_payload_hash_mismatch_count": 0,
        "generation_contract_hash_mismatch_count": 0,
        "preprojection_anchor_mismatch_count": 0,
        "cited_projection_hash_mismatch_count": 0,
        "citation_set_projection_hash_mismatch_count": 0,
        "final_mode_mapping_hash_mismatch_count": 0,
        "blocked_reason_set_mismatch_count": 0,
        "final_answer_payload_hash_mismatch_count": 0,
        "response_envelope_hash_mismatch_count": 0,
        "serialized_output_hash_mismatch_count": 0,
        "answer_body_hash_mismatch_count": 0,
        "citation_body_hash_mismatch_count": 0,
        "refusal_body_hash_mismatch_count": 0,
        "runtime_error_count": 0,
        "mismatch_count": 0,
    }
    diff = {
        "mismatch_rows": [
            {
                "answer_body_hash_mismatch": 1,
                "final_mode_mapping_hash_mismatch": 1,
            }
        ]
    }

    gate = build_gate(targeted_report=targeted, diff_report=diff)

    assert gate["changed_field_outside_contract_count"] == 1
    assert gate["targeted_pass"] is False
