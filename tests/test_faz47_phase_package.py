from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "faz47"))


def _load_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_phase_package = _load_module("faz47_build_phase_package", "scripts/faz47/build_phase_package.py")
faz47_lib = _load_module("faz47_lib_exact", "scripts/faz47/faz47_lib.py")

build_phase_payload = build_phase_package.build_phase_payload
PASS_DECISION = faz47_lib.PASS_DECISION
FAIL_DECISION = faz47_lib.FAIL_DECISION
REFERENCE_DOCS = faz47_lib.REFERENCE_DOCS
load_text = faz47_lib.load_text


def _reference_texts() -> dict[str, str]:
    return {key: load_text(path) for key, path in REFERENCE_DOCS.items()}


def test_phase_payload_passes_with_exact_postpilot_closure_and_next_track_contract() -> None:
    payload = build_phase_payload(_reference_texts())
    assert payload["reconciliation"]["official_decision"] == PASS_DECISION
    assert payload["wp_statuses"]["WP-1"] == "PASS"
    assert payload["wp_statuses"]["WP-6"] == "PASS"
    assert payload["postpilot_closure"]["planned_session_count"] == 9
    assert payload["legacy_queue_normalization"]["active_internal_pilot_candidate"] == "NONE"
    assert payload["rc_s_next_track"]["next_candidate_id"] == "RC-S"
    assert payload["rc_s_source_set"]["metadata_contract_exact"] is True


def test_phase_payload_fails_when_reference_pack_loses_required_marker() -> None:
    texts = _reference_texts()
    texts["faz46"] = texts["faz46"].replace(
        "PASS - RC-R Narrow Internal Pilot Executed Under Canonical Current Authority",
        "PASS - RC-R Narrow Internal Pilot Mutated",
    )
    payload = build_phase_payload(texts)
    assert payload["reconciliation"]["official_decision"] == FAIL_DECISION
    assert payload["wp_statuses"]["WP-1"] == "FAIL"
    assert payload["reference_pack"]["reference_pack_contradiction_count"] == 1
