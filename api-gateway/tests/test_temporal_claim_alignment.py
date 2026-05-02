from __future__ import annotations

from pathlib import Path

from rag.answer_synthesis import apply_temporal_claim_alignment, sanitize_public_answer_contract


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


def _active_kanun_evidence() -> list[dict[str, object]]:
    return [
        {
            "source_id": "KVKK:6698:m6:f0:from2016-04-07:to9999-12-31",
            "citation": "KVKK m.6/f.0",
            "source_identifier": "KVKK m.1",
            "source_title": "Kişisel Verilerin Korunması Kanunu",
            "source_family": "kanun",
            "article_or_section": "6",
            "effective_state": "active",
            "quoted_or_extracted_span": "Güncel özel nitelikli kişisel veri işleme rejimi.",
        }
    ]


def _active_tuzuk_evidence() -> list[dict[str, object]]:
    return [
        {
            "source_id": "859727:859727:m4:f0:from1985-09-07:to9999-12-31",
            "citation": "859727 m.4/f.0",
            "source_identifier": "859727 m.1",
            "source_title": "Radyasyon Güvenliği Tüzüğü",
            "source_family": "tuzuk",
            "article_or_section": "4",
            "effective_state": "active",
            "quoted_or_extracted_span": "Aktif tüzük m.4 radyasyon güvenliği kapsamını düzenler.",
        }
    ]


def _active_teblig_evidence() -> list[dict[str, object]]:
    return [
        {
            "source_id": "23093:23093:m13:f0:from2025-01-01:to9999-12-31",
            "citation": "23093 m.13/f.0",
            "source_identifier": "23093 m.1",
            "source_title": "Aktif Tebliğ",
            "source_family": "tebligler",
            "article_or_section": "13",
            "effective_state": "active",
            "quoted_or_extracted_span": "Aktif tebliğ m.13 elektronik bildirim usulünü düzenler.",
        }
    ]


def _active_preservation_trace() -> dict[str, object]:
    return {
        "question_raw": (
            "Cevabı eski KVKK yurt dışı aktarım rejimine göre mi, yoksa güncel rejime göre mi kurmalısın?"
        ),
        "retrieval": {
            "source_family_resolution": {
                "predicted_family": "kanun",
                "historical_or_repealed_question": True,
                "historical_scope_detected": True,
                "preferred_families": ["kanun"],
            },
            "article_span_selector": {
                "legacy_intent_binding_active": True,
                "legacy_candidate_preferred": False,
                "scenario_current_law_question": True,
            },
        },
    }


def _legacy_mulga_trace() -> dict[str, object]:
    return {
        "question_raw": "Tapu işlemlerinde 1994 tarihli Tapu Sicili Tüzüğünü kullanmak neden doğrudan hata üretir?",
        "retrieval": {
            "source_family_resolution": {
                "predicted_family": "tuzuk",
                "historical_or_repealed_question": True,
                "historical_scope_detected": True,
                "family_candidates": [
                    {
                        "family": "mulga_kanun",
                        "signals": ["legacy_source_risk_signal"],
                    }
                ],
            },
            "article_span_selector": {
                "legacy_intent_binding_active": True,
                "legacy_candidate_preferred": False,
            },
        },
    }


def test_active_non_mulga_preserves_claim_family() -> None:
    _answer, patch = apply_temporal_claim_alignment(
        answer_text="Aktif kanun cevabı.",
        answer_contract=_historical_contract(
            source_family_claimed="MULGA",
            effective_state_claimed="repealed",
            answer_mode="repealed_transition_answer",
        ),
        assembled_evidence=_active_kanun_evidence(),
        trace_payload=_active_preservation_trace(),
    )

    assert patch["split_temporal_policy_applied"] is True
    assert patch["split_temporal_policy_bucket"] == "active_non_mulga_preserve_family"
    assert patch["claim_family_rewrite_allowed"] is False
    assert patch["historical_claim_surface_allowed"] is False
    assert patch["s5_family_identifier_guard_applied"] is True
    assert patch["s5_guard_type"] == "active_non_mulga_claim_preservation"
    assert patch["s5_claim_family_preserved"] is True
    assert patch["source_family_claimed"] == "KANUN"
    assert patch["source_family_claimed"] != "MULGA"


