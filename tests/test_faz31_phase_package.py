from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "faz31"))


def _load_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_phase_package = _load_module("faz31_build_phase_package", "scripts/faz31/build_phase_package.py")
materialize_reference_pack = _load_module("faz31_materialize_reference_pack", "scripts/faz31/materialize_reference_pack.py")
faz31_lib = _load_module("faz31_lib_exact", "scripts/faz31/faz31_lib.py")

build_materialization_payload = materialize_reference_pack.build_materialization_payload
build_phase_payload = build_phase_package.build_phase_payload
PASS_DECISION = faz31_lib.PASS_DECISION
FAIL_DECISION = faz31_lib.FAIL_DECISION


def test_materialized_payload_freezes_expected_reference_chain() -> None:
    payload = build_materialization_payload()
    assert payload["reference_pack"]["reference_pack_integrity_pass"] is True
    assert payload["reference_pack"]["reference_pack_contradiction_count"] == 0
    assert payload["reference_pack"]["canonical_current_authority_ref"] == "FAZ21"
    assert payload["contract"]["candidate_status"] == "frozen_failed_repair_candidate"
    assert len(payload["topology_rows"]) == 4


def test_phase_payload_passes_with_current_forensic_truth_adopted() -> None:
    payload = build_phase_payload(build_materialization_payload())
    assert payload["reconciliation"]["official_decision"] == PASS_DECISION
    assert payload["wp_statuses"]["WP-1"] == "PASS"
    assert payload["wp_statuses"]["WP-6"] == "PASS"
    assert payload["adoption"]["current_forensic_truth_adopted"] is True
    assert payload["archive_reclassification"]["historical_stable_repair_truth_reclassified"] is True
    assert payload["consumer_binding"]["repair_truth_comparison_order"] == "current_forensic_truth -> historical_repair_archive"


def test_phase_payload_fails_when_current_forensic_truth_becomes_unexplained() -> None:
    materialized = build_materialization_payload()
    materialized["truths"]["current_forensic_repair_truth"]["boundary_frontier_166"]["unexplained_count"] = 1
    payload = build_phase_payload(materialized)
    assert payload["reconciliation"]["official_decision"] == FAIL_DECISION
    assert payload["wp_statuses"]["WP-3"] == "FAIL"
    assert payload["wp_statuses"]["WP-6"] == "FAIL"
