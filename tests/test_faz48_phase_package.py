from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "faz48"))

from build_phase_package import build_phase_payload  # type: ignore
from faz48_lib import FAIL_DECISION, PASS_DECISION, REFERENCE_DOCS  # type: ignore


def _reference_texts() -> dict[str, str]:
    return {name: path.read_text(encoding="utf-8") for name, path in REFERENCE_DOCS.items()}


def test_current_repo_state_is_no_go_due_to_source_and_metadata_readiness_gap():
    payload = build_phase_payload(_reference_texts())

    assert payload["reconciliation"]["official_decision"] == FAIL_DECISION
    assert payload["wp_statuses"]["WP-1"] == "PASS"
    assert payload["wp_statuses"]["WP-2"] == "PASS"
    assert payload["wp_statuses"]["WP-3"] == "PASS"
    assert payload["wp_statuses"]["WP-4"] == "FAIL"
    assert payload["wp_statuses"]["WP-5"] == "FAIL"
    assert payload["wp_statuses"]["WP-6"] == "PASS"
    assert payload["wp_statuses"]["WP-7"] == "PASS"
    assert payload["wp_statuses"]["WP-8"] == "FAIL"
    assert payload["reconciliation"]["missing_primary_source_manifest_count"] == 6
    assert payload["reconciliation"]["missing_primary_raw_storage_location_count"] == 6
    assert payload["reconciliation"]["missing_primary_canonical_source_locator_count"] == 2
    assert payload["reconciliation"]["missing_mandatory_metadata_mapping_count"] == 48
    assert payload["reconciliation"]["runtime_error_count"] == 0
    assert payload["reconciliation"]["unexplained_count"] == 0


def test_pass_decision_when_reference_chain_and_readiness_rows_are_fully_closed():
    repo_files = [
        "data/raw/tmk/tmk_manifest.json",
        "data/raw/tmk/tmk_corpus.jsonl",
        "data/raw/tck/tck_manifest.json",
        "data/raw/tck/tck_corpus.jsonl",
        "data/raw/hmk/hmk_manifest.json",
        "data/raw/hmk/hmk_corpus.jsonl",
        "data/raw/cmk/cmk_manifest.json",
        "data/raw/cmk/cmk_corpus.jsonl",
        "data/raw/ttk/ttk_manifest.json",
        "data/raw/ttk/ttk_corpus.jsonl",
        "data/raw/ik/ik_manifest.json",
        "data/raw/ik/ik_corpus.jsonl",
    ]

    payload = build_phase_payload(
        _reference_texts(),
        repo_files=repo_files,
        locator_support={
            "TMK": True,
            "TCK": True,
            "HMK": True,
            "CMK": True,
            "TTK": True,
            "İK": True,
        },
    )

    assert payload["reconciliation"]["official_decision"] == PASS_DECISION
    assert payload["wp_statuses"]["WP-4"] == "PASS"
    assert payload["wp_statuses"]["WP-5"] == "PASS"
    assert payload["reconciliation"]["missing_primary_source_manifest_count"] == 0
    assert payload["reconciliation"]["missing_primary_raw_storage_location_count"] == 0
    assert payload["reconciliation"]["missing_primary_canonical_source_locator_count"] == 0
    assert payload["reconciliation"]["missing_mandatory_metadata_mapping_count"] == 0
