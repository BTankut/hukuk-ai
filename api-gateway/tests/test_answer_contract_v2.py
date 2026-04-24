from __future__ import annotations

from answer_contract_v2 import build_or_repair_answer_contract, controlled_fallback_answer


def test_repair_selects_partial_identifier_evidence_before_first_fallback():
    result = build_or_repair_answer_contract(
        qid="KANUN-01",
        answer_text="İşe iade şartı İş Kanunu m.18'e dayanır. [Kaynak: IK m.18]",
        citations=["IK m.18"],
        answer_contract={
            "answer_text": "İşe iade şartı İş Kanunu m.18'e dayanır. [Kaynak: IK m.18]",
            "primary_source_id": "IK m.18",
            "source_validity": "active",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "target_date": "2026-04-21",
            "assembled_evidence": [
                {
                    "source_id": "24083:24083:m20:f0",
                    "citation": "24083 m.20/f.0",
                    "source_title": "Türkiye İnsan Hakları ve Eşitlik Kurumunda Sözleşmeli Personel Usul ve Esasları",
                    "source_family": "teblig",
                    "source_identifier": "24083 m.20",
                    "article_or_section": "20",
                    "effective_state": "active",
                },
                {
                    "source_id": "IK:4857:m18:f0:from1900-01-01:to9999-12-31",
                    "citation": "IK m.18/f.0",
                    "source_title": "İŞ KANUNU",
                    "source_family": "kanun",
                    "source_identifier": "IK m.18",
                    "article_or_section": "18",
                    "effective_state": "active",
                },
            ],
        },
    )

    contract = result.contract
    assert contract["source_family_claimed"] == "KANUN"
    assert contract["source_identifier_claimed"] == "IK m.18"
    assert contract["source_title_claimed"] == "İŞ KANUNU"
    assert contract["article_or_section_claimed"] == "madde:18"
    assert "same_evidence_identifier_mismatch" not in contract["verification_findings"]


def test_repair_does_not_match_short_law_abbreviation_as_source_identifier():
    result = build_or_repair_answer_contract(
        qid="TBK-PARTIAL",
        answer_text="Bildirim süresi TBK m.432'de düzenlenir. [Kaynak: TBK m.432]",
        citations=["TBK m.432"],
        answer_contract={
            "answer_text": "Bildirim süresi TBK m.432'de düzenlenir. [Kaynak: TBK m.432]",
            "primary_source_id": "TBK m.432",
            "source_validity": "active",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "assembled_evidence": [
                {
                    "source_id": "TBK:6098:m438:f0",
                    "citation": "TBK m.438/f.0",
                    "source_title": "TÜRK BORÇLAR KANUNU",
                    "source_family": "kanun",
                    "source_identifier": "TBK m.438",
                    "law_short_name": "TBK",
                    "article_or_section": "438",
                    "effective_state": "active",
                },
                {
                    "source_id": "TBK:6098:m432:f0",
                    "citation": "TBK m.432/f.0",
                    "source_title": "TÜRK BORÇLAR KANUNU",
                    "source_family": "kanun",
                    "source_identifier": "TBK m.432",
                    "law_short_name": "TBK",
                    "article_or_section": "432",
                    "effective_state": "active",
                },
            ],
        },
    )

    contract = result.contract
    assert contract["source_identifier_claimed"] == "TBK m.432"
    assert contract["article_or_section_claimed"] == "madde:432"
    assert "same_evidence_article_mismatch" not in contract["verification_findings"]


def test_repair_uses_mapped_evidence_family_when_predicted_family_is_strong():
    result = build_or_repair_answer_contract(
        qid="YON-MAPPED",
        answer_text="Mesafeli sözleşmeler için ilgili yönetmelik uygulanır. [Kaynak: 20237 m.1]",
        citations=["20237 m.1"],
        answer_contract={
            "answer_text": "Mesafeli sözleşmeler için ilgili yönetmelik uygulanır. [Kaynak: 20237 m.1]",
            "primary_source_id": "20237 m.1",
            "source_validity": "active",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "retrieval": {
                "source_family_resolution": {
                    "predicted_family": "yonetmelik",
                    "family_confidence": 0.86,
                },
            },
            "assembled_evidence": [
                {
                    "source_id": "20237:20237:m1:f0",
                    "citation": "20237 m.1/f.0",
                    "source_title": "MESAFELİ SÖZLEŞMELER YÖNETMELİĞİ",
                    "source_family": "kky",
                    "source_family_canonical": "kky",
                    "source_family_mapped": "yonetmelik",
                    "source_identifier": "20237 m.1",
                    "article_or_section": "1",
                    "effective_state": "active",
                },
            ],
        },
    )

    assert result.contract["source_family_claimed"] == "YONETMELIK"