def test_active_non_mulga_preserves_claim_identifier() -> None:
    _answer, patch = apply_temporal_claim_alignment(
        answer_text="Aktif kanun cevabı.",
        answer_contract=_historical_contract(
            source_family_claimed="MULGA",
            source_identifier_claimed="MULGA m.0",
            effective_state_claimed="repealed",
            answer_mode="repealed_transition_answer",
        ),
        assembled_evidence=_active_kanun_evidence(),
        trace_payload=_active_preservation_trace(),
    )

    assert patch["source_identifier_claimed"] == "KVKK m.6"
    assert patch["article_or_section_claimed"] == "madde:6"
    assert patch["claim_identifier_rewrite_allowed"] is False
    assert patch["temporal_support_only"] is True
    assert patch["s5_claim_identifier_preserved"] is True


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


def test_relation_chain_allows_controlled_historical_claim() -> None:
    _answer, patch = apply_temporal_claim_alignment(
        answer_text="Kısa cevap.",
        answer_contract=_historical_contract(),
        assembled_evidence=_historical_chain_evidence(),
    )

    assert patch["split_temporal_policy_bucket"] == "relation_chain_historical_three_part_claim"
    assert patch["claim_family_rewrite_allowed"] == "controlled"
    assert patch["claim_identifier_rewrite_allowed"] == "controlled"
    assert patch["historical_claim_surface_allowed"] is True


def test_repeal_instrument_not_primary_substantive_rule() -> None:
    _answer, patch = apply_temporal_claim_alignment(
        answer_text="Kaldırma maddesi asıl kuraldır.",
        answer_contract=_historical_contract(),
        assembled_evidence=_historical_chain_evidence(),
    )

    assert patch["source_identifier_claimed"] != "rg20230101 m.1"
    assert patch["temporal_claim_repeal_source_key"].endswith("rg20230101:m1:f0:from2023-01-01:to9999-12-31")
    assert patch["effective_state_claimed"] == "repealed"


def test_legacy_mulga_without_relation_chain_keeps_historical_surface() -> None:
    evidence = [
        {
            "source_id": "20135150:20135150:m90:f0:from1900-01-01:to9999-12-31",
            "citation": "20135150 m.90/f.0",
            "source_identifier": "20135150 m.1",
            "source_title": "Tapu Sicili Tüzüğü",
            "source_family": "mulga_kanun",
            "article_or_section": "90",
            "effective_state": "historical_repealed",
            "quoted_or_extracted_span": "Tapu sicili tüzüğünün tarihsel maddesi.",
        }
    ]

    _answer, patch = apply_temporal_claim_alignment(
        answer_text="1994 tarihli tüzük bugün doğrudan uygulanmamalıdır.",
        answer_contract=_historical_contract(
            source_family_claimed="MULGA",
            source_identifier_claimed="20135150 m.90",
            effective_state_claimed="repealed",
            answer_mode="not_currently_applicable_answer",
        ),
        assembled_evidence=evidence,
        trace_payload=_legacy_mulga_trace(),
    )

    assert patch["split_temporal_policy_bucket"] == "legacy_mulga_historical_surface_without_relation_chain"
    assert patch["claim_family_rewrite_allowed"] == "limited_to_historical_surface"
    assert patch["historical_claim_surface_allowed"] is True
    assert patch["source_family_claimed"] == "MULGA"
    assert patch["effective_state_claimed"] == "repealed"


