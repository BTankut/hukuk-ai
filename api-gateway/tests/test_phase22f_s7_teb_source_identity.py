from pathlib import Path

from rag.orchestrator import RetrievedChunk
from rag.source_identity import (
    _chunk_matches_selected_source_key,
    _detect_teb_kdv_source_identity_signal,
    _select_metadata_first_source_candidates,
)
from source_family_resolver import SourceFamilyResolution


def _family_resolution(
    *,
    predicted_family: str | None = "teblig",
    routing_families: list[str] | None = None,
    preferred_families: list[str] | None = None,
) -> SourceFamilyResolution:
    return SourceFamilyResolution(
        predicted_family=predicted_family,
        family_confidence=0.84,
        routing_families=routing_families or ["teblig"],
        preferred_families=preferred_families or ["teblig"],
    )


def _catalog() -> dict[str, dict[str, object]]:
    return {
        "19631": {
            "source_key": "19631",
            "canonical_title": "KATMA DEĞER VERGİSİ GENEL UYGULAMA TEBLİĞİ",
            "canonical_identifier": "19631",
            "canonical_identifier_type": "teblig_no",
            "source_family_canonical": "teblig",
            "source_family_raw": "teblig",
            "source_family_mapped": "teblig",
            "effective_state": "active",
            "year_signals": ["2014"],
            "alias_titles": ["KDV Genel Uygulama Tebliği"],
        },
        "99999": {
            "source_key": "99999",
            "canonical_title": "ELEKTRONİK TEBLİGAT GENEL TEBLİĞİ",
            "canonical_identifier": "99999",
            "canonical_identifier_type": "teblig_no",
            "source_family_canonical": "teblig",
            "source_family_raw": "teblig",
            "source_family_mapped": "teblig",
            "effective_state": "active",
            "year_signals": ["2020"],
            "alias_titles": ["Elektronik Tebligat Genel Tebliği"],
        },
    }


def test_kdv_teblig_operational_signal_selects_general_application_teblig():
    selector = _select_metadata_first_source_candidates(
        query="KDV tevkifatı ve iade bakımından ana tebliğin konsolide metnine göre cevapla.",
        requested_source_families=["teblig"],
        source_family_resolution=_family_resolution(),
        catalog_loader=_catalog,
    )

    assert selector is not None
    assert selector["selected_source_keys"] == ["19631"]
    assert selector["metadata_lookup_source"] == "teb_kdv_source_identity_lookup"
    assert selector["teb_kdv_signal_detected"] is True
    assert selector["teb_kdv_candidate_injected"] is True
    assert selector["teb_kdv_candidate_source_key"] == "19631"
    assert selector["candidates"][0]["teb_kdv_rerank_boost_applied"] is True


def test_kdv_signal_requires_teblig_family_context():
    signal = _detect_teb_kdv_source_identity_signal(
        query="KDV iade şartları bakımından güncel kanun hükmü nedir?",
        requested_source_families=["kanun"],
        source_family_resolution=_family_resolution(
            predicted_family="kanun",
            routing_families=["kanun"],
            preferred_families=["kanun"],
        ),
    )

    assert signal["teb_kdv_signal_detected"] is False
    assert signal["teb_kdv_candidate_source_key"] == ""


def test_non_kdv_teblig_query_does_not_force_kdv_general_application_source():
    selector = _select_metadata_first_source_candidates(
        query="Elektronik tebliğ başvuru usulü ve bildirim süresi nedir?",
        requested_source_families=["teblig"],
        source_family_resolution=_family_resolution(),
        catalog_loader=_catalog,
    )

    assert selector is None or "19631" not in selector.get("selected_source_keys", [])


def test_phase24w_recovery_flag_blocks_title_only_selected_source_match(monkeypatch):
    chunk = RetrievedChunk(
        text="body",
        citation="123 m.1/f.0",
        source="123",
        metadata={
            "canonical_identifier": "123",
            "source_title": "Example Regulation",
            "madde_no": "1",
        },
    )

    monkeypatch.delenv("ENABLE_PHASE24W_SOURCE_IDENTITY_RECOVERY", raising=False)
    assert _chunk_matches_selected_source_key(chunk, {"Example Regulation"}) is True

    monkeypatch.setenv("ENABLE_PHASE24W_SOURCE_IDENTITY_RECOVERY", "true")
    assert _chunk_matches_selected_source_key(chunk, {"Example Regulation"}) is False


