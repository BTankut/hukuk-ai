from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "faz21"))

from build_phase_package import build_phase_payload  # type: ignore


def _reference(name: str, rows: list[dict]) -> dict:
    return {
        "reference_name": name,
        "candidate_pair": "rc_g_vs_rc_j",
        "families": rows,
        "reference_pack_hash": f"{name}-hash",
        "reference_pack_integrity_pass": True,
        "reference_pack_contradiction_count": 0,
    }


def test_faz21_phase_payload_passes_for_faz20_truth() -> None:
    faz20_reconciliation = {
        "wp3_pass": True,
        "wp4_pass": True,
        "wp5_pass": True,
        "replay_19_reference_match": True,
        "surface_breach_stage_set": [],
        "recording_only_stage_set": [],
        "frontier_count": 2,
        "first_divergence_assigned_count": 2,
        "primary_reason_assigned_count": 2,
        "unexplained_count": 0,
        "dominant_stage": "H10",
        "dominant_reason": "authority_summary_materialization_delta",
    }
    faz20_truth_matrix = {
        "rows": [
            {
                "replay_name": "faz13",
                "family_name": "v3-170",
                "reference_mismatch_count": 6,
                "reference_mismatch_question_ids": ["TBK-051", "TBK-054"],
            },
            {
                "replay_name": "faz18",
                "family_name": "faz1-50",
                "reference_mismatch_count": 1,
                "reference_mismatch_question_ids": ["TBK-027"],
            },
        ]
    }
    faz20_root_cause = {
        "rows": [
            {
                "replay_name": "faz13",
                "family_name": "v3-170",
                "first_divergence_stage": "H10",
                "primary_reason": "authority_summary_materialization_delta",
                "reference_mismatch_ordinals": [1, 4],
            },
            {
                "replay_name": "faz18",
                "family_name": "faz1-50",
                "first_divergence_stage": "H10",
                "primary_reason": "authority_summary_materialization_delta",
                "reference_mismatch_ordinals": [27],
            },
        ]
    }
    faz19_reference = _reference(
        "faz19",
        [
            {
                "family_name": "faz1-50",
                "mismatch_count": 0,
                "runtime_error_count": 0,
                "family_metric_delta_zero": True,
                "mismatch_stage_histogram": {},
                "mismatch_question_ids": [],
                "mismatch_ordinals": [],
            },
            {
                "family_name": "v2-95",
                "mismatch_count": 0,
                "runtime_error_count": 0,
                "family_metric_delta_zero": True,
                "mismatch_stage_histogram": {},
                "mismatch_question_ids": [],
                "mismatch_ordinals": [],
            },
            {
                "family_name": "v3-170",
                "mismatch_count": 0,
                "runtime_error_count": 0,
                "family_metric_delta_zero": True,
                "mismatch_stage_histogram": {},
                "mismatch_question_ids": [],
                "mismatch_ordinals": [],
            },
        ],
    )

    payload = build_phase_payload(
        faz20_reconciliation=faz20_reconciliation,
        faz20_truth_matrix=faz20_truth_matrix,
        faz20_root_cause=faz20_root_cause,
        faz13_reference=_reference(
            "faz13",
            [
                {
                    "family_name": "v3-170",
                    "mismatch_count": 6,
                    "runtime_error_count": 0,
                    "family_metric_delta_zero": True,
                    "mismatch_stage_histogram": {"final_mode_mapping_hash": 6},
                    "mismatch_question_ids": ["TBK-051", "TBK-054"],
                    "mismatch_ordinals": [1, 4],
                    "first_divergence_stage_set": ["final_mode_mapping_hash"],
                    "reason_histogram": {"final_mode_mapping_delta": 6},
                }
            ],
        ),
        faz18_reference=_reference(
            "faz18",
            [
                {
                    "family_name": "faz1-50",
                    "mismatch_count": 1,
                    "runtime_error_count": 0,
                    "family_metric_delta_zero": True,
                    "mismatch_stage_histogram": {"final_answer_payload_hash": 1},
                    "mismatch_question_ids": ["TBK-027"],
                    "mismatch_ordinals": [27],
                    "first_divergence_stage_set": ["final_answer_payload_hash"],
                    "reason_histogram": {"response_envelope_projection_delta": 1},
                }
            ],
        ),
        faz19_reference=faz19_reference,
    )

    assert payload["official_decision"] == "PASS - Current Authority Canonicalized"
    assert payload["next_official_work"] == "rc-m discard and output-parity surface forensics reopen under canonical current authority"
    assert payload["gate_payload"]["current_canonical_authority_adopted"] is True
    assert payload["gate_payload"]["historical_archive_reclassified"] is True
    assert payload["gate_payload"]["downstream_consumer_binding_pass"] is True


