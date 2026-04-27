from __future__ import annotations

import hashlib
import re
from typing import Any

from faz2a_hardening import dedupe_strings, normalize_query_text, normalize_whitespace
from rag.required_slot_matrix import (
    RequiredSlotResolution,
    resolve_required_slot_matrix,
    runtime_slots_for_matrix_slot,
)


def answer_template_for_query(query: str) -> str:
    normalized = normalize_query_text(query or "")
    if any(
        term in normalized
        for term in (
            "usul",
            "basvuru",
            "itiraz",
            "sure",
            "dava sart",
            "on sart",
            "tescil",
            "ilan",
            "noter",
            "noterce",
            "yeterli midir",
            "yeterli mi",
        )
    ):
        return "procedure"
    if any(term in normalized for term in ("istisna", "muaf", "haric", "sakli", "uygulanmaz")):
        return "exception"
    if any(term in normalized for term in ("kosul", "sart", "hangi hallerde", "aranir", "gerekir")):
        return "condition"
    if any(
        term in normalized
        for term in (
            "fark",
            "karsilastir",
            "yoksa",
            "eski",
            "guncel",
            "guncellik",
            "hala",
            "tarih",
            "gecici",
            "hangisi",
        )
    ):
        return "comparison_or_temporal"
    return "direct"


def query_contains_any(normalized_query: str, terms: tuple[str, ...]) -> bool:
    return any(term in normalized_query for term in terms)


def source_family_resolution_slot_values(
    source_family_resolution: Any,
    key: str,
) -> list[str]:
    if isinstance(source_family_resolution, dict):
        raw_value = source_family_resolution.get(key)
    elif source_family_resolution is not None:
        raw_value = getattr(source_family_resolution, key, None)
    else:
        raw_value = None

    if raw_value is None:
        return []
    if isinstance(raw_value, str):
        return [raw_value]
    if isinstance(raw_value, (list, tuple, set)):
        values: list[str] = []
        for item in raw_value:
            if isinstance(item, dict):
                values.append(str(item.get("family") or ""))
            else:
                values.append(str(getattr(item, "family", item) or ""))
        return values
    return [str(raw_value)]


def source_families_for_required_slot_matrix(
    *,
    requested_source_families: list[str] | None = None,
    source_family_resolution: Any = None,
    chunks: list[Any] | None = None,
    resolve_chunk_routing_family: Any = None,
    resolve_chunk_source_family: Any = None,
) -> list[str]:
    families: list[str] = []
    families.extend(requested_source_families or [])
    for key in (
        "predicted_family",
        "expected_family_prior",
        "preferred_families",
        "routing_families",
        "fallback_families",
        "family_candidates",
    ):
        families.extend(source_family_resolution_slot_values(source_family_resolution, key))
    for chunk in (chunks or [])[:8]:
        if resolve_chunk_routing_family is not None:
            families.append(resolve_chunk_routing_family(chunk) or "")
        if resolve_chunk_source_family is not None:
            families.append(resolve_chunk_source_family(chunk) or "")
    return dedupe_strings([family for family in families if str(family or "").strip()])


def resolve_required_slot_matrix_for_query(
    *,
    query: str,
    template: str,
    requested_source_families: list[str] | None = None,
    source_family_resolution: Any = None,
    chunks: list[Any] | None = None,
    resolve_chunk_routing_family: Any = None,
    resolve_chunk_source_family: Any = None,
) -> RequiredSlotResolution:
    return resolve_required_slot_matrix(
        query=query,
        answer_template=template,
        source_families=source_families_for_required_slot_matrix(
            requested_source_families=requested_source_families,
            source_family_resolution=source_family_resolution,
            chunks=chunks,
            resolve_chunk_routing_family=resolve_chunk_routing_family,
            resolve_chunk_source_family=resolve_chunk_source_family,
        ),
    )


