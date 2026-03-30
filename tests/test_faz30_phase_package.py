from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "faz30"))


def _load_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_phase_package = _load_module("faz30_build_phase_package", "scripts/faz30/build_phase_package.py")
materialize_reference_pack = _load_module("faz30_materialize_reference_pack", "scripts/faz30/materialize_reference_pack.py")
faz30_lib = _load_module("faz30_lib_exact", "scripts/faz30/faz30_lib.py")

build_phase_payload = build_phase_package.build_phase_payload
build_materialization_payload = materialize_reference_pack.build_materialization_payload
FAIL_UNLOCALIZED = faz30_lib.FAIL_UNLOCALIZED
PASS_LOCALIZED = faz30_lib.PASS_LOCALIZED
PASS_RESTORED = faz30_lib.PASS_RESTORED


def _capture_truth(*, boundary_override: dict | None = None, spillover_override: dict | None = None, triplet_override: dict | None = None, retention_override: dict | None = None, truth_override: dict | None = None) -> dict:
    boundary = {
        "record_count": 166,
        "mismatch_count": 152,
        "faz1_50_mismatch_count": 14,
        "v2_95_mismatch_count": 52,
        "v3_170_mismatch_count": 86,
        "preprojection_hash_mismatch_count": 152,
        "raw_answer_hash_mismatch_count": 152,
        "response_envelope_hash_mismatch_count": 92,
        "runtime_error_count": 0,
        "first_break_stage_assigned_count": 152,
        "primary_reason_assigned_count": 152,
        "first_runtime_error_stage_assigned_count": 0,
        "runtime_primary_reason_assigned_count": 0,
        "unexplained_count": 0,
        "dominant_runtime_error_stage": "",
        "dominant_runtime_error_primary_reason": "",
    }
    spillover = {
        "record_count": 24,
        "mismatch_count": 5,
        "faz1_50_mismatch_count": 0,
        "v2_95_mismatch_count": 0,
        "v3_170_mismatch_count": 5,
        "preprojection_hash_mismatch_count": 5,
        "raw_answer_hash_mismatch_count": 5,
        "response_envelope_hash_mismatch_count": 2,
        "runtime_error_count": 0,
        "first_break_stage_assigned_count": 5,
        "primary_reason_assigned_count": 5,
        "first_runtime_error_stage_assigned_count": 0,
        "runtime_primary_reason_assigned_count": 0,
        "unexplained_count": 0,
        "dominant_runtime_error_stage": "",
        "dominant_runtime_error_primary_reason": "",
    }
    triplet = {
        "persisted_pii_redaction_pass": False,
        "tokenizer_backed_accounting_pass": False,
        "api_versioning_pass": False,
        "one_command_release_smoke_pass": False,
        "pii_leak_found": True,
        "token_accounting_fallback_found": True,
        "api_versioning_gap_found": True,
        "release_smoke_gap_found": True,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    retention = {
        "retained_after_family_eval": False,
        "retained_after_restart": False,
        "retained_after_restore": True,
        "answer_path_delta_reintroduced": True,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    truth = {
        "matches_faz28_truth": True,
        "matches_faz29_truth": False,
        "matches_neither_new_stable_truth": False,
    }

    if boundary_override:
        boundary.update(boundary_override)
    if spillover_override:
        spillover.update(spillover_override)
    if triplet_override:
        triplet.update(triplet_override)
    if retention_override:
        retention.update(retention_override)
    if truth_override:
        truth.update(truth_override)

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
        "boundary": boundary,
        "spillover": spillover,
        "failing_control_triplet": triplet,
        "retention_truth": retention,
        "truth_flags": truth,
    }


def _control_matrix(**overrides: object) -> dict:
    payload = {
        "rows": [
            {
                "control_set_id": "C8",
                "record_count": 190,
                "mismatch_count": 157,
                "runtime_error_count": 0,
                "preprojection_hash_mismatch_count": 157,
                "raw_answer_hash_mismatch_count": 157,
                "response_envelope_hash_mismatch_count": 94,
                "first_runtime_error_stage": "",
                "dominant_primary_reason": "",
                "capture_stability_match": True,
            }
        ],
        "minimal_failing_control_set": "none",
        "dominant_interaction_class": "boundary_pack_orchestration_runtime_mutation",
        "single_control_root_cause_found": False,
        "interaction_root_cause_found": False,
        "unexplained_count": 0,
    }
    payload.update(overrides)
    return payload


def test_materialized_payload_freezes_exact_contract() -> None:
    payload = build_materialization_payload()
    assert payload["reference_pack"]["candidate_id"] == "RC-O"
    assert payload["reference_pack"]["control_candidate"] == "RC-J"
    assert payload["contract"]["candidate_status"] == "frozen_failed_repair_candidate"
    assert len(payload["boundary_records"]) == 166
    assert len(payload["spillover_records"]) == 24
    assert len(payload["combined_records"]) == 190


def test_phase_payload_passes_when_truth_restored_to_faz28() -> None:
    materialized = build_materialization_payload()
    capture = _capture_truth()
    payload = build_phase_payload(
        materialized=materialized,
        capture_a=capture,
        capture_b=capture,
        control_matrix=_control_matrix(),
    )

    assert payload["official_decision"] == PASS_RESTORED
    assert payload["wp_statuses"]["WP-8"] == "PASS"
    current_truth_row = next(row for row in payload["lineage_rows"] if row["truth_class"] == "current_forensic_truth")
    assert current_truth_row["first_break_stage_assigned_count"] == 152


def test_phase_payload_maps_runtime_localization_to_pass_b() -> None:
    materialized = build_materialization_payload()
    capture = _capture_truth(
        boundary_override={
            "mismatch_count": 166,
            "preprojection_hash_mismatch_count": 0,
            "raw_answer_hash_mismatch_count": 0,
            "response_envelope_hash_mismatch_count": 0,
            "runtime_error_count": 166,
            "first_break_stage_assigned_count": 0,
            "primary_reason_assigned_count": 0,
            "first_runtime_error_stage_assigned_count": 166,
            "runtime_primary_reason_assigned_count": 166,
        },
        spillover_override={
            "mismatch_count": 24,
            "preprojection_hash_mismatch_count": 0,
            "raw_answer_hash_mismatch_count": 0,
            "response_envelope_hash_mismatch_count": 0,
            "runtime_error_count": 24,
            "first_break_stage_assigned_count": 0,
            "primary_reason_assigned_count": 0,
            "first_runtime_error_stage_assigned_count": 24,
            "runtime_primary_reason_assigned_count": 24,
        },
        truth_override={
            "matches_faz28_truth": False,
            "matches_faz29_truth": True,
            "matches_neither_new_stable_truth": False,
        },
    )
    payload = build_phase_payload(
        materialized=materialized,
        capture_a=capture,
        capture_b=capture,
        control_matrix=_control_matrix(
            minimal_failing_control_set="C8",
            dominant_interaction_class="multi_control_interaction_runtime_mutation",
            interaction_root_cause_found=True,
        ),
    )

    assert payload["official_decision"] == PASS_LOCALIZED
    assert payload["wp_statuses"]["WP-6"] == "PASS"


def test_phase_payload_allows_localized_decision_with_unstable_twin_capture() -> None:
    materialized = build_materialization_payload()
    capture_a = _capture_truth(
        boundary_override={
            "mismatch_count": 152,
            "response_envelope_hash_mismatch_count": 86,
        },
        spillover_override={
            "mismatch_count": 4,
            "response_envelope_hash_mismatch_count": 1,
        },
        truth_override={
            "matches_faz28_truth": False,
            "matches_faz29_truth": False,
            "matches_neither_new_stable_truth": True,
        },
    )
    capture_b = _capture_truth(
        boundary_override={
            "mismatch_count": 149,
            "v2_95_mismatch_count": 50,
            "v3_170_mismatch_count": 85,
            "preprojection_hash_mismatch_count": 149,
            "raw_answer_hash_mismatch_count": 149,
            "response_envelope_hash_mismatch_count": 90,
            "first_break_stage_assigned_count": 149,
            "primary_reason_assigned_count": 149,
        },
        spillover_override={
            "mismatch_count": 3,
            "v2_95_mismatch_count": 1,
            "v3_170_mismatch_count": 2,
            "preprojection_hash_mismatch_count": 3,
            "raw_answer_hash_mismatch_count": 3,
            "response_envelope_hash_mismatch_count": 1,
            "first_break_stage_assigned_count": 3,
            "primary_reason_assigned_count": 3,
        },
        truth_override={
            "matches_faz28_truth": False,
            "matches_faz29_truth": False,
            "matches_neither_new_stable_truth": True,
        },
    )
    payload = build_phase_payload(
        materialized=materialized,
        capture_a=capture_a,
        capture_b=capture_b,
        control_matrix=_control_matrix(
            minimal_failing_control_set="none",
            dominant_interaction_class="boundary_pack_orchestration_runtime_mutation",
            single_control_root_cause_found=False,
            interaction_root_cause_found=False,
            unexplained_count=0,
        ),
    )

    assert payload["wp_statuses"]["WP-4"] == "PASS"
    assert payload["wp_statuses"]["WP-5"] == "PASS"
    assert payload["official_decision"] == PASS_LOCALIZED


def test_phase_payload_fails_when_truth_flags_are_not_one_hot() -> None:
    materialized = build_materialization_payload()
    capture = _capture_truth(
        truth_override={
            "matches_faz28_truth": False,
            "matches_faz29_truth": False,
            "matches_neither_new_stable_truth": False,
        }
    )
    payload = build_phase_payload(
        materialized=materialized,
        capture_a=capture,
        capture_b=capture,
        control_matrix=_control_matrix(),
    )

    assert payload["official_decision"] == FAIL_UNLOCALIZED
    assert payload["wp_statuses"]["WP-8"] == "FAIL"
