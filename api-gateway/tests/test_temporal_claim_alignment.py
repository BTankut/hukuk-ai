from __future__ import annotations

from rag.answer_synthesis import apply_temporal_claim_alignment


def _historical_chain_evidence() -> list[dict[str, object]]:
    return [
        {
            "source_id": "phase:test:regulation:old:m22:f0:from2012-01-01:to2023-01-01",
            "citation": "OLD_REG m.22/f.0",
            "source_identifier": "12345 m.1",
            "source_title": "Eski Öğrenci Disiplin Yönetmeliği",
            "source_family": "kky",
            "article_or_section": "22",
            "effective_state": "historical_repealed",
            "quoted_or_extracted_span": "Eski yönetmelik m.22, disiplin karar süresini düzenler.",
        },
        {
            "source_id": "phase:test:regulation_repeal:rg20230101:m1:f0:from2023-01-01:to9999-12-31",
            "citation": "rg20230101 m.1/f.0",
            "source_identifier": "rg20230101 m.1",
            "source_title": "Eski disiplin yönetmeliğini kaldıran düzenleme",
            "source_family": "yonetmelik",
            "article_or_section": "1",
            "effective_state": "repeal_instrument",
            "relation_chain_role": "repeal_instrument",
            "relation_chain_expansion_applied": True,
            "relation_chain_source_key": "phase:test:regulation:old:m22:f0:from2012-01-01:to2023-01-01",
            "relation_chain_repeal_source_key": "phase:test:regulation_repeal:rg20230101:m1:f0:from2023-01-01:to9999-12-31",
            "relation_chain_current_basis_source_key": "phase:test:law:2547:m54:f0:from1981-01-01:to9999-12-31",
            "quoted_or_extracted_span": "Eski yönetmelik yürürlükten kaldırılmıştır.",
        },
        {
            "source_id": "phase:test:law:2547:m54:f0:from1981-01-01:to9999-12-31",
            "citation": "2547 m.54/f.0",
            "source_identifier": "2547 m.1",
            "source_title": "Yükseköğretim Kanunu",
            "source_family": "kanun",
            "article_or_section": "54",
            "effective_state": "active",
            "relation_chain_role": "current_law_basis",
            "relation_chain_expansion_applied": True,
            "relation_chain_source_key": "phase:test:regulation:old:m22:f0:from2012-01-01:to2023-01-01",
            "relation_chain_repeal_source_key": "phase:test:regulation_repeal:rg20230101:m1:f0:from2023-01-01:to9999-12-31",
            "relation_chain_current_basis_source_key": "phase:test:law:2547:m54:f0:from1981-01-01:to9999-12-31",
            "quoted_or_extracted_span": "Güncel disiplin dayanağı 2547 sayılı Kanun m.54 kapsamındadır.",
        },
    ]


def _historical_contract(**overrides: object) -> dict[str, object]:
    contract: dict[str, object] = {
        "answer_mode": "repealed_transition_answer",
        "grounding_status": "partially_grounded",
        "source_family_claimed": "YONETMELIK",
        "source_title_claimed": "Eski disiplin yönetmeliğini kaldıran düzenleme",
        "source_identifier_claimed": "rg20230101 m.1",
        "article_or_section_claimed": "madde:1",
        "effective_state_claimed": "active",
        "confidence_0_100": 40,
        "needs_manual_review": True,
        "temporal_qualification": "2026-05-01",
    }
    contract.update(overrides)
    return contract


def test_historical_chain_synthesis_uses_three_roles() -> None:
    answer, patch = apply_temporal_claim_alignment(
        answer_text="Kısa cevap.",
        answer_contract=_historical_contract(),
        assembled_evidence=_historical_chain_evidence(),
    )

    assert patch["temporal_claim_alignment_applied"] is True
    assert patch["temporal_claim_primary_role"] == "current_law_basis"
    assert "Tarihsel kaynak" in answer
    assert "Yürürlük sınırı" in answer
    assert "Kanun bağlantısı" in answer