def test_repair_prefers_specific_mapped_family_over_generic_selected_evidence_family():
    result = build_or_repair_answer_contract(
        qid="KKY-MAPPED",
        answer_text="Uzaktan müşteri edinme bakımından ilgili kurum yönetmeliği uygulanır. [Kaynak: 38568 m.1]",
        citations=["38568 m.1"],
        answer_contract={
            "answer_text": "Uzaktan müşteri edinme bakımından ilgili kurum yönetmeliği uygulanır. [Kaynak: 38568 m.1]",
            "primary_source_id": "38568 m.1",
            "source_validity": "active",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "retrieval": {
                "source_family_resolution": {
                    "predicted_family": "yonetmelik",
                    "family_confidence": 0.82,
                },
                "article_span_selector": {
                    "requested_source_families": ["kky", "yonetmelik", "cb_yonetmelik", "uy"],
                    "preferred_source_families": ["kky"],
                },
            },
            "assembled_evidence": [
                {
                    "source_id": "38568:38568:m1:f0",
                    "citation": "38568 m.1/f.0",
                    "source_title": "UZAKTAN KİMLİK TESPİTİ YÖNETMELİĞİ",
                    "source_family": "yonetmelik",
                    "source_family_canonical": "yonetmelik",
                    "source_family_mapped": "kky",
                    "source_identifier": "38568 m.1",
                    "article_or_section": "1",
                    "effective_state": "active",
                },
            ],
        },
    )

    assert result.contract["source_family_claimed"] == "KKY"


def test_repair_replacement_guard_blocks_identifier_rewrite_from_selected_evidence():
    result = build_or_repair_answer_contract(
        qid="GUARD-01",
        answer_text="İlgili karar uygulanır. [Kaynak: 3350 m.1]",
        citations=["3350 m.1"],
        answer_contract={
            "answer_text": "İlgili karar uygulanır. [Kaynak: 3350 m.1]",
            "primary_source_id": "1901",
            "source_identifier_claimed": "1901",
            "source_validity": "active",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "retrieval": {
                "source_identity_reranker": {
                    "title_match_type": "weak_overlap",
                    "document_identity_score": 72.0,
                    "replacement_guard_triggered": True,
                }
            },
            "assembled_evidence": [
                {
                    "source_id": "3350:3350:m1:f0",
                    "citation": "3350 m.1/f.0",
                    "source_title": "İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350)",
                    "source_family": "cb_karar",
                    "source_identifier": "3350 m.1",
                    "article_or_section": "1",
                    "effective_state": "active",
                },
            ],
        },
    )

    assert result.contract["identifier_integrity_status"] == "unverified_claim_suppressed"
    assert "claimed_identifier_replaced_by_selected_evidence" not in result.contract["verification_findings"]


def test_repair_does_not_treat_article_number_as_source_identity():
    result = build_or_repair_answer_contract(
        qid="ARTICLE-ONLY-MISMATCH",
        answer_text="İtiraz usulü IK m.20'de düzenlenir. [Kaynak: IK m.20]",
        citations=["IK m.20", "TBK m.432"],
        answer_contract={
            "answer_text": "İtiraz usulü IK m.20'de düzenlenir. [Kaynak: IK m.20]",
            "primary_source_id": "IK m.20",
            "source_validity": "active",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "assembled_evidence": [
                {
                    "source_id": "24083:24083:m20:f0",
                    "citation": "24083 m.20/f.0",
                    "source_title": "Türkiye İnsan Hakları ve Eşitlik Kurumunda Sözleşmeli Personel Usul ve Esasları",
                    "source_family": "teblig",
                    "source_identifier": "24083 m.20",
                    "article_or_section": "20",
                    "effective_state": "active",
                },
                {
                    "source_id": "TBK:6098:m432:f0",
                    "citation": "TBK m.432/f.0",
                    "source_title": "TÜRK BORÇLAR KANUNU",
                    "source_family": "kanun",
                    "source_identifier": "TBK m.432",
                    "article_or_section": "432",
                    "effective_state": "active",
                },
            ],
        },
    )

    contract = result.contract
    assert contract["source_identifier_claimed"] == "unknown"
    assert contract["article_or_section_claimed"] == "madde:20"
    assert contract["identifier_integrity_status"] == "unverified_claim_suppressed"
    assert "claimed_identifier_suppressed" in contract["verification_findings"]
    assert "same_evidence_identifier_mismatch" in contract["verification_findings"]


