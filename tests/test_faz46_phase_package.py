from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "faz46"))


def _load_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_phase_package = _load_module("faz46_build_phase_package", "scripts/faz46/build_phase_package.py")
faz46_lib = _load_module("faz46_lib_exact", "scripts/faz46/faz46_lib.py")

build_phase_payload = build_phase_package.build_phase_payload
PASS_DECISION = faz46_lib.PASS_DECISION
ADMISSION_FAIL_DECISION = faz46_lib.ADMISSION_FAIL_DECISION
REFERENCE_DOCS = faz46_lib.REFERENCE_DOCS
load_text = faz46_lib.load_text


def _reference_texts() -> dict[str, str]:
    return {key: load_text(path) for key, path in REFERENCE_DOCS.items()}


def test_phase_payload_passes_with_exact_narrow_internal_pilot_execution_contract() -> None:
    payload = build_phase_payload(_reference_texts())
    assert payload["reconciliation"]["official_decision"] == PASS_DECISION
    assert payload["wp_statuses"]["WP-7"] == "PASS"
    assert payload["admitted_operator_freeze"]["selected_operator_count"] == 3
    assert len(payload["session_rows"]) == 9
    assert payload["session_aggregates"]["session_success_count"] == 9
    assert payload["session_rows"][0]["session_id"] == "faz46-rc-r-session-001"
    assert payload["session_rows"][-1]["session_id"] == "faz46-rc-r-session-009"


def test_phase_payload_fails_when_admission_is_not_ready() -> None:
    payload = build_phase_payload(_reference_texts(), admitted_operator_ids=["internal_operator_001", "internal_operator_002"])
    assert payload["reconciliation"]["official_decision"] == ADMISSION_FAIL_DECISION
    assert payload["wp_statuses"]["WP-3"] == "FAIL"
    assert payload["reconciliation"]["selected_operator_count"] == 2
    assert payload["reconciliation"]["planned_session_count"] == 0