def must_have_fact_slots_for_query(query: str, template: str) -> list[str]:
    normalized = normalize_query_text(query or "")
    slots = ["result_or_holding", "governing_source"]
    if query_contains_any(
        normalized,
        (
            "hangi mevzuat",
            "hangi duzenleme",
            "hangi belge",
            "hangi kaynak",
            "tuzuk",
            "yonetmelik",
            "teblig",
            "karar",
            "genelge",
            "kararname",
        ),
    ):
        slots.extend(["exact_source_identity", "document_selection_reason"])
    if query_contains_any(normalized, ("madde", "fikra", "bent", "paragraf", "hukum")):
        slots.append("article_or_span")
    if template == "procedure":
        slots.append("procedure_or_consequence")
    if template == "exception":
        slots.extend(["exception_or_limitation", "scenario_applicability"])
    if template == "condition":
        slots.append("scenario_applicability")
    if query_contains_any(normalized, ("istisna", "muaf", "haric", "sakli", "uygulanmaz")):
        slots.append("exception_or_limitation")
    if query_contains_any(normalized, ("kosul", "sart", "hangi hallerde", "aranir", "gerekir")):
        slots.append("scenario_applicability")
    if template == "comparison_or_temporal":
        slots.append("temporal_validity")
    if query_contains_any(
        normalized,
        (
            "guncel",
            "guncellik",
            "hala",
            "halen yururlukte",
            "yururlukte mi",
            "yururluk",
            "mulga",
            "eski",
            "gecici",
            "son durum",
            "ne zaman yururluge",
            "dogrudan uygulan",
            "dogrudan hukum",
            "guvenli midir",
            "riskli",
            "hatali",
        ),
    ):
        slots.append("temporal_validity")
    if query_needs_historical_transition_slots(normalized):
        slots.extend(["historical_period", "current_applicability", "transition_or_replacement_rule"])
    elif query_needs_current_applicability_slot(normalized):
        slots.append("current_applicability")
    if query_contains_any(
        normalized,
        (
            "ust norm",
            "alt norm",
            "kanun mu",
            "yonetmelik mi",
            "hangisi uygulanir",
            "normlar hiyerarsisi",
            "kanuna aykiri",
        ),
    ) or (
        "yoksa" in normalized
        and query_contains_any(normalized, ("kanun", "yonetmelik", "teblig", "tuzuk", "genelge", "karar"))
    ):
        slots.append("hierarchy_or_conflict_rule")
    return dedupe_strings(slots)


def query_needs_historical_transition_slots(normalized_query: str) -> bool:
    historical_or_repealed = query_contains_any(
        normalized_query,
        (
            "mulga",
            "mülga",
            "ilga",
            "yururlukten kaldir",
            "yururlukten kalk",
            "eski metin",
            "eski khk",
            "eski tuzuk",
            "eski tüzük",
            "eski yonetmelik",
            "eski yönetmelik",
            "eski yonetmeligi",
            "eski yönetmeliği",
            "eski duzenleme",
            "eski düzenleme",
            "onceki duzenleme",
            "tarihsel",
            "o tarihte",
            "gecis hukmu",
            "gecici madde",
            "yerine gecen",
            "yerini alan",
        ),
    )
    direct_risk = query_contains_any(
        normalized_query,
        (
            "dogrudan uygulan",
            "dogrudan hukum",
            "esas almak",
            "guvenli midir",
            "riskli",
            "hatali",
            "hata",
            "guncellik hatasi",
        ),
    )
    historical_year = bool(re.search(r"(?<!\d)(?:19\d{2}|200\d|201\d)(?!\d)", normalized_query))
    return bool(historical_or_repealed or (historical_year and direct_risk))


def query_needs_current_applicability_slot(normalized_query: str) -> bool:
    return query_contains_any(
        normalized_query,
        (
            "bugun",
            "guncel",
            "guncellik",
            "halen",
            "hala",
            "yururlukte mi",
            "gecerli mi",
            "son durum",
            "2026'da dogrudan",
            "2026 da dogrudan",
        ),
    )


