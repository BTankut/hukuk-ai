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
