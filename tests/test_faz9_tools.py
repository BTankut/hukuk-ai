from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "faz9"))

import build_rc_j_manifest as manifest_builder  # noqa: E402
import build_preprojection_gate as gate_builder  # noqa: E402
import build_sentinel12_pack as sentinel_builder  # noqa: E402
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


def test_witness_forensics_classifies_raw_generation_nondeterminism() -> None:
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
    assert summary["primary_reason"] == "raw_generation_nondeterminism"


def test_witness_forensics_classifies_missing_candidate_trace_as_runtime_error() -> None:
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
        "per_question": [{"question_id": "TBK-005", "trace": {}}],
    }

    summary = witness_builder.build_witness_forensics(
        reference_report=reference_report,
        candidate_report=candidate_report,
        question_id="TBK-005",
    )

    assert summary["unexplained_count"] == 0
    assert summary["first_divergence_stage"] == "model_request_payload"
    assert summary["primary_reason"] == "parity_runtime_error"


def test_build_preprojection_gate_counts_stage_mismatch_and_runtime_error() -> None:
    reference_report = {
        "report_meta": {"eval_family": "faz1-50", "checkpoint_ref": "rc-g"},
        "per_question": [
            _question(
                "TBK-005",
                {
                    "normalized_request": "a",
                    "model_request_payload": "b",
                    "generation_contract": "c",
                    "raw_answer_object": "d",
                },
            ),
            _question(
                "TBK-006",
                {
                    "normalized_request": "e",
                    "model_request_payload": "f",
                    "generation_contract": "g",
                    "raw_answer_object": "h",
                },
            ),
        ],
    }
    reference_report["per_question"][0]["trace"]["parity_trace"]["preprojection_hash"] = "d"
    reference_report["per_question"][1]["trace"]["parity_trace"]["preprojection_hash"] = "h"

    candidate_report = {
        "report_meta": {"eval_family": "faz1-50", "checkpoint_ref": "rc-j"},
        "per_question": [
            _question(
                "TBK-005",
                {
                    "normalized_request": "a",
                    "model_request_payload": "DIFF",
                    "generation_contract": "c",
                    "raw_answer_object": "RAW",
                },
            ),
            {"question_id": "TBK-006", "trace": {}},
        ],
    }
    candidate_report["per_question"][0]["trace"]["parity_trace"]["preprojection_hash"] = "RAW"

    summary = gate_builder.build_gate(reference_report, candidate_report)

    assert summary["model_request_payload_hash_mismatch_count"] == 1
    assert summary["raw_answer_hash_mismatch_count"] == 1
    assert summary["preprojection_hash_mismatch_count"] == 1
    assert summary["parity_runtime_error_count"] == 1


def test_build_sentinel12_pack_applies_tbk005_replacement_rule() -> None:
    frontier = {
        "rows": [
            {"family": "faz1-50", "question_id": "TBK-001"},
            {"family": "faz1-50", "question_id": "TBK-002"},
            {"family": "faz1-50", "question_id": "TBK-003"},
            {"family": "faz1-50", "question_id": "TBK-004"},
            {"family": "faz1-50", "question_id": "TBK-005"},
            {"family": "v2-95", "question_id": "HAL-001"},
            {"family": "v2-95", "question_id": "HAL-002"},
            {"family": "v2-95", "question_id": "HAL-003"},
            {"family": "v2-95", "question_id": "HAL-004"},
            {"family": "v3-170", "question_id": "HAL-001"},
            {"family": "v3-170", "question_id": "HAL-002"},
            {"family": "v3-170", "question_id": "HAL-003"},
            {"family": "v3-170", "question_id": "HAL-004"},
        ]
    }
    faz1_bank = {f"TBK-00{i}": {"id": f"TBK-00{i}"} for i in range(1, 6)}
    v2_bank = {f"HAL-00{i}": {"id": f"HAL-00{i}"} for i in range(1, 5)}
    v3_bank = {f"HAL-00{i}": {"id": f"HAL-00{i}"} for i in range(1, 5)}

    summary = sentinel_builder.build_selection(
        frontier=frontier,
        faz1_bank=faz1_bank,
        v2_bank=v2_bank,
        v3_bank=v3_bank,
    )

    assert summary["selected_ids_by_family"]["faz1-50"] == ["TBK-001", "TBK-002", "TBK-003", "TBK-005"]
    assert summary["selected_ids_by_family"]["v2-95"] == ["HAL-001", "HAL-002", "HAL-003", "HAL-004"]
    assert len({item["id"] for item in summary["questions"]}) == 12


def test_build_preprojection_gate_preserves_duplicate_question_ids_by_occurrence() -> None:
    reference_report = {
        "report_meta": {"eval_family": "sentinel12", "checkpoint_ref": "rc-g"},
        "per_question": [
            _question("HAL-001", {"normalized_request": "a", "model_request_payload": "b", "generation_contract": "c", "raw_answer_object": "d"}),
            _question("HAL-001", {"normalized_request": "e", "model_request_payload": "f", "generation_contract": "g", "raw_answer_object": "h"}),
        ],
    }
    reference_report["per_question"][0]["trace"]["parity_trace"]["preprojection_hash"] = "d"
    reference_report["per_question"][1]["trace"]["parity_trace"]["preprojection_hash"] = "h"

    candidate_report = {
        "report_meta": {"eval_family": "sentinel12", "checkpoint_ref": "rc-j"},
        "per_question": [
            _question("HAL-001", {"normalized_request": "a", "model_request_payload": "b", "generation_contract": "c", "raw_answer_object": "d"}),
            _question("HAL-001", {"normalized_request": "e", "model_request_payload": "DIFF", "generation_contract": "g", "raw_answer_object": "h"}),
        ],
    }
    candidate_report["per_question"][0]["trace"]["parity_trace"]["preprojection_hash"] = "d"
    candidate_report["per_question"][1]["trace"]["parity_trace"]["preprojection_hash"] = "h"

    summary = gate_builder.build_gate(reference_report, candidate_report)

    assert summary["question_count"] == 2
    assert summary["compared_question_count"] == 2
    assert summary["model_request_payload_hash_mismatch_count"] == 1