def test_active_non_mulga_historical_surface_clamp_preserves_claim_family() -> None:
    _answer, patch = apply_temporal_claim_alignment(
        answer_text="Aktif tüzük cevabı.",
        answer_contract=_historical_contract(
            source_family_claimed="MULGA",
            source_identifier_claimed="MULGA m.4",
            effective_state_claimed="repealed",
            answer_mode="not_currently_applicable_answer",
        ),
        assembled_evidence=_active_tuzuk_evidence(),
        trace_payload=_legacy_mulga_trace(),
    )

    assert patch["split_temporal_policy_bucket"] == "active_non_mulga_preserve_family"
    assert patch["source_family_claimed"] == "TUZUK"
    assert patch["source_family_claimed"] != "MULGA"
    assert patch["s5_guard_type"] == "active_non_mulga_historical_surface_clamp"
    assert patch["s5_claim_family_preserved"] is True


def test_active_non_mulga_historical_surface_clamp_preserves_claim_identifier() -> None:
    _answer, patch = apply_temporal_claim_alignment(
        answer_text="Aktif tüzük cevabı.",
        answer_contract=_historical_contract(
            source_family_claimed="MULGA",
            source_identifier_claimed="MULGA m.4",
            effective_state_claimed="repealed",
            answer_mode="not_currently_applicable_answer",
        ),
        assembled_evidence=_active_tuzuk_evidence(),
        trace_payload=_legacy_mulga_trace(),
    )

    assert patch["source_identifier_claimed"] == "859727 m.4"
    assert patch["article_or_section_claimed"] == "madde:4"
    assert patch["s5_claim_identifier_preserved"] is True
    assert patch["s5_article_surface_preserved"] is True


def test_matching_active_repeal_proof_gets_mulga_historical_surface() -> None:
    evidence = [
        {
            "source_id": "20135150:20135150:m90:f0:from2013-07-01:to9999-12-31",
            "citation": "20135150 m.90/f.0",
            "source_identifier": "20135150 m.1",
            "source_title": "Tapu Sicili Tüzüğü",
            "source_family": "tuzuk",
            "article_or_section": "90",
            "effective_state": "active",
            "quoted_or_extracted_span": (
                "18/5/1994 tarihli Tapu Sicili Tüzüğü yürürlükten kaldırılmıştır."
            ),
        }
    ]

    answer, patch = apply_temporal_claim_alignment(
        answer_text="Aktif tüzük cevabı.",
        answer_contract=_historical_contract(
            source_family_claimed="MULGA",
            source_identifier_claimed="MULGA m.90",
            effective_state_claimed="repealed",
            answer_mode="not_currently_applicable_answer",
        ),
        assembled_evidence=evidence,
        trace_payload=_legacy_mulga_trace(),
    )

    assert patch["split_temporal_policy_bucket"] == "historical_repeal_proof_from_active_selected_source"
    assert patch["source_family_claimed"] == "MULGA"
    assert patch["effective_state_claimed"] == "repealed"
    assert patch["s5_guard_type"] == "mulga_historical_repeal_proof_guard"
    assert patch["s7m_historical_repeal_proof_contract_applied"] is True
    assert patch["s7m_historical_repeal_query_match"] is True
    assert "Mülga/hedef kaynak" in answer