def test_repair_uses_strong_family_routed_evidence_over_off_family_model_citation():
    result = build_or_repair_answer_contract(
        qid="CBG-FAMILY-OVERRIDE",
        answer_text="Yanıt yanlışlıkla tebliğe atıf yaptı. [Kaynak: 22980 m.7]",
        citations=["22980 m.7"],
        answer_contract={
            "answer_text": "Yanıt yanlışlıkla tebliğe atıf yaptı. [Kaynak: 22980 m.7]",
            "primary_source_id": "22980 m.7",
            "source_validity": "active",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "retrieval": {
                "source_family_resolution": {
                    "predicted_family": "cb_genelge",
                    "family_confidence": 0.86,
                }
            },
            "assembled_evidence": [
                {
                    "source_id": "22980:22980:m7:f0",
                    "citation": "22980 m.7/f.0",
                    "source_title": "MİLLİ EMLAK GENEL TEBLİĞİ (SIRA NO: 375)",
                    "source_family": "teblig",
                    "source_identifier": "22980 m.7",
                    "article_or_section": "7",
                    "effective_state": "active",
                },
                {
                    "source_id": "14:14:m0:f0",
                    "citation": "14 m.0/f.0",
                    "source_title": "Rehberlik, Teftiş ve Denetim Faaliyetlerinin Düzenli ve Etkin Bir Şekilde Yerine Getirilmesi ile İlgili",
                    "source_family": "cb_genelge",
                    "source_identifier": "14 m.0",
                    "article_or_section": "0",
                    "effective_state": "active",
                },
            ],
        },
    )

    contract = result.contract
    assert contract["source_family_claimed"] == "CB_GENELGE"
    assert contract["source_identifier_claimed"] == "14 m.0"
    assert contract["source_title_claimed"].startswith("Rehberlik")
    assert "predicted_family_overrode_model_source" in contract["verification_findings"]


def test_repair_adds_phase2_contract_fields_for_grounded_answer():
    result = build_or_repair_answer_contract(
        qid="KANUN-01",
        answer_text="Fesih bildirimi yazili yapilmalidir. [Kaynak: IK m.18]",
        citations=["IK m.18"],
        answer_contract={
            "answer_text": "Fesih bildirimi yazili yapilmalidir. [Kaynak: IK m.18]",
            "primary_source_id": "IK m.18",
            "source_validity": "active",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "target_date": "2026-04-21",
            "assembled_evidence": [
                {
                    "source_id": "IK m.18",
                    "citation": "IK m.18",
                    "source_title": "4857 sayili Is Kanunu",
                    "belge_turu": "KANUN",
                    "madde_no": "18",
                    "mulga": False,
                    "yururluk_bitis": "9999-12-31",
                }
            ],
        },
    )

    contract = result.contract
    assert contract["qid"] == "KANUN-01"
    assert contract["confidence_0_100"] >= 70
    assert contract["answer_mode"] == "direct_answer"
    assert contract["grounding_status"] == "fully_grounded"
    assert contract["source_family_claimed"] == "KANUN"
    assert contract["article_or_section_claimed"] == "madde:18"
    assert contract["needs_manual_review"] is False
    assert result.validation["contract_valid"] is True
    assert result.validation["confidence_policy_ok"] is True


def test_repair_degrades_unsupported_confident_shape_to_not_grounded_band():
    result = build_or_repair_answer_contract(
        qid="Q2",
        answer_text="Kesin olarak cevap budur.",
        citations=[],
        answer_contract={"answer_text": "Kesin olarak cevap budur.", "final_mode": "answer"},
        final_mode="answer",
        final_reason=None,
    )

    contract = result.contract
    assert contract["grounding_status"] == "not_grounded"
    assert contract["answer_mode"] == "insufficient_grounding"
    assert contract["confidence_0_100"] <= 39
    assert contract["needs_manual_review"] is True
    assert result.validation["unsupported_confident_answer"] is False


def test_repair_qualifies_fully_grounded_answer_when_runtime_slots_are_partial():
    result = build_or_repair_answer_contract(
        qid="PHASE15A-PARTIAL-SLOTS",
        answer_text="Fesih bildirimi yazili yapilmalidir. [Kaynak: IK m.18]",
        citations=["IK m.18"],
        answer_contract={
            "answer_text": "Fesih bildirimi yazili yapilmalidir. [Kaynak: IK m.18]",
            "primary_source_id": "IK m.18",
            "source_validity": "active",
            "final_mode": "answer",
            "required_fact_coverage_score": 0.82,
            "candidate_completeness_score": 0.9,
            "minimum_answer_facts_present": False,
            "missing_fact_slots": ["procedure_or_consequence"],
            "rubric_aligned_completeness_class": "structurally_full_but_legally_misaligned",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "target_date": "2026-04-21",
            "retrieval": {
                "article_span_selector": {
                    "selector_evidence_sufficiency": "exact_enough",
                    "support_span_count": 2,
                }
            },
            "assembled_evidence": [
                {
                    "source_id": "IK m.18",
                    "citation": "IK m.18",
                    "source_title": "4857 sayili Is Kanunu",
                    "belge_turu": "KANUN",
                    "madde_no": "18",
                    "mulga": False,
                    "yururluk_bitis": "9999-12-31",
                }
            ],
        },
    )

    contract = result.contract
    assert contract["grounding_status"] == "partially_grounded"
    assert contract["answer_mode"] == "qualified_answer"
    assert contract["confidence_0_100"] < 70
    assert contract["needs_manual_review"] is True
    assert contract["confidence_policy_adjusted"] is True
    assert "required_fact_coverage_below_0_95" in contract["confidence_policy_adjustment_reasons"]
    assert "minimum_answer_facts_missing" in contract["confidence_policy_adjustment_reasons"]
    assert result.validation["unsupported_confident_answer"] is False