_REQUIRED_SLOT_SCHEMA: dict[str, dict[str, str]] = {
    "result_or_holding": {
        "description": "Kaynağın soruya bağlanan kısa hüküm/sonuç içeriği.",
        "evidence_policy": "selected_span_excerpt",
    },
    "governing_source": {
        "description": "Cevabın merkez aldığı kaynak ailesi ve belge.",
        "evidence_policy": "source_metadata_or_citation",
    },
    "exact_source_identity": {
        "description": "Belge adı/numarası ve kaynak kimliği.",
        "evidence_policy": "source_identifier_metadata",
    },
    "article_or_span": {
        "description": "Seçilen madde, fıkra veya span kimliği.",
        "evidence_policy": "selector_span_or_citation",
    },
    "temporal_validity": {
        "description": "Yürürlük/güncellik durumu ve tarihsel bağ.",
        "evidence_policy": "effective_state_metadata_or_temporal_clause",
    },
    "historical_period": {
        "description": "Mülga/tarihsel kaynaklarda uygulanabilir dönem.",
        "evidence_policy": "effective_state_or_repeal_metadata",
    },
    "current_applicability": {
        "description": "Kaynağın bugünkü/güncel doğrudan uygulanabilirliği.",
        "evidence_policy": "effective_state_with_cautious_current_scope",
    },
    "transition_or_replacement_rule": {
        "description": "Geçiş, yerine geçen düzenleme veya bu bilginin kanıtta açık olup olmadığı.",
        "evidence_policy": "explicit_transition_clause_or_temporal_safety_limit",
    },
    "procedure_or_consequence": {
        "description": "Usul, süre, yaptırım, bildirim veya sonuç.",
        "evidence_policy": "selected_span_excerpt",
    },
    "scenario_applicability": {
        "description": "Somut olaya uygulanma şartı veya kapsam.",
        "evidence_policy": "selected_span_excerpt",
    },
    "exception_or_limitation": {
        "description": "İstisna, sınırlama, muafiyet veya uygulanmama hali.",
        "evidence_policy": "selected_span_excerpt",
    },
    "document_selection_reason": {
        "description": "Neden bu belgenin seçildiği.",
        "evidence_policy": "source_identity_and_query_family_alignment",
    },
    "hierarchy_or_conflict_rule": {
        "description": "Normlar arası öncelik/çatışma veya dayanak ilişkisi.",
        "evidence_policy": "selected_span_excerpt",
    },
}


def required_slot_schema(required_slots: list[str]) -> list[dict[str, str]]:
    return [
        {"slot_name": slot, **_REQUIRED_SLOT_SCHEMA.get(slot, {"description": "", "evidence_policy": ""})}
        for slot in required_slots
    ]


def compact_slot_value(value: str, *, max_len: int = 360) -> str:
    text = normalize_whitespace(value or "")
    if len(text) <= max_len:
        return text
    truncated = text[: max_len - 1].rsplit(" ", 1)[0].strip()
    return f"{truncated}…"


def slot_quote_hash(value: str) -> str:
    if not value:
        return ""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


_ANSWER_SLOT_EXTRACTION_VERSION = "phase18b-2026-04-25"
_DETERMINISTIC_MATRIX_SLOTS = {
    "governing_source",
    "exact_source_identity",
    "article_or_span",
    "selected_primary_source",
    "source_family",
    "identifier",
    "issuer",
    "circular_number_or_date",
    "decision_number",
    "teblig_identifier",
    "effective_state",
    "effective_period",
    "effective_date",
    "current_source",
    "source_is_repealed_or_historical",
    "applicable_period",
}


def answer_slot_extraction_method(matrix_slot: str) -> str:
    return "deterministic" if matrix_slot in _DETERMINISTIC_MATRIX_SLOTS else "hybrid"


