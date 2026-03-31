from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "faz39"))


def _load_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_phase_package = _load_module("faz39_build_phase_package", "scripts/faz39/build_phase_package.py")
faz39_lib = _load_module("faz39_lib_exact", "scripts/faz39/faz39_lib.py")

build_materialized_payload = build_phase_package.build_materialized_payload
build_phase_payload = build_phase_package.build_phase_payload
PASS_DECISION = faz39_lib.PASS_DECISION
FAIL_DECISION = faz39_lib.FAIL_DECISION


def test_materialized_payload_freezes_expected_reference_chain() -> None:
    payload = build_materialized_payload()
    assert payload["reference_pack"]["reference_pack_integrity_pass"] is True
    assert payload["reference_pack"]["reference_pack_contradiction_count"] == 0
    assert payload["reference_pack"]["canonical_current_authority_ref"] == "FAZ21"
    assert payload["reference_pack"]["current_perimeter_truth_ref"] == "FAZ35"
    assert payload["reference_pack"]["current_instability_truth_ref"] == "FAZ38"
    assert payload["contract"]["candidate_status"] == "frozen_failed_repair_candidate"
    assert payload["contract"]["repair_truth_comparison_order"] == (
        "current_perimeter_truth_reference -> current_repair_truth -> historical_repair_archive"
    )
    assert len(payload["topology_rows"]) == 5


def test_phase_payload_passes_with_current_instability_truth_adopted() -> None:
    payload = build_phase_payload(build_materialized_payload())
    assert payload["reconciliation"]["official_decision"] == PASS_DECISION
    assert payload["wp_statuses"]["WP-1"] == "PASS"
    assert payload["wp_statuses"]["WP-7"] == "PASS"
    assert payload["current_perimeter_truth_preservation"]["current_perimeter_truth_reference_preserved"] is True
    assert payload["current_instability_truth_adoption"]["current_instability_truth_adopted"] is True
    assert payload["historical_archive_reclassification"]["historical_failed_repair_truth_reclassified"] is True
    assert payload["consumer_binding"]["repair_truth_comparison_order"] == (
        "current_perimeter_truth_reference -> current_repair_truth -> historical_repair_archive"
    )


def test_phase_payload_fails_when_current_instability_truth_contract_breaks() -> None:
    materialized = build_materialized_payload()
    materialized["faz38_support"]["union_instability_rowset_count"] = 5
    payload = build_phase_payload(materialized)
    assert payload["reconciliation"]["official_decision"] == FAIL_DECISION
    assert payload["wp_statuses"]["WP-4"] == "FAIL"
    assert payload["wp_statuses"]["WP-7"] == "FAIL"
