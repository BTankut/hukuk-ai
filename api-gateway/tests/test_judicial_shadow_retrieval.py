from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_pipeline.indexing import InMemoryVectorStore
from data_pipeline.judicial import (
    JudicialHybridRetriever,
    PersistentJudicialExactLookupStore,
    assert_judicial_runtime_disabled,
    audit_processed_judicial_corpus,
    build_judicial_chunks_stream,
    build_judicial_exact_lookup_index,
    build_judicial_lexical_index,
    build_judicial_manifest_record,
    build_judicial_offline_eval_cases,
    build_judicial_vector_shadow_sizing,
    evaluate_judicial_offline_eval_cases,
    query_judicial_lexical_index,
    run_judicial_vector_shadow_batch,
    validate_judicial_evidence_results,
)


SAMPLE_TEXT = """T. C. Yargıtay 9. Hukuk Dairesi

Davacı işçilik alacağı ve fazla mesai ücreti istemiştir.

Mahkemece verilen karar temyiz edilmiştir.

Yargıtay, TBK m.49 bakımından tazminat koşullarını tartışmıştır.

Sonuç olarak hükmün bozulmasına karar verilmiştir."""


class FakeEmbedder:
    dimension = 4

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text) % 7), 0.0, 1.0, 0.5] for text in texts]


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _sample_record() -> dict:
    return build_judicial_manifest_record(
        text=SAMPLE_TEXT,
        source_authority="Yargıtay",
        court="Yargıtay",
        chamber="9HD",
        decision_date="2024-05-10",
        esas_no="2024/12345",
        karar_no="2024/6789",
        source_url="https://karararama.yargitay.gov.tr/ornek-shadow",
        download_timestamp="2026-05-19T00:00:00+00:00",
        related_law_refs=["TBK m.49"],
    )


def _build_processed_fixture(tmp_path: Path) -> tuple[Path, dict]:
    processed = tmp_path / "processed"
    processed.mkdir()
    record = _sample_record()
    duplicate = dict(record)
    duplicate["duplicate_status"] = "exact_duplicate"
    duplicate["raw_row_number"] = 2
    manifest_path = processed / "judicial_manifest.jsonl"
    _write_jsonl(manifest_path, [record, duplicate])
    _write_jsonl(
        processed / "judicial_quarantine.jsonl",
        [
            {
                "row_number": 3,
                "reason": "missing_decision_date",
                "reasons": ["missing_decision_date"],
                "source_url": "https://karararama.yargitay.gov.tr/missing",
            }
        ],
    )
    _write_jsonl(
        processed / "judicial_duplicate_map.jsonl",
        [
            {
                "row_number": 2,
                "duplicate_status": "exact_duplicate",
                "canonical_row_number": 1,
                "canonical_decision_id": record["canonical_decision_id"],
                "citation_key": record["citation_key"],
            }
        ],
    )
    _write_json(
        processed / "raw_preflight_stats.json",
        {
            "total_lines": 3,
            "valid_json_count": 3,
            "invalid_json_count": 0,
            "accepted_like_rows": 2,
            "metadata_deficient_rows": 1,
        },
    )
    _write_json(
        processed / "judicial_ingest_stats.json",
        {
            "accepted_rows": 2,
            "canonical_decision_count": 1,
            "duplicate_counts": {"exact_duplicate": 1, "unique": 1},
            "invalid_json_rows": 0,
            "quarantine_reason_counts": {"missing_decision_date": 1},
            "quarantined_rows": 1,
            "total_rows": 3,
            "valid_json_rows": 3,
        },
    )
    build_judicial_chunks_stream(manifest_path, processed, max_paragraphs_per_chunk=2)
    build_judicial_exact_lookup_index(
        manifest_path,
        processed,
        chunks_path=processed / "judicial_chunks.jsonl",
    )
    return processed, record


def test_processed_corpus_coverage_audit_passes_with_machine_checkable_counts(tmp_path) -> None:
    processed, _record = _build_processed_fixture(tmp_path)

    audit = audit_processed_judicial_corpus(processed, output_path=processed / "audit.json")

    assert audit["pass"] is True
    assert audit["raw_to_accepted_gap"]["raw_rows"] == 3
    assert audit["raw_to_accepted_gap"]["accepted_rows"] == 2
    assert audit["raw_to_accepted_gap"]["canonical_decisions"] == 1
    assert audit["raw_to_accepted_gap"]["top_quarantine_reasons"] == {"missing_decision_date": 1}
    assert audit["integrity"]["canonical_decision_id_unique_duplicates"] == 0
    assert audit["integrity"]["citation_key_unique_duplicates"] == 0
    assert audit["integrity"]["chunk_key_duplicates"] == 0
    assert audit["integrity"]["unresolved_chunk_refs"] == 0


