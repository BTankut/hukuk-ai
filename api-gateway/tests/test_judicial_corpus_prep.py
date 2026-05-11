from __future__ import annotations

import pytest

from data_pipeline.judicial import (
    DisabledJudicialRuntimeError,
    JudicialRetrievalLane,
    assert_judicial_runtime_disabled,
    build_indexable_documents,
    build_judicial_gate_skeleton,
    build_judicial_manifest_record,
    detect_duplicate_statuses,
    generate_citation_key,
    normalize_judicial_text,
    prepare_judicial_chunks,
    validate_judicial_chunks,
    validate_judicial_manifest,
)
from rag.query_analyzer import analyze_query


SAMPLE_DECISION_TEXT = """T. C. Yargıtay 9. Hukuk Dairesi

Davacı işçilik alacağı istemiştir.

Mahkemece verilen karar temyiz edilmiştir.

Sonuç olarak hükmün bozulmasına karar verilmiştir."""


def _sample_record(**overrides):
    record = build_judicial_manifest_record(
        text=SAMPLE_DECISION_TEXT,
        source_authority="Yargıtay",
        court="Yargıtay",
        chamber="9HD",
        decision_date="2024-05-10",
        esas_no="2024/12345",
        karar_no="2024/6789",
        source_url="https://karararama.yargitay.gov.tr/ornek",
        download_timestamp="2026-05-11T00:00:00+00:00",
        related_law_refs=["TBK m.49"],
    )
    record.update(overrides)
    return record


def test_judicial_normalization_preserves_original_and_paragraphs() -> None:
    normalized = normalize_judicial_text(SAMPLE_DECISION_TEXT)

    assert normalized.original_text == SAMPLE_DECISION_TEXT
    assert normalized.paragraphs[0].startswith("T.C. Yargıtay")
    assert len(normalized.paragraphs) == 4
    assert "\n\n" in normalized.normalized_text
    assert len(normalized.document_hash) == 64
    assert len(normalized.normalized_text_hash) == 64


def test_citation_key_and_manifest_validation_are_deterministic() -> None:
    record = _sample_record()

    assert generate_citation_key(record) == "YARGITAY_9HD_2024_12345E_2024_6789K_2024-05-10"
    summary = validate_judicial_manifest([record]).to_dict()

    assert summary["pass"] is True
    assert summary["error_count"] == 0
    assert summary["duplicate_counts"] == {"unique": 1}


def test_manifest_validation_fails_missing_required_identity_fields() -> None:
    record = _sample_record(court="", source_url="", document_hash="not-a-hash")

    summary = validate_judicial_manifest([record]).to_dict()

    assert summary["pass"] is False
    assert {error["field"] for error in summary["errors"]} >= {
        "court",
        "source_url",
        "document_hash",
    }


def test_duplicate_detection_marks_exact_normalized_and_metadata_conflicts() -> None:
    first = _sample_record(source_url="https://example.test/a")
    exact = dict(first, source_url="https://example.test/b")
    normalized = _sample_record(
        source_url="https://example.test/c",
        document_hash="0" * 64,
    )
    conflict = _sample_record(
        source_url="https://example.test/d",
        document_hash="1" * 64,
        normalized_text_hash="2" * 64,
    )

    records = detect_duplicate_statuses([first, exact, normalized, conflict])
    statuses = [record["duplicate_status"] for record in records]

    assert statuses[0] == "metadata_conflict"
    assert statuses[1] == "metadata_conflict"
    assert statuses[2] == "metadata_conflict"
    assert statuses[3] == "metadata_conflict"
    assert validate_judicial_manifest(records).to_dict()["metadata_conflict_count"] == 4


def test_chunk_generation_preserves_decision_identity_and_paragraph_range() -> None:
    record = _sample_record()
    chunks = prepare_judicial_chunks(record, max_paragraphs_per_chunk=2)
    summary = validate_judicial_chunks(chunks).to_dict()

    assert summary["pass"] is True
    assert len(chunks) == 3
    first_meta = chunks[0]["metadata"]
    assert first_meta["source_type"] == "judicial_decision"
    assert first_meta["citation_key"] == "YARGITAY_9HD_2024_12345E_2024_6789K_2024-05-10"
    assert first_meta["paragraph_index"] == 0
    assert first_meta["evidence_block_type"] == "metadata_header"
    body_meta = chunks[1]["metadata"]
    assert body_meta["paragraph_index"] == 1
    assert body_meta["paragraph_start"] == 1
    assert body_meta["paragraph_end"] == 2
    assert body_meta["chunk_key"].endswith(":p1-2")


def test_judicial_retrieval_lane_is_indexable_offline_but_disabled_at_runtime(monkeypatch) -> None:
    monkeypatch.delenv("JUDICIAL_RUNTIME_ENABLED", raising=False)
    chunks = prepare_judicial_chunks(_sample_record(), max_paragraphs_per_chunk=2)
    lane = JudicialRetrievalLane(chunks=chunks)

    docs = build_indexable_documents(chunks)
    offline_results, stats = lane.retrieve(query="işçilik alacağı", top_k=5)

    assert assert_judicial_runtime_disabled()["pass"] is True
    assert len(docs) == len(chunks)
    assert stats.collection == "judicial_decisions_pending"
    assert offline_results
    with pytest.raises(DisabledJudicialRuntimeError):
        lane.retrieve(query="işçilik alacağı", runtime=True)


def test_judicial_gate_skeleton_is_inactive_until_enabled(monkeypatch) -> None:
    monkeypatch.delenv("JUDICIAL_CORPUS_GATE_ENABLED", raising=False)

    gate = build_judicial_gate_skeleton()

    assert gate["active"] is False
    assert "judicial_retrieval_hit_at_20" in gate["metrics"]
    assert "unsupported case-law claim" in gate["failure_modes"]


def test_case_law_queries_remain_out_of_scope_before_judicial_closure() -> None:
    analysis = analyze_query("Yargıtay'ın en yeni emsal kararı nedir?")

    assert analysis.out_of_scope is True