def test_repair_marks_cross_family_evidence_conflict_as_partial():
    result = build_or_repair_answer_contract(
        qid="CBKAR-TEST",
        answer_text="Bu belge kanun olarak uygulanır. [Kaynak: 3350 m.5]",
        citations=["3350 m.5"],
        answer_contract={
            "answer_text": "Bu belge kanun olarak uygulanır. [Kaynak: 3350 m.5]",
            "primary_source_id": "3350 m.5",
            "source_family_claimed": "KANUN",
            "source_identifier_claimed": "3350 m.5",
            "source_validity": "active",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "target_date": "2026-04-21",
            "query_signals": {
                "source_family_resolution": {
                    "predicted_family": "cb_karar",
                    "family_confidence": 0.86,
                }
            },
            "retrieval": {
                "retrieval_verification_features": {
                    "cross_family_conflict_flag": True,
                }
            },
            "assembled_evidence": [
                {
                    "source_id": "3350:3350:m5:f0:from1900-01-01:to9999-12-31",
                    "citation": "3350 m.5/f.0",
                    "source_title": "İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350)",
                    "belge_turu": "cb_karar",
                    "madde_no": "5",
                    "mulga": False,
                    "yururluk_bitis": "9999-12-31",
                }
            ],
        },
    )

    contract = result.contract
    assert contract["source_family_claimed"] == "CB_KARAR"
    assert contract["grounding_status"] == "partially_grounded"
    assert contract["confidence_0_100"] < 70
    assert contract["needs_manual_review"] is True
    assert "cross_family_evidence_conflict" in contract["verification_findings"]


def test_repair_flags_same_evidence_identifier_and_article_mismatch():
    result = build_or_repair_answer_contract(
        qid="PHASE4-SAME-EVIDENCE",
        answer_text="Bu sonuç 9999 sayılı metnin 12. maddesine dayanır. [Kaynak: 9999 m.12]",
        citations=["9999 m.12"],
        answer_contract={
            "answer_text": "Bu sonuç 9999 sayılı metnin 12. maddesine dayanır. [Kaynak: 9999 m.12]",
            "primary_source_id": "9999 m.12",
            "source_family_claimed": "KANUN",
            "source_identifier_claimed": "9999 m.12",
            "article_or_section_claimed": "madde:12",
            "source_validity": "active",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "assembled_evidence": [
                {
                    "source_id": "40969:m27:f0",
                    "citation": "40969 m.27/f.0",
                    "source_family": "uy",
                    "source_identifier": "40969 m.27",
                    "source_title": "KIRKLARELİ ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ",
                    "article_or_section": "27",
                    "effective_state": "active",
                    "quoted_or_extracted_span": "Tez danışmanı atanmasına ilişkin kural.",
                }
            ],
        },
    )

    contract = result.contract
    assert contract["grounding_status"] == "partially_grounded"
    assert contract["confidence_0_100"] < 70
    assert contract["needs_manual_review"] is True
    assert "same_evidence_family_mismatch" in contract["verification_findings"]
    assert "same_evidence_identifier_mismatch" in contract["verification_findings"]
    assert "same_evidence_article_mismatch" in contract["verification_findings"]


def test_repair_accepts_phase4_canonical_same_evidence_fields():
    result = build_or_repair_answer_contract(
        qid="PHASE4-GROUNDED",
        answer_text="Tez danışmanı atanması yönetmelik m.27'de düzenlenir. [Kaynak: 40969 m.27]",
        citations=["40969 m.27"],
        answer_contract={
            "answer_text": "Tez danışmanı atanması yönetmelik m.27'de düzenlenir. [Kaynak: 40969 m.27]",
            "primary_source_id": "40969 m.27",
            "source_family_claimed": "UY",
            "source_title_claimed": "Kırklareli Üniversitesi Lisansüstü Eğitim ve Öğretim Yönetmeliği",
            "source_identifier_claimed": "40969 m.27",
            "article_or_section_claimed": "madde:27",
            "source_validity": "active",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "assembled_evidence": [
                {
                    "source_id": "40969:m27:f0",
                    "citation": "40969 m.27/f.0",
                    "source_family": "uy",
                    "source_identifier": "40969 m.27",
                    "source_title": "KIRKLARELİ ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ",
                    "article_or_section": "27",
                    "effective_state": "active",
                    "quoted_or_extracted_span": "Tez danışmanı atanmasına ilişkin kural.",
                }
            ],
        },
    )

    contract = result.contract
    assert contract["grounding_status"] == "fully_grounded"
    assert contract["needs_manual_review"] is False
    assert contract["verification_findings"] == []


