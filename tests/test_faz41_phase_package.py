from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "faz41"))


def _load_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_phase_package = _load_module("faz41_build_phase_package", "scripts/faz41/build_phase_package.py")
faz41_lib = _load_module("faz41_lib_exact", "scripts/faz41/faz41_lib.py")

build_phase_payload = build_phase_package.build_phase_payload
PASS_DECISION = faz41_lib.PASS_DECISION
FAIL_DECISION = faz41_lib.FAIL_DECISION
REFERENCE_DOCS = faz41_lib.REFERENCE_DOCS
load_text = faz41_lib.load_text


def _reference_texts() -> dict[str, str]:
    return {key: load_text(path) for key, path in REFERENCE_DOCS.items()}


def test_phase_payload_passes_with_exact_steering_reentry_contract() -> None:
    payload = build_phase_payload(_reference_texts())
    assert payload["reconciliation"]["official_decision"] == PASS_DECISION
    assert payload["wp_statuses"]["WP-1"] == "PASS"
    assert payload["wp_statuses"]["WP-6"] == "PASS"
    assert payload["next_phase_contract"]["next_candidate_id"] == "RC-R"
    assert payload["queue_normalization"]["archived_candidate_set"] == ["RC-M", "RC-O", "RC-Q"]
    assert payload["topology_rows"][0]["candidate_id"] == "RC-G"


def test_phase_payload_fails_when_reference_pack_loses_required_marker() -> None:
    texts = _reference_texts()
    texts["faz40"] = texts["faz40"].replace(
        "PASS - RC-Q Discard Archived Under Canonical Current Authority",
        "PASS - RC-Q Discard Archive Mutated",
    )
    payload = build_phase_payload(texts)
    assert payload["reconciliation"]["official_decision"] == FAIL_DECISION
    assert payload["wp_statuses"]["WP-1"] == "FAIL"
    assert payload["wp_statuses"]["WP-6"] == "FAIL"
    assert payload["reference_pack"]["reference_pack_contradiction_count"] == 1
