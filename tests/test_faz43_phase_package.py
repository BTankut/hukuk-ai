from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "faz43"))


def _load_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_phase_package = _load_module("faz43_build_phase_package", "scripts/faz43/build_phase_package.py")
faz43_lib = _load_module("faz43_lib_exact", "scripts/faz43/faz43_lib.py")

build_phase_payload = build_phase_package.build_phase_payload
PASS_DECISION = faz43_lib.PASS_DECISION
FAIL_DECISION = faz43_lib.FAIL_DECISION
REFERENCE_DOCS = faz43_lib.REFERENCE_DOCS
load_text = faz43_lib.load_text


def _reference_texts() -> dict[str, str]:
    return {key: load_text(path) for key, path in REFERENCE_DOCS.items()}


def test_phase_payload_passes_with_exact_cutover_readiness_contract() -> None:
    payload = build_phase_payload(_reference_texts())
    assert payload["reconciliation"]["official_decision"] == PASS_DECISION
    assert payload["wp_statuses"]["WP-1"] == "PASS"
    assert payload["wp_statuses"]["WP-8"] == "PASS"
    assert payload["cutover_readiness_contract"]["candidate_id"] == "RC-R"
    assert payload["post_cutover_parity"]["preprojection_hash_mismatch_count"] == 0
    assert payload["targeted_acceptance_postcutover"]["mandatory_auth_pass"] is True
    assert payload["retention_postrollback"]["retained_after_rollback"] is True


def test_phase_payload_fails_when_reference_pack_loses_required_marker() -> None:
    texts = _reference_texts()
    texts["faz42"] = texts["faz42"].replace(
        "PASS - RC-R Process-Isolated Perimeter Isolated",
        "PASS - RC-R Process-Isolated Perimeter Mutated",
    )
    payload = build_phase_payload(texts)
    assert payload["reconciliation"]["official_decision"] == FAIL_DECISION
    assert payload["wp_statuses"]["WP-1"] == "FAIL"
    assert payload["reference_pack"]["reference_pack_contradiction_count"] == 1