def test_matching_legacy_khk_target_gets_mulga_historical_surface() -> None:
    evidence = [
        {
            "source_id": "555:555:m18:f0:from1995-06-27:to9999-12-31",
            "citation": "555 m.18/f.0",
            "source_identifier": "555 m.1",
            "source_title": "Coğrafi İşaretlerin Korunması Hakkında Kanun Hükmünde Kararname",
            "source_family": "khk",
            "article_or_section": "18",
            "effective_state": "active",
            "quoted_or_extracted_span": "Ticari markalarla ilişki ve eski KHK sistemindeki tescil sınırı.",
        }
    ]

    _answer, patch = apply_temporal_claim_alignment(
        answer_text="Aktif KHK cevabı.",
        answer_contract=_historical_contract(
            source_family_claimed="MULGA",
            source_identifier_claimed="555 m.18",
            effective_state_claimed="repealed",
            answer_mode="not_currently_applicable_answer",
        ),
        assembled_evidence=evidence,
        trace_payload={
            "question_raw": (
                "Marka, patent ve tasarım uyuşmazlığında 551/554/555/556 sayılı eski KHK'larla "
                "2026'da doğrudan hüküm kurmak neden risklidir?"
            ),
            "retrieval": {
                "source_family_resolution": {
                    "predicted_family": "khk",
                    "historical_or_repealed_question": True,
                    "historical_scope_detected": True,
                    "family_candidates": [
                        {
                            "family": "mulga_kanun",
                            "signals": ["legacy_source_risk_signal"],
                        }
                    ],
                },
                "article_span_selector": {
                    "legacy_intent_binding_active": True,
                    "legacy_candidate_preferred": False,
                },
            },
        },
    )

    assert patch["split_temporal_policy_bucket"] == "historical_repeal_proof_from_active_selected_source"
    assert patch["source_family_claimed"] == "MULGA"
    assert patch["effective_state_claimed"] == "repealed"
    assert patch["s5_guard_type"] == "mulga_historical_repeal_proof_guard"
    assert patch["s7m_historical_repeal_proof_reason"].startswith("active_selected_legacy_khk_target")


def test_historical_article_surface_preserved() -> None:
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
        answer_text="Tarihsel cevap.",
        answer_contract=_historical_contract(
            source_identifier_claimed="6570 m.2",
            article_or_section_claimed="madde:2",
            effective_state_claimed="active",
        ),
        assembled_evidence=evidence,
    )

    assert patch["source_identifier_claimed"] == "6570 m.gec1"
    assert patch["article_or_section_claimed"] == "geçici madde 1"
    assert patch["s5_guard_type"] == "historical_article_surface_guard"
    assert patch["s5_article_surface_preserved"] is True


def test_historical_surface_current_law_exception_preserves_active_current_identifier() -> None:
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
        },
        {
            "source_id": "TBK:6098:m344:f0:from2011-02-04:to9999-12-31",
            "citation": "TBK m.344/f.0",
            "source_identifier": "TBK m.1",
            "source_title": "Türk Borçlar Kanunu",
            "source_family": "kanun",
            "article_or_section": "344",
            "effective_state": "active",
            "quoted_or_extracted_span": "Kira bedeli artışında TÜFE on iki aylık ortalama sınırı uygulanır.",
        },
    ]

    answer, patch = apply_temporal_claim_alignment(
        answer_text="2026 güncel kira artış cevabı.",
        answer_contract=_historical_contract(
            source_family_claimed="MULGA",
            source_identifier_claimed="6570 m.gec1",
            effective_state_claimed="repealed",
            answer_mode="repealed_transition_answer",
        ),
        assembled_evidence=evidence,
        trace_payload={
            "question_raw": (
                "2026 kira artış sorusunda geçici yüzde yirmi beş sınırını hâlâ otomatik "
                "uygulamak neden güncellik hatasıdır?"
            ),
            "retrieval": {
                "source_family_resolution": {
                    "preferred_source_families": ["mulga_kanun", "kanun"],
                    "pre_filter_family_set": "kanun | mulga_kanun",
                    "reranked_family_set": "mulga_kanun | kanun",
                    "family_collision_pair": "kanun|mulga_kanun",
                }
            },
        },
    )

    assert patch["split_temporal_policy_bucket"] == "current_law_basis_exception_from_historical_surface"
    assert patch["source_family_claimed"] == "MULGA"
    assert patch["source_identifier_claimed"] == "6570 m.gec1"
    assert patch["article_or_section_claimed"] == "madde:344"
    assert patch["effective_state_claimed"] == "repealed"
    assert patch["current_law_basis_primary_allowed"] is False
    assert patch["mulga_dual_role_contract_applied"] is True
    assert patch["primary_historical_source_family"] == "MULGA"
    assert patch["primary_historical_source_identifier"] == "6570 m.gec1"
    assert patch["current_law_basis_family"] == "KANUN"
    assert patch["current_law_basis_identifier"] == "TBK m.344"
    assert patch["current_law_basis_article_or_section"] == "madde:344"
    assert patch["mulga_current_law_statement_required"] is True
    assert patch["mulga_current_law_statement_present"] is True
    assert patch["s5_guard_type"] == "mulga_dual_role_current_law_basis_guard"
    assert "TBK m.344" in answer
    assert "yüzde yirmi beş" in answer
    assert "TÜFE on iki aylık ortalama" in answer