def best_evidence_row_for_matrix_slot(
    matrix_slot: str,
    evidence_slot_values: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    runtime_candidates = runtime_slots_for_matrix_slot(matrix_slot)
    rows_by_slot = {
        str(row.get("slot_name") or ""): row
        for row in evidence_slot_values
        if isinstance(row, dict)
    }
    best_row: dict[str, Any] = {}
    best_confidence = -1.0
    for runtime_slot in runtime_candidates:
        row = rows_by_slot.get(runtime_slot)
        if not row:
            continue
        try:
            confidence = float(row.get("slot_confidence") or 0.0)
        except (TypeError, ValueError):
            confidence = 0.0
        has_value = bool(str(row.get("slot_value") or "").strip())
        score = confidence + (0.01 if has_value else 0.0)
        if score > best_confidence:
            best_confidence = score
            best_row = row
    return best_row, runtime_candidates


def build_verified_answer_slots(
    *,
    required_slot_resolution: RequiredSlotResolution,
    evidence_slot_values: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    answer_slots: list[dict[str, Any]] = []
    critical_runtime_slots = set(required_slot_resolution.critical_slots)
    critical_missing: list[str] = []
    methods: list[str] = []

    for matrix_slot in required_slot_resolution.matrix_slots:
        evidence_row, runtime_candidates = best_evidence_row_for_matrix_slot(
            matrix_slot,
            evidence_slot_values,
        )
        value = str(evidence_row.get("slot_value") or "").strip()
        span_id = str(evidence_row.get("evidence_span_id") or "").strip()
        article_or_span = str(evidence_row.get("evidence_article") or span_id or "").strip()
        reason = str(evidence_row.get("slot_missing_reason") or "").strip()
        try:
            confidence = float(evidence_row.get("slot_confidence") or 0.0)
        except (TypeError, ValueError):
            confidence = 0.0

        if value and span_id and confidence >= 0.65:
            fill_status = "filled"
            verifier_status = "verified"
            missing_reason = None
        elif value and span_id:
            fill_status = "unsupported"
            verifier_status = "needs_review"
            missing_reason = reason or "evidence_below_verification_threshold"
        else:
            fill_status = "missing"
            verifier_status = "failed"
            missing_reason = reason or "no_matching_evidence_span"

        method = answer_slot_extraction_method(matrix_slot)
        methods.append(method)
        if fill_status != "filled" and critical_runtime_slots & set(runtime_candidates):
            critical_missing.append(matrix_slot)

        answer_slots.append(
            {
                "slot_name": matrix_slot,
                "required": True,
                "value": value or None,
                "evidence_span_keys": [span_id] if span_id and value else [],
                "evidence_article_or_span": article_or_span or None,
                "extraction_method": method,
                "fill_status": fill_status,
                "verifier_status": verifier_status,
                "confidence_0_100": int(round(max(0.0, min(1.0, confidence)) * 100)),
                "slot_missing_reason": missing_reason,
                "runtime_slot_candidates": runtime_candidates,
            }
        )

    filled_count = sum(1 for slot in answer_slots if slot.get("fill_status") == "filled")
    verified_count = sum(1 for slot in answer_slots if slot.get("verifier_status") == "verified")
    unsupported_count = sum(1 for slot in answer_slots if slot.get("fill_status") == "unsupported")
    missing_count = sum(1 for slot in answer_slots if slot.get("fill_status") == "missing")
    return answer_slots, {
        "answer_slot_extraction_version": _ANSWER_SLOT_EXTRACTION_VERSION,
        "answer_slot_required_count": len(answer_slots),
        "answer_slot_filled_count": filled_count,
        "answer_slot_verified_count": verified_count,
        "answer_slot_missing_count": missing_count,
        "answer_slot_unsupported_count": unsupported_count,
        "answer_slot_extraction_methods": dedupe_strings(methods),
        "critical_answer_slots_missing": dedupe_strings(critical_missing),
    }
