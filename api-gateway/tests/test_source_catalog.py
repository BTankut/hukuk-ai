from __future__ import annotations

import json

from rag.source_catalog import (
    enrich_metadata_with_source_title,
    load_source_metadata_catalog,
    load_source_title_catalog,
)


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
    load_source_metadata_catalog.cache_clear()
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
    assert enriched["full_title"] == "TAPU SİCİLİ TÜZÜĞÜ"
    assert enriched["issuer"] == "Bakanlar Kurulu"
    assert enriched["source_family_canonical"] == "tuzuk"
    assert enriched["effective_state"] == "active"
    load_source_title_catalog.cache_clear()
    load_source_metadata_catalog.cache_clear()


def test_enrich_metadata_adds_phase4_canonical_fields(tmp_path, monkeypatch):
    article_rows = tmp_path / "article_rows.jsonl"
    article_rows.write_text(
        json.dumps(
            {
                "source_id": "10868:10868:m0:f0:from2026-01-15:to9999-12-31",
                "belge_turu": "cb_karar",
                "belge_no": "10868",
                "belge_kisa_adi": "10868",
                "belge_adi": "2026 YILI YATIRIM PROGRAMININ KABULÜ VE UYGULANMASINA DAİR KARAR (KARAR SAYISI: 10868)",
                "madde_no": "0",
                "fikra_no": "0",
                "display_citation": "10868 m.0",
                "resmi_gazete_tarih": "2026-01-15",
                "resmi_gazete_sayi": "33000",
                "yururluk_baslangic": "2026-01-15",
                "yururluk_bitis": "9999-12-31",
                "mulga": False,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("MEVZUAT_ARTICLE_ROWS_PATH", str(article_rows))
    load_source_metadata_catalog.cache_clear()
    load_source_title_catalog.cache_clear()

    enriched = enrich_metadata_with_source_title(
        {
            "source_id": "10868:10868:m0:f0:from2026-01-15:to9999-12-31",
            "belge_no": "10868",
        }
    )

    assert enriched["full_title"].startswith("2026 YILI YATIRIM PROGRAMININ")
    assert enriched["issuer"] == "Cumhurbaşkanlığı"
    assert enriched["official_gazette_no"] == "33000"
    assert enriched["official_gazette_date"] == "2026-01-15"
    assert enriched["effective_start"] == "2026-01-15"
    assert enriched["effective_end"] == "9999-12-31"
    assert enriched["canonical_identifier_display"] == "10868 m.0"
    assert enriched["source_family_canonical"] == "cb_karar"
    assert enriched["effective_state"] == "active"
    load_source_title_catalog.cache_clear()
    load_source_metadata_catalog.cache_clear()
