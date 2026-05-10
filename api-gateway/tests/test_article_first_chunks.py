from __future__ import annotations

import hashlib
import json
from pathlib import Path

from data_pipeline.article_first_chunks import (
    DEFAULT_ARTICLE_FIRST_COLLECTION,
    REQUIRED_CHUNK_FIELDS,
    chunk_records_for_article_row,
    split_article_units,
    validate_article_first_chunks,
    validate_article_first_source,
)


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _row(**overrides: object) -> dict[str, object]:
    body = str(overrides.pop("body", "Kusurlu ve hukuka aykırı bir fiille başkasına zarar veren bunu giderir."))
    row: dict[str, object] = {
        "belge_turu": "kanun",
        "belge_no": "6098",
        "belge_kisa_adi": "TBK",
        "belge_adi": "TÜRK BORÇLAR KANUNU",
        "kanun_no": "6098",
        "kanun_kisa_adi": "TBK",
        "kanun_adi": "TÜRK BORÇLAR KANUNU",
        "madde_no": "49",
        "madde_no_int": 49,
        "fikra_no": "0",
        "source_id": "6098:6098:m49:f0:from2012-07-01:to9999-12-31",
        "display_citation": "TBK m.49",
        "canonical_source_locator": "law://6098/6098/TBK m.49",
        "yururluk_baslangic": "2012-07-01",
        "yururluk_bitis": "9999-12-31",
        "mulga": False,
        "kind": "main",
        "heading": "Sorumluluk",
        "body": body,
        "kaynak_url": "https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=6098&MevzuatTur=1&MevzuatTertip=5",
        "resmi_gazete_tarih": "2011-02-04",
        "resmi_gazete_sayi": "27836",
        "metin_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
    }
    row.update(overrides)
    return row


def test_short_article_stays_whole_and_has_required_metadata() -> None:
    records = chunk_records_for_article_row(_row(), row_number=1)

    assert len(records) == 1
    record = records[0]
    metadata = record["metadata"]
    assert record["chunk_id"] == metadata["chunk_id"]
    assert metadata["collection_name"] == DEFAULT_ARTICLE_FIRST_COLLECTION
    assert metadata["source_id"] == "kanun:6098"
    assert metadata["source_family"] == "kanun"
    assert metadata["title"] == "Türk Borçlar Kanunu"
    assert metadata["article_no"] == "49"
    assert metadata["article_type"] == "main"
    assert metadata["paragraph_no"] == "0"
    assert metadata["canonical_citation"] == "Türk Borçlar Kanunu m. 49"
    assert metadata["chunk_text_hash"] == hashlib.sha256(record["text"].encode("utf-8")).hexdigest()
    assert all(field in metadata for field in REQUIRED_CHUNK_FIELDS)


def test_repealed_article_uses_source_id_temporal_end_date() -> None:
    row = _row(
        belge_turu="mulga_kanun",
        belge_no="7354",
        source_id="7354:7354:m2:f0:from2022-02-14:to1900-01-01",
        yururluk_bitis=None,
        mulga=True,
    )

    record = chunk_records_for_article_row(row, row_number=3)[0]

    assert record["metadata"]["article_type"] == "repealed"
    assert record["metadata"]["effective_state"] == "repealed"
    assert record["metadata"]["effective_end_date"] == "1900-01-01"


def test_long_article_splits_by_explicit_paragraph_and_keeps_parent_article() -> None:
    body = "\n".join(
        [
            "(1) " + " ".join(["birinci"] * 20),
            "(2) " + " ".join(["ikinci"] * 20),
        ]
    )

    records = chunk_records_for_article_row(_row(body=body), row_number=7, max_words=12)

    assert len(records) >= 4
    parent_ids = {record["metadata"]["parent_article_id"] for record in records}
    assert len(parent_ids) == 1
    assert {record["metadata"]["paragraph_no"].split(".", 1)[0] for record in records} == {"1", "2"}
    assert all(record["metadata"]["canonical_citation"].startswith("Türk Borçlar Kanunu m. 49/") for record in records)
    assert all(record["metadata"]["chunk_unit_type"] != "article" for record in records)


def test_split_article_units_packs_physical_paragraphs_for_long_unnumbered_body() -> None:
    body = "\n".join(f"Satır {idx} " + "kelime " * 5 for idx in range(20))

    units = split_article_units(body, max_words=30)

    assert len(units) > 1
    assert all(unit.paragraph_no.startswith("p") for unit in units)
    assert all(unit.text.strip() for unit in units)


def test_validate_article_first_source_accepts_duplicate_source_rows_without_collapsing_manifest_count(tmp_path: Path) -> None:
    rows_path = tmp_path / "article_rows.jsonl"
    manifest_path = tmp_path / "source_manifest.json"
    duplicate = _row()
    _write_jsonl(rows_path, [duplicate, duplicate])
    manifest_path.write_text(json.dumps({"total_articles": 2}), encoding="utf-8")

    result = validate_article_first_source(rows_path, source_manifest_path=manifest_path)

    assert result["pass"] is True
    assert result["source_row_count"] == 2
    assert result["article_count"] == 2
    assert result["manifest_article_count_mismatch"] == 0
    assert result["duplicate_canonical_chunk_key_count"] == 0
    assert result["empty_chunk_count"] == 0
    assert result["citation_missing_count"] == 0


def test_validate_article_first_chunks_detects_acceptance_failures() -> None:
    bad_record = {
        "id": "bad",
        "text": "",
        "metadata": {
            "chunk_id": "bad",
            "source_id": "kanun:1",
            "source_family": "kanun",
            "title": "Test Kanunu",
            "law_no": "1",
            "source_no": "1",
            "article_no": "1",
            "article_type": "invalid",
            "paragraph_no": "0",
            "subparagraph_no": None,
            "article_heading": "",
            "hierarchy_path": "source:kanun:1/article:main:1/paragraph:0",
            "effective_state": "historical",
            "effective_start_date": "2000-01-01",
            "effective_end_date": "2001-01-01",
            "version_date": "2000-01-01",
            "official_url": "https://www.mevzuat.gov.tr/",
            "source_hash": "abc",
            "chunk_text_hash": "not-the-real-hash",
            "canonical_chunk_key": "same",
            "parent_article_id": "kanun:1:m1:r1",
            "chunk_unit_type": "article",
            "promote_for_current_law": True,
        },
    }

    result = validate_article_first_chunks([bad_record, bad_record], expected_article_count=1)

    assert result["pass"] is False
    assert result["empty_chunk_count"] == 2
    assert result["citation_missing_count"] == 2
    assert result["duplicate_canonical_chunk_key_count"] == 1
    assert result["duplicate_chunk_id_count"] == 1
    assert result["invalid_article_type_count"] == 2
    assert result["noncurrent_promoted_count"] == 2
    assert result["chunk_text_hash_mismatch_count"] == 2
