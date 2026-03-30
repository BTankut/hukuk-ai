from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "faz33"))


def _load_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_phase_package = _load_module("faz33_build_phase_package", "scripts/faz33/build_phase_package.py")
faz33_lib = _load_module("faz33_lib_exact", "scripts/faz33/faz33_lib.py")

build_phase_payload = build_phase_package.build_phase_payload
PASS_DECISION = faz33_lib.PASS_DECISION
FAIL_DECISION = faz33_lib.FAIL_DECISION
REFERENCE_DOCS = faz33_lib.REFERENCE_DOCS
load_text = faz33_lib.load_text


def _reference_texts() -> dict[str, str]:
    return {key: load_text(path) for key, path in REFERENCE_DOCS.items()}


def test_phase_payload_passes_with_exact_steering_contract() -> None:
    payload = build_phase_payload(_reference_texts())
    assert payload["reconciliation"]["official_decision"] == PASS_DECISION
    assert payload["wp_statuses"]["WP-1"] == "PASS"
    assert payload["wp_statuses"]["WP-5"] == "PASS"
    assert payload["legacy_normalization"]["active_quality_reference"] == "RC-G"
    assert payload["next_phase_contract"]["next_candidate_id"] == "RC-P"
    assert payload["next_phase_contract"]["allowed_diff_surface"] == "non_model_visible_release_controls_perimeter_only"
    assert payload["next_phase_contract"]["answer_path_delta_allowed"] is False


def test_phase_payload_fails_when_reference_chain_breaks() -> None:
    texts = _reference_texts()
    texts["faz32"] = texts["faz32"].replace(
        "PASS - RC-O Discard Archived Under Canonical Current Authority",
        "PASS - RC-O Discard Archived Mutated",
    )
    payload = build_phase_payload(texts)
    assert payload["reconciliation"]["official_decision"] == FAIL_DECISION
    assert payload["wp_statuses"]["WP-1"] == "FAIL"
    assert payload["wp_statuses"]["WP-5"] == "FAIL"
    assert payload["reference_pack"]["reference_pack_contradiction_count"] == 1
