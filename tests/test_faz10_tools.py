from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "faz10"))

import build_rc_k_manifest as manifest_builder  # noqa: E402
import faz10_lib as faz10_lib  # noqa: E402


def test_build_rc_k_manifest_keeps_empty_answer_path_delta(tmp_path: Path) -> None:
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
        "family_reports": [{"family": "v3-170"}],
    }
    diagnostic_manifest = {
        "candidate_id": "rc-j-20260324",
        "answer_path_identity": {
            "claim_binding_version": "v3",
            "final_mode_mapping_version": "v3",
            "source_locking_version": "v1",
            "citation_normalization_version": "v1",
            "law_scope_gate_version": "v2",
            "trace_contract_version": "faz10-v3-runtime-parity-trace-schema-v1",
            "schema_contract_version": "structured-answer-contract-v1",
        },
    }
    output_path = tmp_path / "manifest.json"
    manifest = manifest_builder.build_manifest(
        reference_manifest=reference_manifest,
        diagnostic_manifest=diagnostic_manifest,
        candidate_id="rc-k-20260324",
        checkpoint_ref="rc-k-2026-03-24",
        git_commit="deadbeef",
        output_path=output_path,
        allowed_diff_surface=["api-gateway/src/llm/client.py"],
        allowed_diff_surface_notes=["deterministic generation runtime topology"],
    )

    assert manifest["answer_path_delta"] == []
    assert manifest["runner_mode"] == "rc_k_v3_preprojection_parity_safe"
    assert manifest["diagnostic_source_candidate_id"] == "rc-j-20260324"
    assert output_path.exists()


def test_faz10_runtime_trace_stage_order_is_frozen() -> None:
    assert faz10_lib.TRACE_STAGE_ORDER == [
        "normalized_request",
        "model_request_payload",
        "generation_contract",
        "worker_assignment_tuple",
        "session_namespace_after_payload_freeze",
        "cache_namespace_or_cache_key",
        "generation_start_ordinal",
        "first_token_id_hash",
        "raw_token_stream_hash",
        "raw_answer_object",
        "response_envelope",
        "eval_client_parsed_object",
        "normalized_parity_object",
    ]


def test_primary_reason_mapping_keeps_planner_reason_set() -> None:
    assert faz10_lib.PRIMARY_REASONS["L0"] == "raw_generation_nondeterminism"
    assert faz10_lib.PRIMARY_REASONS["L7"] == "generation_cache_namespace_drift"