def test_repair_treats_generic_yonetmelik_and_uy_as_compatible_specificity():
    result = build_or_repair_answer_contract(
        qid="PHASE8C-FAMILY-COMPAT",
        answer_text="Tez danışmanı yönetmelik m.27'de düzenlenir. [Kaynak: 40969 m.27]",
        citations=["40969 m.27"],
        answer_contract={
            "answer_text": "Tez danışmanı yönetmelik m.27'de düzenlenir. [Kaynak: 40969 m.27]",
            "source_family_claimed": "YONETMELIK",
            "source_identifier_claimed": "40969 m.27",
            "article_or_section_claimed": "madde:27",
            "source_validity": "active",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "assembled_evidence": [
                {
                    "source_id": "40969:m27:f0",
                    "citation": "40969 m.27/f.0",
                    "source_family": "uy",
                    "source_identifier": "40969 m.27",
                    "source_title": "KIRKLARELİ ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ",
                    "article_or_section": "27",
                    "effective_state": "active",
                }
            ],
        },
    )

    contract = result.contract
    assert contract["source_family_claimed"] == "UY"
    assert contract["family_compatibility_status"] == "generic_specific_compatible"
    assert "family_compatibility_failed" not in contract["verification_findings"]
    assert contract["grounding_status"] == "fully_grounded"


def test_repair_replaces_mismatched_identifier_when_selector_evidence_is_authoritative():
    result = build_or_repair_answer_contract(
        qid="PHASE8C-ID-INTEGRITY",
        answer_text="Tez danışmanı 9999 sayılı metne göre düzenlenir. [Kaynak: 9999 m.12]",
        citations=["9999 m.12"],
        answer_contract={
            "answer_text": "Tez danışmanı 9999 sayılı metne göre düzenlenir. [Kaynak: 9999 m.12]",
            "source_family_claimed": "UY",
            "source_identifier_claimed": "9999 m.12",
            "article_or_section_claimed": "madde:12",
            "source_validity": "active",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "retrieval": {
                "article_span_selector": {
                    "selected_document_id": "40969",
                    "selected_article": "27",
                    "selector_evidence_sufficiency": "exact_enough",
                    "metadata_identity_strength": "strong",
                    "selector_exact_article_hit": True,
                    "support_span_count": 2,
                    "article_match_type": "exact",
                    "temporal_state_resolved": True,
                }
            },
            "assembled_evidence": [
                {
                    "source_id": "40969:m27:f0",
                    "citation": "40969 m.27/f.0",
                    "source_family": "uy",
                    "source_identifier": "40969 m.27",
                    "source_title": "KIRKLARELİ ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ",
                    "article_or_section": "27",
                    "effective_state": "active",
                }
            ],
        },
    )

    contract = result.contract
    assert contract["source_identifier_claimed"] == "40969 m.27"
    assert contract["identifier_integrity_status"] == "replaced_by_selected_evidence"
    assert contract["grounding_status"] == "partially_grounded"
    assert contract["confidence_0_100"] < 70
    assert "claimed_identifier_replaced_by_selected_evidence" in contract["verification_findings"]


def test_repair_suppresses_selected_identifier_without_query_or_identity_anchor():
    result = build_or_repair_answer_contract(
        qid="PHASE10D-ID-SUPPRESS",
        answer_text="Başvuru usulü kaynakta açıklanır. [Kaynak: 40969 m.27]",
        citations=["40969 m.27"],
        answer_contract={
            "answer_text": "Başvuru usulü kaynakta açıklanır. [Kaynak: 40969 m.27]",
            "source_family_claimed": "UY",
            "article_or_section_claimed": "madde:27",
            "source_validity": "active",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "question_raw": "Başvuru usulü nedir?",
            "retrieval": {
                "source_identity_reranker": {
                    "document_identity_score": 30,
                    "title_match_type": "none",
                    "identifier_match_type": "not_requested",
                }
            },
            "assembled_evidence": [
                {
                    "source_id": "40969:m27:f0",
                    "citation": "40969 m.27/f.0",
                    "source_family": "uy",
                    "source_identifier": "40969 m.27",
                    "source_title": "KIRKLARELİ ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ",
                    "article_or_section": "27",
                    "effective_state": "active",
                }
            ],
        },
    )

    contract = result.contract
    assert contract["source_identifier_claimed"] == "unknown"
    assert contract["identifier_integrity_status"] == "selected_evidence_identifier_suppressed"
    assert "selected_identifier_suppressed_without_query_anchor" in contract["verification_findings"]


