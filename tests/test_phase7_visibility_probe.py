from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/benchmark/phase7_visibility_probe.py"
SPEC = importlib.util.spec_from_file_location("phase7_visibility_probe", MODULE_PATH)
assert SPEC and SPEC.loader
phase7_visibility_probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(phase7_visibility_probe)

best_catalog_match = phase7_visibility_probe.best_catalog_match
expected_family_canonical = phase7_visibility_probe.expected_family_canonical
identifier_filter = phase7_visibility_probe.identifier_filter
row_matches_expected_source = phase7_visibility_probe.row_matches_expected_source
status_for_probe = phase7_visibility_probe.status_for_probe
title_filter = phase7_visibility_probe.title_filter


def test_phase7_family_aliases_preserve_subtype_compatibility():
    assert expected_family_canonical("CB_KARAR") == "cb_karar"
    assert "kky" in phase7_visibility_probe.compatible_families("YONETMELIK")
    assert "yonetmelik" in phase7_visibility_probe.compatible_families("KKY")


def test_phase7_catalog_match_uses_identifier_and_title_overlap():
    tracker_row = {
        "expected_family": "CB_KARAR",
        "expected_source_title": "Yatırımlarda Devlet Yardımları Hakkında Karar (Karar Sayısı: 9903)",
        "expected_identifier": "9903",
    }
    catalog_rows = [
        {
            "source_key": "9903",
            "source_family_canonical": "cb_karar",
            "canonical_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR (KARAR SAYISI: 9903)",
            "canonical_title_normalized": "yatirimlarda devlet yardimlari hakkinda karar karar sayisi 9903",
            "canonical_identifier": "9903",
            "cross_refs": "9903",
        }
    ]

    match = best_catalog_match(tracker_row, catalog_rows)

    assert match is not None
    assert match["source_key"] == "9903"


def test_phase7_catalog_match_rejects_incompatible_related_law_identifier():
    tracker_row = {
        "expected_family": "YONETMELIK",
        "expected_source_title": "Konkordato Komiserliği Yönetmeliği",
        "expected_identifier": "2004",
    }
    catalog_rows = [
        {
            "source_key": "IIK",
            "source_family_canonical": "kanun",
            "canonical_title": "İCRA VE İFLAS KANUNU",
            "canonical_title_normalized": "icra ve iflas kanunu",
            "canonical_identifier": "2004",
            "cross_refs": "2004",
        }
    ]

    assert best_catalog_match(tracker_row, catalog_rows) is None


def test_phase7_catalog_match_rejects_generic_title_overlap_without_identifier():
    tracker_row = {
        "expected_family": "CB_YONETMELIK",
        "expected_source_title": "Resmî Yazışmalarda Uygulanacak Usul ve Esaslar Hakkında Yönetmelik",
        "expected_identifier": "",
    }
    catalog_rows = [
        {
            "source_key": "200915188",
            "source_family_canonical": "cb_yonetmelik",
            "canonical_title": "KAMU KURUM VE KURULUŞLARINA İŞÇİ ALINMASINDA UYGULANACAK USUL VE ESASLAR HAKKINDA YÖNETMELİK",
            "canonical_title_normalized": "kamu kurum ve kuruluslarina isci alinmasinda uygulanacak usul ve esaslar hakkinda yonetmelik",
            "canonical_identifier": "200915188",
            "cross_refs": "200915188",
        }
    ]

    assert best_catalog_match(tracker_row, catalog_rows) is None


def test_phase7_filters_include_identifier_and_title_terms():
    assert 'metadata["kanun_no"] == "6102"' in identifier_filter(["6102"])
    expr = title_filter("Türk Ticaret Kanunu")
    assert "TÜRK" in expr
    assert "TICARET" in expr


def test_phase7_hit_matching_accepts_compatible_regulation_family(tmp_path, monkeypatch):
    from rag.source_catalog import load_source_metadata_catalog, load_source_title_catalog

    article_rows = tmp_path / "article_rows.jsonl"
    article_rows.write_text("", encoding="utf-8")
    monkeypatch.setenv("MEVZUAT_ARTICLE_ROWS_PATH", str(article_rows))
    load_source_metadata_catalog.cache_clear()
    load_source_title_catalog.cache_clear()

    hit = {
        "text": "20237 m.1 MESAFELİ SÖZLEŞMELER YÖNETMELİĞİ",
        "metadata": {
            "belge_turu": "kky",
            "belge_no": "20237",
            "kanun_no": "20237",
            "belge_adi": "MESAFELİ SÖZLEŞMELER YÖNETMELİĞİ",
        },
    }
    tracker_row = {
        "expected_family": "YONETMELIK",
        "expected_source_title": "Mesafeli Sözleşmeler Yönetmeliği",
        "expected_identifier": "6502",
        "expected_related_identifiers": "",
    }

    assert row_matches_expected_source(hit, tracker_row)
    load_source_metadata_catalog.cache_clear()
    load_source_title_catalog.cache_clear()


def test_phase7_hit_matching_rejects_generic_overlap_without_distinctive_terms(tmp_path, monkeypatch):
    from rag.source_catalog import load_source_metadata_catalog, load_source_title_catalog

    article_rows = tmp_path / "article_rows.jsonl"
    article_rows.write_text("", encoding="utf-8")
    monkeypatch.setenv("MEVZUAT_ARTICLE_ROWS_PATH", str(article_rows))
    load_source_metadata_catalog.cache_clear()
    load_source_title_catalog.cache_clear()

    hit = {
        "text": "KAMU KURUM VE KURULUŞLARINA İŞÇİ ALINMASINDA UYGULANACAK USUL VE ESASLAR HAKKINDA YÖNETMELİK",
        "metadata": {
            "belge_turu": "cb_yonetmelik",
            "belge_no": "200915188",
            "belge_adi": "KAMU KURUM VE KURULUŞLARINA İŞÇİ ALINMASINDA UYGULANACAK USUL VE ESASLAR HAKKINDA YÖNETMELİK",
        },
    }
    tracker_row = {
        "expected_family": "CB_YONETMELIK",
        "expected_source_title": "Resmî Yazışmalarda Uygulanacak Usul ve Esaslar Hakkında Yönetmelik",
        "expected_identifier": "",
        "expected_related_identifiers": "",
    }

    assert not row_matches_expected_source(hit, tracker_row)
    load_source_metadata_catalog.cache_clear()
    load_source_title_catalog.cache_clear()


def test_phase7_status_classification_keeps_open_source_gaps_separate():
    assert status_for_probe(
        catalog_match=None,
        candidate_source_found=False,
        exact_identifier_found=False,
        title_found=False,
        year_found=False,
    ) == (
        "not_available_in_current_corpus",
        "open_source_acquisition_required",
        "not_retrieved_or_not_indexed",
    )
    assert status_for_probe(
        catalog_match={"source_key": "6102"},
        candidate_source_found=False,
        exact_identifier_found=True,
        title_found=False,
        year_found=False,
    )[2] == "gold_document_not_retrieved"
    assert status_for_probe(
        catalog_match=None,
        candidate_source_found=True,
        exact_identifier_found=False,
        title_found=False,
        year_found=False,
    )[2] == "visibility_resolved"
