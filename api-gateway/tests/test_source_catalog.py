from __future__ import annotations

import json

from rag.source_catalog import (
    canonical_catalog_audit,
    canonical_identifier_type,
    enrich_metadata_with_source_title,
    load_canonical_source_catalog,
    load_source_metadata_catalog,
    load_source_title_catalog,
    normalize_canonical_text,
    source_family_mapping_profile,
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
    assert enriched["canonical_title"].startswith("2026 YILI YATIRIM PROGRAMININ")
    assert enriched["canonical_title_normalized"].startswith("2026 yili yatirim programinin")
    assert enriched["canonical_identifier"] == "10868"
    assert enriched["canonical_identifier_type"] == "karar_sayisi"
    assert enriched["issuer_normalized"] == "cumhurbaskanligi"
    assert enriched["issuer_canonical"] == "Cumhurbaşkanlığı"
    assert enriched["issuing_body_level"] == "cumhurbaskanligi"
    assert enriched["decision_year"] == "2026"
    assert enriched["decision_number"] == "10868"
    assert enriched["is_repealed"] is False
    assert enriched["canonical_title_family_normalized"].startswith("2026 yili yatirim programinin")
    assert enriched["metadata_provenance"]["decision_number"] == "inferred-normalized"
    assert "2026" in enriched["year_signals"]
    assert "10868" in enriched["cross_refs"]
    load_source_title_catalog.cache_clear()
    load_source_metadata_catalog.cache_clear()


def test_phase5_canonical_catalog_groups_source_identity(tmp_path, monkeypatch):
    article_rows = tmp_path / "article_rows.jsonl"
    article_rows.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "source_id": "3350:3350:m1:f0:from2021-01-01:to9999-12-31",
                        "belge_turu": "cb_karar",
                        "belge_no": "3350",
                        "belge_kisa_adi": "3350",
                        "belge_adi": "İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350)",
                        "madde_no": "1",
                        "resmi_gazete_tarih": "2020-12-31",
                        "resmi_gazete_sayi": "31351",
                        "yururluk_baslangic": "2021-01-01",
                        "yururluk_bitis": "9999-12-31",
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "source_id": "3350:3350:m2:f0:from2021-01-01:to9999-12-31",
                        "belge_turu": "cb_karar",
                        "belge_no": "3350",
                        "belge_kisa_adi": "3350",
                        "belge_adi": "İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350)",
                        "madde_no": "2",
                        "yururluk_baslangic": "2021-01-01",
                        "yururluk_bitis": "9999-12-31",
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("MEVZUAT_ARTICLE_ROWS_PATH", str(article_rows))
    load_canonical_source_catalog.cache_clear()

    catalog = load_canonical_source_catalog()

    assert "3350" in catalog
    record = catalog["3350"]
    assert record["source_family_canonical"] == "cb_karar"
    assert record["canonical_title"] == "İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350)"
    assert record["canonical_title_normalized"] == "ithalat rejimi karari karar sayisi 3350"
    assert record["canonical_identifier"] == "3350"
    assert record["canonical_identifier_type"] == "karar_sayisi"
    assert record["issuer"] == "Cumhurbaşkanlığı"
    assert record["decision_number"] == "3350"
    assert record["decision_year"] == "2020"
    assert "2020" in record["year_signals"]
    assert "2021" in record["year_signals"]
    assert "3350" in record["cross_refs"]
    audit = canonical_catalog_audit(catalog)
    assert audit["record_count"] >= 1
    assert audit["missing"]["canonical_title"] == 0
    load_canonical_source_catalog.cache_clear()


def test_phase6_family_metadata_backfill_extracts_teblig_and_university_fields(tmp_path, monkeypatch):
    article_rows = tmp_path / "article_rows.jsonl"
    article_rows.write_text("", encoding="utf-8")
    monkeypatch.setenv("MEVZUAT_ARTICLE_ROWS_PATH", str(article_rows))
    load_source_metadata_catalog.cache_clear()
    load_source_title_catalog.cache_clear()

    teblig = enrich_metadata_with_source_title(
        {
            "belge_turu": "teblig",
            "belge_no": "19186",
            "belge_adi": "VERGİ USUL KANUNU GENEL TEBLİĞİ (SIRA NO: 431)",
            "resmi_gazete_tarih": "2013-12-30",
        }
    )
    university = enrich_metadata_with_source_title(
        {
            "belge_turu": "uy",
            "belge_no": "40969",
            "belge_adi": "KIRKLARELİ ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ",
        }
    )

    assert teblig["sira_no"] == "431"
    assert teblig["decision_year"] == "2013"
    assert teblig["metadata_provenance"]["sira_no"] == "inferred-normalized"
    assert university["university_name_canonical"] == "KIRKLARELİ ÜNİVERSİTESİ"
    assert university["issuing_body_level"] == "universite"
    load_source_title_catalog.cache_clear()
    load_source_metadata_catalog.cache_clear()


def test_source_family_mapping_profile_bridges_generic_regulation_surfaces():
    kky_profile = source_family_mapping_profile(
        {
            "belge_turu": "kky",
            "belge_adi": "MESAFELİ SÖZLEŞMELER YÖNETMELİĞİ",
        }
    )
    teblig_profile = source_family_mapping_profile(
        {
            "belge_turu": "teblig",
            "belge_adi": "ELEKTRONİK TEBLİGAT YÖNETMELİĞİ",
        }
    )
    mulga_profile = source_family_mapping_profile(
        {
            "belge_turu": "mulga",
            "belge_adi": "MÜLGA BORÇLAR KANUNU",
        }
    )

    assert kky_profile["source_family_canonical"] == "kky"
    assert kky_profile["source_family_mapped"] == "yonetmelik"
    assert kky_profile["source_family_mapping_reason"] == "kky_to_yonetmelik"
    assert teblig_profile["source_family_mapped"] == "yonetmelik"
    assert teblig_profile["source_family_mapping_reason"] == "teblig_to_yonetmelik"
    assert mulga_profile["source_family_mapped"] == "kanun"
    assert mulga_profile["source_family_mapping_reason"] == "mulga_to_kanun"


def test_phase5_normalization_and_identifier_type_helpers():
    assert normalize_canonical_text("İthalat Rejimi Kararı") == "ithalat rejimi karari"
    assert (
        canonical_identifier_type(
            {
                "belge_turu": "cb_kararname",
                "belge_adi": "3 SAYILI CUMHURBAŞKANLIĞI KARARNAMESİ",
            }
        )
        == "kararname_no"
    )
