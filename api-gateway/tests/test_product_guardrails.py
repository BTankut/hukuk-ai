from __future__ import annotations

from config import Settings
from product_controls.guardrails import evaluate_product_guardrails


def test_guardrails_default_off() -> None:
    settings = Settings()

    assert settings.enable_product_guardrails is False
    result = evaluate_product_guardrails(
        answer_text="Kesinlikle uygulanır.",
        selected_evidence=[],
        enabled=settings.enable_product_guardrails,
    )

    assert result.enabled is False
    assert result.decision == "disabled"
    assert result.blocked is False


def test_unsupported_confident_blocks_when_enabled() -> None:
    result = evaluate_product_guardrails(
        answer_text="Bu hüküm kesinlikle uygulanır.",
        selected_evidence=[],
        enabled=True,
    )

    assert result.blocked is True
    assert result.decision == "block_unsupported_confident_answer"
    assert "unsupported_confident_answer" in result.reasons


def test_insufficient_evidence_returns_safe_mode() -> None:
    result = evaluate_product_guardrails(
        answer_text="Bu konuda karar verilebilir.",
        selected_evidence=[],
        enabled=True,
    )

    assert result.blocked is True
    assert result.fallback_mode == "fallback_insufficient_evidence"
    assert "insufficient_evidence" in result.reasons


def test_repealed_source_adds_warning() -> None:
    result = evaluate_product_guardrails(
        answer_text="Tarihsel hüküm budur. [Kaynak: Eski Tüzük m.1]",
        selected_evidence=[{"source_key": "old_tuzuk", "effective_state": "repealed"}],
        enabled=True,
        effective_state="repealed",
    )

    assert result.blocked is False
    assert result.decision == "allow_with_warning"
    assert "repealed_or_historical_warning" in result.warnings


def test_manual_review_trigger_set() -> None:
    result = evaluate_product_guardrails(
        answer_text="Kaynaklı ama hassas cevap. [Kaynak: TBK m.49]",
        selected_evidence=[{"source_key": "TBK", "article": "49"}],
        enabled=True,
        manual_review_required=True,
    )

    assert result.manual_review_required is True
    assert "manual_review_required" in result.warnings
