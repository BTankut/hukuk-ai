from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "faz16"))

from build_breach_sentinel_16 import build_pack
from build_candidate_isolation_gate import build_gate as build_candidate_gate
from build_current_authority_summary import build_summary
from build_final_report_pack import decide
from build_replacement_gate import build_full_gate, build_targeted_gate


def test_breach_sentinel_selection_is_deterministic() -> None:
    payload = {
        "rows": [
            {"family_id": "faz1-50", "question_id": f"TBK-0{i:02d}", "ordinal_index": i}
            for i in range(1, 8)
        ]
        + [
            {"family_id": "v2-95", "question_id": f"TBK-1{i:02d}", "ordinal_index": i}
            for i in range(1, 10)
        ]
        + [
            {"family_id": "v3-170", "question_id": f"TBK-2{i:02d}", "ordinal_index": i}
            for i in range(1, 10)
        ]
    }
    pack = build_pack(payload)
    assert pack["count"] == 16
    assert pack["family_breakdown"] == {"faz1-50": 4, "v2-95": 6, "v3-170": 6}
    assert [row["question_id"] for row in pack["rows"][:4]] == ["TBK-001", "TBK-002", "TBK-003", "TBK-004"]


def test_current_authority_summary_passes_with_downstream_only_diff() -> None:
    summary = build_summary(
        [
            {
                "family_id": "faz1-50",
                "reference_runtime_error_count": 0,
                "candidate_runtime_error_count": 0,
                "family_metric_delta_zero": True,
                "mismatch_count": 1,
                "mismatch_rows": [{"question_id": "TBK-027", "first_divergence_stage": "final_answer_payload_hash"}],
            },
            {
                "family_id": "v2-95",
                "reference_runtime_error_count": 0,
                "candidate_runtime_error_count": 0,
                "family_metric_delta_zero": True,
                "mismatch_count": 0,
                "mismatch_rows": [],
            },
            {
                "family_id": "v3-170",
                "reference_runtime_error_count": 0,
                "candidate_runtime_error_count": 0,
                "family_metric_delta_zero": True,
                "mismatch_count": 0,
                "mismatch_rows": [],
            },
        ]
    )
    assert summary["wp2_pass"] is True
    assert summary["control_pair_breach_in_f0_f12"] is False


def test_candidate_isolation_gate_flags_outside_authorized_record() -> None:
    summary, table = build_candidate_gate(
        [
            {
                "family_id": "v3-170",
                "question_count": 6,
                "runtime_error_count": 0,
                "mismatch_count": 1,
                "normalized_request_hash_mismatch_count": 0,
                "model_request_payload_hash_mismatch_count": 0,
                "generation_contract_hash_mismatch_count": 0,
                "preprojection_anchor_mismatch_count": 0,
                "cited_projection_hash_mismatch_count": 0,
                "citation_set_projection_hash_mismatch_count": 0,
                "final_mode_mapping_hash_mismatch_count": 1,
                "blocked_reason_set_mismatch_count": 1,
                "response_envelope_hash_mismatch_count": 1,
                "changed_field_outside_contract_count": 0,
                "mismatch_rows": [
                    {
                        "question_id": "TBK-999",
                        "ordinal_index": 9,
                        "first_divergence_stage": "final_mode_mapping_hash",
                        "primary_reason": "final_mode_mapping_delta",
                        "changed_field_set": ["final_mode_mapping_hash"],
                        "changed_field_outside_contract": [],
                        "normalized_request_hash_mismatch": 0,
                        "model_request_payload_hash_mismatch": 0,
                        "generation_contract_hash_mismatch": 0,
                        "preprojection_anchor_mismatch": 0,
                        "cited_projection_hash_mismatch": 0,
                        "citation_set_projection_hash_mismatch": 0,
                    }
                ],
            }
        ],
        allowed_question_ids={"TBK-051"},
    )
    assert summary["gate_pass"] is False
    assert summary["changed_record_outside_authorized_set_count"] == 1
    assert table["rows"][0]["outside_authorized_record_set"] is True


def test_replacement_gate_detects_new_stage_outside_authority_snapshot() -> None:
    summary, table = build_full_gate(
        [
            {
                "family_id": "faz1-50",
                "reference_runtime_error_count": 0,
                "candidate_runtime_error_count": 0,
                "family_metric_delta_zero": True,
                "mismatch_rows": [
                    {"question_id": "TBK-027", "ordinal_index": 27, "first_divergence_stage": "response_envelope_hash"}
                ],
            }
        ],
        [
            {
                "family_id": "faz1-50",
                "mismatch_rows": [
                    {"question_id": "TBK-027", "ordinal_index": 27, "first_divergence_stage": "final_answer_payload_hash"}
                ]
            }
        ],
    )
    assert summary["gate_pass"] is False
    assert summary["new_stage_count_outside_authority_snapshot"] == 1
    assert table["rows"][0]["kind"] == "new_stage_outside_authority_snapshot"


def test_replacement_targeted_gate_passes_with_zero_mismatch() -> None:
    gate = build_targeted_gate(
        [
            {
                "reference_runtime_error_count": 0,
                "candidate_runtime_error_count": 0,
                "mismatch_count": 0,
                "changed_field_outside_contract_count": 0,
                "family_metric_delta_zero": True,
            }
        ]
    )
    assert gate["gate_pass"] is True


def test_replacement_targeted_gate_fails_on_outside_contract_field() -> None:
    gate = build_targeted_gate(
        [
            {
                "reference_runtime_error_count": 0,
                "candidate_runtime_error_count": 0,
                "mismatch_count": 0,
                "changed_field_outside_contract_count": 1,
                "family_metric_delta_zero": True,
            }
        ]
    )
    assert gate["gate_pass"] is False
    assert gate["changed_field_outside_contract_count"] == 1


def test_final_report_decision_allows_early_control_authority_stop() -> None:
    decision, next_work = decide(
        wp2_summary={"wp2_pass": False},
        wp3_manifest=None,
        wp4_candidate_gate=None,
        wp4_replacement_gate=None,
        wp5_gate=None,
        wp6_candidate_gate=None,
        wp6_replacement_gate=None,
    )
    assert decision == "NO-GO - Control Authority Unstable"
    assert next_work == "rc-g-vs-rc-j current authority recapture repeatability forensics"