def test_uy_claim_family_not_overwritten_by_generic_yonetmelik() -> None:
    evidence = [
        {
            "source_id": "kky:12420:m4:f0",
            "citation": "12420 m.4/f.0",
            "source_identifier": "12420 m.1",
            "source_title": "Savunma Araştırmaları Enstitüsü Yönetmeliği",
            "source_family": "kky",
            "article_or_section": "4",
            "effective_state": "active",
            "quoted_or_extracted_span": "Genel yönetmelik hükmü.",
        },
        {
            "source_id": "uy:24839:m7:f0",
            "citation": "24839 m.7/f.0",
            "source_identifier": "24839 m.1",
            "source_title": "Siirt Üniversitesi Ön Lisans ve Lisans Eğitim-Öğretim ve Sınav Yönetmeliği",
            "source_family": "uy",
            "article_or_section": "7",
            "effective_state": "active",
            "quoted_or_extracted_span": "Kayıt yenileme, ders kayıt koşulu ve kredi yükü düzenlenir.",
        },
    ]

    _answer, patch = apply_temporal_claim_alignment(
        answer_text="Üniversite yönetmeliği cevabı.",
        answer_contract={
            "answer_mode": "qualified_answer",
            "source_family_claimed": "YONETMELIK",
            "source_identifier_claimed": "12420 m.4",
            "article_or_section_claimed": "madde:4",
            "effective_state_claimed": "active",
        },
        assembled_evidence=evidence,
        trace_payload={
            "question_raw": (
                "Bir lisans öğrencisinin ders ekle-sil, kayıt yenileme ve dönemlik azami kredi yükü "
                "hangi üniversite yönetmeliğinde düzenlenir?"
            ),
            "retrieval": {
                "source_family_resolution": {
                    "preferred_source_families": ["uy"],
                    "pre_filter_family_set": "yonetmelik | uy",
                    "reranked_family_set": "yonetmelik | uy",
                    "family_collision_pair": "uy|yonetmelik",
                }
            },
        },
    )

    assert patch["source_family_claimed"] == "UY"
    assert patch["source_identifier_claimed"] == "24839 m.7"
    assert patch["s5_guard_type"] == "uy_yonetmelik_family_boundary_guard"
    assert patch["s5_claim_family_preserved"] is True


def test_teblig_claim_family_not_overwritten_by_mulga() -> None:
    _answer, patch = apply_temporal_claim_alignment(
        answer_text="Aktif tebliğ cevabı.",
        answer_contract=_historical_contract(
            source_family_claimed="MULGA",
            source_identifier_claimed="MULGA m.13",
            effective_state_claimed="repealed",
            answer_mode="not_currently_applicable_answer",
        ),
        assembled_evidence=_active_teblig_evidence(),
        trace_payload=_legacy_mulga_trace(),
    )

    assert patch["source_family_claimed"] == "TEBLIGLER"
    assert patch["source_identifier_claimed"] == "23093 m.13"
    assert patch["s5_guard_type"] == "teblig_domain_mismatch_guard"
    assert patch["s5_claim_family_preserved"] is True


