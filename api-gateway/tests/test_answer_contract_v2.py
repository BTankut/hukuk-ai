from __future__ import annotations

from answer_contract_v2 import build_or_repair_answer_contract


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
    assert contract["grounding_status"] == "partially_grounded"
    assert contract["confidence_0_100"] < 70
    assert contract["needs_manual_review"] is True
    assert "selector_insufficient_support" in contract["verification_findings"]
    assert "selector_insufficient_selector_support" in contract["verification_findings"]