def test_repeal_instrument_not_primary_substantive_rule() -> None:
    _answer, patch = apply_temporal_claim_alignment(
        answer_text="Kaldırma maddesi asıl kuraldır.",
        answer_contract=_historical_contract(),
        assembled_evidence=_historical_chain_evidence(),
    )

    assert patch["source_identifier_claimed"] != "rg20230101 m.1"
    assert patch["temporal_claim_repeal_source_key"].endswith("rg20230101:m1:f0:from2023-01-01:to9999-12-31")
    assert patch["effective_state_claimed"] == "repealed"


def test_current_basis_claim_matches_current_source() -> None:
    _answer, patch = apply_temporal_claim_alignment(
        answer_text="Kısa cevap.",
        answer_contract=_historical_contract(),
        assembled_evidence=_historical_chain_evidence(),
    )

    assert patch["temporal_claim_current_basis_source_key"] == (
        "phase:test:law:2547:m54:f0:from1981-01-01:to9999-12-31"
    )
    assert patch["temporal_claim_current_basis_identifier"] == "2547 m.54"


def test_repealed_source_not_claimed_active() -> None:
    evidence = [
        {
            "source_id": "6570:6570:mGEC1:f0:from1955-05-27:to1900-01-01",
            "citation": "6570 m.GEC1/f.0",
            "source_identifier": "6570 m.2",
            "source_title": "Yürürlükten Kaldırılan Hükümler",
            "source_family": "mulga_kanun",
            "article_or_section": "gec1",
            "effective_state": "repealed",
            "quoted_or_extracted_span": "Geçici madde tarihsel kira rejimini düzenler.",
        }
    ]

    _answer, patch = apply_temporal_claim_alignment(
        answer_text="Aktif kaynak gibi cevap.",
        answer_contract=_historical_contract(
            source_identifier_claimed="unknown",
            article_or_section_claimed="madde:2",
            effective_state_claimed="active",
        ),
        assembled_evidence=evidence,
    )

    assert patch["effective_state_claimed"] == "repealed"
    assert patch["source_identifier_claimed"] == "6570 m.gec1"
    assert patch["article_or_section_claimed"] == "geçici madde 1"


def test_no_qid_specific_temporal_alignment() -> None:
    answer, patch = apply_temporal_claim_alignment(
        answer_text="Doğal dilde tarihsel soru.",
        answer_contract=_historical_contract(qid="UNRELATED-NATURAL-LANGUAGE-CASE"),
        assembled_evidence=_historical_chain_evidence(),
    )

    assert patch["temporal_claim_alignment_applied"] is True
    assert patch["temporal_claim_missing_reason"] == "none"
    assert "UNRELATED" not in answer


def test_active_non_historical_contract_not_aligned_by_incidental_repeal_text() -> None:
    evidence = [
        {
            "source_id": "23093:23093:m13:f0:from2025-01-01:to9999-12-31",
            "citation": "23093 m.13/f.0",
            "source_identifier": "23093 m.13",
            "source_title": "Aktif Tebliğ",
            "source_family": "tebligler",
            "article_or_section": "13",
            "effective_state": "active",
            "quoted_or_extracted_span": "Bu aktif tebliğ maddesi eski bir hükmün yürürlükten kaldırılmasına atıf yapar.",
        }
    ]

    answer, patch = apply_temporal_claim_alignment(
        answer_text="Aktif tebliğ cevabı.",
        answer_contract={
            "answer_mode": "qualified_answer",
            "source_family_claimed": "TEBLIGLER",
            "source_identifier_claimed": "23093 m.13",
            "article_or_section_claimed": "madde:13",
            "effective_state_claimed": "active",
        },
        assembled_evidence=evidence,
    )

    assert answer == "Aktif tebliğ cevabı."
    assert patch["temporal_claim_alignment_applied"] is False
