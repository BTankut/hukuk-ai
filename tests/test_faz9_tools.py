from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "faz9"))

import build_rc_j_manifest as manifest_builder  # noqa: E402
import build_tbk005_witness_forensics as witness_builder  # noqa: E402


def _question(question_id: str, stage_hashes: dict[str, str]) -> dict:
    return {
        "question_id": question_id,
        "trace": {
            "parity_trace": {
                "stages": [
                    {"stage": stage, "hash": stage_hash, "payload": {stage: stage_hash}}
                    for stage, stage_hash in stage_hashes.items()
                ]
            }
        },
    }


def test_build_rc_j_manifest_keeps_empty_answer_path_delta(tmp_path: Path) -> None:
    reference_manifest = {
        "candidate_id": "rc-g-faz6-accepted-20260323",
        "base_model_id": "Qwen/test",
        "adapter_id": "adapter",
        "claim_binding_version": "v3",
        "final_mode_mapping_version": "v3",
        "source_locking_version": "v1",
        "citation_normalization_version": "v1",
        "law_scope_gate_version": "v2",
        "schema_contract_version": "structured-answer-contract-v1",
        "family_reports": [{"family": "faz1-50"}],
    }
    output_path = tmp_path / "manifest.json"
    manifest = manifest_builder.build_manifest(
        reference_manifest=reference_manifest,
        candidate_id="rc-j-20260324",
        checkpoint_ref="rc-j-2026-03-24",
        git_commit="deadbeef",
        output_path=output_path,
        allowed_diff_surface=["api-gateway/src/routers/chat.py"],
        allowed_diff_surface_notes=["model request payload canonicalization"],
    )

    assert manifest["answer_path_delta"] == []
    assert manifest["runner_mode"] == "rc_j_model_visible_surface_parity_safe"
    assert output_path.exists()


def test_witness_forensics_localizes_raw_answer_object_drift() -> None:
    reference_report = {
        "report_meta": {"eval_family": "faz1-50-witness", "checkpoint_ref": "rc-g"},
        "per_question": [
            _question(
                "TBK-005",
                {
                    "raw_input_request": "a",
                    "normalized_request": "b",
                    "auth_enriched_request": "c",
                    "session_enriched_request": "d",
                    "retrieval_input_payload": "e",
                    "retrieved_source_id_ordered_list": "f",
                    "assembly_payload": "g",
                    "model_request_payload": "h",
                    "generation_contract": "i",
                    "raw_answer_object": "j",
                    "response_envelope": "k",
                    "eval_client_parsed_object": "l",
                    "normalized_parity_object": "m",
                },
            )
        ],
    }
    candidate_report = {
        "report_meta": {"eval_family": "faz1-50-witness", "checkpoint_ref": "rc-i"},
        "per_question": [
            _question(
                "TBK-005",
                {
                    "raw_input_request": "a",
                    "normalized_request": "b",
                    "auth_enriched_request": "c",
                    "session_enriched_request": "d",
                    "retrieval_input_payload": "e",
                    "retrieved_source_id_ordered_list": "f",
                    "assembly_payload": "g",
                    "model_request_payload": "h",
                    "generation_contract": "i",
                    "raw_answer_object": "DIFF",
                    "response_envelope": "k2",
                    "eval_client_parsed_object": "l2",
                    "normalized_parity_object": "m2",
                },
            )
        ],
    }

    summary = witness_builder.build_witness_forensics(
        reference_report=reference_report,
        candidate_report=candidate_report,
        question_id="TBK-005",
    )

    assert summary["unexplained_count"] == 0
    assert summary["first_divergence_stage"] == "raw_answer_object"
    assert summary["primary_reason"] == "raw_answer_object_hash_drift"
