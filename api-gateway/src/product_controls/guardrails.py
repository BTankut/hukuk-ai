from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


_SOURCE_REF_RE = re.compile(r"\[Kaynak:\s*([^\]]+)\]|\b[A-ZÇĞİÖŞÜ]{2,8}\s+m\.?\s*\d+", re.IGNORECASE)
_CONFIDENT_PHRASES = (
    "kesinlikle",
    "mutlaka",
    "tereddütsüz",
    "açıktır",
    "uygulanır",
    "zorundadır",
)


@dataclass(slots=True)
class ProductGuardrailsDecision:
    enabled: bool
    decision: str
    blocked: bool
    fallback_mode: str | None = None
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    manual_review_required: bool = False
    legal_disclaimer_required: bool = False
    confidence_threshold_result: str = "not_evaluated"

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "decision": self.decision,
            "blocked": self.blocked,
            "fallback_mode": self.fallback_mode,
            "reasons": self.reasons,
            "warnings": self.warnings,
            "manual_review_required": self.manual_review_required,
            "legal_disclaimer_required": self.legal_disclaimer_required,
            "confidence_threshold_result": self.confidence_threshold_result,
        }


def _has_source_reference(answer_text: str) -> bool:
    return bool(_SOURCE_REF_RE.search(answer_text or ""))


def _looks_confident(answer_text: str) -> bool:
    lowered = (answer_text or "").casefold()
    return any(phrase in lowered for phrase in _CONFIDENT_PHRASES)


def evaluate_product_guardrails(
    *,
    answer_text: str,
    selected_evidence: list[dict[str, Any]] | None = None,
    enabled: bool = False,
    confidence: float | None = None,
    min_confidence: float = 0.65,
    source_available: bool = True,
    current_law_resolved: bool = True,
    effective_state: str | None = None,
    manual_review_required: bool = False,
    legal_disclaimer_required: bool = True,
) -> ProductGuardrailsDecision:
    """Preview product guardrail decisions without mutating live runtime."""

    if not enabled:
        return ProductGuardrailsDecision(
            enabled=False,
            decision="disabled",
            blocked=False,
            legal_disclaimer_required=False,
        )

    evidence = selected_evidence or []
    reasons: list[str] = []
    warnings: list[str] = []
    confidence_result = "not_evaluated"

    if confidence is not None:
        confidence_result = "pass" if confidence >= min_confidence else "fail_low_confidence"
        if confidence < min_confidence:
            reasons.append("confidence_threshold")

    if not source_available:
        reasons.append("source_unavailable")

    if not evidence:
        reasons.append("insufficient_evidence")

    if _looks_confident(answer_text) and (not evidence or not _has_source_reference(answer_text)):
        reasons.append("unsupported_confident_answer")

    if not current_law_resolved:
        warnings.append("current_law_uncertainty")

    if (effective_state or "").casefold() in {"repealed", "historical", "mulga", "mülga"}:
        warnings.append("repealed_or_historical_warning")

    if manual_review_required:
        warnings.append("manual_review_required")

    blocking_reasons = {
        "unsupported_confident_answer",
        "insufficient_evidence",
        "source_unavailable",
        "confidence_threshold",
    }
    blocked = any(reason in blocking_reasons for reason in reasons)
    if blocked:
        if "source_unavailable" in reasons:
            decision = "block_source_unavailable"
            fallback_mode = "fallback_source_unavailable"
        elif "unsupported_confident_answer" in reasons:
            decision = "block_unsupported_confident_answer"
            fallback_mode = "fallback_insufficient_evidence"
        elif "confidence_threshold" in reasons:
            decision = "block_low_confidence"
            fallback_mode = "fallback_low_confidence"
        else:
            decision = "block_insufficient_evidence"
            fallback_mode = "fallback_insufficient_evidence"
    elif warnings:
        decision = "allow_with_warning"
        fallback_mode = None
    elif legal_disclaimer_required:
        decision = "allow_with_disclaimer"
        fallback_mode = None
    else:
        decision = "allow"
        fallback_mode = None

    return ProductGuardrailsDecision(
        enabled=True,
        decision=decision,
        blocked=blocked,
        fallback_mode=fallback_mode,
        reasons=reasons,
        warnings=warnings,
        manual_review_required=manual_review_required,
        legal_disclaimer_required=legal_disclaimer_required,
        confidence_threshold_result=confidence_result,
    )
