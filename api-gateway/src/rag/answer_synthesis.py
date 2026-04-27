"""Answer synthesis and finalization helpers.

This module starts with low-risk formatting/serialization helpers only. Policy
and replacement decisions remain in the router until separately gated.
"""

from __future__ import annotations

from typing import Any

from answer_contract_v2 import controlled_fallback_answer
from faz2a_hardening import dedupe_strings, normalize_query_text
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


VERIFIED_ANSWER_PLAN_HEADER = "Doğrulanmış cevap planı:"


def verified_slots_by_name(answer_contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    slots = answer_contract.get("answer_slots")
    if not isinstance(slots, list):
        return {}
    verified: dict[str, dict[str, Any]] = {}
    for slot in slots:
        if not isinstance(slot, dict):
            continue
        slot_name = str(slot.get("slot_name") or "").strip()
        if not slot_name:
            continue
        if (
            str(slot.get("fill_status") or "") == "filled"
            and str(slot.get("verifier_status") or "") == "verified"
            and str(slot.get("value") or "").strip()
        ):
            verified[slot_name] = slot
    return verified


def first_verified_plan_value(
    verified_slots: dict[str, dict[str, Any]],
    slot_names: tuple[str, ...],
) -> tuple[str, str]:
    for slot_name in slot_names:
        slot = verified_slots.get(slot_name)
        if slot:
            return slot_name, verified_answer_plan_slot_value(slot)
    return "", ""


def build_verified_answer_plan(answer_contract: dict[str, Any]) -> dict[str, Any]:
    verified_slots = verified_slots_by_name(answer_contract)
    slot_items = answer_contract.get("answer_slots") if isinstance(answer_contract.get("answer_slots"), list) else []
    missing_slots = [
        str(slot.get("slot_name") or "")
        for slot in slot_items
        if isinstance(slot, dict)
        and str(slot.get("slot_name") or "").strip()
        and str(slot.get("fill_status") or "") != "filled"
    ]
    direct_name, direct_value = first_verified_plan_value(
        verified_slots,
        ("direct_conclusion", "direct_rule", "rule", "conclusion", "operative_rule", "operative_clause"),
    )
    basis_names = (
        "governing_source",
        "exact_source_identity",
        "selected_primary_source",
        "identifier",
        "article_or_span",
        "issuer",
        "circular_number_or_date",
        "decision_number",
        "teblig_identifier",
    )
    legal_basis_slots = [
        {"slot_name": name, "value": verified_answer_plan_slot_value(verified_slots[name])}
        for name in basis_names
        if name in verified_slots
    ][:4]
    temporal_name, temporal_value = first_verified_plan_value(
        verified_slots,
        ("temporal_validity", "effective_state", "effective_period", "effective_date", "current_applicability"),
    )
    scenario_name, scenario_value = first_verified_plan_value(
        verified_slots,
        ("facts_applied", "scenario_applicability", "scope_or_addressee", "scope"),
    )
    procedure_name, procedure_value = first_verified_plan_value(
        verified_slots,
        ("procedure", "consequence", "obligations", "procedure_or_formula", "procedure_or_consequence"),
    )
    exception_name, exception_value = first_verified_plan_value(
        verified_slots,
        ("exception_or_limitation", "exception_rule", "exception_conditions"),
    )
    transition_name, transition_value = first_verified_plan_value(
        verified_slots,
        ("transition_rule", "transition_or_replacement_rule", "replacement_or_current_law_relation"),
    )
    return {
        "direct_answer_slot": {"slot_name": direct_name, "value": direct_value} if direct_value else None,
        "legal_basis_slots": legal_basis_slots,
        "temporal_validity_slot": {"slot_name": temporal_name, "value": temporal_value} if temporal_value else None,
        "scenario_application_slot": {"slot_name": scenario_name, "value": scenario_value} if scenario_value else None,
        "procedure_or_consequence_slot": {"slot_name": procedure_name, "value": procedure_value} if procedure_value else None,
        "exception_or_limitation_slot": {"slot_name": exception_name, "value": exception_value} if exception_value else None,
        "transition_or_replacement_slot": {"slot_name": transition_name, "value": transition_value} if transition_value else None,
        "missing_slots": dedupe_strings(missing_slots),
        "confidence_policy": {
            "ceiling": answer_contract.get("confidence_policy_ceiling"),
            "reasons": answer_contract.get("confidence_policy_ceiling_reasons") or [],
        },
    }


def verified_slot_controlled_replacement_allowed(
    *,
    answer_contract: dict[str, Any],
    final_mode: str | None,
) -> bool:
    if final_mode not in {"refusal", "blocked"}:
        return False
    if (
        answer_contract.get("answer_suppressed_due_to_evidence_gap") is True
        or answer_contract.get("insufficient_canonical_span_evidence") is True
    ):
        return False

    verified_slots = verified_slots_by_name(answer_contract)
    if len(verified_slots) < 2:
        return False
    has_basis = bool(
        {
            "governing_source",
            "exact_source_identity",
            "selected_primary_source",
            "identifier",
            "article_or_span",
        }
        & set(verified_slots)
    )
    has_rule = bool(
        {
            "direct_conclusion",
            "direct_rule",
            "rule",
            "conclusion",
            "operative_rule",
            "operative_clause",
            "procedure",
            "consequence",
            "obligations",
            "procedure_or_formula",
            "procedure_or_consequence",
            "current_applicability",
        }
        & set(verified_slots)
    )
    return has_basis and has_rule


def apply_verified_answer_slot_plan_to_answer_text(
    *,
    answer_text: str,
    answer_contract: dict[str, Any] | None,
    final_mode: str | None,
) -> tuple[str, dict[str, Any]]:
    if not isinstance(answer_contract, dict):
        return answer_text, {
            "verified_answer_slot_synthesis_applied": False,
            "verified_answer_slot_synthesis_slots": [],
            "verified_answer_slot_synthesis_reason": "no_contract",
            "verified_answer_plan": None,
            "verified_answer_plan_missing_slots": [],
        }
    controlled_replacement = verified_slot_controlled_replacement_allowed(
        answer_contract=answer_contract,
        final_mode=final_mode,
    )
    if final_mode not in {"answer", "partial"} and not controlled_replacement:
        return answer_text, {
            "verified_answer_slot_synthesis_applied": False,
            "verified_answer_slot_synthesis_slots": [],
            "verified_answer_slot_synthesis_reason": "final_mode_not_answer_or_partial",
            "verified_answer_plan": None,
            "verified_answer_plan_missing_slots": [],
        }
    if not (answer_text or "").strip() and not controlled_replacement:
        return answer_text, {
            "verified_answer_slot_synthesis_applied": False,
            "verified_answer_slot_synthesis_slots": [],
            "verified_answer_slot_synthesis_reason": "empty_answer",
            "verified_answer_plan": None,
            "verified_answer_plan_missing_slots": [],
        }
    if VERIFIED_ANSWER_PLAN_HEADER in answer_text:
        return answer_text, {
            "verified_answer_slot_synthesis_applied": False,
            "verified_answer_slot_synthesis_slots": [],
            "verified_answer_slot_synthesis_reason": "already_applied",
            "verified_answer_plan": answer_contract.get("verified_answer_plan"),
            "verified_answer_plan_missing_slots": answer_contract.get("verified_answer_plan_missing_slots") or [],
        }
    if (
        answer_contract.get("answer_suppressed_due_to_evidence_gap") is True
        or answer_contract.get("insufficient_canonical_span_evidence") is True
    ):
        return answer_text, {
            "verified_answer_slot_synthesis_applied": False,
            "verified_answer_slot_synthesis_slots": [],
            "verified_answer_slot_synthesis_reason": "canonical_evidence_gap",
            "verified_answer_plan": None,
            "verified_answer_plan_missing_slots": [],
        }

    plan = build_verified_answer_plan(answer_contract)
    lines: list[str] = []
    synthesized_slots: list[str] = []
    if plan.get("legal_basis_slots"):
        basis_text = "; ".join(str(item.get("value") or "") for item in plan["legal_basis_slots"] if item.get("value"))
        if basis_text:
            lines.append(f"- Dayanak: {basis_text}")
            synthesized_slots.extend(str(item.get("slot_name") or "") for item in plan["legal_basis_slots"])
    for label, key in (
        ("Kural/sonuç", "direct_answer_slot"),
        ("Yürürlük/güncellik", "temporal_validity_slot"),
        ("Uygulama/kapsam", "scenario_application_slot"),
        ("Usul/sonuç", "procedure_or_consequence_slot"),
        ("İstisna/sınırlama", "exception_or_limitation_slot"),
        ("Geçiş/güncel ilişki", "transition_or_replacement_slot"),
    ):
        slot = plan.get(key)
        if isinstance(slot, dict) and slot.get("value"):
            lines.append(f"- {label}: {slot['value']}")
            synthesized_slots.append(str(slot.get("slot_name") or ""))
    missing_slots = [slot for slot in plan.get("missing_slots") or [] if slot]
    if missing_slots:
        lines.append("- Eksik doğrulanmış slotlar: " + ", ".join(missing_slots[:8]))

    if not lines:
        return answer_text, {
            "verified_answer_slot_synthesis_applied": False,
            "verified_answer_slot_synthesis_slots": [],
            "verified_answer_slot_synthesis_reason": "no_verified_slots",
            "verified_answer_plan": plan,
            "verified_answer_plan_missing_slots": missing_slots,
        }

    if controlled_replacement:
        return (
            "Mevcut doğrulanmış kaynak parçalarına göre sınırlı cevap:\n" + "\n".join(lines),
            {
                "verified_answer_slot_synthesis_applied": True,
                "verified_answer_slot_synthesis_slots": dedupe_strings(synthesized_slots),
                "verified_answer_slot_synthesis_reason": "verified_slots_replaced_unsupported_generation",
                "verified_answer_slot_synthesis_controlled_replacement": True,
                "verified_answer_plan": plan,
                "verified_answer_plan_missing_slots": missing_slots,
            },
        )

    return (
        f"{answer_text.strip()}\n\n{VERIFIED_ANSWER_PLAN_HEADER}\n" + "\n".join(lines),
        {
            "verified_answer_slot_synthesis_applied": True,
            "verified_answer_slot_synthesis_slots": dedupe_strings(synthesized_slots),
            "verified_answer_slot_synthesis_reason": "verified_slots_made_visible",
            "verified_answer_slot_synthesis_controlled_replacement": False,
            "verified_answer_plan": plan,
            "verified_answer_plan_missing_slots": missing_slots,
        },
    )


def resolve_contract_suppressed_answer_text(
    *,
    answer_text: str,
    answer_contract: dict[str, Any] | None,
) -> str:
    if isinstance(answer_contract, dict) and answer_contract.get("answer_suppressed_due_to_evidence_gap") is True:
        return controlled_fallback_answer(answer_contract)
    return answer_text


EVIDENCE_SLOT_SYNTHESIS_HEADER = "Kaynaklardan çıkarılan zorunlu noktalar:"
EVIDENCE_SLOT_SYNTHESIS_LABELS = {
    "result_or_holding": "Sonuç/hüküm",
    "governing_source": "Dayanak kaynak",
    "exact_source_identity": "Belge kimliği",
    "article_or_span": "Madde/span",
    "temporal_validity": "Yürürlük/güncellik",
    "historical_period": "Tarihsel dönem",
    "current_applicability": "Güncel uygulanabilirlik",
    "transition_or_replacement_rule": "Geçiş/yerine geçen düzenleme",
    "procedure_or_consequence": "Usul/sonuç",
    "scenario_applicability": "Somut olaya uygulanma",
    "exception_or_limitation": "İstisna/sınırlama",
    "document_selection_reason": "Belge seçimi",
    "hierarchy_or_conflict_rule": "Norm ilişkisi",
}


def apply_evidence_slot_synthesis_to_answer_text(
    *,
    answer_text: str,
    answer_contract: dict[str, Any] | None,
    final_mode: str | None,
) -> tuple[str, dict[str, Any]]:
    if not isinstance(answer_contract, dict):
        return answer_text, {
            "evidence_slot_synthesis_applied": False,
            "evidence_slot_synthesis_slots": [],
            "evidence_slot_synthesis_reason": "final_mode_not_answer_or_no_contract",
        }
    required_slots = [
        str(slot)
        for slot in answer_contract.get("must_have_fact_slots") or []
        if isinstance(slot, str) and slot.strip()
    ]
    answer_mode = str(answer_contract.get("answer_mode") or "")
    mulga_controlled_mode = answer_mode in {
        "historical_repealed_answer",
        "repealed_transition_answer",
        "not_currently_applicable_answer",
    } or bool({"historical_period", "current_applicability", "transition_or_replacement_rule"} & set(required_slots))
    if final_mode not in {"answer", "partial"} and not mulga_controlled_mode:
        return answer_text, {
            "evidence_slot_synthesis_applied": False,
            "evidence_slot_synthesis_slots": [],
            "evidence_slot_synthesis_reason": "final_mode_not_answer_or_no_contract",
        }
    if not (answer_text or "").strip():
        return answer_text, {
            "evidence_slot_synthesis_applied": False,
            "evidence_slot_synthesis_slots": [],
            "evidence_slot_synthesis_reason": "empty_answer",
        }
    if EVIDENCE_SLOT_SYNTHESIS_HEADER in answer_text:
        return answer_text, {
            "evidence_slot_synthesis_applied": False,
            "evidence_slot_synthesis_slots": [],
            "evidence_slot_synthesis_reason": "already_applied",
        }
    if (
        answer_contract.get("answer_suppressed_due_to_evidence_gap") is True
        or answer_contract.get("insufficient_canonical_span_evidence") is True
    ):
        return answer_text, {
            "evidence_slot_synthesis_applied": False,
            "evidence_slot_synthesis_slots": [],
            "evidence_slot_synthesis_reason": "canonical_evidence_gap",
        }
    missing_slots = [
        str(slot)
        for slot in answer_contract.get("missing_fact_slots") or []
        if isinstance(slot, str) and slot.strip()
    ]
    candidate_slots = missing_slots
    synthesis_success_reason = "missing_slots_filled_from_selected_evidence"
    if not candidate_slots:
        try:
            slot_coverage = float(answer_contract.get("answer_slot_coverage_score") or 0.0)
        except (TypeError, ValueError):
            slot_coverage = 0.0
        controlled_evidence_surface = answer_text.strip().startswith(
            "Mevcut doğrulanmış kaynak parçalarına göre sınırlı cevap:"
        )
        if not required_slots or (slot_coverage >= 0.98 and not controlled_evidence_surface):
            return answer_text, {
                "evidence_slot_synthesis_applied": False,
                "evidence_slot_synthesis_slots": [],
                "evidence_slot_synthesis_reason": "no_missing_slots",
            }
        candidate_slots = required_slots
        synthesis_success_reason = "slot_values_made_visible_from_selected_evidence"
    slot_values = answer_contract.get("evidence_required_slot_values")
    if not isinstance(slot_values, list):
        return answer_text, {
            "evidence_slot_synthesis_applied": False,
            "evidence_slot_synthesis_slots": [],
            "evidence_slot_synthesis_reason": "no_evidence_slot_values",
        }

    normalized_answer = normalize_query_text(answer_text)
    rows_by_slot = {
        str(row.get("slot_name") or ""): row
        for row in slot_values
        if isinstance(row, dict)
    }
    synthesis_lines: list[str] = []
    synthesized_slots: list[str] = []
    for slot in candidate_slots:
        row = rows_by_slot.get(slot)
        if not isinstance(row, dict):
            continue
        try:
            confidence = float(row.get("slot_confidence") or 0.0)
        except (TypeError, ValueError):
            confidence = 0.0
        slot_value = compact_slot_value(str(row.get("slot_value") or ""), max_len=300)
        evidence_span_id = str(row.get("evidence_span_id") or "").strip()
        if confidence < 0.65 or not slot_value or not evidence_span_id:
            continue
        value_terms = [
            token
            for token in normalize_query_text(slot_value).split()
            if len(token) >= 5
        ][:8]
        if value_terms and sum(1 for token in value_terms if token in normalized_answer) >= min(3, len(value_terms)):
            continue
        label = EVIDENCE_SLOT_SYNTHESIS_LABELS.get(slot, slot)
        synthesis_lines.append(f"- {label}: {slot_value} [Kaynak: {evidence_span_id}]")
        synthesized_slots.append(slot)
        if len(synthesis_lines) >= 5:
            break

    if not synthesis_lines:
        return answer_text, {
            "evidence_slot_synthesis_applied": False,
            "evidence_slot_synthesis_slots": [],
            "evidence_slot_synthesis_reason": "no_confident_missing_slot_values",
        }
    synthesized_answer = (
        f"{answer_text.strip()}\n\n"
        f"{EVIDENCE_SLOT_SYNTHESIS_HEADER}\n"
        + "\n".join(synthesis_lines)
    )
    return synthesized_answer, {
        "evidence_slot_synthesis_applied": True,
        "evidence_slot_synthesis_slots": synthesized_slots,
        "evidence_slot_synthesis_reason": synthesis_success_reason,
    }


def resolve_public_answer_text(
    *,
    answer_text: str,
    answer_contract: dict[str, Any] | None,
    final_mode: str | None,
) -> str:
    if final_mode not in {"answer", "partial"}:
        return answer_text
    if not isinstance(answer_contract, dict):
        return answer_text
    contract_answer_text = answer_contract.get("answer_text")
    if not isinstance(contract_answer_text, str):
        return answer_text
    normalized_contract = contract_answer_text.strip()
    if not normalized_contract:
        return answer_text
    return normalized_contract