def test_repair_trusts_selector_exact_identifier_for_natural_language_question():
    result = build_or_repair_answer_contract(
        qid="KANUN-01-NATURAL",
        answer_text="İşe iade güvencesi İş Kanunu m.18 kapsamında değerlendirilir. [Kaynak: IK m.18]",
        citations=["IK m.18", "IK m.20", "IK m.21"],
        answer_contract={
            "answer_text": "İşe iade güvencesi İş Kanunu m.18 kapsamında değerlendirilir. [Kaynak: IK m.18]",
            "primary_source_id": "IK m.18",
            "source_validity": "active",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "question_raw": (
                "42 çalışanlı bir işyerinde 8 aylık kıdemi bulunan işçi performans gerekçesiyle çıkarılırsa "
                "işe iade davası açabilir mi?"
            ),
            "retrieval": {
                "source_identity_reranker": {
                    "document_identity_score": 59.9,
                    "title_match_type": "none",
                    "identifier_match_type": "not_requested",
                    "replacement_guard_triggered": True,
                },
                "article_span_selector": {
                    "selected_document_id": "İŞ KANUNU",
                    "selected_article": "18",
                    "selector_document_rank": 1,
                    "selector_exact_article_hit": True,
                    "selector_evidence_sufficiency": "exact_enough",
                    "metadata_identity_strength": "medium",
                    "support_span_count": 1,
                    "selector_support_span_count": 1,
                    "article_match_type": "source_local_support",
                    "scenario_current_law_question": True,
                    "temporal_state_resolved": True,
                    "query_article_tokens": [],
                },
            },
            "assembled_evidence": [
                {
                    "source_id": "IK:4857:m18:f0:from1900-01-01:to9999-12-31",
                    "citation": "IK m.18/f.0",
                    "source_title": "İŞ KANUNU",
                    "source_family": "kanun",
                    "source_identifier": "IK m.18",
                    "article_or_section": "18",
                    "effective_state": "active",
                    "quoted_or_extracted_span": "Otuz veya daha fazla işçi çalıştıran işyerlerinde en az altı aylık kıdemi olan işçi işe iade korumasından yararlanır.",
                }
            ],
        },
    )

    contract = result.contract
    assert contract["source_identifier_claimed"] == "IK m.18"
    assert contract["identifier_integrity_status"] == "exact"
    assert contract["grounding_status"] == "fully_grounded"
    assert contract["answer_mode"] == "direct_answer"
    assert contract["answer_suppressed_due_to_evidence_gap"] is False
    assert "selected_identifier_suppressed_without_query_anchor" not in contract["verification_findings"]
    assert "support_insufficient_for_specific_claim" not in contract["verification_findings"]
    assert contract["needs_manual_review"] is False


def test_repair_uses_phase6_selector_insufficient_support_as_confidence_ceiling():
    result = build_or_repair_answer_contract(
        qid="PHASE6-SELECTOR",
        answer_text="Tez danışmanı madde 12'de düzenlenir. [Kaynak: 2547 m.12]",
        citations=["2547 m.12"],
        answer_contract={
            "answer_text": "Tez danışmanı madde 12'de düzenlenir. [Kaynak: 2547 m.12]",
            "primary_source_id": "2547 m.12",
            "source_family_claimed": "KANUN",
            "source_identifier_claimed": "2547 m.12",
            "article_or_section_claimed": "madde:12",
            "source_validity": "active",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "retrieval": {
                "article_span_selector": {
                    "selector_evidence_sufficiency": "insufficient_support",
                    "metadata_identity_strength": "weak",
                    "manual_review_trigger_reason": "insufficient_selector_support",
                }
            },
            "assembled_evidence": [
                {
                    "source_id": "2547:m12:f0",
                    "citation": "2547 m.12/f.0",
                    "source_family": "kanun",
                    "source_identifier": "2547 m.12",
                    "source_title": "YÜKSEKÖĞRETİM KANUNU",
                    "article_or_section": "12",
                    "effective_state": "active",
                    "quoted_or_extracted_span": "Genel kanun hükmü.",
                }
            ],
        },
    )

    contract = result.contract
    assert contract["grounding_status"] == "not_grounded"
    assert contract["confidence_0_100"] < 40
    assert contract["needs_manual_review"] is True
    assert contract["answer_suppressed_due_to_evidence_gap"] is True
    assert "selector_insufficient_support" in contract["verification_findings"]
    assert "selector_insufficient_selector_support" in contract["verification_findings"]


def test_repair_suppresses_answer_when_article_lock_fails_for_specific_claim():
    result = build_or_repair_answer_contract(
        qid="PHASE7-ARTICLE-LOCK",
        answer_text="Tez danışmanı kesin olarak madde 12'de düzenlenir. [Kaynak: 2547 m.12]",
        citations=["2547 m.12"],
        answer_contract={
            "answer_text": "Tez danışmanı kesin olarak madde 12'de düzenlenir. [Kaynak: 2547 m.12]",
            "primary_source_id": "2547 m.12",
            "source_family_claimed": "KANUN",
            "source_identifier_claimed": "2547 m.12",
            "article_or_section_claimed": "madde:12",
            "source_validity": "active",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "retrieval": {
                "article_span_selector": {
                    "query_article_tokens": ["12"],
                    "selector_exact_article_hit": False,
                    "selector_support_span_count": 1,
                    "support_span_count": 1,
                    "selector_evidence_sufficiency": "insufficient_support",
                    "metadata_identity_strength": "weak",
                    "article_match_type": "source_local_support",
                    "manual_review_trigger_reason": "article_span_not_found",
                    "temporal_state_resolved": False,
                }
            },
            "target_date": "current",
            "assembled_evidence": [
                {
                    "source_id": "2547:m9:f0",
                    "citation": "2547 m.9/f.0",
                    "source_family": "kanun",
                    "source_identifier": "2547 m.9",
                    "source_title": "YÜKSEKÖĞRETİM KANUNU",
                    "article_or_section": "9",
                    "effective_state": "active",
                    "quoted_or_extracted_span": "Genel kanun hükmü.",
                }
            ],
        },
    )

    contract = result.contract
    assert contract["grounding_status"] == "not_grounded"
    assert contract["answer_mode"] == "insufficient_grounding"
    assert contract["confidence_0_100"] < 40
    assert contract["article_lock_failed"] is True
    assert contract["support_insufficient_for_specific_claim"] is True
    assert contract["temporal_clause_missing"] is True
    assert contract["answer_suppressed_due_to_evidence_gap"] is True
    assert contract["unsupported_reason"] == "evidence_gap"
    assert "answer_suppressed_due_to_evidence_gap" in contract["verification_findings"]
    assert contract["answer_text"].startswith("Bu soruya mevcut kaynaklarla tam destekli")


