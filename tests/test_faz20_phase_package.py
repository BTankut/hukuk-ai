from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str((Path(__file__).resolve().parents[1] / "scripts/faz20")))

from build_phase_package import build_phase_payload  # type: ignore


def test_faz20_phase_payload_passes_when_replay19_matches_and_only_h10_h11_drift_remains() -> None:
    reference_packs = {
        "faz13": {
            "reference_pack_integrity_pass": True,
            "reference_pack_contradiction_count": 0,
            "families": [
                {
                    "family_name": "faz1-50",
                    "mismatch_count": 0,
                    "runtime_error_count": 0,
                    "family_metric_delta_zero": True,
                    "mismatch_stage_histogram": {},
                    "mismatch_question_ids": [],
                    "mismatch_ordinals": [],
                    "first_divergence_stage_set": [],
                    "reason_histogram": {},
                    "authoritative_summary_hash": "a",
                },
                {
                    "family_name": "v2-95",
                    "mismatch_count": 0,
                    "runtime_error_count": 0,
                    "family_metric_delta_zero": True,
                    "mismatch_stage_histogram": {},
                    "mismatch_question_ids": [],
                    "mismatch_ordinals": [],
                    "first_divergence_stage_set": [],
                    "reason_histogram": {},
                    "authoritative_summary_hash": "b",
                },
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
                    "authoritative_summary_hash": "c",
                },
            ],
        },
        "faz18": {
            "reference_pack_integrity_pass": True,
            "reference_pack_contradiction_count": 0,
            "families": [
                {
                    "family_name": "faz1-50",
                    "mismatch_count": 1,
                    "runtime_error_count": 0,
                    "family_metric_delta_zero": True,
                    "mismatch_stage_histogram": {"response_envelope_hash": 1},
                    "mismatch_question_ids": ["TBK-027"],
                    "mismatch_ordinals": [27],
                    "first_divergence_stage_set": ["response_envelope_hash"],
                    "reason_histogram": {"response_envelope_projection_delta": 1},
                    "authoritative_summary_hash": "d",
                },
                {
                    "family_name": "v2-95",
                    "mismatch_count": 0,
                    "runtime_error_count": 0,
                    "family_metric_delta_zero": True,
                    "mismatch_stage_histogram": {},
                    "mismatch_question_ids": [],
                    "mismatch_ordinals": [],
                    "first_divergence_stage_set": [],
                    "reason_histogram": {},
                    "authoritative_summary_hash": "e",
                },
                {
                    "family_name": "v3-170",
                    "mismatch_count": 0,
                    "runtime_error_count": 0,
                    "family_metric_delta_zero": True,
                    "mismatch_stage_histogram": {},
                    "mismatch_question_ids": [],
                    "mismatch_ordinals": [],
                    "first_divergence_stage_set": [],
                    "reason_histogram": {},
                    "authoritative_summary_hash": "f",
                },
            ],
        },
        "faz19": {
            "reference_pack_integrity_pass": True,
            "reference_pack_contradiction_count": 0,
            "families": [
                {
                    "family_name": family,
                    "mismatch_count": 0,
                    "runtime_error_count": 0,
                    "family_metric_delta_zero": True,
                    "mismatch_stage_histogram": {},
                    "mismatch_question_ids": [],
                    "mismatch_ordinals": [],
                    "first_divergence_stage_set": [],
                    "reason_histogram": {},
                    "authoritative_summary_hash": family,
                }
                for family in ("faz1-50", "v2-95", "v3-170")
            ],
        },
    }
    lineage_matrix = {
        "rows": [
            {"reference_name": name, "surface_breach_stage_set": [], "recording_only_stage_set": []}
            for name in ("faz13", "faz18", "faz19")
        ]
    }
    replay_payloads = {
        "faz13": {
            "reference_match": False,
            "runtime_error_count": 0,
            "family_metric_delta_zero": True,
            "breach_in_h0_h9": False,
            "first_divergence_stage": "H10",
            "primary_reason": "authority_summary_materialization_delta",
            "families": [
                {
                    "family_name": "faz1-50",
                    "mismatch_count": 0,
                    "runtime_error_count": 0,
                    "family_metric_delta_zero": True,
                    "mismatch_stage_histogram": {},
                    "mismatch_question_ids": [],
                    "mismatch_ordinals": [],
                    "reason_histogram": {},
                },
                {
                    "family_name": "v2-95",
                    "mismatch_count": 0,
                    "runtime_error_count": 0,
                    "family_metric_delta_zero": True,
                    "mismatch_stage_histogram": {},
                    "mismatch_question_ids": [],
                    "mismatch_ordinals": [],
                    "reason_histogram": {},
                },
                {
                    "family_name": "v3-170",
                    "mismatch_count": 0,
                    "runtime_error_count": 0,
                    "family_metric_delta_zero": True,
                    "mismatch_stage_histogram": {},
                    "mismatch_question_ids": [],
                    "mismatch_ordinals": [],
                    "reason_histogram": {},
                },
            ],
            "comparison_rows": [
                {"family_name": "faz1-50", "match": True},
                {"family_name": "v2-95", "match": True},
                {"family_name": "v3-170", "match": False},
            ],
        },
        "faz18": {
            "reference_match": False,
            "runtime_error_count": 0,
            "family_metric_delta_zero": True,
            "breach_in_h0_h9": False,
            "first_divergence_stage": "H10",
            "primary_reason": "authority_summary_materialization_delta",
            "families": [
                {
                    "family_name": "faz1-50",
                    "mismatch_count": 0,
                    "runtime_error_count": 0,
                    "family_metric_delta_zero": True,
                    "mismatch_stage_histogram": {},
                    "mismatch_question_ids": [],
                    "mismatch_ordinals": [],
                    "reason_histogram": {},
                },
                {
                    "family_name": "v2-95",
                    "mismatch_count": 0,
                    "runtime_error_count": 0,
                    "family_metric_delta_zero": True,
                    "mismatch_stage_histogram": {},
                    "mismatch_question_ids": [],
                    "mismatch_ordinals": [],
                    "reason_histogram": {},
                },
                {
                    "family_name": "v3-170",
                    "mismatch_count": 0,
                    "runtime_error_count": 0,
                    "family_metric_delta_zero": True,
                    "mismatch_stage_histogram": {},
                    "mismatch_question_ids": [],
                    "mismatch_ordinals": [],
                    "reason_histogram": {},
                },
            ],
            "comparison_rows": [
                {"family_name": "faz1-50", "match": False},
                {"family_name": "v2-95", "match": True},
                {"family_name": "v3-170", "match": True},
            ],
        },
        "faz19": {
            "reference_match": True,
            "runtime_error_count": 0,
            "family_metric_delta_zero": True,
            "breach_in_h0_h9": False,
            "first_divergence_stage": None,
            "primary_reason": "stable_current_truth_canonical",
            "families": [
                {
                    "family_name": family,
                    "mismatch_count": 0,
                    "runtime_error_count": 0,
                    "family_metric_delta_zero": True,
                    "mismatch_stage_histogram": {},
                    "mismatch_question_ids": [],
                    "mismatch_ordinals": [],
                    "reason_histogram": {},
                }
                for family in ("faz1-50", "v2-95", "v3-170")
            ],
            "comparison_rows": [
                {"family_name": "faz1-50", "match": True},
                {"family_name": "v2-95", "match": True},
                {"family_name": "v3-170", "match": True},
            ],
        },
    }

    payload = build_phase_payload(
        reference_packs=reference_packs,
        lineage_matrix=lineage_matrix,
        replay_payloads=replay_payloads,
    )

    assert payload["official_decision"] == "PASS - Current Authority Canonicalization Authorized"
    assert payload["next_official_work"] == "current authority canonicalization gate"
