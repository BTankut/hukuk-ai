from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "faz44"))


def _load_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_phase_package = _load_module("faz44_build_phase_package", "scripts/faz44/build_phase_package.py")
faz44_lib = _load_module("faz44_lib_exact", "scripts/faz44/faz44_lib.py")

build_phase_payload = build_phase_package.build_phase_payload
PASS_DECISION = faz44_lib.PASS_DECISION
FAIL_DECISION = faz44_lib.FAIL_DECISION
REFERENCE_DOCS = faz44_lib.REFERENCE_DOCS
load_text = faz44_lib.load_text


def _reference_texts() -> dict[str, str]:
    return {key: load_text(path) for key, path in REFERENCE_DOCS.items()}


def test_phase_payload_passes_with_exact_narrow_internal_pilot_contract() -> None:
    payload = build_phase_payload(_reference_texts())
    assert payload["reconciliation"]["official_decision"] == PASS_DECISION
    assert payload["wp_statuses"]["WP-1"] == "PASS"
    assert payload["wp_statuses"]["WP-6"] == "PASS"
    assert payload["steering_contract"]["pilot_candidate_id"] == "RC-R"
    assert payload["steering_contract"]["pilot_start_authorized_in_this_phase"] is False
    assert payload["governance_boundary"]["internal_named_allowlist_only"] is True
    assert payload["observation_and_rollback_readiness"]["rollback_target"] == "RC-G canonical answer lane"


def test_phase_payload_fails_when_reference_pack_loses_required_marker() -> None:
    texts = _reference_texts()
    texts["faz43"] = texts["faz43"].replace(
        "PASS - Cutover Readiness Closed Under Canonical Current Authority",
        "PASS - Cutover Readiness Mutated",
    )
    payload = build_phase_payload(texts)
    assert payload["reconciliation"]["official_decision"] == FAIL_DECISION
    assert payload["wp_statuses"]["WP-1"] == "FAIL"
    assert payload["reference_pack"]["reference_pack_contradiction_count"] == 1
