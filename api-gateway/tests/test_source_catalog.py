from __future__ import annotations

import json

from rag.source_catalog import enrich_metadata_with_source_title, load_source_title_catalog


def test_enrich_metadata_with_source_title_uses_article_rows_catalog(tmp_path, monkeypatch):
    article_rows = tmp_path / "article_rows.jsonl"
    article_rows.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "source_id": "20135150:20135150:m1:f0:from1900-01-01:to9999-12-31",
                        "belge_no": "20135150",
                        "belge_kisa_adi": "20135150",
                        "kanun_no": "20135150",
                        "kanun_kisa_adi": "20135150",
                        "belge_adi": "TAPU SİCİLİ TÜZÜĞÜ",
                    },
                    ensure_ascii=False,
                )
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("MEVZUAT_ARTICLE_ROWS_PATH", str(article_rows))
    load_source_title_catalog.cache_clear()

    enriched = enrich_metadata_with_source_title(
        {
            "source_id": "20135150:20135150:m7:f0:from1900-01-01:to9999-12-31",
            "belge_no": "20135150",
            "belge_kisa_adi": "20135150",
            "kanun_no": "20135150",
            "kanun_kisa_adi": "20135150",
        }
    )

    assert enriched["source_title"] == "TAPU SİCİLİ TÜZÜĞÜ"
    assert enriched["belge_adi"] == "TAPU SİCİLİ TÜZÜĞÜ"
    assert enriched["kanun_adi"] == "TAPU SİCİLİ TÜZÜĞÜ"
    load_source_title_catalog.cache_clear()
