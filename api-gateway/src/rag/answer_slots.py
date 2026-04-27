from __future__ import annotations

import hashlib
from typing import Any

from faz2a_hardening import dedupe_strings, normalize_whitespace
from rag.required_slot_matrix import RequiredSlotResolution, runtime_slots_for_matrix_slot


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
