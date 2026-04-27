"""Answer synthesis and finalization helpers.

This module starts with low-risk formatting/serialization helpers only. Policy
and replacement decisions remain in the router until separately gated.
"""

from __future__ import annotations

from typing import Any

from rag.answer_slots import compact_slot_value


def build_native_dialog_fallback_answer(intent: str) -> str:
    if intent == "gratitude":
        return "Rica ederim. İstersen mevzuat sorunu doğrudan kanun ve madde numarasıyla sor."
    if intent == "capability":
        return (
            "Merhaba. Mevzuat sorularında yardımcı olabilirim; özellikle kanun ve madde bazlı "
            "sorularda daha isabetli çalışırım. İstersen sorunu doğrudan yaz."
        )
    return "Merhaba. Mevzuat sorularında yardımcı olabilirim; istersen sorunu doğrudan yaz."


def build_persisted_raw_answer_snapshot(
    *,
    answer_text: str,
    citations: list[str],
    source_ids: list[str],
    final_mode: str | None,
    final_reason: str | None,
) -> dict[str, Any]:
    return {
        "answer_text": answer_text,
        "ordered_citation_list": list(citations),
        "ordered_source_id_list": list(source_ids),
        "final_mode": final_mode,
        "final_reason": final_reason,
    }


def build_persisted_response_envelope_snapshot(
    *,
    response_id: str,
    blocked: bool,
    final_mode: str | None,
    final_reason: str | None,
    citations: list[str],
    source_ids: list[str],
) -> dict[str, Any]:
    return {
        "response_id": response_id,
        "blocked": blocked,
        "final_mode": final_mode,
        "final_reason": final_reason,
        "ordered_citation_list": list(citations),
        "ordered_source_id_list": list(source_ids),
    }


def sanitize_public_final_mode(final_mode: str | None) -> str | None:
    if final_mode == "blocked":
        return "refusal"
    return final_mode


def sanitize_public_answer_contract(answer_contract: dict[str, Any] | None) -> dict[str, Any] | None:
    if answer_contract is None:
        return None
    sanitized = dict(answer_contract)
    sanitized["final_mode"] = sanitize_public_final_mode(answer_contract.get("final_mode"))
    return sanitized


def verified_answer_plan_slot_value(slot: dict[str, Any]) -> str:
    value = compact_slot_value(str(slot.get("value") or ""), max_len=260)
    evidence_keys = [
        str(item).strip()
        for item in slot.get("evidence_span_keys") or []
        if str(item or "").strip()
    ]
    if evidence_keys:
        return f"{value} [Kaynak: {evidence_keys[0]}]"
    return value
