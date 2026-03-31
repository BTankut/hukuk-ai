from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "faz38"))


def _load_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_phase_package = _load_module("faz38_build_phase_package", "scripts/faz38/build_phase_package.py")
faz38_lib = _load_module("faz38_lib_exact", "scripts/faz38/faz38_lib.py")

build_materialized_payload = build_phase_package.build_materialized_payload
build_phase_payload = build_phase_package.build_phase_payload
load_capture_bundle = build_phase_package._load_capture_bundle
FAIL_AUTHORITY = faz38_lib.FAIL_AUTHORITY
PASS_DECISION = faz38_lib.PASS_DECISION


def test_materialized_payload_freezes_exact_contract() -> None:
    payload = build_materialized_payload()
    assert payload["reference_pack"]["canonical_current_authority_ref"] == "FAZ21"
    assert payload["reference_pack"]["post_rc_o_steering_ref"] == "FAZ33"
    assert payload["contract"]["candidate_id"] == "RC-Q"
    assert payload["contract"]["patch_existing_candidate_authorized"] is False


def test_phase_payload_passes_on_faz37_twin_capture_truth() -> None:
    payload = build_phase_payload(capture_a=load_capture_bundle("a"), capture_b=load_capture_bundle("b"))

    assert payload["official_decision"] == PASS_DECISION
    assert payload["overlap_matrix"]["frontier_instability_rowset_count"] == 6
    assert payload["overlap_matrix"]["response_envelope_instability_rowset_count"] == 3
    assert payload["overlap_matrix"]["full_family_instability_rowset_count"] == 3
    assert payload["overlap_matrix"]["union_instability_rowset_count"] == 6
    assert payload["root_cause_summary"]["unexplained_count"] == 0
    assert payload["wp_statuses"]["WP-6"] == "PASS"


def test_phase_payload_maps_wp2_breach_to_authority_failure() -> None:
    capture_a = load_capture_bundle("a")
    capture_b = load_capture_bundle("b")
    capture_b["current_authority"] = dict(capture_b["current_authority"])
    capture_b["current_authority"]["control_pair_authority_match"] = False

    payload = build_phase_payload(capture_a=capture_a, capture_b=capture_b)

    assert payload["wp_statuses"]["WP-2"] == "FAIL"
    assert payload["official_decision"] == FAIL_AUTHORITY