def test_phase24w_recovery_flag_preserves_canonical_selected_source_match(monkeypatch):
    chunk = RetrievedChunk(
        text="body",
        citation="123 m.1/f.0",
        source="123",
        metadata={
            "canonical_identifier": "123",
            "source_title": "Example Regulation",
            "madde_no": "1",
        },
    )

    monkeypatch.setenv("ENABLE_PHASE24W_SOURCE_IDENTITY_RECOVERY", "true")

    assert _chunk_matches_selected_source_key(chunk, {"123"}) is True


def test_phase24x_gate_demotes_support_law_identifier_when_regulation_is_requested(monkeypatch):
    monkeypatch.setenv("ENABLE_PHASE24X_FAMILY_DOMAIN_COMPATIBILITY_GATE", "true")

    selector = _select_metadata_first_source_candidates(
        query="3194 sayılı kanun tek başına yetmez; planlı alanlar imar yönetmeliği de devreye girer mi?",
        requested_source_families=["kanun", "yonetmelik"],
        source_family_resolution=SourceFamilyResolution(
            predicted_family="kanun",
            family_confidence=0.82,
            routing_families=["kanun", "yonetmelik"],
            preferred_families=["kanun", "yonetmelik"],
        ),
        catalog_loader=lambda: {
            "3194": {
                "source_key": "3194",
                "canonical_title": "İMAR KANUNU",
                "canonical_identifier": "3194",
                "canonical_identifier_type": "law_no",
                "source_family_canonical": "kanun",
                "source_family_raw": "kanun",
                "source_family_mapped": "kanun",
                "effective_state": "active",
            },
            "23722": {
                "source_key": "23722",
                "canonical_title": "PLANLI ALANLAR İMAR YÖNETMELİĞİ",
                "canonical_identifier": "23722",
                "canonical_identifier_type": "regulation_no",
                "source_family_canonical": "yonetmelik",
                "source_family_raw": "yonetmelik",
                "source_family_mapped": "yonetmelik",
                "effective_state": "active",
            },
        },
    )

    assert selector is not None
    assert selector["selected_source_keys"][0] == "23722"
    assert selector["phase24x_family_domain_gate_enabled"] is True
    assert selector["phase24x_filtered_candidates"][0]["source_key"] == "3194"
    assert selector["phase24x_filtered_candidates"][0]["phase24x_candidate_block_reason"] == "support_identifier_context"


def test_phase24x_gate_blocks_sector_title_only_primary_and_forces_fallback(monkeypatch):
    monkeypatch.setenv("ENABLE_PHASE24X_FAMILY_DOMAIN_COMPATIBILITY_GATE", "true")

    selector = _select_metadata_first_source_candidates(
        query="Tüketici hakları yönetmeliği kişiye özel ölçü mobilya cayma hakkı nedir?",
        requested_source_families=["yonetmelik"],
        source_family_resolution=SourceFamilyResolution(
            predicted_family="yonetmelik",
            family_confidence=0.8,
            routing_families=["yonetmelik"],
            preferred_families=["yonetmelik"],
        ),
        catalog_loader=lambda: {
            "24039": {
                "source_key": "24039",
                "canonical_title": "ELEKTRONİK HABERLEŞME SEKTÖRÜNE İLİŞKİN TÜKETİCİ HAKLARI YÖNETMELİĞİ",
                "canonical_identifier": "24039",
                "canonical_identifier_type": "regulation_no",
                "source_family_canonical": "kky",
                "source_family_raw": "kky",
                "source_family_mapped": "yonetmelik",
                "source_family_mapping_reason": "kky_to_yonetmelik",
                "effective_state": "active",
            },
        },
    )

    assert selector is not None
    assert selector["metadata_lookup_hit"] is False
    assert selector["phase24x_fallback_after_all_metadata_candidates_blocked"] is True
    assert selector["phase24x_filtered_candidates"][0]["source_key"] == "24039"
    assert (
        selector["phase24x_filtered_candidates"][0]["phase24x_candidate_block_reason"]
        == "domain_incompatible_title_only_primary"
    )


def test_phase22f_s7_source_identity_fix_has_no_qid_specific_runtime_branch():
    source = Path(__file__).resolve().parents[1] / "src" / "rag" / "source_identity.py"

    assert "TEB-04" not in source.read_text(encoding="utf-8")
    assert "KANUN-08" not in source.read_text(encoding="utf-8")
    assert "YON-05" not in source.read_text(encoding="utf-8")
