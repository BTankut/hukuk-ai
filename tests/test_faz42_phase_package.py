from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "faz42"))


def _load_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_phase_package = _load_module("faz42_build_phase_package", "scripts/faz42/build_phase_package.py")
faz42_lib = _load_module("faz42_lib_exact", "scripts/faz42/faz42_lib.py")

build_phase_payload = build_phase_package.build_phase_payload
PASS_DECISION = faz42_lib.PASS_DECISION
FAIL_AUTH_DECISION = faz42_lib.FAIL_AUTH_DECISION
REFERENCE_DOCS = faz42_lib.REFERENCE_DOCS
load_text = faz42_lib.load_text


def _reference_texts() -> dict[str, str]:
    return {key: load_text(path) for key, path in REFERENCE_DOCS.items()}


def test_phase_payload_passes_with_exact_process_isolated_contract() -> None:
    payload = build_phase_payload(_reference_texts())
    assert payload["reconciliation"]["official_decision"] == PASS_DECISION
    assert payload["wp_statuses"]["WP-1"] == "PASS"
    assert payload["wp_statuses"]["WP-9"] == "PASS"
    assert payload["build_contract"]["candidate_id"] == "RC-R"
    assert payload["full_family_parity"]["preprojection_hash_mismatch_count"] == 0
    assert payload["targeted_acceptance"]["tokenizer_usage_total"] > 0.0


def test_phase_payload_fails_when_reference_pack_loses_required_marker() -> None:
    texts = _reference_texts()
    texts["faz41"] = texts["faz41"].replace(
        "PASS - Post-RC-Q Steering Re-Entered Under Canonical Current Authority",
        "PASS - Post-RC-Q Steering Re-Entry Mutated",
    )
    payload = build_phase_payload(texts)
    assert payload["reconciliation"]["official_decision"] == FAIL_AUTH_DECISION
    assert payload["wp_statuses"]["WP-1"] == "FAIL"
    assert payload["reference_pack"]["reference_pack_contradiction_count"] == 1
