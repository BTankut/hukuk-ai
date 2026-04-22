from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/benchmark/phase7_acquisition_tracker.py"
SPEC = importlib.util.spec_from_file_location("phase7_acquisition_tracker", MODULE_PATH)
assert SPEC and SPEC.loader
phase7_acquisition_tracker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(phase7_acquisition_tracker)

build_tracker = phase7_acquisition_tracker.build_tracker
extract_identifiers = phase7_acquisition_tracker.extract_identifiers
split_expected_source = phase7_acquisition_tracker.split_expected_source


def test_phase7_tracker_extracts_primary_and_related_identifiers():
    rows = build_tracker(
        [
            {
                "qid": "CBKAR-05",
                "priority": "1",
                "blocker_type": "not_retrieved_or_not_indexed",
                "expected_family": "CB_KARAR",
                "expected_source": (
                    "Türk Parası Kıymetini Koruma Hakkında 32 Sayılı Karar | "
                    "Türk Parası Kıymetini Koruma Hakkında 32 Sayılı Karara İlişkin Tebliğ "
                    "(2008-32/34)"
                ),
                "owner": "needs_corpus_acquisition",
                "action_type": "source_acquisition_or_reindex",
                "resolution_status": "open",
            }
        ]
    )

    row = rows[0]
    assert row["expected_source_title"] == "Türk Parası Kıymetini Koruma Hakkında 32 Sayılı Karar"
    assert row["expected_identifier"] == "32"
    assert row["expected_identifier_type"] == "karar_sayisi"
    assert row["expected_related_identifiers"] == "teblig_no:2008-32/34"
    assert row["availability_status"] == "pending_visibility_probe"
    assert row["resolution_status"] == "pending_visibility_probe"
    assert row["next_action"] == "run_visibility_probe_then_acquire_or_reindex_if_absent"


def test_phase7_tracker_preserves_visibility_repair_action():
    rows = build_tracker(
        [
            {
                "qid": "KANUN-06",
                "priority": "3",
                "blocker_type": "gold_document_not_retrieved",
                "expected_family": "KANUN",
                "expected_source": "6102 sayılı Türk Ticaret Kanunu",
                "owner": "needs_corpus_acquisition",
                "action_type": "index_visibility_or_metadata_filter_repair",
                "resolution_status": "open",
            }
        ]
    )

    assert rows[0]["expected_identifier"] == "6102"
    assert rows[0]["expected_identifier_type"] == "kanun_no"
    assert rows[0]["next_action"] == "run_visibility_probe_then_repair_metadata_filter_or_selector"


def test_phase7_identifier_extraction_prefers_decision_number():
    assert extract_identifiers("İthalat Rejimi Kararı (Karar Sayısı: 3350)")[0] == (
        "karar_sayisi",
        "3350",
    )


def test_phase7_split_expected_source_handles_empty_related_sources():
    title, related = split_expected_source("Elektronik Tebligat Yönetmeliği | 7201 sayılı Tebligat Kanunu")

    assert title == "Elektronik Tebligat Yönetmeliği"
    assert related == ["7201 sayılı Tebligat Kanunu"]
