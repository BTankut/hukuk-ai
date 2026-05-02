from pathlib import Path

from rag.source_identity import (
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


def test_phase22f_s7_source_identity_fix_has_no_qid_specific_runtime_branch():
    source = Path(__file__).resolve().parents[1] / "src" / "rag" / "source_identity.py"

    assert "TEB-04" not in source.read_text(encoding="utf-8")