def test_faz21_phase_payload_fails_when_replay19_match_breaks() -> None:
    faz20_reconciliation = {
        "wp3_pass": True,
        "wp4_pass": True,
        "wp5_pass": True,
        "replay_19_reference_match": False,
        "surface_breach_stage_set": [],
        "recording_only_stage_set": [],
        "frontier_count": 2,
        "first_divergence_assigned_count": 2,
        "primary_reason_assigned_count": 2,
        "unexplained_count": 0,
        "dominant_stage": "H10",
        "dominant_reason": "authority_summary_materialization_delta",
    }
    faz20_truth_matrix = {
        "rows": [
            {
                "replay_name": "faz13",
                "family_name": "v3-170",
                "reference_mismatch_count": 6,
                "reference_mismatch_question_ids": ["TBK-051"],
            },
            {
                "replay_name": "faz18",
                "family_name": "faz1-50",
                "reference_mismatch_count": 1,
                "reference_mismatch_question_ids": ["TBK-027"],
            },
        ]
    }
    faz20_root_cause = {
        "rows": [
            {
                "replay_name": "faz13",
                "family_name": "v3-170",
                "first_divergence_stage": "H10",
                "primary_reason": "authority_summary_materialization_delta",
                "reference_mismatch_ordinals": [1],
            },
            {
                "replay_name": "faz18",
                "family_name": "faz1-50",
                "first_divergence_stage": "H10",
                "primary_reason": "authority_summary_materialization_delta",
                "reference_mismatch_ordinals": [27],
            },
        ]
    }
    faz19_reference = _reference(
        "faz19",
        [
            {
                "family_name": "faz1-50",
                "mismatch_count": 0,
                "runtime_error_count": 0,
                "family_metric_delta_zero": True,
                "mismatch_stage_histogram": {},
                "mismatch_question_ids": [],
                "mismatch_ordinals": [],
            },
            {
                "family_name": "v2-95",
                "mismatch_count": 0,
                "runtime_error_count": 0,
                "family_metric_delta_zero": True,
                "mismatch_stage_histogram": {},
                "mismatch_question_ids": [],
                "mismatch_ordinals": [],
            },
            {
                "family_name": "v3-170",
                "mismatch_count": 0,
                "runtime_error_count": 0,
                "family_metric_delta_zero": True,
                "mismatch_stage_histogram": {},
                "mismatch_question_ids": [],
                "mismatch_ordinals": [],
            },
        ],
    )

    payload = build_phase_payload(
        faz20_reconciliation=faz20_reconciliation,
        faz20_truth_matrix=faz20_truth_matrix,
        faz20_root_cause=faz20_root_cause,
        faz13_reference=_reference(
            "faz13",
            [
                {
                    "family_name": "v3-170",
                    "mismatch_count": 6,
                    "runtime_error_count": 0,
                    "family_metric_delta_zero": True,
                    "mismatch_stage_histogram": {"final_mode_mapping_hash": 6},
                    "mismatch_question_ids": ["TBK-051"],
                    "mismatch_ordinals": [1],
                    "first_divergence_stage_set": ["final_mode_mapping_hash"],
                    "reason_histogram": {"final_mode_mapping_delta": 6},
                }
            ],
        ),
        faz18_reference=_reference(
            "faz18",
            [
                {
                    "family_name": "faz1-50",
                    "mismatch_count": 1,
                    "runtime_error_count": 0,
                    "family_metric_delta_zero": True,
                    "mismatch_stage_histogram": {"final_answer_payload_hash": 1},
                    "mismatch_question_ids": ["TBK-027"],
                    "mismatch_ordinals": [27],
                    "first_divergence_stage_set": ["final_answer_payload_hash"],
                    "reason_histogram": {"response_envelope_projection_delta": 1},
                }
            ],
        ),
        faz19_reference=faz19_reference,
    )

    assert payload["official_decision"] == "NO-GO - Current Authority Canonicalization Breach"