def test_repair_marks_legacy_khk_query_as_repealed_mulga_family():
    result = build_or_repair_answer_contract(
        qid="MULGA-04",
        answer_text="551 sayılı eski KHK'larla 2026'da doğrudan hüküm kurmak risklidir. [Kaynak: 551 m.1]",
        citations=["551 m.1"],
        answer_contract={
            "answer_text": "551 sayılı eski KHK'larla 2026'da doğrudan hüküm kurmak risklidir. [Kaynak: 551 m.1]",
            "primary_source_id": "551 m.1",
            "source_validity": "active",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "question_raw": "Marka ve patent uyuşmazlığında 551 sayılı eski KHK'larla 2026'da hüküm kurmak neden risklidir?",
            "retrieval": {
                "source_family_resolution": {
                    "historical_or_repealed_question": True,
                    "historical_scope_detected": True,
                    "repealed_scope_detected": True,
                },
                "article_span_selector": {
                    "legacy_intent_binding_active": True,
                    "legacy_candidate_preferred": True,
                    "document_state_binding_reason": "legacy_scope_candidate_preferred",
                },
            },
            "assembled_evidence": [
                {
                    "source_id": "551:551:m1:f0:from1995-06-27:to9999-12-31",
                    "citation": "551 m.1/f.0",
                    "source_title": "PATENT HAKLARININ KORUNMASI HAKKINDA KANUN HÜKMÜNDE KARARNAME",
                    "source_family": "khk",
                    "source_identifier": "551 m.1",
                    "article_or_section": "1",
                    "effective_state": "active",
                }
            ],
        },
    )

    contract = result.contract
    assert contract["source_family_claimed"] == "MULGA"
    assert contract["effective_state_claimed"] == "repealed"
    assert contract["answer_mode"] == "not_currently_applicable_answer"


def test_legacy_suppressed_answer_keeps_temporal_answer_mode():
    result = build_or_repair_answer_contract(
        qid="MULGA-01",
        answer_text="Mülga öğrenci disiplin yönetmeliğine 2026'da doğrudan dayanmak güvenli değildir. [Kaynak: 2547 m.65]",
        citations=["2547 m.65"],
        answer_contract={
            "answer_text": "Mülga öğrenci disiplin yönetmeliğine 2026'da doğrudan dayanmak güvenli değildir. [Kaynak: 2547 m.65]",
            "primary_source_id": "2547 m.65",
            "source_validity": "repealed",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "question_raw": "Yükseköğretim öğrencisine disiplin cezası verilirken hâlâ mülga düzenlemeye dayanmak güvenli midir?",
            "retrieval": {
                "source_family_resolution": {
                    "predicted_family": "mulga_kanun",
                    "historical_or_repealed_question": True,
                    "historical_scope_detected": True,
                },
                "article_span_selector": {
                    "selector_evidence_sufficiency": "partially_supported",
                    "support_span_count": 1,
                    "support_insufficient_for_specific_claim": True,
                },
            },
            "assembled_evidence": [
                {
                    "source_id": "2547:65",
                    "citation": "2547 m.65",
                    "source_family": "mulga_kanun",
                    "source_identifier": "2547 m.65",
                    "article_or_section": "65",
                    "effective_state": "repealed",
                }
            ],
        },
    )

    contract = result.contract
    assert contract["grounding_status"] == "not_grounded"
    assert contract["answer_mode"] == "not_currently_applicable_answer"
    fallback = controlled_fallback_answer(contract)
    assert "bugün doğrudan güncel hüküm dayanağı" in fallback
    assert "mülga/tarihsel" in fallback
    assert "Mevcut rejim" in fallback