def test_persistent_exact_lookup_query_returns_metadata_and_chunk_refs(tmp_path) -> None:
    processed, record = _build_processed_fixture(tmp_path)
    store = PersistentJudicialExactLookupStore(processed / "judicial_exact_lookup.sqlite")

    by_citation = store.lookup("citation_key", record["citation_key"])
    by_metadata = store.lookup_by_metadata(
        court="Yargıtay",
        chamber="9HD",
        esas_no="2024/12345",
        karar_no="2024/6789",
        decision_date="2024-05-10",
    )

    assert by_citation[0]["metadata"]["court"] == "Yargıtay"
    assert by_citation[0]["metadata"]["chamber"] == "9HD"
    assert by_citation[0]["metadata"]["decision_date"] == "2024-05-10"
    assert by_citation[0]["metadata"]["esas_no"] == "2024/12345"
    assert by_citation[0]["metadata"]["karar_no"] == "2024/6789"
    assert by_citation[0]["metadata"]["source_url"] == record["source_url"]
    assert by_citation[0]["chunk_refs"]
    assert by_metadata[0]["canonical_decision_id"] == record["canonical_decision_id"]


def test_exact_lookup_compacts_newline_court_metadata_for_composite_keys(tmp_path) -> None:
    record = build_judicial_manifest_record(
        text=SAMPLE_TEXT,
        source_authority="Adalet",
        court="İstanbul\n3. Asliye Ticaret Mahkemesi",
        chamber="GENEL",
        decision_date="2024-05-10",
        esas_no="2024/12345",
        karar_no="2024/6789",
        source_url="https://karararama.yargitay.gov.tr/newline-court",
        download_timestamp="2026-05-19T00:00:00+00:00",
        related_law_refs=[],
    )
    manifest_path = tmp_path / "manifest.jsonl"
    chunks_path = tmp_path / "chunks.jsonl"
    _write_jsonl(manifest_path, [record])
    _write_jsonl(chunks_path, [])
    build_judicial_exact_lookup_index(manifest_path, tmp_path, chunks_path=chunks_path)
    store = PersistentJudicialExactLookupStore(tmp_path / "judicial_exact_lookup.sqlite")

    rows = store.lookup_by_metadata(
        court="İstanbul 3. Asliye Ticaret Mahkemesi",
        chamber="GENEL",
        esas_no="2024/12345",
        karar_no="2024/6789",
        decision_date="2024-05-10",
    )

    assert rows[0]["canonical_decision_id"] == record["canonical_decision_id"]


def test_lexical_retrieval_uses_sqlite_bm25_filters_and_citation_contract(tmp_path) -> None:
    processed, record = _build_processed_fixture(tmp_path)
    stats = build_judicial_lexical_index(processed / "judicial_chunks.jsonl", processed, batch_size=1)

    results = query_judicial_lexical_index(
        processed / "judicial_lexical_index.sqlite",
        "işçilik alacağı fazla mesai bozma",
        filters={"court": "Yargıtay", "chamber": "9HD", "year": "2024", "related_law_refs": "TBK m.49"},
        top_k=5,
    )

    assert stats["chunks_indexed"] > 0
    assert results
    assert results[0]["retrieval_lane"] == "lexical"
    assert results[0]["citation_key"] == record["citation_key"]
    assert results[0]["canonical_decision_id"] == record["canonical_decision_id"]
    assert results[0]["court"] == "Yargıtay"
    assert results[0]["paragraph_start"] >= 1
    assert results[0]["source_url"] == record["source_url"]
    assert results[0]["metadata_filters_applied"]["year"] == "2024"


def test_hybrid_retrieval_preserves_lanes_scores_and_evidence_checks(tmp_path) -> None:
    processed, record = _build_processed_fixture(tmp_path)
    build_judicial_lexical_index(processed / "judicial_chunks.jsonl", processed)
    retriever = JudicialHybridRetriever(
        exact_store=PersistentJudicialExactLookupStore(processed / "judicial_exact_lookup.sqlite"),
        lexical_index_path=processed / "judicial_lexical_index.sqlite",
    )

    results = retriever.retrieve(
        query="işçilik alacağı bozma",
        exact_key_type="citation_key",
        exact_key=record["citation_key"],
        filters={"court": "Yargıtay"},
        top_k=5,
    )
    validation = validate_judicial_evidence_results(results)

    assert results
    assert results[0]["retrieval_lane"] == "hybrid"
    assert "exact" in results[0]["score_components"]
    assert "lexical" in results[0]["score_components"]
    assert results[0]["final_score"] == results[0]["score"]
    assert validation["pass"] is True


