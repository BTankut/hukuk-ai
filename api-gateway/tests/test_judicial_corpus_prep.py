from __future__ import annotations

import json
import hashlib
import sqlite3

import pytest

from data_pipeline.judicial import (
    DisabledJudicialRuntimeError,
    JudicialExactLookup,
    JudicialOfflineRetrievalPath,
    JudicialRetrievalLane,
    adapt_raw_judicial_decision,
    assert_judicial_runtime_disabled,
    build_exact_lookup_keys,
    build_indexable_documents,
    build_judicial_chunks_stream,
    build_judicial_exact_lookup_index,
    build_judicial_gate_skeleton,
    build_judicial_manifest_record,
    build_judicial_manifest_stream,
    build_shadow_index_plan,
    detect_duplicate_statuses,
    evaluate_offline_judicial_gate_state,
    generate_citation_key,
    inspect_judicial_package,
    normalize_judicial_text,
    prepare_judicial_chunks,
    preflight_judicial_jsonl,
    validate_judicial_chunks,
    validate_judicial_manifest,
)
from rag.query_analyzer import analyze_query


SAMPLE_DECISION_TEXT = """T. C. Yargıtay 9. Hukuk Dairesi

Davacı işçilik alacağı istemiştir.

Mahkemece verilen karar temyiz edilmiştir.

Sonuç olarak hükmün bozulmasına karar verilmiştir."""


RAW_DECISION_ROW = {
    "document_id": "1021302000",
    "mime_type": "text/html",
    "plain_text": (
        "T.C. İSTANBUL 19. ASLİYE TİCARET MAHKEMESİ\n\n"
        "ESAS NO : 2023/716 Esas\n"
        "KARAR NO : 2024/320\n"
        "DAVA : Tazminat\n"
        "KARAR TARİHİ : 29/04/2024\n\n"
        "Mahkememizde görülmekte olan davada TBK m.49 tartışılmıştır.\n\n"
        "Hüküm kurulmuştur."
    ),
    "markdown_content": "ignored",
    "source_url": "https://mevzuat.adalet.gov.tr/ictihat/1021302000",
    "version": 1,
}


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


def _write_jsonl(path, rows) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            if isinstance(row, str):
                handle.write(row + "\n")
            else:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def test_judicial_normalization_preserves_original_and_paragraphs() -> None:
    normalized = normalize_judicial_text(SAMPLE_DECISION_TEXT)

    assert normalized.original_text == SAMPLE_DECISION_TEXT
    assert normalized.paragraphs[0].startswith("T.C. Yargıtay")
    assert len(normalized.paragraphs) == 4
    assert "\n\n" in normalized.normalized_text
    assert len(normalized.document_hash) == 64
    assert len(normalized.normalized_text_hash) == 64


def test_raw_schema_adapter_maps_downloaded_adalet_row() -> None:
    mapping = adapt_raw_judicial_decision(
        RAW_DECISION_ROW,
        row_number=1,
        download_timestamp="2026-05-18T00:00:00+00:00",
    )

    assert mapping.accepted is True
    record = mapping.record or {}
    assert record["source_type"] == "judicial_decision"
    assert record["source_authority"] == "Adalet Bakanlığı İçtihat"
    assert record["court"] == "İSTANBUL 19. ASLİYE TİCARET MAHKEMESİ"
    assert record["chamber"] == "GENEL"
    assert record["decision_date"] == "2024-04-29"
    assert record["esas_no"] == "2023/716"
    assert record["karar_no"] == "2024/320"
    assert record["source_schema"] == "adalet_ictihat_jsonl_v1"
    assert record["text_field"] == "plain_text"
    assert "TBK m.49" in record["related_law_refs"]
    assert record["mapping_warnings"] == ["chamber_absent_defaulted_to_GENEL"]


def test_raw_schema_adapter_quarantines_missing_metadata() -> None:
    mapping = adapt_raw_judicial_decision(
        {"plain_text": "karar metni", "source_url": "https://mevzuat.adalet.gov.tr/ictihat/1"},
        row_number=7,
    )

    assert mapping.accepted is False
    assert mapping.quarantine is not None
    assert set(mapping.quarantine["reasons"]) >= {
        "missing_court",
        "missing_decision_date",
        "missing_case_or_esas_no",
        "missing_decision_or_karar_no",
    }


