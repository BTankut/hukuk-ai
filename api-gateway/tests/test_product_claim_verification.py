from __future__ import annotations

from config import Settings
from product_controls.claim_verification import evaluate_claim_verification


def _contract(**claim_overrides):
    claim = {
        "claim_id": "claim-1",
        "text": "TBK m.49 haksiz fiil sorumlulugunu duzenler.",
        "evidence_ids": ["ev-1"],
        "source_family": "KANUN",
        "source_identifier": "TBK",
        "effective_state": "active",
    }
    claim.update(claim_overrides)
    return {
        "answer_text": "TBK m.49 haksiz fiil sorumlulugunu duzenler.",
        "citations": ["TBK m.49"],
        "claims": [claim],
    }


def _evidence(**overrides):
    row = {
        "evidence_id": "ev-1",
        "source_family": "KANUN",
        "source_identifier": "TBK",
        "effective_state": "active",
        "text": "TBK m.49 metni",
    }
    row.update(overrides)
    return [row]


def test_claim_verification_default_off() -> None:
    settings = Settings()

    assert settings.enable_product_claim_verification is False
    result = evaluate_claim_verification(
        answer_contract=_contract(),
        selected_evidence=_evidence(),
        enabled=settings.enable_product_claim_verification,
    )

    assert result.enabled is False
    assert result.verification_status == "disabled"


def test_unsupported_claim_detected() -> None:
    result = evaluate_claim_verification(
        answer_contract=_contract(evidence_ids=[]),
        selected_evidence=_evidence(),
        enabled=True,
    )

    assert result.verification_status == "fail"
    assert result.unsupported_claim_count == 1
    assert "unsupported_claim" in result.verification_failures


def test_source_identifier_mismatch_detected() -> None:
    result = evaluate_claim_verification(
        answer_contract=_contract(source_identifier="TMK"),
        selected_evidence=_evidence(source_identifier="TBK"),
        enabled=True,
    )

    assert result.source_consistency_result == "fail"
    assert "source_consistency_failed" in result.verification_failures
    assert "source_identifier_mismatch" in result.claim_to_evidence_map[0]["failure_reasons"]


def test_effective_state_mismatch_detected() -> None:
    result = evaluate_claim_verification(
        answer_contract=_contract(effective_state="active"),
        selected_evidence=_evidence(effective_state="repealed"),
        enabled=True,
    )

    assert result.effective_state_result == "fail"
    assert "effective_state_failed" in result.verification_failures


def test_verification_fail_preview_generated() -> None:
    result = evaluate_claim_verification(
        answer_contract={"answer_text": "", "citations": []},
        selected_evidence=[],
        enabled=True,
    )

    assert result.verification_status == "fail"
    assert result.answer_contract_validity == "fail"
    assert result.verification_fail_response is not None
    assert "güvenilir cevap veremem" in result.verification_fail_response
