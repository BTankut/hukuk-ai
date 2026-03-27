from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "faz24"))

from build_phase_package import build_phase_payload  # type: ignore


def _reference_texts() -> dict[str, str]:
    return {
        "faz16": "PASS - Replacement Build Surface Isolated\nruntime_error_count = 0\ncontrol_pair_breach_in_f0_f12 = false\n",
        "faz17": "NO-GO - RC-M Output Parity Surface Breach\nruntime_error_count = 0\nauthoritative_summary_mismatch_count = 1\noutput_parity_surface_breach_count = 1\nlocalized_authorized_downstream_drift_count = 0\n",
        "faz21": "PASS - Current Authority Canonicalized\ncurrent_canonical_authority_adopted = true\nhistorical_archive_reclassified = true\ndownstream_consumer_binding_pass = true\nauthoritative comparison order = `current_canonical -> historical_archive`\nhistorical archive kanali = `diagnostic_only`\nsurface_breach_from_history_reintroduced = false\n",
        "faz22": "NO-GO - RC-M Surface Breach Non-Reproducible Under Canonical Current Authority\nauthoritative_summary_mismatch_count = 0\noutput_parity_surface_breach_count = 0\nfrontier_candidate_count = 0\n",
        "faz23": "PASS - RC-M Authoritative Summary Truth Reconciled Under Canonical Current Authority\nhistorical_summary_mismatch_count = `1`\ncurrent_summary_mismatch_count = `0`\nhistorical_surface_breach_count = `1`\ncurrent_surface_breach_count = `0`\nhistorical_frontier_candidate_count = `1`\ncurrent_frontier_candidate_count = `0`\nhistorical_summary_truth_reclassified_to_archive_after_canonical_current_authority_adoption\nhistorical_summary_truth_reclassified_to_archive\n",
    }


def test_faz24_payload_pass_path() -> None:
    payload = build_phase_payload(_reference_texts())
    assert payload["wp_statuses"] == {
        "WP-1": "PASS",
        "WP-2": "PASS",
        "WP-3": "PASS",
        "WP-4": "PASS",
        "WP-5": "PASS",
    }
    assert payload["reconciliation"]["official_decision"] == "PASS - RC-M Discard Archived Under Canonical Current Authority"
    assert payload["reconciliation"]["next_official_work"] == "post-rc-m steering re-entry under canonical current authority"


def test_faz24_payload_fails_when_reference_pack_breaks() -> None:
    texts = _reference_texts()
    texts["faz23"] = texts["faz23"].replace("current_summary_mismatch_count = `0`\n", "")
    payload = build_phase_payload(texts)
    assert payload["reference_pack"]["reference_pack_integrity_pass"] is False
    assert payload["wp_statuses"]["WP-1"] == "FAIL"
    assert payload["reconciliation"]["official_decision"] == "FAIL - RC-M Archival Closure Contract Not Materialized"


def test_faz24_registry_and_denylist_close_rc_m() -> None:
    payload = build_phase_payload(_reference_texts())
    assert payload["registry"]["active_candidate_set_contains_rc_m"] is False
    assert payload["registry"]["archive_registry_contains_rc_m"] is True
    assert all(value is False for value in payload["planner_denylist"].values())