def test_preflight_streams_schema_inventory_and_capped_samples(tmp_path) -> None:
    raw_path = tmp_path / "decision_rows.jsonl"
    missing = dict(RAW_DECISION_ROW, plain_text="")
    _write_jsonl(raw_path, [RAW_DECISION_ROW, "{bad json", missing])

    summary = preflight_judicial_jsonl(raw_path, sample_cap=1)

    assert summary["total_lines"] == 3
    assert summary["valid_json_count"] == 2
    assert summary["invalid_json_count"] == 1
    assert summary["field_inventory"]["plain_text"] == 2
    assert summary["null_empty_counts"]["plain_text"] == 1
    assert summary["text_field_coverage"]["plain_text"] == 1
    assert summary["accepted_like_rows"] == 1
    assert summary["metadata_deficient_rows"] == 1
    assert summary["quarantine_reason_counts"]["invalid_json"] == 1
    assert len(summary["malformed_row_samples"]) == 1
    assert len(summary["metadata_deficient_row_samples"]) == 1
    assert summary["estimated_embedding_index_storage"]["collection"] == "judicial_decisions_v1_shadow"
    assert summary["source_authority_distribution"]["Adalet Bakanlığı İçtihat"] == 1
    assert summary["source_url_coverage"] == 2
    assert summary["estimated_exact_lookup_index_storage"]["lookup_keys_per_record"] == 7


def test_package_integrity_check_reads_sha256sums_and_merge_report(tmp_path) -> None:
    package_dir = tmp_path / "final_package"
    package_dir.mkdir()
    payload = package_dir / "decision_rows.jsonl"
    payload.write_text(json.dumps(RAW_DECISION_ROW, ensure_ascii=False) + "\n", encoding="utf-8")
    digest = hashlib.sha256(payload.read_bytes()).hexdigest()
    (package_dir / "SHA256SUMS").write_text(f"{digest}  decision_rows.jsonl\n", encoding="utf-8")
    (package_dir / "merge_report.json").write_text(
        json.dumps({"processed_unique": 1, "metadata_bad_lines": 0}),
        encoding="utf-8",
    )

    summary = inspect_judicial_package(package_dir, verify_hashes=True)

    assert summary["pass"] is True
    assert summary["hashes_verified"] is True
    assert summary["file_count"] == 1
    assert summary["missing_files"] == []
    assert summary["hash_mismatches"] == []
    assert summary["merge_report"]["processed_unique"] == 1


def test_citation_key_and_manifest_validation_are_deterministic() -> None:
    record = _sample_record()

    assert generate_citation_key(record) == "YARGITAY_9HD_2024_12345E_2024_6789K_2024-05-10"
    assert record["canonical_decision_id"] == (
        "judicial_decision:YARGITAY_9HD_2024_12345E_2024_6789K_2024-05-10"
    )
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


def test_raw_schema_adapter_quarantines_missing_chamber_for_chambered_court() -> None:
    mapping = adapt_raw_judicial_decision(
        {
            "court": "Yargıtay",
            "plain_text": (
                "Yargıtay\n\n"
                "ESAS NO : 2024/123\n"
                "KARAR NO : 2024/456\n"
                "KARAR TARİHİ : 10/05/2024\n\n"
                "Karar metni."
            ),
            "source_url": "https://karararama.yargitay.gov.tr/ornek",
        },
        row_number=3,
    )

    assert mapping.accepted is False
    assert mapping.quarantine is not None
    assert "missing_chamber" in mapping.quarantine["reasons"]


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
    assert len(chunks) == 2
    first_meta = chunks[0]["metadata"]
    assert first_meta["source_type"] == "judicial_decision"
    assert first_meta["citation_key"] == "YARGITAY_9HD_2024_12345E_2024_6789K_2024-05-10"
    assert first_meta["source_authority"] == "Yargıtay"
    assert first_meta["paragraph_index"] == 1
    assert first_meta["evidence_block_type"] == "unknown"
    body_meta = chunks[0]["metadata"]
    assert body_meta["paragraph_index"] == 1
    assert body_meta["paragraph_start"] == 1
    assert body_meta["paragraph_end"] == 2
    assert body_meta["year"] == "2024"
    assert body_meta["chunk_key"].endswith(":p1-2")


