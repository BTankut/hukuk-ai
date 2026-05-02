"""Answer synthesis and finalization helpers.

This module starts with low-risk formatting/serialization helpers only. Policy
and replacement decisions remain in the router until separately gated.
"""

from __future__ import annotations

import re
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


def _s5_family_identifier_guard_fields(
    *,
    applied: bool = False,
    guard_type: str = "not_applicable",
    claim_family_preserved: bool = False,
    claim_identifier_preserved: bool = False,
    article_surface_preserved: bool = False,
    reason: str = "not_evaluated",
) -> dict[str, Any]:
    return {
        "s5_family_identifier_guard_applied": applied,
        "s5_guard_type": guard_type,
        "s5_claim_family_preserved": claim_family_preserved,
        "s5_claim_identifier_preserved": claim_identifier_preserved,
        "s5_article_surface_preserved": article_surface_preserved,
        "s5_guard_reason": reason,
    }


def sanitize_public_answer_contract(answer_contract: dict[str, Any] | None) -> dict[str, Any] | None:
    if answer_contract is None:
        return None
    sanitized = dict(answer_contract)
    sanitized["final_mode"] = sanitize_public_final_mode(answer_contract.get("final_mode"))
    sanitized.setdefault("split_temporal_policy_applied", False)
    sanitized.setdefault("claim_family_rewrite_allowed", False)
    sanitized.setdefault("historical_claim_surface_allowed", False)
    sanitized.setdefault("split_temporal_policy_bucket", "not_applicable")
    sanitized.setdefault("split_temporal_policy_reason", "not_evaluated")
    sanitized.setdefault("claim_identifier_rewrite_allowed", False)
    sanitized.setdefault("temporal_support_only", True)
    sanitized.setdefault("current_law_basis_primary_allowed", False)
    for key, value in _s5_family_identifier_guard_fields().items():
        sanitized.setdefault(key, value)
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
CONTROLLED_VERIFIED_SLOT_PREFIX = "Mevcut doğrulanmış kaynak parçalarına göre sınırlı cevap:"


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


def _plan_value_dedupe_key(value: str) -> str:
    normalized = normalize_query_text(value or "")
    normalized = normalized.replace("[kaynak:", " kaynak ")
    return " ".join(normalized.split())


