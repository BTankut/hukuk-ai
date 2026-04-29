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
    resolution = resolve_required_slot_matrix(
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
    return phase20_calibrated_required_slot_resolution(
        resolution=resolution,
        query=query,
        template=template,
    )


_PHASE20_REQUIRED_SLOT_CALIBRATION_SUFFIX = "+phase20b"
_PHASE20_RUNTIME_SLOT_OVERRIDES: dict[str, list[str]] = {
    "direct_legal_conclusion": ["result_or_holding"],
    "document_selection_rationale": ["document_selection_reason"],
    "governing_regulation": ["governing_source", "exact_source_identity"],
    "procedure_or_condition": ["procedure_or_consequence", "scenario_applicability"],
    "relation_to_law_if_question_asks": ["hierarchy_or_conflict_rule", "document_selection_reason"],
    "scenario_application": ["scenario_applicability"],
    "supporting_regulation_or_teblig_relation": [
        "hierarchy_or_conflict_rule",
        "document_selection_reason",
    ],
}
_PHASE20_CRITICAL_RUNTIME_SLOTS = {
    "governing_source",
    "exact_source_identity",
    "temporal_validity",
    "current_applicability",
    "transition_or_replacement_rule",
    "article_or_span",
}
_PHASE20_SLOT_FALLBACK_CANDIDATES: dict[str, list[str]] = {
    "exception_or_limitation": [
        "result_or_holding",
        "procedure_or_consequence",
        "scenario_applicability",
    ],
    "hierarchy_or_conflict_rule": [
        "document_selection_reason",
        "temporal_validity",
        "result_or_holding",
        "procedure_or_consequence",
    ],
    "procedure_or_consequence": [
        "result_or_holding",
        "scenario_applicability",
    ],
    "scenario_applicability": [
        "result_or_holding",
        "procedure_or_consequence",
        "exception_or_limitation",
    ],
    "transition_or_replacement_rule": [
        "temporal_validity",
        "current_applicability",
        "result_or_holding",
    ],
}
_PHASE20_SLOT_SUPPORT_TERMS: dict[str, tuple[str, ...]] = {
    "exception_or_limitation": (
        "istisna",
        "sakli",
        "haric",
        "muaf",
        "uygulanmaz",
        "sinir",
        "dahil degil",
        "ancak",
        "talep edilmesi",
    ),
    "hierarchy_or_conflict_rule": (
        "dayanak",
        "uyarinca",
        "kanun",
        "yonetmelik",
        "teblig",
        "karar",
        "kaldirilan mevzuat",
        "yururlukten kaldir",
        "oncelik",
        "ust norm",
        "alt norm",
        "gecis",
        "gecici",
        "onceki",
        "eski",
        "yeni",
        "cercevesinde",
    ),
    "procedure_or_consequence": (
        "usul",
        "sure",
        "basvuru",
        "bildirim",
        "tescil",
        "ilan",
        "sonuc",
        "yukumluluk",
        "zorundadir",
        "gerekir",
        "teslim",
        "olustur",
    ),
    "scenario_applicability": (
        "kapsam",
        "uygulan",
        "bakimindan",
        "halinde",
        "sart",
        "kosul",
        "kurum",
        "kurulus",
        "isyer",
        "sozlesme",
        "adres",
    ),
    "transition_or_replacement_rule": (
        "gecis",
        "gecici",
        "yerine gec",
        "yerini alan",
        "kaldirilan",
        "yururlukten kaldir",
        "mevcut rejim",
        "onceki",
        "yeni",
    ),
}


def runtime_slots_for_matrix_slot_calibrated(matrix_slot: str) -> list[str]:
    override = _PHASE20_RUNTIME_SLOT_OVERRIDES.get(str(matrix_slot or ""))
    if override is not None:
        return override
    return runtime_slots_for_matrix_slot(matrix_slot)


def _phase20_slot_text_supports(runtime_slot: str, value: str) -> bool:
    terms = _PHASE20_SLOT_SUPPORT_TERMS.get(runtime_slot)
    if not terms:
        return False
    normalized = normalize_query_text(value or "")
    return query_contains_any(normalized, terms)


def _phase20_fallback_evidence_row(
    *,
    runtime_candidates: list[str],
    evidence_slot_values: list[dict[str, Any]],
) -> dict[str, Any]:
    rows_by_slot = {
        str(row.get("slot_name") or ""): row
        for row in evidence_slot_values
        if isinstance(row, dict)
    }
    for runtime_slot in runtime_candidates:
        fallback_slots = _PHASE20_SLOT_FALLBACK_CANDIDATES.get(runtime_slot, [])
        for fallback_slot in fallback_slots:
            row = rows_by_slot.get(fallback_slot)
            if not row:
                continue
            value = str(row.get("slot_value") or "").strip()
            span_id = str(row.get("evidence_span_id") or "").strip()
            try:
                confidence = float(row.get("slot_confidence") or 0.0)
            except (TypeError, ValueError):
                confidence = 0.0
            if value and span_id and confidence >= 0.65 and _phase20_slot_text_supports(runtime_slot, value):
                cloned = dict(row)
                cloned["slot_confidence"] = min(confidence, 0.66)
                cloned["slot_missing_reason"] = f"phase20c_evidence_fallback:{fallback_slot}"
                return cloned
    return {}


def _phase20_relation_requested(normalized_query: str) -> bool:
    return query_contains_any(
        normalized_query,
        (
            "dayanak",
            "dayan",
            "ilisk",
            "iliski",
            "baglant",
            "kanun mu",
            "yonetmelik mi",
            "teblig mi",
            "hangisi uygulanir",
            "normlar hiyerarsisi",
            "kanuna aykiri",
            "ust norm",
            "alt norm",
            "yoksa",
        ),
    )


def _phase20_family_slot_additions(
    *,
    source_families: list[str],
    normalized_query: str,
) -> tuple[list[str], list[str]]:
    families = set(source_families)
    labels: list[str] = []
    slots: list[str] = []
    if families & {"mulga", "mulga_kanun"}:
        labels.append("MULGA")
        slots.append("direct_conclusion")
    if "teblig" in families or "tebligler" in families:
        labels.append("TEBLIGLER")
        slots.append("exception_or_limitation")
    if "yonetmelik" in families:
        labels.append("YONETMELIK")
        slots.extend(
            [
                "governing_regulation",
                "article_or_span",
                "scope",
                "procedure_or_condition",
                "exception_or_limitation",
                "direct_conclusion",
            ]
        )
        if _phase20_relation_requested(normalized_query):
            slots.append("relation_to_law_if_question_asks")
    if "cb_karar" in families and _phase20_relation_requested(normalized_query):
        labels.append("CB_KARAR")
        slots.append("supporting_regulation_or_teblig_relation")
    return dedupe_strings(labels), dedupe_strings(slots)


def phase20_calibrated_required_slot_resolution(
    *,
    resolution: RequiredSlotResolution,
    query: str,
    template: str,
) -> RequiredSlotResolution:
    normalized_query = normalize_query_text(query or "")
    family_labels, family_slots = _phase20_family_slot_additions(
        source_families=resolution.source_families,
        normalized_query=normalized_query,
    )
    if not family_slots:
        return resolution

    matrix_slots = dedupe_strings([*resolution.matrix_slots, *family_slots])
    runtime_slots: list[str] = []
    for slot in matrix_slots:
        runtime_slots.extend(runtime_slots_for_matrix_slot_calibrated(slot))
    runtime_slots = dedupe_strings(["result_or_holding", "governing_source", *runtime_slots])
    critical_slots = [
        slot
        for slot in runtime_slots
        if slot in (set(resolution.critical_slots) | _PHASE20_CRITICAL_RUNTIME_SLOTS)
    ]
    version = resolution.matrix_version
    if not version.endswith(_PHASE20_REQUIRED_SLOT_CALIBRATION_SUFFIX):
        version = f"{version}{_PHASE20_REQUIRED_SLOT_CALIBRATION_SUFFIX}"
    return RequiredSlotResolution(
        matrix_version=version,
        task_type=resolution.task_type,
        answer_template=template or resolution.answer_template,
        source_families=resolution.source_families,
        family_labels=dedupe_strings([*resolution.family_labels, *family_labels]),
        task_slots=resolution.task_slots,
        family_slots=dedupe_strings([*resolution.family_slots, *family_slots]),
        query_slots=resolution.query_slots,
        matrix_slots=matrix_slots,
        runtime_slots=runtime_slots,
        critical_slots=critical_slots,
        resolution_reason=dedupe_strings(
            [*resolution.resolution_reason, "phase20b_required_slot_calibration"]
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
            "onceki rejim",
            "tarihsel",
            "o tarihte",
            "gecis",
            "gecis hukmu",
            "gecici madde",
            "eski rejim",
            "yeni rejim",
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
    runtime_candidates = runtime_slots_for_matrix_slot_calibrated(matrix_slot)
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
    best_value = str(best_row.get("slot_value") or "").strip()
    best_span_id = str(best_row.get("evidence_span_id") or "").strip()
    if not best_value or not best_span_id or best_confidence < 0.65:
        fallback_row = _phase20_fallback_evidence_row(
            runtime_candidates=runtime_candidates,
            evidence_slot_values=evidence_slot_values,
        )
        if fallback_row:
            return fallback_row, runtime_candidates
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


def _phase20_materialize_answer_slot_evidence_values(
    *,
    evidence_required_slot_values: list[dict[str, Any]],
    answer_slots: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    materialized = list(evidence_required_slot_values)
    existing_slot_names = {
        str(row.get("slot_name") or "")
        for row in materialized
        if isinstance(row, dict) and str(row.get("slot_name") or "").strip()
    }
    for slot in answer_slots:
        if not isinstance(slot, dict):
            continue
        slot_name = str(slot.get("slot_name") or "").strip()
        if not slot_name or slot_name in existing_slot_names:
            continue
        if str(slot.get("fill_status") or "") != "filled" or str(slot.get("verifier_status") or "") != "verified":
            continue
        value = str(slot.get("value") or "").strip()
        evidence_keys = [
            str(item).strip()
            for item in slot.get("evidence_span_keys") or []
            if str(item or "").strip()
        ]
        if not value or not evidence_keys:
            continue
        try:
            confidence = float(slot.get("confidence_0_100") or 0.0) / 100.0
        except (TypeError, ValueError):
            confidence = 0.0
        materialized.append(
            {
                "slot_name": slot_name,
                "slot_value": value,
                "evidence_span_id": evidence_keys[0],
                "evidence_article": str(slot.get("evidence_article_or_span") or evidence_keys[0]),
                "slot_confidence": round(max(0.0, min(1.0, confidence)), 3),
                "slot_missing_reason": "phase20c_verified_answer_slot_materialized",
            }
        )
        existing_slot_names.add(slot_name)
    return materialized


_INLINE_CITATION_RE = re.compile(r"\[Kaynak:\s*([^\]]+)\]")


def count_answer_fact_units(answer_text: str) -> int:
    stripped = re.sub(r"\[Kaynak:[^\]]+\]", " ", answer_text or "")
    pieces = re.split(r"(?:\n+|(?<=[.!?])\s+|(?:^|\s)(?:[-*]|\d+[.)])\s+)", stripped)
    long_pieces = [
        piece.strip()
        for piece in pieces
        if len(piece.strip()) >= 28 and any(char.isalpha() for char in piece)
    ]
    citation_count = len(_INLINE_CITATION_RE.findall(answer_text or ""))
    return max(len(long_pieces), citation_count)


def build_completeness_synthesis_features(
    *,
    query: str,
    answer_text: str,
    article_span_selector: dict[str, Any] | None,
    chunks: list[Any],
    requested_source_families: list[str] | None = None,
    source_family_resolution: Any = None,
    resolve_chunk_routing_family: Any = None,
    resolve_chunk_source_family: Any = None,
    satisfied_completeness_slots: Any = None,
    evidence_supported_completeness_slots: Any = None,
    build_evidence_required_slot_values: Any = None,
    build_answer_slot_evidence_map: Any = None,
) -> dict[str, Any]:
    template = answer_template_for_query(query)
    required_slot_resolution = resolve_required_slot_matrix_for_query(
        query=query,
        template=template,
        requested_source_families=requested_source_families,
        source_family_resolution=source_family_resolution,
        chunks=chunks,
        resolve_chunk_routing_family=resolve_chunk_routing_family,
        resolve_chunk_source_family=resolve_chunk_source_family,
    )
    required_slots = must_have_fact_slots_for_query(query, template)
    minimum_required_facts = max(2 if template == "direct" else 3, min(len(required_slots), 3))
    answer_fact_units = count_answer_fact_units(answer_text)
    citation_count = len(_INLINE_CITATION_RE.findall(answer_text or ""))
    support_span_count = 0
    selector = article_span_selector if isinstance(article_span_selector, dict) else {}
    candidate_completeness_score = selector.get("candidate_completeness_score")
    selected_document_has_body_span = bool(selector.get("selected_document_has_body_span"))
    selected_document_has_non_title_span = bool(selector.get("selected_document_has_non_title_span"))
    selected_document_has_document_level_body_span = bool(
        selector.get("selected_document_has_document_level_body_span")
    )
    selected_document_has_materialized_body_span = bool(
        selector.get("selected_document_has_materialized_body_span")
    )
    title_only_answer_degraded = bool(selector.get("title_only_answer_degraded"))
    insufficient_canonical_span_evidence = bool(selector.get("insufficient_canonical_span_evidence"))
    if isinstance(article_span_selector, dict):
        try:
            support_span_count = int(article_span_selector.get("support_span_count") or 0)
        except (TypeError, ValueError):
            support_span_count = 0
    effective_support_count = support_span_count
    if effective_support_count == 0 and citation_count and chunks:
        effective_support_count = min(citation_count, len(chunks))

    has_answer = bool((answer_text or "").strip()) and not str(answer_text).startswith("REFUSED_OR_EMPTY:")
    satisfied_slots = (
        satisfied_completeness_slots(
            required_slots=required_slots,
            query=query,
            answer_text=answer_text,
            article_span_selector=article_span_selector,
            chunks=chunks,
            answer_fact_units=answer_fact_units,
            citation_count=citation_count,
            support_span_count=effective_support_count,
        )
        if has_answer
        else []
    )
    evidence_reentry_slots = [
        slot
        for slot in evidence_supported_completeness_slots(
            required_slots=required_slots,
            article_span_selector=article_span_selector,
            chunks=chunks,
        )
        if slot not in set(satisfied_slots)
    ]
    if has_answer and evidence_reentry_slots:
        satisfied_slots = dedupe_strings([*satisfied_slots, *evidence_reentry_slots])
    missing_slots = [slot for slot in required_slots if slot not in set(satisfied_slots)]
    evidence_required_slot_values = build_evidence_required_slot_values(
        required_slots=required_slots,
        article_span_selector=article_span_selector,
        chunks=chunks,
        query=query,
    )
    matrix_evidence_required_slot_values = build_evidence_required_slot_values(
        required_slots=required_slot_resolution.runtime_slots,
        article_span_selector=article_span_selector,
        chunks=chunks,
        query=query,
    )
    answer_slots, answer_slot_summary = build_verified_answer_slots(
        required_slot_resolution=required_slot_resolution,
        evidence_slot_values=matrix_evidence_required_slot_values,
    )
    answer_slot_evidence_map, answer_slot_coverage_score, answer_slot_missing_reasons = (
        build_answer_slot_evidence_map(
            required_slots=required_slots,
            satisfied_slots=satisfied_slots,
            evidence_reentry_slots=evidence_reentry_slots,
            missing_slots=missing_slots,
            article_span_selector=article_span_selector,
            chunks=chunks,
            query=query,
        )
    )
    verified_matrix_slot_count = int(answer_slot_summary.get("answer_slot_verified_count") or 0)
    required_matrix_slot_count = int(answer_slot_summary.get("answer_slot_required_count") or 0)
    matrix_answer_slot_coverage_score = round(
        verified_matrix_slot_count / required_matrix_slot_count,
        3,
    ) if required_matrix_slot_count else 1.0
    if matrix_answer_slot_coverage_score > float(answer_slot_coverage_score or 0.0):
        # Phase 20C can improve evidence-backed slot coverage, but it must not
        # remove the confidence cap before Phase 20D makes those slots visible in
        # the final answer text.
        answer_slot_coverage_score = round(min(matrix_answer_slot_coverage_score, 0.89), 3)
    evidence_required_slot_values = _phase20_materialize_answer_slot_evidence_values(
        evidence_required_slot_values=evidence_required_slot_values,
        answer_slots=answer_slots,
    )
    evidence_required_slot_value_count = sum(
        1 for row in evidence_required_slot_values if float(row.get("slot_confidence") or 0.0) >= 0.65
    )
    slot_factor = len(satisfied_slots) / len(required_slots) if required_slots else 1.0
    answer_factor = min(1.0, answer_fact_units / minimum_required_facts) if has_answer else 0.0
    evidence_factor = (
        min(1.0, effective_support_count / max(1, minimum_required_facts))
        if effective_support_count
        else (0.5 if chunks else 0.0)
    )
    coverage_score = round((0.55 * slot_factor) + (0.25 * answer_factor) + (0.20 * evidence_factor), 3)
    minimum_answer_facts_present = bool(
        has_answer
        and answer_fact_units >= minimum_required_facts
        and citation_count >= 1
        and effective_support_count >= 1
        and not missing_slots
        and not insufficient_canonical_span_evidence
    )
    structurally_full = bool(
        has_answer
        and answer_fact_units >= minimum_required_facts
        and citation_count >= 1
        and effective_support_count >= 1
    )
    if insufficient_canonical_span_evidence:
        degrade_reason = "insufficient_canonical_span_evidence"
        rubric_class = "legally_aligned_but_partial" if has_answer else "insufficient_both"
        minimum_answer_facts_present = False
        if "article_or_span" in required_slots and "article_or_span" not in missing_slots:
            missing_slots = [*missing_slots, "article_or_span"]
        satisfied_slots = [slot for slot in satisfied_slots if slot != "article_or_span"]
    elif not has_answer:
        degrade_reason = "no_answer"
        rubric_class = "insufficient_both"
    elif missing_slots:
        degrade_reason = "missing_required_fact_slots:" + ",".join(missing_slots)
        rubric_class = "structurally_full_but_legally_misaligned" if structurally_full else "insufficient_both"
    elif answer_fact_units < minimum_required_facts:
        degrade_reason = "answer_too_short_for_template"
        rubric_class = "insufficient_both"
    elif citation_count == 0:
        degrade_reason = "missing_source_citations"
        rubric_class = "insufficient_both"
    elif not chunks:
        degrade_reason = "no_retrieved_evidence"
        rubric_class = "insufficient_both"
    elif effective_support_count == 0:
        degrade_reason = "no_selector_support_spans"
        rubric_class = "legally_aligned_but_partial"
    elif not minimum_answer_facts_present:
        degrade_reason = "partial_evidence_only"
        rubric_class = "legally_aligned_but_partial"
    else:
        degrade_reason = "complete_enough"
        rubric_class = "rubric_sufficient"

    return {
        "required_fact_coverage_score": coverage_score,
        "minimum_answer_facts_present": minimum_answer_facts_present,
        "completeness_degrade_reason": degrade_reason,
        "task_type_answer_template_used": template,
        "must_have_fact_slots": required_slots,
        "satisfied_fact_slots": satisfied_slots,
        "missing_fact_slots": missing_slots,
        "evidence_slot_reentry_applied": bool(evidence_reentry_slots),
        "evidence_slot_reentry_slots": evidence_reentry_slots,
        "rubric_aligned_completeness_class": rubric_class,
        "answer_slot_evidence_map": answer_slot_evidence_map,
        "answer_slot_coverage_score": answer_slot_coverage_score,
        "answer_slot_missing_reasons": answer_slot_missing_reasons,
        "required_slot_schema": required_slot_schema(required_slots),
        "evidence_required_slot_values": evidence_required_slot_values,
        "evidence_required_slot_value_count": evidence_required_slot_value_count,
        "matrix_answer_slot_coverage_score": matrix_answer_slot_coverage_score,
        **required_slot_resolution.to_trace_dict(),
        "answer_slots": answer_slots,
        **answer_slot_summary,
        "candidate_completeness_score": candidate_completeness_score,
        "selected_document_has_body_span": selected_document_has_body_span,
        "selected_document_has_non_title_span": selected_document_has_non_title_span,
        "selected_document_has_document_level_body_span": selected_document_has_document_level_body_span,
        "selected_document_has_materialized_body_span": selected_document_has_materialized_body_span,
        "title_only_answer_degraded": title_only_answer_degraded,
        "insufficient_canonical_span_evidence": insufficient_canonical_span_evidence,
    }