def test_judicial_retrieval_lane_is_indexable_offline_but_disabled_at_runtime(monkeypatch) -> None:
    monkeypatch.delenv("JUDICIAL_RUNTIME_ENABLED", raising=False)
    chunks = prepare_judicial_chunks(_sample_record(), max_paragraphs_per_chunk=2)
    lane = JudicialRetrievalLane(chunks=chunks)

    docs = build_indexable_documents(chunks)
    offline_results, stats = lane.retrieve(query="işçilik alacağı", top_k=5)

    assert assert_judicial_runtime_disabled()["pass"] is True
    assert len(docs) == len([chunk for chunk in chunks if chunk["metadata"]["vector_index_eligible"]])
    assert stats.collection == "judicial_decisions_v1_shadow"
    assert offline_results
    with pytest.raises(DisabledJudicialRuntimeError):
        lane.retrieve(query="işçilik alacağı", runtime=True)


def test_streaming_manifest_builder_quarantines_and_marks_duplicates(tmp_path) -> None:
    raw_path = tmp_path / "decision_rows.jsonl"
    exact_duplicate = dict(RAW_DECISION_ROW, source_url="https://mevzuat.adalet.gov.tr/ictihat/1021302001")
    normalized_duplicate = dict(
        RAW_DECISION_ROW,
        source_url="https://mevzuat.adalet.gov.tr/ictihat/1021302002",
        plain_text=RAW_DECISION_ROW["plain_text"].replace("\n\n", "\r\n\r\n"),
    )
    metadata_conflict = dict(
        RAW_DECISION_ROW,
        source_url="https://mevzuat.adalet.gov.tr/ictihat/1021302003",
        plain_text=RAW_DECISION_ROW["plain_text"].replace("Hüküm kurulmuştur.", "Farklı hüküm kurulmuştur."),
    )
    missing_text = dict(RAW_DECISION_ROW, plain_text="", markdown_content="")
    _write_jsonl(
        raw_path,
        [RAW_DECISION_ROW, exact_duplicate, normalized_duplicate, metadata_conflict, missing_text, "{bad"],
    )

    stats = build_judicial_manifest_stream(raw_path, tmp_path / "processed")
    manifest_path = tmp_path / "processed" / "judicial_manifest.jsonl"
    quarantine_path = tmp_path / "processed" / "judicial_quarantine.jsonl"
    duplicate_map_path = tmp_path / "processed" / "judicial_duplicate_map.jsonl"
    records = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines()]
    quarantines = [json.loads(line) for line in quarantine_path.read_text(encoding="utf-8").splitlines()]
    duplicate_rows = [json.loads(line) for line in duplicate_map_path.read_text(encoding="utf-8").splitlines()]

    assert stats["total_rows"] == 6
    assert stats["accepted_rows"] == 4
    assert stats["quarantined_rows"] == 2
    assert {item["reason"] for item in quarantines} == {"missing_text", "invalid_json"}
    assert stats["duplicate_counts"] == {"metadata_conflict": 4}
    assert {record["duplicate_status"] for record in records} == {"metadata_conflict"}
    assert len(duplicate_rows) == 4
    assert validate_judicial_manifest(records).to_dict()["pass"] is True


def test_streaming_manifest_builder_marks_canonical_id_collisions(tmp_path) -> None:
    raw_path = tmp_path / "decision_rows.jsonl"
    first = dict(
        RAW_DECISION_ROW,
        court="İSTANBUL 19. ASLİYE TİCARET MAHKEMESİ",
    )
    collision = dict(
        RAW_DECISION_ROW,
        court="ISTANBUL 19. ASLIYE TICARET MAHKEMESI",
        source_url="https://mevzuat.adalet.gov.tr/ictihat/1021302999",
        plain_text=RAW_DECISION_ROW["plain_text"] + "\n\nEk gerekçe.",
    )
    _write_jsonl(raw_path, [first, collision])

    stats = build_judicial_manifest_stream(raw_path, tmp_path / "processed")
    manifest_path = tmp_path / "processed" / "judicial_manifest.jsonl"
    records = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines()]

    assert stats["duplicate_counts"] == {"near_duplicate_candidate": 1, "unique": 1}
    assert stats["canonical_decision_count"] == 1
    assert [record["duplicate_status"] for record in records] == ["unique", "near_duplicate_candidate"]


