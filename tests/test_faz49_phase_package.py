from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "faz49"))


def _load_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_phase_package = _load_module("faz49_build_phase_package", "scripts/faz49/build_phase_package.py")
faz49_lib = _load_module("faz49_lib_exact", "scripts/faz49/faz49_lib.py")

build_phase_payload = build_phase_package.build_phase_payload
PASS_DECISION = faz49_lib.PASS_DECISION
FAIL_DECISION = faz49_lib.FAIL_DECISION
REFERENCE_DOCS = faz49_lib.REFERENCE_DOCS
load_text = faz49_lib.load_text


def _reference_texts() -> dict[str, str]:
    return {key: load_text(path) for key, path in REFERENCE_DOCS.items()}


def test_phase_payload_passes_with_exact_controlled_real_world_validation_contract() -> None:
    payload = build_phase_payload(_reference_texts())

    assert payload["reconciliation"]["official_decision"] == PASS_DECISION
    assert payload["wp_statuses"]["WP-7"] == "PASS"
    assert payload["reconciliation"]["total_session_count"] == 30
    assert payload["human_review_summary"]["supported_source_correct_count"] == 24
    assert payload["human_review_summary"]["citation_readable_count"] == 25
    assert payload["human_review_summary"]["answer_usable_count"] == 23
    assert payload["human_review_summary"]["refusal_correct_count"] == 5
    assert payload["human_review_summary"]["human_escalation_needed_count"] == 2
    assert payload["human_review_summary"]["total_rejected_session_count"] == 2
    assert payload["shadow_summary"]["preprojection_hash_mismatch_count"] == 0
    assert payload["post_run_parity"]["v3_170_mismatch_count"] == 0


def test_phase_payload_fails_when_any_model_visible_delta_is_introduced() -> None:
    payload = build_phase_payload(
        _reference_texts(),
        session_overrides={
            "faz49-bt-session-001": {
                "preprojection_hash_match": False,
            }
        },
    )

    assert payload["reconciliation"]["official_decision"] == FAIL_DECISION
    assert payload["wp_statuses"]["WP-5"] == "FAIL"
    assert payload["reconciliation"]["hard_fail_triggered"] is True
    assert payload["shadow_summary"]["preprojection_hash_mismatch_count"] == 1
