from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/benchmark/phase7_owner_backlog_refresh.py"
SPEC = importlib.util.spec_from_file_location("phase7_owner_backlog_refresh", MODULE_PATH)
assert SPEC and SPEC.loader
phase7_owner_backlog_refresh = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(phase7_owner_backlog_refresh)

build_refresh = phase7_owner_backlog_refresh.build_refresh


def test_visibility_resolved_acquisition_row_moves_to_selector_logic() -> None:
    rows = build_refresh(
        [
            {
                "qid": "CBKAR-01",
                "primary_owner": "needs_corpus_acquisition",
                "expected_family": "CB_KARAR",
                "expected_source": "İthalat Rejimi Kararı",
            }
        ],
        [
            {
                "qid": "CBKAR-01",
                "availability_status": "indexed_and_retrieval_visible",
                "resolution_status": "visibility_resolved_pending_benchmark_rerun",
                "phase7_blocker_type": "visibility_resolved",
            }
        ],
    )

    assert rows[0]["phase7_primary_owner"] == "needs_selector_logic"
    assert rows[0]["phase7_next_action"] == "query_visibility_or_selector_repair"


def test_unavailable_source_remains_corpus_acquisition() -> None:
    rows = build_refresh(
        [{"qid": "TUZUK-05", "primary_owner": "needs_corpus_acquisition"}],
        [
            {
                "qid": "TUZUK-05",
                "availability_status": "not_available_in_current_corpus",
                "resolution_status": "open_source_acquisition_required",
                "next_action": "acquire_primary_source_then_reindex",
            }
        ],
    )

    assert rows[0]["phase7_primary_owner"] == "needs_corpus_acquisition"
    assert rows[0]["phase7_next_action"] == "acquire_primary_source_then_reindex"


def test_catalog_backfill_visibility_row_moves_to_metadata() -> None:
    rows = build_refresh(
        [{"qid": "CBY-01", "primary_owner": "needs_corpus_acquisition"}],
        [
            {
                "qid": "CBY-01",
                "availability_status": "indexed_and_retrieval_visible_catalog_backfill_required",
                "resolution_status": "visibility_resolved_catalog_backfill_required",
                "phase7_blocker_type": "visibility_resolved",
            }
        ],
    )

    assert rows[0]["phase7_primary_owner"] == "needs_metadata_backfill"