def test_streaming_chunk_writer_keeps_only_canonical_records_by_default(tmp_path) -> None:
    manifest_path = tmp_path / "judicial_manifest.jsonl"
    unique = _sample_record()
    duplicate = _sample_record(
        source_url="https://example.test/dup",
        duplicate_status="exact_duplicate",
    )
    _write_jsonl(manifest_path, [unique, duplicate])

    stats = build_judicial_chunks_stream(manifest_path, tmp_path, max_paragraphs_per_chunk=2)
    chunks_path = tmp_path / "judicial_chunks.jsonl"
    chunks = [json.loads(line) for line in chunks_path.read_text(encoding="utf-8").splitlines()]

    assert stats["input_records"] == 2
    assert stats["canonical_records"] == 1
    assert stats["skipped_noncanonical_records"] == 1
    assert stats["chunks_written"] == 2
    assert all(chunk["metadata"]["evidence_block_type"] == "unknown" for chunk in chunks)
    assert validate_judicial_chunks(chunks).to_dict()["pass"] is True


def test_exact_lookup_supports_required_keys_and_persistent_index(tmp_path) -> None:
    record = _sample_record()
    lookup = JudicialExactLookup.from_records([record])

    assert build_exact_lookup_keys(record)
    assert lookup.lookup("citation_key", record["citation_key"]) == record
    assert lookup.lookup("canonical_decision_id", record["canonical_decision_id"]) == record
    assert lookup.lookup("source_url", record["source_url"]) == record
    assert lookup.lookup("document_hash", record["document_hash"]) == record
    assert lookup.lookup("normalized_text_hash", record["normalized_text_hash"]) == record
    assert (
        lookup.lookup_by_metadata(
            court="Yargıtay",
            chamber="9HD",
            esas_no="2024/12345",
            karar_no="2024/6789",
            decision_date="2024-05-10",
        )
        == record
    )

    manifest_path = tmp_path / "judicial_manifest.jsonl"
    _write_jsonl(manifest_path, [record])
    chunks_path = tmp_path / "judicial_chunks.jsonl"
    chunks = prepare_judicial_chunks(record, max_paragraphs_per_chunk=2)
    _write_jsonl(chunks_path, chunks)
    stats = build_judicial_exact_lookup_index(manifest_path, tmp_path, chunks_path=chunks_path)
    assert stats["records_indexed"] == 1
    assert stats["lookup_key_count"] == len(build_exact_lookup_keys(record))
    assert stats["chunk_refs_count"] == len(chunks)
    with sqlite3.connect(tmp_path / "judicial_exact_lookup.sqlite") as conn:
        refs = conn.execute("SELECT COUNT(*) FROM chunk_refs").fetchone()[0]
    assert refs == len(chunks)


def test_persistent_exact_lookup_keeps_ambiguous_lookup_keys(tmp_path) -> None:
    first = _sample_record()
    second = build_judicial_manifest_record(
        text=f"{SAMPLE_DECISION_TEXT}\n\nEk gerekçe.",
        source_authority="Yargıtay",
        court="Yargıtay",
        chamber="9HD",
        decision_date="2024-05-11",
        esas_no="2024/12345",
        karar_no="2024/6789",
        source_url="https://karararama.yargitay.gov.tr/ornek-2",
        download_timestamp="2026-05-11T00:00:00+00:00",
        related_law_refs=["TBK m.49"],
    )
    manifest_path = tmp_path / "judicial_manifest.jsonl"
    _write_jsonl(manifest_path, [first, second])

    stats = build_judicial_exact_lookup_index(manifest_path, tmp_path)
    ambiguous_key = dict(build_exact_lookup_keys(first))["court_chamber_esas_karar"]

    assert stats["lookup_key_count"] == len(build_exact_lookup_keys(first)) + len(build_exact_lookup_keys(second))
    assert stats["duplicate_lookup_keys"] == 1
    with sqlite3.connect(tmp_path / "judicial_exact_lookup.sqlite") as conn:
        rows = conn.execute(
            "SELECT canonical_decision_id FROM lookup WHERE lookup_type = ? AND lookup_key = ?",
            ("court_chamber_esas_karar", ambiguous_key),
        ).fetchall()
    assert {row[0] for row in rows} == {
        first["canonical_decision_id"],
        second["canonical_decision_id"],
    }