def test_anti_confusion_rejects_legislation_duplicate_and_metadata_header_evidence() -> None:
    invalid = {
        "text": "TBK m.49 metni",
        "selected_chunk_text": "TBK m.49 metni",
        "chunk_key": "duplicate",
        "citation_key": "x",
        "canonical_decision_id": "x",
        "court": "Yargıtay",
        "chamber": "9HD",
        "decision_date": "2024-05-10",
        "esas_no": "2024/1",
        "karar_no": "2024/2",
        "paragraph_start": 0,
        "paragraph_end": 0,
        "source_url": "https://example.invalid",
        "source_type": "legislation",
        "retrieval_lane": "lexical",
        "score": 1.0,
        "metadata_filters_applied": {},
        "metadata": {"duplicate_status": "exact_duplicate", "vector_index_eligible": False},
    }

    validation = validate_judicial_evidence_results([invalid, dict(invalid)])

    assert validation["pass"] is False
    modes = {failure["mode"] for failure in validation["failures"]}
    assert "source_type_confusion" in modes
    assert "noncanonical_duplicate_evidence" in modes
    assert "metadata_header_as_evidence" in modes
    assert "duplicate_chunk_support" in modes


def test_vector_shadow_sizing_and_checkpoint_resume(tmp_path, monkeypatch) -> None:
    processed, _record = _build_processed_fixture(tmp_path)
    chunks_path = processed / "judicial_chunks.jsonl"
    monkeypatch.setenv("EMBEDDING_DIM", "4")

    sizing = build_judicial_vector_shadow_sizing(chunks_path, batch_size=2, output_path=processed / "sizing.json")
    dry = run_judicial_vector_shadow_batch(chunks_path, processed / "vector_checkpoint.sqlite", batch_size=1)
    real = run_judicial_vector_shadow_batch(
        chunks_path,
        processed / "vector_checkpoint.sqlite",
        batch_size=1,
        dry_run=False,
        embedder=FakeEmbedder(),
        vector_store=InMemoryVectorStore(),
    )
    resumed = run_judicial_vector_shadow_batch(chunks_path, processed / "vector_checkpoint.sqlite", batch_size=1)

    assert sizing["embedding_dim"] == 4
    assert sizing["checkpoint_required"] is True
    assert sizing["skip_already_embedded_chunk_key"] is True
    assert dry["status"] == "dry_run_no_embeddings"
    assert real["status"] == "small_batch_checkpointed"
    assert real["embeddings_written"] == 1
    assert resumed["skipped_completed"] == 1


def test_offline_eval_cases_cover_required_metrics_and_runtime_closed(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("JUDICIAL_RUNTIME_ENABLED", raising=False)
    processed, record = _build_processed_fixture(tmp_path)
    build_judicial_lexical_index(processed / "judicial_chunks.jsonl", processed)
    cases = build_judicial_offline_eval_cases(record)
    evaluation = evaluate_judicial_offline_eval_cases(
        cases,
        exact_store=PersistentJudicialExactLookupStore(processed / "judicial_exact_lookup.sqlite"),
        lexical_index_path=processed / "judicial_lexical_index.sqlite",
    )

    assert assert_judicial_runtime_disabled()["pass"] is True
    assert {case["id"] for case in cases} == {
        "exact_ek_lookup",
        "court_chamber_date_lookup",
        "source_url_lookup",
        "hash_lookup",
        "legal_issue_lexical",
        "legal_issue_hybrid",
        "cross_law_judicial_reasoning",
        "legislation_judicial_distinction",
        "unsupported_case_law_query",
        "duplicate_canonical_behavior",
        "metadata_filter_behavior",
    }
    assert evaluation["pass"] is True
    assert set(evaluation["metrics"]) == {
        "exact_lookup_success_rate",
        "lexical_retrieval_hit_at_20",
        "hybrid_retrieval_hit_at_20",
        "decision_citation_validity_rate",
        "court_metadata_accuracy",
        "esas_karar_number_accuracy",
        "decision_date_accuracy",
        "selected_judicial_evidence_recall",
        "unsupported_judicial_claim_rate",
        "mevzuat_judicial_confusion_rate",
        "latency_p95_ms_exact_lookup",
        "latency_p95_ms_lexical_retrieval",
    }


def test_runtime_judicial_enabled_true_remains_fail_closed(monkeypatch) -> None:
    monkeypatch.setenv("JUDICIAL_RUNTIME_ENABLED", "true")

    assert assert_judicial_runtime_disabled()["pass"] is False
