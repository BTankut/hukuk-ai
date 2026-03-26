from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "faz17"))

from build_authoritative_family_report import build_report as build_family_report
from build_authoritative_summary import build_summary
from build_final_report_pack import decide
from build_frontier_localization import build_payload


def test_family_report_adds_body_hash_counts() -> None:
    source = {
        "family_id": "faz1-50",
        "question_count": 1,
        "reference_runtime_error_count": 0,
        "candidate_runtime_error_count": 0,
        "mismatch_count": 1,
        "family_metric_delta_zero": True,
        "metric_delta": {"citation_delta": 0, "correct_source_delta": 0, "hallucination_delta": 0, "refusal_delta": 0, "error_delta": 0},
        "authoritative_rows": [
            {
                "question_id": "TBK-027",
                "answer_body_hash": "a",
                "reference_answer_body_hash": "b",
                "citation_body_hash": "c",
                "reference_citation_body_hash": "c",
                "refusal_body_hash": "d",
                "reference_refusal_body_hash": "d",
            }
        ],
        "mismatch_rows": [{"question_id": "TBK-027", "first_divergence_stage": "final_answer_payload_hash", "primary_reason": "x"}],
    }
    report = build_family_report(source)
    assert report["answer_body_hash_mismatch_count"] == 1
    assert report["citation_body_hash_mismatch_count"] == 0
    assert report["gate_pass"] is False


def test_summary_passes_only_when_all_families_pass() -> None:
    summary = build_summary(
        [
            {"family_id": "faz1-50", "question_count": 1, "runtime_error_count": 0, "mismatch_count": 0, "family_metric_delta_zero": True, "gate_pass": True},
            {"family_id": "v2-95", "question_count": 1, "runtime_error_count": 0, "mismatch_count": 0, "family_metric_delta_zero": True, "gate_pass": True},
            {"family_id": "v3-170", "question_count": 1, "runtime_error_count": 0, "mismatch_count": 0, "family_metric_delta_zero": True, "gate_pass": True},
        ]
    )
    assert summary["wp3_pass"] is True


def test_frontier_localization_marks_unauthorized_record_as_surface_breach() -> None:
    authoritative_reports = [
        {
            "family_id": "faz1-50",
            "mismatch_rows": [
                {
                    "family_id": "faz1-50",
                    "question_id": "TBK-027",
                    "ordinal_index": 27,
                    "normalized_request_hash_mismatch": 0,
                    "model_request_payload_hash_mismatch": 0,
                    "generation_contract_hash_mismatch": 0,
                    "preprojection_anchor_mismatch": 0,
                    "cited_projection_hash_mismatch": 0,
                    "citation_set_projection_hash_mismatch": 0,
                    "first_divergence_stage": "final_answer_payload_hash",
                    "primary_reason": "response_envelope_projection_delta",
                }
            ],
        }
    ]
    diagnostic_reports = [
        {
            "family_id": "faz1-50",
            "authoritative_rows": [
                {
                    "question_id": "TBK-027",
                    "runtime_error": 0,
                    "reference_runtime_error": 0,
                    "changed_field_set": [],
                    "changed_field_outside_contract": [],
                }
            ],
            "mismatch_rows": [],
        }
    ]
    _, _, _, replay, _ = build_payload(authoritative_reports, diagnostic_reports)
    assert replay["output_parity_surface_breach_count"] == 1
    assert replay["localized_authorized_downstream_drift_count"] == 0


def test_final_decision_selects_surface_breach_when_wp3_fails() -> None:
    decision, next_work = decide(
        wp3_summary={"wp3_pass": False, "runtime_error_count": 0},
        wp4_frontier_replay={"output_parity_surface_breach_count": 1},
    )
    assert decision == "NO-GO - RC-M Output Parity Surface Breach"
    assert next_work == "rc-m discard and output-parity surface forensics"
