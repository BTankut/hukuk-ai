from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "faz32"))


def _load_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_phase_package = _load_module("faz32_build_phase_package", "scripts/faz32/build_phase_package.py")
faz32_lib = _load_module("faz32_lib_exact", "scripts/faz32/faz32_lib.py")

build_phase_payload = build_phase_package.build_phase_payload
PASS_DECISION = faz32_lib.PASS_DECISION
FAIL_DECISION = faz32_lib.FAIL_DECISION
REFERENCE_DOCS = faz32_lib.REFERENCE_DOCS
load_text = faz32_lib.load_text


def _reference_texts() -> dict[str, str]:
    return {key: load_text(path) for key, path in REFERENCE_DOCS.items()}


def test_phase_payload_passes_with_exact_closure_contract() -> None:
    payload = build_phase_payload(_reference_texts())
    assert payload["reconciliation"]["official_decision"] == PASS_DECISION
    assert payload["wp_statuses"]["WP-1"] == "PASS"
    assert payload["wp_statuses"]["WP-5"] == "PASS"
    assert payload["archival_contract"]["candidate_status"] == "discard_archived"
    assert payload["registry"]["archive_registry_contains_rc_o"] is True
    assert payload["planner_denylist"]["planner_can_open_build_for_rc_o"] is False
    assert payload["tombstone"]["tombstone_status"] == "active"


def test_phase_payload_fails_when_reference_pack_loses_required_marker() -> None:
    texts = _reference_texts()
    texts["faz31"] = texts["faz31"].replace(
        "PASS - RC-O Repair Truth Reconciled Under Canonical Current Authority",
        "PASS - RC-O Repair Truth Reconciliation Mutated",
    )
    payload = build_phase_payload(texts)
    assert payload["reconciliation"]["official_decision"] == FAIL_DECISION
    assert payload["wp_statuses"]["WP-1"] == "FAIL"
    assert payload["wp_statuses"]["WP-5"] == "FAIL"
    assert payload["reference_pack"]["reference_pack_contradiction_count"] == 1