def _append_unique_plan_slot(
    plan_slots: list[dict[str, str]],
    *,
    slot_name: str,
    value: str,
    seen_values: set[str],
) -> None:
    key = _plan_value_dedupe_key(value)
    if not key or key in seen_values:
        return
    plan_slots.append({"slot_name": slot_name, "value": value})
    seen_values.add(key)


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
        (
            "direct_conclusion",
            "direct_legal_conclusion",
            "result_or_holding",
            "direct_rule",
            "rule",
            "conclusion",
            "operative_rule",
            "operative_clause",
            "operative_instruction",
            "administrative_effect",
        ),
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
        "hierarchy_or_conflict_rule",
    )
    legal_basis_slots: list[dict[str, str]] = []
    seen_basis_values: set[str] = set()
    for name in basis_names:
        if name not in verified_slots:
            continue
        _append_unique_plan_slot(
            legal_basis_slots,
            slot_name=name,
            value=verified_answer_plan_slot_value(verified_slots[name]),
            seen_values=seen_basis_values,
        )
        if len(legal_basis_slots) >= 4:
            break
    temporal_name, temporal_value = first_verified_plan_value(
        verified_slots,
        (
            "temporal_validity",
            "effective_state",
            "effective_period",
            "effective_date",
            "current_applicability",
            "source_is_repealed_or_historical",
            "applicable_period",
            "no_active_law_overclaim",
        ),
    )
    scenario_name, scenario_value = first_verified_plan_value(
        verified_slots,
        ("facts_applied", "scenario_applicability", "scenario_application", "scope_or_addressee", "scope"),
    )
    procedure_name, procedure_value = first_verified_plan_value(
        verified_slots,
        (
            "procedure",
            "consequence",
            "obligations",
            "procedure_or_formula",
            "procedure_or_consequence",
            "operative_instruction",
            "operative_clause",
            "administrative_effect",
        ),
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


def verified_answer_plan_visible_slot_names(plan: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for item in plan.get("legal_basis_slots") or []:
        if isinstance(item, dict):
            names.append(str(item.get("slot_name") or ""))
    for key in (
        "direct_answer_slot",
        "temporal_validity_slot",
        "scenario_application_slot",
        "procedure_or_consequence_slot",
        "exception_or_limitation_slot",
        "transition_or_replacement_slot",
    ):
        slot = plan.get(key)
        if isinstance(slot, dict):
            names.append(str(slot.get("slot_name") or ""))
    return dedupe_strings([name for name in names if name])


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
    if answer_text.strip().startswith(CONTROLLED_VERIFIED_SLOT_PREFIX):
        plan = build_verified_answer_plan(answer_contract)
        return answer_text, {
            "verified_answer_slot_synthesis_applied": False,
            "verified_answer_slot_synthesis_slots": verified_answer_plan_visible_slot_names(plan),
            "verified_answer_slot_synthesis_reason": "controlled_verified_surface_already_present",
            "verified_answer_plan": plan,
            "verified_answer_plan_missing_slots": plan.get("missing_slots") or [],
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
            f"{CONTROLLED_VERIFIED_SLOT_PREFIX}\n" + "\n".join(lines),
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

TEMPORAL_CLAIM_ALIGNMENT_HEADER = "Tarihsel/yürürlük zinciri:"
_TEMPORAL_REPEALED_MODES = {
    "historical_repealed_answer",
    "repealed_transition_answer",
    "not_currently_applicable_answer",
    "repealed_or_uncertain",
}
_TEMPORAL_REPEALED_STATES = {"repealed", "historical", "historical_repealed"}
_TEMPORAL_REPEAL_STATES = {"repeal_instrument"}
_TEMPORAL_ACTIVE_STATES = {"active", "amended"}
_SPLIT_ACTIVE_NON_MULGA_FAMILIES = {
    "kanun",
    "khk",
    "teblig",
    "tebligler",
    "tuzuk",
    "uy",
    "kky",
    "yonetmelik",
    "cb_genelge",
    "cb_karar",
    "cb_kararname",
    "cb_yonetmelik",
}
_SPLIT_ACTIVE_NON_REPEALED_STATES = {"active", "current", "amended", "unknown_non_repealed", "unknown"}
_SPLIT_HISTORICAL_RISK_TERMS = (
    "hatali",
    "hata",
    "risk",
    "riskli",
    "guvenli",
    "dogrudan",
    "dayanmak",
    "esas almak",
    "hukum kurmak",
)
_SPLIT_HISTORICAL_CONTEXT_TERMS = (
    "eski",
    "mulga",
    "tarihsel",
    "tarihli",
    "yururlukten kaldir",
    "yururlukten kalk",
)
_S5_CURRENT_LAW_EXCEPTION_TERMS = (
    "2026",
    "bugun",
    "guncel",
    "guncellik",
    "mevcut",
    "hala",
    "halen",
    "gecerli",
    "otomatik",
    "uygulamak",
    "uygulan",
    "esas alin",
)
_S5_QUERY_STOPWORDS = {
    "hangi",
    "neden",
    "sadece",
    "yerine",
    "cevabi",
    "cevap",
    "sorusu",
    "sorusunda",
    "hakkinda",
    "madde",
    "kanun",
    "tuzuk",
    "teblig",
    "yonetmelik",
}
_TEMPORAL_REPEAL_TEXT_RE = re.compile(
    r"\b("
    r"m[uü]lga|"
    r"y[uü]r[uü]rl[uü]kten\s+kald[ıi]r|"
    r"yururlukten\s+kaldir|"
    r"y[uü]r[uü]rl[uü]kten\s+kalk|"
    r"yururlukten\s+kalk"
    r")",
    re.IGNORECASE,
)
_TEMPORAL_ARTICLE_RE = re.compile(r"\bm(?P<article>GEC\d+|\d+[a-z]?)\b", re.IGNORECASE)


def _temporal_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _temporal_first_text(*values: Any) -> str:
    for value in values:
        text = _temporal_text(value)
        if text:
            return text
    return ""


def _temporal_truthy(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return normalize_query_text(value) in {"1", "true", "yes", "y", "evet"}
    return False


def _temporal_normalized(value: Any) -> str:
    return normalize_query_text(_temporal_text(value))


def _temporal_has_repeal_text(*values: Any) -> bool:
    return bool(_TEMPORAL_REPEAL_TEXT_RE.search(" ".join(_temporal_text(value) for value in values)))


def _temporal_item_text(item: dict[str, Any]) -> str:
    return " ".join(
        _temporal_text(item.get(key))
        for key in (
            "quoted_or_extracted_span",
            "excerpt",
            "text",
            "source_title",
            "citation",
            "source_id",
            "source_identifier",
            "effective_state",
        )
    )


def _temporal_source_key(item: dict[str, Any] | None) -> str:
    if not isinstance(item, dict):
        return ""
    return _temporal_first_text(
        item.get("source_id"),
        item.get("canonical_source_key_v2"),
        item.get("binding_source_key"),
        item.get("relation_chain_source_key"),
        item.get("citation"),
        item.get("source_identifier"),
    )


def _temporal_article_raw(item: dict[str, Any] | None) -> str:
    if not isinstance(item, dict):
        return ""
    raw = _temporal_first_text(
        item.get("article_or_section"),
        item.get("madde_no"),
        item.get("article"),
    )
    if raw:
        return raw
    for key in ("source_id", "citation", "source_identifier"):
        match = _TEMPORAL_ARTICLE_RE.search(_temporal_text(item.get(key)))
        if match:
            return match.group("article")
    return ""


def _temporal_article_claim(item: dict[str, Any] | None) -> str:
    raw = _temporal_article_raw(item)
    if not raw:
        return "unknown"
    normalized = raw.strip().lower().replace("geç", "gec")
    if normalized.startswith("gec"):
        digits = "".join(ch for ch in normalized if ch.isdigit())
        return f"geçici madde {digits}" if digits else "geçici madde"
    if normalized.startswith("madde:") or normalized.startswith("geçici madde"):
        return raw
    return f"madde:{raw}"


def _temporal_identifier_base(item: dict[str, Any] | None) -> str:
    if not isinstance(item, dict):
        return ""
    candidates = [
        _temporal_text(item.get("source_identifier")),
        _temporal_text(item.get("citation")),
        _temporal_text(item.get("source_id")),
    ]
    for candidate in candidates:
        candidate = re.sub(r"/f\.\w+$", "", candidate)
        candidate = re.sub(r"\s+m\.(?:GEC\d+|\d+[a-z]?)\b.*$", "", candidate, flags=re.IGNORECASE)
        if not candidate:
            continue
        if ":" in candidate:
            parts = [part for part in candidate.split(":") if part]
            for part in parts:
                if re.fullmatch(r"\d{2,9}|[A-ZÇĞİÖŞÜA-Za-z_]+\d*", part):
                    return part
            continue
        return candidate
    return ""


def _temporal_identifier_claim(item: dict[str, Any] | None) -> str:
    if not isinstance(item, dict):
        return "unknown"
    article = _temporal_article_raw(item)
    base = _temporal_identifier_base(item)
    if base and article:
        return f"{base} m.{article}"
    return _temporal_first_text(item.get("citation"), item.get("source_identifier"), item.get("source_id"), "unknown")


def _temporal_source_title(item: dict[str, Any] | None) -> str:
    if not isinstance(item, dict):
        return "unknown"
    return _temporal_first_text(
        item.get("source_title"),
        item.get("full_title"),
        item.get("belge_adi"),
        item.get("kanun_adi"),
        item.get("title"),
        item.get("source"),
        "unknown",
    )


def _temporal_citation(item: dict[str, Any] | None) -> str:
    if not isinstance(item, dict):
        return "unknown"
    return _temporal_first_text(item.get("citation"), _temporal_identifier_claim(item), item.get("source_id"), "unknown")


def _temporal_excerpt(item: dict[str, Any] | None, *, max_len: int = 360) -> str:
    if not isinstance(item, dict):
        return ""
    value = _temporal_first_text(
        item.get("quoted_or_extracted_span"),
        item.get("excerpt"),
        item.get("text"),
        item.get("source_title"),
    )
    return compact_slot_value(value, max_len=max_len)


def _temporal_family(item: dict[str, Any] | None) -> str:
    if not isinstance(item, dict):
        return ""
    return _temporal_normalized(
        item.get("source_family")
        or item.get("source_family_canonical")
        or item.get("source_family_mapped")
        or item.get("belge_turu")
        or item.get("source_type")
    )


def _temporal_family_claim(family: str) -> str:
    aliases = {
        "teblig": "TEBLIGLER",
        "tebligler": "TEBLIGLER",
        "mulga_kanun": "MULGA",
        "mulga": "MULGA",
        "cb_genelge": "CB_GENELGE",
        "cb_karar": "CB_KARAR",
        "cb_kararname": "CB_KARARNAME",
        "cb_yonetmelik": "CB_YONETMELIK",
    }
    normalized = _temporal_normalized(family)
    if not normalized:
        return "UNKNOWN"
    return aliases.get(normalized, normalized.upper())


def _temporal_effective_state(item: dict[str, Any] | None) -> str:
    if not isinstance(item, dict):
        return ""
    return _temporal_normalized(item.get("effective_state") or item.get("historical_source_effective_state"))


def _temporal_effective_state_claim(item: dict[str, Any] | None) -> str:
    state = _temporal_effective_state(item)
    if state in {"active", "current"}:
        return "active"
    if state == "amended":
        return "amended"
    if state in _TEMPORAL_REPEALED_STATES or state in _TEMPORAL_REPEAL_STATES:
        return "repealed"
    return "unknown"


def _temporal_item_role(item: dict[str, Any]) -> str:
    role = _temporal_normalized(item.get("relation_chain_role"))
    if role in {"historical_rule", "repeal_instrument", "current_law_basis"}:
        return role
    state = _temporal_effective_state(item)
    family = _temporal_family(item)
    text = _temporal_item_text(item)
    if state in _TEMPORAL_REPEAL_STATES:
        return "repeal_instrument"
    if role in {"repeal", "repeal_or_currentness_source"}:
        return "repeal_instrument"
    if role in {"current", "current_basis"}:
        return "current_law_basis"
    if state in _TEMPORAL_REPEALED_STATES or "mulga" in family:
        return "historical_rule"
    return ""


def _temporal_find_keyed_evidence(evidence: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    normalized_key = _temporal_normalized(key)
    if not normalized_key:
        return None
    for item in evidence:
        candidates = {
            _temporal_normalized(item.get("source_id")),
            _temporal_normalized(item.get("canonical_source_key_v2")),
            _temporal_normalized(item.get("binding_source_key")),
            _temporal_normalized(item.get("relation_chain_source_key")),
        }
        if normalized_key in candidates:
            return item
    return None


def _temporal_collect_evidence(
    *,
    assembled_evidence: list[dict[str, Any]] | None,
    trace_payload: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(assembled_evidence, list):
        found.extend(item for item in assembled_evidence if isinstance(item, dict))
    if isinstance(trace_payload, dict):
        for key in ("assembled_evidence", "rerank_list"):
            value = trace_payload.get(key)
            if isinstance(value, list):
                found.extend(item for item in value if isinstance(item, dict))
        context = trace_payload.get("context_assembly")
        if isinstance(context, dict) and isinstance(context.get("assembled_evidence"), list):
            found.extend(item for item in context["assembled_evidence"] if isinstance(item, dict))
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in found:
        marker = "|".join(
            _temporal_text(item.get(key))
            for key in ("source_id", "citation", "source_identifier", "article_or_section", "span_id")
        )
        if marker in seen:
            continue
        seen.add(marker)
        deduped.append(item)
    return deduped


def _temporal_trace_parent(trace_payload: dict[str, Any] | None, key: str) -> dict[str, Any]:
    if not isinstance(trace_payload, dict):
        return {}
    direct = trace_payload.get(key)
    if isinstance(direct, dict):
        return direct
    for parent_key in ("retrieval", "parsed_query", "query_signals", "context_assembly"):
        parent = trace_payload.get(parent_key)
        if isinstance(parent, dict) and isinstance(parent.get(key), dict):
            return parent[key]
    return {}


def _temporal_trace_question_text(trace_payload: dict[str, Any] | None) -> str:
    if not isinstance(trace_payload, dict):
        return ""
    direct = _temporal_text(trace_payload.get("question_raw") or trace_payload.get("question"))
    if direct:
        return direct
    for parent_key in ("query_signals", "parsed_query", "retrieval"):
        parent = trace_payload.get(parent_key)
        if not isinstance(parent, dict):
            continue
        value = _temporal_first_text(parent.get("user_query"), parent.get("retrieval_query"), parent.get("enriched_query"))
        if value:
            return value
    return ""


def _split_trace_family_values(family_resolution: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("predicted_family", "expected_family_prior"):
        values.append(_temporal_normalized(family_resolution.get(key)))
    for key in ("preferred_families", "fallback_families", "routing_families"):
        raw = family_resolution.get(key)
        if isinstance(raw, list):
            values.extend(_temporal_normalized(item) for item in raw)
    return [value for value in values if value]


def _split_family_candidate_has_signal(family_resolution: dict[str, Any], signal: str) -> bool:
    candidates = family_resolution.get("family_candidates")
    if not isinstance(candidates, list):
        return False
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        signals = candidate.get("signals")
        if isinstance(signals, list) and signal in {str(item) for item in signals}:
            return True
    return False


def _split_query_has_historical_surface_intent(question: str) -> bool:
    normalized = normalize_query_text(question or "")
    if not normalized:
        return False
    has_risk_term = any(term in normalized for term in _SPLIT_HISTORICAL_RISK_TERMS)
    has_context_term = any(term in normalized for term in _SPLIT_HISTORICAL_CONTEXT_TERMS)
    has_old_year = any(int(match.group(0)) < 2018 for match in re.finditer(r"\b(?:19|20)\d{2}\b", normalized))
    return bool(has_risk_term and (has_context_term or has_old_year))


def _s5_trace_family_surface(trace_payload: dict[str, Any] | None) -> str:
    if not isinstance(trace_payload, dict):
        return ""
    family_resolution = _temporal_trace_parent(trace_payload, "source_family_resolution")
    selector = _temporal_trace_parent(trace_payload, "article_span_selector")
    values: list[str] = []
    for parent in (trace_payload, family_resolution, selector):
        for key in (
            "predicted_family",
            "expected_family_prior",
            "preferred_families",
            "preferred_source_families",
            "fallback_families",
            "routing_families",
            "pre_filter_family_set",
            "reranked_family_set",
            "family_collision_pair",
            "collision_resolution_reason",
            "selected_family_source",
        ):
            raw = parent.get(key)
            if isinstance(raw, list):
                values.extend(_temporal_text(item) for item in raw)
            else:
                values.append(_temporal_text(raw))
    return normalize_query_text(" | ".join(value for value in values if value))


def _s5_trace_mentions_family(trace_payload: dict[str, Any] | None, family: str) -> bool:
    surface = _s5_trace_family_surface(trace_payload)
    if not surface:
        return False
    normalized_family = re.escape(normalize_query_text(family))
    return bool(re.search(rf"(?:^|[^a-z0-9_]){normalized_family}(?:$|[^a-z0-9_])", surface))


def _s5_query_has_undergraduate_university_course_signal(question: str) -> bool:
    normalized = normalize_query_text(question or "")
    if not normalized or "lisansustu" in normalized:
        return False
    has_university = "universite" in normalized or "universitesi" in normalized
    has_undergraduate = "on lisans" in normalized or re.search(r"(?:^|\s)lisans(?:\s|$)", normalized) is not None
    has_course_registration = any(
        term in normalized
        for term in (
            "ders",
            "kayit",
            "kredi",
            "sinav",
            "egitim ogretim",
        )
    )
    return bool(has_university and has_undergraduate and has_course_registration)


def _s5_viable_uy_candidate(item: dict[str, Any]) -> bool:
    if _temporal_family(item) != "uy":
        return False
    state = _temporal_effective_state(item) or "unknown"
    if state not in _SPLIT_ACTIVE_NON_REPEALED_STATES:
        return False
    title = normalize_query_text(_temporal_source_title(item))
    if "universite" not in title and "universitesi" not in title:
        return False
    if "lisansustu" in title:
        return False
    if "lisans" not in title:
        return False
    return bool(_temporal_article_raw(item) or _temporal_identifier_base(item))


def _s5_select_uy_boundary_candidate(
    *,
    evidence: list[dict[str, Any]],
    trace_payload: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not _s5_query_has_undergraduate_university_course_signal(_temporal_trace_question_text(trace_payload)):
        return None
    if not (_s5_trace_mentions_family(trace_payload, "uy") and _s5_trace_mentions_family(trace_payload, "yonetmelik")):
        return None
    for item in evidence:
        if _s5_viable_uy_candidate(item):
            return item
    return None


def _s5_query_has_current_law_exception_need(trace_payload: dict[str, Any] | None) -> bool:
    question = normalize_query_text(_temporal_trace_question_text(trace_payload))
    if not question:
        return False
    return any(term in question for term in _S5_CURRENT_LAW_EXCEPTION_TERMS)


def _s5_query_content_terms(trace_payload: dict[str, Any] | None) -> set[str]:
    question = normalize_query_text(_temporal_trace_question_text(trace_payload))
    terms = {
        token
        for token in re.findall(r"[a-z0-9]{4,}", question)
        if token not in _S5_QUERY_STOPWORDS
    }
    return terms


def _s5_current_law_candidate_score(item: dict[str, Any], query_terms: set[str]) -> int:
    family = _temporal_family(item)
    if family not in _SPLIT_ACTIVE_NON_MULGA_FAMILIES:
        return -1_000
    state = _temporal_effective_state(item) or "unknown"
    if state not in _SPLIT_ACTIVE_NON_REPEALED_STATES:
        return -1_000
    article = _temporal_article_raw(item)
    if not article or article == "0":
        return -1_000
    item_text = normalize_query_text(_temporal_item_text(item))
    overlap = {term for term in query_terms if term in item_text}
    score = 10 * len(overlap)
    if family in {"kanun", "khk"}:
        score += 25
    else:
        score += 15
    score += 10
    if "gecici madde" in item_text or "yururlukten kaldir" in item_text or "islenemeyen" in item_text:
        score -= 25
    if "uygulanmaz" in item_text or "mulga" in item_text or "8 yil sureyle" in item_text:
        score -= 25
    if "yuzde yirmi bes" in item_text or "%25" in item_text:
        score -= 15
    return score


def _s5_select_current_law_basis_exception_candidate(
    *,
    evidence: list[dict[str, Any]],
    roles: dict[str, dict[str, Any] | None],
    trace_payload: dict[str, Any] | None,
) -> dict[str, Any] | None:
    selected = roles.get("historical") or roles.get("selected")
    selected_family = _temporal_family(selected)
    selected_state = _temporal_effective_state(selected)
    if selected_state not in _TEMPORAL_REPEALED_STATES and "mulga" not in selected_family:
        return None
    if not _s5_query_has_current_law_exception_need(trace_payload):
        return None
    if not (
        (_s5_trace_mentions_family(trace_payload, "mulga") or _s5_trace_mentions_family(trace_payload, "mulga_kanun"))
        and _s5_trace_mentions_family(trace_payload, "kanun")
    ):
        return None
    query_terms = _s5_query_content_terms(trace_payload)
    best_item: dict[str, Any] | None = None
    best_score = -1_000
    for item in evidence:
        score = _s5_current_law_candidate_score(item, query_terms)
        if score > best_score:
            best_item = item
            best_score = score
    if best_item is not None and best_score >= 35:
        return best_item
    return None


def _s5_active_non_mulga_guard_fields(
    *,
    answer_contract: dict[str, Any],
    selected: dict[str, Any] | None,
    historical_surface_intent: bool,
    intent_reason: str,
) -> dict[str, Any]:
    selected_family = _temporal_family(selected)
    claimed_family = _temporal_normalized(answer_contract.get("source_family_claimed"))
    guard_type = "active_non_mulga_claim_preservation"
    reason = "active_selected_non_mulga_claim_preserved"
    if historical_surface_intent:
        guard_type = "active_non_mulga_historical_surface_clamp"
        reason = f"active_selected_non_mulga_blocks_historical_surface:{intent_reason}"
    if selected_family in {"teblig", "tebligler"} and claimed_family in {"mulga", "mulga_kanun"}:
        guard_type = "teblig_domain_mismatch_guard"
        reason = f"active_teblig_blocks_mulga_claim_overwrite:{intent_reason}"
    if selected_family == "uy" and claimed_family in {"yonetmelik", "kky"}:
        guard_type = "uy_yonetmelik_family_boundary_guard"
        reason = f"active_uy_blocks_generic_yonetmelik_claim_overwrite:{intent_reason}"
    return _s5_family_identifier_guard_fields(
        applied=True,
        guard_type=guard_type,
        claim_family_preserved=True,
        claim_identifier_preserved=True,
        article_surface_preserved=True,
        reason=reason,
    )


def _split_temporal_historical_surface_intent(
    *,
    answer_contract: dict[str, Any],
    selected: dict[str, Any] | None,
    trace_payload: dict[str, Any] | None,
) -> tuple[bool, str]:
    selected_family = _temporal_family(selected)
    selected_state = _temporal_effective_state(selected)
    if selected_state in _TEMPORAL_REPEALED_STATES or "mulga" in selected_family:
        return True, "selected_evidence_historical_or_repealed"

    family_resolution = _temporal_trace_parent(trace_payload, "source_family_resolution")
    selector = _temporal_trace_parent(trace_payload, "article_span_selector")
    question = _temporal_trace_question_text(trace_payload)
    if _temporal_truthy(selector.get("legacy_candidate_preferred")):
        return True, "legacy_candidate_preferred"
    if _split_family_candidate_has_signal(family_resolution, "legacy_source_risk_signal"):
        return True, "legacy_source_risk_signal"
    if _temporal_truthy(family_resolution.get("repealed_scope_detected")) and _split_query_has_historical_surface_intent(question):
        return True, "repealed_scope_with_historical_surface_intent"
    family_values = set(_split_trace_family_values(family_resolution))
    if {"mulga", "mulga_kanun"} & family_values and _split_query_has_historical_surface_intent(question):
        return True, "mulga_family_context_with_historical_surface_intent"
    if _split_query_has_historical_surface_intent(question):
        return True, "query_historical_surface_intent"
    if (
        _temporal_normalized(answer_contract.get("source_family_claimed")) == "mulga"
        and selected_state not in _SPLIT_ACTIVE_NON_REPEALED_STATES
    ):
        return True, "contract_mulga_with_non_active_selected_evidence"
    return False, "no_historical_surface_intent"


def _split_current_law_basis_primary_allowed(
    *,
    answer_contract: dict[str, Any],
    trace_payload: dict[str, Any] | None,
) -> bool:
    answer_mode = _temporal_text(answer_contract.get("answer_mode"))
    if answer_mode in {"repealed_transition_answer", "not_currently_applicable_answer"}:
        return True
    normalized_question = normalize_query_text(_temporal_trace_question_text(trace_payload))
    return any(
        term in normalized_question
        for term in (
            "bugun",
            "guncel",
            "mevcut",
            "hala",
            "halen",
            "gecerli",
            "gecis",
            "yerine gec",
            "dogrudan uygulan",
            "guvenli",
            "risk",
            "2026",
        )
    )


def _split_temporal_policy(
    *,
    answer_contract: dict[str, Any],
    roles: dict[str, dict[str, Any] | None],
    relation_chain_present: bool,
    missing_reason: str,
    trace_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    selected = roles.get("selected")
    selected_family = _temporal_family(selected)
    selected_state = _temporal_effective_state(selected) or "unknown"
    historical_surface_intent, intent_reason = _split_temporal_historical_surface_intent(
        answer_contract=answer_contract,
        selected=selected,
        trace_payload=trace_payload,
    )
    if relation_chain_present and missing_reason == "none":
        return {
            "split_temporal_policy_applied": True,
            "claim_family_rewrite_allowed": "controlled",
            "historical_claim_surface_allowed": True,
            "split_temporal_policy_bucket": "relation_chain_historical_three_part_claim",
            "split_temporal_policy_reason": "complete_relation_chain",
            "claim_identifier_rewrite_allowed": "controlled",
            "temporal_support_only": False,
            "current_law_basis_primary_allowed": _split_current_law_basis_primary_allowed(
                answer_contract=answer_contract,
                trace_payload=trace_payload,
            ),
            **_s5_family_identifier_guard_fields(
                applied=False,
                guard_type="relation_chain_controlled_historical_claim",
                reason="complete_relation_chain_controls_historical_surface",
            ),
        }
    if (
        not relation_chain_present
        and selected_family in _SPLIT_ACTIVE_NON_MULGA_FAMILIES
        and selected_state in _SPLIT_ACTIVE_NON_REPEALED_STATES
    ):
        return {
            "split_temporal_policy_applied": True,
            "claim_family_rewrite_allowed": False,
            "historical_claim_surface_allowed": False,
            "split_temporal_policy_bucket": "active_non_mulga_preserve_family",
            "split_temporal_policy_reason": f"active_selected_evidence_without_relation_chain:{intent_reason}",
            "claim_identifier_rewrite_allowed": False,
            "temporal_support_only": True,
            "current_law_basis_primary_allowed": False,
            **_s5_active_non_mulga_guard_fields(
                answer_contract=answer_contract,
                selected=selected,
                historical_surface_intent=historical_surface_intent,
                intent_reason=intent_reason,
            ),
        }
    if not relation_chain_present and historical_surface_intent:
        selected_article_present = bool(_temporal_article_raw(selected))
        return {
            "split_temporal_policy_applied": True,
            "claim_family_rewrite_allowed": "limited_to_historical_surface",
            "historical_claim_surface_allowed": True,
            "split_temporal_policy_bucket": "legacy_mulga_historical_surface_without_relation_chain",
            "split_temporal_policy_reason": intent_reason,
            "claim_identifier_rewrite_allowed": "limited_to_historical_surface",
            "temporal_support_only": False,
            "current_law_basis_primary_allowed": False,
            **_s5_family_identifier_guard_fields(
                applied=selected_article_present,
                guard_type="historical_article_surface_guard" if selected_article_present else "not_applicable",
                claim_family_preserved=False,
                claim_identifier_preserved=selected_article_present,
                article_surface_preserved=selected_article_present,
                reason=(
                    f"historical_surface_claim_keeps_selected_article:{intent_reason}"
                    if selected_article_present
                    else f"historical_surface_without_selected_article:{intent_reason}"
                ),
            ),
        }
    return {
        "split_temporal_policy_applied": False,
        "claim_family_rewrite_allowed": False,
        "historical_claim_surface_allowed": False,
        "split_temporal_policy_bucket": "not_applicable",
        "split_temporal_policy_reason": intent_reason,
        "claim_identifier_rewrite_allowed": False,
        "temporal_support_only": True,
        "current_law_basis_primary_allowed": False,
        **_s5_family_identifier_guard_fields(reason=intent_reason),
    }


def _temporal_relation_chain_present(evidence: list[dict[str, Any]]) -> bool:
    return any(
        _temporal_truthy(item.get("relation_chain_expansion_applied"))
        or bool(_temporal_text(item.get("relation_chain_role")))
        for item in evidence
    )


def _temporal_roles(evidence: list[dict[str, Any]]) -> dict[str, dict[str, Any] | None]:
    roles: dict[str, dict[str, Any] | None] = {
        "historical": None,
        "repeal": None,
        "current": None,
        "selected": evidence[0] if evidence else None,
    }
    current_key = ""
    repeal_key = ""
    historical_key = ""
    for item in evidence:
        current_key = current_key or _temporal_text(item.get("relation_chain_current_basis_source_key"))
        repeal_key = repeal_key or _temporal_text(item.get("relation_chain_repeal_source_key"))
        historical_key = historical_key or _temporal_text(item.get("relation_chain_source_key"))
    if current_key:
        roles["current"] = _temporal_find_keyed_evidence(evidence, current_key)
    if repeal_key:
        roles["repeal"] = _temporal_find_keyed_evidence(evidence, repeal_key)
    if historical_key:
        roles["historical"] = _temporal_find_keyed_evidence(evidence, historical_key)

    for item in evidence:
        role = _temporal_item_role(item)
        if role == "historical_rule" and roles["historical"] is None:
            roles["historical"] = item
        elif role == "repeal_instrument" and roles["repeal"] is None:
            roles["repeal"] = item
        elif role == "current_law_basis" and roles["current"] is None:
            roles["current"] = item

    selected = roles["selected"]
    if isinstance(selected, dict) and _temporal_item_role(selected) == "historical_rule":
        roles["historical"] = selected
    return roles


def _temporal_context_present(answer_contract: dict[str, Any], evidence: list[dict[str, Any]]) -> bool:
    del evidence
    answer_mode = _temporal_text(answer_contract.get("answer_mode"))
    effective_state = _temporal_normalized(answer_contract.get("effective_state_claimed"))
    source_family = _temporal_normalized(answer_contract.get("source_family_claimed"))
    if answer_mode in _TEMPORAL_REPEALED_MODES or effective_state in _TEMPORAL_REPEALED_STATES or "mulga" in source_family:
        return True
    return False


def _temporal_line(label: str, item: dict[str, Any] | None, description: str) -> str:
    if not isinstance(item, dict):
        return f"- {label}: {description}"
    title = _temporal_source_title(item)
    identifier = _temporal_identifier_claim(item)
    article = _temporal_article_claim(item)
    excerpt = _temporal_excerpt(item)
    citation = _temporal_citation(item)
    basis = f"{title}; {identifier}; {article}"
    if excerpt:
        return f"- {label}: {description} {basis}. {excerpt} [Kaynak: {citation}]"
    return f"- {label}: {description} {basis} [Kaynak: {citation}]"


def _temporal_build_role_answer(
    *,
    roles: dict[str, dict[str, Any] | None],
    relation_chain_present: bool,
    missing_reason: str,
) -> str:
    lines: list[str] = [TEMPORAL_CLAIM_ALIGNMENT_HEADER]
    historical = roles.get("historical") or roles.get("selected")
    repeal = roles.get("repeal")
    current = roles.get("current")
    lines.append(
        _temporal_line(
            "Tarihsel kaynak",
            historical,
            "Bu kaynak yalnız tarihsel dönem bağlamında okunmalıdır.",
        )
    )
    if repeal is not None:
        lines.append(
            _temporal_line(
                "Yürürlük sınırı",
                repeal,
                "Bu kanıt tarihsel kaynağın yürürlükten kaldırılması sınırını gösterir.",
            )
        )
    if current is not None:
        lines.append(
            _temporal_line(
                "Kanun bağlantısı",
                current,
                "İlişki zincirinde yer alan ek kanun bağlantısıdır; tarihsel kaynak metniyle karıştırılmamalıdır.",
            )
        )
    if not relation_chain_present or missing_reason != "none":
        lines.append(
            "- Sınır: İlişki zinciri tam doğrulanmadığı için cevap tarihsel/yürürlük değerlendirmesiyle sınırlıdır; "
            "eksik neden: "
            + missing_reason
            + "."
        )
    return "\n".join(lines)


def _temporal_missing_reason(
    *,
    relation_chain_present: bool,
    roles: dict[str, dict[str, Any] | None],
) -> str:
    if not relation_chain_present:
        return "no_relation_chain"
    if roles.get("repeal") is None:
        return "missing_repeal_source"
    if roles.get("current") is None:
        return "missing_current_basis_source"
    if roles.get("historical") is None and roles.get("selected") is None:
        return "no_historical_or_repealed_evidence"
    return "none"


def _temporal_status(
    *,
    relation_chain_present: bool,
    missing_reason: str,
    contract: dict[str, Any],
    roles: dict[str, dict[str, Any] | None],
) -> str:
    if missing_reason == "no_historical_or_repealed_evidence":
        return "no_historical_context"
    effective_state = _temporal_normalized(contract.get("effective_state_claimed"))
    if effective_state == "active" and _temporal_context_present(contract, [item for item in roles.values() if isinstance(item, dict)]):
        return "corrected_repealed_not_active"
    if not relation_chain_present or missing_reason != "none":
        return "qualified_missing_relation"
    return "aligned"


def _temporal_contract_patch(
    *,
    answer_text: str,
    answer_contract: dict[str, Any],
    roles: dict[str, dict[str, Any] | None],
    relation_chain_present: bool,
    missing_reason: str,
    consistency_status: str,
    split_policy: dict[str, Any],
) -> dict[str, Any]:
    historical = roles.get("historical") or roles.get("selected")
    repeal = roles.get("repeal")
    current = roles.get("current")
    current_primary_allowed = bool(split_policy.get("current_law_basis_primary_allowed"))
    primary = (
        current
        if relation_chain_present and current is not None and missing_reason == "none" and current_primary_allowed
        else historical or repeal or current
    )
    primary_role = (
        "current_law_basis"
        if primary is current and relation_chain_present and current is not None and missing_reason == "none"
        else "historical_rule"
    )
    source_identifier = _temporal_identifier_claim(primary)
    article_or_section = _temporal_article_claim(primary)
    answer_mode = (
        answer_contract.get("answer_mode")
        if answer_contract.get("answer_mode") in _TEMPORAL_REPEALED_MODES
        else "qualified_answer"
    )
    patch = {
        "temporal_claim_alignment_applied": True,
        "temporal_claim_primary_role": primary_role,
        "temporal_claim_historical_source_key": _temporal_source_key(historical),
        "temporal_claim_repeal_source_key": _temporal_source_key(repeal),
        "temporal_claim_current_basis_source_key": _temporal_source_key(current),
        "temporal_claim_consistency_status": consistency_status,
        "temporal_claim_missing_reason": missing_reason,
        "temporal_claim_historical_identifier": _temporal_identifier_claim(historical) if historical else "",
        "temporal_claim_repeal_identifier": _temporal_identifier_claim(repeal) if repeal else "",
        "temporal_claim_current_basis_identifier": _temporal_identifier_claim(current) if current else "",
        "answer_text": answer_text,
        "final_answer": answer_text,
        "answer_mode": answer_mode,
        "grounding_status": "partially_grounded",
        "source_family_claimed": "MULGA",
        "source_title_claimed": _temporal_source_title(primary),
        "source_identifier_claimed": source_identifier,
        "article_or_section_claimed": article_or_section,
        "effective_state_claimed": "repealed",
        "temporal_qualification": _temporal_first_text(
            answer_contract.get("temporal_qualification"),
            "historical/repealed",
        ),
        "final_reason": (
            f"dayanak=MULGA:{source_identifier}; madde={article_or_section}; "
            f"yururluk=repealed; grounding=partially_grounded; sonuc={answer_mode}; belirsizlik=var"
        ),
        "needs_manual_review": True,
        "unsupported_reason": None,
        "answer_suppressed_due_to_evidence_gap": False,
        "support_insufficient_for_specific_claim": False,
        "insufficient_canonical_span_evidence": False,
        **split_policy,
    }
    try:
        current_confidence = int(answer_contract.get("confidence_0_100") or 0)
    except (TypeError, ValueError):
        current_confidence = 0
    patch["confidence_0_100"] = min(max(current_confidence, 40), 60)
    return patch


def _temporal_active_preservation_patch(
    *,
    answer_text: str,
    answer_contract: dict[str, Any],
    selected: dict[str, Any],
    consistency_status: str,
    split_policy: dict[str, Any],
) -> dict[str, Any]:
    selected_family = _temporal_family(selected)
    source_family = _temporal_family_claim(selected_family)
    source_identifier = _temporal_identifier_claim(selected)
    article_or_section = _temporal_article_claim(selected)
    effective_state = _temporal_effective_state_claim(selected)
    answer_mode = _temporal_text(answer_contract.get("answer_mode"))
    if answer_mode in _TEMPORAL_REPEALED_MODES or not answer_mode:
        answer_mode = "qualified_answer"
    grounding_status = _temporal_text(answer_contract.get("grounding_status")) or "partially_grounded"
    needs_manual_review = bool(answer_contract.get("needs_manual_review"))
    unsupported_reason = answer_contract.get("unsupported_reason")
    if unsupported_reason in {"temporal_mismatch", "source_validity_unknown"}:
        unsupported_reason = None
    final_reason = (
        f"dayanak={source_family}:{source_identifier}; madde={article_or_section}; "
        f"yururluk={effective_state}; grounding={grounding_status}; sonuc={answer_mode}; "
        f"belirsizlik={'var' if needs_manual_review else 'yok'}"
    )
    try:
        current_confidence = int(answer_contract.get("confidence_0_100") or 0)
    except (TypeError, ValueError):
        current_confidence = 0
    return {
        "temporal_claim_alignment_applied": True,
        "temporal_claim_primary_role": "selected_active_source",
        "temporal_claim_historical_source_key": "",
        "temporal_claim_repeal_source_key": "",
        "temporal_claim_current_basis_source_key": "",
        "temporal_claim_consistency_status": consistency_status,
        "temporal_claim_missing_reason": "support_only_active_non_mulga_preservation",
        "temporal_claim_historical_identifier": "",
        "temporal_claim_repeal_identifier": "",
        "temporal_claim_current_basis_identifier": "",
        "answer_text": answer_text,
        "final_answer": answer_text,
        "answer_mode": answer_mode,
        "grounding_status": grounding_status,
        "source_family_claimed": source_family,
        "source_title_claimed": _temporal_source_title(selected),
        "source_identifier_claimed": source_identifier,
        "article_or_section_claimed": article_or_section,
        "effective_state_claimed": effective_state,
        "temporal_qualification": _temporal_first_text(answer_contract.get("temporal_qualification"), "current"),
        "final_reason": final_reason,
        "needs_manual_review": needs_manual_review,
        "unsupported_reason": unsupported_reason,
        "confidence_0_100": current_confidence,
        **split_policy,
    }


def apply_temporal_claim_alignment(
    *,
    answer_text: str,
    answer_contract: dict[str, Any] | None,
    assembled_evidence: list[dict[str, Any]] | None = None,
    trace_payload: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    if not isinstance(answer_contract, dict):
        return answer_text, {
            "temporal_claim_alignment_applied": False,
            "temporal_claim_primary_role": "",
            "temporal_claim_historical_source_key": "",
            "temporal_claim_repeal_source_key": "",
            "temporal_claim_current_basis_source_key": "",
            "temporal_claim_consistency_status": "no_historical_context",
            "temporal_claim_missing_reason": "no_historical_or_repealed_evidence",
            "split_temporal_policy_applied": False,
            "claim_family_rewrite_allowed": False,
            "historical_claim_surface_allowed": False,
            "split_temporal_policy_bucket": "not_applicable",
            "split_temporal_policy_reason": "no_contract",
            "claim_identifier_rewrite_allowed": False,
            "temporal_support_only": True,
            "current_law_basis_primary_allowed": False,
            **_s5_family_identifier_guard_fields(reason="no_contract"),
        }
    evidence = _temporal_collect_evidence(assembled_evidence=assembled_evidence, trace_payload=trace_payload)
    relation_chain_present = _temporal_relation_chain_present(evidence)
    uy_boundary_candidate = _s5_select_uy_boundary_candidate(
        evidence=evidence,
        trace_payload=trace_payload,
    )
    if isinstance(uy_boundary_candidate, dict) and not relation_chain_present:
        split_policy = {
            "split_temporal_policy_applied": True,
            "claim_family_rewrite_allowed": False,
            "historical_claim_surface_allowed": False,
            "split_temporal_policy_bucket": "active_non_mulga_preserve_family",
            "split_temporal_policy_reason": "s5_uy_yonetmelik_boundary_candidate_available",
            "claim_identifier_rewrite_allowed": False,
            "temporal_support_only": True,
            "current_law_basis_primary_allowed": False,
            **_s5_family_identifier_guard_fields(
                applied=True,
                guard_type="uy_yonetmelik_family_boundary_guard",
                claim_family_preserved=True,
                claim_identifier_preserved=True,
                article_surface_preserved=True,
                reason="uy_candidate_available_with_undergraduate_course_registration_terms",
            ),
        }
        patch = _temporal_active_preservation_patch(
            answer_text=answer_text,
            answer_contract=answer_contract,
            selected=uy_boundary_candidate,
            consistency_status="uy_family_boundary_preserved",
            split_policy=split_policy,
        )
        return answer_text, patch
    if not relation_chain_present and not _temporal_context_present(answer_contract, evidence):
        return answer_text, {
            "temporal_claim_alignment_applied": False,
            "temporal_claim_primary_role": "",
            "temporal_claim_historical_source_key": "",
            "temporal_claim_repeal_source_key": "",
            "temporal_claim_current_basis_source_key": "",
            "temporal_claim_consistency_status": "no_historical_context",
            "temporal_claim_missing_reason": "no_historical_or_repealed_evidence",
            "split_temporal_policy_applied": False,
            "claim_family_rewrite_allowed": False,
            "historical_claim_surface_allowed": False,
            "split_temporal_policy_bucket": "not_applicable",
            "split_temporal_policy_reason": "no_historical_or_repealed_evidence",
            "claim_identifier_rewrite_allowed": False,
            "temporal_support_only": True,
            "current_law_basis_primary_allowed": False,
            **_s5_family_identifier_guard_fields(reason="no_historical_or_repealed_evidence"),
        }
    roles = _temporal_roles(evidence)
    if roles.get("historical") is None and roles.get("repeal") is None and roles.get("selected") is None:
        return answer_text, {
            "temporal_claim_alignment_applied": False,
            "temporal_claim_primary_role": "",
            "temporal_claim_historical_source_key": "",
            "temporal_claim_repeal_source_key": "",
            "temporal_claim_current_basis_source_key": "",
            "temporal_claim_consistency_status": "no_historical_context",
            "temporal_claim_missing_reason": "no_historical_or_repealed_evidence",
            "split_temporal_policy_applied": False,
            "claim_family_rewrite_allowed": False,
            "historical_claim_surface_allowed": False,
            "split_temporal_policy_bucket": "not_applicable",
            "split_temporal_policy_reason": "no_historical_or_repealed_evidence",
            "claim_identifier_rewrite_allowed": False,
            "temporal_support_only": True,
            "current_law_basis_primary_allowed": False,
            **_s5_family_identifier_guard_fields(reason="no_historical_or_repealed_evidence"),
        }
    missing_reason = _temporal_missing_reason(relation_chain_present=relation_chain_present, roles=roles)
    consistency_status = _temporal_status(
        relation_chain_present=relation_chain_present,
        missing_reason=missing_reason,
        contract=answer_contract,
        roles=roles,
    )
    split_policy = _split_temporal_policy(
        answer_contract=answer_contract,
        roles=roles,
        relation_chain_present=relation_chain_present,
        missing_reason=missing_reason,
        trace_payload=trace_payload,
    )
    current_law_exception_candidate = None
    if split_policy.get("split_temporal_policy_bucket") == "legacy_mulga_historical_surface_without_relation_chain":
        current_law_exception_candidate = _s5_select_current_law_basis_exception_candidate(
            evidence=evidence,
            roles=roles,
            trace_payload=trace_payload,
        )
    if isinstance(current_law_exception_candidate, dict):
        exception_policy = {
            **split_policy,
            "split_temporal_policy_bucket": "current_law_basis_exception_from_historical_surface",
            "split_temporal_policy_reason": (
                "s5_current_law_basis_candidate_available:"
                + str(split_policy.get("split_temporal_policy_reason") or "unknown")
            ),
            "claim_family_rewrite_allowed": False,
            "historical_claim_surface_allowed": False,
            "claim_identifier_rewrite_allowed": False,
            "temporal_support_only": True,
            "current_law_basis_primary_allowed": True,
            **_s5_family_identifier_guard_fields(
                applied=True,
                guard_type="historical_surface_current_law_basis_exception_guard",
                claim_family_preserved=True,
                claim_identifier_preserved=True,
                article_surface_preserved=True,
                reason="active_current_law_candidate_available_for_currentness_question",
            ),
        }
        patch = _temporal_active_preservation_patch(
            answer_text=answer_text,
            answer_contract=answer_contract,
            selected=current_law_exception_candidate,
            consistency_status="current_law_basis_preserved",
            split_policy=exception_policy,
        )
        return answer_text, patch
    if split_policy.get("split_temporal_policy_bucket") == "active_non_mulga_preserve_family":
        selected = roles.get("selected")
        if isinstance(selected, dict):
            patch = _temporal_active_preservation_patch(
                answer_text=answer_text,
                answer_contract=answer_contract,
                selected=selected,
                consistency_status="active_non_mulga_preserved",
                split_policy=split_policy,
            )
            return answer_text, patch
    if (answer_text or "").strip().startswith(TEMPORAL_CLAIM_ALIGNMENT_HEADER):
        aligned_answer = answer_text.strip()
    else:
        aligned_answer = _temporal_build_role_answer(
            roles=roles,
            relation_chain_present=relation_chain_present,
            missing_reason=missing_reason,
        )
    patch = _temporal_contract_patch(
        answer_text=aligned_answer,
        answer_contract=answer_contract,
        roles=roles,
        relation_chain_present=relation_chain_present,
        missing_reason=missing_reason,
        consistency_status=consistency_status,
        split_policy=split_policy,
    )
    return aligned_answer, patch


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