def test_repair_preserves_explicit_legacy_khk_family_when_query_is_bound_to_khk():
    result = build_or_repair_answer_contract(
        qid="KHK-03",
        answer_text="Geçiş bakımından önce 703 sayılı KHK, ardından ilgili CBK bağlantısı kontrol edilmelidir. [Kaynak: 703 m.1]",
        citations=["703 m.1"],
        answer_contract={
            "answer_text": "Geçiş bakımından önce 703 sayılı KHK, ardından ilgili CBK bağlantısı kontrol edilmelidir. [Kaynak: 703 m.1]",
            "primary_source_id": "703 m.1",
            "source_validity": "active",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "question_raw": "Mevzuat hâlâ Bakanlar Kurulu veya eski teşkilat isimlerine atıf yapıyorsa, Cumhurbaşkanlığı Hükümet Sistemine geçiş bakımından hangi KHK ve hangi CBK bağlantısı kontrol edilmelidir?",
            "retrieval": {
                "source_family_resolution": {
                    "predicted_family": "khk",
                    "preferred_families": ["khk"],
                    "historical_or_repealed_question": True,
                    "historical_scope_detected": True,
                    "repealed_scope_detected": False,
                },
                "article_span_selector": {
                    "legacy_intent_binding_active": True,
                    "legacy_candidate_preferred": True,
                    "preferred_source_families": ["khk"],
                    "document_state_binding_reason": "legacy_scope_candidate_preferred",
                },
            },
            "assembled_evidence": [
                {
                    "source_id": "703:703:m1:f0:from2018-07-09:to9999-12-31",
                    "citation": "703 m.1/f.0",
                    "source_title": "703 SAYILI KANUN HÜKMÜNDE KARARNAME",
                    "source_family": "khk",
                    "source_identifier": "703 m.1",
                    "article_or_section": "1",
                    "effective_state": "active",
                }
            ],
        },
    )

    contract = result.contract
    assert contract["source_family_claimed"] == "KHK"
    assert contract["effective_state_claimed"] == "repealed"


def test_repair_marks_legacy_tuzuk_query_as_repealed_when_old_year_is_explicit():
    result = build_or_repair_answer_contract(
        qid="MULGA-03",
        answer_text="1994 tarihli Tapu Sicili Tüzüğünü bugün doğrudan kullanmak hata üretir. [Kaynak: 20135150 m.90]",
        citations=["20135150 m.90"],
        answer_contract={
            "answer_text": "1994 tarihli Tapu Sicili Tüzüğünü bugün doğrudan kullanmak hata üretir. [Kaynak: 20135150 m.90]",
            "primary_source_id": "20135150 m.90",
            "source_validity": "active",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "question_raw": "Tapu işlemlerinde 1994 tarihli Tapu Sicili Tüzüğünü kullanmak neden doğrudan hata üretir?",
            "retrieval": {
                "source_family_resolution": {
                    "historical_or_repealed_question": True,
                    "historical_scope_detected": True,
                },
                "article_span_selector": {
                    "legacy_intent_binding_active": True,
                    "legacy_candidate_preferred": False,
                    "document_state_binding_reason": "legacy_scope_no_compatible_candidate",
                },
            },
            "assembled_evidence": [
                {
                    "source_id": "20135150:20135150:m90:f0:from1900-01-01:to9999-12-31",
                    "citation": "20135150 m.90/f.0",
                    "source_title": "TAPU SİCİLİ TÜZÜĞÜ",
                    "source_family": "tuzuk",
                    "source_identifier": "20135150 m.90",
                    "article_or_section": "90",
                    "effective_state": "active",
                }
            ],
        },
    )

    contract = result.contract
    assert contract["source_family_claimed"] == "MULGA"
    assert contract["effective_state_claimed"] == "repealed"


def test_repair_suppresses_title_only_canonical_span_gap():
    result = build_or_repair_answer_contract(
        qid="CBKAR-08",
        answer_text="9903 sayılı Karar uygulanır. [Kaynak: 9903 m.0/f.0]",
        citations=["9903 m.0/f.0"],
        answer_contract={
            "answer_text": "9903 sayılı Karar uygulanır. [Kaynak: 9903 m.0/f.0]",
            "primary_source_id": "9903 m.0",
            "source_validity": "active",
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
        trace_payload={
            "retrieval": {
                "article_span_selector": {
                    "selected_document_key": "9903",
                    "selected_main_span_id": "9903 m.0/f.0",
                    "selected_article": "0",
                    "selector_evidence_sufficiency": "partially_supported",
                    "support_span_count": 1,
                    "insufficient_canonical_span_evidence": True,
                    "title_only_answer_degraded": True,
                }
            },
            "assembled_evidence": [
                {
                    "source_id": "9903:9903:m0:f0",
                    "citation": "9903 m.0/f.0",
                    "source_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR",
                    "source_family": "cb_karar",
                    "source_identifier": "9903 m.0",
                    "article_or_section": "0",
                    "effective_state": "active",
                }
            ],
        },
    )

    contract = result.contract
    assert contract["answer_mode"] == "insufficient_grounding"
    assert contract["grounding_status"] == "not_grounded"
    assert contract["support_insufficient_for_specific_claim"] is True
    assert contract["answer_suppressed_due_to_evidence_gap"] is True
    assert "insufficient_canonical_span_evidence" in contract["verification_findings"]
    assert result.validation["unsupported_confident_answer"] is False