def test_supporting_temporal_note_does_not_overwrite_primary_claim() -> None:
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
    assert patch.get("source_family_claimed", "TEBLIGLER") == "TEBLIGLER"


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


def test_current_law_basis_is_support_unless_current_only() -> None:
    _answer, patch = apply_temporal_claim_alignment(
        answer_text="Tarihsel yönetmelik maddesi.",
        answer_contract=_historical_contract(answer_mode="historical_repealed_answer"),
        assembled_evidence=_historical_chain_evidence(),
        trace_payload={
            "question_raw": "2012 tarihli disiplin yönetmeliğinin 22. maddesindeki tarihsel kural neydi?"
        },
    )

    assert patch["split_temporal_policy_bucket"] == "relation_chain_historical_three_part_claim"
    assert patch["current_law_basis_primary_allowed"] is False
    assert patch["temporal_claim_current_basis_identifier"] == "2547 m.54"
    assert patch["source_identifier_claimed"] == "12345 m.22"


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


def test_no_qid_specific_split_temporal_policy() -> None:
    _answer, patch = apply_temporal_claim_alignment(
        answer_text="Aktif kanun cevabı.",
        answer_contract=_historical_contract(
            qid="RANDOM-NATURAL-LANGUAGE-CASE",
            source_family_claimed="MULGA",
            effective_state_claimed="repealed",
            answer_mode="repealed_transition_answer",
        ),
        assembled_evidence=_active_kanun_evidence(),
        trace_payload=_active_preservation_trace(),
    )

    assert patch["split_temporal_policy_bucket"] == "active_non_mulga_preserve_family"
    assert patch["source_family_claimed"] == "KANUN"
    assert "RANDOM-NATURAL-LANGUAGE-CASE" not in patch["split_temporal_policy_reason"]


def test_no_qid_specific_s5_rules() -> None:
    _answer, patch = apply_temporal_claim_alignment(
        answer_text="Aktif tüzük cevabı.",
        answer_contract=_historical_contract(
            qid="TUZUK-04",
            source_family_claimed="MULGA",
            source_identifier_claimed="MULGA m.4",
            effective_state_claimed="repealed",
            answer_mode="not_currently_applicable_answer",
        ),
        assembled_evidence=_active_tuzuk_evidence(),
        trace_payload=_legacy_mulga_trace(),
    )

    assert patch["s5_family_identifier_guard_applied"] is True
    assert patch["s5_guard_type"] == "active_non_mulga_historical_surface_clamp"
    assert "TUZUK-04" not in patch["s5_guard_reason"]


def test_public_contract_always_exposes_split_temporal_policy_fields() -> None:
    sanitized = sanitize_public_answer_contract(
        {
            "final_mode": "answer",
            "source_family_claimed": "YONETMELIK",
            "effective_state_claimed": "active",
        }
    )

    assert sanitized is not None
    assert sanitized["split_temporal_policy_applied"] is False
    assert sanitized["split_temporal_policy_bucket"] == "not_applicable"
    assert sanitized["split_temporal_policy_reason"] == "not_evaluated"
    assert sanitized["claim_family_rewrite_allowed"] is False
    assert sanitized["claim_identifier_rewrite_allowed"] is False
    assert sanitized["historical_claim_surface_allowed"] is False
    assert sanitized["temporal_support_only"] is True
    assert sanitized["s5_family_identifier_guard_applied"] is False
    assert sanitized["s5_guard_type"] == "not_applicable"
    assert sanitized["s5_guard_reason"] == "not_evaluated"
    assert sanitized["mulga_dual_role_contract_applied"] is False
    assert sanitized["s7m_historical_repeal_proof_contract_applied"] is False


def test_s7m_mulga_dual_role_policy_has_no_qid_specific_runtime_branch() -> None:
    source = Path(__file__).resolve().parents[1] / "src" / "rag" / "answer_synthesis.py"

    assert "MULGA-05" not in source.read_text(encoding="utf-8")


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