def test_shadow_index_plan_is_offline_and_skips_metadata_headers() -> None:
    chunks = prepare_judicial_chunks(_sample_record(), max_paragraphs_per_chunk=2)
    plan = build_shadow_index_plan(
        chunks=chunks,
        embedding_dim=8,
        batch_size=1,
        estimated_seconds_per_batch=0.5,
    )

    assert plan["collection"] == "judicial_decisions_v1_shadow"
    assert plan["runtime_enabled"] is False
    assert plan["status"] == "plan_only_no_embedding_started"
    assert plan["chunk_count"] == 2
    assert plan["checkpoint_required"] is True
    assert plan["estimated_embedding_runtime_seconds"] == 1.0
    assert "year" in plan["metadata_filters"]
    assert plan["resume_behavior"].startswith("skip existing chunk_key")


def test_offline_retrieval_path_exposes_exact_and_semantic_lanes(monkeypatch) -> None:
    monkeypatch.delenv("JUDICIAL_RUNTIME_ENABLED", raising=False)
    record = _sample_record()
    chunks = prepare_judicial_chunks(record, max_paragraphs_per_chunk=2, include_header_chunk=False)
    path = JudicialOfflineRetrievalPath(records=[record], chunks=chunks)

    exact_results = path.retrieve(
        query="ignored",
        exact_key_type="citation_key",
        exact_key=record["citation_key"],
    )
    semantic_results = path.retrieve(query="işçilik alacağı")

    assert exact_results[0]["retrieval_lane"] == "exact"
    assert exact_results[0]["retrieval_score"] == 1.0
    assert exact_results[0]["citation_key"] == record["citation_key"]
    assert exact_results[0]["paragraph_start"] == 1
    assert semantic_results[0]["retrieval_lane"] == "semantic"
    assert semantic_results[0]["metadata_filters_applied"] == {}
    assert semantic_results[0]["selected_chunk_text"]
    with pytest.raises(DisabledJudicialRuntimeError):
        path.retrieve(query="işçilik alacağı", runtime=True)


def test_judicial_gate_skeleton_is_inactive_until_enabled(monkeypatch) -> None:
    monkeypatch.delenv("JUDICIAL_CORPUS_GATE_ENABLED", raising=False)

    gate = build_judicial_gate_skeleton()

    assert gate["active"] is False
    assert "judicial_retrieval_hit_at_20" in gate["metrics"]
    assert "unsupported case-law claim" in gate["failure_modes"]
    assert "exact_lookup_success_rate" in gate["offline_checks"]
    assert "manifest_required_fields_validity" in gate["offline_checks"]


def test_offline_judicial_gate_requires_all_checks_and_runtime_disabled(monkeypatch) -> None:
    monkeypatch.delenv("JUDICIAL_CORPUS_GATE_ENABLED", raising=False)
    checks = {
        "raw_jsonl_validity": True,
        "manifest_required_fields_validity": True,
        "quarantine_reason_coverage": True,
        "duplicate_status_coverage": True,
        "citation_key_determinism": True,
        "canonical_decision_id_uniqueness": True,
        "chunk_key_uniqueness": True,
        "chunk_metadata_validity": True,
        "chunk_hash_validity": True,
        "exact_lookup_success_rate": True,
        "judicial_retrieval_hit_at_20": True,
        "decision_citation_validity_rate": True,
        "court_metadata_accuracy": True,
        "esas_karar_number_accuracy": True,
        "decision_date_accuracy": True,
        "selected_judicial_evidence_recall": True,
        "unsupported_judicial_claim_rate": True,
        "mevzuat_judicial_confusion_rate": True,
        "runtime_enabled_false": True,
        "runtime_enabled": False,
    }

    result = evaluate_offline_judicial_gate_state(checks)

    assert result["pass"] is True
    assert result["activation_scope"] == "offline_validation_only"
    assert result["runtime_enabled"] is False


def test_case_law_queries_remain_out_of_scope_before_judicial_closure() -> None:
    analysis = analyze_query("Yargıtay'ın en yeni emsal kararı nedir?")

    assert analysis.out_of_scope is True
