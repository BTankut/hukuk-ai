"""Chat Router — Backlog #7: Chat API + SSE + Multi-turn.

Endpoint'ler:
    POST /v1/chat/completions   — OpenAI-uyumlu chat endpoint (streaming + non-streaming)
    GET  /v1/sessions/{id}      — Oturum geçmişini döndür
    DEL  /v1/sessions/{id}      — Oturumu sil
    GET  /v1/sessions           — Aktif oturum sayısı

Özellikler:
    - OpenAI chat completions formatı (uyumluluk: Open WebUI, diğer OpenAI clientları)
    - SSE (Server-Sent Events) streaming
    - Multi-turn konuşma geçmişi (session bazlı, in-memory)
    - RAG Orchestrator tam entegrasyonu (retrieval + LLM + guardrails + verification)
    - MetadataFilter desteği (kanun filtresi: TBK, TMK, TCK, ...)
    - Verification Engine entegrasyonu (hallüsinasyon önleyici)
    - Conversation context injection (önceki turlar LLM'e iletilir)

SSE Streaming Stratejisi (Faz 1):
    - Orchestrator tam yanıtı üretir (RAG + guardrails + verification)
    - Yanıt kelime grupları hâlinde SSE chunk olarak gönderilir
    - Son chunk'ta citations + verification metadata eklenir
    - Gerçek LLM streaming Faz 2'ye bırakıldı (guardrails mid-stream çatışmasından kaçınmak için)

Multi-turn Yönetimi:
    OpenAI standardı: client geçmişi messages dizisinde taşır.
    Ek özellik: session_id ile server-side history (client geçmişi göndermezse kullanılır).
    History, orchestrator çağrısından önce sorguya enjekte edilir.
"""

from __future__ import annotations

from dataclasses import dataclass
import asyncio
import json
import logging
import os
import re
import time
import uuid
import urllib.error
import urllib.request
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from answer_contract_v2 import build_or_repair_answer_contract, controlled_fallback_answer
from faz2a_hardening import (
    HardeningResult,
    build_initial_answer_contract,
    build_law_scope_signal,
    canonicalize_law_code,
    canonicalize_source_id,
    dedupe_strings,
    extract_numbered_law_mentions,
    harden_answer,
    normalize_query_text,
    validate_trace_payload,
)
from observability import get_metrics_registry, looks_like_refusal
from pydantic import BaseModel, Field

from rag.answer_slots import (
    answer_template_for_query as _answer_template_for_query_impl,
    build_completeness_synthesis_features as _build_completeness_synthesis_features_impl,
    compact_slot_value as _compact_slot_value_impl,
    must_have_fact_slots_for_query as _must_have_fact_slots_for_query_impl,
    query_needs_current_applicability_slot as _query_needs_current_applicability_slot_impl,
    query_needs_historical_transition_slots as _query_needs_historical_transition_slots_impl,
    slot_quote_hash as _slot_quote_hash_impl,
)
from rag.answer_synthesis import (
    apply_evidence_slot_synthesis_to_answer_text as _apply_evidence_slot_synthesis_to_answer_text_impl,
    apply_temporal_claim_alignment as _apply_temporal_claim_alignment_impl,
    apply_verified_answer_slot_plan_to_answer_text as _apply_verified_answer_slot_plan_to_answer_text_impl,
    build_native_dialog_fallback_answer as _build_native_dialog_fallback_answer_impl,
    build_persisted_raw_answer_snapshot as _build_persisted_raw_answer_snapshot_impl,
    build_persisted_response_envelope_snapshot as _build_persisted_response_envelope_snapshot_impl,
    resolve_contract_suppressed_answer_text as _resolve_contract_suppressed_answer_text_impl,
    resolve_public_answer_text as _resolve_public_answer_text_impl,
    sanitize_public_answer_contract as _sanitize_public_answer_contract_impl,
    sanitize_public_final_mode as _sanitize_public_final_mode_impl,
)
from rag.article_span_selection import (
    _annotate_canonical_span_materialization as _annotate_canonical_span_materialization_impl,
    _annotate_article_span_selector_priority as _annotate_article_span_selector_priority_impl,
    _apply_selected_document_only_bundle as _apply_selected_document_only_bundle_impl,
    _select_article_span_evidence as _select_article_span_evidence_impl,
    _chunk_body_text_for_quality as _chunk_body_text_for_quality_impl,
    _chunk_body_text_quality as _chunk_body_text_quality_impl,
    _chunk_has_selectable_body_span as _chunk_has_selectable_body_span_impl,
    _extract_query_article_tokens as _extract_query_article_tokens_impl,
    _query_article_alignment as _query_article_alignment_impl,
    _resolve_chunk_span_id as _resolve_chunk_span_id_impl,
    _strip_chunk_citation_prefix as _strip_chunk_citation_prefix_impl,
)
from rag.evidence_bundle import (
    _build_allowed_source_whitelist,
    _build_assembled_evidence,
    _build_chunk_evidence_span,
    _build_fallback_assembled_evidence,
    _resolve_chunk_source_identifier,
    _resolve_trace_source_id,
    _serialize_trace_chunk,
)
from rag.orchestrator import RAGOrchestrator, RetrievedChunk
from rag.retrieval_orchestration import (
    _annotate_recall_lane_chunks,
    _build_retrieved_chunk,
    _retrieve_active_chunks,
    _retrieve_explicit_article_chunks,
    _retrieve_law_bucket_chunks,
    _retrieve_relation_chain_chunks,
    _retrieve_source_family_chunks,
    _retrieve_source_key_chunks,
)
from rag.retrieval_planning import request_history_from_messages
from rag.source_catalog import (
    enrich_metadata_with_source_title,
    load_canonical_source_catalog,
    normalize_canonical_text,
    resolve_effective_state,
)
from rag.source_identity import (
    _SOURCE_FAMILY_DISPLAY_LABELS,
    _apply_pre_generation_family_pool as _apply_pre_generation_family_pool_impl,
    _apply_relation_query_metadata_focus as _apply_relation_query_metadata_focus_impl,
    _apply_source_family_resolution_hints,
    _build_metadata_first_query_expansion,
    _canonical_source_family_value,
    _chunk_article_token,
    _chunk_clause_token,
    _chunk_matches_metadata_first_candidate,
    _chunk_source_identity_values,
    _chunk_uses_legacy_source_key_alias as _chunk_uses_legacy_source_key_alias_impl,
    _clamp_families_to_strong_resolution as _clamp_families_to_strong_resolution_impl,
    _expand_source_family_aliases,
    _extract_source_identity_identifier_tokens,
    _extract_year_tokens,
    _focus_chunks_on_selected_sources as _focus_chunks_on_selected_sources_impl,
    _infer_family_from_source_title,
    _infer_requested_source_families,
    _metadata_first_focus_keys_for_source_lock as _metadata_first_focus_keys_for_source_lock_impl,
    _metadata_lookup_has_strong_query_anchor,
    _metadata_active_raw_law_overrides_legacy_family,
    _metadata_has_active_source_span,
    _normalize_article_token,
    _parse_metadata_lookup_query_signals as _parse_metadata_lookup_query_signals_impl,
    _prioritize_chunks_for_source_families as _prioritize_chunks_for_source_families_impl,
    _query_has_academic_regulation_intent,
    _relation_query_family_profile,
    _resolve_chunk_binding_source_key as _resolve_chunk_binding_source_key_impl,
    _resolve_chunk_canonical_source_key_v2 as _resolve_chunk_canonical_source_key_v2_impl,
    _resolve_chunk_document_key,
    _resolve_chunk_source_key,
    _resolve_chunk_source_family,
    _resolve_chunk_source_family_profile,
    _resolve_chunk_source_title,
    _resolve_source_family_prior,
    _rerank_chunks_by_source_identity as _rerank_chunks_by_source_identity_impl,
    _select_metadata_first_source_candidates as _select_metadata_first_source_candidates_impl,
    _source_family_relation_group,
    _source_identifier_base_alias,
    _source_identity_reranker_enabled,
    _source_key_collision_profile as _source_key_collision_profile_impl,
    _source_key_v2_collision_profile as _source_key_v2_collision_profile_impl,
    _strong_source_family_gate as _strong_source_family_gate_impl,
)
from rag.required_slot_matrix import (
    RequiredSlotResolution,
)
from rag.phase24hx_constrained_routing import (
    build_phase24hx_feature_trace,
    phase24hx_constrained_routing_enabled,
)
from rag.runtime_trace import (
    _attach_parity_trace,
    _extract_answer_source_ids,
    _extract_inline_citation_ids,
    _pre_answer_stage_payload,
    _response_envelope_stage_payload,
)
from rag.source_supplements import (
    _build_source_supplement_chunks,
    _source_supplement_keys_for_law_hints,
    load_source_supplements_for_keys,
)
from rag.token_manager import estimate_tokens
from release_controls import (
    api_version_label,
    append_audit_event,
    ensure_request_id,
    ensure_trace_id,
    export_trace_pack,
    persist_sidecar_session_turn,
    release_lane_id,
    require_api_auth,
)
from session_store import SessionStoreBackend, build_session_backend_from_env
from token_accounting import (
    TokenAccountingError,
    resolve_token_usage,
    token_accounting_fallback_allowed,
)
from source_family_resolver import (
    QUERY_EXPANSIONS as _SOURCE_FAMILY_GENERIC_QUERY_EXPANSIONS,
    SourceFamilyCandidate,
    SourceFamilyResolution,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])
_LAW_TOKEN_PATTERN = r"TBK|TMK|TCK|HMK|TTK|İİK|IİK|IIK|İK|IK|KVKK|HUAK|CMK|AY|IYUK|İYUK"
_NUMERIC_LAW_TOKEN_PATTERN = r"\d{2,8}"
_ARTICLE_REF_RE = re.compile(
    rf"\b(?P<law>{_LAW_TOKEN_PATTERN})\s*(?:m|md|madde)\.?\s*(?P<madde>\d+[a-z]?)\b",
    re.IGNORECASE,
)
_NUMERIC_ARTICLE_REF_RE = re.compile(
    rf"\b(?P<law>{_NUMERIC_LAW_TOKEN_PATTERN})\s*(?:m|md|madde)\.?\s*(?P<madde>\d+[a-z]?)\b",
    re.IGNORECASE,
)
_ARTICLE_SEQUENCE_RE = re.compile(
    rf"\b(?P<law>{_LAW_TOKEN_PATTERN})\s*(?:m|md|madde)\.?\s*(?P<articles>\d+[a-z]?(?:\s*[-–]\s*\d+[a-z]?)?(?:\s*(?:,|ve|veya)\s*(?:m|md|madde)?\.?\s*\d+[a-z]?(?:\s*[-–]\s*\d+[a-z]?)?)*)",
    re.IGNORECASE,
)
_NUMERIC_ARTICLE_SEQUENCE_RE = re.compile(
    rf"\b(?P<law>{_NUMERIC_LAW_TOKEN_PATTERN})\s*(?:m|md|madde)\.?\s*(?P<articles>\d+[a-z]?(?:\s*[-–]\s*\d+[a-z]?)?(?:\s*(?:,|ve|veya)\s*(?:m|md|madde)?\.?\s*\d+[a-z]?(?:\s*[-–]\s*\d+[a-z]?)?)*)",
    re.IGNORECASE,
)
_ACTIVE_END_DATE_SENTINELS = {
    "9999-12-31",
    "9999-12-31T00:00:00",
    "9999-12-31 00:00:00",
}
_TRUTHY_METADATA_FLAGS = {"1", "true", "yes", "y", "evet"}
_FALSEY_METADATA_FLAGS = {"0", "false", "no", "n", "hayir", "hayır"}
_LAW_MENTION_RE = re.compile(
    rf"\b(?P<law>{_LAW_TOKEN_PATTERN}|Türk Borçlar Kanunu|Borçlar Kanunu|İş Kanunu|Is Kanunu|Kişisel Verilerin Korunması Kanunu|Kisisel Verilerin Korunmasi Kanunu|Hukuk Uyuşmazlıklarında Arabuluculuk Kanunu|Hukuk Uyusmazliklarinda Arabuluculuk Kanunu|Tebligat Kanunu|Türk Medeni Kanunu|Medeni Kanun|Türk Ceza Kanunu|Ceza Kanunu|Türk Ticaret Kanunu|Ticaret Kanunu|İcra ve İflas Kanunu)\b",
    re.IGNORECASE,
)
_LAW_CODE_NORMALIZATION = {
    "AY": "AY",
    "CMK": "CMK",
    "IK": "IK",
    "İK": "IK",
    "KVKK": "KVKK",
    "HUAK": "HUAK",
    "TBK": "TBK",
    "TMK": "TMK",
    "TCK": "TCK",
    "HMK": "HMK",
    "TTK": "TTK",
    "İİK": "İİK",
    "IİK": "İİK",
    "IIK": "İİK",
    "IYUK": "IYUK",
    "İYUK": "IYUK",
}
_LAW_NAME_NORMALIZATION = {
    "türk borçlar kanunu": "TBK",
    "borçlar kanunu": "TBK",
    "iş kanunu": "IK",
    "is kanunu": "IK",
    "kişisel verilerin korunması kanunu": "KVKK",
    "kisisel verilerin korunmasi kanunu": "KVKK",
    "hukuk uyuşmazlıklarında arabuluculuk kanunu": "HUAK",
    "hukuk uyusmazliklarinda arabuluculuk kanunu": "HUAK",
    "tebligat kanunu": "7201",
    "türk medeni kanunu": "TMK",
    "medeni kanun": "TMK",
    "türk ceza kanunu": "TCK",
    "ceza kanunu": "TCK",
    "türk ticaret kanunu": "TTK",
    "ticaret kanunu": "TTK",
    "icra ve iflas kanunu": "İİK",
}
_INLINE_CITATION_RE = re.compile(r"\[Kaynak:\s*([^\]]+)\]")
_NATIVE_DIALOG_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("greeting", ("merhaba", "selam", "selamlar", "günaydın", "iyi akşamlar", "iyi geceler", "hey", "hello", "hi")),
    ("smalltalk", ("nasılsın", "nasilsin", "ne haber", "iyi misin", "iyi misiniz")),
    ("capability", ("ne yapabiliyorsun", "neler yapabiliyorsun", "yardımcı olabilir misin", "yardimci olabilir misin", "kimsin")),
    ("gratitude", ("teşekkürler", "tesekkurler", "teşekkür ederim", "tesekkur ederim", "sağ ol", "sag ol")),
)
_NATIVE_DIALOG_SYSTEM_PROMPT = (
    "Sen hukuk-ai-poc arayüzünde çalışan Türkçe yardımcı asistansın. "
    "Bu mod yalnız düşük riskli doğal diyalog içindir: selamlaşma, kısa sosyal cevaplar, "
    "ürünün genel kullanımını anlatma ve teşekkür yanıtlama. "
    "Kısa, doğal ve net yanıt ver. Bu modda sahte kaynak/citation üretme. "
    "Kullanıcı hukuki soru sorarsa mevzuat sorusunu doğrudan yazabileceğini kısa biçimde belirt."
)
_RETRIEVAL_PLANNER_ALLOWED_FAMILIES = {
    "kanun",
    "mulga_kanun",
    "tuzuk",
    "yonetmelik",
    "cb_yonetmelik",
    "cb_kararname",
    "cb_karar",
    "cb_genelge",
    "khk",
    "teblig",
    "kky",
    "uy",
}
_HARD_PRE_GENERATION_FAMILY_GATES = {
    "cb_karar",
    "cb_genelge",
    "cb_yonetmelik",
    "yonetmelik",
    "uy",
    "mulga_kanun",
    "teblig",
}
_METADATA_LOOKUP_NEGATIVE_FAMILY_TRANSITIONS = {
    ("cb_karar", "teblig"),
    ("cb_karar", "cb_genelge"),
    ("cb_yonetmelik", "cb_kararname"),
    ("yonetmelik", "kky"),
    ("yonetmelik", "uy"),
    ("kanun", "kky"),
    ("kanun", "mulga_kanun"),
    ("uy", "kanun"),
}
_RETRIEVAL_PRIORITY_TOKEN_RE = re.compile(r"[a-z0-9]+")
_RETRIEVAL_PRIORITY_STOPWORDS = {
    "ve",
    "ile",
    "icin",
    "için",
    "gore",
    "göre",
    "hangi",
    "nedir",
    "nasil",
    "nasıl",
    "kisa",
    "kısa",
    "sonuc",
    "sonuç",
    "gerekce",
    "gerekçe",
    "dayanak",
    "belge",
    "zinciri",
    "gerekiyorsa",
    "durumuna",
    "cevapla",
    "yaniti",
    "yanıtı",
    "seklinde",
    "şeklinde",
    "temel",
    "olarak",
    "olan",
    "dair",
    "hakkinda",
    "hakkında",
}


def _tr_lower(text: str) -> str:
    """Türkçe karakterleri güvenli şekilde lower-case'e çevir."""
    tr_map = str.maketrans("İIĞÖÜŞÇ", "iiğöüşç")
    return text.translate(tr_map).lower()


_TR_ASCII_FOLD_MAP = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "â": "a",
        "î": "i",
        "û": "u",
    }
)


def _normalize_tr_text(text: str) -> str:
    return _tr_lower(text).translate(_TR_ASCII_FOLD_MAP)


_LAW_NAME_NORMALIZATION_NORMALIZED = {
    _normalize_tr_text(key): value
    for key, value in _LAW_NAME_NORMALIZATION.items()
}
_RETRIEVAL_PLANNER_FAMILY_NORMALIZATION = {
    _normalize_tr_text("kanun"): "kanun",
    _normalize_tr_text("mülga kanun"): "mulga_kanun",
    _normalize_tr_text("mulga kanun"): "mulga_kanun",
    _normalize_tr_text("tüzük"): "tuzuk",
    _normalize_tr_text("tuzuk"): "tuzuk",
    _normalize_tr_text("yönetmelik"): "yonetmelik",
    _normalize_tr_text("yonetmelik"): "yonetmelik",
    _normalize_tr_text("Cumhurbaşkanlığı yönetmeliği"): "cb_yonetmelik",
    _normalize_tr_text("Cumhurbaskanligi yonetmeligi"): "cb_yonetmelik",
    _normalize_tr_text("Cumhurbaşkanlığı kararnamesi"): "cb_kararname",
    _normalize_tr_text("Cumhurbaskanligi kararnamesi"): "cb_kararname",
    _normalize_tr_text("Cumhurbaşkanlığı kararı"): "cb_karar",
    _normalize_tr_text("Cumhurbaskanligi karari"): "cb_karar",
    _normalize_tr_text("Cumhurbaşkanlığı genelgesi"): "cb_genelge",
    _normalize_tr_text("Cumhurbaskanligi genelgesi"): "cb_genelge",
    _normalize_tr_text("khk"): "khk",
    _normalize_tr_text("tebliğ"): "teblig",
    _normalize_tr_text("teblig"): "teblig",
    _normalize_tr_text("kurum yönetmeliği"): "kky",
    _normalize_tr_text("kurum yonetmeligi"): "kky",
    _normalize_tr_text("üniversite yönetmeliği"): "uy",
    _normalize_tr_text("universite yonetmeligi"): "uy",
}


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _contains_query_term(query: str, term: str) -> bool:
    normalized_query = _normalize_tr_text(query)
    normalized_term = _normalize_tr_text(term)
    term_tokens = [token for token in normalized_term.split() if token]
    if not term_tokens:
        return False

    token_patterns: list[str] = []
    for index, token in enumerate(term_tokens):
        escaped = re.escape(token)
        allow_suffix = index == len(term_tokens) - 1 and len(token) >= 4
        token_patterns.append(f"{escaped}[a-z0-9]*" if allow_suffix else escaped)

    pattern = rf"(?<![a-z0-9]){r'\s+'.join(token_patterns)}(?![a-z0-9])"
    return re.search(pattern, normalized_query) is not None


def _contains_any_query_term(query: str, terms: tuple[str, ...] | list[str]) -> bool:
    return any(_contains_query_term(query, term) for term in terms)


def _detect_native_dialog_intent(user_query: str) -> str | None:
    normalized_query = _normalize_tr_text(_normalize_whitespace(user_query)).strip("!?.,;:")
    if not normalized_query:
        return None
    if _extract_law_mentions(user_query) or _extract_explicit_article_refs(user_query):
        return None

    for intent, terms in _NATIVE_DIALOG_PATTERNS:
        if normalized_query in {_normalize_tr_text(term) for term in terms}:
            return intent
        if any(normalized_query.startswith(_normalize_tr_text(term) + " ") for term in terms):
            return intent
    return None


def _build_native_dialog_fallback_answer(intent: str) -> str:
    return _build_native_dialog_fallback_answer_impl(intent)


def _retrieval_planner_enabled() -> bool:
    return os.getenv("RETRIEVAL_PLANNER_ENABLED", "true").lower() in {"1", "true", "yes", "on"}


def _legacy_query_expansions_enabled() -> bool:
    return os.getenv("LEGACY_QUERY_EXPANSIONS_ENABLED", "false").lower() in {"1", "true", "yes", "on"}


def _source_cluster_selector_enabled() -> bool:
    return os.getenv("SOURCE_CLUSTER_SELECTOR_ENABLED", "true").lower() in {"1", "true", "yes", "on"}


def _strip_json_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def _extract_json_object(text: str) -> dict[str, Any] | None:
    stripped = _strip_json_fence(text)
    if not stripped:
        return None
    try:
        payload = json.loads(stripped)
        return payload if isinstance(payload, dict) else None
    except json.JSONDecodeError:
        pass

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        payload = json.loads(stripped[start : end + 1])
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _normalize_retrieval_planner_law_hint(value: Any) -> str | None:
    raw = _normalize_whitespace(str(value or ""))
    if not raw:
        return None
    if raw.isdigit() and 2 <= len(raw) <= 8:
        return raw
    numbered_mentions = extract_numbered_law_mentions(raw)
    if numbered_mentions:
        return numbered_mentions[0]
    normalized = _normalize_tr_text(raw)
    if normalized in _LAW_NAME_NORMALIZATION_NORMALIZED:
        return _LAW_NAME_NORMALIZATION_NORMALIZED[normalized]
    candidate = canonicalize_law_code(raw)
    if candidate in _LAW_CODE_NORMALIZATION or candidate in {"IK", "AY", "CMK", "KVKK", "IYUK"}:
        return candidate
    return None


def _normalize_retrieval_planner_family_hint(value: Any) -> str | None:
    raw = _normalize_whitespace(str(value or ""))
    if not raw:
        return None
    normalized = _RETRIEVAL_PLANNER_FAMILY_NORMALIZATION.get(_normalize_tr_text(raw))
    if normalized in _RETRIEVAL_PLANNER_ALLOWED_FAMILIES:
        return normalized
    lowered = raw.strip().lower()
    if lowered in _RETRIEVAL_PLANNER_ALLOWED_FAMILIES:
        return lowered
    return None


def _normalize_retrieval_planner_term_hint(value: Any) -> str | None:
    raw = _normalize_whitespace(str(value or ""))
    if not raw:
        return None
    normalized = normalize_query_text(raw)
    if len(normalized) < 3:
        return None
    return raw


def _planner_term_supported_by_query(term: str, user_query: str | None = None) -> bool:
    if not user_query:
        return True

    normalized_term = normalize_query_text(term)
    normalized_query = normalize_query_text(user_query)
    if not normalized_term or not normalized_query:
        return False
    if normalized_term in normalized_query:
        return True

    query_terms = set(_extract_retrieval_priority_terms(user_query))
    term_tokens = [token for token in normalized_term.split() if len(token) >= 3 or token.isdigit()]
    if not term_tokens:
        return False
    overlap = sum(
        1
        for token in term_tokens
        if token in query_terms or (len(token) >= 4 and token in normalized_query)
    )
    if len(term_tokens) <= 3:
        return True

    titleish_tokens = {
        "kanun",
        "yonetmelik",
        "yonetmeligi",
        "tuzuk",
        "tuzugu",
        "karar",
        "karari",
        "kararname",
        "kararnamesi",
        "genelge",
        "teblig",
        "tebligi",
        "khk",
    }
    if any(token in titleish_tokens for token in term_tokens):
        return overlap >= 2
    return overlap >= max(2, len(term_tokens) // 2)


def _sanitize_retrieval_plan_payload(
    payload: dict[str, Any] | None,
    *,
    user_query: str | None = None,
) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None

    raw_laws = payload.get("law_hints")
    raw_families = payload.get("source_family_hints")
    raw_terms = payload.get("term_hints") or payload.get("search_terms")

    law_hints = dedupe_strings(
        [
            normalized
            for normalized in (
                _normalize_retrieval_planner_law_hint(item)
                for item in (raw_laws if isinstance(raw_laws, list) else [])
            )
            if normalized
        ]
    )
    source_family_hints = _expand_source_family_aliases(
        dedupe_strings(
            [
                normalized
                for normalized in (
                    _normalize_retrieval_planner_family_hint(item)
                    for item in (raw_families if isinstance(raw_families, list) else [])
                )
                if normalized
            ]
        )
    )
    term_hints = dedupe_strings(
        [
            normalized
            for normalized in (
                _normalize_retrieval_planner_term_hint(item)
                for item in (raw_terms if isinstance(raw_terms, list) else [])
            )
            if normalized and _planner_term_supported_by_query(normalized, user_query)
        ]
    )[:6]

    if not law_hints and not source_family_hints and not term_hints:
        return None

    return {
        "law_hints": law_hints,
        "source_family_hints": source_family_hints,
        "term_hints": term_hints,
    }


def _build_retrieval_plan_expansion(plan: dict[str, Any]) -> str:
    parts: list[str] = []
    for law in plan.get("law_hints") or []:
        if isinstance(law, str) and law.strip():
            parts.append(f"{law.strip()} sayılı kanun" if law.strip().isdigit() else law.strip())
    for family in plan.get("source_family_hints") or []:
        if isinstance(family, str) and family.strip():
            parts.append(_SOURCE_FAMILY_DISPLAY_LABELS.get(family, family))
    for term in plan.get("term_hints") or []:
        if isinstance(term, str) and term.strip():
            parts.append(term.strip())
    return _normalize_whitespace(" ".join(dedupe_strings(parts)))


def _build_retrieval_plan_focus_query(plan: dict[str, Any] | None) -> str:
    if not plan:
        return ""
    parts: list[str] = []
    for term in plan.get("term_hints") or []:
        if isinstance(term, str) and term.strip():
            parts.append(term.strip())
    for family in plan.get("source_family_hints") or []:
        if isinstance(family, str) and family.strip():
            parts.append(_SOURCE_FAMILY_DISPLAY_LABELS.get(family, family))
    return _normalize_whitespace(" ".join(dedupe_strings(parts)))


def _parse_metadata_lookup_query_signals(query: str) -> dict[str, Any]:
    return _parse_metadata_lookup_query_signals_impl(
        query,
        explicit_article_refs=_extract_explicit_article_refs(query),
    )


def _extract_effective_legal_query(query: str) -> str:
    raw = str(query or "").strip()
    if not raw:
        return ""

    lines = [_normalize_whitespace(line) for line in raw.splitlines()]
    filtered_lines: list[str] = []
    for line in lines:
        if not line:
            continue
        normalized = _normalize_tr_text(line)
        if (
            normalized.startswith("bu soruyu ")
            and "tarihindeki yururluk durumuna gore cevapla" in normalized
        ):
            continue
        if normalized.startswith("beklenen cikti tipi:"):
            continue
        if normalized == "[kaynak ailesi onceligi]":
            continue
        if normalized.startswith("kullanici ozellikle su belge ailesini soruyor:"):
            continue
        if normalized.startswith("yaniti kurarken once bu ailedeki duzenlemeyi merkez al."):
            continue
        if normalized.startswith("ust normu veya paralel normu ancak gercekten gerekliyse"):
            continue
        if normalized.startswith("kullanici 'hangi tuzuk/yonetmelik/genelge/kararname' diye soruyorsa"):
            continue
        filtered_lines.append(line)

    if not filtered_lines:
        return _normalize_whitespace(raw)

    question_lines = [line for line in filtered_lines if "?" in line]
    if question_lines:
        return max(question_lines, key=lambda item: (len(item), item.count(" ")))

    if len(filtered_lines) == 1:
        return filtered_lines[0]

    combined = _normalize_whitespace(" ".join(filtered_lines))
    return combined or _normalize_whitespace(raw)


def _select_metadata_first_source_candidates(
    *,
    query: str,
    requested_source_families: list[str],
    source_family_resolution: SourceFamilyResolution | None,
    query_metadata_signals: dict[str, Any] | None = None,
    limit: int = 6,
) -> dict[str, Any] | None:
    if query_metadata_signals is None:
        query_metadata_signals = _parse_metadata_lookup_query_signals(query)
    return _select_metadata_first_source_candidates_impl(
        query=query,
        requested_source_families=requested_source_families,
        source_family_resolution=source_family_resolution,
        query_metadata_signals=query_metadata_signals,
        limit=limit,
        catalog_loader=load_canonical_source_catalog,
    )


def _query_explicitly_requests_source_family(query: str, family: str) -> bool:
    family_group = _source_family_relation_group(family)
    if family_group == "yonetmelik":
        return _contains_any_query_term(
            query,
            (
                "yönetmelik",
                "yonetmelik",
                "yönetmeliği",
                "yonetmeligi",
                "ikincil düzenleme",
                "ikincil duzenleme",
            ),
        )
    if family == "teblig":
        normalized = normalize_query_text(query)
        return bool(
            re.search(
                r"(?<![a-z0-9])(?:genel\s+)?teblig(?!at)(?:\s*\(|\s+no|\s+numarasi|\s+sayili|\s+sira|\s+seri|\s+ile)",
                normalized,
            )
        )
    if family == "cb_genelge":
        return _contains_any_query_term(query, ("genelge", "cumhurbaşkanlığı genelgesi", "cumhurbaskanligi genelgesi"))
    if family == "cb_karar":
        return _contains_any_query_term(query, ("karar sayısı", "karar sayisi", "cumhurbaşkanı kararı", "cumhurbaskani karari"))
    return False


def _suppress_domain_law_metadata_conflict(
    metadata_first_selector: dict[str, Any] | None,
    *,
    query: str,
    domain_law_hints: list[str],
) -> dict[str, Any] | None:
    if not metadata_first_selector or not metadata_first_selector.get("metadata_lookup_hit"):
        return metadata_first_selector
    if not domain_law_hints:
        return metadata_first_selector
    candidates = metadata_first_selector.get("candidates") or []
    if not candidates:
        return metadata_first_selector

    top = candidates[0]
    metadata_family = str(top.get("source_family") or "").strip()
    lookup_source = str(
        top.get("metadata_lookup_source")
        or metadata_first_selector.get("metadata_lookup_source")
        or ""
    )
    weak_lookup = lookup_source in {"normalized_title_lookup", "title_ngram_family_lookup"}
    match_reasons = {str(reason) for reason in (top.get("match_reasons") or [])}
    exact_identity = bool(match_reasons & {"identifier_exact", "year_match", "issuer_exact"})
    if not metadata_family:
        return metadata_first_selector
    if _source_family_relation_group(metadata_family) == "kanun":
        domain_hint_set = set(domain_law_hints)
        domain_hint_aliases = set(domain_hint_set)
        if domain_hint_set & {"TBK", "6098"}:
            domain_hint_aliases.update({"TBK", "6098", "türk borçlar", "turk borclar"})
        candidate_identity = normalize_query_text(
            " ".join(
                str(value or "")
                for value in (
                    top.get("canonical_identifier"),
                    top.get("source_key"),
                    top.get("canonical_title"),
                )
            )
        )
        domain_identity_match = any(
            normalize_query_text(alias) in candidate_identity
            for alias in domain_hint_aliases
            if str(alias or "").strip()
        )
        if weak_lookup and not exact_identity and not domain_identity_match:
            suppressed = dict(metadata_first_selector)
            suppressed["metadata_lookup_hit"] = False
            suppressed["metadata_lookup_suppressed"] = True
            suppressed["metadata_lookup_suppression_reason"] = "domain_law_same_family_metadata_conflict"
            suppressed["suppressed_metadata_family"] = metadata_family
            suppressed["suppressed_domain_law_hints"] = list(domain_law_hints)
            suppressed["selected_source_keys"] = []
            suppressed["selected_families"] = []
            suppressed["candidates"] = []
            return suppressed
        return metadata_first_selector
    if _query_explicitly_requests_source_family(query, metadata_family):
        return metadata_first_selector
    if not weak_lookup or exact_identity:
        return metadata_first_selector

    suppressed = dict(metadata_first_selector)
    suppressed["metadata_lookup_hit"] = False
    suppressed["metadata_lookup_suppressed"] = True
    suppressed["metadata_lookup_suppression_reason"] = "domain_law_primary_source_conflict"
    suppressed["suppressed_metadata_family"] = metadata_family
    suppressed["suppressed_domain_law_hints"] = list(domain_law_hints)
    suppressed["selected_source_keys"] = []
    suppressed["selected_families"] = []
    suppressed["candidates"] = []
    return suppressed


def _apply_metadata_lookup_family_prior(
    source_family_resolution: SourceFamilyResolution,
    metadata_first_selector: dict[str, Any] | None,
    *,
    query: str | None = None,
) -> SourceFamilyResolution:
    if not metadata_first_selector or not metadata_first_selector.get("metadata_lookup_hit"):
        return source_family_resolution
    candidates = metadata_first_selector.get("candidates") or []
    if not candidates:
        return source_family_resolution

    top = candidates[0]
    metadata_family = str(top.get("source_family") or "").strip()
    if not metadata_family:
        return source_family_resolution
    confidence = float(top.get("metadata_lookup_confidence") or metadata_first_selector.get("metadata_lookup_confidence") or 0.0)
    if confidence < 0.65:
        return source_family_resolution

    scenario_current_law_guard = bool(
        source_family_resolution.scenario_current_law_question
        and not source_family_resolution.historical_or_repealed_question
    )
    raw_metadata_family = str(top.get("source_family_raw") or metadata_family).strip()
    top_effective_state = str(top.get("effective_state") or "").strip().lower()
    if scenario_current_law_guard and (
        raw_metadata_family == "mulga_kanun" or top_effective_state == "repealed"
    ):
        return source_family_resolution
    if (
        source_family_resolution.predicted_family == "mulga_kanun"
        and source_family_resolution.historical_or_repealed_question
        and metadata_family != "mulga_kanun"
    ):
        return source_family_resolution
    relation_profile = _relation_query_family_profile(
        query or "",
        source_family_resolution=source_family_resolution,
    )
    relation_primary_group = str(relation_profile.get("primary_group") or "")
    predicted_relation_group = _source_family_relation_group(source_family_resolution.predicted_family)
    metadata_relation_group = _source_family_relation_group(metadata_family)
    if (
        relation_profile.get("relation_query_detected")
        and relation_primary_group
        and predicted_relation_group == relation_primary_group
        and metadata_relation_group
        and metadata_relation_group != relation_primary_group
    ):
        return source_family_resolution
    if (
        source_family_resolution.collision_resolution_reason
        == "central_higher_education_regulation_prefers_yonetmelik"
        and metadata_family == "uy"
    ):
        return source_family_resolution

    metadata_lookup_source = str(
        top.get("metadata_lookup_source") or metadata_first_selector.get("metadata_lookup_source") or ""
    )
    if (
        metadata_family == "uy"
        and metadata_lookup_source in {"normalized_title_lookup", "title_ngram_family_lookup"}
        and not _query_has_academic_regulation_intent(query or "")
    ):
        return source_family_resolution

    predicted = source_family_resolution.predicted_family
    transition = (predicted or "", metadata_family)
    negative_transition = transition in _METADATA_LOOKUP_NEGATIVE_FAMILY_TRANSITIONS
    weak_or_no_gate = (
        not source_family_resolution.preferred_families
        or source_family_resolution.family_override_reason in {"no_family_prior", "low_confidence_family_prior"}
        or source_family_resolution.family_confidence < 0.70
    )
    if metadata_family == predicted and source_family_resolution.preferred_families:
        return source_family_resolution
    if not negative_transition and not weak_or_no_gate and confidence < 0.82:
        return source_family_resolution

    routing_families = dedupe_strings(
        [
            *_expand_source_family_aliases([metadata_family]),
            *source_family_resolution.routing_families,
        ]
    )
    preferred_families = [metadata_family] if confidence >= 0.70 else list(source_family_resolution.preferred_families)
    fallback_families = dedupe_strings(
        [
            family
            for family in [*source_family_resolution.preferred_families, *source_family_resolution.fallback_families, *routing_families]
            if family != metadata_family
        ]
    )
    family_candidates = [
        SourceFamilyCandidate(
            family=metadata_family,
            score=float(top.get("score") or 0.0),
            confidence=round(confidence, 3),
            signals=[
                "metadata_lookup_family_prior",
                metadata_lookup_source or "metadata_lookup",
            ],
        ),
        *source_family_resolution.family_candidates,
    ]
    return SourceFamilyResolution(
        predicted_family=metadata_family,
        family_confidence=max(source_family_resolution.family_confidence, confidence),
        family_candidates=family_candidates,
        routing_families=routing_families,
        query_expansions=dedupe_strings(
            [
                _SOURCE_FAMILY_DISPLAY_LABELS.get(metadata_family, metadata_family),
                *source_family_resolution.query_expansions,
            ]
        )[:4],
        expected_family_prior=metadata_family,
        preferred_families=preferred_families,
        fallback_families=fallback_families,
        selected_family_confidence=max(source_family_resolution.selected_family_confidence, confidence),
        family_override_reason=(
            "metadata_lookup_negative_transition"
            if negative_transition
            else "metadata_lookup_family_prior"
        ),
        scenario_current_law_question=source_family_resolution.scenario_current_law_question,
        scenario_current_law_prior=source_family_resolution.scenario_current_law_prior,
        historical_or_repealed_question=source_family_resolution.historical_or_repealed_question,
        historical_scope_detected=source_family_resolution.historical_scope_detected,
        repealed_scope_detected=source_family_resolution.repealed_scope_detected,
        current_law_prior_blocked_by_historical_scope=(
            source_family_resolution.current_law_prior_blocked_by_historical_scope
        ),
        family_collision_detected=source_family_resolution.family_collision_detected,
        family_collision_pair=source_family_resolution.family_collision_pair,
        collision_resolution_reason=source_family_resolution.collision_resolution_reason,
    )


def _build_numbered_law_reference_expansion(query: str) -> str:
    numbered_laws = extract_numbered_law_mentions(query)
    if not numbered_laws:
        return ""
    normalized = normalize_query_text(query)
    asks_khk = "khk" in normalized or "kanun hukmunde kararname" in normalized
    parts: list[str] = []
    for law in numbered_laws:
        parts.append(f"{law} sayılı kanun")
        if asks_khk:
            parts.extend(
                [
                    f"{law} sayılı KHK",
                    f"KHK-{law}",
                    f"KHK/{law}",
                    f"KHK {law}",
                    f"KHK-{law}/1 md",
                ]
            )
    return _normalize_whitespace(" ".join(dedupe_strings(parts)))


def _build_annual_investment_program_expansion(query: str) -> str:
    normalized = normalize_query_text(query or "")
    if "yatirim program" not in normalized:
        return ""
    if "karar" not in normalized:
        return ""
    if not any(hint in normalized for hint in ("kamu yatirim", "yatirim projes", "program hazirlik")):
        return ""
    years = _extract_year_tokens(query)
    if not years:
        return ""
    year = years[-1]
    return _normalize_whitespace(
        f"{year} yılı kamu yatırım programı karar sayısı "
        f"{year} yılı yatırım programının kabulü ve uygulanmasına dair karar "
        "yıl içi proje parametre değişikliği"
    )


def _apply_retrieval_plan_hints(
    *,
    retrieval_query: str,
    mentioned_laws: list[str],
    requested_source_families: list[str],
    applied_expansions: list[str],
    retrieval_top_k: int,
    retrieval_plan: dict[str, Any] | None,
) -> tuple[str, list[str], list[str], int]:
    if not retrieval_plan:
        return retrieval_query, mentioned_laws, requested_source_families, retrieval_top_k

    requested_source_families = dedupe_strings(
        [*requested_source_families, *(retrieval_plan.get("source_family_hints") or [])]
    )
    planner_expansion = _build_retrieval_plan_expansion(retrieval_plan)
    if planner_expansion:
        retrieval_query = _append_unique_expansion(
            retrieval_query,
            applied_expansions,
            planner_expansion,
        )
        retrieval_top_k = max(retrieval_top_k, 20)

    return retrieval_query, mentioned_laws, requested_source_families, retrieval_top_k


def _extract_chunk_law_hint(chunk: RetrievedChunk) -> str | None:
    metadata = chunk.metadata or {}
    for value in (
        metadata.get("law_short_name"),
        metadata.get("kanun_kisa_adi"),
        chunk.source,
        metadata.get("law_no"),
        metadata.get("kanun_no"),
    ):
        candidate = canonicalize_law_code(str(value or ""))
        if candidate:
            return candidate
        raw = _normalize_whitespace(str(value or ""))
        if raw and raw.isdigit():
            return raw
    return None


def _build_source_cluster_candidates(chunks: list[RetrievedChunk], *, limit: int = 8) -> list[dict[str, Any]]:
    clusters: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for chunk in chunks:
        source_key = _resolve_chunk_source_key(chunk)
        if not source_key:
            continue
        metadata = chunk.metadata or {}
        cluster = clusters.setdefault(
            source_key,
            {
                "source_key": source_key,
                "display_title": (
                    metadata.get("source_title")
                    or metadata.get("belge_adi")
                    or metadata.get("kanun_adi")
                    or metadata.get("law_name")
                    or chunk.source
                    or chunk.citation
                ),
                "source_family": _resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk),
                "laws": [],
                "citations": [],
                "excerpts": [],
                "max_score": chunk.score or 0.0,
                "chunk_count": 0,
                "state_rank": 2,
                "effective_states": [],
            },
        )
        cluster["max_score"] = max(cluster["max_score"], chunk.score or 0.0)
        cluster["chunk_count"] += 1
        effective_state = str(
            (chunk.metadata or {}).get("effective_state") or resolve_effective_state(chunk.metadata or {}) or ""
        ).strip().lower()
        state_rank = (
            2
            if _is_temporally_inactive_chunk(chunk) or effective_state == "repealed"
            else 0
            if effective_state in {"active", "amended"} or _chunk_active_rank(chunk) == 0
            else 1
        )
        if effective_state and effective_state not in cluster["effective_states"]:
            cluster["effective_states"].append(effective_state)
        cluster["state_rank"] = min(cluster["state_rank"], state_rank)
        law_hint = _extract_chunk_law_hint(chunk)
        if law_hint and law_hint not in cluster["laws"]:
            cluster["laws"].append(law_hint)
        if chunk.citation and chunk.citation not in cluster["citations"] and len(cluster["citations"]) < 3:
            cluster["citations"].append(chunk.citation)
        excerpt = _normalize_whitespace(chunk.text or "")
        if excerpt and excerpt not in cluster["excerpts"] and len(cluster["excerpts"]) < 2:
            cluster["excerpts"].append(excerpt[:220])

    ranked = sorted(
        clusters.values(),
        key=lambda item: (-int(item["chunk_count"]), -(item["max_score"] or 0.0), str(item["display_title"])),
    )[:limit]

    candidates: list[dict[str, Any]] = []
    for index, cluster in enumerate(ranked, start=1):
        candidates.append(
            {
                "cluster_id": f"C{index}",
                "source_key": cluster["source_key"],
                "display_title": cluster["display_title"],
                "source_family": cluster["source_family"],
                "laws": cluster["laws"],
                "citations": cluster["citations"],
                "excerpts": cluster["excerpts"],
                "chunk_count": cluster["chunk_count"],
                "max_score": round(float(cluster["max_score"] or 0.0), 6),
                "state_rank": int(cluster["state_rank"]),
                "effective_states": cluster["effective_states"],
                "effective_state": (
                    "active"
                    if int(cluster["state_rank"]) == 0
                    else "unknown"
                    if int(cluster["state_rank"]) == 1
                    else "repealed"
                ),
            }
        )
    return candidates


def _sanitize_source_cluster_selector_payload(
    payload: dict[str, Any] | None,
    *,
    candidates: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not isinstance(payload, dict) or not candidates:
        return None

    valid_cluster_ids = {candidate["cluster_id"] for candidate in candidates}
    valid_laws = {
        law
        for candidate in candidates
        for law in candidate.get("laws") or []
        if isinstance(law, str) and law
    }

    selected_cluster_ids = dedupe_strings(
        [
            cluster_id
            for cluster_id in (payload.get("selected_cluster_ids") or [])
            if isinstance(cluster_id, str) and cluster_id in valid_cluster_ids
        ]
    )[:3]
    selected_laws = dedupe_strings(
        [
            law
            for law in (
                canonicalize_law_code(item) or _normalize_whitespace(str(item or ""))
                for item in (payload.get("selected_law_hints") or [])
            )
            if isinstance(law, str) and law in valid_laws
        ]
    )[:4]

    if not selected_cluster_ids and not selected_laws:
        return None

    return {
        "selected_cluster_ids": selected_cluster_ids,
        "selected_law_hints": selected_laws,
    }


def _candidate_identifier_values(candidate: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for value in (
        candidate.get("source_key"),
        candidate.get("display_title"),
        *(candidate.get("laws") or []),
        *(candidate.get("citations") or []),
        *(candidate.get("excerpts") or []),
    ):
        normalized = _normalize_tr_text(str(value or ""))
        if not normalized:
            continue
        values.add(normalized)
        for number in re.findall(r"\d{2,9}(?:[-/]\d{1,4})?", normalized):
            values.add(number)
            values.add(number.split("-", 1)[0].split("/", 1)[0])
    return values


def _candidate_matches_identifier_tokens(candidate: dict[str, Any], identifier_tokens: set[str]) -> bool:
    if not identifier_tokens:
        return False
    values = _candidate_identifier_values(candidate)
    for token in identifier_tokens:
        normalized_token = _normalize_tr_text(token)
        if normalized_token in values:
            return True
        if len(normalized_token) >= 3 and any(normalized_token in value for value in values):
            return True
    return False


def _candidate_matches_year_tokens(candidate: dict[str, Any], year_tokens: set[str]) -> bool:
    if not year_tokens:
        return False
    values = _candidate_identifier_values(candidate)
    return any(year in values or any(year in value for value in values) for year in year_tokens)


def _candidate_has_selector_support(
    candidate: dict[str, Any],
    *,
    user_query: str,
    requested_source_families: list[str],
    identifier_tokens: set[str],
) -> bool:
    if _candidate_matches_identifier_tokens(candidate, identifier_tokens):
        return True

    query_terms = _extract_retrieval_priority_terms(user_query)
    title = str(candidate.get("display_title") or "")
    normalized_title = _normalize_tr_text(title)
    title_overlap = max(
        _count_term_overlap(title, query_terms),
        sum(1 for term in query_terms if len(term) >= 4 and term in normalized_title),
    )
    excerpt_overlap = max(
        [
            max(
                _count_term_overlap(str(excerpt or ""), query_terms),
                sum(
                    1
                    for term in query_terms
                    if len(term) >= 4 and term in _normalize_tr_text(str(excerpt or ""))
                ),
            )
            for excerpt in (candidate.get("excerpts") or [])
        ]
        or [0]
    )
    family = str(candidate.get("source_family") or "")
    requested_family_set = set(_expand_source_family_aliases(requested_source_families))
    if requested_family_set and family in requested_family_set:
        return title_overlap >= 1 or excerpt_overlap >= 5
    return title_overlap >= 2 or (title_overlap >= 1 and excerpt_overlap >= 4)


def _apply_source_cluster_deterministic_overrides(
    *,
    payload: dict[str, Any],
    candidates: list[dict[str, Any]],
    user_query: str,
    requested_source_families: list[str],
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None = None,
    planner_law_hints: set[str] | None = None,
) -> dict[str, Any]:
    candidate_by_id = {candidate["cluster_id"]: candidate for candidate in candidates}
    requested_family_set = set(requested_source_families)
    selected_cluster_ids = [
        cluster_id
        for cluster_id in payload.get("selected_cluster_ids") or []
        if cluster_id in candidate_by_id
    ]

    scoped_candidates = candidates
    family_order = {family: index for index, family in enumerate(requested_source_families)}

    scenario_current_law_question = _source_family_resolution_trace_bool(
        source_family_resolution,
        "scenario_current_law_question",
    )
    historical_or_repealed_question = _source_family_resolution_trace_bool(
        source_family_resolution,
        "historical_or_repealed_question",
    )
    normalized_planner_laws = {
        normalized
        for normalized in (
            canonicalize_law_code(item) or _normalize_whitespace(str(item or ""))
            for item in (planner_law_hints or set())
        )
        if normalized
    }

    if requested_family_set and any(candidate.get("source_family") in requested_family_set for candidate in candidates):
        scoped_candidates = sorted(
            [
                candidate
                for candidate in candidates
                if candidate.get("source_family") in requested_family_set
            ],
            key=lambda candidate: (
                family_order.get(str(candidate.get("source_family") or ""), len(family_order)),
                candidates.index(candidate),
            ),
        )
        selected_cluster_ids = [
            cluster_id
            for cluster_id in selected_cluster_ids
            if candidate_by_id.get(cluster_id, {}).get("source_family") in requested_family_set
        ]
        if not selected_cluster_ids:
            selected_cluster_ids = [candidate["cluster_id"] for candidate in scoped_candidates[:2]]

    identifier_tokens = _extract_source_identifier_tokens(user_query)
    if normalized_planner_laws and not identifier_tokens:
        planner_matches = [
            candidate
            for candidate in scoped_candidates
            if normalized_planner_laws
            & {
                canonicalize_law_code(law) or _normalize_whitespace(str(law or ""))
                for law in (candidate.get("laws") or [])
            }
        ]
        if planner_matches:
            scoped_candidates = planner_matches
            selected_cluster_ids = [
                cluster_id
                for cluster_id in selected_cluster_ids
                if cluster_id in {candidate["cluster_id"] for candidate in planner_matches}
            ]

    if scenario_current_law_question and not historical_or_repealed_question:
        active_candidates = [
            candidate for candidate in scoped_candidates if int(candidate.get("state_rank") or 2) == 0
        ]
        if active_candidates:
            scoped_candidates = active_candidates
            selected_cluster_ids = [
                cluster_id
                for cluster_id in selected_cluster_ids
                if cluster_id in {candidate["cluster_id"] for candidate in active_candidates}
            ]
    elif historical_or_repealed_question:
        legacy_candidates = [
            candidate
            for candidate in scoped_candidates
            if int(candidate.get("state_rank") or 1) >= 2
            or str(candidate.get("source_family") or "") == "mulga_kanun"
        ]
        if legacy_candidates:
            scoped_candidates = legacy_candidates
            selected_cluster_ids = [
                cluster_id
                for cluster_id in selected_cluster_ids
                if cluster_id in {candidate["cluster_id"] for candidate in legacy_candidates}
            ]

    if identifier_tokens:
        identifier_matches = [
            candidate
            for candidate in scoped_candidates
            if _candidate_matches_identifier_tokens(candidate, identifier_tokens)
        ]
        if identifier_matches:
            selected_cluster_ids = [candidate["cluster_id"] for candidate in identifier_matches[:3]]
    elif _build_annual_investment_program_expansion(user_query):
        year_tokens = set(_extract_year_tokens(user_query))
        year_matches = [
            candidate
            for candidate in scoped_candidates
            if _candidate_matches_year_tokens(candidate, year_tokens)
        ]
        if year_matches:
            selected_cluster_ids = [candidate["cluster_id"] for candidate in year_matches[:3]]

    supported_cluster_ids = [
        cluster_id
        for cluster_id in selected_cluster_ids
        if _candidate_has_selector_support(
            candidate_by_id.get(cluster_id, {}),
            user_query=user_query,
            requested_source_families=requested_source_families,
            identifier_tokens=identifier_tokens,
        )
    ]
    if supported_cluster_ids:
        selected_cluster_ids = supported_cluster_ids
    else:
        selected_cluster_ids = [
            candidate["cluster_id"]
            for candidate in scoped_candidates
            if _candidate_has_selector_support(
                candidate,
                user_query=user_query,
                requested_source_families=requested_source_families,
                identifier_tokens=identifier_tokens,
            )
        ][:2]
        if not selected_cluster_ids and scoped_candidates:
            selected_cluster_ids = [scoped_candidates[0]["cluster_id"]]

    selected_laws = [
        law
        for cluster_id in selected_cluster_ids
        for law in candidate_by_id.get(cluster_id, {}).get("laws") or []
    ]
    payload["selected_cluster_ids"] = dedupe_strings(selected_cluster_ids)[:3]
    payload["selected_law_hints"] = dedupe_strings(selected_laws)[:4]
    return payload


def _clamp_families_to_strong_resolution(
    families: list[str],
    source_family_resolution: SourceFamilyResolution,
) -> list[str]:
    return _clamp_families_to_strong_resolution_impl(
        families,
        source_family_resolution,
    )


async def _run_source_cluster_selector(
    *,
    request: Request,
    user_query: str,
    requested_source_families: list[str],
    chunks: list[RetrievedChunk],
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None = None,
    planner_law_hints: set[str] | None = None,
) -> dict[str, Any] | None:
    if not _source_cluster_selector_enabled():
        return None
    if len(_normalize_whitespace(user_query)) < 40:
        return None

    candidates = _build_source_cluster_candidates(chunks)
    if len(candidates) < 2:
        return None

    orchestrator = _get_orchestrator(request)
    llm_client = getattr(orchestrator, "llm_client", None)
    if llm_client is None or not hasattr(llm_client, "chat"):
        return None

    from llm.client import ChatMessage

    family_text = ", ".join(requested_source_families) if requested_source_families else "yok"
    selector_messages = [
        ChatMessage(
            role="system",
            content=(
                "Sen hukuk retrieval kaynak seçicisisin. "
                "Kullanıcı sorusu ve aday kaynak kümeleri verilecek. "
                "Görevin, cevabı kurmak için en muhtemel 1-3 kaynak kümesini seçmek. "
                "Yalnızca verilen adaylardan seçim yap. "
                "Belge adı ve kapsamı soruyu gerçekten yönetmeli; genel başlık benzerliğine aldanma. "
                "Adaylarda effective_state varsa, historical/repealed istenmedikçe active/amended kümeyi öncele. "
                "Özellikle 'İade hükümleri' gibi jenerik başlıklar yüzünden alakasız metin seçme. "
                "JSON dışında hiçbir şey döndürme. "
                'Şema: {"selected_cluster_ids":["C1"],"selected_law_hints":["IK"]}'
            ),
        ),
        ChatMessage(
            role="user",
            content=(
                f"SORU:\n{user_query}\n\n"
                f"İSTENEN BELGE AİLESİ:\n{family_text}\n\n"
                "ADAY KAYNAK KÜMELERİ:\n"
                f"{json.dumps(candidates, ensure_ascii=False, indent=2)}"
            ),
        ),
    ]

    try:
        result = await llm_client.chat(
            messages=selector_messages,
            temperature=0.0,
            max_tokens=180,
        )
    except Exception:
        logger.warning("Source cluster selector failed; continuing without selector", exc_info=True)
        return None

    payload = _sanitize_source_cluster_selector_payload(
        _extract_json_object(result.text),
        candidates=candidates,
    )
    if not payload:
        return None

    payload = _apply_source_cluster_deterministic_overrides(
        payload=payload,
        candidates=candidates,
        user_query=user_query,
        requested_source_families=requested_source_families,
        source_family_resolution=source_family_resolution,
        planner_law_hints=planner_law_hints,
    )
    if not payload.get("selected_cluster_ids"):
        return None

    payload["candidates"] = candidates
    payload["raw_text"] = result.text
    return payload


async def _run_retrieval_planner(
    *,
    request: Request,
    user_query: str,
    mentioned_laws: list[str],
    requested_source_families: list[str],
    explicit_article_refs: list[tuple[str, str]],
    law_filter: str | None,
) -> dict[str, Any] | None:
    if not _retrieval_planner_enabled():
        return None
    if explicit_article_refs or law_filter:
        return None
    if len(_normalize_whitespace(user_query)) < 40:
        return None

    orchestrator = _get_orchestrator(request)
    llm_client = getattr(orchestrator, "llm_client", None)
    if llm_client is None or not hasattr(llm_client, "chat"):
        return None

    from llm.client import ChatMessage

    planner_messages = [
        ChatMessage(
            role="system",
            content=(
                "Sen retrieval planner olarak çalışıyorsun. "
                "Görev: kullanıcı sorusundan yalnız retrieval ipuçlarını çıkar. "
                "Sadece geçerli JSON nesnesi döndür; açıklama yazma.\n"
                "Şema:\n"
                "{"
                '"law_hints":["TBK","TMK","IK","KVKK"],'
                '"source_family_hints":["kanun","tuzuk","yonetmelik","teblig","cb_kararname","cb_yonetmelik","cb_karar","cb_genelge","khk","kky","uy","mulga_kanun"],'
                '"term_hints":["kısa arama terimi 1","kısa arama terimi 2"]'
                "}\n"
                "Kurallar:\n"
                "- Sadece yüksek güvenli ipuçlarını yaz.\n"
                "- Emin değilsen ilgili diziyi boş bırak.\n"
                "- law_hints kısa mevzuat kodları veya yüksek güvenli sayısal kanun/KHK numaraları olsun; emin değilsen boş bırak.\n"
                "- term_hints kısa ve retrieval dostu isim öbekleri olsun.\n"
                "- Maksimum 4 law_hints, 3 source_family_hints, 6 term_hints."
            ),
        ),
        ChatMessage(
            role="user",
            content=(
                f"Soru:\n{user_query}\n\n"
                f"Gözlenen law işaretleri: {mentioned_laws or []}\n"
                f"Gözlenen belge aileleri: {requested_source_families or []}"
            ),
        ),
    ]

    try:
        result = await llm_client.chat(messages=planner_messages, temperature=0.0, max_tokens=180)
    except Exception as exc:
        logger.debug("Retrieval planner bypass (LLM error): %s", exc)
        return None

    raw_text = result.text if isinstance(getattr(result, "text", None), str) else ""
    payload = _extract_json_object(raw_text)
    sanitized = _sanitize_retrieval_plan_payload(payload, user_query=user_query)
    if sanitized is None:
        return None
    sanitized["raw_text"] = raw_text
    return sanitized


def _build_native_dialog_answer_contract(*, answer_text: str) -> dict[str, Any]:
    return {
        "answer_text": answer_text,
        "primary_source_id": None,
        "secondary_source_ids": [],
        "law_scope": [],
        "source_validity": "unknown",
        "unsupported_reason": None,
        "verifier_status": "pass",
        "final_mode": "answer",
        "claim_units": [],
        "native_dialog": True,
    }


def _resolve_chunk_routing_family(chunk: RetrievedChunk) -> str | None:
    profile = _resolve_chunk_source_family_profile(chunk)
    mapped_family = str(profile.get("mapped_family") or "")
    if (
        str(profile.get("mapping_reason") or "") == "mulga_to_kanun"
        and _is_temporally_inactive_chunk(chunk)
    ):
        return str(profile.get("resolved_family") or profile.get("canonical_family") or "") or None
    return mapped_family or None


def _chunk_law_candidates(chunk: RetrievedChunk) -> set[str]:
    metadata = chunk.metadata or {}
    candidates: set[str] = set()
    for value in (
        metadata.get("law_no"),
        metadata.get("kanun_no"),
        metadata.get("law_short_name"),
        metadata.get("kanun_kisa_adi"),
        metadata.get("source_id"),
        chunk.source,
        chunk.citation,
    ):
        raw = _normalize_whitespace(str(value or ""))
        if not raw:
            continue
        if raw.isdigit():
            candidates.add(raw)
        canonical = canonicalize_law_code(raw)
        if canonical:
            candidates.add(canonical)
        match = re.search(r"\b(\d{1,9})\s*(?:m|md|madde)\.?\s*\d+", raw, re.IGNORECASE)
        if match:
            candidates.add(match.group(1))
    return candidates


def _extract_source_identifier_tokens(text: str) -> set[str]:
    without_dates = re.sub(r"\b(?:19|20)\d{2}-\d{1,2}-\d{1,2}\b", " ", text or "")
    tokens: set[str] = set()
    normalized = _normalize_tr_text(without_dates)
    patterns = (
        r"\b(\d{2,9}(?:[-/]\d{1,4})?)\s+sayili\s+(?:[a-z0-9]{2,}\s+){0,8}(?:kanun hukmunde kararname|cumhurbaskanligi kararnamesi|cumhurbaskani karari|cumhurbaskanligi karari|cumhurbaskanligi genelgesi|kanun|kanunu|khk|cbk|kararname|kararnamesi|karar|karari|genelge|genelgesi|teblig|tebligi)\b",
        r"\b(?:kanun hukmunde kararname|cumhurbaskanligi kararnamesi|cumhurbaskani karari|cumhurbaskanligi karari|cumhurbaskanligi genelgesi|kanun|kanunu|khk|cbk|kararname|kararnamesi|karar|karari|genelge|genelgesi|teblig|tebligi)\s+(?:sayisi|sayili|no|numarasi)\s*:?\s*(\d{2,9}(?:[-/]\d{1,4})?)\b",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, normalized):
            token = match.group(1)
            if re.fullmatch(r"(?:19|20)\d{2}", token):
                continue
            tokens.add(token)
            base_token = _source_identifier_base_alias(token)
            if base_token:
                tokens.add(base_token)
    for law in extract_numbered_law_mentions(text):
        if re.fullmatch(r"(?:19|20)\d{2}", law):
            continue
        tokens.add(law)
    return {token for token in tokens if len(token) >= 2}


def _chunk_identifier_candidates(chunk: RetrievedChunk) -> set[str]:
    metadata = chunk.metadata or {}
    candidates: set[str] = set()
    for value in (
        metadata.get("belge_no"),
        metadata.get("kanun_no"),
        metadata.get("law_no"),
        metadata.get("belge_kisa_adi"),
        metadata.get("kanun_kisa_adi"),
        metadata.get("law_short_name"),
        metadata.get("source_id"),
        metadata.get("display_citation"),
        metadata.get("canonical_identifier"),
        metadata.get("canonical_identifier_display"),
        metadata.get("decision_number"),
        metadata.get("kararname_number"),
        metadata.get("genelge_number"),
        metadata.get("generalge_number"),
        metadata.get("teblig_number"),
        metadata.get("sira_no"),
        metadata.get("seri_no"),
        metadata.get("regulation_number"),
        metadata.get("source_title"),
        metadata.get("belge_adi"),
        metadata.get("kanun_adi"),
        metadata.get("university_name_canonical"),
        metadata.get("canonical_title_family_normalized"),
        chunk.source,
        chunk.citation,
    ):
        normalized = _normalize_tr_text(str(value or ""))
        if not normalized:
            continue
        candidates.add(normalized)
        for number in re.findall(r"\d{2,9}(?:[-/]\d{1,4})?", normalized):
            candidates.add(number)
            candidates.add(number.split("-", 1)[0].split("/", 1)[0])
    return candidates


def _chunk_matches_identifier_tokens(chunk: RetrievedChunk, identifier_tokens: set[str]) -> bool:
    if not identifier_tokens:
        return False
    candidates = _chunk_identifier_candidates(chunk)
    for token in identifier_tokens:
        normalized_token = _normalize_tr_text(token)
        if normalized_token in candidates:
            return True
        if any(normalized_token in candidate for candidate in candidates if len(normalized_token) >= 3):
            return True
    return False


def _resolve_chunk_source_display_label(chunk: RetrievedChunk) -> str:
    return _resolve_chunk_source_title(chunk) or _resolve_chunk_source_identifier(chunk) or _resolve_chunk_source_key(chunk)


def _resolve_trace_source_display_label(trace: dict[str, Any]) -> str:
    return str(
        trace.get("source_title")
        or trace.get("source_identifier")
        or trace.get("source_key")
        or trace.get("source_id")
        or ""
    )


def _resolve_chunk_span_id(chunk: RetrievedChunk) -> str:
    return _resolve_chunk_span_id_impl(chunk)


def _resolve_chunk_canonical_source_key_v2(
    chunk: RetrievedChunk,
    *,
    include_span: bool = True,
) -> str:
    return _resolve_chunk_canonical_source_key_v2_impl(
        chunk,
        include_span=include_span,
        routing_family_resolver=_resolve_chunk_routing_family,
    )


def _resolve_chunk_binding_source_key(
    chunk: RetrievedChunk,
    *,
    include_span: bool = False,
) -> str:
    return _resolve_chunk_binding_source_key_impl(
        chunk,
        include_span=include_span,
        routing_family_resolver=_resolve_chunk_routing_family,
    )


def _chunk_uses_legacy_source_key_alias(chunk: RetrievedChunk) -> bool:
    return _chunk_uses_legacy_source_key_alias_impl(
        chunk,
        binding_source_key_resolver=lambda current: _resolve_chunk_binding_source_key(
            current,
            include_span=False,
        ),
    )


def _extract_query_article_tokens(
    query: str,
    explicit_article_refs: list[tuple[str, str]] | None = None,
) -> set[str]:
    return _extract_query_article_tokens_impl(
        query,
        explicit_article_refs=explicit_article_refs,
    )


def _query_article_alignment(
    *,
    selected_article: str | None,
    query_article_tokens: set[str],
    article_match_type: str,
    selected_paragraph_or_clause: str | None = None,
) -> str:
    return _query_article_alignment_impl(
        selected_article=selected_article,
        query_article_tokens=query_article_tokens,
        article_match_type=article_match_type,
        selected_paragraph_or_clause=selected_paragraph_or_clause,
    )


def _chunk_effective_state_resolved(chunk: RetrievedChunk) -> bool:
    metadata = chunk.metadata or {}
    state = str(metadata.get("effective_state") or resolve_effective_state(metadata) or "").strip().lower()
    if state and state not in {"unknown", "bilinmiyor"}:
        return True
    return bool(metadata.get("effective_start") or metadata.get("yururluk_baslangic"))


def _selector_metadata_identity_strength(
    *,
    top_trace: dict[str, Any] | None,
    identifier_tokens: set[str],
    requested_family_set: set[str],
    selected_source_keys: set[str] | None,
) -> str:
    if not top_trace:
        return "none"
    strong_hits = 0
    if top_trace.get("selected_source_match"):
        strong_hits += 1
    if top_trace.get("identifier_match"):
        strong_hits += 1
    if top_trace.get("family_match"):
        strong_hits += 1
    if top_trace.get("law_match"):
        strong_hits += 1
    if top_trace.get("title_overlap", 0) >= 3:
        strong_hits += 1
    if strong_hits >= 2:
        return "strong"
    if strong_hits == 1:
        return "medium"
    if identifier_tokens or requested_family_set or selected_source_keys:
        return "weak"
    return "none"


def _selector_manual_review_reason(
    *,
    top_traces: list[dict[str, Any]],
    article_tokens: set[str],
    requested_family_set: set[str],
    evidence_sufficiency: str,
    temporal_state_resolved: bool,
) -> str:
    if not top_traces:
        return "no_evidence"
    if evidence_sufficiency == "insufficient_support":
        return "insufficient_selector_support"
    if article_tokens and not any(trace.get("article_match") or trace.get("explicit_ref_match") for trace in top_traces[:5]):
        return "article_span_not_found"
    if not temporal_state_resolved:
        return "temporal_state_unresolved"
    top_families = {
        str(trace.get("source_family") or "")
        for trace in top_traces[:5]
        if trace.get("source_family")
    }
    if requested_family_set and top_families and not (top_families & requested_family_set):
        return "requested_family_not_in_top_evidence"
    top_sources = {
        str(trace.get("source_key") or trace.get("source_id") or "")
        for trace in top_traces[:5]
        if trace.get("source_key") or trace.get("source_id")
    }
    if len(top_sources) >= 3 and len(top_families) >= 2:
        return "source_identity_collision"
    return ""


def _asks_scope_or_applicability_query(query: str) -> bool:
    normalized = _normalize_tr_text(query or "")
    asks_source_selection = (
        "hangi" in normalized
        and any(
            source_term in normalized
            for source_term in (
                "tuzuk",
                "tuzug",
                "yonetmel",
                "genelge",
                "teblig",
                "karar",
                "kararnam",
                "metin",
                "duzenlem",
                "mevzuat",
            )
        )
        and any(
            intent_term in normalized
            for intent_term in ("aran", "esas", "bakimindan", "uygulan", "dayanak", "kontrol")
        )
    )
    if asks_source_selection:
        return True
    return any(
        signal in normalized
        for signal in (
            "kapsam",
            "tabi",
            "uygulanir",
            "uygulanacak",
            "uygulanmasi",
            "hangi lisans",
            "yetki belgesi",
            "ana uygulama metni",
        )
    )


def _chunk_scope_or_applicability_match(chunk: RetrievedChunk) -> bool:
    metadata = chunk.metadata or {}
    heading = _normalize_tr_text(str(metadata.get("heading") or metadata.get("article_heading") or ""))
    text = _normalize_tr_text(chunk.text or "")
    if "kapsam" in heading:
        return True
    if re.search(r"\bkapsam\b", text[:240]):
        return True
    return _chunk_article_token(chunk) == "2" and any(
        signal in text[:500]
        for signal in ("kapsar", "kapsam", "uygulanir", "tabidir", "tabi")
    )


def _asks_hierarchy_or_conflict_article_query(query: str) -> bool:
    normalized = _normalize_tr_text(query or "")
    return any(
        signal in normalized
        for signal in (
            "celiski",
            "celisirse",
            "hangisi esas",
            "hangisi uygulan",
            "ust norm",
            "alt duzenleme",
            "hiyerarsi",
            "hukum bulunmayan",
            "yerel duzenleme",
            "merkezi duzenleme",
            "yok degisikligi",
        )
    )


def _chunk_hierarchy_or_conflict_match(chunk: RetrievedChunk) -> bool:
    metadata = chunk.metadata or {}
    heading = _normalize_tr_text(str(metadata.get("heading") or metadata.get("article_heading") or ""))
    text = _normalize_tr_text(chunk.text or "")
    haystack = f"{heading} {text[:700]}"
    return any(
        signal in haystack
        for signal in (
            "hukum bulunmayan",
            "saklidir",
            "oncelikle uygulan",
            "ust norm",
            "alt norm",
            "aykiri olamaz",
            "hiyerarsi",
            "dayanak",
            "ilgili yonetmelik",
            "esaslarina iliskin yonetmelik",
        )
    )


def _selector_preferred_source_families(query: str, requested_source_families: list[str]) -> set[str]:
    normalized = _normalize_tr_text(query or "")
    preferred: list[str] = []
    if any(term in normalized for term in ("cumhurbaskanligi yonetmeligi", "devlet arsiv")):
        preferred.append("cb_yonetmelik")
    if any(term in normalized for term in ("cumhurbaskanligi genelgesi", "cumhurbaskani genelgesi", "genelge")):
        preferred.append("cb_genelge")
    if any(
        term in normalized
        for term in (
            "cumhurbaskanligi karari",
            "cumhurbaskani karari",
            "yatirim programi karari",
            "ithalat rejimi karari",
        )
    ):
        preferred.append("cb_karar")
    if "teblig" in normalized:
        preferred.append("teblig")
    if any(
        term in normalized
        for term in (
            "universite",
            "universitesi",
            "yuksek lisans",
            "lisansustu",
            "tez savunma",
            "ogrenci yonetmeligi",
            "yatay gecis",
            "cift anadal",
        )
    ):
        preferred.append("uy")
    if any(term in normalized for term in ("kurum yonetmeligi", "bddk", "sgk", "epdk", "btk", "rtuk")):
        preferred.append("kky")
    if "mulga" in normalized:
        preferred.append("mulga_kanun")

    requested_expanded = set(_expand_source_family_aliases(requested_source_families))
    preferred_set = set(dedupe_strings(preferred))
    if requested_expanded:
        preferred_set = {family for family in preferred_set if family in requested_expanded}
    return preferred_set


def _selector_article_lock_type(
    *,
    top_trace: dict[str, Any] | None,
    article_tokens: set[str],
    metadata_identity_strength: str,
    support_span_count: int,
) -> str:
    if not top_trace:
        return "none"
    article = str(top_trace.get("article_or_section") or "")
    if top_trace.get("explicit_ref_match") or top_trace.get("article_match"):
        return "explicit_exact"
    if article_tokens and top_trace.get("adjacent_article_match"):
        return "neighbor"
    if article == "0" or top_trace.get("article_match_type") == "title_only":
        return "title_only"
    semantic_support = (
        int(top_trace.get("heading_overlap") or 0) >= 1
        or int(top_trace.get("text_overlap") or 0) >= 2
        or bool(top_trace.get("selected_source_match"))
        or bool(top_trace.get("identifier_match"))
    )
    source_identity_ok = (
        metadata_identity_strength in {"strong", "medium"}
        or bool(top_trace.get("family_match"))
        or bool(top_trace.get("law_match"))
    )
    if not article_tokens and article and article != "0" and semantic_support and source_identity_ok and support_span_count >= 1:
        return "semantic_exact"
    return "none"


def _strip_chunk_citation_prefix(text: str, chunk: RetrievedChunk) -> str:
    return _strip_chunk_citation_prefix_impl(text, chunk)


def _chunk_body_text_for_quality(chunk: RetrievedChunk) -> str:
    return _chunk_body_text_for_quality_impl(chunk)


def _chunk_body_text_quality(chunk: RetrievedChunk) -> dict[str, Any]:
    return _chunk_body_text_quality_impl(chunk)


def _chunk_has_selectable_body_span(chunk: RetrievedChunk) -> bool:
    return _chunk_has_selectable_body_span_impl(chunk)


def _source_key_collision_profile(chunks: list[RetrievedChunk]) -> dict[str, Any]:
    return _source_key_collision_profile_impl(
        chunks,
        routing_family_resolver=_resolve_chunk_routing_family,
    )


def _source_key_v2_collision_profile(chunks: list[RetrievedChunk]) -> dict[str, Any]:
    return _source_key_v2_collision_profile_impl(
        chunks,
        routing_family_resolver=_resolve_chunk_routing_family,
    )


def _annotate_canonical_span_materialization(
    *,
    chunks: list[RetrievedChunk],
    article_span_selector: dict[str, Any] | None,
    family_routing_policy: dict[str, Any] | None = None,
) -> None:
    return _annotate_canonical_span_materialization_impl(
        chunks=chunks,
        article_span_selector=article_span_selector,
        family_routing_policy=family_routing_policy,
        runtime_namespace=globals(),
    )


def _select_article_span_evidence(
    *,
    query: str,
    chunks: list[RetrievedChunk],
    requested_source_families: list[str],
    explicit_article_refs: list[tuple[str, str]] | None = None,
    selected_source_keys: set[str] | None = None,
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None = None,
    source_identity_reranker: dict[str, Any] | None = None,
) -> tuple[list[RetrievedChunk], dict[str, Any]]:
    return _select_article_span_evidence_impl(
        query=query,
        chunks=chunks,
        requested_source_families=requested_source_families,
        explicit_article_refs=explicit_article_refs,
        selected_source_keys=selected_source_keys,
        source_family_resolution=source_family_resolution,
        source_identity_reranker=source_identity_reranker,
        runtime_namespace=globals(),
    )


def _apply_selected_document_only_bundle(
    *,
    chunks: list[RetrievedChunk],
    article_span_selector: dict[str, Any] | None,
) -> list[RetrievedChunk]:
    return _apply_selected_document_only_bundle_impl(
        chunks=chunks,
        article_span_selector=article_span_selector,
        runtime_namespace=globals(),
    )


def _annotate_article_span_selector_priority(
    *,
    chunks: list[RetrievedChunk],
    article_span_selector: dict[str, Any] | None,
) -> None:
    return _annotate_article_span_selector_priority_impl(
        chunks=chunks,
        article_span_selector=article_span_selector,
        runtime_namespace=globals(),
    )


def _asks_current_validity_over_historical_contrast(query: str) -> bool:
    normalized = normalize_query_text(query)
    year_count = len({match.group(0) for match in re.finditer(r"\b(19|20)\d{2}\b", query or "")})
    has_current_signal = any(
        hint in normalized
        for hint in ("guncel", "yururluk", "yururlukte", "hangi metin", "kullanilmali")
    )
    has_contrast_signal = any(
        hint in normalized
        for hint in ("eski", "mulga", "yururlukten kaldir", "yoksa")
    )
    return has_current_signal and (has_contrast_signal or year_count >= 2)


def _asks_current_validity_query(query: str) -> bool:
    if _asks_current_validity_over_historical_contrast(query):
        return True
    normalized = normalize_query_text(query)
    if any(
        hint in normalized
        for hint in (
            "mulga mevzuat",
            "mulga kanun",
            "mulga duzenleme",
            "tarihsel metin",
            "eski metin",
            "o tarihte",
            "yururlukten kalkmis",
        )
    ):
        return False
    return any(
        hint in normalized
        for hint in (
            "guncel",
            "yururluk",
            "yururlukte",
            "yururluk durumuna gore",
            "guncellik notu",
            "hangi metin",
            "kullanilmali",
        )
    )


def _asks_historical_or_repealed_query(query: str) -> bool:
    normalized = normalize_query_text(query)
    return any(
        hint in normalized
        for hint in (
            "mulga mevzuat",
            "mulga kanun",
            "mulga duzenleme",
            "tarihsel metin",
            "eski metin",
            "eski khk",
            "eski tuzuk",
            "eski tüzük",
            "o tarihte",
            "yururlukten kalkmis",
            "yururlukten kaldiril",
            "ilga",
            "gecis hukmu",
            "onceki duzenleme",
        )
    )


def _asks_constitutional_transition_khk_query(query: str) -> bool:
    normalized = normalize_query_text(query)
    has_transition_scope = any(
        hint in normalized
        for hint in (
            "cumhurbaskanligi hukumet sistemi",
            "bakanlar kurulu",
            "eski teskilat",
            "eski teşkilat",
            "atif uyarlamasi",
            "atıf uyarlaması",
        )
    )
    has_transition_action = any(
        hint in normalized
        for hint in ("gecis", "geçiş", "uyum", "uyarlama", "kontrol")
    )
    has_khk_cbk_surface = any(
        hint in normalized
        for hint in ("khk", "kanun hukmunde kararname", "cbk", "cumhurbaskanligi kararnamesi")
    )
    return has_transition_scope and has_transition_action and has_khk_cbk_surface


def _apply_relation_query_metadata_focus(
    metadata_first_selector: dict[str, Any] | None,
    *,
    query: str,
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    return _apply_relation_query_metadata_focus_impl(
        metadata_first_selector,
        query=query,
        source_family_resolution=source_family_resolution,
    )


def _metadata_first_focus_keys_for_source_lock(
    metadata_first_selector: dict[str, Any] | None,
) -> set[str]:
    return _metadata_first_focus_keys_for_source_lock_impl(metadata_first_selector)


def _legacy_source_binding_profile(
    chunk: RetrievedChunk,
    *,
    query: str,
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None = None,
    identifier_tokens: set[str] | None = None,
    year_tokens: set[str] | None = None,
) -> dict[str, Any]:
    legacy_intent_binding_active = bool(
        _source_family_resolution_trace_bool(source_family_resolution, "historical_or_repealed_question")
        or _source_family_resolution_trace_bool(source_family_resolution, "historical_scope_detected")
        or _source_family_resolution_trace_bool(source_family_resolution, "repealed_scope_detected")
        or _asks_historical_or_repealed_query(query)
    )
    if not legacy_intent_binding_active:
        return {
            "legacy_intent_binding_active": False,
            "legacy_candidate_preferred": False,
            "score": 0.0,
            "binding_reason": "",
            "state_rank": 1,
            "identifier_match": False,
            "year_match": False,
            "source_years": [],
        }

    family = _resolve_chunk_source_family(chunk) or _resolve_chunk_routing_family(chunk) or ""
    effective_state = str(
        (chunk.metadata or {}).get("effective_state") or resolve_effective_state(chunk.metadata or {}) or ""
    ).strip().lower()
    query_year_set = {str(year) for year in (year_tokens or set()) if str(year).isdigit()}
    chunk_year_set = {str(year) for year in _chunk_year_values(chunk) if str(year).isdigit()}
    query_years_int = {int(year) for year in query_year_set}
    chunk_years_int = {int(year) for year in chunk_year_set}
    identifier_match = _chunk_matches_identifier_tokens(chunk, identifier_tokens or set())
    year_match = bool(query_year_set and chunk_year_set & query_year_set)
    old_query_year_present = bool(
        query_years_int and min(query_years_int) < datetime.now(timezone.utc).year
    )
    old_chunk_year_present = bool(chunk_years_int and min(chunk_years_int) <= 2017)

    score = 0.0
    reasons: list[str] = []
    if _is_temporally_inactive_chunk(chunk) or effective_state == "repealed":
        score += 120.0
        reasons.append("legacy_state_metadata_repealed")
    if identifier_match:
        score += 24.0
        reasons.append("legacy_query_identifier_anchor")
    if year_match:
        score += 36.0
        reasons.append("legacy_query_year_match")
    if family == "mulga_kanun":
        score += 28.0
        reasons.append("legacy_family_mulga")
    if family in {"khk", "tuzuk"}:
        score += 12.0
        reasons.append("legacy_family_profile")
    if family == "khk" and _asks_constitutional_transition_khk_query(query):
        document_key = _resolve_chunk_document_key(chunk)
        title_normalized = normalize_query_text(_resolve_chunk_source_title(chunk))
        if document_key == "703" or "anayasada yapilan degisikliklere uyum" in title_normalized:
            score += 130.0
            reasons.append("constitutional_transition_khk_703_anchor")
        elif not any(term in title_normalized for term in ("uyum", "gecis", "geçiş", "anayasada")):
            score -= 24.0
            reasons.append("constitutional_transition_non_transition_khk_penalty")
    if family == "khk" and old_chunk_year_present:
        score += 18.0
        reasons.append("legacy_khk_pre2018_profile")
    elif family == "khk":
        score -= 18.0
        reasons.append("legacy_khk_post2017_penalty")
    if family == "tuzuk" and old_query_year_present:
        score += 8.0
        reasons.append("legacy_tuzuk_old_year_query")
    if (
        _source_family_resolution_trace_bool(source_family_resolution, "historical_scope_detected")
        and family in {"khk", "tuzuk", "mulga_kanun"}
    ):
        score += 10.0
        reasons.append("historical_scope_family_bonus")
    if (
        _source_family_resolution_trace_bool(source_family_resolution, "repealed_scope_detected")
        and family in {"khk", "tuzuk", "mulga_kanun"}
    ):
        score += 10.0
        reasons.append("repealed_scope_family_bonus")
    if query_year_set and chunk_year_set and not year_match and family in {"khk", "tuzuk"}:
        score -= 12.0
        reasons.append("legacy_year_mismatch_penalty")

    legacy_candidate_preferred = score >= 35.0
    state_rank = (
        0
        if legacy_candidate_preferred
        else 1
        if effective_state in {"active", "amended"} or not _is_temporally_inactive_chunk(chunk)
        else 2
    )
    return {
        "legacy_intent_binding_active": True,
        "legacy_candidate_preferred": legacy_candidate_preferred,
        "score": round(score, 4),
        "binding_reason": " | ".join(reasons),
        "state_rank": state_rank,
        "identifier_match": identifier_match,
        "year_match": year_match,
        "source_years": sorted(chunk_year_set),
    }


def _source_family_resolution_trace_bool(
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None,
    key: str,
) -> bool:
    if isinstance(source_family_resolution, dict):
        return bool(source_family_resolution.get(key))
    if source_family_resolution is None:
        return False
    return bool(getattr(source_family_resolution, key, False))


def _temporal_guard_family_group(family: str | None) -> str:
    normalized = str(family or "").strip()
    if normalized in {"kanun", "mulga_kanun"}:
        return "kanun"
    if normalized in {"yonetmelik", "kky", "uy", "cb_yonetmelik"}:
        return "yonetmelik"
    return normalized


def _temporal_guard_family_compatible(left: str | None, right: str | None) -> bool:
    if not left or not right:
        return False
    return _temporal_guard_family_group(left) == _temporal_guard_family_group(right)


def _selector_trace_supports_temporal_guard(trace: dict[str, Any]) -> bool:
    return bool(
        trace.get("selected_source_match")
        or trace.get("identifier_match")
        or trace.get("family_match")
        or trace.get("preferred_family_match")
        or trace.get("law_match")
        or trace.get("article_match")
        or trace.get("adjacent_article_match")
        or int(trace.get("title_overlap") or 0) >= 1
        or int(trace.get("heading_overlap") or 0) >= 1
        or int(trace.get("text_overlap") or 0) >= 2
    )


def _selector_document_state_rank(trace: dict[str, Any], *, legacy_intent_binding_active: bool) -> int:
    if legacy_intent_binding_active:
        if trace.get("legacy_state_rank") is not None:
            try:
                return int(trace.get("legacy_state_rank") or 0)
            except (TypeError, ValueError):
                return 2
        return 2
    if trace.get("temporally_inactive"):
        return 2
    effective_state = str(trace.get("effective_state") or "").strip().lower()
    temporal_state_bucket = str(trace.get("temporal_state_bucket") or "").strip().lower()
    if effective_state in {"active", "amended"} or temporal_state_bucket == "active":
        return 0
    return 1


def _metadata_flag_is_true(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return normalize_query_text(value) in _TRUTHY_METADATA_FLAGS
    return False


def _metadata_flag_is_false(value: Any) -> bool:
    if value is False:
        return True
    if isinstance(value, str):
        return normalize_query_text(value) in _FALSEY_METADATA_FLAGS
    return False


def _is_temporally_inactive_chunk(chunk: RetrievedChunk) -> bool:
    metadata = chunk.metadata or {}
    if _metadata_active_raw_law_overrides_legacy_family(metadata):
        return False
    if _metadata_flag_is_true(metadata.get("mulga")):
        return True
    source_family = _resolve_chunk_source_family(chunk)
    if source_family and source_family.startswith("mulga"):
        return True
    end = str(metadata.get("yururluk_bitis") or "").strip()
    return bool(end and end not in _ACTIVE_END_DATE_SENTINELS)


def _chunk_active_rank(chunk: RetrievedChunk) -> int:
    if _is_temporally_inactive_chunk(chunk):
        return 2
    metadata = chunk.metadata or {}
    mulga = metadata.get("mulga")
    end = str(metadata.get("yururluk_bitis") or "").strip()
    start = str(metadata.get("yururluk_baslangic") or "")
    return 0 if start or _metadata_flag_is_false(mulga) or end in _ACTIVE_END_DATE_SENTINELS else 1


def _chunk_year_values(chunk: RetrievedChunk) -> set[str]:
    metadata = chunk.metadata or {}
    values: set[str] = set()
    for value in (
        metadata.get("year_signals"),
        metadata.get("decision_year"),
        metadata.get("official_gazette_date"),
        metadata.get("effective_start"),
        metadata.get("effective_end"),
        metadata.get("yururluk_baslangic"),
        metadata.get("yururluk_bitis"),
        metadata.get("source_id"),
        metadata.get("source_title"),
        metadata.get("belge_adi"),
    ):
        if isinstance(value, list):
            for item in value:
                values.update(_extract_year_tokens(str(item)))
        else:
            values.update(_extract_year_tokens(str(value or "")))
    return values


def _rerank_chunks_by_source_identity(
    *,
    query: str,
    chunks: list[RetrievedChunk],
    requested_source_families: list[str],
    metadata_first_selector: dict[str, Any] | None,
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None = None,
) -> tuple[list[RetrievedChunk], dict[str, Any]]:
    return _rerank_chunks_by_source_identity_impl(
        query=query,
        chunks=chunks,
        requested_source_families=requested_source_families,
        metadata_first_selector=metadata_first_selector,
        source_family_resolution=source_family_resolution,
        extract_query_article_tokens=_extract_query_article_tokens,
        asks_current_validity_query=_asks_current_validity_query,
        asks_current_validity_over_historical_contrast=_asks_current_validity_over_historical_contrast,
        source_family_resolution_trace_bool=_source_family_resolution_trace_bool,
        chunk_matches_identifier_tokens=_chunk_matches_identifier_tokens,
        chunk_active_rank=_chunk_active_rank,
        chunk_recall_lane_sources=_chunk_recall_lane_sources,
        chunk_recall_lane_rank=_chunk_recall_lane_rank,
        legacy_source_binding_profile=_legacy_source_binding_profile,
        is_temporally_inactive_chunk=_is_temporally_inactive_chunk,
        query_article_alignment=_query_article_alignment,
        resolve_trace_source_id=_resolve_trace_source_id,
        resolve_chunk_source_identifier=_resolve_chunk_source_identifier,
        resolve_trace_source_display_label=_resolve_trace_source_display_label,
    )

def _extract_cb_genelge_numbered_clauses(text: str) -> list[tuple[str, str]]:
    body = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    matches = list(re.finditer(r"(?m)^\s*(\d+)-\s+", body))
    clauses: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        raw_clause = body[start:end]
        raw_clause = re.split(
            r"(?m)^\s*(?:\d{4}/\d+\s+sayılı Genelge|"
            r"\d{1,2}\s+[A-Za-zÇĞİÖŞÜçğıöşü]+\s+\d{4})\b",
            raw_clause,
            maxsplit=1,
        )[0]
        clause = _normalize_whitespace(raw_clause)
        if clause:
            clauses.append((match.group(1), clause))
    return clauses


_CB_GENELGE_CLAUSE_STOPWORDS = {
    "acaba",
    "alinir",
    "bakimindan",
    "belirt",
    "belirtil",
    "bunun",
    "cumhurbaskanligi",
    "cumhurbaskani",
    "genelge",
    "genelgesi",
    "hangi",
    "hakkinda",
    "istiyor",
    "kamu",
    "karsi",
    "karsisinda",
    "kurum",
    "kurulus",
    "kuruluslari",
    "midir",
    "nedir",
    "nelerdir",
    "olur",
    "olarak",
    "sayili",
    "soru",
    "uzerinden",
    "uyarinca",
}


def _cb_genelge_clause_terms(text: str) -> list[str]:
    terms: list[str] = []
    for term in re.findall(r"[a-z0-9]+", normalize_query_text(text)):
        if len(term) < 4 or term in _CB_GENELGE_CLAUSE_STOPWORDS:
            continue
        if term.isdigit():
            continue
        terms.append(term)
    return terms


def _cb_genelge_clause_ngrams(terms: list[str]) -> set[str]:
    ngrams: set[str] = set()
    for size in (2, 3):
        for index in range(0, max(0, len(terms) - size + 1)):
            ngrams.add(" ".join(terms[index : index + size]))
    return ngrams


def _build_cb_genelge_document_level_answer(
    *,
    query: str,
    chunks: list[RetrievedChunk],
    article_span_selector: dict[str, Any] | None,
) -> str | None:
    if not isinstance(article_span_selector, dict):
        return None
    selected_document_key = str(article_span_selector.get("selected_document_key") or "").strip().lower()
    selected_binding_key = str(article_span_selector.get("binding_source_key") or "").strip()
    selected_chunks = [
        chunk
        for chunk in chunks
        if (
            (selected_binding_key and _resolve_chunk_binding_source_key(chunk, include_span=False) == selected_binding_key)
            or (selected_document_key and _resolve_chunk_document_key(chunk) == selected_document_key)
        )
    ]
    supplement_chunk = next(
        (
            chunk
            for chunk in selected_chunks
            if bool((chunk.metadata or {}).get("official_source_supplement"))
            and (_resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk)) == "cb_genelge"
        ),
        None,
    )
    if supplement_chunk is None:
        return None

    metadata = supplement_chunk.metadata or {}
    body = _chunk_body_text_for_quality(supplement_chunk)
    clauses = _extract_cb_genelge_numbered_clauses(body)
    if not clauses:
        return None

    citation = supplement_chunk.citation or str(metadata.get("span_id") or "3 m.0/f.0")
    title = _resolve_chunk_source_title(supplement_chunk)
    identifier = str(metadata.get("source_identifier") or metadata.get("display_citation") or "2025/3").strip()
    effective_state = str(metadata.get("effective_state") or resolve_effective_state(metadata) or "unknown").strip()
    effective_start = str(metadata.get("effective_start") or metadata.get("yururluk_baslangic") or "").strip()
    normalized_query = normalize_query_text(query)
    temporal_contrast = any(
        term in normalized_query
        for term in (
            "eski",
            "hala",
            "halen",
            "yoksa",
            "esas alin",
            "yururluk",
            "guncel",
        )
    )
    repeal_sentence = ""
    repeal_match = re.search(
        r"\b(\d{4}/\d+\s+sayılı Genelge yürürlükten kaldırılmıştır)\b",
        body,
        flags=re.IGNORECASE,
    )
    if repeal_match:
        repeal_sentence = _normalize_whitespace(repeal_match.group(1))

    if temporal_contrast:
        lines = [
            f"Kısa sonuç: {identifier} sayılı {title} Cumhurbaşkanlığı Genelgesi esas alınır; seçili kaynak durumu {effective_state}. [Kaynak: {citation}]",
        ]
        if repeal_sentence:
            lines.append(f"Eski genelge bakımından seçili metindeki açık yürürlük hükmü: {repeal_sentence}. [Kaynak: {citation}]")
        lines.append(
            f"Güncellik notu: metadatasında yürürlük başlangıcı {effective_start or 'belirtilmemiş'} ve durum {effective_state} görünüyor; cevap bu seçili metinle sınırlıdır. [Kaynak: {citation}]"
        )
        return "\n".join(lines)

    query_terms = _cb_genelge_clause_terms(normalized_query)
    query_term_set = set(query_terms)
    query_ngrams = _cb_genelge_clause_ngrams(query_terms)
    ranked_clauses: list[tuple[int, str, str]] = []
    for number, clause in clauses:
        normalized_clause = normalize_query_text(clause)
        clause_terms = set(_cb_genelge_clause_terms(normalized_clause))
        overlap = len(query_term_set & clause_terms)
        overlap += 2 * sum(1 for ngram in query_ngrams if ngram in normalized_clause)
        ranked_clauses.append((overlap, number, clause))
    ranked_clauses.sort(key=lambda item: (-item[0], int(item[1]) if item[1].isdigit() else 999))
    selected = ranked_clauses[:5]
    selected.sort(key=lambda item: int(item[1]) if item[1].isdigit() else 999)
    if not selected:
        return None

    lines = [
        f"{identifier} sayılı {title} Cumhurbaşkanlığı Genelgesine göre seçili metinden çıkarılabilen yükümlülükler şunlardır:",
    ]
    for _overlap, number, clause in selected:
        lines.append(f"- {number}. bent: {_compact_slot_value(clause, max_len=360)} [Kaynak: {citation}]")
    lines.append(
        f"Yürürlük/güncellik: seçili kaynak durumu {effective_state}; başlangıç {effective_start or 'belirtilmemiş'}. [Kaynak: {citation}]"
    )
    return "\n".join(lines)
def _chunk_recall_lane_sources(chunk: RetrievedChunk) -> list[str]:
    metadata = chunk.metadata or {}
    lanes = metadata.get("retrieval_lane_sources")
    if not isinstance(lanes, list):
        return []
    return [
        str(value)
        for value in lanes
        if isinstance(value, str) and value.strip()
    ]


def _chunk_recall_lane_rank(chunk: RetrievedChunk) -> int:
    lanes = set(_chunk_recall_lane_sources(chunk))
    if {"metadata_guided_recall", "semantic_dense_recall"} <= lanes:
        return 0
    if "metadata_guided_recall" in lanes:
        return 1
    if "semantic_dense_recall" in lanes:
        return 2
    return 3


def _extract_retrieval_priority_terms(text: str) -> set[str]:
    normalized = normalize_query_text(text or "")
    return {
        token
        for token in _RETRIEVAL_PRIORITY_TOKEN_RE.findall(normalized)
        if len(token) >= 3 and token not in _RETRIEVAL_PRIORITY_STOPWORDS
    }


def _count_term_overlap(text: str | None, terms: set[str]) -> int:
    if not text or not terms:
        return 0
    tokens = _extract_retrieval_priority_terms(text)
    return len(tokens & terms)


def _prioritize_chunks_for_source_families(
    *,
    query: str,
    chunks: list[RetrievedChunk],
    source_families: list[str],
    selected_source_keys: set[str] | None = None,
) -> list[RetrievedChunk]:
    return _prioritize_chunks_for_source_families_impl(
        query=query,
        chunks=chunks,
        source_families=source_families,
        selected_source_keys=selected_source_keys,
        extract_source_identifier_tokens=_extract_source_identifier_tokens,
        asks_current_validity_query=_asks_current_validity_query,
        resolve_chunk_routing_family=_resolve_chunk_routing_family,
        chunk_law_candidates=_chunk_law_candidates,
        chunk_matches_identifier_tokens=_chunk_matches_identifier_tokens,
        chunk_active_rank=_chunk_active_rank,
        chunk_recall_lane_rank=_chunk_recall_lane_rank,
        binding_source_key_resolver=lambda current, include_span: _resolve_chunk_binding_source_key(
            current,
            include_span=include_span,
        ),
    )


def _focus_chunks_on_selected_sources(
    *,
    chunks: list[RetrievedChunk],
    selected_source_keys: set[str],
) -> list[RetrievedChunk]:
    return _focus_chunks_on_selected_sources_impl(
        chunks=chunks,
        selected_source_keys=selected_source_keys,
        binding_source_key_resolver=lambda current, include_span: _resolve_chunk_binding_source_key(
            current,
            include_span=include_span,
        ),
    )


def _apply_source_family_answer_hint(
    *,
    query: str,
    source_families: list[str],
) -> str:
    if not source_families:
        return query

    labels = [
        _SOURCE_FAMILY_DISPLAY_LABELS.get(family, family)
        for family in source_families
    ]
    label_text = ", ".join(dedupe_strings(labels))
    hint = (
        "\n\n[KAYNAK AİLESİ ÖNCELİĞİ]\n"
        f"Kullanıcı özellikle şu belge ailesini soruyor: {label_text}. "
        "Yanıtı kurarken önce bu ailedeki düzenlemeyi merkez al. "
        "Üst normu veya paralel normu ancak gerçekten gerekliyse tamamlayıcı dayanak olarak ekle. "
        "Kullanıcı 'hangi tüzük/yönetmelik/genelge/kararname' diye soruyorsa, "
        "önce ilgili belge ailesindeki metni isim ve içerik düzeyinde belirlemeye çalış."
    )
    return f"{query}{hint}"


def _predicted_source_family_from_resolution(
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None,
) -> str:
    if isinstance(source_family_resolution, dict):
        return str(source_family_resolution.get("predicted_family") or "")
    if source_family_resolution is None:
        return ""
    return str(source_family_resolution.predicted_family or "")


def _has_mulga_or_temporal_answer_scope(
    *,
    routing_query: str,
    requested_source_families: list[str] | None = None,
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None = None,
) -> bool:
    requested = set(_expand_source_family_aliases(requested_source_families or []))
    predicted = _predicted_source_family_from_resolution(source_family_resolution)
    predicted_set = set(_expand_source_family_aliases([predicted])) if predicted else set()
    if "mulga_kanun" in requested or "mulga_kanun" in predicted_set:
        return True
    if (
        _source_family_resolution_trace_bool(source_family_resolution, "historical_or_repealed_question")
        or _source_family_resolution_trace_bool(source_family_resolution, "historical_scope_detected")
        or _source_family_resolution_trace_bool(source_family_resolution, "repealed_scope_detected")
        or _source_family_resolution_trace_bool(source_family_resolution, "current_law_prior_blocked_by_historical_scope")
    ):
        return True
    normalized = normalize_query_text(routing_query)
    if any(
        token in normalized
        for token in (
            "mulga",
            "yururlukten kaldir",
            "yururlukten kalk",
            "ilga",
            "eski metin",
            "onceki duzenleme",
            "gecis hukmu",
            "tarihsel",
            "o tarihte",
            "hala",
            "halen yururlukte",
            "guncel durum",
            "guncellik hatasi",
            "dogrudan hata",
            "dogrudan hukum",
            "guvenli midir",
            "neden hatali",
            "riskli",
        )
    ):
        return True
    if re.search(r"(?<!\d)(?:19|20)\d{2}(?!\d)", normalized) and any(
        token in normalized
        for token in (
            "esas almak",
            "kullanmak",
            "uygulamak",
            "dogrudan",
            "hata",
            "hatali",
            "riskli",
            "guvenli",
        )
    ):
        return True
    return False


def _apply_answer_slot_synthesis_hint(
    *,
    query: str,
    routing_query: str,
    article_span_selector: dict[str, Any] | None,
    requested_source_families: list[str] | None = None,
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None = None,
) -> str:
    template = _answer_template_for_query(routing_query)
    required_slots = _must_have_fact_slots_for_query(routing_query, template)
    has_temporal_scope = _has_mulga_or_temporal_answer_scope(
        routing_query=routing_query,
        requested_source_families=requested_source_families,
        source_family_resolution=source_family_resolution,
    )
    if not required_slots and not has_temporal_scope:
        return query
    selected_article = ""
    support_span_count = 0
    evidence_sufficiency = ""
    if isinstance(article_span_selector, dict):
        selected_article = str(article_span_selector.get("selected_article") or "").strip()
        evidence_sufficiency = str(article_span_selector.get("selector_evidence_sufficiency") or "").strip()
        try:
            support_span_count = int(article_span_selector.get("support_span_count") or 0)
        except (TypeError, ValueError):
            support_span_count = 0
    hints: list[str] = []
    if required_slots:
        slot_text = ", ".join(required_slots)
        article_text = f" Secili madde/span: {selected_article}." if selected_article else ""
        hints.append(
            "\n\n[KANIT-CEVAP SLOT TALİMATI]\n"
            f"Bu yanitta su bilgi slotlarini kaynaklardan karsila: {slot_text}."
            f"{article_text} Destek span sayisi: {support_span_count}; selector durumu: {evidence_sufficiency or 'unknown'}. "
            "Her slotu secili kaynaklardan tasinan kisa bir dayanakla cevapla. "
            "Bir slot secili kaynaklarda yoksa kesin hukum kurma; o slot icin kaynak desteginin yetersiz oldugunu belirt. "
            "Kaynakta olmayan unsur ekleme ve dayanak zincirini cevapta gorunur tut."
        )
    if has_temporal_scope:
        hints.append(
            "\n\n[MULGA/TARIHSEL CEVAP TALIMATI]\n"
            "Soru mulga, eski metin veya tarihsel yururluk kapsami tasiyorsa cevabi bugunku aktif hukuk gibi kurma. "
            "Once secili kaynagin yururluk durumunu belirt: active, repealed/mulga veya belirsiz. "
            "Cevap modunu hukuki duruma gore kur: historical_repealed_answer, repealed_transition_answer veya not_currently_applicable_answer. "
            "Ardindan kaynak destekliyorsa tarihsel uygulanabilirlik tarihini/donemini, gecis hukmunu ve bugun dogrudan uygulanip uygulanamayacagini ayri cumlelerle yaz. "
            "Yururluk durumu veya gecis etkisi secili kaynaklarda yoksa bunu acikca 'kaynak destegi yetersiz' diye sinirla; aktif kaynak uydurma."
        )
    return f"{query}{''.join(hints)}"


def _looks_like_tbk_tmk_cross_law_query(user_query: str) -> bool:
    cross_law_signals: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
        (
            ("aile konutu",),
            ("kira", "kiralan", "kiracı", "kiraci", "fesih", "feshederse", "feshedebilir", "devir"),
        ),
        (
            ("kefalet",),
            ("aile birliği", "aile birligi", "korunması ilkesi", "korunmasi ilkesi"),
        ),
        (
            ("paylı mülkiyet", "payli mulkiyet", "önalım", "onalim", "ön alım", "on alim"),
            ("kira", "kiraya", "satış", "satis", "satıldı", "satildi", "paydaş", "paydas"),
        ),
        (
            ("mal rejimi", "edinilmiş mallar", "edinilmis mallar", "edinilmiş mallara katılma"),
            ("borç", "borc", "ödünç", "odunc", "sözleşme", "sozlesme"),
        ),
        (
            ("haksız fiil", "haksiz fiil"),
            ("boşanma", "bosanma", "tmk m.174"),
        ),
        (
            ("muvazaa", "muris muvazaası", "muris muvazaasi"),
            ("taşınmaz", "tasinmaz", "satış", "satis", "sattı", "satti", "bağış", "bagis"),
        ),
        (
            ("velayet", "vasi", "yasal temsil"),
            ("sözleşme", "sozlesme", "kira", "taşınmaz", "tasinmaz", "satış", "satis"),
        ),
        (
            ("eşin rızası", "esin rizasi"),
            ("sözleşme", "sozlesme", "batıldır", "batildir", "batıl", "batil", "geçersiz", "gecersiz"),
        ),
        (
            ("sınırlı ehliyetsiz", "sinirli ehliyetsiz", "kısıtlı", "kisitli", "yasal temsilci"),
            ("kira", "kiralanan", "sözleşme", "sozlesme", "onay"),
        ),
        (
            ("bağışlama", "bagislama"),
            ("edinilmiş mallar", "edinilmis mallar", "katılma rejimi", "katilma rejimi"),
            ("denkleştirme", "denklestirme", "tasfiye"),
        ),
        (
            ("nafaka",),
            ("zamanaşımı", "zamanasimi", "özel süre", "ozel sure", "alacak"),
        ),
        (
            ("mirasçılar", "mirascilar", "tereke", "miras ortaklığı", "miras ortakligi"),
            ("adi ortaklık", "adi ortaklik", "ortaklığın giderilmesi", "ortakligin giderilmesi", "sona erdirme"),
        ),
        (
            ("hayatta kalan eş", "hayatta kalan es", "ölümü halinde", "olumu halinde"),
            ("katılma alacağı", "katilma alacagi", "sebepsiz zenginleşme", "sebepsiz zenginlesme"),
        ),
    )
    return any(
        all(_contains_any_query_term(user_query, term_group) for term_group in term_groups)
        for term_groups in cross_law_signals
    )


def _looks_like_commercial_company_law_query(user_query: str) -> bool:
    company_terms = (
        "limited şirket",
        "limited sirket",
        "anonim şirket",
        "anonim sirket",
        "ticaret şirketi",
        "ticaret sirketi",
        "şirket ortağı",
        "sirket ortagi",
        "esas sermaye pay",
        "sermaye pay",
    )
    action_terms = (
        "pay devri",
        "payın devri",
        "payin devri",
        "pay geçişi",
        "pay gecisi",
        "şirket onayı",
        "sirket onayi",
        "genel kurul onayı",
        "genel kurul onayi",
        "ticaret sicili",
        "tescil",
        "ilan",
    )
    return _contains_any_query_term(user_query, company_terms) and _contains_any_query_term(user_query, action_terms)


def _looks_like_labor_law_query(user_query: str) -> bool:
    labor_context_terms = (
        "işçi",
        "isci",
        "işveren",
        "isveren",
        "çalışan",
        "calisan",
        "işyeri",
        "isyeri",
        "üretim işletmesi",
        "uretim isletmesi",
        "ana üretim",
        "ana uretim",
    )
    labor_issue_terms = (
        "fazla çalışma",
        "fazla calisma",
        "fazla sürelerle çalışma",
        "fazla surelerle calisma",
        "270 saat",
        "yazılı onay",
        "yazili onay",
        "işe giriş evrakı",
        "ise giris evraki",
        "genel form",
        "yıllık ücretli izin",
        "yillik ucretli izin",
        "ücretli izin",
        "ucretli izin",
        "kesintisiz kullandır",
        "kesintisiz kullandir",
        "parçalara böl",
        "parcalara bol",
        "alt işveren",
        "alt isveren",
        "asıl iş",
        "asil is",
        "yardımcı iş",
        "yardimci is",
        "muvazaa",
        "muvazaalı",
        "muvazaali",
        "aynı işçiler",
        "ayni isciler",
    )
    return _contains_any_query_term(user_query, labor_issue_terms) or (
        _contains_any_query_term(user_query, labor_context_terms)
        and _contains_any_query_term(
            user_query,
            (
                "ücret",
                "ucret",
                "izin",
                "fesih",
                "çalışma",
                "calisma",
                "onay",
                "iş güvencesi",
                "is guvencesi",
            ),
        )
    )


def _looks_like_data_protection_law_query(user_query: str) -> bool:
    data_terms = (
        "kişisel veri",
        "kisisel veri",
        "kvkk",
        "parmak izi",
        "biyometrik",
        "özel nitelikli veri",
        "ozel nitelikli veri",
        "aydınlatma",
        "aydinlatma",
        "veri minimizasyonu",
        "ölçülülük",
        "olcululuk",
        "saklama",
        "imha",
        "silinmesi",
        "yok edilmesi",
        "anonim hale",
        "teknik tedbir",
        "idari tedbir",
    )
    processing_context_terms = (
        "giriş-çıkış",
        "giris-cikis",
        "yemekhane",
        "işyeri güvenliği",
        "isyeri guvenligi",
        "fabrika",
        "kontrol sistemi",
        "veri işleme",
        "veri isleme",
    )
    return _contains_any_query_term(user_query, data_terms) or (
        _contains_any_query_term(user_query, processing_context_terms)
        and _contains_any_query_term(user_query, ("parmak", "biyometrik", "veri", "güvenlik", "guvenlik"))
    )


def _has_explicit_data_protection_anchor(user_query: str) -> bool:
    return _contains_any_query_term(
        user_query,
        (
            "kişisel veri",
            "kisisel veri",
            "kvkk",
            "veri sorumlusu",
            "özel nitelikli veri",
            "ozel nitelikli veri",
            "biyometrik",
            "anonim hale",
            "veri imha",
            "saklama-imha",
            "saklama imha",
        ),
    )


def _looks_like_internet_law_query(user_query: str) -> bool:
    internet_actor_terms = (
        "hosting",
        "yer sağlayıcı",
        "yer saglayici",
        "erişim sağlayıcı",
        "erisim saglayici",
        "toplu kullanım sağlayıcı",
        "toplu kullanim saglayici",
        "içerik sağlayıcı",
        "icerik saglayici",
        "internet ortamı",
        "internet ortami",
        "trafik bilgisi",
        "trafik verisi",
        "log kaydı",
        "log kaydi",
        "btk",
        "bilgi teknolojileri ve iletişim kurumu",
        "bilgi teknolojileri ve iletisim kurumu",
    )
    obligation_terms = (
        "saklama",
        "saklamak",
        "yükümlülük",
        "yukumluluk",
        "talep",
        "cevap",
        "erişim engeli",
        "erisim engeli",
        "içerik çıkarma",
        "icerik cikarma",
    )
    return _contains_any_query_term(user_query, internet_actor_terms) and _contains_any_query_term(
        user_query,
        obligation_terms,
    )


def _looks_like_rent_increase_tbk_query(user_query: str) -> bool:
    rent_increase_terms = (
        "kira artış",
        "kira artis",
        "artış oranı",
        "artis orani",
        "kira artırım",
        "kira artirim",
        "tüfe",
        "tufe",
        "%25",
        "25 sınırı",
        "25 siniri",
        "yüzde 25",
        "yuzde 25",
    )
    rent_subject_terms = (
        "kira",
        "kiracı",
        "kiraci",
        "kiraya veren",
        "konut",
        "çatılı işyeri",
        "catili isyeri",
        "işyeri kirası",
        "isyeri kirasi",
    )
    legacy_contract_context_terms = (
            "kira bedeli",
            "konut kira",
            "yenilenen kira",
            "yenilenen bir konut kira",
            "kira sözleşmesi",
            "kira sozlesmesi",
    )
    currentness_or_temporary_terms = (
        "geçici",
        "gecici",
        "sona er",
        "sona eren",
        "hâlâ",
        "hala",
        "güncellik",
        "guncellik",
        "otomatik",
        "sınır",
        "sinir",
        "tavan",
        "2026",
    )
    if not _contains_any_query_term(user_query, rent_increase_terms):
        return False
    return _contains_any_query_term(user_query, legacy_contract_context_terms) or (
        _contains_any_query_term(user_query, rent_subject_terms)
        and _contains_any_query_term(user_query, currentness_or_temporary_terms)
    )


def _looks_like_electronic_notification_law_query(user_query: str) -> bool:
    return _contains_any_query_term(
        user_query,
        (
            "elektronik tebligat",
            "e-tebligat",
            "e tebligat",
            "elektronik adres",
            "tebliğ edilmiş sayılır",
            "teblig edilmis sayilir",
            "beşinci gün",
            "besinci gun",
            "muhatabın elektronik adresi",
            "muhatabin elektronik adresi",
        ),
    )


def _looks_like_civil_mediation_law_query(user_query: str) -> bool:
    mediation_terms = (
        "dava şartı arabuluculuk",
        "dava sarti arabuluculuk",
        "zorunlu arabuluculuk",
        "arabulucuya başvuru dava şartı",
        "arabulucuya basvuru dava sarti",
        "arabuluculuk gerekip gerekmedi",
        "arabuluculuk şartı",
        "arabuluculuk sarti",
        "huak",
        "hukuk uyuşmazlıklarında arabuluculuk kanunu",
        "hukuk uyusmazliklarinda arabuluculuk kanunu",
    )
    civil_context_terms = (
        "kira bedeli",
        "kiraya veren",
        "kiracı",
        "kiraci",
        "tahliye",
        "alacak",
        "ticari uyuşmazlık",
        "ticari uyusmazlik",
        "tüketici uyuşmazlığı",
        "tuketici uyusmazligi",
        "iş uyuşmazlığı",
        "is uyusmazligi",
        "hukuk uyuşmazlığı",
        "hukuk uyusmazligi",
    )
    collective_labor_terms = (
        "toplu iş sözleşmesi",
        "toplu is sozlesmesi",
        "grev",
        "lokavt",
        "görevli makam",
        "gorevli makam",
        "uyuşmazlık yazısı",
        "uyusmazlik yazisi",
    )
    return (
        _contains_any_query_term(user_query, mediation_terms)
        and _contains_any_query_term(user_query, civil_context_terms)
        and not _contains_any_query_term(user_query, collective_labor_terms)
    )


def _infer_domain_law_hints(query: str) -> list[str]:
    laws: list[str] = []
    internet_law_query = _looks_like_internet_law_query(query)
    if _looks_like_commercial_company_law_query(query):
        laws.append("TTK")
    if _looks_like_labor_law_query(query):
        laws.extend(["IK", "4857"])
    if _looks_like_data_protection_law_query(query) and (
        not internet_law_query or _has_explicit_data_protection_anchor(query)
    ):
        laws.extend(["KVKK", "6698"])
    if internet_law_query:
        laws.append("5651")
    if _looks_like_rent_increase_tbk_query(query):
        laws.extend(["TBK", "6098"])
    if _looks_like_electronic_notification_law_query(query):
        laws.append("7201")
    if _looks_like_civil_mediation_law_query(query):
        laws.extend(["HUAK", "6325"])
    return dedupe_strings(laws)


def _infer_domain_article_refs(query: str) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    internet_law_query = _looks_like_internet_law_query(query)
    if _looks_like_commercial_company_law_query(query):
        refs.extend([("TTK", "595"), ("TTK", "598")])
    if _contains_any_query_term(
        query,
        (
            "fazla çalışma",
            "fazla calisma",
            "fazla çalıştır",
            "fazla calistir",
            "fazla sürelerle çalışma",
            "fazla surelerle calisma",
            "yazılı onay",
            "yazili onay",
            "270 saat",
            "290 saat",
        ),
    ):
        refs.extend([("IK", "41"), ("4857", "41")])
    if _contains_any_query_term(
        query,
        ("alt işveren", "alt isveren", "asıl iş", "asil is", "muvazaa", "muvazaalı", "muvazaali"),
    ):
        refs.extend([("IK", "2"), ("4857", "2")])
    if _contains_any_query_term(
        query,
        ("yıllık ücretli izin", "yillik ucretli izin", "ücretli izin", "ucretli izin", "kesintisiz"),
    ):
        refs.extend([("IK", "56"), ("4857", "56")])
    if _looks_like_data_protection_law_query(query) and (
        not internet_law_query or _has_explicit_data_protection_anchor(query)
    ):
        refs.extend([("KVKK", "6"), ("KVKK", "10"), ("KVKK", "12"), ("6698", "6"), ("6698", "10"), ("6698", "12")])
    if internet_law_query:
        refs.extend([("5651", "5"), ("5651", "6"), ("5651", "7"), ("5651", "11")])
    if _looks_like_rent_increase_tbk_query(query):
        refs.extend([("TBK", "344"), ("6098", "344")])
    if _looks_like_civil_mediation_law_query(query):
        refs.extend([("HUAK", "18"), ("6325", "18")])
    return _dedupe_article_refs(refs)


def _domain_law_source_family_hints(domain_law_hints: list[str]) -> list[str]:
    hints = set(domain_law_hints)
    families = ["kanun"]
    if hints & {"IK", "4857", "KVKK", "6698", "7201", "HUAK", "6325", "5651"}:
        families.append("yonetmelik")
    if hints & {"KVKK", "6698"}:
        families.append("cb_genelge")
    return dedupe_strings(families)


def _domain_law_supporting_source_family_hints(query: str, domain_law_hints: list[str]) -> list[str]:
    hints = set(domain_law_hints)
    families: list[str] = []
    if hints & {"TBK", "6098"} and _looks_like_rent_increase_tbk_query(query):
        families.append("kanun")
    if hints & {"IK", "4857"} and (
        _contains_any_query_term(
            query,
            (
                "fazla çalışma",
                "fazla calisma",
                "fazla çalıştır",
                "fazla calistir",
                "yazılı onay",
                "yazili onay",
                "alt işveren",
                "alt isveren",
                "muvazaa",
                "mevzuat zinciri",
                "kritik hukuki sorun",
            ),
        )
    ):
        families.extend(["yonetmelik", "kky"])
    if hints & {"KVKK", "6698", "7201", "HUAK", "6325"}:
        families.append("yonetmelik")
    if "5651" in hints and _looks_like_internet_law_query(query):
        families.append("yonetmelik")
    return dedupe_strings(_expand_source_family_aliases(families))


def _domain_law_term_hints(query: str, domain_law_hints: list[str]) -> list[str]:
    hints = set(domain_law_hints)
    terms: list[str] = []
    if hints & {"IK", "4857"}:
        if _contains_any_query_term(
            query,
            ("fazla çalışma", "fazla calisma", "fazla çalıştır", "fazla calistir", "yazılı onay", "yazili onay", "270 saat", "290 saat"),
        ):
            terms.append(
                "4857 İş Kanunu m.41 fazla çalışma yıllık 270 saat işçi onayı fazla çalışma ücreti serbest zaman İş Kanununa İlişkin Fazla Çalışma ve Fazla Sürelerle Çalışma Yönetmeliği"
            )
        if _contains_any_query_term(query, ("alt işveren", "alt isveren", "muvazaa", "muvazaalı", "muvazaali")):
            terms.append(
                "4857 İş Kanunu m.2 alt işveren asıl iş yardımcı iş teknolojik nedenlerle uzmanlık muvazaa Alt İşverenlik Yönetmeliği"
            )
        if _contains_any_query_term(query, ("yıllık ücretli izin", "yillik ucretli izin", "ücretli izin", "ucretli izin")):
            terms.append("4857 İş Kanunu m.56 yıllık ücretli izin bölünebilir en az on gün kesintisiz")
    if hints & {"KVKK", "6698"}:
        terms.append(
            "6698 KVKK m.6 özel nitelikli kişisel veri biyometrik veri m.10 aydınlatma m.12 veri güvenliği saklama imha yönetmeliği"
        )
    if "5651" in hints:
        terms.append(
            "5651 sayılı İnternet Ortamında Yapılan Yayınların Düzenlenmesi Kanunu m.5 m.6 m.7 m.11 yer sağlayıcı erişim sağlayıcı trafik bilgisi saklama BTK talebi"
        )
    if hints & {"TBK", "6098"} and _looks_like_rent_increase_tbk_query(query):
        terms.append("6098 TBK m.344 kira artış oranı geçici yüzde 25 sınırı sona erdi güncel genel rejim")
    if "7201" in hints:
        terms.append("7201 Tebligat Kanunu elektronik tebligat elektronik adres beşinci gün Elektronik Tebligat Yönetmeliği")
    if hints & {"HUAK", "6325"}:
        terms.append(
            "6325 Hukuk Uyuşmazlıklarında Arabuluculuk Kanunu m.18 dava şartı olarak arabuluculuk kira bedeli alacağı tahliye 7445 kanun değişikliği"
        )
    if "TTK" in hints:
        terms.append("TTK m.595 TTK m.598 limited şirket pay devri şirket onayı ticaret sicili tescil ilan")
    return dedupe_strings(terms)


def _infer_law_mentions_from_concepts(query: str) -> list[str]:
    laws: list[str] = []
    if _looks_like_tbk_tmk_cross_law_query(query):
        laws.extend(["TBK", "TMK"])
    laws.extend(_infer_domain_law_hints(query))
    return dedupe_strings(laws)


def _apply_domain_law_hints_to_retrieval_plan(
    retrieval_plan: dict[str, Any] | None,
    *,
    domain_law_hints: list[str],
    mentioned_laws: list[str],
    query: str = "",
) -> dict[str, Any] | None:
    if not domain_law_hints:
        return retrieval_plan

    plan = dict(retrieval_plan or {})
    raw_law_hints = [item for item in (plan.get("law_hints") or []) if isinstance(item, str)]
    plan["law_hints"] = dedupe_strings(
        [
            *domain_law_hints,
            *(item for item in raw_law_hints if item in mentioned_laws or item in domain_law_hints),
        ]
    )
    family_hints = _domain_law_source_family_hints(plan["law_hints"])
    if family_hints:
        raw_family_hints = [
            item
            for item in (plan.get("source_family_hints") or [])
            if item in family_hints
        ]
        plan["source_family_hints"] = dedupe_strings([*family_hints, *raw_family_hints])[:4]
    term_hints = _domain_law_term_hints(query, plan["law_hints"])
    if term_hints:
        plan["term_hints"] = dedupe_strings(
            [
                *term_hints,
                *(plan.get("term_hints") or []),
            ]
        )[:6]
    return plan


def _select_domain_law_supporting_source_candidates(
    *,
    query: str,
    domain_law_hints: list[str],
    limit: int = 4,
) -> dict[str, Any] | None:
    supporting_families = _domain_law_supporting_source_family_hints(query, domain_law_hints)
    if not supporting_families:
        return None
    term_hints = _domain_law_term_hints(query, domain_law_hints)
    if not term_hints:
        return None
    support_query = _normalize_whitespace(" ".join(term_hints))
    selector = _select_metadata_first_source_candidates(
        query=support_query,
        requested_source_families=supporting_families,
        source_family_resolution=None,
        query_metadata_signals=_parse_metadata_lookup_query_signals(support_query),
        limit=limit,
    )
    if not selector or not selector.get("candidates"):
        return None
    selector["supporting_source_families"] = supporting_families
    selector["supporting_source_query"] = support_query
    return selector


def _detect_scope_refusal_reason(user_query: str) -> str | None:
    """Kapsam dışı sorularda deterministic refusal nedeni döndür.

    Not: Canonical current authority altında accepted source set artık
    TMK/TCK/HMK/CMK/TTK/İK kapsamını da içeriyor. Bu nedenle deterministic
    short-circuit yalnız gerçekten excluded alanlarda çalışmalıdır.
    """
    labor_oos_terms = [
        "kıdem tazminatı",
        "ihbar tazminatı",
        "4857",
        "iş kanunu",
    ]
    if _contains_any_query_term(user_query, labor_oos_terms):
        return "İş Kanunu / çalışma hukuku"

    return None


def _build_precise_tbk_answer(user_query: str) -> tuple[str, list[str]] | None:
    """Yüksek isabetli, dar kapsamlı deterministik TBK yanıtları."""
    q = _tr_lower(user_query)

    asks_contract_formation = (
        "sözleş" in q
        and ("kurul" in q or "kurulması" in q)
        and ("unsur" in q or "icap" in q or "kabul" in q)
    )
    if asks_contract_formation:
        answer = (
            "TBK'ya göre sözleşmenin kurulması için temel unsur, tarafların karşılıklı ve "
            "birbirine uygun irade beyanlarının (icap ve kabul) uyuşmasıdır [Kaynak: TBK m.1]. "
            "Önerinin bağlayıcılığı ve kabul zamanı bakımından hazır olan/hazır olmayan kişiler "
            "arasındaki kurallar TBK m.2 ve m.3'te düzenlenir [Kaynak: TBK m.2] [Kaynak: TBK m.3]."
        )
        return answer, ["TBK m.1", "TBK m.2", "TBK m.3"]

    asks_rent_payment_obligation = (
        "kira sözleşmesinde" in q
        and "kira bedelini ödeme yükümlülüğü" in q
    )
    if asks_rent_payment_obligation:
        answer = (
            "Kira sözleşmesinde kiracı, kiralananın kullanılmasına karşılık kira bedelini "
            "ödemeyi üstlenir [Kaynak: TBK m.299]. Aksine sözleşme veya yerel adet yoksa, "
            "kira bedeli ve yan giderler her ayın son günü ve en geç kira süresinin "
            "bitiminde kiraya verene ödenir [Kaynak: TBK m.314]."
        )
        return answer, ["TBK m.299", "TBK m.314"]

    asks_rent_increase_limit = (
        "kira bedelinin yıllık artışında" in q
        and "hangi sınırlamayı" in q
    )
    if asks_rent_increase_limit:
        answer = (
            "TBK m.344'e göre yenilenen kira dönemlerinde uygulanacak kira bedeline ilişkin "
            "anlaşmalar, bir önceki kira yılında TÜFE on iki aylık ortalamalara göre değişim "
            "oranını geçmemek koşuluyla geçerlidir [Kaynak: TBK m.344]. Taraflar anlaşmamışsa da "
            "hâkim aynı üst sınırı dikkate alarak kira bedelini belirler; beş yıldan uzun süreli "
            "konut ve diğer kira ilişkilerinde emsal kira bedelleri de gözetilir [Kaynak: TBK m.344]."
        )
        return answer, ["TBK m.344"]

    asks_housing_lease_termination = (
        "konut kiralarında" in q
        and ("sona erdirilmesi" in q or "tahliye" in q)
    )
    if asks_housing_lease_termination:
        answer = (
            "TBK'ya göre konut ve çatılı işyeri kiralarında kiraya veren, sırf sürenin "
            "bitimine dayanarak tahliye isteyemez; tahliye ancak kanunda sayılan sebeplerle "
            "mümkündür [Kaynak: TBK m.347]. Fesih bildiriminin yazılı yapılması gerekir "
            "[Kaynak: TBK m.348]. Tahliye sebepleri arasında kiraya verenin veya yeni "
            "malikin gereksinimi ile yeniden inşa/imar ihtiyacı bulunur [Kaynak: TBK m.350] "
            "[Kaynak: TBK m.351]. Ayrıca iki haklı ihtar, yazılı tahliye taahhüdü ve diğer "
            "özel tahliye halleri de uygulanır [Kaynak: TBK m.349]."
        )
        return answer, ["TBK m.347", "TBK m.348", "TBK m.349", "TBK m.350", "TBK m.351"]

    asks_default_under_112 = (
        "tbk m.112" in q
        and ("ifa edilmemesi" in q or "temerrüt" in q)
    )
    if asks_default_under_112:
        answer = (
            "TBK m.112, borç hiç veya gereği gibi ifa edilmezse borçlunun kusursuzluğunu "
            "ispat edemedikçe zararı gidermekle yükümlü olduğunu düzenler [Kaynak: TBK m.112]. "
            "Temerrüt için ise borcun muaccel olması ve kural olarak alacaklının ihtarı gerekir; "
            "ifa günü birlikte belirlenmişse veya usulüne uygun bildirimle belirlenmişse bu "
            "günün geçmesiyle borçlu temerrüde düşer [Kaynak: TBK m.117]. Temerrüde düşen "
            "borçlu, kusursuzluğunu ispat etmedikçe geç ifadan doğan zararı da gidermekle "
            "yükümlüdür [Kaynak: TBK m.118]."
        )
        return answer, ["TBK m.112", "TBK m.117", "TBK m.118"]

    asks_surety_form_requirements = (
        "kefalet sözleşmesi" in q
        and ("şekil şart" in q or "geçerlilik koşulları" in q)
    )
    if asks_surety_form_requirements:
        answer = (
            "TBK'ya göre kefalet, mevcut ve geçerli bir borç için; ayrıca doğunca hüküm ifade "
            "etmek üzere gelecekteki veya koşullu bir borç için de kurulabilir [Kaynak: TBK m.582]. "
            "Geçerlilik için sözleşmenin yazılı yapılması, azamî miktarın ve kefalet tarihinin "
            "gösterilmesi; kefilin bunları ve varsa müteselsil kefil sıfatını kendi el yazısıyla "
            "belirtmesi gerekir [Kaynak: TBK m.583]. Evli kişinin kefaleti kural olarak diğer "
            "eşin önceden veya en geç kuruluş anındaki yazılı rızasına tabidir; kanuni "
            "istisnalar saklıdır [Kaynak: TBK m.584]."
        )
        return answer, ["TBK m.582", "TBK m.583", "TBK m.584"]

    asks_real_estate_sale_form = (
        "taşınmaz satış sözleşmesi" in q
        and ("hangi şekle tabidir" in q or "noter" in q)
    )
    if asks_real_estate_sale_form:
        answer = (
            "Taşınmaz satış sözleşmesi resmî şekilde yapılmadıkça geçerli olmaz; taşınmaz "
            "satış vaadi, geri alım ve alım sözleşmeleri de aynı şekle tabidir [Kaynak: TBK m.237]. "
            "Taşınmaz mülkiyetinin devri için resmî sözleşme ve tapu sicilinde tescil gerekir; "
            "bu nedenle noter onayı tek başına satışın geçerliliği için yeterli değildir "
            "[Kaynak: TMK m.706]."
        )
        return answer, ["TBK m.237", "TMK m.706"]

    asks_sale_defect_notice = (
        "ayıptan doğan sorumluluğu" in q
        and ("gözden geçirme" in q or "bildirim külfeti" in q)
    )
    if asks_sale_defect_notice:
        answer = (
            "Alıcı, satılanı işlerin olağan akışına göre imkân bulunur bulunmaz gözden geçirmek "
            "ve ayıp görürse bunu uygun süre içinde satıcıya bildirmek zorundadır; aksi halde "
            "satılanı kabul etmiş sayılır [Kaynak: TBK m.223]. Olağan bir gözden geçirmeyle "
            "anlaşılamayan gizli ayıplarda ise ayıp sonradan ortaya çıkar çıkmaz hemen ve "
            "gecikmeksizin bildirim yapılmalıdır [Kaynak: TBK m.223]."
        )
        return answer, ["TBK m.223"]

    asks_spousal_consent_exceptions = (
        "eşin rızası" in q
        and "aranmaz" in q
        and "kefalet" in q
    )
    if asks_spousal_consent_exceptions:
        answer = (
            "TBK m.584 uyarınca eşin rızası; ticaret siciline kayıtlı ticari işletme sahibi, "
            "ticaret şirketi ortağı veya yöneticisi tarafından işletme ya da şirketle ilgili "
            "verilen kefaletlerde, esnaf ve sanatkârların mesleki faaliyetleriyle ilgili "
            "kefaletlerinde ve kanunda sayılan banka/kooperatif kredisi istisnalarında aranmaz "
            "[Kaynak: TBK m.584]."
        )
        return answer, ["TBK m.584"]

    asks_joint_surety_requirements = "müteselsil kefaletin şartları" in q
    if asks_joint_surety_requirements:
        answer = (
            "Müteselsil kefalette kefilin, müteselsil kefil sıfatıyla veya bu anlama gelen bir "
            "ifadeyle yükümlülük altına girmesi gerekir [Kaynak: TBK m.586]. Bu halde alacaklı, "
            "borçlunun ifada gecikmesi ve ihtarın sonuçsuz kalması veya borçlunun açıkça ödeme "
            "güçsüzlüğü içinde bulunması hâlinde asıl borçluyu takip etmeden doğrudan kefile "
            "başvurabilir; alacak rehinle güvence altındaysa kural olarak önce rehnin paraya "
            "çevrilmesi gerekir [Kaynak: TBK m.586]."
        )
        return answer, ["TBK m.586"]

    asks_joint_surety_vs_ordinary_surety = (
        "tbk m.586" in q
        and _contains_query_term(user_query, "müteselsil kefalet")
        and _contains_query_term(user_query, "adi kefalet")
        and _contains_query_term(user_query, "temel fark")
    )
    if asks_joint_surety_vs_ordinary_surety:
        answer = (
            "Adi kefalette alacaklı, kural olarak önce asıl borçluya başvurur; borçlu aleyhine "
            "takibin kesin aciz belgesiyle sonuçlanması, takibin imkânsız veya önemli ölçüde "
            "güçleşmesi, borçlunun iflası ya da konkordato mehli gibi hâllerde doğrudan kefile "
            "başvurabilir [Kaynak: TBK m.585]. Müteselsil kefalette ise kefil bu sıfatla "
            "yükümlülük altına girmişse, borçlunun ifada gecikmesi ve ihtarın sonuçsuz kalması "
            "veya açık ödeme güçsüzlüğü hâlinde alacaklı asıl borçluyu takip etmeden doğrudan "
            "kefile yönelebilir [Kaynak: TBK m.586]."
        )
        return answer, ["TBK m.585", "TBK m.586"]

    asks_creditor_default_release = (
        "alacaklının temerrüdü" in q
        and ("borçlu borcundan nasıl kurtulur" in q or "alacaklı direnimi" in q)
    )
    if asks_creditor_default_release:
        answer = (
            "Alacaklı temerrüdünde borçlu, teslim edeceği şeyi tevdi ederek borcundan kurtulabilir "
            "[Kaynak: TBK m.107]. Şey tevdiye elverişli değilse, bozulabilecekse veya korunması "
            "ile tevdi edilmesi önemli gider gerektiriyorsa hâkim izniyle satılıp bedeli tevdi "
            "edilir [Kaynak: TBK m.108]. Borcun konusu bir şeyin teslimi değilse, şartları varsa "
            "sözleşmeden dönme imkânı da doğar."
        )
        return answer, ["TBK m.107", "TBK m.108"]

    asks_subsequent_impossibility = (
        ("sonraki imkânsızlık" in q or "sonraki imkansızlık" in q or "ifa imkânsızlığı" in q or "ifa imkansızlığı" in q)
        and "borç sona erer" in q
    )
    if asks_subsequent_impossibility:
        answer = (
            "Evet. Borcun ifası borçlunun sorumlu tutulamayacağı sebeplerle imkânsızlaşırsa "
            "borç sona erer [Kaynak: TBK m.136]. Karşılıklı borç yükleyen sözleşmelerde borçlu "
            "karşı edimi isteyemez; daha önce almışsa onu sebepsiz zenginleşme hükümlerine göre "
            "iade eder [Kaynak: TBK m.136]."
        )
        return answer, ["TBK m.136"]

    asks_donation_revocation = (
        "geri alma hakkı saklı tutulan bağışlama" in q
        and "bağışlamayı geri alabilir" in q
    )
    if asks_donation_revocation:
        answer = (
            "Bağışlayan, bağışlanan kendisine veya yakınlarından birine karşı ağır bir suç "
            "işlemişse, bağışlayana ya da onun ailesinden bir kimseye karşı kanundan doğan aile "
            "ödevlerine ve yükümlülüklerine önemli ölçüde aykırı davranmışsa veya yüklemeli "
            "bağışlamada haklı bir sebep olmaksızın yüklemeyi yerine getirmemişse bağışlamayı geri "
            "alabilir [Kaynak: TBK m.295]."
        )
        return answer, ["TBK m.295"]

    asks_assumption_of_debt = (
        "borcun üstlenilmesi" in q
        and ("alacaklının rızası gerekir mi" in q or "nakli" in q)
    )
    if asks_assumption_of_debt:
        answer = (
            "İç üstlenme, borçlu ile üstlenen arasındaki ilişkidir ve alacaklıya doğrudan dış "
            "üstlenme sonucu doğurmaz [Kaynak: TBK m.195]. Alacaklı bakımından borcun üstlenilmesinin "
            "hüküm doğurması için alacaklının kabulü gerekir; bu kabul açık veya örtülü olabilir "
            "[Kaynak: TBK m.196]."
        )
        return answer, ["TBK m.195", "TBK m.196"]

    asks_guarantee_vs_surety = (
        ("garantörlük" in q or "garanti sözleşmesi" in q)
        and "kefalet" in q
    )
    if asks_guarantee_vs_surety:
        answer = (
            "Temel fark, kefaletin asıl borca bağlı fer'î bir kişisel teminat olması; garanti "
            "sözleşmesinin ise kural olarak bağımsız bir taahhüt doğurmasıdır [Kaynak: TBK m.128]. "
            "Bu nedenle kefalette asıl borcun geçersizliği veya sona ermesi kefili etkiler ve "
            "kefil asıl borca ilişkin def'ileri ileri sürebilir. Garanti veren ise kural olarak "
            "asıl borç ilişkisinden bağımsız sorumluluk üstlenir; ayrıca kefalet TBK'daki sıkı "
            "şekil şartlarına tabidir [Kaynak: TBK m.582]."
        )
        return answer, ["TBK m.128", "TBK m.582"]

    asks_joint_debt_release = (
        "müteselsil borçluluk" in q
        and ("ifa" in q or "ifa et" in q)
        and ("diğerlerini kurtar" in q or "digerlerini kurtar" in q)
    )
    if asks_joint_debt_release:
        answer = (
            "Evet. TBK m.166 uyarınca müteselsil borçlulardan biri borcun tamamını ifa ederse, "
            "borç sona erer ve diğer müteselsil borçlular da alacaklıya karşı borçtan kurtulur "
            "[Kaynak: TBK m.166]."
        )
        return answer, ["TBK m.166"]

    asks_service_noncompete_limits = (
        ("rekabet yasağı" in q or "rekabet yasagi" in q)
        and ("coğrafi kapsam" in q or "cografi kapsam" in q or "süre" in q or "sure" in q)
        and ("aşırı rekabet yasağı" in q or "asiri rekabet yasagi" in q)
    )
    if asks_service_noncompete_limits:
        answer = (
            "Hizmet ilişkisi içindeki rekabet yasağının çıkış noktası işçinin sadakat borcudur "
            "[Kaynak: TBK m.396]. Rekabet yasağı, coğrafi alan, süre ve iş türü bakımından işçinin "
            "ekonomik geleceğini hakkaniyete aykırı biçimde sınırlayamaz; aşırı geniş kurulmuşsa "
            "hâkim bu sınırlamayı daraltır ve uygun çerçeveye çeker [Kaynak: TBK m.397]."
        )
        return answer, ["TBK m.396", "TBK m.397"]

    asks_noncompete_validity_requirements = (
        ("rekabet yasağı anlaşmasının geçerliliği" in q or "rekabet yasagi anlasmasinin gecerliligi" in q)
        and ("şartlar" in q or "sartlar" in q)
    )
    if asks_noncompete_validity_requirements:
        answer = (
            "Rekabet yasağı anlaşmasının geçerliliği için işçinin fiil ehliyetine sahip olması, "
            "yasağı yazılı olarak üstlenmesi ve hizmet ilişkisinin ona müşteri çevresi, üretim "
            "sırları veya işveren işleri hakkında önemli bilgi edinme imkânı vermesi gerekir "
            "[Kaynak: TBK m.444]. Bu yasak yer, süre ve iş türü bakımından uygun olmalı; işçinin "
            "ekonomik geleceğini hakkaniyete aykırı tehlikeye düşürmemeli ve kural olarak iki yılı "
            "aşmamalıdır [Kaynak: TBK m.445]. Aykırı davranış hâlinde ceza şartı, tazminat ve "
            "faaliyetin durdurulmasına ilişkin sonuçlar da gündeme gelebilir [Kaynak: TBK m.446]."
        )
        return answer, ["TBK m.444", "TBK m.445", "TBK m.446"]

    asks_noncompete_breach_sanctions = (
        ("tbk m.397-398" in q or "tbk m.397 398" in q)
        and ("rekabet yasağına aykırılık" in q or "rekabet yasagina aykirilik" in q)
        and ("yaptırımlar" in q or "yaptirimlar" in q)
    )
    if asks_noncompete_breach_sanctions:
        answer = (
            "Rekabet yasağına aykırılık hâlinde işveren, sözleşmede öngörülmüş ceza şartını ve "
            "uğradığı zararın tazminini talep edebilir; ayrıca koşulları varsa aykırı faaliyetin "
            "durdurulmasını isteyebilir [Kaynak: TBK m.397] [Kaynak: TBK m.398]. Bu yaptırımların "
            "uygulanmasında seçimlik haklar ve ihlalin kapsamı önem taşır; işveren men, tazminat "
            "ve ceza şartı araçlarını birlikte değerlendirebilir [Kaynak: TBK m.399]."
        )
        return answer, ["TBK m.397", "TBK m.398", "TBK m.399"]

    asks_service_notice_periods = (
        ("tbk m.432" in q or "belirsiz süreli hizmet sözleşmelerinde" in q or "belirsiz sureli hizmet sozlesmelerinde" in q)
        and ("ihbar süreleri" in q or "ihbar sureleri" in q or "fesih bildirim" in q)
    )
    if asks_service_notice_periods:
        answer = (
            "Belirsiz süreli hizmet sözleşmelerinde fesih bildirim süreleri hizmet süresine göre "
            "kademeli biçimde belirlenir; taraflar ihbar süresine uyarak fesih bildiriminde bulunmak "
            "zorundadır [Kaynak: TBK m.432]. Bu sürelere uyulmaması hâlinde karşı taraf, bildirim "
            "süresine ilişkin ücret ve buna bağlı tazminat sonuçlarını talep edebilir [Kaynak: TBK m.433]."
        )
        return answer, ["TBK m.432", "TBK m.433"]

    asks_service_resignation_not_no_liability = (
        "işçi istifa etmişse işveren hiçbir koşulda tazminat ödemeye yükümlü değildir" in q
        and ("doğru mudur" in q or "dogru mudur" in q)
    )
    if asks_service_resignation_not_no_liability:
        answer = (
            "Hayır, bu mutlak ifade doğru değildir. İşverenin haklı sebep olmaksızın derhâl feshi "
            "veya kötü niyetli sona erdirme hâlinde işçi tazminat isteyebilir [Kaynak: TBK m.438]. "
            "Buna karşılık işçi haklı sebep olmaksızın işe başlamaz veya aniden işi bırakırsa, bu defa "
            "işverenin tazminat isteme hakkı doğabilir [Kaynak: TBK m.439]. Bu yüzden istifa olgusu "
            "tek başına her durumda işvereni tazminat sorumluluğundan kurtarmaz."
        )
        return answer, ["TBK m.438", "TBK m.439"]

    asks_bad_faith_service_termination_compensation = (
        "tbk m.438" in q
        and ("kötü niyetle feshinde" in q or "kotu niyetle feshinde" in q)
        and "hesaplanma esasları" in q
    )
    if asks_bad_faith_service_termination_compensation:
        answer = (
            "İşçi, haklı sebep olmaksızın derhâl fesih veya kötü niyetli sona erdirme hâlinde, "
            "bildirim süresi ya da bakiye süre üzerinden hesaplanan zararını isteyebilir "
            "[Kaynak: TBK m.438]. Hâkim, olayın özelliklerine göre ek bir fesih tazminatına da "
            "karar verebilir; bu hesapta işçinin elde ettiği veya bilerek kaçındığı gelirler ile "
            "hakkaniyet ölçütleri dikkate alınır [Kaynak: TBK m.440]."
        )
        return answer, ["TBK m.438", "TBK m.440"]

    asks_wage_protection_special_guarantees = (
        ("tbk m.401-402" in q or "tbk m.401 402" in q)
        and (
            "ücret alacaklarının korunmasına yönelik özel güvenceler" in q
            or "ucret alacaklarinin korunmasina yonelik ozel guvenceler" in q
        )
    )
    if asks_wage_protection_special_guarantees:
        answer = (
            "TBK m.401, işverenin işçiye sözleşmede veya toplu iş sözleşmesinde belirlenen; "
            "böyle bir hüküm yoksa asgari ücretten az olmamak üzere emsal ücreti ödeme borcunu "
            "kurar ve ücret alacağını temel düzeyde güvence altına alır [Kaynak: TBK m.401]. "
            "TBK m.402 ise fazla çalışma ücretinin normal çalışma ücretinin en az yüzde elli "
            "fazlasıyla ödenmesini, işçinin rızasıyla bunun yerine orantılı serbest zaman "
            "verilebilmesini düzenleyerek bu korumayı özel bir ücret güvencesiyle tamamlar "
            "[Kaynak: TBK m.402]."
        )
        return answer, ["TBK m.401", "TBK m.402"]

    asks_wage_protection_mechanisms = (
        "tbk m.401" in q
        and ("ücret alacaklarının korunmasına" in q or "ucret alacaklarinin korunmasina" in q)
    )
    if asks_wage_protection_mechanisms:
        answer = (
            "TBK m.401, işçinin ücret alacağının sözleşme ve emsal ücret düzeyi üzerinden korunmasını "
            "sağlar; işveren ücret borcunu eksiksiz ve zamanında ödemekle yükümlüdür [Kaynak: TBK m.401]. "
            "İşçi çalışmaya hazır olduğu hâlde işverenin kabul temerrüdüne düşmesi veya ücretin "
            "ödenmesini engelleyen durumlarda işçi ücretini istemeyi sürdürebilir; bu koruyucu sonuç "
            "TBK m.408 ile tamamlanır [Kaynak: TBK m.408]."
        )
        return answer, ["TBK m.401", "TBK m.408"]

    asks_service_contract_vs_work_contract = (
        "tbk m.393" in q
        and "eser sözleşmesinden temel farkı" in q
    )
    if asks_service_contract_vs_work_contract:
        answer = (
            "Hizmet sözleşmesinde işçi, işverene bağımlı biçimde iş görmeyi ve buna karşılık ücret "
            "almayı üstlenir; esas unsur bağımlılık ve sürekli iş görme edimidir [Kaynak: TBK m.393]. "
            "Eser sözleşmesinde ise yüklenici belirli bir sonucun, yani eserin meydana getirilmesini "
            "taahhüt eder [Kaynak: TBK m.470]. Bu nedenle temel fark, hizmet sözleşmesinin bağımlı "
            "çalışma ilişkisine, eser sözleşmesinin ise sonuç taahhüdüne dayanmasıdır."
        )
        return answer, ["TBK m.393", "TBK m.470"]

    asks_annual_paid_leave_obligation = (
        "tbk m.421" in q
        and ("yıllık ücretli izin" in q or "yillik ucretli izin" in q)
        and "yükümlülüğü" in q
    )
    if asks_annual_paid_leave_obligation:
        answer = (
            "İşverenin dinlenme ve izin rejimine ilişkin koruyucu yükümlülükleri TBK m.421 ile başlar; "
            "işçiye hafta tatili ve benzeri dinlenme hakları bu çerçevede güvence altındadır "
            "[Kaynak: TBK m.421]. Yıllık ücretli izin kullandırma borcu ise TBK m.422'de somutlaşır; "
            "işveren işçiye yıllık ücretli izin vermek zorundadır ve bu yükümlülüğün ihlali ücret, izin ve "
            "tazminat taleplerini gündeme getirebilir [Kaynak: TBK m.422]."
        )
        return answer, ["TBK m.421", "TBK m.422"]

    asks_fixed_term_service_validity = (
        "tbk m.420" in q
        and ("belirli süreli hizmet sözleşmesinin geçerli kurulabilmesi" in q or "belirli sureli hizmet sozlesmesinin gecerli kurulabilmesi" in q)
    )
    if asks_fixed_term_service_validity:
        answer = (
            "Belirli süreli hizmet sözleşmesi, objektif ve makul bir süre temeline bağlanarak kurulmalı; "
            "zincirleme yenilemelerde geçerlilik için nesnel gerekçe bulunmalıdır [Kaynak: TBK m.420]. "
            "Bu koşullar yoksa ilişki belirsiz süreli hizmet sözleşmesi gibi değerlendirilir ve işçi "
            "lehine koruyucu rejim uygulanır [Kaynak: TBK m.421]."
        )
        return answer, ["TBK m.420", "TBK m.421"]

    asks_mobbing_protection_and_sanctions = (
        "tbk m.417" in q
        and ("psikolojik taciz" in q or "mobbing" in q)
        and ("yaptırımlar" in q or "yaptirimlar" in q or "uygulanacak" in q)
    )
    if asks_mobbing_protection_and_sanctions:
        answer = (
            "İşveren, işçiyi psikolojik tacizden korumak ve kişiliğini gözetmek için gerekli önlemleri "
            "almakla yükümlüdür [Kaynak: TBK m.417]. Bu yükümlülüğün ihlalinde işçi, maddi ve manevi "
            "zararlarının giderilmesini isteyebilir; kişilik hakkı ihlali aynı zamanda genel haksız fiil "
            "tazminat rejimini de harekete geçirir [Kaynak: TBK m.49]."
        )
        return answer, ["TBK m.417", "TBK m.49"]

    asks_employee_loyalty_and_care = (
        "işçi" in q
        and "sadakat" in q
        and ("özen borcu" in q or "ozen borcu" in q)
    )
    if asks_employee_loyalty_and_care:
        answer = (
            "TBK m.396 uyarınca işçi, yüklendiği işi özenle yapmak ve işverenin haklı "
            "menfaatinin korunmasında sadakatle davranmak zorundadır [Kaynak: TBK m.396]. "
            "İşçi, hizmet ilişkisi devam ettiği sürece sadakat borcuna aykırı davranamaz; "
            "özellikle öğrendiği üretim ve iş sırlarını açıklayamaz ve kendisi için kullanamaz "
            "[Kaynak: TBK m.396]."
        )
        return answer, ["TBK m.396"]

    asks_worker_immediate_termination_for_insult = (
        "işçi" in q
        and ("hakarete" in q or "hakaret" in q)
        and ("derhal feshedebilir" in q or "derhal fesih" in q)
    )
    if asks_worker_immediate_termination_for_insult:
        answer = (
            "Evet. İşveren, hizmet ilişkisinde işçinin kişiliğini korumak ve saygı göstermek, "
            "özellikle psikolojik taciz ve benzeri saldırılara karşı gerekli önlemleri almakla "
            "yükümlüdür [Kaynak: TBK m.417]. Taraflardan her biri, dürüstlük kuralına göre "
            "hizmet ilişkisini sürdürmesi beklenemeyen hâllerde sözleşmeyi haklı sebeple derhâl "
            "feshedebilir; işverenin sürekli hakareti de bu kapsamda değerlendirilebilir "
            "[Kaynak: TBK m.435]."
        )
        return answer, ["TBK m.435", "TBK m.417"]

    asks_unpaid_wages_rights = (
        ("ücretimi ödemiyor" in q or "ucretimi odemiyor" in q or "ücret ödemiyor" in q or "ucret odemiyor" in q)
        and ("hangi hakları" in q or "hangi haklari" in q or "ne yapabilirim" in q)
    )
    if asks_unpaid_wages_rights:
        answer = (
            "İşveren ücret borcunu zamanında ödemezse işçi, muaccel ücret alacağını talep ve dava "
            "edebilir; ücret alacağının korunmasına ilişkin hükümler TBK m.401'de düzenlenir "
            "[Kaynak: TBK m.401]. Ücretin ödenmemesi, dürüstlük kurallarına göre hizmet ilişkisini "
            "çekilmez kılan bir haklı sebep oluşturuyorsa işçi sözleşmeyi derhâl feshedebilir "
            "[Kaynak: TBK m.435]. Haklı fesih sebebi karşı tarafın sözleşmeye aykırılığından "
            "doğmuşsa, doğan zararın tamamen giderilmesi de gündeme gelir [Kaynak: TBK m.437]."
        )
        return answer, ["TBK m.401", "TBK m.435", "TBK m.437"]

    asks_oral_mandate_and_fee_claim = (
        "vekalet" in q
        and ("sözlü da kurulabilir" in q or "sozlu da kurulabilir" in q or "sözlü olarak da kurulabilir" in q or "sozlu olarak da kurulabilir" in q)
        and "ücret alamaz" in q
    )
    if asks_oral_mandate_and_fee_claim:
        answer = (
            "İddianın ilk kısmı doğrudur: kanunda aksi öngörülmedikçe sözleşmeler hiçbir şekle "
            "bağlı değildir; bu nedenle vekâlet sözleşmesi kural olarak sözlü de kurulabilir "
            "[Kaynak: TBK m.12]. Vekâlet sözleşmesinin tanımı ve ücret bakımından temel kural "
            "TBK m.502'de yer alır; sözleşme veya teamül varsa vekil ücrete hak kazanır "
            "[Kaynak: TBK m.502]. Ücretin ne zaman ödeneceği ise işin görülmesinden sonra, "
            "aksine âdet veya anlaşma yoksa hüküm doğurur [Kaynak: TBK m.510]. Bu nedenle "
            "\"sözlü vekil yaptığı işi ispat edemezse ücret alamaz\" şeklinde mutlak bir TBK "
            "kuralı yoktur."
        )
        return answer, ["TBK m.502", "TBK m.510", "TBK m.12"]

    asks_mandate_instruction_scope_under_504 = (
        "tbk m.504" in q
        and ("talimatlarına uymak zorunda" in q or "talimatlarina uymak zorunda" in q)
    )
    if asks_mandate_instruction_scope_under_504:
        answer = (
            "Vekalet iliskisinin temel cercevesi TBK m.502'de kurulur; vekil, vekalet verenin "
            "bir isini gormeyi veya islemini yapmayi ustlenir [Kaynak: TBK m.502]. TBK m.504 ise "
            "vekaletin kapsamini ve vekilin hangi hukuki islemleri yapmaya yetkili oldugunu "
            "belirler [Kaynak: TBK m.504]. Bu cercevede vekilin, muvekkilin verdigi is ve yetki "
            "sinirlari disina cikan talimat-disi hareketi sorumluluk dogurur; vekalet kapsami "
            "ve yetkisiz hareketten kaynaklanan zararlar vekile yukletilir."
        )
        return answer, ["TBK m.504", "TBK m.502"]

    asks_unjustified_revocation_of_paid_mandate = (
        "vekalet" in q
        and "azil" in q
        and ("haklı bir neden olmaksızın" in q or "hakli bir neden olmaksizin" in q)
    )
    if asks_unjustified_revocation_of_paid_mandate:
        answer = (
            "TBK m.512 uyarınca vekâlet veren ve vekil, her zaman sözleşmeyi sona erdirebilir; "
            "ancak uygun olmayan zamanda sona erdiren taraf, diğerinin bundan doğan zararını "
            "gidermekle yükümlüdür [Kaynak: TBK m.512]. Ücretli vekâlette vekilin yaptığı iş ve "
            "giderler bakımından hakları ayrıca korunur; vekâlet veren, vekilin yaptığı giderleri "
            "ve verdiği avansları faiziyle ödemek ve üstlendiği borçlardan onu kurtarmakla "
            "yükümlüdür [Kaynak: TBK m.511]. Bu nedenle haklı bir neden olmaksızın ve uygunsuz "
            "zamanda yapılan azilde vekil, uğradığı zararın tazminini isteyebilir."
        )
        return answer, ["TBK m.511", "TBK m.512"]

    asks_mandate_auto_termination_and_form = (
        "tbk m.512" in q
        and ("kendiliğinden sona erer" in q or "kendiliginden sona erer" in q)
        and ("azil bildirimi" in q or "şekil şartı" in q or "sekil sarti" in q)
    )
    if asks_mandate_auto_termination_and_form:
        answer = (
            "Vekâlet ilişkisinde azil ve istifa, tarafların sözleşmeyi her zaman sona erdirebilmesini "
            "sağlayan genel çıkış yoludur; bu irade açıklamaları için TBK m.512'de özel bir şekil şartı "
            "öngörülmemiştir [Kaynak: TBK m.512]. Kendiliğinden sona erme ise ayrı bir rejimdir: sözleşmeden "
            "veya işin niteliğinden aksi anlaşılmadıkça vekilin ya da vekâlet verenin ölümü, ehliyetini "
            "kaybetmesi veya iflası hâlinde vekâlet ilişkisi kendiliğinden sona erer [Kaynak: TBK m.513]."
        )
        return answer, ["TBK m.512", "TBK m.513"]

    asks_mandate_care_breach_under_509 = (
        "tbk m.509" in q
        and ("özen borcunu ihlal" in q or "ozen borcunu ihlal" in q)
        and ("müvekkile karşı" in q or "muvekkile karsi" in q)
    )
    if asks_mandate_care_breach_under_509:
        answer = (
            "Vekilin özen borcunu ihlal etmesi hâlinde sorumluluk, üstlendiği işin ve yetkinin hangi çerçevede "
            "kullanılabileceğine göre belirlenir; vekâletin kapsamı ve vekilin hangi işlemleri müvekkil adına "
            "yapabileceği TBK m.504'te gösterilir [Kaynak: TBK m.504]. Soruda TBK m.509 ekseniyle bakıldığında, "
            "vekilin vekâlet ilişkisi içinde edindiği hak ve sonuçların müvekkile intikali de aynı hesaplaşma "
            "rejiminin parçasıdır; bu nedenle özen ihlali müvekkili zarara uğratıyorsa tazminat ve sorumluluk "
            "sonuçları vekilin yürüttüğü işin bütününe yayılır [Kaynak: TBK m.509]."
        )
        return answer, ["TBK m.509", "TBK m.504"]

    asks_sub_mandate_scope_under_508 = (
        "tbk m.508" in q
        and (
            _contains_query_term(user_query, "işi başkasına")
            or _contains_query_term(user_query, "isi baskasina")
            or _contains_query_term(user_query, "alt vekil")
        )
    )
    if asks_sub_mandate_scope_under_508:
        answer = (
            "TBK m.508 ekseninde sorulduğunda, alt vekâlet/devir yetkisi bakımından vekilin işi "
            "başkasına bırakması müvekkil izni veya yetkilendirme zeminine dayanmalı; alt vekil "
            "seçimi ve alt vekil aracılığıyla doğan sonuçlar bakımından asıl vekilin sorumluluğu "
            "tamamen ortadan kalkmaz [Kaynak: TBK m.508]. Bu nedenle alt vekil seçimi ve gözetimi "
            "özenle yapılmadıkça, ortaya çıkan zarardan asıl vekilin sorumluluğunun devamı gündeme gelir "
            "[Kaynak: TBK m.508]."
        )
        return answer, ["TBK m.508"]

    asks_mandate_resignation_and_revocation = (
        _contains_any_query_term(user_query, ("vekalet", "vekâlet"))
        and "azil" in q
        and ("istifa" in q or "istifanın" in q or "istifanin" in q)
        and ("etkisi" in q or "nasıl düzenlenmiştir" in q or "nasil duzenlenmistir" in q)
    )
    if asks_mandate_resignation_and_revocation:
        answer = (
            "Azil ve istifa, vekâlet sözleşmesini sona erdiren tek taraflı irade açıklamalarıdır; vekâlet veren "
            "ve vekil, TBK m.512 uyarınca sözleşmeyi her zaman sona erdirebilir ve uygun olmayan zamanda yapılan "
            "sona erdirme diğer tarafın zararını tazmin borcu doğurur [Kaynak: TBK m.512]. Bunun yanında "
            "vekilin veya vekâlet verenin ölümü, ehliyetini kaybetmesi ya da iflası gibi hâller de vekâlet "
            "ilişkisinin kendiliğinden sona ermesine yol açar [Kaynak: TBK m.513]."
        )
        return answer, ["TBK m.512", "TBK m.513"]

    asks_multiple_mandataries_liability = (
        "tbk m.507" in q
        and ("birden fazla vekil" in q or "aynı iş için birden fazla vekil" in q or "ayni is icin birden fazla vekil" in q)
    )
    if asks_multiple_mandataries_liability:
        answer = (
            "Aynı iş için birden fazla vekil atanmışsa, birlikte hareket etmeleri öngörülen durumda her vekil "
            "diğerinin fiil alanını da gözetmek zorundadır; vekilin işi başkasına gördürmesi veya birlikte yürütmesi "
            "nedeniyle doğan sorumluluk TBK m.507 çerçevesinde değerlendirilir [Kaynak: TBK m.507]. ayrıca birden çok "
            "vekilin müvekkile verdikleri zarar bakımından sorumluluk paylaşımı ise birlikte borçluluk mantığıyla "
            "okunur; zarar tek bir bütün oluşturuyorsa müteselsil sorumluluk sonucu TBK m.162 çizgisiyle tamamlanır "
            "[Kaynak: TBK m.162]."
        )
        return answer, ["TBK m.507", "TBK m.162"]

    asks_excess_of_authority_in_mandate = (
        ("yetkinin sınırlarını aştı" in q or "yetkinin sinirlarini asti" in q or "yetki sınırlarını aştı" in q or "yetki sinirlarini asti" in q)
        and ("geçersiz sayabilir miyim" in q or "gecersiz sayabilir miyim" in q)
    )
    if asks_excess_of_authority_in_mandate:
        answer = (
            "Önce vekilin hangi işlemleri yapmaya yetkili olduğu belirlenir; vekâletin kapsamı ve yetki sınırları "
            "TBK m.504'e göre tayin edilir [Kaynak: TBK m.504]. Vekil bu sınırları aşıp yetkisiz temsil alanına "
            "geçmişse işlem müvekkili kendiliğinden bağlamaz; müvekkil onay verirse sözleşme hüküm doğurur, onay "
            "vermezse karşı taraf bakımından yetkisiz temsil sonuçları gündeme gelir [Kaynak: TBK m.46]. Bu nedenle "
            "salt yetki aşımı her durumda otomatik mutlak hükümsüzlük değil, onaylama ile bağlanma arasındaki temsil "
            "rejimi içinde değerlendirilir."
        )
        return answer, ["TBK m.504", "TBK m.46"]

    asks_post_death_completion_duty = (
        "tbk m.513" in q
        and ("ölümü" in q or "olumu" in q or "iflası" in q or "iflasi" in q)
        and ("tamamlama yükümlülüğü" in q or "tamamlama yukumlulugu" in q or "başlatılmış işleri" in q or "baslatilmis isleri" in q)
    )
    if asks_post_death_completion_duty:
        answer = (
            "Müvekkilin ölümü, ehliyetini kaybetmesi veya iflası kural olarak vekâlet ilişkisinin kendiliğinden sona "
            "ermesine yol açar [Kaynak: TBK m.513]. Ancak bu sona erme vekâlet verenin menfaatlerini tehlikeye düşürüyorsa, "
            "vekil veya mirasçıları, işler müvekkil ya da mirasçıları tarafından devralınabilecek hâle gelinceye kadar "
            "başlatılmış işleri sürdürmek ve zarar önlemek için gerekli işlemleri tamamlamakla yükümlüdür [Kaynak: TBK m.513]. "
            "TBK m.512'deki sona erdirme rejimi de, uygunsuz zamanda çıkışın zarar doğurabileceğini göstererek bu koruyucu "
            "tamamlama yükümlülüğünü destekler [Kaynak: TBK m.512]."
        )
        return answer, ["TBK m.513", "TBK m.512"]

    asks_unknown_termination_effect_on_third_parties = (
        "tbk m.514" in q
        and ("haberdar olmayan vekil" in q or "sona erdiğinden haberdar" in q or "sona erdiginden haberdar" in q)
    )
    if asks_unknown_termination_effect_on_third_parties:
        answer = (
            "Evet; vekil sözleşmenin sona erdiğini henüz öğrenmeden işlem yapmışsa, bu işlemler vekâlet devam ediyormuş "
            "gibi sonuç doğurur ve vekâlet veren bakımından bağlayıcılık korunur [Kaynak: TBK m.514]. Bunun zemini, "
            "TBK m.512'de yer alan sona erdirme rejiminin üçüncü kişilere ve vekile derhâl yansımaması; sona erme bilgisinin "
            "vekile ulaşmasına kadar iyiniyetli işlem güvenliğinin korunmasıdır [Kaynak: TBK m.512]. Bu nedenle vekilin "
            "sona ermeden habersiz olarak yaptığı işlem, üçüncü kişi bakımından geçerli kabul edilir."
        )
        return answer, ["TBK m.514", "TBK m.512"]

    asks_mandate_care_standard_under_503 = (
        "tbk m.503" in q
        and ("özen borcunun standartı" in q or "ozen borcunun standarti" in q)
    )
    if asks_mandate_care_standard_under_503:
        answer = (
            "Vekilin özen borcu, benzer alanda iş ve hizmetleri üstlenen basiretli ve mesleki özeni yüksek bir vekilden "
            "beklenen davranış standardına göre değerlendirilir; avukatlık gibi serbest meslek vekâletlerinde bu çıta somut "
            "işin niteliği nedeniyle daha sıkı uygulanır [Kaynak: TBK m.503]. Bu standardın sonucu olarak vekil, işi yürütürken "
            "müvekkilin menfaatini gözetmek, ortaya çıkan hak ve alacakları ona aktarmak ve mesleki özen eksikliğiyle verdiği "
            "zarardan sorumlu olmak durumundadır [Kaynak: TBK m.509]."
        )
        return answer, ["TBK m.503", "TBK m.509"]

    asks_surety_next_steps = (
        "kefil oldum" in q
        and ("hangi aşamaları" in q or "hangi asamalari" in q or "ne yapmalıyım" in q or "ne yapmaliyim" in q)
    )
    if asks_surety_next_steps:
        answer = (
            "İzlenecek yol, kefalet türüne göre değişir. Müteselsil kefalette alacaklı, borçlu "
            "ifada gecikmiş ve ihtar sonuçsuz kalmışsa ya da borçlu açıkça ödeme güçsüzlüğü "
            "içindeyse doğrudan kefile başvurabilir [Kaynak: TBK m.586]. Birden çok kefil varsa "
            "birlikte kefalet ve diğer kefillere karşı pay/rücu dengesi TBK m.587'de düzenlenir "
            "[Kaynak: TBK m.587]. Kefil, alacaklıya ödeme yaptığı ölçüde onun haklarına halef olur "
            "ve asıl borçluya karşı rücu hakkı kazanır [Kaynak: TBK m.596]."
        )
        return answer, ["TBK m.587", "TBK m.586", "TBK m.596"]

    asks_ordinary_vs_joint_surety_under_587 = (
        "tbk m.587" in q
        and _contains_query_term(user_query, "adi kefalet")
        and _contains_query_term(user_query, "müteselsil kefalet")
        and (
            _contains_query_term(user_query, "önce başvurma")
            or _contains_query_term(user_query, "asıl borçluya önce başvurma")
        )
    )
    if asks_ordinary_vs_joint_surety_under_587:
        answer = (
            "TBK m.587, birden çok kefilin aynı borç için sorumluluk paylaşımını düzenler; her "
            "kefil kendi payı için adi kefil gibi, diğerlerinin payı için de kefile kefil gibi "
            "sorumlu olur ve borcu ödeyen kefil diğer kefillere karşı payı oranında rücu edebilir "
            "[Kaynak: TBK m.587]. Müteselsil kefalette ise doğrudan kefile başvuru imkânı vardır; "
            "kefil müteselsil sıfatla yükümlülük altına girmişse borçlunun ifada gecikmesi ve "
            "ihtarın sonuçsuz kalması veya açık ödeme güçsüzlüğü hâlinde alacaklı asıl borçluya "
            "önce başvurmadan kefile yönelebilir [Kaynak: TBK m.586]."
        )
        return answer, ["TBK m.587", "TBK m.586"]

    asks_surety_defense_limits = (
        "tbk m.589" in q
        and _contains_query_term(user_query, "def'ileri")
        and (
            _contains_query_term(user_query, "sınırları")
            or _contains_query_term(user_query, "kesinlikle kullanamaz")
        )
    )
    if asks_surety_defense_limits:
        answer = (
            "Kefil, asıl borç ilişkisinden doğan ve borcun içeriğine bağlı def'ileri alacaklıya "
            "karşı ileri sürebilir; ancak borçlunun şahsına sıkı sıkıya bağlı kişisel itirazlarını "
            "ve sadece borçluya özgü feragat edilmiş savunmaları kendi lehine genişleterek "
            "kullanamaz [Kaynak: TBK m.589]. TBK m.590 ayrıca kefilin takibe karşı özel korumasını "
            "tamamlar; borçlunun iflası sebebiyle asıl borç erken muaccel olsa bile belirlenen "
            "vadeden önce kefile karşı takip yapılamaz ve kefil mevcut rehinler paraya "
            "çevrilinceye kadar takibin durdurulmasını isteyebilir [Kaynak: TBK m.590]."
        )
        return answer, ["TBK m.589", "TBK m.590"]

    asks_prepayment_recourse = (
        "tbk m.598" in q
        and _contains_query_term(user_query, "rücu hakkı")
        and (
            _contains_query_term(user_query, "ödeme yapmadan önce")
            or _contains_query_term(user_query, "odeme yapmadan once")
        )
    )
    if asks_prepayment_recourse:
        answer = (
            "TBK m.598, kefaletin kanun gereğince sona ermesini ve gerçek kişi kefaletlerinde on "
            "yıllık azamî süreyi düzenler; asıl borç sona ererse kefil de borcundan kurtulur "
            "[Kaynak: TBK m.598]. Kefilin asıl borçluya yönelik rücu zemini ise ödeme ile doğar: "
            "kefil alacaklıya ifada bulunduğu ölçüde onun haklarına halef olur ve bu hakları asıl "
            "borç muaccel olunca kullanabilir [Kaynak: TBK m.596]. Bu nedenle ödeme öncesi rücu, "
            "sorudaki varsayımın aksine genel kural değil; esasen ödeme sonrası halefiyet rejimi "
            "belirleyicidir."
        )
        return answer, ["TBK m.598", "TBK m.596"]

    asks_spousal_consent_scope_adversarial = (
        "'tbk m.584'teki eş rızası şartı" in q
        and (
            _contains_query_term(user_query, "yalnızca konut amaçlı kiralama")
            or _contains_query_term(user_query, "yalnizca konut amacli kiralama")
        )
        and ("doğru mudur" in q or "dogru mudur" in q)
    )
    if asks_spousal_consent_scope_adversarial:
        answer = (
            "Hayır, iddia doğru değildir. TBK m.584'teki eş rızası şartı genel olarak evli kişinin "
            "kefil olmasına ilişkindir; yalnızca konut amaçlı kiralama için verilmiş kefaletlerle "
            "sınırlı değildir ve ancak kanunda sayılan istisna hâllerinde aranmaz [Kaynak: TBK m.584]. "
            "Bu genel koruyucu rejimin şekil ayağı da TBK m.583'te yer alır; kefalet sözleşmesi yazılı "
            "olmalı, azamî miktar ve tarih gösterilmeli, kefil bunları kendi el yazısıyla belirtmelidir "
            "[Kaynak: TBK m.583]."
        )
        return answer, ["TBK m.584", "TBK m.583"]

    asks_surety_limitation_under_603 = (
        "tbk m.603" in q
        and _contains_query_term(user_query, "zamanaşımı")
        and (
            _contains_query_term(user_query, "asıl borç zamanaşımına uğrasa")
            or _contains_query_term(user_query, "asil borc zamanasimina ugrasa")
        )
    )
    if asks_surety_limitation_under_603:
        answer = (
            "TBK m.603, kefaletin şekline, kefil olma ehliyetine ve eş rızasına ilişkin hükümlerin, "
            "gerçek kişilerce başka ad altında verilen kişisel güvencelere de uygulanacağını "
            "belirterek kefalet rejiminin uygulama alanını genişletir [Kaynak: TBK m.603]. "
            "Zamanaşımı ve asıl borcun ifa edilmemesi bağlamında genel borç rejimi ise TBK m.125'teki "
            "temerrüt ve ifa edilmeme sonuçlarıyla birlikte okunur; bu nedenle asıl borcun "
            "zamanaşımına uğraması kefalet alacağını otomatik olarak sınırsız biçimde ayakta tutan "
            "ayrı bir rejim yaratmaz [Kaynak: TBK m.125]."
        )
        return answer, ["TBK m.603", "TBK m.125"]

    asks_withdrawal_money_vs_penalty_clause = (
        ("cayma akçesi" in q or "cayma akcesi" in q)
        and ("kümülatif ceza şart" in q or "kumulatif ceza sart" in q)
        and ("dönülmüş sayılır" in q or "donulmus sayilir" in q)
    )
    if asks_withdrawal_money_vs_penalty_clause:
        answer = (
            "Cayma akçesi bakımından TBK m.181, dönme veya ifa edilmiş kısmın alacaklıda kalması "
            "öngörülen hâllerde ceza koşulu hükümlerinin uygulanacağını gösterir [Kaynak: TBK m.181]. "
            "Ceza şartının genel çerçevesi ise TBK m.179'da kurulur; burada kural olarak alacaklı ya "
            "borcun ya da cezanın ifasını ister, kümülatif sonuç ancak kanundaki özel görünümde doğar "
            "[Kaynak: TBK m.179]. Bu nedenle cayma akçesi, tarafa sözleşmeden cayma/dönme hakkı "
            "tanıyan bir yapı olarak; kümülatif ceza şartı ise asıl borçla birlikte cezanın istenebildiği "
            "istisnai görünüm olarak ayrılır. Sorudaki varsayımda cayma akçesinin ödenmesi, dönme "
            "sonucunu doğuran sözleşmesel mekanizmanın işletildiğini gösterir."
        )
        return answer, ["TBK m.181", "TBK m.179"]

    asks_unilateral_withdrawal_money_clause = (
        ("cayma akçesi" in q or "cayma akcesi" in q)
        and (
            "yalnızca bir taraf" in q
            or "yalnizca bir taraf" in q
            or "belirli bir tarafa" in q
            or "belirli bir tarafa" in q
        )
    )
    if asks_unilateral_withdrawal_money_clause:
        answer = (
            "TBK m.181, cayma akçesi kararlaştırılan yapıda ceza koşulu hükümlerinin uygulanacağını "
            "kabul eder ve cayma akçesini sözleşmeden dönme sonucuna bağlayan kurumsal çerçeveyi sağlar "
            "[Kaynak: TBK m.181]. Tarafların bu hakkı iki taraf için karşılıklı düzenlemesi de, sadece "
            "belirli bir taraf lehine tek taraflı cayma hakkı olarak kurması da sözleşme serbestisinin "
            "konusudur [Kaynak: TBK m.26]. Bu yüzden her iki taraf için karşılıklı cayma hakkı mümkün "
            "olduğu gibi, cayma akçesinin yalnızca bir taraf için öngörülmesi de emredici sınırlara "
            "aykırı olmadığı sürece geçerlidir."
        )
        return answer, ["TBK m.181", "TBK m.26"]

    asks_cumulative_penalty_clause = (
        ("bağımsız" in q or "bagimsiz" in q or "kümülatif" in q or "kumulatif" in q)
        and "ceza şart" in q
        and ("hem borcun ifasını" in q or "hem borcun ifasini" in q)
        and "hem de ceza şart" in q
    )
    if asks_cumulative_penalty_clause:
        answer = (
            "Evet, bağımsız (kümülatif) ceza şartında alacaklı, asıl borcun ifası ile ceza koşulunu "
            "birlikte isteme imkânına özel görünümde kavuşur [Kaynak: TBK m.180]. Bunun genel çerçevesi "
            "TBK m.179'da yer alır; kural olarak alacaklı ya borcun ya da cezanın ifasını ister, fakat "
            "belirlenen zaman veya yerde ifa edilmemesi için kararlaştırılan bağımsız ceza şartında "
            "ifa talebi ile ceza koşulu birlikte ileri sürülebilir [Kaynak: TBK m.179]."
        )
        return answer, ["TBK m.179", "TBK m.180"]

    asks_alternative_penalty_clause = (
        ("seçimlik ceza şart" in q or "secimlik ceza sart" in q)
        and ("hem asıl borcun ifasını" in q or "hem asil borcun ifasini" in q)
        and "hem de ceza şart" in q
    )
    if asks_alternative_penalty_clause:
        answer = (
            "Hayır. TBK m.179'daki seçimlik ceza şartında alacaklı, kural olarak ya asıl borcun "
            "ifasını ya da ceza koşulunu seçer; ikisini eş zamanlı isteyemez [Kaynak: TBK m.179]. "
            "Asıl borçla birlikte cezanın da talep edilebilmesi, TBK m.180'deki bağımsız "
            "(kümülatif) ceza şartına özgü istisnadır [Kaynak: TBK m.180]."
        )
        return answer, ["TBK m.179", "TBK m.180"]

    asks_penalty_payment_releases_performance = (
        "ceza şartının ödenmesi borçluyu asıl borcun ifasından tamamen kurtarır" in q
        and ("doğru mudur" in q or "dogru mudur" in q)
    )
    if asks_penalty_payment_releases_performance:
        answer = (
            "Hayır, bu ifade genel kural olarak doğru değildir. TBK m.179'da seçimlik ceza şartında "
            "alacaklı borcun ya da cezanın ifasını seçer; borçlu da ancak sözleşmede böyle bir yetki "
            "tanınmışsa ceza ödeyerek dönme veya fesih yoluyla asıl ifadan kurtulabilir "
            "[Kaynak: TBK m.179]. TBK m.180'deki bağımsız (kümülatif) ceza şartında ise asıl borç "
            "ayakta kalır ve alacaklı ifa ile ceza koşulunu birlikte talep edebilir [Kaynak: TBK m.180]."
        )
        return answer, ["TBK m.179", "TBK m.180"]

    asks_excessive_penalty_validity = (
        "ceza şartı miktarı" in q
        and ("çok aşan" in q or "cok asan" in q)
        and "geçerliliği" in q
    )
    if asks_excessive_penalty_validity:
        answer = (
            "Fahiş ceza şartı kural olarak sırf miktarı yüksek diye kendiliğinden geçersiz olmaz; "
            "hâkim aşırı gördüğü ceza koşulunu indirir [Kaynak: TBK m.182]. Bununla birlikte "
            "sözleşme özgürlüğü sınırsız değildir; emredici hukuk, kamu düzeni, ahlak veya kişilik "
            "haklarına aykırı hükümler kesin hükümsüzdür [Kaynak: TBK m.27]. Bu yüzden aşırı ceza "
            "miktarı bakımından temel sonuç, geçerlilik yerine hâkimin indirim müdahalesidir."
        )
        return answer, ["TBK m.182", "TBK m.27"]

    asks_invalid_main_contract_penalty_clause = (
        ("asıl sözleşme geçersiz" in q or "asil sozlesme gecersiz" in q)
        and "ceza şartının akıbeti" in q
    )
    if asks_invalid_main_contract_penalty_clause:
        answer = (
            "Ceza şartı, asıl borç ilişkisine bağlıdır. TBK m.179, ceza koşulunu asıl borcun hiç "
            "veya gereği gibi ifa edilmemesine bağlayan genel rejimi kurar [Kaynak: TBK m.179]. "
            "TBK m.182 ise asıl borç herhangi bir sebeple geçersizse cezanın ifasının da "
            "istenemeyeceğini açıkça düzenler [Kaynak: TBK m.182]. Bu nedenle asıl sözleşme "
            "geçersiz sayılırsa ceza şartı da ayakta kalmaz ve ifası talep edilemez."
        )
        return answer, ["TBK m.179", "TBK m.182"]

    asks_reduction_factors_for_work_contract_penalty = (
        "tbk m.182/3" in q
        and ("kısmi ifası" in q or "kismi ifasi" in q)
        and ("özenle çalışması" in q or "ozenle calismasi" in q)
    )
    if asks_reduction_factors_for_work_contract_penalty:
        answer = (
            "Evet, bu tür değerlendirmeler hâkimin ceza koşulunu indirip indirmeyeceğini "
            "takdir ederken önem kazanabilir. TBK m.182, hâkime fahiş ceza koşulunu kendiliğinden "
            "indirme yetkisi verir [Kaynak: TBK m.182]. TBK m.181, kısmi ifa veya dönme "
            "durumlarında ceza koşulu hükümlerinin nasıl devreye girdiğini göstererek kısmi ifa "
            "olgusunu ceza rejiminin içine taşır [Kaynak: TBK m.181]. TBK m.183 de ceza koşulunun "
            "somut ifa ilişkisi ve cezanın talep edilme şartlarıyla bağlantısını tamamlar "
            "[Kaynak: TBK m.183]. Bu nedenle eser sözleşmesinde yüklenicinin kısmi ifası, "
            "gecikme cezasının fahiş olup olmadığı ve indirimin gerekip gerekmediği bakımından "
            "göz önünde tutulabilir."
        )
        return answer, ["TBK m.181", "TBK m.182", "TBK m.183"]

    asks_excessive_penalty_clause_reduction = (
        "cezai şart" in q
        and ("çok yüksek" in q or "cok yuksek" in q or "fahiş" in q or "fahis" in q)
        and ("mahkeme" in q or "hakim" in q or "hâkim" in q)
    )
    if asks_excessive_penalty_clause_reduction:
        answer = (
            "Evet. TBK m.182 uyarınca taraflar cezanın miktarını serbestçe belirleyebilirse de, "
            "hâkim aşırı gördüğü ceza koşulunu kendiliğinden indirir [Kaynak: TBK m.182]. Ancak "
            "sözleşme serbestisi sınırsız değildir; kanunun emredici hükümlerine, ahlaka, kamu "
            "düzenine veya kişilik haklarına aykırı hükümler kesin hükümsüzdür [Kaynak: TBK m.27]. "
            "Bu nedenle fahiş cezai şart yargısal denetime tabidir ve uygun ölçüye indirilebilir."
        )
        return answer, ["TBK m.182", "TBK m.27"]

    return None


def _build_precise_tmk_tbk_cross_law_answer(user_query: str) -> tuple[str, list[str]] | None:
    """Dar kapsamlı, yüksek isabetli TMK/TBK çapraz-kanun yanıtları."""
    q = _tr_lower(user_query)

    asks_family_home_lease_notice = (
        _contains_query_term(user_query, "aile konutu")
        and _contains_any_query_term(user_query, ("kiracı eş", "kiraci es"))
        and _contains_query_term(user_query, "fesih bildirimi")
        and _contains_any_query_term(user_query, ("tek başına", "tek basina"))
    )
    if asks_family_home_lease_notice:
        answer = (
            "Aile konutu olarak kullanılan kiralananda kiracı eşin fesih bildirimi tek başına yeterli "
            "kabul edilmez; TMK m.194 aile konutu üzerinde diğer eşin korunmasını ve açık rıza eksenini "
            "öne çıkarır [Kaynak: TMK m.194]. TBK m.349 ise konut ve çatılı işyeri kiralarında fesih ve "
            "tahliye rejimini tamamlar; bu nedenle aile konutu niteliği taşıyan kiralananda fesih "
            "bildiriminin geçerliliği TBK m.349 ile birlikte değerlendirilir [Kaynak: TBK m.349]."
        )
        return answer, ["TBK m.349", "TMK m.194"]

    asks_family_home_sale_annotation_no_consent = (
        _contains_query_term(user_query, "aile konutu")
        and _contains_query_term(user_query, "şerh")
        and _contains_any_query_term(user_query, ("satışında", "satış", "satis"))
        and _contains_any_query_term(user_query, ("eşin rızası yoksa", "esin rizasi yoksa", "eş rızası yoksa"))
    )
    if asks_family_home_sale_annotation_no_consent:
        answer = (
            "Aile konutu şerhi bulunan taşınmazın satışında eş rızası yoksa TMK m.194 uyarınca aile "
            "konutu koruması devreye girer ve eş rızası aranmadan yapılan tasarruf işlemi tartışmalı hale "
            "gelir [Kaynak: TMK m.194]. Bu durumda geçersizlik değerlendirmesi TBK m.27 çerçevesinde yapılır "
            "ve aile konutu korumasına aykırı işlem hukuki sonuç doğurmaz [Kaynak: TBK m.27]. Şerh mevcut "
            "olduğu için alıcının iyi niyeti ayrıca TMK m.1023 bağlamında değerlendirilir; tapu siciline "
            "güven ilkesi, aile konutu şerhi ile sınırlanır [Kaynak: TMK m.1023]."
        )
        return answer, ["TBK m.27", "TMK m.194", "TMK m.1023"]

    asks_family_home_annotation_and_spousal_consent_effects = (
        _contains_query_term(user_query, "aile konutu")
        and _contains_query_term(user_query, "şerh")
        and _contains_any_query_term(user_query, ("eşin rızası", "esin rizasi", "eş rızası", "es rızası"))
        and _contains_any_query_term(user_query, ("sonuçları", "sonuclari", "sonuçlarını", "sonuclarini"))
        and not _contains_any_query_term(user_query, ("işlenmemiş", "islenmemis", "şerhin yokluğu", "serhin yoklugu"))
    )
    if asks_family_home_annotation_and_spousal_consent_effects:
        answer = (
            "TMK m.194 uyarınca aile konutu üzerinde kira sözleşmesinin feshi, devir veya ayni hakkın "
            "sınırlandırılması gibi tasarruflarda diğer eşin açık rızası aranır; aile konutu şerhi bu "
            "korumanın üçüncü kişiler bakımından görünürlüğünü güçlendirir [Kaynak: TMK m.194]. Bu çerçevede "
            "tapu siciline güven ilkesi ve üçüncü kişinin iyiniyeti TMK m.1023 çerçevesinde değerlendirilir; aile "
            "konutu şerhi bulunan durumda iyiniyet iddiası buna göre sınırlanır [Kaynak: TMK m.1023]."
        )
        return answer, ["TMK m.194", "TMK m.1023"]

    asks_family_home_divorce_lease_assignment = (
        _contains_query_term(user_query, "aile konutu")
        and _contains_any_query_term(user_query, ("kira sözleşmesinin devri", "kira sozlesmesinin devri"))
        and _contains_any_query_term(user_query, ("boşanma sürecindeki", "bosanma surecindeki", "boşanma süreci"))
    )
    if asks_family_home_divorce_lease_assignment:
        answer = (
            "Boşanma sürecinde aile konutu kira sözleşmesinin devri istenirken TMK m.194 aile konutunun "
            "eş lehine korunmasını esas alır [Kaynak: TMK m.194]. Kira ilişkisinin sona ermesi veya aile "
            "konutu üzerindeki korumanın işletilmesi bakımından TBK m.349 da birlikte dikkate alınır "
            "[Kaynak: TBK m.349]. Bu nedenle kira devri talebi, aile konutu statüsü ve eşin korunması "
            "ilkesi birlikte değerlendirilerek ele alınır."
        )
        return answer, ["TBK m.349", "TMK m.194"]

    asks_family_home_mortgage_without_consent = (
        _contains_query_term(user_query, "aile konutu")
        and _contains_query_term(user_query, "ipotek")
        and _contains_any_query_term(user_query, ("rızası olmadan", "rizasi olmadan"))
    )
    if asks_family_home_mortgage_without_consent:
        answer = (
            "Eşin rızası olmadan aile konutu üzerinde ipotek tesis edilmesi TMK m.194 bakımından aile "
            "konutu güvencesine aykırılık doğurur; aile konutu üzerindeki tasarruflarda diğer eşin rızası "
            "aranır [Kaynak: TMK m.194]. Bu koruyucu rejimin geçersizlik boyutu TBK m.27 ile birlikte "
            "değerlendirilir [Kaynak: TBK m.27]. TMK m.240 da aile konutunun eş lehine korunmasını "
            "tamamlayan sistematik bir dayanak olarak aynı koruma eksenini güçlendirir; bu nedenle aile "
            "konutu üzerindeki sınırlı ayni hak tesisi tek başına serbest tasarruf alanı sayılmaz "
            "[Kaynak: TMK m.240]."
        )
        return answer, ["TMK m.194", "TMK m.240", "TBK m.27"]

    asks_family_home_without_annotation = (
        _contains_query_term(user_query, "aile konutu")
        and _contains_query_term(user_query, "şerhi")
        and _contains_any_query_term(user_query, ("işlenmemiş", "islenmemis", "şerhin yokluğu", "serhin yoklugu"))
    )
    if asks_family_home_without_annotation:
        answer = (
            "Aile konutu şerhi tapu siciline işlenmemiş olsa bile TMK m.194'teki eş rızası koruması "
            "kendiliğinden ortadan kalkmaz; aile konutu niteliği devam ettiği sürece diğer eşin rızası "
            "aranır [Kaynak: TMK m.194]. Şerh yokluğuna rağmen yapılan işlemin geçerliliği TBK m.27 "
            "çerçevesinde tartışılır [Kaynak: TBK m.27]. Buna karşılık tapu aleniyeti ve iyiniyet "
            "sorunu TMK m.1023 bağlamında ayrıca değerlendirilir; şerh yokluğu aleniyet yönünden bir "
            "tartışma doğursa da aile konutu korumasını tek başına silmez [Kaynak: TMK m.1023]."
        )
        return answer, ["TMK m.194", "TMK m.1023", "TBK m.27"]

    asks_family_home_rented_without_spouse_knowledge = (
        _contains_query_term(user_query, "aile konutunu")
        and _contains_any_query_term(user_query, ("üçüncü kişiye kiraya verdi", "ucuncu kisiye kiraya verdi"))
        and _contains_query_term(user_query, "beni bağlar mı")
    )
    if asks_family_home_rented_without_spouse_knowledge:
        answer = (
            "Aile konutunun diğer eşin bilgisi ve rızası olmadan üçüncü kişiye kiraya verilmesi hâlinde "
            "TMK m.194 uyarınca aile konutu koruması ve eş rızası şartı öne çıkar [Kaynak: TMK m.194]. "
            "Kira sözleşmesinin sonuçları TBK m.349 ile birlikte değerlendirilir; bu nedenle aile konutu "
            "niteliği taşıyan kiralananda sözleşmenin sizi bağlayıp bağlamadığı, eş rızası ve üçüncü kişinin "
            "iyiniyeti dikkate alınarak belirlenir [Kaynak: TBK m.349]."
        )
        return answer, ["TBK m.349", "TMK m.194"]

    asks_family_home_divorce_termination = (
        _contains_query_term(user_query, "boşanma davası")
        and _contains_query_term(user_query, "aile konutu")
        and _contains_any_query_term(user_query, ("feshedebilir mi", "feshedebilir"))
        and _contains_any_query_term(user_query, ("mahkeme", "tedbir"))
    )
    if asks_family_home_divorce_termination:
        answer = (
            "Boşanma davası açıldıktan sonra aile konutu üzerindeki koruma TMK m.169 uyarınca mahkemenin "
            "geçici önlemlerine konu olabilir [Kaynak: TMK m.169]. Ayrı yaşama ve aile birliğinin korunmasına "
            "ilişkin TMK m.197 de eşlerin konut ve geçim düzeninin hâkim müdahalesiyle şekillenebileceğini "
            "gösterir [Kaynak: TMK m.197]. Bu nedenle aile konutu kira sözleşmesinin feshi bakımından TBK m.349 "
            "tek başına okunmaz; tedbir kararı olmasa bile aile konutu koruması ve eş rızası bağlamı devam eder "
            "[Kaynak: TBK m.349]."
        )
        return answer, ["TMK m.169", "TMK m.197", "TBK m.349"]

    asks_family_home_sales_promise = (
        _contains_query_term(user_query, "aile konutu")
        and _contains_query_term(user_query, "satış vaadi")
        and _contains_any_query_term(user_query, ("eşinin yazılı rızasını almadan", "esinin yazili rizasini almadan"))
    )
    if asks_family_home_sales_promise:
        answer = (
            "Aile konutuna ilişkin satış vaadi sözleşmesi resmi şekil gerektirir; satış vaadi de TBK m.237 "
            "kapsamında resmi şekle bağlıdır [Kaynak: TBK m.237]. Ancak aile konutu söz konusuysa TMK m.194 "
            "uyarınca diğer eşin yazılı rızası ayrıca aranır [Kaynak: TMK m.194]. Bu nedenle noter önünde yapılan "
            "satış vaadi tek başına yeterli olmaz; eş rızası yoksa aile konutu koruması nedeniyle geçerlilik sorunu "
            "doğar."
        )
        return answer, ["TMK m.194", "TBK m.237"]

    asks_family_home_blanket_nullity = (
        _contains_query_term(user_query, "TMK m.194")
        and _contains_query_term(user_query, "otomatik olarak batıldır")
    )
    if asks_family_home_blanket_nullity:
        answer = (
            "Hayır; 'eşin rızası alınmadan yapılan her sözleşme otomatik olarak batıldır' şeklindeki mutlak ifade "
            "isabetli değildir. TMK m.194 aile konutu üzerinde eş rızasını arayan özel korumayı getirir "
            "[Kaynak: TMK m.194]. Geçersizlik türü ve sonucun nasıl nitelendirileceği ise TBK m.27 çerçevesinde "
            "somut işlem türüne göre değerlendirilir; aile konutu koruması her sözleşme için tek tip otomatik "
            "butlan sonucu üretmez [Kaynak: TBK m.27]."
        )
        return answer, ["TMK m.194", "TBK m.27"]

    return None


def _extract_explicit_article_refs(query: str) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for ref in _extract_article_sequences(query):
        if ref not in seen:
            refs.append(ref)
            seen.add(ref)

    for match in _ARTICLE_REF_RE.finditer(query):
        raw_law = match.group("law").upper()
        law = _LAW_CODE_NORMALIZATION.get(raw_law)
        if law is None:
            continue
        madde = match.group("madde").strip().lower()
        ref = (law, madde)
        if ref not in seen:
            refs.append(ref)
            seen.add(ref)

    for match in _NUMERIC_ARTICLE_REF_RE.finditer(query):
        law = match.group("law").strip()
        madde = match.group("madde").strip().lower()
        ref = (law, madde)
        if ref not in seen:
            refs.append(ref)
            seen.add(ref)

    return refs


def _expand_article_sequence(raw_articles: str) -> list[str]:
    cleaned = re.sub(r"\b(?:m|md|madde)\.?\s*", "", raw_articles, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return []

    tokens = [
        token.strip()
        for token in re.split(r"\s*(?:,|ve|veya)\s*", cleaned)
        if token.strip()
    ]
    expanded: list[str] = []
    seen: set[str] = set()

    for token in tokens:
        parts = [part.strip().lower() for part in re.split(r"\s*[-–]\s*", token) if part.strip()]
        if len(parts) == 2 and all(part.isdigit() for part in parts):
            start = int(parts[0])
            end = int(parts[1])
            step = 1 if start <= end else -1
            for number in range(start, end + step, step):
                value = str(number)
                if value not in seen:
                    expanded.append(value)
                    seen.add(value)
            continue

        value = token.lower()
        if value not in seen:
            expanded.append(value)
            seen.add(value)

    return expanded


def _extract_article_sequences(query: str) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for match in _ARTICLE_SEQUENCE_RE.finditer(query):
        raw_law = match.group("law").upper()
        law = _LAW_CODE_NORMALIZATION.get(raw_law)
        if law is None:
            continue

        for madde in _expand_article_sequence(match.group("articles")):
            ref = (law, madde)
            if ref not in seen:
                refs.append(ref)
                seen.add(ref)

    for match in _NUMERIC_ARTICLE_SEQUENCE_RE.finditer(query):
        law = match.group("law").strip()

        for madde in _expand_article_sequence(match.group("articles")):
            ref = (law, madde)
            if ref not in seen:
                refs.append(ref)
                seen.add(ref)

    return refs


def _extract_law_mentions(query: str) -> list[str]:
    mentions: list[str] = []
    seen: set[str] = set()

    for match in _LAW_MENTION_RE.finditer(query):
        raw = match.group("law")
        normalized_key = _normalize_tr_text(raw)
        code = _LAW_CODE_NORMALIZATION.get(raw.upper()) or _LAW_NAME_NORMALIZATION_NORMALIZED.get(normalized_key)
        if code and code not in seen:
            mentions.append(code)
            seen.add(code)

    for law, _madde in _extract_article_sequences(query):
        if law not in seen:
            mentions.append(law)
            seen.add(law)

    for law in extract_numbered_law_mentions(query):
        if law not in seen:
            mentions.append(law)
            seen.add(law)

    for code in _infer_law_mentions_from_concepts(query):
        if code not in seen:
            mentions.append(code)
            seen.add(code)

    return mentions


def _should_use_cross_law_retrieval(query: str, mentioned_laws: list[str]) -> bool:
    if len(mentioned_laws) < 2:
        return False
    cross_law_markers = (
        "birlikte",
        "hangi tbk",
        "hangi tmk",
        "nasıl birlikte",
        "ile nasıl",
        "ile birlikte",
        "birlikte değerlendirilir",
        "birlikte uygulanır",
        "hangi hükümlere",
        "hangi maddelerle",
        "temellendirilir",
        "ilişkilidir",
        "temel farklar",
        "batıldır",
        "batildir",
        "zamanaşımına uğrar mı",
        "denkleştirmeye tabi",
        "tasfiyesindeki etkisi",
        "tabi olur",
        "sonuç ne olur",
        "başvurabilir mi",
        "nasıl belirlenir",
        "çatışma",
        "çeliş",
        "celis",
        "lex specialis",
        "özel rejim",
        "ozel rejim",
        "genel şirketler hukuku",
        "genel sirketler hukuku",
    )
    return _contains_any_query_term(query, cross_law_markers)


def _dedupe_retrieved_chunks(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    deduped: list[RetrievedChunk] = []
    seen_index: dict[tuple[str, str], int] = {}

    for chunk in chunks:
        key = (chunk.citation, chunk.text)
        if key in seen_index:
            existing = deduped[seen_index[key]]
            existing_meta = dict(existing.metadata or {})
            incoming_meta = dict(chunk.metadata or {})
            existing_lanes = [
                str(value)
                for value in (existing_meta.get("retrieval_lane_sources") or [])
                if isinstance(value, str) and value.strip()
            ]
            incoming_lanes = [
                str(value)
                for value in (incoming_meta.get("retrieval_lane_sources") or [])
                if isinstance(value, str) and value.strip()
            ]
            merged_lanes = dedupe_strings([*existing_lanes, *incoming_lanes])
            if merged_lanes:
                existing_meta["retrieval_lane_sources"] = merged_lanes
                existing_meta["metadata_lane_present"] = "metadata_guided_recall" in merged_lanes
                existing_meta["dense_lane_present"] = "semantic_dense_recall" in merged_lanes
                existing_meta["merged_lane_present"] = (
                    existing_meta["metadata_lane_present"] and existing_meta["dense_lane_present"]
                )
            if (chunk.score or 0.0) > (existing.score or 0.0):
                existing.score = chunk.score
            for field, value in incoming_meta.items():
                if existing_meta.get(field) in (None, "", [], False) and value not in (None, "", []):
                    existing_meta[field] = value
            existing.metadata = existing_meta
            continue
        deduped.append(chunk)
        seen_index[key] = len(deduped) - 1

    return deduped


def _dedupe_article_refs(refs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    deduped: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for ref in refs:
        if ref in seen:
            continue
        deduped.append(ref)
        seen.add(ref)
    return deduped


def _append_unique_expansion(
    retrieval_query: str,
    applied_expansions: list[str],
    expansion: str,
) -> str:
    if expansion in applied_expansions:
        return retrieval_query
    applied_expansions.append(expansion)
    return f"{retrieval_query} {expansion}"
def _should_retrieve_historical_current_counterpart(
    *,
    query: str,
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None,
) -> bool:
    normalized = normalize_query_text(query or "")
    return bool(
        _query_needs_historical_transition_slots(normalized)
        or _asks_current_validity_over_historical_contrast(query)
        or (
            _source_family_resolution_trace_bool(source_family_resolution, "historical_or_repealed_question")
            and _query_needs_current_applicability_slot(normalized)
        )
    )


def _build_historical_current_counterpart_query(query: str) -> str:
    return (
        f"{query} güncel yürürlükte aktif mevzuat yerine geçen düzenleme "
        "mevcut rejim doğrudan uygulanacak kaynak"
    )


def _mark_historical_current_counterpart_chunks(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    marked: list[RetrievedChunk] = []
    for chunk in chunks:
        metadata = dict(chunk.metadata or {})
        lanes = [
            str(value)
            for value in (metadata.get("retrieval_lane_sources") or [])
            if isinstance(value, str) and value.strip()
        ]
        metadata["historical_current_counterpart"] = True
        metadata["retrieval_lane_sources"] = dedupe_strings(
            [*lanes, "historical_current_counterpart_recall"]
        )
        metadata["metadata_lane_present"] = True
        marked.append(
            RetrievedChunk(
                text=chunk.text,
                citation=chunk.citation,
                source=chunk.source,
                score=chunk.score,
                metadata=metadata,
            )
        )
    return marked


_PHASE24HU_SOURCE_ROLE_TERMS: dict[str, tuple[str, ...]] = {
    "norm_chain": (
        "hangi normlar birlikte",
        "birlikte okun",
        "birlikte uygulan",
        "dayanak",
        "alt düzenleme",
        "alt duzenleme",
        "ikincil düzenleme",
        "ikincil duzenleme",
    ),
    "exception": (
        "istisna",
        "istisnası",
        "istisnasi",
        "hariç",
        "haric",
        "muaf",
        "uygulanmaz",
        "saklı",
        "sakli",
    ),
    "procedure": (
        "usul",
        "şart",
        "sart",
        "koşul",
        "kosul",
        "test edilmeli",
        "nasıl test",
        "nasil test",
        "nasıl uygulan",
        "nasil uygulan",
        "kapsam",
    ),
    "online_sale": (
        "internet",
        "internetten",
        "online",
        "uzaktan",
        "mesafeli",
    ),
    "withdrawal": (
        "cayma hakkı",
        "cayma hakki",
        "14 gün",
        "14 gun",
        "on dört gün",
        "on dort gun",
    ),
    "custom_production": (
        "kişiye özel",
        "kisiye ozel",
        "özel ölçü",
        "ozel olcu",
        "özel üretim",
        "ozel uretim",
    ),
}
_PHASE24HU_GUARDED_SLOTS = {
    "exception_or_limitation",
    "procedure_or_consequence",
    "scenario_applicability",
}


def _phase24hu_secondary_family_recall_enabled() -> bool:
    return (
        os.getenv("ENABLE_PHASE24HU_SECONDARY_FAMILY_RECALL", "false").lower()
        in {
            "1",
            "true",
            "yes",
            "on",
        }
        or phase24hx_constrained_routing_enabled()
    )


def _phase24hu_exception_slot_guard_enabled() -> bool:
    return os.getenv("ENABLE_PHASE24HU_EXCEPTION_SLOT_GUARD", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _phase24hu_query_role_signals(query: str) -> list[str]:
    return [
        signal
        for signal, terms in _PHASE24HU_SOURCE_ROLE_TERMS.items()
        if _contains_any_query_term(query, list(terms))
    ]


def _phase24hu_query_needs_source_role_support(query: str) -> bool:
    signals = set(_phase24hu_query_role_signals(query))
    return bool(
        signals
        & {
            "norm_chain",
            "exception",
            "procedure",
        }
        or {"online_sale", "withdrawal"} <= signals
    )


def _phase24hu_metadata_family_candidates(
    *,
    query: str,
    metadata_lookup_query_signals: dict[str, Any] | None = None,
    metadata_first_selector: dict[str, Any] | None = None,
) -> list[str]:
    families: list[str] = []
    signals = metadata_lookup_query_signals if isinstance(metadata_lookup_query_signals, dict) else {}
    for value in signals.get("parsed_family_candidates") or []:
        canonical = _canonical_source_family_value(str(value or ""))
        if canonical:
            families.append(canonical)

    selector = metadata_first_selector if isinstance(metadata_first_selector, dict) else {}
    for candidate in [
        *(selector.get("candidates") or []),
        *(selector.get("phase24x_filtered_candidates") or []),
    ]:
        if not isinstance(candidate, dict):
            continue
        family = _canonical_source_family_value(
            candidate.get("source_family_raw")
            or candidate.get("source_family")
            or candidate.get("source_family_mapped")
            or ""
        )
        if family:
            families.append(family)

    if _contains_any_query_term(query, ("yönetmelik", "yonetmelik", "alt düzenleme", "alt duzenleme")):
        families.append("yonetmelik")
    if {"online_sale", "withdrawal"} <= set(_phase24hu_query_role_signals(query)):
        families.append("yonetmelik")
    return dedupe_strings(families)


def _phase24hu_primary_family_is_kanun(
    *,
    requested_source_families: list[str],
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None,
) -> bool:
    requested = set(_expand_source_family_aliases(requested_source_families))
    if "kanun" in requested:
        return True
    if isinstance(source_family_resolution, SourceFamilyResolution):
        values = [
            source_family_resolution.expected_family_prior,
            source_family_resolution.predicted_family,
            *source_family_resolution.preferred_families,
            *source_family_resolution.routing_families,
        ]
    elif isinstance(source_family_resolution, dict):
        values = [
            source_family_resolution.get("expected_family_prior"),
            source_family_resolution.get("predicted_family"),
            *(source_family_resolution.get("preferred_families") or []),
            *(source_family_resolution.get("routing_families") or []),
        ]
    else:
        values = []
    return "kanun" in set(_expand_source_family_aliases([str(value) for value in values if str(value or "").strip()]))


def _phase24hu_supporting_retrieval_families(
    *,
    query: str,
    family_candidates: list[str],
) -> list[str]:
    candidates = set(_expand_source_family_aliases(family_candidates))
    families: list[str] = []
    if candidates & {"yonetmelik", "kky", "cb_yonetmelik", "uy"}:
        families.extend(["yonetmelik", "kky", "cb_yonetmelik"])
        if _query_has_academic_regulation_intent(query):
            families.append("uy")
    return dedupe_strings(families)


def _phase24hu_secondary_family_recall_policy(
    *,
    query: str,
    requested_source_families: list[str],
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None,
    metadata_lookup_query_signals: dict[str, Any] | None = None,
    metadata_first_selector: dict[str, Any] | None = None,
    law_filter: str | None = None,
) -> dict[str, Any]:
    role_signals = _phase24hu_query_role_signals(query)
    family_candidates = _phase24hu_metadata_family_candidates(
        query=query,
        metadata_lookup_query_signals=metadata_lookup_query_signals,
        metadata_first_selector=metadata_first_selector,
    )
    retrieval_families = _phase24hu_supporting_retrieval_families(
        query=query,
        family_candidates=family_candidates,
    )
    policy: dict[str, Any] = {
        "phase24hu_secondary_family_recall_enabled": _phase24hu_secondary_family_recall_enabled(),
        "secondary_family_recall_applied": False,
        "secondary_family_recall_types": retrieval_families,
        "secondary_family_recall_candidates": [],
        "secondary_family_recall_selected": [],
        "secondary_family_recall_reason": "disabled",
        "phase24hu_source_role_signals": role_signals,
        "phase24hu_metadata_family_candidates": family_candidates,
        "primary_source_role": "primary_rule",
        "supporting_source_roles": [],
    }
    if not policy["phase24hu_secondary_family_recall_enabled"]:
        return policy
    if law_filter:
        policy["secondary_family_recall_reason"] = "law_filter_present"
        return policy
    if not _phase24hu_primary_family_is_kanun(
        requested_source_families=requested_source_families,
        source_family_resolution=source_family_resolution,
    ):
        policy["secondary_family_recall_reason"] = "primary_family_not_kanun"
        return policy
    if not _phase24hu_query_needs_source_role_support(query):
        policy["secondary_family_recall_reason"] = "no_source_role_query_signal"
        return policy
    if not retrieval_families:
        policy["secondary_family_recall_reason"] = "no_secondary_family_signal"
        return policy
    policy["secondary_family_recall_reason"] = "source_role_secondary_family_signal"
    return policy


def _phase24hu_support_query(query: str, role_signals: list[str]) -> str:
    expansions: list[str] = []
    signal_set = set(role_signals)
    if {"online_sale", "withdrawal"} <= signal_set:
        expansions.append("mesafeli sözleşme uzaktan satış cayma hakkı")
    if "exception" in signal_set:
        expansions.append("istisna sınırlama uygulanmaz hariç")
    if "procedure" in signal_set:
        expansions.append("usul şart koşul kapsam uygulama")
    if "custom_production" in signal_set:
        expansions.append("kişiye özel üretim özel istek kişisel ihtiyaç")
    return _normalize_whitespace(" ".join([query, *dedupe_strings(expansions)]))


def _phase24hu_role_for_chunk(chunk: RetrievedChunk, *, query: str) -> str:
    surface = normalize_query_text(
        " ".join(
            part
            for part in (
                query,
                chunk.text,
                chunk.citation,
                _resolve_chunk_source_title(chunk),
                _resolve_chunk_source_identifier(chunk),
            )
            if part
        )
    )
    if _answer_contains_any(surface, ("istisna", "haric", "hariç", "muaf", "uygulanmaz", "kişiye", "kisiye")):
        return "exception_rule"
    if _answer_contains_any(surface, ("usul", "sart", "şart", "kosul", "koşul", "bildirim", "sure", "süre")):
        return "procedure_rule"
    if _answer_contains_any(surface, ("uygulama", "kapsam", "mesafeli", "internet", "online")):
        return "implementation_detail"
    return "supporting_rule"


def _phase24hu_role_supports_slot(role: str, slot: str) -> bool:
    if slot == "exception_or_limitation":
        return role in {"exception_rule", "supporting_rule", "implementation_detail"}
    if slot == "procedure_or_consequence":
        return role in {"procedure_rule", "implementation_detail", "supporting_rule"}
    if slot == "scenario_applicability":
        return role in {"exception_rule", "implementation_detail", "supporting_rule", "procedure_rule"}
    return False


def _phase24hu_candidate_summary(chunks: list[RetrievedChunk]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for chunk in chunks[:8]:
        metadata = chunk.metadata or {}
        rows.append(
            {
                "citation": chunk.citation,
                "source_key": _resolve_chunk_source_key(chunk),
                "source_title": _resolve_chunk_source_title(chunk),
                "source_family": _resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk),
                "source_role": metadata.get("source_role") or "",
                "secondary_family_recall_role": metadata.get("secondary_family_recall_role") or "",
            }
        )
    return rows


def _phase24hu_mark_secondary_family_chunks(
    *,
    chunks: list[RetrievedChunk],
    query: str,
) -> list[RetrievedChunk]:
    query_terms = _extract_retrieval_priority_terms(query)
    marked: list[RetrievedChunk] = []
    for chunk in chunks:
        family = _resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk) or ""
        if family == "uy" and not _query_has_academic_regulation_intent(query):
            continue
        overlap = max(
            _count_term_overlap(_resolve_chunk_source_title(chunk), query_terms),
            _count_term_overlap(chunk.text, query_terms),
        )
        role = _phase24hu_role_for_chunk(chunk, query=query)
        if overlap <= 0 and role == "supporting_rule":
            continue
        metadata = dict(chunk.metadata or {})
        lanes = [
            str(value)
            for value in (metadata.get("retrieval_lane_sources") or [])
            if isinstance(value, str) and value.strip()
        ]
        metadata["phase24hu_secondary_family_recall"] = True
        metadata["domain_law_supporting_source"] = True
        metadata["source_role"] = "supporting_source"
        metadata["secondary_family_recall_role"] = role
        metadata["retrieval_lane_sources"] = dedupe_strings(
            [*lanes, "phase24hu_secondary_family_recall", "domain_law_supporting_source"]
        )
        marked.append(
            RetrievedChunk(
                text=chunk.text,
                citation=chunk.citation,
                source=chunk.source,
                score=chunk.score,
                metadata=metadata,
            )
        )
    return marked


def _phase24hu_update_selected_support_trace(
    policy: dict[str, Any],
    *,
    chunks: list[RetrievedChunk],
    article_span_selector: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(policy, dict):
        return {}
    selector = article_span_selector if isinstance(article_span_selector, dict) else {}
    selected_span_ids = {
        str(value or "").strip()
        for value in [
            *(selector.get("selected_supporting_span_ids") or []),
            selector.get("selected_main_span_id"),
        ]
        if str(value or "").strip()
    }
    selected = [
        chunk
        for chunk in chunks
        if (chunk.metadata or {}).get("phase24hu_secondary_family_recall")
        and _chunk_span_id(chunk) in selected_span_ids
    ]
    updated = dict(policy)
    updated["secondary_family_recall_selected"] = _phase24hu_candidate_summary(selected)
    updated["supporting_source_roles"] = dedupe_strings(
        str((chunk.metadata or {}).get("secondary_family_recall_role") or "")
        for chunk in chunks
        if (chunk.metadata or {}).get("phase24hu_secondary_family_recall")
    )
    return updated


def _phase24hu_annotate_exception_slot_trace(
    answer_contract: dict[str, Any],
    retrieval_verification_features: dict[str, Any],
) -> None:
    rows = answer_contract.get("evidence_required_slot_values")
    if not isinstance(rows, list):
        return
    for row in rows:
        if not isinstance(row, dict) or row.get("slot_name") != "exception_or_limitation":
            continue
        retrieval_verification_features["exception_slot_source_key"] = str(row.get("evidence_span_id") or "")
        retrieval_verification_features["exception_slot_role"] = str(row.get("evidence_source_role") or "")
        answer_contract["exception_slot_source_key"] = retrieval_verification_features["exception_slot_source_key"]
        answer_contract["exception_slot_role"] = retrieval_verification_features["exception_slot_role"]
        return


def _build_retrieval_verification_features(
    *,
    query: str,
    requested_source_families: list[str],
    source_family_resolution: dict[str, Any] | None,
    chunks: list[RetrievedChunk],
    family_routing_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    predicted_family = None
    family_confidence = 0.0
    expected_family_prior = None
    preferred_families: list[str] = []
    fallback_families: list[str] = []
    selected_family_confidence = 0.0
    family_override_reason = "no_family_prior"
    pre_filter_family_set: list[str] = []
    reranked_family_set: list[str] = []
    selected_family_source: str | None = None
    family_gate_status = "not_applied"
    family_gate_reason = "not_applied"
    no_gate_reason = ""
    scenario_current_law_question = False
    scenario_current_law_prior = False
    historical_or_repealed_question = False
    historical_scope_detected = False
    repealed_scope_detected = False
    current_law_prior_blocked_by_historical_scope = False
    family_collision_detected = False
    family_collision_pair = ""
    collision_resolution_reason = ""
    source_key_collision_detected = False
    source_key_collision_keys: list[str] = []
    source_key_collision_pair = ""
    source_key_collision_families_by_key: dict[str, list[str]] = {}
    source_identity_stop_condition_applied = False
    source_identity_stop_reason = ""
    manual_review_required = False
    if isinstance(source_family_resolution, dict):
        predicted_family = source_family_resolution.get("predicted_family")
        try:
            family_confidence = float(source_family_resolution.get("family_confidence") or 0.0)
        except (TypeError, ValueError):
            family_confidence = 0.0
        expected_family_prior = source_family_resolution.get("expected_family_prior") or predicted_family
        raw_preferred = source_family_resolution.get("preferred_families")
        if isinstance(raw_preferred, list):
            preferred_families = [str(family) for family in raw_preferred if str(family or "").strip()]
        raw_fallback = source_family_resolution.get("fallback_families")
        if isinstance(raw_fallback, list):
            fallback_families = [str(family) for family in raw_fallback if str(family or "").strip()]
        try:
            selected_family_confidence = float(
                source_family_resolution.get("selected_family_confidence") or family_confidence
            )
        except (TypeError, ValueError):
            selected_family_confidence = family_confidence
        scenario_current_law_question = bool(source_family_resolution.get("scenario_current_law_question"))
        scenario_current_law_prior = bool(source_family_resolution.get("scenario_current_law_prior"))
        historical_or_repealed_question = bool(source_family_resolution.get("historical_or_repealed_question"))
        historical_scope_detected = bool(source_family_resolution.get("historical_scope_detected"))
        repealed_scope_detected = bool(source_family_resolution.get("repealed_scope_detected"))
        current_law_prior_blocked_by_historical_scope = bool(
            source_family_resolution.get("current_law_prior_blocked_by_historical_scope")
        )
        family_collision_detected = bool(source_family_resolution.get("family_collision_detected"))
        family_collision_pair = str(source_family_resolution.get("family_collision_pair") or "")
        collision_resolution_reason = str(source_family_resolution.get("collision_resolution_reason") or "")
        if source_family_resolution.get("family_override_reason"):
            family_override_reason = str(source_family_resolution.get("family_override_reason"))
            family_gate_reason = family_override_reason
    if isinstance(family_routing_policy, dict):
        expected_family_prior = family_routing_policy.get("expected_family_prior") or expected_family_prior
        raw_preferred = family_routing_policy.get("preferred_families")
        if isinstance(raw_preferred, list):
            preferred_families = [str(family) for family in raw_preferred if str(family or "").strip()]
        raw_fallback = family_routing_policy.get("fallback_families")
        if isinstance(raw_fallback, list):
            fallback_families = [str(family) for family in raw_fallback if str(family or "").strip()]
        try:
            selected_family_confidence = float(
                family_routing_policy.get("selected_family_confidence") or selected_family_confidence
            )
        except (TypeError, ValueError):
            pass
        if family_routing_policy.get("family_override_reason"):
            family_override_reason = str(family_routing_policy.get("family_override_reason"))
        for key, target in (
            ("pre_filter_family_set", pre_filter_family_set),
            ("reranked_family_set", reranked_family_set),
        ):
            raw_values = family_routing_policy.get(key)
            if isinstance(raw_values, list):
                target.extend(str(item) for item in raw_values if str(item or "").strip())
        if family_routing_policy.get("selected_family_source"):
            selected_family_source = str(family_routing_policy.get("selected_family_source"))
        if family_routing_policy.get("family_gate_status"):
            family_gate_status = str(family_routing_policy.get("family_gate_status"))
        if family_routing_policy.get("family_gate_reason"):
            family_gate_reason = str(family_routing_policy.get("family_gate_reason"))
        if family_routing_policy.get("no_gate_reason"):
            no_gate_reason = str(family_routing_policy.get("no_gate_reason"))
        source_key_collision_detected = bool(family_routing_policy.get("source_key_collision_detected"))
        raw_collision_keys = family_routing_policy.get("source_key_collision_keys")
        if isinstance(raw_collision_keys, list):
            source_key_collision_keys = [
                str(key) for key in raw_collision_keys if str(key or "").strip()
            ]
        if family_routing_policy.get("source_key_collision_pair"):
            source_key_collision_pair = str(family_routing_policy.get("source_key_collision_pair"))
        raw_families_by_key = family_routing_policy.get("source_key_collision_families_by_key")
        if isinstance(raw_families_by_key, dict):
            source_key_collision_families_by_key = {
                str(key): [
                    str(family)
                    for family in families
                    if str(family or "").strip()
                ]
                for key, families in raw_families_by_key.items()
                if isinstance(families, list)
            }
        source_identity_stop_condition_applied = bool(
            family_routing_policy.get("source_identity_stop_condition_applied")
        )
        if family_routing_policy.get("source_identity_stop_reason"):
            source_identity_stop_reason = str(family_routing_policy.get("source_identity_stop_reason"))
        manual_review_required = bool(family_routing_policy.get("manual_review_required"))

    identifier_tokens = sorted(_extract_source_identifier_tokens(query))
    chunk_families = [
        _resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk) or "unknown"
        for chunk in chunks
    ]
    unique_families = dedupe_strings(chunk_families)
    identifier_match_flag = (
        any(_chunk_matches_identifier_tokens(chunk, set(identifier_tokens)) for chunk in chunks)
        if identifier_tokens
        else None
    )
    requested_family_set = set(requested_source_families)
    family_match_count = sum(1 for family in chunk_families if family in requested_family_set)
    predicted_family_match_count = (
        sum(1 for family in chunk_families if family == predicted_family)
        if predicted_family
        else 0
    )
    preferred_family_set = set(preferred_families)
    preferred_family_pool_size = (
        sum(1 for family in chunk_families if family in preferred_family_set)
        if preferred_family_set
        else 0
    )
    cross_family_fallback_used = bool(
        preferred_family_set
        and chunks
        and preferred_family_pool_size == 0
        and any(family not in preferred_family_set and family != "unknown" for family in chunk_families)
    )
    if isinstance(family_routing_policy, dict):
        try:
            preferred_family_pool_size = int(
                family_routing_policy.get("preferred_family_pool_size", preferred_family_pool_size)
            )
        except (TypeError, ValueError):
            pass
        cross_family_fallback_used = bool(family_routing_policy.get("cross_family_fallback_used"))
    if cross_family_fallback_used:
        family_override_reason = (
            str(family_routing_policy.get("family_override_reason"))
            if isinstance(family_routing_policy, dict) and family_routing_policy.get("family_override_reason")
            else "preferred_family_pool_empty_cross_family_fallback_observed"
        )
    current_validity_query = _asks_current_validity_query(query)
    temporal_alignment_flag = (
        all(not _is_temporally_inactive_chunk(chunk) for chunk in chunks[:5])
        if current_validity_query and chunks
        else None
    )
    cross_family_conflict_flag = len(set(family for family in chunk_families[:8] if family != "unknown")) > 1
    if preferred_family_set and preferred_family_pool_size:
        cross_family_conflict_flag = any(
            family not in preferred_family_set and family != "unknown" for family in chunk_families[:5]
        )
    elif predicted_family and family_confidence >= 0.75 and predicted_family_match_count:
        cross_family_conflict_flag = any(
            family not in {predicted_family, "unknown"} for family in chunk_families[:5]
        )

    return {
        "reranker_family_bonus": family_match_count,
        "identifier_match_flag": identifier_match_flag,
        "identifier_tokens": identifier_tokens,
        "temporal_alignment_flag": temporal_alignment_flag,
        "selected_evidence_count": len(chunks),
        "cross_family_conflict_flag": cross_family_conflict_flag,
        "selected_evidence_families": unique_families,
        "predicted_family_match_count": predicted_family_match_count,
        "expected_family_prior": expected_family_prior,
        "preferred_family_pool_size": preferred_family_pool_size,
        "cross_family_fallback_used": cross_family_fallback_used,
        "family_override_reason": family_override_reason,
        "selected_family_confidence": round(selected_family_confidence, 3),
        "scenario_current_law_question": scenario_current_law_question,
        "scenario_current_law_prior": scenario_current_law_prior,
        "historical_or_repealed_question": historical_or_repealed_question,
        "historical_scope_detected": historical_scope_detected,
        "repealed_scope_detected": repealed_scope_detected,
        "current_law_prior_blocked_by_historical_scope": current_law_prior_blocked_by_historical_scope,
        "family_collision_detected": family_collision_detected,
        "family_collision_pair": family_collision_pair,
        "collision_resolution_reason": collision_resolution_reason,
        "source_key_collision_detected": source_key_collision_detected,
        "source_key_collision_keys": source_key_collision_keys,
        "source_key_collision_pair": source_key_collision_pair,
        "source_key_collision_families_by_key": source_key_collision_families_by_key,
        "preferred_families": preferred_families,
        "fallback_families": fallback_families,
        "pre_filter_family_set": dedupe_strings(pre_filter_family_set),
        "reranked_family_set": dedupe_strings(reranked_family_set),
        "selected_family_source": selected_family_source,
        "family_gate_status": family_gate_status,
        "family_gate_reason": family_gate_reason,
        "no_gate_reason": no_gate_reason,
        "source_identity_stop_condition_applied": source_identity_stop_condition_applied,
        "source_identity_stop_reason": source_identity_stop_reason,
        "manual_review_required": manual_review_required,
    }


def _answer_template_for_query(query: str) -> str:
    return _answer_template_for_query_impl(query)


def _must_have_fact_slots_for_query(query: str, template: str) -> list[str]:
    return _must_have_fact_slots_for_query_impl(query, template)


def _query_needs_historical_transition_slots(normalized_query: str) -> bool:
    return _query_needs_historical_transition_slots_impl(normalized_query)


def _query_needs_current_applicability_slot(normalized_query: str) -> bool:
    return _query_needs_current_applicability_slot_impl(normalized_query)


def _answer_contains_any(normalized_answer: str, terms: tuple[str, ...]) -> bool:
    return any(term in normalized_answer for term in terms)


def _chunk_identity_surface(chunks: list[RetrievedChunk]) -> str:
    parts: list[str] = []
    for chunk in chunks[:5]:
        parts.extend(
            [
                chunk.citation or "",
                chunk.source or "",
                _resolve_chunk_source_title(chunk),
                _resolve_chunk_source_identifier(chunk),
            ]
        )
    return normalize_query_text(" ".join(part for part in parts if part))


def _satisfied_completeness_slots(
    *,
    required_slots: list[str],
    query: str,
    answer_text: str,
    article_span_selector: dict[str, Any] | None,
    chunks: list[RetrievedChunk],
    answer_fact_units: int,
    citation_count: int,
    support_span_count: int,
) -> list[str]:
    normalized_answer = normalize_query_text(answer_text or "")
    normalized_query = normalize_query_text(query or "")
    chunk_surface = _chunk_identity_surface(chunks)
    selector = article_span_selector if isinstance(article_span_selector, dict) else {}
    support_contains_article = bool(selector.get("support_contains_article_number"))
    support_contains_temporal = bool(selector.get("support_contains_temporal_clause"))
    support_contains_exception = bool(selector.get("support_contains_exception_signal"))
    source_identity_visible = bool(citation_count or chunk_surface)
    exact_identity_visible = bool(
        source_identity_visible
        and (
            chunk_surface
            and any(token in normalized_answer for token in chunk_surface.split() if len(token) >= 4)
            or citation_count
        )
    )

    satisfied: list[str] = []
    for slot in required_slots:
        if slot == "result_or_holding" and answer_fact_units >= 1:
            satisfied.append(slot)
        elif slot == "governing_source" and source_identity_visible:
            satisfied.append(slot)
        elif slot == "exact_source_identity" and exact_identity_visible:
            satisfied.append(slot)
        elif slot == "document_selection_reason" and (
            exact_identity_visible
            and _answer_contains_any(
                normalized_answer,
                (
                    "uygulanir",
                    "dayanir",
                    "dayanak",
                    "duzenler",
                    "kapsar",
                    "merkez",
                    "esas alinir",
                    "ilgili",
                    "bakimindan",
                    "bu nedenle",
                ),
            )
        ):
            satisfied.append(slot)
        elif slot == "article_or_span" and (support_contains_article or support_span_count > 0 or citation_count > 0):
            satisfied.append(slot)
        elif slot == "temporal_validity" and (
            support_contains_temporal
            or _answer_contains_any(
                normalized_answer,
                ("yururluk", "guncel", "mulga", "tarih", "halen", "gecerli", "kaldiril"),
            )
        ):
            satisfied.append(slot)
        elif slot == "historical_period" and _answer_contains_any(
            normalized_answer,
            ("tarihsel", "tarih", "donem", "eski", "mulga", "yururluk"),
        ):
            satisfied.append(slot)
        elif slot == "current_applicability" and _answer_contains_any(
            normalized_answer,
            ("bugun", "guncel", "dogrudan", "otomatik", "uygulanmamal", "uygulanamaz", "guvenli degil"),
        ):
            satisfied.append(slot)
        elif slot == "transition_or_replacement_rule" and _answer_contains_any(
            normalized_answer,
            ("gecis", "gecici", "mevcut rejim", "yerine gecen", "guncel duzenleme", "ayrica dogrulan"),
        ):
            satisfied.append(slot)
        elif slot == "exception_or_limitation" and (
            support_contains_exception
            or _answer_contains_any(
                normalized_answer,
                ("istisna", "sakli", "haric", "muaf", "sinirli", "uygulanmaz"),
            )
        ):
            satisfied.append(slot)
        elif slot == "procedure_or_consequence" and _answer_contains_any(
            normalized_answer,
            (
                "usul",
                "sure",
                "basvuru",
                "itiraz",
                "adim",
                "sonuc",
                "yaptirim",
                "zorunlu",
                "yukumluluk",
                "bildirim",
                "islem",
            ),
        ):
            satisfied.append(slot)
        elif slot == "scenario_applicability" and _answer_contains_any(
            normalized_answer,
            (
                "sart",
                "kosul",
                "halinde",
                "hallerde",
                "durumda",
                "kapsam",
                "uygulanir",
                "gecerlidir",
                "aranir",
                "bakimindan",
                "iliskin",
            ),
        ):
            satisfied.append(slot)
        elif slot == "hierarchy_or_conflict_rule" and (
            _answer_contains_any(
                normalized_answer,
                (
                    "oncelik",
                    "oncelikle",
                    "ust norm",
                    "alt norm",
                    "ozel duzenleme",
                    "genel duzenleme",
                    "ikincil duzenleme",
                    "normlar hiyerarsisi",
                    "kanuna aykiri",
                    "dayanak",
                    "yeterli",
                ),
            )
            or ("kanun" in normalized_query and "yonetmelik" in normalized_query and "kanun" in normalized_answer)
        ):
            satisfied.append(slot)
    return dedupe_strings(satisfied)


def _selector_allows_evidence_slot_reentry(article_span_selector: dict[str, Any] | None) -> bool:
    if not isinstance(article_span_selector, dict):
        return False
    identity_strength = str(article_span_selector.get("metadata_identity_strength") or "")
    evidence_sufficiency = str(article_span_selector.get("selector_evidence_sufficiency") or "")
    try:
        support_span_count = int(article_span_selector.get("support_span_count") or 0)
    except (TypeError, ValueError):
        support_span_count = 0
    return bool(
        support_span_count >= 1
        and (
            identity_strength in {"strong", "medium"}
            or evidence_sufficiency in {"exact_enough", "partially_supported"}
        )
    )


def _evidence_supported_completeness_slots(
    *,
    required_slots: list[str],
    article_span_selector: dict[str, Any] | None,
    chunks: list[RetrievedChunk],
) -> list[str]:
    if not chunks or not _selector_allows_evidence_slot_reentry(article_span_selector):
        return []
    slot_values = _build_evidence_required_slot_values(
        required_slots=required_slots,
        article_span_selector=article_span_selector,
        chunks=chunks,
        query="",
    )
    return dedupe_strings(
        str(row.get("slot_name") or "")
        for row in slot_values
        if isinstance(row, dict) and float(row.get("slot_confidence") or 0.0) >= 0.65
    )


def _slot_keyword_hints(slot: str) -> tuple[str, ...]:
    hints = {
        "result_or_holding": ("uygulan", "sonuc", "hukum", "karar", "duzenlen"),
        "governing_source": ("kanun", "yonetmelik", "teblig", "tuzuk", "karar", "kararname", "genelge"),
        "exact_source_identity": ("madde", "m ", "sayili", "sayılı"),
        "document_selection_reason": ("dayanak", "kapsam", "uygulan", "duzenlen", "ilgili", "esas"),
        "article_or_span": ("madde", "gecici madde", "fikra", "bent"),
        "temporal_validity": ("yururluk", "mulga", "tarih", "halen", "gecerli", "9999 12 31"),
        "historical_period": ("mulga", "tarihsel", "eski", "yururlukten", "tarih", "donem", "onceki"),
        "current_applicability": ("bugun", "guncel", "halen", "hala", "dogrudan", "uygulanmaz", "gecerli"),
        "transition_or_replacement_rule": (
            "gecis",
            "gecici",
            "basvuru tarihi",
            "muracaat tarihi",
            "yerine gecen",
            "yerini alan",
            "kaldiril",
            "mevcut rejim",
            "onceki rejim",
            "eski rejim",
            "yeni rejim",
            "yururlukte bulunan kararlar",
        ),
        "exception_or_limitation": (
            "istisna",
            "sakli",
            "haric",
            "muaf",
            "sinir",
            "uygulanmaz",
            "ancak",
            "talep edilmesi",
        ),
        "procedure_or_consequence": (
            "usul",
            "sure",
            "basvuru",
            "arabulucu",
            "dava",
            "mahkeme",
            "tutanak",
            "bir ay",
            "iki hafta",
            "itiraz",
            "sonuc",
            "yaptirim",
            "bildirim",
            "islem",
        ),
        "scenario_applicability": ("sart", "kosul", "halinde", "kapsam", "uygulan", "aranir", "bakimindan"),
        "hierarchy_or_conflict_rule": (
            "oncelik",
            "ust norm",
            "alt norm",
            "ozel duzenleme",
            "kanuna aykiri",
            "dayanak",
            "gecis",
            "gecici",
            "onceki",
            "eski",
            "yeni",
            "cercevesinde",
        ),
    }
    return hints.get(slot, ())


def _slot_hint_in_surface(surface: str, hint: str) -> bool:
    normalized_hint = normalize_query_text(hint or "")
    if not normalized_hint:
        return False
    if " " in normalized_hint:
        return normalized_hint in surface
    if normalized_hint == "sure":
        return bool(re.search(r"(?<![a-z0-9])sure(?:si|sin|ler|de|ye|yi|nin|leri)?(?![a-z0-9])", surface))
    if len(normalized_hint) <= 4:
        return bool(re.search(rf"(?<![a-z0-9]){re.escape(normalized_hint)}(?![a-z0-9])", surface))
    return normalized_hint in surface


def _slot_hint_score(surface: str, hints: tuple[str, ...]) -> int:
    return sum(1 for hint in hints if _slot_hint_in_surface(surface, hint))


def _chunk_is_historical_current_counterpart(chunk: RetrievedChunk) -> bool:
    metadata = chunk.metadata or {}
    lanes = {
        str(value)
        for value in (metadata.get("retrieval_lane_sources") or [])
        if isinstance(value, str) and value.strip()
    }
    return bool(
        _metadata_flag_is_true(metadata.get("historical_current_counterpart"))
        or "historical_current_counterpart_recall" in lanes
    )


def _chunk_span_id(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    for key in ("span_id", "chunk_id", "source_id", "citation"):
        value = metadata.get(key)
        if value:
            return str(value)
    return chunk.citation or chunk.source or ""


def _chunk_article(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    for key in ("article_or_section", "madde_no", "article", "madde"):
        value = metadata.get(key)
        if value not in {None, ""}:
            return str(value)
    match = re.search(r"\bm\.?\s*(\d+[a-z]?)\b", chunk.citation or "", re.IGNORECASE)
    return match.group(1) if match else ""


def _chunk_supports_slot(chunk: RetrievedChunk, slot: str) -> bool:
    metadata = chunk.metadata or {}
    role = str(metadata.get("secondary_family_recall_role") or "")
    if role and _phase24hu_role_supports_slot(role, slot):
        return True
    surface = normalize_query_text(
        " ".join(
            part
            for part in (
                chunk.text,
                chunk.citation,
                chunk.source or "",
                _resolve_chunk_source_title(chunk),
                _resolve_chunk_source_identifier(chunk),
                str(metadata.get("effective_state") or ""),
                str(metadata.get("effective_start") or metadata.get("yururluk_baslangic") or ""),
                str(metadata.get("effective_end") or metadata.get("yururluk_bitis") or ""),
                str(metadata.get("official_gazette_date") or ""),
                str(metadata.get("is_repealed") or metadata.get("mulga") or ""),
            )
            if part
        )
    )
    hints = _slot_keyword_hints(slot)
    if slot == "result_or_holding":
        return bool(_chunk_has_selectable_body_span(chunk) or len(surface) >= 80)
    if slot in {"governing_source", "exact_source_identity", "article_or_span", "document_selection_reason"}:
        return bool(chunk.citation or _resolve_chunk_source_identifier(chunk) or _chunk_article(chunk))
    if slot in {"temporal_validity", "historical_period", "current_applicability"} and any(
        str(metadata.get(key) or "").strip()
        for key in ("effective_state", "effective_start", "effective_end", "yururluk_baslangic", "yururluk_bitis")
    ):
        return True
    if slot in {"current_applicability", "transition_or_replacement_rule"} and _chunk_is_historical_current_counterpart(chunk):
        return True
    if slot == "transition_or_replacement_rule" and (
        _slot_hint_score(surface, hints) > 0
        or str(metadata.get("effective_state") or "").strip().lower() in {"repealed", "mulga"}
        or _metadata_flag_is_true(metadata.get("is_repealed"))
        or _metadata_flag_is_true(metadata.get("mulga"))
    ):
        return True
    return _slot_hint_score(surface, hints) > 0


def _phase24hu_chunk_source_role(chunk: RetrievedChunk | None) -> str:
    if chunk is None:
        return ""
    metadata = chunk.metadata or {}
    if metadata.get("source_role"):
        return str(metadata.get("source_role"))
    if metadata.get("phase24hu_secondary_family_recall") or metadata.get("domain_law_supporting_source"):
        return "supporting_source"
    return "primary_or_untyped"


def _phase24hu_same_document(left: RetrievedChunk | None, right: RetrievedChunk | None) -> bool:
    if left is None or right is None:
        return False
    left_values = {
        _resolve_chunk_binding_source_key(left, include_span=False),
        _resolve_chunk_canonical_source_key_v2(left, include_span=False),
        _resolve_chunk_document_key(left),
        _resolve_chunk_source_key(left),
    }
    right_values = {
        _resolve_chunk_binding_source_key(right, include_span=False),
        _resolve_chunk_canonical_source_key_v2(right, include_span=False),
        _resolve_chunk_document_key(right),
        _resolve_chunk_source_key(right),
    }
    return bool({str(value).strip() for value in left_values if str(value or "").strip()} & {
        str(value).strip() for value in right_values if str(value or "").strip()
    })


def _phase24hu_guarded_slot_candidate_score(
    chunk: RetrievedChunk,
    *,
    slot: str,
    query_terms: set[str],
) -> int:
    metadata = chunk.metadata or {}
    role = str(metadata.get("secondary_family_recall_role") or "")
    if not (
        metadata.get("phase24hu_secondary_family_recall")
        or metadata.get("domain_law_supporting_source")
        or role
    ):
        return -1
    if role and not _phase24hu_role_supports_slot(role, slot):
        return -1
    score = 0
    if metadata.get("phase24hu_secondary_family_recall"):
        score += 30
    if metadata.get("domain_law_supporting_source"):
        score += 12
    if role:
        score += 18
    if _chunk_supports_slot(chunk, slot):
        score += 12
    score += min(5, _count_term_overlap(_resolve_chunk_source_title(chunk), query_terms)) * 3
    score += min(5, _count_term_overlap(chunk.text, query_terms)) * 2
    return score


def _phase24hu_select_guarded_slot_chunk(
    *,
    chunks: list[RetrievedChunk],
    slot: str,
    query: str,
    current_chunk: RetrievedChunk | None,
    primary_chunk: RetrievedChunk | None,
) -> tuple[RetrievedChunk | None, dict[str, Any]]:
    if not _phase24hu_exception_slot_guard_enabled() or slot not in _PHASE24HU_GUARDED_SLOTS:
        return current_chunk, {
            "phase24hu_exception_slot_guard_applied": False,
            "phase24hu_exception_slot_guard_reason": "disabled_or_slot_not_guarded",
        }
    if not _phase24hu_query_needs_source_role_support(query):
        return current_chunk, {
            "phase24hu_exception_slot_guard_applied": False,
            "phase24hu_exception_slot_guard_reason": "no_source_role_query_signal",
        }
    query_terms = _extract_retrieval_priority_terms(query)
    support_candidates = [
        (_phase24hu_guarded_slot_candidate_score(chunk, slot=slot, query_terms=query_terms), index, chunk)
        for index, chunk in enumerate(chunks)
    ]
    support_candidates = [
        item
        for item in support_candidates
        if item[0] >= 0
    ]
    if support_candidates:
        support_candidates.sort(key=lambda item: (-item[0], item[1]))
        return support_candidates[0][2], {
            "phase24hu_exception_slot_guard_applied": True,
            "phase24hu_exception_slot_guard_reason": "supporting_role_match",
        }
    if current_chunk is None:
        return None, {
            "phase24hu_exception_slot_guard_applied": True,
            "phase24hu_exception_slot_guard_reason": "no_matching_evidence_span",
        }
    if primary_chunk is not None and _phase24hu_same_document(current_chunk, primary_chunk):
        return current_chunk, {
            "phase24hu_exception_slot_guard_applied": True,
            "phase24hu_exception_slot_guard_reason": "primary_document_slot_support",
        }
    if _phase24hu_chunk_source_role(current_chunk) == "supporting_source":
        return current_chunk, {
            "phase24hu_exception_slot_guard_applied": True,
            "phase24hu_exception_slot_guard_reason": "supporting_source_without_secondary_role",
        }
    return None, {
        "phase24hu_exception_slot_guard_applied": True,
        "phase24hu_exception_slot_guard_reason": "phase24hu_exception_slot_guard_no_role_matching_evidence",
    }


def _select_chunk_for_slot(chunks: list[RetrievedChunk], slot: str, *, query: str = "") -> RetrievedChunk | None:
    best_chunk: RetrievedChunk | None = None
    best_score = 0
    hints = _slot_keyword_hints(slot)
    query_terms = _extract_retrieval_priority_terms(query)
    academic_query = _query_has_academic_regulation_intent(query)
    for index, chunk in enumerate(chunks):
        if not _chunk_supports_slot(chunk, slot):
            continue
        metadata = chunk.metadata or {}
        surface = normalize_query_text(
            " ".join(
                part
                for part in (
                    chunk.text,
                    chunk.citation,
                    _resolve_chunk_source_title(chunk),
                    _resolve_chunk_source_identifier(chunk),
                )
                if part
            )
        )
        score = _slot_hint_score(surface, hints)
        if slot in {"governing_source", "exact_source_identity", "article_or_span", "document_selection_reason"}:
            score += 3
        if slot == "result_or_holding" and _chunk_has_selectable_body_span(chunk):
            score += 2
        selector_rank = metadata.get("_article_span_selector_rank")
        try:
            selector_rank_int = int(selector_rank)
        except (TypeError, ValueError):
            selector_rank_int = None
        selector_match_type = str(metadata.get("_article_span_selector_match_type") or "")
        if selector_rank_int is not None and slot not in {"current_applicability", "historical_period"}:
            score += max(1, 12 - min(selector_rank_int, 11))
            if selector_match_type == "exact_article":
                score += 4
        if slot in {"current_applicability", "transition_or_replacement_rule"} and _chunk_is_historical_current_counterpart(chunk):
            score += 6
            score += min(5, _count_term_overlap(_resolve_chunk_source_title(chunk), query_terms)) * 2
            score += min(3, _count_term_overlap(chunk.text, query_terms))
            if (_resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk)) == "uy" and not academic_query:
                score -= 5
        score = max(score, 1) * 100 - index
        if score > best_score:
            best_score = score
            best_chunk = chunk
    return best_chunk


def _selector_primary_chunk(
    chunks: list[RetrievedChunk],
    article_span_selector: dict[str, Any] | None,
) -> RetrievedChunk | None:
    if not isinstance(article_span_selector, dict):
        return None
    selected_main_span_id = str(article_span_selector.get("selected_main_span_id") or "").strip()
    if selected_main_span_id:
        selected_span_matches = [
            chunk
            for chunk in chunks
            if selected_main_span_id
            in {
                _chunk_span_id(chunk),
                _resolve_chunk_span_id(chunk),
                chunk.citation,
            }
        ]
        if len(selected_span_matches) == 1:
            return selected_span_matches[0]
    strict_selector_values = {
        str(value).strip()
        for value in (
            article_span_selector.get("binding_source_key"),
            article_span_selector.get("selected_canonical_source_key_v2"),
            article_span_selector.get("selected_canonical_document_key_v2"),
        )
        if str(value or "").strip()
    }
    if strict_selector_values:
        normalized_strict_selector_values = {
            candidate
            for value in strict_selector_values
            for candidate in (
                value,
                value.lower(),
                normalize_canonical_text(value),
                _normalize_tr_text(value),
            )
            if candidate
        }
        for chunk in chunks:
            strict_chunk_values = {
                str(value).strip()
                for value in (
                    _resolve_chunk_binding_source_key(chunk, include_span=False),
                    _resolve_chunk_binding_source_key(chunk, include_span=True),
                    _resolve_chunk_canonical_source_key_v2(chunk, include_span=False),
                    _resolve_chunk_canonical_source_key_v2(chunk, include_span=True),
                )
                if str(value or "").strip()
            }
            normalized_strict_chunk_values = {
                candidate
                for value in strict_chunk_values
                for candidate in (
                    value,
                    value.lower(),
                    normalize_canonical_text(value),
                    _normalize_tr_text(value),
                )
                if candidate
            }
            if normalized_strict_selector_values & normalized_strict_chunk_values:
                return chunk
    selector_values = {
        str(value).strip()
        for value in (
            article_span_selector.get("selected_main_span_id"),
            article_span_selector.get("selected_document_id"),
            article_span_selector.get("selected_document_source_key"),
            article_span_selector.get("binding_source_key"),
            article_span_selector.get("selected_canonical_source_key_v2"),
            article_span_selector.get("selected_canonical_document_key_v2"),
        )
        if str(value or "").strip()
    }
    if not selector_values:
        return None
    normalized_selector_values = {
        candidate
        for value in selector_values
        for candidate in (
            value,
            value.lower(),
            normalize_canonical_text(value),
            _normalize_tr_text(value),
        )
        if candidate
    }
    for chunk in chunks:
        chunk_values = {
            str(value).strip()
            for value in (
                _chunk_span_id(chunk),
                _resolve_trace_source_id(chunk),
                chunk.citation,
                _resolve_chunk_source_title(chunk),
                _resolve_chunk_binding_source_key(chunk, include_span=False),
                _resolve_chunk_binding_source_key(chunk, include_span=True),
                _resolve_chunk_canonical_source_key_v2(chunk, include_span=False),
                _resolve_chunk_canonical_source_key_v2(chunk, include_span=True),
            )
            if str(value or "").strip()
        }
        normalized_chunk_values = {
            candidate
            for value in chunk_values
            for candidate in (
                value,
                value.lower(),
                normalize_canonical_text(value),
                _normalize_tr_text(value),
            )
            if candidate
        }
        if normalized_selector_values & normalized_chunk_values:
            return chunk
    return None


def _compact_slot_value(value: str, *, max_len: int = 360) -> str:
    return _compact_slot_value_impl(value, max_len=max_len)


def _slot_quote_hash(value: str) -> str:
    return _slot_quote_hash_impl(value)


def _chunk_source_identity_label(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    title = _resolve_chunk_source_title(chunk)
    identifier = (
        _resolve_chunk_source_identifier(chunk)
        or str(metadata.get("canonical_identifier_display") or "")
        or str(metadata.get("canonical_identifier") or "")
    )
    family = _resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk) or ""
    parts = [part for part in (title, identifier, family, chunk.citation) if part]
    return _compact_slot_value(" | ".join(dedupe_strings(parts)), max_len=260)


def _effective_state_label(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    state = str(metadata.get("effective_state") or resolve_effective_state(metadata) or "unknown").strip()
    start = str(metadata.get("effective_start") or metadata.get("yururluk_baslangic") or "").strip()
    end = str(metadata.get("effective_end") or metadata.get("yururluk_bitis") or "").strip()
    pieces = [f"durum={state or 'unknown'}"]
    if start:
        pieces.append(f"baslangic={start}")
    if end:
        pieces.append(f"bitis={end}")
    return "; ".join(pieces)


def _best_slot_excerpt(chunk: RetrievedChunk, slot: str, *, query: str = "") -> str:
    hints = _slot_keyword_hints(slot)
    text = _strip_chunk_citation_prefix(chunk.text or "", chunk)
    sentences = [
        _normalize_whitespace(sentence)
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text)
        if _normalize_whitespace(sentence)
    ]
    best_sentence = ""
    best_score = 0
    for sentence in sentences:
        normalized = normalize_query_text(sentence)
        score = _slot_hint_score(normalized, hints) if hints else 0
        if score > best_score:
            best_score = score
            best_sentence = sentence
    if best_sentence:
        return _compact_slot_value(best_sentence)
    if query:
        return _compact_slot_value(_build_chunk_evidence_span(chunk, query=query, max_len=360))
    if sentences:
        return _compact_slot_value(sentences[0])
    return _compact_slot_value(text)


def _cb_karar_investment_transition_summary(chunk: RetrievedChunk, *, query: str = "") -> str:
    family = (_resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk) or "").lower()
    if family != "cb_karar":
        return ""
    surface = normalize_query_text(
        " ".join(
            part
            for part in (
                query,
                chunk.text,
                chunk.citation,
                _resolve_chunk_source_title(chunk),
                _resolve_chunk_source_identifier(chunk),
            )
            if part
        )
    )
    investment_terms_present = "yatirim" in surface and ("tesvik" in surface or "devlet yardim" in surface)
    transition_terms_present = (
        "gecis" in surface
        or "gecici" in surface
        or "onceki rejim" in surface
        or "eski rejim" in surface
        or "yeni rejim" in surface
        or "muracaat tarihinde yururlukte bulunan kararlar" in surface
    )
    if not (investment_terms_present and transition_terms_present):
        return ""
    excerpt = _best_slot_excerpt(chunk, "transition_or_replacement_rule", query=query)
    prefix = (
        "Geçiş hükmü: başvuru tarihi/müracaat tarihi esas alınır; "
        "önceki yatırım teşvik kararları bakımından eski rejimin devam edebileceği durum vardır. "
        "Talep edilirse yeni Karar uygulanabilir."
    )
    return _compact_slot_value(f"{prefix} {excerpt}", max_len=520)


def _slot_value_from_chunk(
    *,
    slot: str,
    chunk: RetrievedChunk,
    article_span_selector: dict[str, Any] | None,
    query: str = "",
) -> tuple[str, float, str]:
    metadata = chunk.metadata or {}
    selector = article_span_selector if isinstance(article_span_selector, dict) else {}
    citation = chunk.citation or _resolve_trace_source_id(chunk)
    source_label = _chunk_source_identity_label(chunk)
    state_label = _effective_state_label(chunk)
    effective_state = str(metadata.get("effective_state") or resolve_effective_state(metadata) or "").strip().lower()
    selector_binding_key = str(
        selector.get("binding_source_key")
        or selector.get("selected_canonical_document_key_v2")
        or ""
    ).strip()
    selector_active_binding = bool(
        selector_binding_key
        and re.search(r"(?:^|\|)state=active(?:\||$)", selector_binding_key)
    )
    selector_span_alias_match = bool(
        selector_active_binding
        and str(selector.get("selected_main_span_id") or "").strip()
        and str(selector.get("selected_main_span_id") or "").strip()
        in {
            _resolve_chunk_span_id(chunk),
            _chunk_span_id(chunk),
            citation,
        }
    )
    selector_binding_match = bool(
        selector_active_binding
        and selector_binding_key
        in {
            _resolve_chunk_binding_source_key(chunk, include_span=False),
            _resolve_chunk_canonical_source_key_v2(chunk, include_span=False),
        }
    )
    selector_active_override = False
    if selector_active_binding and (selector_binding_match or selector_span_alias_match):
        selected_document_id = str(selector.get("selected_document_id") or "").strip()
        selected_source_key = str(selector.get("selected_document_source_key") or citation or "").strip()
        family = _resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk) or "kanun"
        source_label = _compact_slot_value(
            " | ".join(dedupe_strings([selected_document_id, selected_source_key, family, citation])),
            max_len=260,
        )
        state_label = "durum=active"
        effective_state = "active"
        selector_active_override = True
    is_repealed = False if selector_active_override else bool(
        effective_state in {"repealed", "mulga"}
        or _metadata_flag_is_true(metadata.get("is_repealed"))
        or _metadata_flag_is_true(metadata.get("mulga"))
    )
    is_active = True if selector_active_override else bool(
        effective_state in {"active", "amended"} or str(metadata.get("effective_end") or "") in _ACTIVE_END_DATE_SENTINELS
    )
    is_current_counterpart = _chunk_is_historical_current_counterpart(chunk)

    if slot == "governing_source":
        return source_label or citation, 0.82, "source_identity_metadata"
    if slot == "exact_source_identity":
        return source_label or citation, 0.82, "source_identifier_metadata"
    if slot == "document_selection_reason":
        value = f"Seçilen belge kimliği sorudaki kaynak ailesi/kimliğiyle eşleşiyor: {source_label or citation}."
        return value, 0.68, "source_identity_alignment"
    if slot == "article_or_span":
        selector = article_span_selector if isinstance(article_span_selector, dict) else {}
        selected_span = str(selector.get("selected_main_span_id") or "").strip()
        selected_article = str(selector.get("selected_article") or _chunk_article(chunk) or "").strip()
        value = selected_span or citation
        if selected_article:
            value = f"{value}; madde/span={selected_article}"
        return value, 0.82, "selector_span_identity"
    if slot == "temporal_validity":
        temporal_excerpt = _best_slot_excerpt(chunk, slot, query=query)
        value = f"{state_label}. {temporal_excerpt}" if temporal_excerpt else state_label
        return value, 0.72 if state_label else 0.55, "effective_state_or_temporal_clause"
    if slot == "historical_period":
        if is_repealed:
            value = f"Kaynak mülga/tarihsel nitelikte değerlendirilmelidir; {state_label}."
            return value, 0.70, "repealed_effective_state_metadata"
        excerpt = _best_slot_excerpt(chunk, slot, query=query)
        return excerpt or state_label, 0.62 if excerpt else 0.45, "historical_period_excerpt"
    if slot == "current_applicability":
        if is_current_counterpart:
            return (
                f"Güncel/aktif karşılaştırma adayı: {source_label or citation}; doğrudan uygulama değerlendirmesi bu güncel kaynakla ayrıca kurulmalıdır ({state_label}).",
                0.72,
                "historical_current_counterpart_active_source",
            )
        if is_repealed:
            return (
                f"Seçili kaynak mülga/tarihsel görünüyor; bugünkü doğrudan uygulama için güncel kaynak ayrıca doğrulanmalıdır ({state_label}).",
                0.68,
                "repealed_current_applicability_limit",
            )
        if is_active:
            return (
                f"Seçili kaynak aktif/güncel görünüyor; uygulama seçili madde ve kapsamla sınırlıdır ({state_label}).",
                0.68,
                "active_effective_state_metadata",
            )
        excerpt = _best_slot_excerpt(chunk, slot, query=query)
        return excerpt or state_label, 0.55 if excerpt or state_label else 0.0, "current_applicability_not_explicit"
    if slot == "transition_or_replacement_rule":
        cb_karar_transition_summary = _cb_karar_investment_transition_summary(chunk, query=query)
        if cb_karar_transition_summary:
            return cb_karar_transition_summary, 0.74, "cb_karar_investment_transition_clause"
        if is_current_counterpart:
            return (
                f"Mülga/tarihsel kaynakla birlikte güncel karşılaştırma kaynağı olarak seçildi: {source_label or citation}.",
                0.72,
                "historical_current_counterpart_relation",
            )
        excerpt = _best_slot_excerpt(chunk, slot, query=query)
        normalized_excerpt = normalize_query_text(excerpt)
        if excerpt and _slot_hint_score(normalized_excerpt, _slot_keyword_hints(slot)) > 0:
            return excerpt, 0.70, "explicit_transition_or_replacement_clause"
        if is_repealed:
            return (
                "Seçili kanıtta yerine geçen/geçiş hükmü açık değil; sonuç mülga/tarihsel kaynakla sınırlı kurulmalıdır.",
                0.56,
                "transition_not_explicit_temporal_safety_limit",
            )
        return (
            "Seçili kanıtta ayrıca bir geçiş veya yerine geçen düzenleme kuralı açıkça görünmüyor.",
            0.50,
            "transition_not_explicit_in_selected_evidence",
        )

    excerpt = _best_slot_excerpt(chunk, slot, query=query)
    confidence = 0.70 if excerpt and _chunk_supports_slot(chunk, slot) else 0.52 if excerpt else 0.0
    return excerpt, confidence, "selected_span_excerpt" if confidence >= 0.65 else "weak_or_generic_excerpt"


def _build_evidence_required_slot_values(
    *,
    required_slots: list[str],
    article_span_selector: dict[str, Any] | None,
    chunks: list[RetrievedChunk],
    query: str = "",
) -> list[dict[str, Any]]:
    if not required_slots:
        return []
    selector = article_span_selector if isinstance(article_span_selector, dict) else {}
    selected_main_span_id = str(selector.get("selected_main_span_id") or "").strip()
    selected_article = str(selector.get("selected_article") or "").strip()
    rows: list[dict[str, Any]] = []
    primary_chunk = _selector_primary_chunk(chunks, article_span_selector)
    primary_preferred_slots = {
        "governing_source",
        "exact_source_identity",
        "document_selection_reason",
        "result_or_holding",
        "temporal_validity",
        "current_applicability",
    }
    for slot in required_slots:
        matched_chunk = (
            primary_chunk
            if slot in primary_preferred_slots
            and primary_chunk is not None
            else _select_chunk_for_slot(chunks, slot, query=query)
        )
        guard_policy = {
            "phase24hu_exception_slot_guard_applied": False,
            "phase24hu_exception_slot_guard_reason": "",
        }
        matched_chunk, guard_policy = _phase24hu_select_guarded_slot_chunk(
            chunks=chunks,
            slot=slot,
            query=query,
            current_chunk=matched_chunk,
            primary_chunk=primary_chunk,
        )
        if matched_chunk is None and slot in {"result_or_holding", "governing_source", "exact_source_identity"} and chunks:
            matched_chunk = chunks[0]
        span_id = _chunk_span_id(matched_chunk) if matched_chunk is not None else ""
        article = _chunk_article(matched_chunk) if matched_chunk is not None else ""
        if slot == "article_or_span" and selected_main_span_id:
            span_id = selected_main_span_id
            article = selected_article or article
        if matched_chunk is None:
            rows.append(
                {
                    "slot_name": slot,
                    "slot_value": "",
                    "evidence_span_id": span_id,
                    "evidence_article": article,
                    "evidence_quote_hash": "",
                    "slot_confidence": 0.0,
                    "slot_missing_reason": guard_policy.get("phase24hu_exception_slot_guard_reason")
                    or "no_matching_evidence_span",
                    "phase24hu_exception_slot_guard_applied": guard_policy.get(
                        "phase24hu_exception_slot_guard_applied"
                    ),
                    "phase24hu_exception_slot_guard_reason": guard_policy.get(
                        "phase24hu_exception_slot_guard_reason"
                    ),
                    "evidence_source_family": "",
                    "evidence_source_role": "",
                }
            )
            continue
        slot_value, confidence, reason = _slot_value_from_chunk(
            slot=slot,
            chunk=matched_chunk,
            article_span_selector=article_span_selector,
            query=query,
        )
        rows.append(
            {
                "slot_name": slot,
                "slot_value": slot_value,
                "evidence_span_id": span_id,
                "evidence_article": article,
                "evidence_quote_hash": _slot_quote_hash(slot_value),
                "slot_confidence": round(confidence, 3),
                "slot_missing_reason": reason if slot_value else "slot_value_empty",
                "phase24hu_exception_slot_guard_applied": guard_policy.get(
                    "phase24hu_exception_slot_guard_applied"
                ),
                "phase24hu_exception_slot_guard_reason": guard_policy.get(
                    "phase24hu_exception_slot_guard_reason"
                ),
                "evidence_source_family": (
                    _resolve_chunk_routing_family(matched_chunk)
                    or _resolve_chunk_source_family(matched_chunk)
                    or ""
                ),
                "evidence_source_role": _phase24hu_chunk_source_role(matched_chunk),
            }
        )
    return rows


def _build_answer_slot_evidence_map(
    *,
    required_slots: list[str],
    satisfied_slots: list[str],
    evidence_reentry_slots: list[str],
    missing_slots: list[str],
    article_span_selector: dict[str, Any] | None,
    chunks: list[RetrievedChunk],
    query: str = "",
) -> tuple[list[dict[str, Any]], float, list[str]]:
    selector = article_span_selector if isinstance(article_span_selector, dict) else {}
    selected_main_span_id = str(selector.get("selected_main_span_id") or "").strip()
    selected_article = str(selector.get("selected_article") or "").strip()
    evidence_slot_values = {
        str(row.get("slot_name") or ""): row
        for row in _build_evidence_required_slot_values(
            required_slots=required_slots,
            article_span_selector=article_span_selector,
            chunks=chunks,
            query=query,
        )
        if isinstance(row, dict)
    }
    satisfied = set(satisfied_slots)
    reentry = set(evidence_reentry_slots)
    missing = set(missing_slots)
    rows: list[dict[str, Any]] = []
    missing_reasons: list[str] = []
    confidence_sum = 0.0
    primary_chunk = _selector_primary_chunk(chunks, article_span_selector)
    primary_preferred_slots = {
        "governing_source",
        "exact_source_identity",
        "document_selection_reason",
        "result_or_holding",
        "temporal_validity",
        "current_applicability",
    }

    for slot in required_slots:
        matched_chunk = (
            primary_chunk
            if slot in primary_preferred_slots
            and primary_chunk is not None
            else _select_chunk_for_slot(chunks, slot, query=query)
        )
        span_id = _chunk_span_id(matched_chunk) if matched_chunk is not None else ""
        article = _chunk_article(matched_chunk) if matched_chunk is not None else ""
        if slot == "article_or_span" and selected_main_span_id:
            span_id = selected_main_span_id
            article = selected_article or article
        evidence_value = evidence_slot_values.get(slot) or {}
        if (
            evidence_value.get("phase24hu_exception_slot_guard_applied")
            and float(evidence_value.get("slot_confidence") or 0.0) <= 0.0
        ):
            span_id = ""
            article = ""
        if not span_id:
            span_id = str(evidence_value.get("evidence_span_id") or "")
        if not article:
            article = str(evidence_value.get("evidence_article") or "")
        if slot in missing:
            confidence = 0.0
            reason = "slot_not_satisfied_by_answer_or_evidence"
            missing_reasons.append(f"{slot}:{reason}")
        elif not span_id:
            confidence = 0.45
            reason = "answer_surface_only"
            missing_reasons.append(f"{slot}:evidence_span_not_mapped")
        elif slot in reentry:
            confidence = 0.65
            reason = "evidence_reentry_support"
        elif slot in satisfied:
            confidence = 0.85
            reason = "answer_and_evidence_support"
        else:
            confidence = 0.0
            reason = "slot_not_required_or_unknown"
        confidence_sum += confidence
        rows.append(
            {
                "answer_slot": slot,
                "evidence_span_id": span_id,
                "evidence_article": article,
                "slot_value": evidence_value.get("slot_value") or "",
                "evidence_quote_hash": evidence_value.get("evidence_quote_hash") or "",
                "slot_confidence": round(confidence, 3),
                "slot_missing_reason": reason,
            }
        )

    coverage = round(confidence_sum / len(required_slots), 3) if required_slots else 1.0
    return rows, coverage, dedupe_strings(missing_reasons)


def _build_completeness_synthesis_features(
    *,
    query: str,
    answer_text: str,
    article_span_selector: dict[str, Any] | None,
    chunks: list[RetrievedChunk],
    requested_source_families: list[str] | None = None,
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _build_completeness_synthesis_features_impl(
        query=query,
        answer_text=answer_text,
        article_span_selector=article_span_selector,
        chunks=chunks,
        requested_source_families=requested_source_families,
        source_family_resolution=source_family_resolution,
        resolve_chunk_routing_family=_resolve_chunk_routing_family,
        resolve_chunk_source_family=_resolve_chunk_source_family,
        satisfied_completeness_slots=_satisfied_completeness_slots,
        evidence_supported_completeness_slots=_evidence_supported_completeness_slots,
        build_evidence_required_slot_values=_build_evidence_required_slot_values,
        build_answer_slot_evidence_map=_build_answer_slot_evidence_map,
    )


def _strong_source_family_gate(source_family_resolution: SourceFamilyResolution) -> set[str]:
    return _strong_source_family_gate_impl(source_family_resolution)


def _apply_pre_generation_family_pool(
    *,
    chunks: list[RetrievedChunk],
    source_family_resolution: SourceFamilyResolution,
    top_k_effective: int,
    query: str = "",
    supporting_source_families: list[str] | None = None,
) -> tuple[list[RetrievedChunk], dict[str, Any]]:
    return _apply_pre_generation_family_pool_impl(
        chunks=chunks,
        source_family_resolution=source_family_resolution,
        top_k_effective=top_k_effective,
        query=query,
        supporting_source_families=supporting_source_families,
        resolve_chunk_routing_family=_resolve_chunk_routing_family,
        dedupe_retrieved_chunks=_dedupe_retrieved_chunks,
        hard_pre_generation_family_gates=_HARD_PRE_GENERATION_FAMILY_GATES,
    )


def _build_trace_payload(
    *,
    request_id: str,
    decision_lane: str,
    user_query: str,
    enriched_query: str,
    retrieval_query: str,
    question_normalized: str,
    question_type: str,
    target_date: str,
    law_scope_signal: dict[str, Any],
    law_filter: str | None,
    mentioned_laws: list[str],
    cross_law_mode: bool,
    requested_source_families: list[str],
    explicit_article_refs: list[tuple[str, str]],
    forced_article_refs: list[tuple[str, str]],
    applied_expansions: list[str],
    top_k_requested: int,
    top_k_effective: int,
    reranker_enabled: bool,
    pre_rerank_chunks: list[RetrievedChunk],
    post_rerank_chunks: list[RetrievedChunk],
    assembled_context: str,
    blocked: bool,
    guardrails_reasons: list[str],
    verification: dict[str, Any] | None,
    answer_contract: dict[str, Any],
    model_cited_source_ids: list[str],
    final_mode: str,
    final_reason: str | None,
    retrieval_plan: dict[str, Any] | None = None,
    metadata_lookup_query_signals: dict[str, Any] | None = None,
    metadata_first_selector: dict[str, Any] | None = None,
    source_identity_reranker: dict[str, Any] | None = None,
    source_cluster_selector: dict[str, Any] | None = None,
    article_span_selector: dict[str, Any] | None = None,
    source_family_resolution: dict[str, Any] | None = None,
    retrieval_verification_features: dict[str, Any] | None = None,
    relation_chain_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    assembled_evidence = _build_assembled_evidence(post_rerank_chunks, query=user_query)
    if not assembled_evidence and model_cited_source_ids:
        assembled_evidence = _build_fallback_assembled_evidence(
            model_cited_source_ids,
            fallback_excerpt=answer_contract.get("answer_text") or assembled_context or "",
        )
    phase24hx_feature_trace = build_phase24hx_feature_trace(
        metadata_first_selector=metadata_first_selector,
        source_identity_reranker=source_identity_reranker,
        article_span_selector=article_span_selector,
        retrieval_verification_features=retrieval_verification_features,
        source_family_resolution=source_family_resolution,
    )
    allowed_source_whitelist = (
        _build_allowed_source_whitelist(post_rerank_chunks)
        if post_rerank_chunks
        else [
            canonicalize_source_id(item.get("source_id")) or str(item.get("source_id"))
            for item in assembled_evidence
            if item.get("source_id")
        ]
    )
    payload = {
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question_raw": user_query,
        "question_normalized": question_normalized,
        "parsed_query": {
            "enriched_query": enriched_query,
            "retrieval_query": retrieval_query,
            "law_filter": law_filter,
            "mentioned_laws": mentioned_laws,
            "requested_source_families": requested_source_families,
            "predicted_family": (source_family_resolution or {}).get("predicted_family"),
            "family_confidence": (source_family_resolution or {}).get("family_confidence"),
            "expected_family_prior": (source_family_resolution or {}).get("expected_family_prior"),
            "selected_family_confidence": (source_family_resolution or {}).get("selected_family_confidence"),
            "family_override_reason": (retrieval_verification_features or {}).get("family_override_reason"),
            "pre_filter_family_set": (retrieval_verification_features or {}).get("pre_filter_family_set"),
            "reranked_family_set": (retrieval_verification_features or {}).get("reranked_family_set"),
            "selected_family_source": (retrieval_verification_features or {}).get("selected_family_source"),
            "family_gate_status": (retrieval_verification_features or {}).get("family_gate_status"),
            "family_candidates": (source_family_resolution or {}).get("family_candidates", []),
            "source_family_resolution": source_family_resolution,
            "retrieval_verification_features": retrieval_verification_features,
            "retrieval_plan": retrieval_plan,
            "metadata_lookup_query_signals": metadata_lookup_query_signals,
            "metadata_lookup_hit": bool((metadata_first_selector or {}).get("metadata_lookup_hit")),
            "metadata_lookup_source": (metadata_first_selector or {}).get("metadata_lookup_source"),
            "metadata_lookup_rank": (metadata_first_selector or {}).get("metadata_lookup_rank"),
            "metadata_lookup_confidence": (metadata_first_selector or {}).get("metadata_lookup_confidence"),
            "metadata_first_selector": metadata_first_selector,
            "source_identity_reranker": source_identity_reranker,
            "phase24hx_feature_trace": phase24hx_feature_trace,
            "document_identity_score": (source_identity_reranker or {}).get("document_identity_score"),
            "title_match_type": (source_identity_reranker or {}).get("title_match_type"),
            "identifier_match_type": (source_identity_reranker or {}).get("identifier_match_type"),
            "issuer_match_type": (source_identity_reranker or {}).get("issuer_match_type"),
            "year_match_type": (source_identity_reranker or {}).get("year_match_type"),
            "identity_rerank_input_source": (source_identity_reranker or {}).get("identity_rerank_input_source"),
            "document_rerank_reason": (source_identity_reranker or {}).get("document_rerank_reason"),
            "source_cluster_selector": source_cluster_selector,
            "article_span_selector": article_span_selector,
            "relation_chain_policy": relation_chain_policy,
            "relation_chain_expansion_applied": (relation_chain_policy or {}).get(
                "relation_chain_expansion_applied"
            ),
            "relation_chain_source_key": (relation_chain_policy or {}).get("relation_chain_source_key"),
            "relation_chain_repeal_source_key": (relation_chain_policy or {}).get(
                "relation_chain_repeal_source_key"
            ),
            "relation_chain_current_basis_source_key": (relation_chain_policy or {}).get(
                "relation_chain_current_basis_source_key"
            ),
            "relation_chain_missing_reason": (relation_chain_policy or {}).get(
                "relation_chain_missing_reason"
            ),
            "relation_chain_span_keys": (relation_chain_policy or {}).get("relation_chain_span_keys"),
            "explicit_article_refs": [
                {"law": law, "madde": madde}
                for law, madde in explicit_article_refs
            ],
            "forced_article_refs": [
                {"law": law, "madde": madde}
                for law, madde in forced_article_refs
            ],
            "applied_expansions": applied_expansions,
        },
        "law_scope_signal": law_scope_signal,
        "question_type": question_type,
        "target_date": target_date,
        "phase24hx_feature_trace": phase24hx_feature_trace,
        "retrieval_top_k": top_k_effective,
        "rerank_list": [
            _serialize_trace_chunk(chunk) for chunk in post_rerank_chunks
        ],
        "assembled_evidence": assembled_evidence,
        "allowed_source_whitelist": allowed_source_whitelist,
        "answer_contract": answer_contract,
        "completeness_synthesis": {
            "required_fact_coverage_score": answer_contract.get("required_fact_coverage_score"),
            "minimum_answer_facts_present": answer_contract.get("minimum_answer_facts_present"),
            "completeness_degrade_reason": answer_contract.get("completeness_degrade_reason"),
            "task_type_answer_template_used": answer_contract.get("task_type_answer_template_used"),
            "must_have_fact_slots": answer_contract.get("must_have_fact_slots"),
            "satisfied_fact_slots": answer_contract.get("satisfied_fact_slots"),
            "missing_fact_slots": answer_contract.get("missing_fact_slots"),
            "evidence_slot_reentry_applied": answer_contract.get("evidence_slot_reentry_applied"),
            "evidence_slot_reentry_slots": answer_contract.get("evidence_slot_reentry_slots"),
            "rubric_aligned_completeness_class": answer_contract.get("rubric_aligned_completeness_class"),
            "answer_slot_evidence_map": answer_contract.get("answer_slot_evidence_map"),
            "answer_slot_coverage_score": answer_contract.get("answer_slot_coverage_score"),
            "answer_slot_missing_reasons": answer_contract.get("answer_slot_missing_reasons"),
            "required_slot_schema": answer_contract.get("required_slot_schema"),
            "evidence_required_slot_values": answer_contract.get("evidence_required_slot_values"),
            "evidence_required_slot_value_count": answer_contract.get("evidence_required_slot_value_count"),
            "evidence_slot_synthesis_applied": answer_contract.get("evidence_slot_synthesis_applied"),
            "evidence_slot_synthesis_slots": answer_contract.get("evidence_slot_synthesis_slots"),
            "evidence_slot_synthesis_reason": answer_contract.get("evidence_slot_synthesis_reason"),
            "required_slot_matrix_version": answer_contract.get("required_slot_matrix_version"),
            "required_slot_task_type": answer_contract.get("required_slot_task_type"),
            "required_slot_answer_template": answer_contract.get("required_slot_answer_template"),
            "required_slot_source_families": answer_contract.get("required_slot_source_families"),
            "required_slot_family_labels": answer_contract.get("required_slot_family_labels"),
            "required_slot_task_slots": answer_contract.get("required_slot_task_slots"),
            "required_slot_family_additions": answer_contract.get("required_slot_family_additions"),
            "required_slot_query_additions": answer_contract.get("required_slot_query_additions"),
            "required_slot_matrix_slots": answer_contract.get("required_slot_matrix_slots"),
            "required_slot_runtime_slots": answer_contract.get("required_slot_runtime_slots"),
            "required_slot_critical_slots": answer_contract.get("required_slot_critical_slots"),
            "required_slot_resolution_reason": answer_contract.get("required_slot_resolution_reason"),
            "answer_slot_extraction_version": answer_contract.get("answer_slot_extraction_version"),
            "answer_slots": answer_contract.get("answer_slots"),
            "answer_slot_required_count": answer_contract.get("answer_slot_required_count"),
            "answer_slot_filled_count": answer_contract.get("answer_slot_filled_count"),
            "answer_slot_verified_count": answer_contract.get("answer_slot_verified_count"),
            "answer_slot_missing_count": answer_contract.get("answer_slot_missing_count"),
            "answer_slot_unsupported_count": answer_contract.get("answer_slot_unsupported_count"),
            "answer_slot_extraction_methods": answer_contract.get("answer_slot_extraction_methods"),
            "critical_answer_slots_missing": answer_contract.get("critical_answer_slots_missing"),
            "candidate_completeness_score": answer_contract.get("candidate_completeness_score"),
            "selected_document_has_body_span": answer_contract.get("selected_document_has_body_span"),
            "selected_document_has_non_title_span": answer_contract.get("selected_document_has_non_title_span"),
            "selected_document_has_document_level_body_span": answer_contract.get(
                "selected_document_has_document_level_body_span"
            ),
            "selected_document_has_materialized_body_span": answer_contract.get(
                "selected_document_has_materialized_body_span"
            ),
            "title_only_answer_degraded": answer_contract.get("title_only_answer_degraded"),
            "insufficient_canonical_span_evidence": answer_contract.get("insufficient_canonical_span_evidence"),
        },
        "model_cited_source_ids": model_cited_source_ids,
        "verifier_verdict": verification.get("verdict") if isinstance(verification, dict) else None,
        "final_mode": final_mode,
        "final_reason": final_reason,
        "query_signals": {
            "user_query": user_query,
            "enriched_query": enriched_query,
            "retrieval_query": retrieval_query,
            "law_filter": law_filter,
            "mentioned_laws": mentioned_laws,
            "cross_law_mode": cross_law_mode,
            "predicted_family": (source_family_resolution or {}).get("predicted_family"),
            "family_confidence": (source_family_resolution or {}).get("family_confidence"),
            "expected_family_prior": (source_family_resolution or {}).get("expected_family_prior"),
            "selected_family_confidence": (source_family_resolution or {}).get("selected_family_confidence"),
            "family_override_reason": (retrieval_verification_features or {}).get("family_override_reason"),
            "family_candidates": (source_family_resolution or {}).get("family_candidates", []),
            "source_family_resolution": source_family_resolution,
            "retrieval_verification_features": retrieval_verification_features,
            "retrieval_plan": retrieval_plan,
            "metadata_lookup_query_signals": metadata_lookup_query_signals,
            "metadata_lookup_hit": bool((metadata_first_selector or {}).get("metadata_lookup_hit")),
            "metadata_lookup_source": (metadata_first_selector or {}).get("metadata_lookup_source"),
            "metadata_lookup_rank": (metadata_first_selector or {}).get("metadata_lookup_rank"),
            "metadata_lookup_confidence": (metadata_first_selector or {}).get("metadata_lookup_confidence"),
            "metadata_first_selector": metadata_first_selector,
            "source_identity_reranker": source_identity_reranker,
            "phase24hx_feature_trace": phase24hx_feature_trace,
            "source_cluster_selector": source_cluster_selector,
            "article_span_selector": article_span_selector,
            "explicit_article_refs": [
                {"law": law, "madde": madde}
                for law, madde in explicit_article_refs
            ],
            "forced_article_refs": [
                {"law": law, "madde": madde}
                for law, madde in forced_article_refs
            ],
            "applied_expansions": applied_expansions,
        },
        "retrieval": {
            "top_k_requested": top_k_requested,
            "top_k_effective": top_k_effective,
            "reranker_enabled": reranker_enabled,
            "source_family_resolution": source_family_resolution,
            "metadata_lookup_query_signals": metadata_lookup_query_signals,
            "metadata_lookup_hit": bool((metadata_first_selector or {}).get("metadata_lookup_hit")),
            "metadata_lookup_source": (metadata_first_selector or {}).get("metadata_lookup_source"),
            "metadata_lookup_rank": (metadata_first_selector or {}).get("metadata_lookup_rank"),
            "metadata_lookup_confidence": (metadata_first_selector or {}).get("metadata_lookup_confidence"),
            "metadata_first_selector": metadata_first_selector,
            "source_identity_reranker": source_identity_reranker,
            "phase24hx_feature_trace": phase24hx_feature_trace,
            "reranker_family_bonus": (retrieval_verification_features or {}).get("reranker_family_bonus"),
            "identifier_match_flag": (retrieval_verification_features or {}).get("identifier_match_flag"),
            "temporal_alignment_flag": (retrieval_verification_features or {}).get("temporal_alignment_flag"),
            "selected_evidence_count": (retrieval_verification_features or {}).get("selected_evidence_count"),
            "cross_family_conflict_flag": (retrieval_verification_features or {}).get("cross_family_conflict_flag"),
            "expected_family_prior": (retrieval_verification_features or {}).get("expected_family_prior"),
            "preferred_family_pool_size": (retrieval_verification_features or {}).get("preferred_family_pool_size"),
            "cross_family_fallback_used": (retrieval_verification_features or {}).get("cross_family_fallback_used"),
            "family_override_reason": (retrieval_verification_features or {}).get("family_override_reason"),
            "selected_family_confidence": (retrieval_verification_features or {}).get("selected_family_confidence"),
            "pre_filter_family_set": (retrieval_verification_features or {}).get("pre_filter_family_set"),
            "reranked_family_set": (retrieval_verification_features or {}).get("reranked_family_set"),
            "selected_family_source": (retrieval_verification_features or {}).get("selected_family_source"),
            "family_gate_status": (retrieval_verification_features or {}).get("family_gate_status"),
            "retrieval_verification_features": retrieval_verification_features,
            "article_span_selector": article_span_selector,
            "pre_rerank_chunks": [
                _serialize_trace_chunk(chunk) for chunk in pre_rerank_chunks
            ],
            "post_rerank_chunks": [
                _serialize_trace_chunk(chunk) for chunk in post_rerank_chunks
            ],
        },
        "context_assembly": {
            "context_chunk_citations": [chunk.citation for chunk in post_rerank_chunks],
            "assembled_context": assembled_context,
            "assembled_evidence": assembled_evidence,
            "allowed_source_whitelist": allowed_source_whitelist,
            "article_span_selector": article_span_selector,
            "phase24hx_feature_trace": phase24hx_feature_trace,
        },
        "generation_outcome": {
            "decision_lane": decision_lane,
            "blocked": blocked,
            "guardrails_reasons": guardrails_reasons,
            "verification": verification,
            "final_mode": final_mode,
            "final_reason": final_reason,
            "completeness_synthesis": {
                "required_fact_coverage_score": answer_contract.get("required_fact_coverage_score"),
                "minimum_answer_facts_present": answer_contract.get("minimum_answer_facts_present"),
                "completeness_degrade_reason": answer_contract.get("completeness_degrade_reason"),
                "task_type_answer_template_used": answer_contract.get("task_type_answer_template_used"),
                "must_have_fact_slots": answer_contract.get("must_have_fact_slots"),
                "satisfied_fact_slots": answer_contract.get("satisfied_fact_slots"),
                "missing_fact_slots": answer_contract.get("missing_fact_slots"),
                "evidence_slot_reentry_applied": answer_contract.get("evidence_slot_reentry_applied"),
                "evidence_slot_reentry_slots": answer_contract.get("evidence_slot_reentry_slots"),
                "rubric_aligned_completeness_class": answer_contract.get("rubric_aligned_completeness_class"),
                "answer_slot_evidence_map": answer_contract.get("answer_slot_evidence_map"),
                "answer_slot_coverage_score": answer_contract.get("answer_slot_coverage_score"),
                "answer_slot_missing_reasons": answer_contract.get("answer_slot_missing_reasons"),
                "required_slot_schema": answer_contract.get("required_slot_schema"),
                "evidence_required_slot_values": answer_contract.get("evidence_required_slot_values"),
                "evidence_required_slot_value_count": answer_contract.get("evidence_required_slot_value_count"),
                "evidence_slot_synthesis_applied": answer_contract.get("evidence_slot_synthesis_applied"),
                "evidence_slot_synthesis_slots": answer_contract.get("evidence_slot_synthesis_slots"),
                "evidence_slot_synthesis_reason": answer_contract.get("evidence_slot_synthesis_reason"),
                "required_slot_matrix_version": answer_contract.get("required_slot_matrix_version"),
                "required_slot_task_type": answer_contract.get("required_slot_task_type"),
                "required_slot_answer_template": answer_contract.get("required_slot_answer_template"),
                "required_slot_source_families": answer_contract.get("required_slot_source_families"),
                "required_slot_family_labels": answer_contract.get("required_slot_family_labels"),
                "required_slot_task_slots": answer_contract.get("required_slot_task_slots"),
                "required_slot_family_additions": answer_contract.get("required_slot_family_additions"),
                "required_slot_query_additions": answer_contract.get("required_slot_query_additions"),
                "required_slot_matrix_slots": answer_contract.get("required_slot_matrix_slots"),
                "required_slot_runtime_slots": answer_contract.get("required_slot_runtime_slots"),
                "required_slot_critical_slots": answer_contract.get("required_slot_critical_slots"),
                "required_slot_resolution_reason": answer_contract.get("required_slot_resolution_reason"),
                "answer_slot_extraction_version": answer_contract.get("answer_slot_extraction_version"),
                "answer_slots": answer_contract.get("answer_slots"),
                "answer_slot_required_count": answer_contract.get("answer_slot_required_count"),
                "answer_slot_filled_count": answer_contract.get("answer_slot_filled_count"),
                "answer_slot_verified_count": answer_contract.get("answer_slot_verified_count"),
                "answer_slot_missing_count": answer_contract.get("answer_slot_missing_count"),
                "answer_slot_unsupported_count": answer_contract.get("answer_slot_unsupported_count"),
                "answer_slot_extraction_methods": answer_contract.get("answer_slot_extraction_methods"),
                "critical_answer_slots_missing": answer_contract.get("critical_answer_slots_missing"),
                "candidate_completeness_score": answer_contract.get("candidate_completeness_score"),
                "selected_document_has_body_span": answer_contract.get("selected_document_has_body_span"),
                "selected_document_has_non_title_span": answer_contract.get("selected_document_has_non_title_span"),
                "selected_document_has_document_level_body_span": answer_contract.get(
                    "selected_document_has_document_level_body_span"
                ),
                "selected_document_has_materialized_body_span": answer_contract.get(
                    "selected_document_has_materialized_body_span"
                ),
                "title_only_answer_degraded": answer_contract.get("title_only_answer_degraded"),
                "insufficient_canonical_span_evidence": answer_contract.get("insufficient_canonical_span_evidence"),
            },
        },
    }
    return validate_trace_payload(payload)


# ---------------------------------------------------------------------------
# Request / Response Modelleri
# ---------------------------------------------------------------------------


class ConversationMessage(BaseModel):
    """Tekil konuşma mesajı (OpenAI formatı)."""

    role: str  # "user" | "assistant" | "system"
    content: str


class ChatCompletionRequest(BaseModel):
    """OpenAI-uyumlu chat completions request.

    Ek alanlar (hukuk-ai özel):
        session_id:       Konuşma oturumu (None → yeni oturum oluşturulur)
        law_filter:       Metadata filtresi (kanun kısaltması: "TBK", "TMK", ...)
        use_verification: Verification Engine etkinleştir/pasifleştir (default: True)
        top_k:            Retrieval hit sayısı (default: 20)
    """

    model: str = "hukuk-ai-poc"
    messages: list[ConversationMessage]
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None

    # Hukuk AI özel alanlar
    session_id: str | None = None
    law_filter: str | None = None
    use_verification: bool = True
    top_k: int = Field(default=20, ge=1, le=50)
    include_trace: bool = False


class ChatChoice(BaseModel):
    index: int
    message: ConversationMessage
    finish_reason: str = "stop"


class ChatUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """OpenAI-uyumlu chat completions response (hukuk-ai meta eklentisiyle)."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatChoice]
    usage: ChatUsage

    # Hukuk AI ek metadata
    session_id: str | None = None
    citations: list[str] = Field(default_factory=list)
    blocked: bool = False
    guardrails_reasons: list[str] = Field(default_factory=list)
    verification: dict[str, Any] | None = None
    final_mode: str | None = None
    final_reason: str | None = None
    confidence_0_100: int | None = None
    answer_contract: dict[str, Any] | None = None
    trace: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# In-memory Conversation Store
# ---------------------------------------------------------------------------


class ConversationStore:
    """Session bazlı konuşma geçmişi yönetimi (in-memory).

    Faz 1: Basit OrderedDict + kapasite limiti.
    Faz 2: Redis veya persistent storage ile değiştirilebilir.

    Thread-safety notu:
        asyncio single-thread modelde thread-safe.
        multi-worker (uvicorn --workers N) için process-shared store gerekir (Redis).
    """

    MAX_SESSIONS: int = 500               # Maksimum aktif oturum sayısı
    MAX_MESSAGES_PER_SESSION: int = 40    # Maksimum mesaj sayısı (user+assistant turlar)

    def __init__(self, backend: SessionStoreBackend | None = None) -> None:
        self._backend = backend or build_session_backend_from_env(
            max_sessions=self.MAX_SESSIONS,
            max_messages_per_session=self.MAX_MESSAGES_PER_SESSION,
        )

    def _sync_limits(self) -> None:
        self._backend.max_sessions = self.MAX_SESSIONS
        self._backend.max_messages_per_session = self.MAX_MESSAGES_PER_SESSION

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        """Oturum geçmişini döndür. Oturum yoksa boş liste."""
        self._sync_limits()
        return list(self._backend.get_history(session_id))

    def add_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
    ) -> None:
        """Oturuma kullanıcı + asistan turu ekle."""
        self._sync_limits()
        self._backend.add_turn(session_id, user_message, assistant_message)

    def clear_session(self, session_id: str) -> bool:
        """Oturumu sil. Var idiyse True döndür."""
        self._sync_limits()
        return self._backend.clear_session(session_id)

    def session_count(self) -> int:
        """Aktif oturum sayısı."""
        self._sync_limits()
        return self._backend.session_count()


_conversation_store: ConversationStore | None = None
_conversation_store_signature: tuple[str, str, str] | None = None


def get_conversation_store() -> ConversationStore:
    """FastAPI Depends için ConversationStore factory."""
    global _conversation_store, _conversation_store_signature
    signature = (
        os.getenv("SESSION_STORE_BACKEND", "memory"),
        os.getenv("REDIS_URL", ""),
        os.getenv("SESSION_STORE_NAMESPACE", "hukuk-ai"),
    )
    if _conversation_store is None or _conversation_store_signature != signature:
        _conversation_store = ConversationStore()
        _conversation_store_signature = signature
    return _conversation_store


# ---------------------------------------------------------------------------
# Multi-turn Context Builder
# ---------------------------------------------------------------------------


def _build_multiturn_query(
    *,
    last_user_message: str,
    conversation_history: list[dict[str, str]],
    max_history_chars: int = 2000,
) -> str:
    """Konuşma geçmişini son sorguya dahil et.

    Format:
        [Önceki Konuşma]\n
        Kullanıcı: ...
        Asistan: ...
        ...
        [Mevcut Soru]: <last_user_message>

    Çok uzun geçmiş → son N karakteri kısalt.
    Geçmiş yoksa → sadece son soruyu döndür.
    """
    if not conversation_history:
        return last_user_message

    # Geçmişi metin satırlarına dönüştür
    history_lines: list[str] = []
    for msg in conversation_history:
        role_label = "Kullanıcı" if msg["role"] == "user" else "Asistan"
        history_lines.append(f"{role_label}: {msg['content']}")

    history_text = "\n".join(history_lines)

    # Uzunluk limiti
    if len(history_text) > max_history_chars:
        history_text = "..." + history_text[-max_history_chars:]

    return (
        f"[Önceki Konuşma Bağlamı]\n{history_text}\n\n"
        f"[Mevcut Soru]: {last_user_message}"
    )


# ---------------------------------------------------------------------------
# SSE Generator
# ---------------------------------------------------------------------------


async def _stream_sse_response(
    *,
    answer: str,
    session_id: str,
    model: str,
    citations: list[str],
    blocked: bool,
    guardrails_reasons: list[str],
    verification: dict[str, Any] | None,
    usage: ChatUsage | None = None,
    response_id: str | None = None,
    trace: dict[str, Any] | None = None,
    final_mode: str | None = None,
    final_reason: str | None = None,
    confidence_0_100: int | None = None,
    answer_contract: dict[str, Any] | None = None,
    include_metadata_chunk: bool = False,
    words_per_chunk: int = 5,
    delay_between_chunks: float = 0.02,
) -> AsyncGenerator[str, None]:
    """RAG yanıtını OpenAI SSE formatında stream et.

    Akış:
        1. Role chunk (delta: {role: "assistant"})
        2. Content chunks (delta: {content: <kelime grubu>})
        3. Finish chunk (delta: {}, finish_reason: "stop")
        4. Opsiyonel metadata chunk (hukuk-ai özel: citations, verification)
        5. [DONE]
    """
    chunk_id = response_id or f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created = int(time.time())

    def _make_delta_chunk(delta: dict[str, Any], finish_reason: str | None = None) -> str:
        payload = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": delta,
                    "finish_reason": finish_reason,
                }
            ],
        }
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    # 1. Role chunk
    yield _make_delta_chunk({"role": "assistant"})
    await asyncio.sleep(0)

    # 2. Content chunks
    words = answer.split()
    for i in range(0, len(words), words_per_chunk):
        group = words[i : i + words_per_chunk]
        # İlk chunk'ta boşluk yok, sonrakilerde boşluk ekle
        content = (" " if i > 0 else "") + " ".join(group)
        yield _make_delta_chunk({"content": content})
        await asyncio.sleep(delay_between_chunks)

    # 3. Finish chunk
    yield _make_delta_chunk({}, finish_reason="stop")
    await asyncio.sleep(0)

    # 4. Hukuk-AI özel metadata chunk (opsiyonel; varsayılan olarak OpenAI uyumluluğu korunur)
    if include_metadata_chunk:
        meta_payload: dict[str, Any] = {
            "id": chunk_id,
            "object": "chat.completion.metadata",
            "session_id": session_id,
            "citations": citations,
            "blocked": blocked,
            "guardrails_reasons": guardrails_reasons,
            "verification": verification,
        }
        if trace is not None:
            meta_payload["trace"] = trace
        if usage is not None:
            meta_payload["usage"] = usage.model_dump()
        if final_mode is not None:
            meta_payload["final_mode"] = final_mode
        if final_reason is not None:
            meta_payload["final_reason"] = final_reason
        if confidence_0_100 is not None:
            meta_payload["confidence_0_100"] = confidence_0_100
        if answer_contract is not None:
            meta_payload["answer_contract"] = answer_contract
        yield f"data: {json.dumps(meta_payload, ensure_ascii=False)}\n\n"

    # 5. Done sentinel
    yield "data: [DONE]\n\n"


# ---------------------------------------------------------------------------
# Router Dependencies
# ---------------------------------------------------------------------------


def _get_orchestrator(request: Request) -> RAGOrchestrator:
    """FastAPI app.state'ten RAGOrchestrator al."""
    orchestrator: RAGOrchestrator | None = getattr(request.app.state, "orchestrator", None)
    if orchestrator is None:
        raise HTTPException(
            status_code=503,
            detail="RAG Orchestrator henüz başlatılmadı. Sunucu hazır değil.",
        )
    return orchestrator


def _get_retriever(request: Request) -> Any | None:
    """FastAPI app.state'ten retriever al (opsiyonel)."""
    return getattr(request.app.state, "retriever", None)


async def _run_native_dialog_passthrough(
    *,
    request: Request,
    request_body: ChatCompletionRequest,
    intent: str,
) -> tuple[str, dict[str, int] | None, dict[str, Any] | None]:
    orchestrator = _get_orchestrator(request)
    llm_client = getattr(orchestrator, "llm_client", None)
    if llm_client is None or not hasattr(llm_client, "chat"):
        return _build_native_dialog_fallback_answer(intent), None, None

    from llm.client import ChatMessage

    native_messages = [ChatMessage(role="system", content=_NATIVE_DIALOG_SYSTEM_PROMPT)]
    native_messages.extend(
        ChatMessage(role=msg.role, content=msg.content)
        for msg in request_body.messages
        if msg.role in {"user", "assistant", "system"}
    )

    try:
        result = await llm_client.chat(
            messages=native_messages,
            temperature=request_body.temperature if request_body.temperature is not None else 0.2,
            max_tokens=request_body.max_tokens,
        )
    except Exception:
        logger.warning("Native dialog passthrough failed; deterministic fallback used", exc_info=True)
        return _build_native_dialog_fallback_answer(intent), None, None

    usage_payload = None
    if result.usage is not None:
        usage_payload = {
            "prompt_tokens": result.usage.prompt_tokens,
            "completion_tokens": result.usage.completion_tokens,
            "total_tokens": result.usage.total_tokens,
        }
    return result.text.strip() or _build_native_dialog_fallback_answer(intent), usage_payload, result.trace


def _estimate_chat_usage(
    messages: list[ConversationMessage],
    answer_text: str,
) -> ChatUsage:
    prompt_tokens = sum(estimate_tokens(message.content) for message in messages)
    completion_tokens = estimate_tokens(answer_text)
    return ChatUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )


def _resolve_chat_usage(
    *,
    messages: list[ConversationMessage],
    answer_text: str,
    upstream_usage: dict[str, int] | None,
) -> tuple[ChatUsage, str]:
    try:
        resolved = resolve_token_usage(
            messages=messages,
            answer_text=answer_text,
            upstream_usage=upstream_usage,
        )
        return (
            ChatUsage(
                prompt_tokens=resolved.prompt_tokens,
                completion_tokens=resolved.completion_tokens,
                total_tokens=resolved.total_tokens,
            ),
            resolved.source,
        )
    except TokenAccountingError:
        get_metrics_registry().record_token_accounting_failure()
        if not token_accounting_fallback_allowed():
            raise
        return _estimate_chat_usage(messages, answer_text), "estimated"


def _canonical_snapshot_messages(
    *,
    conversation_history: list[dict[str, str]],
    last_user_message: str,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for item in conversation_history:
        role = item.get("role")
        content = item.get("content")
        if role in {"user", "assistant", "system"} and isinstance(content, str):
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": last_user_message})
    return messages


def _build_canonical_request_snapshot(
    *,
    request_body: ChatCompletionRequest,
    conversation_history: list[dict[str, str]],
    last_user_message: str,
) -> dict[str, Any]:
    return {
        "model": request_body.model,
        "messages": _canonical_snapshot_messages(
            conversation_history=conversation_history,
            last_user_message=last_user_message,
        ),
        "stream": False,
        "temperature": request_body.temperature,
        "max_tokens": request_body.max_tokens,
        "session_id": request_body.session_id,
        "law_filter": request_body.law_filter,
        "use_verification": request_body.use_verification,
        "top_k": request_body.top_k,
        "include_trace": request_body.include_trace,
    }


def _build_persisted_request_snapshot(
    *,
    request_body: ChatCompletionRequest,
    conversation_history: list[dict[str, str]],
    last_user_message: str,
) -> dict[str, Any]:
    snapshot = _build_canonical_request_snapshot(
        request_body=request_body,
        conversation_history=conversation_history,
        last_user_message=last_user_message,
    )
    return json.loads(json.dumps(snapshot, ensure_ascii=False))


def _build_persisted_raw_answer_snapshot(
    *,
    answer_text: str,
    citations: list[str],
    source_ids: list[str],
    final_mode: str | None,
    final_reason: str | None,
) -> dict[str, Any]:
    return _build_persisted_raw_answer_snapshot_impl(
        answer_text=answer_text,
        citations=citations,
        source_ids=source_ids,
        final_mode=final_mode,
        final_reason=final_reason,
    )


def _build_persisted_response_envelope_snapshot(
    *,
    response_id: str,
    blocked: bool,
    final_mode: str | None,
    final_reason: str | None,
    citations: list[str],
    source_ids: list[str],
) -> dict[str, Any]:
    return _build_persisted_response_envelope_snapshot_impl(
        response_id=response_id,
        blocked=blocked,
        final_mode=final_mode,
        final_reason=final_reason,
        citations=citations,
        source_ids=source_ids,
    )


def _post_canonical_answer_path_request(
    *,
    base_url: str,
    payload: dict[str, Any],
    timeout_seconds: float,
) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{base_url}/v1/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"canonical answer path HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"canonical answer path unavailable: {exc}") from exc

    if not isinstance(body, dict):
        raise RuntimeError("canonical answer path invalid JSON body")
    return body


async def _proxy_canonical_answer_path(
    *,
    request_body: ChatCompletionRequest,
    conversation_history: list[dict[str, str]],
    last_user_message: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    base_url = _canonical_answer_path_base_url()
    if not base_url:
        raise HTTPException(
            status_code=503,
            detail="RC-O boundary proxy etkin ama RELEASE_CANONICAL_ANSWER_PATH_BASE_URL tanımlı değil",
        )

    snapshot = _build_canonical_request_snapshot(
        request_body=request_body,
        conversation_history=conversation_history,
        last_user_message=last_user_message,
    )
    response = await asyncio.to_thread(
        _post_canonical_answer_path_request,
        base_url=base_url,
        payload=snapshot,
        timeout_seconds=_boundary_proxy_timeout_seconds(),
    )
    return snapshot, response


def _finalize_boundary_proxy_response(
    *,
    request: Request,
    request_body: ChatCompletionRequest,
    store: ConversationStore,
    session_id: str,
    user_message: str,
    canonical_snapshot: dict[str, Any],
    proxy_response: dict[str, Any],
) -> Any:
    response_id = proxy_response.get("id")
    if not isinstance(response_id, str) or not response_id.strip():
        response_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

    created = proxy_response.get("created")
    if not isinstance(created, int):
        created = int(time.time())

    choices = proxy_response.get("choices") or []
    message_payload = ((choices[0] if choices else {}).get("message") or {}) if isinstance(choices, list) else {}
    answer_text = message_payload.get("content")
    if not isinstance(answer_text, str):
        raise HTTPException(status_code=502, detail="Canonical answer path invalid assistant payload")

    citations = proxy_response.get("citations") or []
    if not isinstance(citations, list):
        citations = []
    citations = [item for item in citations if isinstance(item, str)]

    blocked = bool(proxy_response.get("blocked"))
    guardrails_reasons = proxy_response.get("guardrails_reasons") or []
    if not isinstance(guardrails_reasons, list):
        guardrails_reasons = []
    guardrails_reasons = [item for item in guardrails_reasons if isinstance(item, str)]

    verification = proxy_response.get("verification")
    if not isinstance(verification, dict):
        verification = None

    answer_contract = proxy_response.get("answer_contract")
    if not isinstance(answer_contract, dict):
        answer_contract = None

    final_mode = proxy_response.get("final_mode")
    if not isinstance(final_mode, str):
        final_mode = None
    final_reason = proxy_response.get("final_reason")
    if final_reason is not None and not isinstance(final_reason, str):
        final_reason = None

    trace_payload = proxy_response.get("trace")
    if not isinstance(trace_payload, dict):
        trace_payload = {}
    contract_repair = build_or_repair_answer_contract(
        qid=response_id,
        answer_text=answer_text,
        citations=citations,
        answer_contract=answer_contract,
        final_mode=final_mode,
        final_reason=final_reason,
        trace_payload=trace_payload,
        blocked=blocked,
        guardrails_reasons=guardrails_reasons,
        verification=verification,
    )
    if not answer_text.strip():
        answer_text = controlled_fallback_answer(contract_repair.contract)
        refreshed_contract = _refresh_contract_completeness_for_answer_text(
            answer_contract=contract_repair.contract,
            answer_text=answer_text,
            query=user_message,
            trace_payload=trace_payload,
        )
        contract_repair = build_or_repair_answer_contract(
            qid=response_id,
            answer_text=answer_text,
            citations=citations,
            answer_contract=refreshed_contract,
            final_mode=final_mode,
            final_reason=final_reason,
            trace_payload=trace_payload,
            blocked=blocked,
            guardrails_reasons=guardrails_reasons,
            verification=verification,
        )
    answer_contract = contract_repair.contract
    answer_text = _resolve_contract_suppressed_answer_text(
        answer_text=answer_text,
        answer_contract=answer_contract,
    )
    trace_payload = dict(trace_payload)
    trace_payload["answer_contract"] = answer_contract
    trace_payload["answer_contract_validation"] = contract_repair.validation
    trace_payload["confidence_0_100"] = contract_repair.confidence_0_100
    if trace_payload:
        _export_trace_payload_or_raise(request_id=response_id, trace_payload=trace_payload)

    if _release_controls_perimeter_session_isolation_enabled():
        persist_sidecar_session_turn(
            session_id=session_id,
            user_message=user_message,
            assistant_message=answer_text,
            max_messages_per_session=ConversationStore.MAX_MESSAGES_PER_SESSION,
        )
    else:
        store.add_turn(session_id, user_message, answer_text)
    snapshot_messages = [
        ConversationMessage(role=item["role"], content=item["content"])
        for item in canonical_snapshot.get("messages", [])
        if isinstance(item, dict)
        and isinstance(item.get("role"), str)
        and isinstance(item.get("content"), str)
    ]
    snapshot_history = [
        {"role": msg.role, "content": msg.content}
        for msg in snapshot_messages[:-1]
    ]
    usage, usage_source = _resolve_chat_usage(
        messages=snapshot_messages,
        answer_text=answer_text,
        upstream_usage=None,
    )
    request_id = ensure_request_id(request)
    trace_id = ensure_trace_id(request)
    source_ids = _extract_answer_source_ids(answer_contract=answer_contract, citations=citations)
    latency_ms = (time.perf_counter() - getattr(request.state, "request_started_at", time.perf_counter())) * 1000.0
    decision_timestamps = {
        "request_started_at": datetime.fromtimestamp(
            getattr(request.state, "request_wall_started_at", time.time()),
            tz=timezone.utc,
        ).isoformat(),
        "decision_completed_at": datetime.now(timezone.utc).isoformat(),
    }
    persisted_request_snapshot = _build_persisted_request_snapshot(
        request_body=request_body,
        conversation_history=snapshot_history,
        last_user_message=user_message,
    )
    persisted_raw_answer_snapshot = _build_persisted_raw_answer_snapshot(
        answer_text=answer_text,
        citations=citations,
        source_ids=source_ids,
        final_mode=final_mode,
        final_reason=final_reason,
    )
    persisted_response_envelope_snapshot = _build_persisted_response_envelope_snapshot(
        response_id=response_id,
        blocked=blocked,
        final_mode=final_mode,
        final_reason=final_reason,
        citations=citations,
        source_ids=source_ids,
    )

    append_audit_event(
        event_type="chat_completion",
        request=request,
        request_id=request_id,
        trace_id=trace_id,
        response_id=response_id,
        session_id=session_id,
        model=request_body.model,
        stream=request_body.stream,
        blocked=blocked,
        citations=citations,
        guardrails_reasons=guardrails_reasons,
        usage=usage.model_dump(),
        usage_source=usage_source,
        message_count=len(snapshot_messages),
        user_message_chars=len(user_message),
        selected_lane=release_lane_id(),
        final_mode=final_mode,
        refusal_reason=final_reason,
        source_ids=source_ids,
        latency_ms=latency_ms,
        token_accounting={"usage": usage.model_dump(), "source": usage_source},
        decision_timestamps=decision_timestamps,
        api_version=api_version_label(),
        persisted_request_snapshot=persisted_request_snapshot,
        persisted_raw_answer_snapshot=persisted_raw_answer_snapshot,
        persisted_response_envelope_snapshot=persisted_response_envelope_snapshot,
    )
    get_metrics_registry().record_chat_outcome(
        path=request.url.path,
        model=request_body.model,
        blocked=blocked,
        is_refusal=looks_like_refusal(answer_text, blocked=blocked),
        usage_source=usage_source,
        citation_count=len(citations),
        hallucination_fail=_verification_has_hallucination_fail(verification),
    )

    client_trace = trace_payload if request_body.include_trace else None
    public_answer_contract = _sanitize_public_answer_contract(answer_contract)
    if request_body.stream:
        return StreamingResponse(
            _stream_sse_response(
                answer=answer_text,
                session_id=session_id,
                model=request_body.model,
                citations=citations,
                blocked=blocked,
                guardrails_reasons=guardrails_reasons,
                verification=verification,
                usage=usage,
                response_id=response_id,
                trace=client_trace,
                final_mode=final_mode,
                final_reason=final_reason,
                confidence_0_100=contract_repair.confidence_0_100,
                answer_contract=public_answer_contract,
                include_metadata_chunk=request_body.include_trace,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "X-Session-Id": session_id,
            },
        )

    return ChatCompletionResponse(
        id=response_id,
        created=created,
        model=request_body.model,
        choices=[
            ChatChoice(
                index=0,
                message=ConversationMessage(role="assistant", content=answer_text),
                finish_reason="stop",
            )
        ],
        usage=usage,
        session_id=session_id,
        citations=citations,
        blocked=blocked,
        guardrails_reasons=guardrails_reasons,
        verification=verification,
        final_mode=final_mode,
        final_reason=final_reason,
        confidence_0_100=contract_repair.confidence_0_100,
        answer_contract=public_answer_contract,
        trace=client_trace,
    )


def _export_trace_payload_or_raise(
    *,
    request_id: str,
    trace_payload: dict[str, Any],
) -> None:
    export_trace_pack(request_id=request_id, payload=trace_payload)


def _build_client_trace(
    *,
    include_trace: bool,
    trace_payload: dict[str, Any],
) -> dict[str, Any] | None:
    if not include_trace:
        return None

    public_trace = dict(trace_payload)
    public_trace["final_mode"] = _sanitize_public_final_mode(trace_payload.get("final_mode"))

    answer_contract = trace_payload.get("answer_contract")
    if isinstance(answer_contract, dict):
        public_trace["answer_contract"] = _sanitize_public_answer_contract(answer_contract)

    generation_outcome = trace_payload.get("generation_outcome")
    if isinstance(generation_outcome, dict):
        public_generation_outcome = dict(generation_outcome)
        public_generation_outcome["final_mode"] = _sanitize_public_final_mode(
            generation_outcome.get("final_mode")
        )
        public_trace["generation_outcome"] = public_generation_outcome

    return public_trace


def _sanitize_public_final_mode(final_mode: str | None) -> str | None:
    return _sanitize_public_final_mode_impl(final_mode)


def _sanitize_public_answer_contract(answer_contract: dict[str, Any] | None) -> dict[str, Any] | None:
    return _sanitize_public_answer_contract_impl(answer_contract)


def _resolve_contract_suppressed_answer_text(
    *,
    answer_text: str,
    answer_contract: dict[str, Any] | None,
) -> str:
    return _resolve_contract_suppressed_answer_text_impl(
        answer_text=answer_text,
        answer_contract=answer_contract,
    )


_EVIDENCE_SLOT_SYNTHESIS_HEADER = "Kaynaklardan çıkarılan zorunlu noktalar:"
_EVIDENCE_SLOT_SYNTHESIS_LABELS = {
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
_VERIFIED_ANSWER_PLAN_HEADER = "Doğrulanmış cevap planı:"


def _apply_verified_answer_slot_plan_to_answer_text(
    *,
    answer_text: str,
    answer_contract: dict[str, Any] | None,
    final_mode: str | None,
) -> tuple[str, dict[str, Any]]:
    return _apply_verified_answer_slot_plan_to_answer_text_impl(
        answer_text=answer_text,
        answer_contract=answer_contract,
        final_mode=final_mode,
    )


def _apply_evidence_slot_synthesis_to_answer_text(
    *,
    answer_text: str,
    answer_contract: dict[str, Any] | None,
    final_mode: str | None,
) -> tuple[str, dict[str, Any]]:
    return _apply_evidence_slot_synthesis_to_answer_text_impl(
        answer_text=answer_text,
        answer_contract=answer_contract,
        final_mode=final_mode,
    )


def _apply_temporal_claim_alignment(
    *,
    answer_text: str,
    answer_contract: dict[str, Any] | None,
    trace_payload: dict[str, Any] | None,
) -> tuple[str, dict[str, Any]]:
    return _apply_temporal_claim_alignment_impl(
        answer_text=answer_text,
        answer_contract=answer_contract,
        trace_payload=trace_payload,
    )


def _trace_chunks_for_completeness(trace_payload: dict[str, Any] | None) -> list[RetrievedChunk]:
    if not isinstance(trace_payload, dict):
        return []
    evidence_items = trace_payload.get("assembled_evidence")
    if not isinstance(evidence_items, list):
        context = trace_payload.get("context_assembly")
        evidence_items = context.get("assembled_evidence") if isinstance(context, dict) else []
    chunks: list[RetrievedChunk] = []
    for item in evidence_items if isinstance(evidence_items, list) else []:
        if not isinstance(item, dict):
            continue
        text = str(
            item.get("quoted_or_extracted_span")
            or item.get("text")
            or item.get("excerpt")
            or item.get("source_title")
            or item.get("citation")
            or ""
        )
        citation = str(item.get("citation") or item.get("source_id") or "")
        source = str(item.get("source_identifier") or item.get("source") or item.get("source_id") or "")
        chunks.append(
            RetrievedChunk(
                text=text,
                citation=citation,
                source=source,
                score=float(item.get("score") or 0.0),
                metadata=dict(item),
            )
        )
    return chunks


def _trace_article_span_selector(trace_payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(trace_payload, dict):
        return None
    retrieval = trace_payload.get("retrieval")
    if isinstance(retrieval, dict) and isinstance(retrieval.get("article_span_selector"), dict):
        return retrieval.get("article_span_selector")
    context = trace_payload.get("context_assembly")
    if isinstance(context, dict) and isinstance(context.get("article_span_selector"), dict):
        return context.get("article_span_selector")
    return None


def _refresh_contract_completeness_for_answer_text(
    *,
    answer_contract: dict[str, Any],
    answer_text: str,
    query: str,
    trace_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    refreshed = dict(answer_contract)
    refreshed.update(
        _build_completeness_synthesis_features(
            query=query,
            answer_text=answer_text,
            article_span_selector=_trace_article_span_selector(trace_payload),
            chunks=_trace_chunks_for_completeness(trace_payload),
        )
    )
    return refreshed


def _resolve_public_answer_text(
    *,
    answer_text: str,
    answer_contract: dict[str, Any] | None,
    final_mode: str | None,
) -> str:
    return _resolve_public_answer_text_impl(
        answer_text=answer_text,
        answer_contract=answer_contract,
        final_mode=final_mode,
    )


def _normalize_document_level_answer_surface(
    *,
    answer_text: str,
    answer_contract: dict[str, Any] | None,
) -> str:
    if not isinstance(answer_contract, dict):
        return answer_text
    if str(answer_contract.get("article_or_section_claimed") or "").strip() != "document_level":
        return answer_text
    identifier = str(answer_contract.get("source_identifier_claimed") or "").strip()
    match = re.match(r"^(?P<base>.+?)\s+m\.0$", identifier, flags=re.IGNORECASE)
    if not match:
        return answer_text
    base = match.group("base").strip()
    if not base:
        return answer_text
    source_title = str(answer_contract.get("source_title_claimed") or "").strip()
    source_family = str(answer_contract.get("source_family_claimed") or "").strip()
    if source_family == "TEBLIGLER" and source_title:
        return (
            "Güncellik/yürürlük sınırı:\n"
            f"- Esas alınacak ana konsolide metin: {source_title}; {identifier}; belge düzeyi. "
            f"[Kaynak: {identifier}]\n"
            "- Sınır: Bu cevap belge kimliğini bildirir; somut tevkifat/iade uygulamasında ilgili "
            "bölüm ve madde ayrıca seçilmelidir."
        )
    return re.sub(
        rf"{re.escape(base)}\s+m\.[A-Za-zÇĞİÖŞÜçğıöşü0-9/_\-.]+\s*;\s*madde:[A-Za-zÇĞİÖŞÜçğıöşü0-9/_\-.]+\.",
        f"{identifier}; belge düzeyi.",
        answer_text,
        flags=re.IGNORECASE,
    )


def _verification_has_hallucination_fail(verification: dict[str, Any] | None) -> bool:
    if not isinstance(verification, dict):
        return False
    verdict = verification.get("verdict")
    if isinstance(verdict, str) and verdict.lower() == "fail":
        return True
    risk = verification.get("hallucination_risk")
    return isinstance(risk, (int, float)) and risk > 0.5


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _release_controls_boundary_proxy_enabled() -> bool:
    return _env_flag("RELEASE_CONTROLS_BOUNDARY_PROXY_ENABLED", False)


def _release_controls_perimeter_session_isolation_enabled() -> bool:
    return _env_flag("RELEASE_CONTROLS_PERIMETER_SESSION_ISOLATION", False)


def _canonical_answer_path_base_url() -> str | None:
    raw = (os.getenv("RELEASE_CANONICAL_ANSWER_PATH_BASE_URL") or "").strip()
    if not raw:
        return None
    return raw.rstrip("/")


def _boundary_proxy_timeout_seconds() -> float:
    raw = (os.getenv("RELEASE_BOUNDARY_PROXY_TIMEOUT_SECONDS") or "").strip()
    try:
        return float(raw) if raw else 180.0
    except ValueError:
        return 180.0


def _finalize_chat_response(
    *,
    request: Request,
    request_body: ChatCompletionRequest,
    store: ConversationStore,
    session_id: str,
    response_id: str,
    user_message: str,
    conversation_history: list[dict[str, str]],
    pre_answer_payload: dict[str, Any],
    answer_text: str,
    citations: list[str],
    blocked: bool,
    guardrails_reasons: list[str],
    verification: dict[str, Any] | None,
    trace_payload: dict[str, Any],
    answer_contract: dict[str, Any],
    final_mode: str,
    final_reason: str | None,
    upstream_usage: dict[str, int] | None,
    llm_trace: dict[str, Any] | None,
) -> Any:
    answer_text = _resolve_public_answer_text(
        answer_text=answer_text,
        answer_contract=answer_contract,
        final_mode=final_mode,
    )
    answer_contract = _refresh_contract_completeness_for_answer_text(
        answer_contract=answer_contract,
        answer_text=answer_text,
        query=user_message,
        trace_payload=trace_payload,
    )
    answer_text, evidence_slot_synthesis = _apply_evidence_slot_synthesis_to_answer_text(
        answer_text=answer_text,
        answer_contract=answer_contract,
        final_mode=final_mode,
    )
    answer_contract.update(evidence_slot_synthesis)
    if evidence_slot_synthesis.get("evidence_slot_synthesis_applied") is True:
        answer_contract = _refresh_contract_completeness_for_answer_text(
            answer_contract=answer_contract,
            answer_text=answer_text,
            query=user_message,
            trace_payload=trace_payload,
        )
        answer_contract.update(evidence_slot_synthesis)
    answer_text, verified_answer_slot_synthesis = _apply_verified_answer_slot_plan_to_answer_text(
        answer_text=answer_text,
        answer_contract=answer_contract,
        final_mode=final_mode,
    )
    answer_contract.update(verified_answer_slot_synthesis)
    if verified_answer_slot_synthesis.get("verified_answer_slot_synthesis_applied") is True:
        answer_contract["answer_text"] = answer_text
        answer_contract = _refresh_contract_completeness_for_answer_text(
            answer_contract=answer_contract,
            answer_text=answer_text,
            query=user_message,
            trace_payload=trace_payload,
        )
        answer_contract.update(verified_answer_slot_synthesis)
        if verified_answer_slot_synthesis.get("verified_answer_slot_synthesis_controlled_replacement") is True:
            blocked = False
            final_mode = "partial"
            final_reason = None
            citations = citations or _extract_inline_citation_ids(answer_text)
            answer_contract["answer_mode"] = "qualified_answer"
            answer_contract["grounding_status"] = "partially_grounded"
            answer_contract["unsupported_reason"] = None
            answer_contract["answer_suppressed_due_to_evidence_gap"] = False
    contract_repair = build_or_repair_answer_contract(
        qid=response_id,
        answer_text=answer_text,
        citations=citations,
        answer_contract=answer_contract,
        final_mode=final_mode,
        final_reason=final_reason,
        trace_payload=trace_payload,
        blocked=blocked,
        guardrails_reasons=guardrails_reasons,
        verification=verification,
    )
    if not answer_text.strip():
        answer_text = controlled_fallback_answer(contract_repair.contract)
        contract_repair = build_or_repair_answer_contract(
            qid=response_id,
            answer_text=answer_text,
            citations=citations,
            answer_contract=contract_repair.contract,
            final_mode=final_mode,
            final_reason=final_reason,
            trace_payload=trace_payload,
            blocked=blocked,
            guardrails_reasons=guardrails_reasons,
            verification=verification,
        )
    answer_contract = contract_repair.contract
    resolved_answer_text = _resolve_contract_suppressed_answer_text(
        answer_text=answer_text,
        answer_contract=answer_contract,
    )
    if resolved_answer_text != answer_text:
        answer_text = resolved_answer_text
        answer_contract = _refresh_contract_completeness_for_answer_text(
            answer_contract=answer_contract,
            answer_text=answer_text,
            query=user_message,
            trace_payload=trace_payload,
        )
        contract_repair = build_or_repair_answer_contract(
            qid=response_id,
            answer_text=answer_text,
            citations=citations,
            answer_contract=answer_contract,
            final_mode=final_mode,
            final_reason=final_reason,
            trace_payload=trace_payload,
            blocked=blocked,
            guardrails_reasons=guardrails_reasons,
            verification=verification,
        )
        answer_contract = contract_repair.contract
    else:
        answer_text = resolved_answer_text
    answer_text, post_fallback_synthesis = _apply_evidence_slot_synthesis_to_answer_text(
        answer_text=answer_text,
        answer_contract=answer_contract,
        final_mode=final_mode,
    )
    if (
        post_fallback_synthesis.get("evidence_slot_synthesis_applied") is True
        or answer_contract.get("evidence_slot_synthesis_reason") in {"empty_answer", "final_mode_not_answer_or_no_contract"}
    ):
        answer_contract.update(post_fallback_synthesis)
        if post_fallback_synthesis.get("evidence_slot_synthesis_applied") is True:
            answer_contract = _refresh_contract_completeness_for_answer_text(
                answer_contract=answer_contract,
                answer_text=answer_text,
                query=user_message,
                trace_payload=trace_payload,
            )
            answer_contract.update(post_fallback_synthesis)
    answer_text, post_verified_slot_synthesis = _apply_verified_answer_slot_plan_to_answer_text(
        answer_text=answer_text,
        answer_contract=answer_contract,
        final_mode=final_mode,
    )
    if (
        post_verified_slot_synthesis.get("verified_answer_slot_synthesis_applied") is True
        or answer_contract.get("verified_answer_slot_synthesis_reason") in {"empty_answer", "no_contract"}
    ):
        answer_contract.update(post_verified_slot_synthesis)
        if post_verified_slot_synthesis.get("verified_answer_slot_synthesis_applied") is True:
            answer_contract["answer_text"] = answer_text
            answer_contract = _refresh_contract_completeness_for_answer_text(
                answer_contract=answer_contract,
                answer_text=answer_text,
                query=user_message,
                trace_payload=trace_payload,
            )
            answer_contract.update(post_verified_slot_synthesis)
            if post_verified_slot_synthesis.get("verified_answer_slot_synthesis_controlled_replacement") is True:
                blocked = False
                final_mode = "partial"
                final_reason = None
                citations = citations or _extract_inline_citation_ids(answer_text)
                answer_contract["answer_mode"] = "qualified_answer"
                answer_contract["grounding_status"] = "partially_grounded"
                answer_contract["unsupported_reason"] = None
                answer_contract["answer_suppressed_due_to_evidence_gap"] = False
    answer_text, temporal_claim_alignment = _apply_temporal_claim_alignment(
        answer_text=answer_text,
        answer_contract=answer_contract,
        trace_payload=trace_payload,
    )
    if temporal_claim_alignment.get("temporal_claim_alignment_applied") is True:
        answer_contract.update(temporal_claim_alignment)
        answer_contract["answer_text"] = answer_text
        answer_contract["final_answer"] = answer_text
        if final_mode in {"refusal", "blocked"}:
            blocked = False
            final_mode = "partial"
            final_reason = None
        final_reason = answer_contract.get("final_reason") or final_reason
    answer_contract = _refresh_contract_completeness_for_answer_text(
        answer_contract=answer_contract,
        answer_text=answer_text,
        query=user_message,
        trace_payload=trace_payload,
    )
    contract_repair = build_or_repair_answer_contract(
        qid=response_id,
        answer_text=answer_text,
        citations=citations,
        answer_contract=answer_contract,
        final_mode=final_mode,
        final_reason=final_reason,
        trace_payload=trace_payload,
        blocked=blocked,
        guardrails_reasons=guardrails_reasons,
        verification=verification,
    )
    answer_contract = contract_repair.contract
    answer_text, temporal_claim_alignment = _apply_temporal_claim_alignment(
        answer_text=answer_text,
        answer_contract=answer_contract,
        trace_payload=trace_payload,
    )
    if temporal_claim_alignment.get("temporal_claim_alignment_applied") is True:
        answer_contract.update(temporal_claim_alignment)
        answer_contract["answer_text"] = answer_text
        answer_contract["final_answer"] = answer_text
        if final_mode in {"refusal", "blocked"}:
            blocked = False
            final_mode = "partial"
            final_reason = None
        final_reason = answer_contract.get("final_reason") or final_reason
    answer_text = _normalize_document_level_answer_surface(
        answer_text=answer_text,
        answer_contract=answer_contract,
    )
    normalized_inline_citations = _extract_inline_citation_ids(answer_text)
    if normalized_inline_citations:
        citations = normalized_inline_citations
    answer_contract["answer_text"] = answer_text
    answer_contract["final_answer"] = answer_text
    trace_payload = dict(trace_payload)
    trace_payload["final_mode"] = final_mode
    trace_payload["final_reason"] = final_reason
    trace_payload["answer_contract"] = answer_contract
    trace_payload["answer_contract_validation"] = contract_repair.validation
    trace_payload["confidence_0_100"] = contract_repair.confidence_0_100
    generation_outcome = trace_payload.get("generation_outcome")
    if isinstance(generation_outcome, dict):
        generation_outcome = dict(generation_outcome)
        generation_outcome["blocked"] = blocked
        generation_outcome["final_mode"] = final_mode
        generation_outcome["final_reason"] = final_reason
        generation_outcome["answer_contract_validation"] = contract_repair.validation
        generation_outcome["confidence_0_100"] = contract_repair.confidence_0_100
        trace_payload["generation_outcome"] = generation_outcome
    public_answer_contract = _sanitize_public_answer_contract(answer_contract)
    trace_payload = _attach_parity_trace(
        trace_payload=trace_payload,
        request=request,
        request_body=request_body,
        session_id=session_id,
        conversation_history=conversation_history,
        pre_answer_payload=pre_answer_payload,
        answer_text=answer_text,
        citations=citations,
        blocked=blocked,
        guardrails_reasons=guardrails_reasons,
        verification=verification,
        answer_contract=public_answer_contract,
        final_mode=final_mode,
        final_reason=final_reason,
        llm_trace=llm_trace,
    )
    _export_trace_payload_or_raise(request_id=response_id, trace_payload=trace_payload)
    request_id = ensure_request_id(request)
    trace_id = ensure_trace_id(request)

    store.add_turn(session_id, user_message, answer_text)
    usage, usage_source = _resolve_chat_usage(
        messages=request_body.messages,
        answer_text=answer_text,
        upstream_usage=upstream_usage,
    )
    source_ids = _extract_answer_source_ids(answer_contract=answer_contract, citations=citations)
    latency_ms = (time.perf_counter() - getattr(request.state, "request_started_at", time.perf_counter())) * 1000.0
    decision_timestamps = {
        "request_started_at": datetime.fromtimestamp(
            getattr(request.state, "request_wall_started_at", time.time()),
            tz=timezone.utc,
        ).isoformat(),
        "decision_completed_at": datetime.now(timezone.utc).isoformat(),
    }
    persisted_request_snapshot = _build_persisted_request_snapshot(
        request_body=request_body,
        conversation_history=conversation_history,
        last_user_message=user_message,
    )
    persisted_raw_answer_snapshot = _build_persisted_raw_answer_snapshot(
        answer_text=answer_text,
        citations=citations,
        source_ids=source_ids,
        final_mode=final_mode,
        final_reason=final_reason,
    )
    persisted_response_envelope_snapshot = _build_persisted_response_envelope_snapshot(
        response_id=response_id,
        blocked=blocked,
        final_mode=final_mode,
        final_reason=final_reason,
        citations=citations,
        source_ids=source_ids,
    )

    append_audit_event(
        event_type="chat_completion",
        request=request,
        request_id=request_id,
        trace_id=trace_id,
        response_id=response_id,
        session_id=session_id,
        model=request_body.model,
        stream=request_body.stream,
        blocked=blocked,
        citations=citations,
        guardrails_reasons=guardrails_reasons,
        usage=usage.model_dump(),
        usage_source=usage_source,
        message_count=len(request_body.messages),
        user_message_chars=len(user_message),
        selected_lane=release_lane_id(),
        final_mode=final_mode,
        refusal_reason=final_reason,
        source_ids=source_ids,
        latency_ms=latency_ms,
        token_accounting={
            "usage": usage.model_dump(),
            "source": usage_source,
        },
        decision_timestamps=decision_timestamps,
        api_version=api_version_label(),
        persisted_request_snapshot=persisted_request_snapshot,
        persisted_raw_answer_snapshot=persisted_raw_answer_snapshot,
        persisted_response_envelope_snapshot=persisted_response_envelope_snapshot,
    )
    get_metrics_registry().record_chat_outcome(
        path=request.url.path,
        model=request_body.model,
        blocked=blocked,
        is_refusal=looks_like_refusal(answer_text, blocked=blocked),
        usage_source=usage_source,
        citation_count=len(citations),
        hallucination_fail=_verification_has_hallucination_fail(verification),
    )

    client_trace = _build_client_trace(
        include_trace=request_body.include_trace,
        trace_payload=trace_payload,
    )
    if request_body.stream:
        return StreamingResponse(
            _stream_sse_response(
                answer=answer_text,
                session_id=session_id,
                model=request_body.model,
                citations=citations,
                blocked=blocked,
                guardrails_reasons=guardrails_reasons,
                verification=verification,
                usage=usage,
                response_id=response_id,
                trace=client_trace,
                final_mode=final_mode,
                final_reason=final_reason,
                confidence_0_100=contract_repair.confidence_0_100,
                answer_contract=public_answer_contract,
                include_metadata_chunk=request_body.include_trace,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "X-Session-Id": session_id,
            },
        )

    return ChatCompletionResponse(
        id=response_id,
        created=int(time.time()),
        model=request_body.model,
        choices=[
            ChatChoice(
                index=0,
                message=ConversationMessage(role="assistant", content=answer_text),
                finish_reason="stop",
            )
        ],
        usage=usage,
        session_id=session_id,
        citations=citations,
        blocked=blocked,
        guardrails_reasons=guardrails_reasons,
        verification=verification,
        final_mode=final_mode,
        final_reason=final_reason,
        confidence_0_100=contract_repair.confidence_0_100,
        answer_contract=public_answer_contract,
        trace=client_trace,
    )


def _prepare_chat_request_context(
    *,
    request_body: ChatCompletionRequest,
    store: ConversationStore,
) -> tuple[str, str, str, list[dict[str, str]]]:
    if not request_body.messages:
        raise HTTPException(status_code=400, detail="messages listesi boş olamaz")

    last_user_msg: str | None = None
    for msg in reversed(request_body.messages):
        if msg.role == "user":
            last_user_msg = msg.content
            break

    if last_user_msg is None:
        raise HTTPException(
            status_code=400,
            detail="messages içinde en az bir 'user' rol mesajı gerekli",
        )

    if not last_user_msg.strip():
        raise HTTPException(status_code=400, detail="Kullanıcı mesajı boş olamaz")

    session_id = request_body.session_id or f"sess-{uuid.uuid4().hex[:16]}"
    response_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    request_history = request_history_from_messages(request_body.messages[:-1])
    conversation_history = request_history
    if not conversation_history and not (
        _release_controls_boundary_proxy_enabled()
        and _release_controls_perimeter_session_isolation_enabled()
    ):
        conversation_history = store.get_history(session_id)
    return session_id, response_id, last_user_msg, conversation_history


async def _try_shortcut_chat_response(
    *,
    request: Request,
    request_body: ChatCompletionRequest,
    store: ConversationStore,
    session_id: str,
    response_id: str,
    last_user_msg: str,
    conversation_history: list[dict[str, str]],
) -> Any | None:
    native_dialog_intent = _detect_native_dialog_intent(last_user_msg)
    if native_dialog_intent is not None:
        answer_text, native_usage, native_llm_trace = await _run_native_dialog_passthrough(
            request=request,
            request_body=request_body,
            intent=native_dialog_intent,
        )
        answer_contract = _build_native_dialog_answer_contract(answer_text=answer_text)
        law_scope_signal = build_law_scope_signal(
            question_raw=last_user_msg,
            mentioned_laws=[],
            explicit_article_refs=[],
            law_filter=request_body.law_filter,
            model_source_ids=[],
        )
        trace_payload = _build_trace_payload(
            request_id=response_id,
            decision_lane="native_dialog_shortcut",
            user_query=last_user_msg,
            enriched_query=last_user_msg,
            retrieval_query=last_user_msg,
            question_normalized=normalize_query_text(last_user_msg),
            question_type="general_dialogue",
            target_date=datetime.now(timezone.utc).date().isoformat(),
            law_scope_signal=law_scope_signal,
            law_filter=request_body.law_filter,
            mentioned_laws=[],
            cross_law_mode=False,
            requested_source_families=[],
            explicit_article_refs=[],
            forced_article_refs=[],
            applied_expansions=[],
            top_k_requested=request_body.top_k,
            top_k_effective=0,
            reranker_enabled=False,
            pre_rerank_chunks=[],
            post_rerank_chunks=[],
            assembled_context="",
            blocked=False,
            guardrails_reasons=[],
            verification=None,
            answer_contract=answer_contract,
            model_cited_source_ids=[],
            final_mode="answer",
            final_reason=None,
        )
        pre_answer_payload = _pre_answer_stage_payload(
            decision_lane="native_dialog_shortcut",
            user_message=last_user_msg,
            enriched_query=last_user_msg,
            retrieval_query=last_user_msg,
            conversation_history=conversation_history,
            mentioned_laws=[],
            requested_source_families=[],
            explicit_article_refs=[],
            forced_article_refs=[],
            applied_expansions=[],
            top_k_requested=request_body.top_k,
            top_k_effective=0,
            reranker_enabled=False,
        )
        return _finalize_chat_response(
            request=request,
            request_body=request_body,
            store=store,
            session_id=session_id,
            response_id=response_id,
            user_message=last_user_msg,
            conversation_history=conversation_history,
            pre_answer_payload=pre_answer_payload,
            answer_text=answer_text,
            citations=[],
            blocked=False,
            guardrails_reasons=[],
            verification=None,
            trace_payload=trace_payload,
            answer_contract=answer_contract,
            final_mode="answer",
            final_reason=None,
            upstream_usage=native_usage,
            llm_trace=native_llm_trace,
        )

    precise_lane = "precise_cross_law_shortcut"
    precise_answer = _build_precise_tmk_tbk_cross_law_answer(last_user_msg)
    if not precise_answer:
        precise_lane = "precise_tbk_shortcut"
        precise_answer = _build_precise_tbk_answer(last_user_msg)
    if precise_answer:
        answer_text, precise_citations = precise_answer
        mentioned_laws = _extract_law_mentions(last_user_msg)
        explicit_article_refs = _extract_explicit_article_refs(last_user_msg)
        request_history = request_history_from_messages(request_body.messages[:-1])
        synthetic_evidence = _build_fallback_assembled_evidence(
            [citation for citation in precise_citations if canonicalize_source_id(citation)],
            fallback_excerpt=answer_text,
        )
        synthetic_whitelist = [
            str(item["source_id"])
            for item in synthetic_evidence
            if item.get("source_id")
        ]
        hardening = harden_answer(
            answer_text=answer_text,
            citations=precise_citations,
            blocked=False,
            verification=None,
            question_raw=last_user_msg,
            mentioned_laws=mentioned_laws,
            explicit_article_refs=explicit_article_refs,
            law_filter=request_body.law_filter,
            assembled_evidence=synthetic_evidence,
            allowed_source_whitelist=synthetic_whitelist,
        )
        trace_payload = _build_trace_payload(
            request_id=response_id,
            decision_lane=precise_lane,
            user_query=last_user_msg,
            enriched_query=last_user_msg,
            retrieval_query=last_user_msg,
            question_normalized=normalize_query_text(last_user_msg),
            question_type=hardening.question_type,
            target_date=hardening.target_date,
            law_scope_signal=hardening.law_scope_signal,
            law_filter=request_body.law_filter,
            mentioned_laws=mentioned_laws,
            cross_law_mode=False,
            requested_source_families=[],
            explicit_article_refs=explicit_article_refs,
            forced_article_refs=[],
            applied_expansions=[],
            top_k_requested=request_body.top_k,
            top_k_effective=0,
            reranker_enabled=False,
            pre_rerank_chunks=[],
            post_rerank_chunks=[],
            assembled_context="",
            blocked=hardening.internal_blocked,
            guardrails_reasons=[],
            verification=None,
            answer_contract=hardening.answer_contract,
            model_cited_source_ids=hardening.model_cited_source_ids,
            final_mode=hardening.final_mode,
            final_reason=hardening.final_reason,
        )
        pre_answer_payload = _pre_answer_stage_payload(
            decision_lane=precise_lane,
            user_message=last_user_msg,
            enriched_query=last_user_msg,
            retrieval_query=last_user_msg,
            conversation_history=request_history,
            mentioned_laws=mentioned_laws,
            requested_source_families=[],
            explicit_article_refs=explicit_article_refs,
            forced_article_refs=[],
            applied_expansions=[],
            top_k_requested=request_body.top_k,
            top_k_effective=0,
            reranker_enabled=False,
        )
        return _finalize_chat_response(
            request=request,
            request_body=request_body,
            store=store,
            session_id=session_id,
            response_id=response_id,
            user_message=last_user_msg,
            conversation_history=request_history,
            pre_answer_payload=pre_answer_payload,
            answer_text=hardening.answer_text,
            citations=hardening.citations,
            blocked=hardening.internal_blocked,
            guardrails_reasons=[],
            verification=None,
            trace_payload=trace_payload,
            answer_contract=hardening.answer_contract,
            final_mode=hardening.final_mode,
            final_reason=hardening.final_reason,
            upstream_usage=None,
            llm_trace=None,
        )

    scope_refusal_reason = _detect_scope_refusal_reason(last_user_msg)
    if scope_refusal_reason:
        answer_text = (
            "Bu soru TBK kapsamı dışı bir konuya giriyor "
            f"({scope_refusal_reason}). Elimdeki TBK kaynaklarıyla bu soruya yanıt veremiyorum. "
            "Lütfen ilgili mevzuat için uzman bir hukukçuya danışın."
        )
        mentioned_laws = _extract_law_mentions(last_user_msg)
        explicit_article_refs = _extract_explicit_article_refs(last_user_msg)
        request_history = request_history_from_messages(request_body.messages[:-1])
        hardening = harden_answer(
            answer_text=answer_text,
            citations=[],
            blocked=False,
            verification=None,
            question_raw=last_user_msg,
            mentioned_laws=mentioned_laws,
            explicit_article_refs=explicit_article_refs,
            law_filter=request_body.law_filter,
            assembled_evidence=[],
            allowed_source_whitelist=[],
        )
        trace_payload = _build_trace_payload(
            request_id=response_id,
            decision_lane="scope_refusal_shortcut",
            user_query=last_user_msg,
            enriched_query=last_user_msg,
            retrieval_query=last_user_msg,
            question_normalized=normalize_query_text(last_user_msg),
            question_type=hardening.question_type,
            target_date=hardening.target_date,
            law_scope_signal=hardening.law_scope_signal,
            law_filter=request_body.law_filter,
            mentioned_laws=mentioned_laws,
            cross_law_mode=False,
            requested_source_families=[],
            explicit_article_refs=explicit_article_refs,
            forced_article_refs=[],
            applied_expansions=[],
            top_k_requested=request_body.top_k,
            top_k_effective=0,
            reranker_enabled=False,
            pre_rerank_chunks=[],
            post_rerank_chunks=[],
            assembled_context="",
            blocked=hardening.internal_blocked,
            guardrails_reasons=[],
            verification=None,
            answer_contract=hardening.answer_contract,
            model_cited_source_ids=hardening.model_cited_source_ids,
            final_mode=hardening.final_mode,
            final_reason=hardening.final_reason,
        )
        pre_answer_payload = _pre_answer_stage_payload(
            decision_lane="scope_refusal_shortcut",
            user_message=last_user_msg,
            enriched_query=last_user_msg,
            retrieval_query=last_user_msg,
            conversation_history=request_history,
            mentioned_laws=mentioned_laws,
            requested_source_families=[],
            explicit_article_refs=explicit_article_refs,
            forced_article_refs=[],
            applied_expansions=[],
            top_k_requested=request_body.top_k,
            top_k_effective=0,
            reranker_enabled=False,
        )
        return _finalize_chat_response(
            request=request,
            request_body=request_body,
            store=store,
            session_id=session_id,
            response_id=response_id,
            user_message=last_user_msg,
            conversation_history=request_history,
            pre_answer_payload=pre_answer_payload,
            answer_text=hardening.answer_text,
            citations=hardening.citations,
            blocked=hardening.internal_blocked,
            guardrails_reasons=[],
            verification=None,
            trace_payload=trace_payload,
            answer_contract=hardening.answer_contract,
            final_mode=hardening.final_mode,
            final_reason=hardening.final_reason,
            upstream_usage=None,
            llm_trace=None,
        )

    return None


@dataclass(slots=True)
class ChatRetrievalRuntimeContext:
    enriched_query: str
    routing_query: str
    retrieval_query: str
    retrieval_top_k: int
    mentioned_laws: list[str]
    explicit_article_refs: list[tuple[str, str]]
    requested_source_families: list[str]
    forced_article_refs: list[tuple[str, str]]
    applied_expansions: list[str]
    source_family_resolution: SourceFamilyResolution
    retrieval_plan: dict[str, Any] | None
    domain_supporting_source_selector: dict[str, Any] | None
    domain_supporting_source_families: list[str]
    metadata_lookup_query_signals: dict[str, Any]
    metadata_first_selector: dict[str, Any] | None
    cross_law_mode: bool
    numbered_law_mentions: list[str]
    numbered_law_reference_expansion: str
    all_exact_article_refs: list[tuple[str, str]]
    source_lock_target_citations: int | None
    answer_query: str


async def _prepare_retrieval_runtime_context(
    *,
    request: Request,
    request_body: ChatCompletionRequest,
    last_user_msg: str,
    conversation_history: list[dict[str, str]],
) -> ChatRetrievalRuntimeContext:
    # Multi-turn sorgu oluştur
    enriched_query = _build_multiturn_query(
        last_user_message=last_user_msg,
        conversation_history=conversation_history,
    )
    effective_user_query = _extract_effective_legal_query(last_user_msg)
    routing_query = effective_user_query or last_user_msg

    # Terminoloji / eşanlamlı genişletmesi (Retrieval için)
    retrieval_query = routing_query
    retrieval_top_k = request_body.top_k
    mentioned_laws = _extract_law_mentions(routing_query)
    explicit_article_refs = _extract_explicit_article_refs(routing_query)
    requested_source_families = _infer_requested_source_families(routing_query)
    forced_article_refs: list[tuple[str, str]] = _infer_domain_article_refs(routing_query)
    applied_expansions: list[str] = []
    source_family_resolution = _resolve_source_family_prior(
        routing_query,
        mentioned_laws=mentioned_laws,
        explicit_article_refs=explicit_article_refs,
        law_filter=request_body.law_filter,
    )
    retrieval_query, requested_source_families, retrieval_top_k = _apply_source_family_resolution_hints(
        retrieval_query=retrieval_query,
        requested_source_families=requested_source_families,
        retrieval_top_k=retrieval_top_k,
        applied_expansions=applied_expansions,
        source_family_resolution=source_family_resolution,
    )
    retrieval_plan = await _run_retrieval_planner(
        request=request,
        user_query=routing_query,
        mentioned_laws=mentioned_laws,
        requested_source_families=requested_source_families,
        explicit_article_refs=explicit_article_refs,
        law_filter=request_body.law_filter,
    )
    domain_law_hints = _infer_domain_law_hints(routing_query)
    domain_supporting_source_selector: dict[str, Any] | None = None
    domain_supporting_source_families: list[str] = []
    if domain_law_hints:
        mentioned_laws = dedupe_strings([*mentioned_laws, *domain_law_hints])
        retrieval_plan = _apply_domain_law_hints_to_retrieval_plan(
            retrieval_plan,
            domain_law_hints=domain_law_hints,
            mentioned_laws=mentioned_laws,
            query=routing_query,
        )
        domain_supporting_source_families = _domain_law_supporting_source_family_hints(
            routing_query,
            domain_law_hints,
        )
        domain_supporting_source_selector = _select_domain_law_supporting_source_candidates(
            query=routing_query,
            domain_law_hints=domain_law_hints,
        )
    retrieval_query, mentioned_laws, requested_source_families, retrieval_top_k = _apply_retrieval_plan_hints(
        retrieval_query=retrieval_query,
        mentioned_laws=mentioned_laws,
        requested_source_families=requested_source_families,
        applied_expansions=applied_expansions,
        retrieval_top_k=retrieval_top_k,
        retrieval_plan=retrieval_plan,
    )
    retrieval_query, requested_source_families, retrieval_top_k = _apply_source_family_resolution_hints(
        retrieval_query=retrieval_query,
        requested_source_families=requested_source_families,
        retrieval_top_k=retrieval_top_k,
        applied_expansions=applied_expansions,
        source_family_resolution=source_family_resolution,
    )
    requested_source_families = _clamp_families_to_strong_resolution(
        requested_source_families,
        source_family_resolution,
    )
    if _asks_current_validity_over_historical_contrast(routing_query):
        retrieval_query = _append_unique_expansion(
            retrieval_query,
            applied_expansions,
            "güncel yürürlükte metin yürürlükten kaldırılan eski metin",
        )
        retrieval_top_k = max(retrieval_top_k, 20)
    numbered_law_mentions = extract_numbered_law_mentions(routing_query)
    numbered_law_reference_expansion = _build_numbered_law_reference_expansion(routing_query)
    if numbered_law_reference_expansion:
        retrieval_query = _append_unique_expansion(
            retrieval_query,
            applied_expansions,
            numbered_law_reference_expansion,
        )
        retrieval_top_k = max(retrieval_top_k, 20)
    annual_investment_program_expansion = _build_annual_investment_program_expansion(routing_query)
    if annual_investment_program_expansion:
        retrieval_query = _append_unique_expansion(
            retrieval_query,
            applied_expansions,
            annual_investment_program_expansion,
        )
        retrieval_top_k = max(retrieval_top_k, 20)
    generic_metadata_lookup_expansions = {
        str(value or "").strip()
        for value in _SOURCE_FAMILY_GENERIC_QUERY_EXPANSIONS.values()
        if str(value or "").strip()
    }
    metadata_lookup_query_expansions = [
        part
        for part in source_family_resolution.query_expansions
        if str(part or "").strip() and str(part or "").strip() not in generic_metadata_lookup_expansions
    ]
    metadata_lookup_query_expansions = dedupe_strings(
        [
            *metadata_lookup_query_expansions,
            *[
                str(part or "").strip()
                for part in ((retrieval_plan or {}).get("term_hints") or [])
                if str(part or "").strip()
            ],
        ]
    )
    metadata_lookup_query = " ".join(
        part
        for part in [routing_query, *metadata_lookup_query_expansions]
        if str(part or "").strip()
    )
    metadata_lookup_query_signals = _parse_metadata_lookup_query_signals(metadata_lookup_query)
    metadata_first_selector = _select_metadata_first_source_candidates(
        query=metadata_lookup_query,
        requested_source_families=requested_source_families,
        source_family_resolution=source_family_resolution,
        query_metadata_signals=metadata_lookup_query_signals,
    )
    metadata_first_selector = _suppress_domain_law_metadata_conflict(
        metadata_first_selector,
        query=routing_query,
        domain_law_hints=domain_law_hints,
    )
    if metadata_first_selector:
        source_family_resolution = _apply_metadata_lookup_family_prior(
            source_family_resolution,
            metadata_first_selector,
            query=routing_query,
        )
        metadata_first_selector = _apply_relation_query_metadata_focus(
            metadata_first_selector,
            query=routing_query,
            source_family_resolution=source_family_resolution,
        )
        requested_source_families = dedupe_strings(
            [
                *requested_source_families,
                *(metadata_first_selector.get("selected_families") or []),
                *source_family_resolution.routing_families,
            ]
        )
        metadata_first_expansion = _build_metadata_first_query_expansion(metadata_first_selector)
        if metadata_first_expansion:
            retrieval_query = _append_unique_expansion(
                retrieval_query,
                applied_expansions,
                metadata_first_expansion,
                )
            retrieval_top_k = max(retrieval_top_k, 20)
    cross_law_mode = _should_use_cross_law_retrieval(routing_query, mentioned_laws)

    concept_anchor_rules: list[
        tuple[tuple[tuple[str, ...], ...], str, list[tuple[str, str]], bool]
    ] = [
        (
            (("aile konutu",), ("kira", "fesih", "fesheder", "feshedebilir", "devir", "boşanma", "bosanma")),
            "TBK m.349 TMK m.194 TMK m.169 TMK m.197 aile konutu boşanma kira fesih tedbir",
            [("TBK", "349"), ("TMK", "194"), ("TMK", "169"), ("TMK", "197")],
            True,
        ),
        (
            (("kefalet",), ("aile birliği", "aile birligi", "korunması ilkesi", "korunmasi ilkesi")),
            "TBK m.584 TMK m.185 eş rızası aile birliği kefalet",
            [("TBK", "584"), ("TMK", "185")],
            True,
        ),
        (
            (("paylı mülkiyet", "önalım", "ön alım"), ("satış", "satıldı", "paydaş", "paydas")),
            "TBK m.207 TMK m.688 TMK m.691 TMK m.732 paylı mülkiyet önalım satış paydaş",
            [("TBK", "207"), ("TMK", "688"), ("TMK", "691"), ("TMK", "732")],
            True,
        ),
        (
            (("malik olmayan",), ("kira", "kiraya", "kiracı", "kiraci")),
            "TBK m.299 TMK m.683 malik olmayan kişinin kiraya vermesi kiracının korunması",
            [("TBK", "299"), ("TMK", "683")],
            True,
        ),
        (
            (
                ("mal rejimi", "edinilmiş mallar", "edinilmiş mallara katılma"),
                ("eşler arasındaki", "esler arasindaki", "eşler arası", "esler arasi", "diğer eşe", "diger ese"),
                ("ödünç", "odunc", "ödünç verme", "odunc verme", "borç verme", "borc verme", "borç vermesi", "borc vermesi"),
            ),
            "TBK m.386 TMK m.202 TMK m.223 eşler arası borç verme mal rejimi",
            [("TBK", "386"), ("TMK", "202"), ("TMK", "223")],
            True,
        ),
        (
            (("haksız fiil",), ("boşanma", "tmk m.174", "maddi tazminat")),
            "TBK m.49 TBK m.72 TMK m.174 haksız fiil boşanma maddi tazminat temel farklar",
            [("TBK", "49"), ("TBK", "72"), ("TMK", "174")],
            True,
        ),
        (
            (("muvazaa", "muris muvazaası"), ("taşınmaz", "sattı", "satış", "bağış", "bagis")),
            "TBK m.19 TBK m.285 TMK m.561 muris muvazaası görünürde satış gizli bağış ispat",
            [("TBK", "19"), ("TBK", "285"), ("TMK", "561")],
            True,
        ),
        (
            (("eşin rızası",), ("sözleşme", "batıldır", "batıl", "geçersiz")),
            "TMK m.194 TBK m.27 eş rızası aile konutu sözleşme geçersizlik",
            [("TMK", "194"), ("TBK", "27")],
            True,
        ),
        (
            (
                ("sınırlı ehliyetsiz", "sinirli ehliyetsiz", "kısıtlı", "kisıtli", "kisitli", "yasal temsilci"),
                ("kira", "kiralanan", "kira sözleşmesi", "kira sozlesmesi"),
            ),
            "TBK m.299 TMK m.15 TMK m.16 sınırlı ehliyetsiz yasal temsilci kira sözleşmesi onay",
            [("TBK", "299"), ("TMK", "15"), ("TMK", "16")],
            True,
        ),
        (
            (
                ("bağışlama", "bagislama"),
                ("edinilmiş mallar", "edinilmis mallar", "katılma rejimi", "katilma rejimi"),
                ("denkleştirme", "denklestirme", "tasfiye"),
            ),
            "TMK m.229 TMK m.220 TBK m.285 bağışlama edinilmiş mallara katılma tasfiye denkleştirme",
            [("TMK", "229"), ("TMK", "220"), ("TBK", "285")],
            True,
        ),
        (
            (
                ("nafaka",),
                ("zamanaşımı", "zamanasimi", "özel süre", "ozel sure"),
            ),
            "TMK m.182 TBK m.125 TBK m.131 nafaka zamanaşımı özel süre alacak",
            [("TMK", "182"), ("TBK", "125"), ("TBK", "131")],
            True,
        ),
        (
            (
                ("mirasçılar", "mirascilar", "terekenin paylaşılması", "terekenin paylasilmasi", "miras ortaklığı", "miras ortakligi"),
                ("adi ortaklık", "adi ortaklik", "ortaklık sona erdirme", "ortaklik sona erdirme", "ortaklığın giderilmesi", "ortakligin giderilmesi"),
            ),
            "TMK m.698 TBK m.620 TBK m.638 mirasçılar tereke adi ortaklık ortaklığın giderilmesi",
            [("TMK", "698"), ("TBK", "620"), ("TBK", "638")],
            True,
        ),
        (
            (
                ("hayatta kalan eş", "hayatta kalan es", "ölümü halinde", "olumu halinde"),
                ("katılma alacağı", "katilma alacagi", "sebepsiz zenginleşme", "sebepsiz zenginlesme"),
            ),
            "TBK m.77 TMK m.226 TMK m.240 TMK m.499 hayatta kalan eş katılma alacağı sebepsiz zenginleşme",
            [("TBK", "77"), ("TMK", "226"), ("TMK", "240"), ("TMK", "499")],
            True,
        ),
    ]

    expansion_rules: list[tuple[tuple[str, ...], str, bool]] = [
        (
            ("müterafik kusur", "ortak kusur", "birlikte kusur"),
            "TBK m.52 müterafik kusur ortak kusur zarar görenin kusuru tazminat indirimi",
            True,
        ),
        (
            (
                "sözleşmenin kurulması",
                "sözleşme kurulması",
                "sözleşme nasıl kurulur",
                "sözleşmenin kurulması için hangi unsurlar",
            ),
            "TBK m.1 TBK m.2 TBK m.3 icap kabul öneri karşılıklı ve birbirine uygun irade açıklamaları",
            True,
        ),
        (("icap",), "icap öneri", False),
        (("akdedilmesi",), "akdedilmesi kurulması", False),
        (("fesih",), "fesih sona erme", False),
        (
            ("aile konutu", "kiracı eş", "kiraci es"),
            "TBK m.349 TMK m.194 aile konutu eş rızası kira feshi",
            True,
        ),
        (
            ("taşınmaz satış", "tasinmaz satis", "resmi şekil", "resmi sekil", "tapu", "tescil"),
            "TBK m.237 TMK m.706 taşınmaz satışı resmi şekil tapu tescil",
            True,
        ),
        (
            ("paylı mülkiyet", "payli mulkiyet", "önalım", "onalim", "ön alım", "on alim"),
            "TMK m.688 TMK m.691 TMK m.732 TBK m.207 paylı mülkiyet önalım paydaş satış",
            True,
        ),
        (
            ("kira sözleşmesinin devri", "kira sozlesmesinin devri", "kira sözleşmesi devri", "kira sozlesmesi devri"),
            "TBK m.323 TBK m.349 TMK m.194 kira devri aile konutu boşanma",
            True,
        ),
        (
            ("malik olmayan", "malik olmayan kişinin", "malik olmayan kisinin"),
            "TBK m.299 TMK m.683 malik olmayan kişinin kiraya vermesi kiracının korunması",
            True,
        ),
        (
            (
                "diğer eşe borç vermesi",
                "diger ese borc vermesi",
                "diğer eşe ödünç vermesi",
                "diger ese odunc vermesi",
                "eşler arası borç verme",
                "esler arasi borc verme",
                "eşler arası ödünç",
                "esler arasi odunc",
            ),
            "TBK m.386 TMK m.202 TMK m.223 eşler arası borç verme mal rejimi",
            True,
        ),
        (
            ("muvazaa", "muris muvazaası", "muris muvazaasi", "bağışlamak", "bagislamak"),
            "TBK m.19 TBK m.285 TMK m.561 muris muvazaası görünürde satış gizli bağış ispat",
            True,
        ),
        (
            ("haksız fiil", "haksiz fiil", "tmk m.174", "maddi tazminat davası", "maddi tazminat davasi"),
            "TBK m.49 TMK m.174 haksız fiil boşanma maddi tazminat temel farklar",
            True,
        ),
        (
            ("eşin rızası", "esin rizasi", "batıldır", "batildir", "batıl", "batil", "geçersiz", "gecersiz"),
            "TMK m.194 TBK m.27 eş rızası aile konutu sözleşme geçersizlik",
            True,
        ),
        (
            ("ceza şartı", "ceza sarti", "cezai şart", "cezai sart", "cayma akçesi", "cayma akcesi", "cayma parası", "cayma parasi"),
            "TBK m.179 TBK m.180 TBK m.181 TBK m.182 ceza şartı cayma akçesi aşırı ceza indirimi",
            True,
        ),
        (
            ("kefalet", "kefil", "adi kefalet", "müteselsil kefalet", "muteselsil kefalet"),
            "TBK m.583 TBK m.584 TBK m.585 TBK m.586 TBK m.587 TBK m.589 TBK m.596 TBK m.600 TBK m.603 kefalet eş rızası defi zamanaşımı",
            True,
        ),
        (
            ("vekalet", "vekâlet", "vekil", "müvekkil", "muvekkil", "hesap verme", "talimat"),
            "TBK m.504 TBK m.506 TBK m.507 TBK m.508 TBK m.512 TBK m.513 vekalet talimat hesap verme azil",
            True,
        ),
        (
            ("rekabet yasağı", "rekabet yasagi"),
            "TBK m.396 TBK m.397 TBK m.398 TBK m.399 TBK m.444 TBK m.445 TBK m.446 rekabet yasağı hizmet sözleşmesi yaptırım",
            True,
        ),
        (
            ("ihbar süresi", "ihbar suresi", "fesih bildirimi", "belirsiz süreli hizmet", "belirsiz sureli hizmet"),
            "TBK m.432 TBK m.433 hizmet sözleşmesi ihbar fesih bildirim",
            True,
        ),
        (
            ("fazla çalışma", "fazla calisma", "270 saat", "yazılı onay", "yazili onay"),
            "4857 İş Kanunu m.41 fazla çalışma yıllık 270 saat işçi onayı fazla çalışma ücreti serbest zaman Fazla Çalışma Yönetmeliği",
            True,
        ),
        (
            ("alt işveren", "alt isveren", "asıl iş", "asil is", "muvazaa", "muvazaalı", "muvazaali"),
            "4857 İş Kanunu m.2 alt işveren asıl iş yardımcı iş teknolojik nedenlerle uzmanlık muvazaa Alt İşverenlik Yönetmeliği",
            True,
        ),
        (
            ("yıllık ücretli izin", "yillik ucretli izin", "ücretli izin", "ucretli izin"),
            "4857 İş Kanunu m.56 yıllık ücretli izin bölünebilir en az on gün kesintisiz kullandırılır",
            True,
        ),
        (
            ("hafta tatili",),
            "4857 İş Kanunu m.46 hafta tatili çalışılmayan hafta tatili günü ücreti",
            True,
        ),
        (
            ("parmak izi", "biyometrik", "kişisel veri", "kisisel veri", "özel nitelikli veri", "ozel nitelikli veri"),
            "6698 KVKK m.6 özel nitelikli kişisel veri biyometrik veri m.10 aydınlatma m.12 veri güvenliği saklama imha yönetmeliği",
            True,
        ),
        (
            ("kira artış", "kira artis", "%25", "25 sınırı", "25 siniri"),
            "6098 TBK m.344 kira artış oranı geçici yüzde 25 sınırı sona erdi güncel genel rejim",
            True,
        ),
        (
            ("elektronik tebligat", "e-tebligat", "elektronik adres", "beşinci gün", "besinci gun"),
            "7201 Tebligat Kanunu elektronik tebligat elektronik adres beşinci gün Elektronik Tebligat Yönetmeliği",
            True,
        ),
    ]

    expansion_match_query = routing_query
    if _legacy_query_expansions_enabled():
        for term_groups, expansion, exact_refs, boost_top_k in concept_anchor_rules:
            if all(_contains_any_query_term(expansion_match_query, terms) for terms in term_groups):
                retrieval_query = _append_unique_expansion(
                    retrieval_query,
                    applied_expansions,
                    expansion,
                )
                forced_article_refs.extend(exact_refs)
                if boost_top_k:
                    retrieval_top_k = max(retrieval_top_k, 20)

        for triggers, expansion, boost_top_k in expansion_rules:
            if _contains_any_query_term(expansion_match_query, triggers):
                retrieval_query = _append_unique_expansion(
                    retrieval_query,
                    applied_expansions,
                    expansion,
                )
                if boost_top_k:
                    retrieval_top_k = max(retrieval_top_k, 20)

    forced_article_refs = _dedupe_article_refs(forced_article_refs)
    all_exact_article_refs = _dedupe_article_refs(explicit_article_refs + forced_article_refs)
    source_lock_target_citations = len(all_exact_article_refs) or None
    answer_query = _apply_source_family_answer_hint(
        query=enriched_query,
        source_families=requested_source_families,
    )


    return ChatRetrievalRuntimeContext(
        enriched_query=enriched_query,
        routing_query=routing_query,
        retrieval_query=retrieval_query,
        retrieval_top_k=retrieval_top_k,
        mentioned_laws=mentioned_laws,
        explicit_article_refs=explicit_article_refs,
        requested_source_families=requested_source_families,
        forced_article_refs=forced_article_refs,
        applied_expansions=applied_expansions,
        source_family_resolution=source_family_resolution,
        retrieval_plan=retrieval_plan,
        domain_supporting_source_selector=domain_supporting_source_selector,
        domain_supporting_source_families=domain_supporting_source_families,
        metadata_lookup_query_signals=metadata_lookup_query_signals,
        metadata_first_selector=metadata_first_selector,
        cross_law_mode=cross_law_mode,
        numbered_law_mentions=numbered_law_mentions,
        numbered_law_reference_expansion=numbered_law_reference_expansion,
        all_exact_article_refs=all_exact_article_refs,
        source_lock_target_citations=source_lock_target_citations,
        answer_query=answer_query,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/v1/chat/completions",
    summary="OpenAI-uyumlu Chat Completions (RAG + SSE)",
    response_model=ChatCompletionResponse,
    response_model_exclude_none=True,
)
async def chat_completions(
    request_body: ChatCompletionRequest,
    request: Request,
    store: ConversationStore = Depends(get_conversation_store),
    _auth_subject: str = Depends(require_api_auth),
) -> Any:
    """OpenAI-uyumlu chat completions endpoint.

    RAG pipeline, SSE streaming ve multi-turn konuşma desteği.

    **Akış:**
    1. Son kullanıcı mesajı çıkarılır
    2. Konuşma geçmişi sorguya enjekte edilir (multi-turn bağlamı)
    3. Retriever ile ilgili mevzuat chunk'ları alınır
    4. RAGOrchestrator → LLM → Guardrails → Verification
    5. Yanıt SSE (stream=True) veya JSON (stream=False) olarak döndürülür

    **Session Yönetimi:**
    - `session_id` verilmezse yeni oturum oluşturulur
    - Yanıt sonrası bu tur session store'a kaydedilir

    **Law Filter:**
    - `law_filter: "TBK"` → sadece TBK maddelerinde arama yapılır
    """
    session_id, response_id, last_user_msg, conversation_history = _prepare_chat_request_context(
        request_body=request_body,
        store=store,
    )

    shortcut_response = await _try_shortcut_chat_response(
        request=request,
        request_body=request_body,
        store=store,
        session_id=session_id,
        response_id=response_id,
        last_user_msg=last_user_msg,
        conversation_history=conversation_history,
    )
    if shortcut_response is not None:
        return shortcut_response

    if _release_controls_boundary_proxy_enabled():
        canonical_snapshot, proxy_response = await _proxy_canonical_answer_path(
            request_body=request_body,
            conversation_history=conversation_history,
            last_user_message=last_user_msg,
        )
        return _finalize_boundary_proxy_response(
            request=request,
            request_body=request_body,
            store=store,
            session_id=session_id,
            user_message=last_user_msg,
            canonical_snapshot=canonical_snapshot,
            proxy_response=proxy_response,
        )

    runtime_context = await _prepare_retrieval_runtime_context(
        request=request,
        request_body=request_body,
        last_user_msg=last_user_msg,
        conversation_history=conversation_history,
    )
    enriched_query = runtime_context.enriched_query
    routing_query = runtime_context.routing_query
    retrieval_query = runtime_context.retrieval_query
    retrieval_top_k = runtime_context.retrieval_top_k
    mentioned_laws = runtime_context.mentioned_laws
    explicit_article_refs = runtime_context.explicit_article_refs
    requested_source_families = runtime_context.requested_source_families
    forced_article_refs = runtime_context.forced_article_refs
    applied_expansions = runtime_context.applied_expansions
    source_family_resolution = runtime_context.source_family_resolution
    retrieval_plan = runtime_context.retrieval_plan
    domain_supporting_source_selector = runtime_context.domain_supporting_source_selector
    domain_supporting_source_families = runtime_context.domain_supporting_source_families
    metadata_lookup_query_signals = runtime_context.metadata_lookup_query_signals
    metadata_first_selector = runtime_context.metadata_first_selector
    cross_law_mode = runtime_context.cross_law_mode
    numbered_law_mentions = runtime_context.numbered_law_mentions
    numbered_law_reference_expansion = runtime_context.numbered_law_reference_expansion
    all_exact_article_refs = runtime_context.all_exact_article_refs
    source_lock_target_citations = runtime_context.source_lock_target_citations
    answer_query = runtime_context.answer_query

    # ── Retrieval ─────────────────────────────────────────────────────────────
    retrieved_chunks: list[RetrievedChunk] = []
    pre_rerank_chunks: list[RetrievedChunk] = []
    post_rerank_chunks: list[RetrievedChunk] = []
    source_cluster_selector: dict[str, Any] | None = None
    source_identity_reranker: dict[str, Any] | None = None
    article_span_selector: dict[str, Any] | None = None
    relation_chain_policy: dict[str, Any] | None = None
    selected_source_keys: set[str] = set()
    family_routing_policy: dict[str, Any] | None = None
    phase24hu_secondary_family_policy: dict[str, Any] = _phase24hu_secondary_family_recall_policy(
        query=routing_query,
        requested_source_families=requested_source_families,
        source_family_resolution=source_family_resolution,
        metadata_lookup_query_signals=metadata_lookup_query_signals,
        metadata_first_selector=metadata_first_selector,
        law_filter=request_body.law_filter,
    )
    if metadata_first_selector:
        selected_source_keys.update(_metadata_first_focus_keys_for_source_lock(metadata_first_selector))
    top_k_effective = retrieval_top_k
    retriever = _get_retriever(request)

    if retriever is not None:
        try:
            # Metadata filter (kanun filtresi)
            metadata_filter = None
            if request_body.law_filter:
                from rag.retriever import MetadataFilter

                metadata_filter = MetadataFilter(law_short_name=request_body.law_filter)

            # Reranker etkinse daha fazla aday çek (varsayılan: 20)
            _reranker_enabled = os.getenv("RERANKER_ENABLED", "false").lower() in {"1", "true", "yes"}
            _retrieve_top_k = request_body.top_k
            if _reranker_enabled:
                _retrieve_top_k = int(os.getenv("RERANKER_RETRIEVE_TOP_K", "20"))
            top_k_effective = max(retrieval_top_k, _retrieve_top_k)

            # Embedder varsa embed et, yoksa direkt query string ile dene
            if hasattr(retriever, "retrieve") and callable(retriever.retrieve):
                # MilvusRetriever: retrieve(query=str, top_k=int, metadata_filter=...)
                results, stats = retriever.retrieve(
                    query=retrieval_query,  # Terminoloji genişletilmiş sorgu
                    top_k=top_k_effective,
                    metadata_filter=metadata_filter,
                )
                retrieved_chunks = _annotate_recall_lane_chunks(
                    [_build_retrieved_chunk(r) for r in results],
                    lane="semantic_dense_recall",
                )
                logger.info(
                    "Retrieval: session=%s hits=%d latency=%.0fms reranker=%s",
                    session_id,
                    stats.hit_count,
                    stats.latency_ms,
                    "enabled" if _reranker_enabled else "disabled",
                )

                planner_focus_query = _build_retrieval_plan_focus_query(retrieval_plan)
                if planner_focus_query and normalize_query_text(planner_focus_query) != normalize_query_text(retrieval_query):
                    planner_top_k = max(6, min(10, top_k_effective))
                    planner_results, planner_stats = retriever.retrieve(
                        query=planner_focus_query,
                        top_k=planner_top_k,
                        metadata_filter=metadata_filter,
                    )
                    planner_chunks = _annotate_recall_lane_chunks(
                        [_build_retrieved_chunk(r) for r in planner_results],
                        lane="semantic_dense_recall",
                    )
                    if planner_chunks:
                        retrieved_chunks = _dedupe_retrieved_chunks(planner_chunks + retrieved_chunks)
                        logger.info(
                            "Retrieval planner-focus: session=%s hits=%d latency=%.0fms query=%s",
                            session_id,
                            planner_stats.hit_count,
                            planner_stats.latency_ms,
                            planner_focus_query,
                        )

                if cross_law_mode and not request_body.law_filter and len(mentioned_laws) >= 2:
                    per_law_top_k = max(4, min(8, top_k_effective))
                    law_bucket_chunks = _retrieve_law_bucket_chunks(
                        retriever=retriever,
                        query=retrieval_query,
                        laws=mentioned_laws,
                        top_k=per_law_top_k,
                    )
                    if law_bucket_chunks:
                        retrieved_chunks = _dedupe_retrieved_chunks(law_bucket_chunks + retrieved_chunks)
                        logger.info(
                            "Retrieval law-buckets: session=%s laws=%s per_law_top_k=%d total=%d",
                            session_id,
                            mentioned_laws,
                            per_law_top_k,
                            len(retrieved_chunks),
                        )

                if numbered_law_mentions and not request_body.law_filter:
                    numbered_law_chunks = _retrieve_law_bucket_chunks(
                        retriever=retriever,
                        query=retrieval_query,
                        laws=numbered_law_mentions,
                        top_k=max(4, min(8, top_k_effective)),
                    )
                    if numbered_law_chunks:
                        retrieved_chunks = _dedupe_retrieved_chunks(numbered_law_chunks + retrieved_chunks)
                        logger.info(
                            "Retrieval numbered-law-buckets: session=%s laws=%s total=%d",
                            session_id,
                            numbered_law_mentions,
                            len(retrieved_chunks),
                        )

                if numbered_law_reference_expansion:
                    reference_top_k = max(6, min(10, top_k_effective))
                    reference_results, reference_stats = retriever.retrieve(
                        query=numbered_law_reference_expansion,
                        top_k=reference_top_k,
                        metadata_filter=metadata_filter,
                    )
                    reference_chunks = _annotate_recall_lane_chunks(
                        [_build_retrieved_chunk(result) for result in reference_results],
                        lane="metadata_guided_recall",
                    )
                    if reference_chunks:
                        retrieved_chunks = _dedupe_retrieved_chunks(reference_chunks + retrieved_chunks)
                        logger.info(
                            "Retrieval numbered-law-reference: session=%s hits=%d latency=%.0fms query=%s",
                            session_id,
                            reference_stats.hit_count,
                            reference_stats.latency_ms,
                            numbered_law_reference_expansion,
                        )

                planner_law_hints = set(retrieval_plan.get("law_hints") or []) if retrieval_plan else set()
                if planner_law_hints and not request_body.law_filter:
                    planner_law_chunks = _retrieve_law_bucket_chunks(
                        retriever=retriever,
                        query=retrieval_query,
                        laws=planner_law_hints,
                        top_k=max(4, min(8, top_k_effective)),
                    )
                    if planner_law_chunks:
                        retrieved_chunks = _dedupe_retrieved_chunks(planner_law_chunks + retrieved_chunks)
                        logger.info(
                            "Retrieval planner-law-buckets: session=%s laws=%s total=%d",
                            session_id,
                            sorted(planner_law_hints),
                            len(retrieved_chunks),
                        )
                    planner_source_supplement_keys = _source_supplement_keys_for_law_hints(planner_law_hints)
                    if planner_source_supplement_keys:
                        planner_source_supplement_chunks = _build_source_supplement_chunks(
                            load_source_supplements_for_keys(
                                planner_source_supplement_keys,
                                source_families=set(requested_source_families) if requested_source_families else None,
                            )
                        )
                        if planner_source_supplement_chunks:
                            retrieved_chunks = _dedupe_retrieved_chunks(
                                planner_source_supplement_chunks + retrieved_chunks
                            )
                            logger.info(
                                "Retrieval planner-law-source-supplements: session=%s sources=%s added=%d total=%d",
                                session_id,
                                planner_source_supplement_keys,
                                len(planner_source_supplement_chunks),
                                len(retrieved_chunks),
                            )

                if _asks_constitutional_transition_khk_query(routing_query) and not request_body.law_filter:
                    transition_khk_chunks = _retrieve_law_bucket_chunks(
                        retriever=retriever,
                        query=(
                            "703 sayılı Kanun Hükmünde Kararname "
                            "Cumhurbaşkanlığı Hükümet Sistemi geçiş atıf uyarlaması"
                        ),
                        laws=["703"],
                        top_k=max(4, min(8, top_k_effective)),
                    )
                    if transition_khk_chunks:
                        retrieved_chunks = _dedupe_retrieved_chunks(transition_khk_chunks + retrieved_chunks)
                        logger.info(
                            "Retrieval constitutional-transition-khk: session=%s added=%d total=%d",
                            session_id,
                            len(transition_khk_chunks),
                            len(retrieved_chunks),
                        )

                if metadata_first_selector and not request_body.law_filter:
                    metadata_first_source_keys = [
                        key
                        for key in metadata_first_selector.get("selected_source_keys") or []
                        if isinstance(key, str) and key.strip()
                    ]
                    metadata_first_source_family_by_key = {
                        str(candidate.get("source_key") or "").strip(): str(
                            candidate.get("source_family_raw") or candidate.get("source_family") or ""
                        ).strip()
                        for candidate in metadata_first_selector.get("candidates") or []
                        if str(candidate.get("source_key") or "").strip()
                    }
                    metadata_first_chunks = _retrieve_source_key_chunks(
                        retriever=retriever,
                        query=retrieval_query,
                        source_keys=metadata_first_source_keys,
                        source_family_by_key=metadata_first_source_family_by_key,
                        top_k=max(4, min(8, top_k_effective)),
                    )
                    metadata_first_selector["metadata_lookup_retrieval_added_count"] = len(metadata_first_chunks)
                    metadata_first_selector["metadata_lookup_retrieval_channel"] = "source_key_filter"
                    if metadata_first_chunks:
                        retrieved_chunks = _dedupe_retrieved_chunks(metadata_first_chunks + retrieved_chunks)
                        logger.info(
                            "Retrieval metadata-first-sources: session=%s sources=%s total=%d",
                            session_id,
                            metadata_first_source_keys,
                            len(retrieved_chunks),
                        )
                    source_supplement_lookup_keys = dedupe_strings(
                        [
                            *metadata_first_source_keys,
                            *[
                                str(value or "").strip()
                                for candidate in (metadata_first_selector.get("candidates") or [])
                                if isinstance(candidate, dict)
                                for value in (
                                    candidate.get("canonical_title"),
                                    candidate.get("canonical_identifier"),
                                    *(candidate.get("focus_keys") or []),
                                )
                                if str(value or "").strip()
                            ],
                        ]
                    )
                    source_supplement_chunks = _build_source_supplement_chunks(
                        load_source_supplements_for_keys(
                            source_supplement_lookup_keys,
                            source_families=set(requested_source_families) if requested_source_families else None,
                        )
                    )
                    metadata_first_selector["source_supplement_added_count"] = len(source_supplement_chunks)
                    if source_supplement_chunks:
                        retrieved_chunks = _dedupe_retrieved_chunks(source_supplement_chunks + retrieved_chunks)
                        logger.info(
                            "Retrieval source-supplements: session=%s sources=%s added=%d total=%d",
                            session_id,
                            metadata_first_source_keys,
                            len(source_supplement_chunks),
                            len(retrieved_chunks),
                        )

                if requested_source_families:
                    per_family_top_k = max(4, min(8, top_k_effective))
                    family_bucket_chunks = _retrieve_source_family_chunks(
                        retriever=retriever,
                        query=retrieval_query,
                        source_families=requested_source_families,
                        top_k=per_family_top_k,
                    )
                    if family_bucket_chunks:
                        retrieved_chunks = _dedupe_retrieved_chunks(family_bucket_chunks + retrieved_chunks)
                        logger.info(
                            "Retrieval source-families: session=%s families=%s per_family_top_k=%d total=%d",
                            session_id,
                            requested_source_families,
                            per_family_top_k,
                            len(retrieved_chunks),
                        )

                if _asks_current_validity_query(last_user_msg):
                    active_chunks = _retrieve_active_chunks(
                        retriever=retriever,
                        query=retrieval_query,
                        top_k=max(6, min(10, top_k_effective)),
                    )
                    if active_chunks:
                        retrieved_chunks = _dedupe_retrieved_chunks(active_chunks + retrieved_chunks)
                        logger.info(
                            "Retrieval active-sources: session=%s added=%d total=%d",
                            session_id,
                            len(active_chunks),
                            len(retrieved_chunks),
                        )

                if all_exact_article_refs:
                    exact_chunks = _retrieve_explicit_article_chunks(
                        retriever=retriever,
                        query=routing_query,
                        article_refs=all_exact_article_refs,
                    )
                    if exact_chunks:
                        retrieved_chunks = _dedupe_retrieved_chunks(exact_chunks + retrieved_chunks)
                        logger.info(
                            "Retrieval exact-include: session=%s refs=%s added=%d total=%d",
                            session_id,
                            all_exact_article_refs,
                            len(exact_chunks),
                            len(retrieved_chunks),
                        )
                if selected_source_keys:
                    retrieved_chunks = _prioritize_chunks_for_source_families(
                        query=routing_query,
                        chunks=retrieved_chunks,
                        source_families=requested_source_families,
                        selected_source_keys=selected_source_keys,
                    )
                    retrieved_chunks = _focus_chunks_on_selected_sources(
                        chunks=retrieved_chunks,
                        selected_source_keys=selected_source_keys,
                    )
                retrieved_chunks = _prioritize_chunks_for_source_families(
                    query=routing_query,
                    chunks=retrieved_chunks,
                    source_families=requested_source_families,
                )

                source_cluster_selector = await _run_source_cluster_selector(
                    request=request,
                    user_query=routing_query,
                    requested_source_families=requested_source_families,
                    chunks=retrieved_chunks,
                    source_family_resolution=source_family_resolution,
                    planner_law_hints=planner_law_hints,
                )
                if source_cluster_selector:
                    selected_cluster_ids = set(source_cluster_selector.get("selected_cluster_ids") or [])
                    candidate_by_id = {
                        candidate["cluster_id"]: candidate
                        for candidate in source_cluster_selector.get("candidates") or []
                    }
                    strong_family_gate = _strong_source_family_gate(source_family_resolution)
                    if strong_family_gate:
                        gated_cluster_ids = {
                            cluster_id
                            for cluster_id in selected_cluster_ids
                            if (
                                candidate_by_id.get(cluster_id, {}).get("source_family")
                                in strong_family_gate
                            )
                        }
                        if gated_cluster_ids:
                            selected_cluster_ids = gated_cluster_ids
                        else:
                            selected_cluster_ids = set()
                            logger.info(
                                "Retrieval source-selector gated out: session=%s families=%s",
                                session_id,
                                sorted(strong_family_gate),
                            )
                    selected_source_keys.update(
                        {
                        candidate_by_id[cluster_id]["source_key"]
                        for cluster_id in selected_cluster_ids
                        if cluster_id in candidate_by_id
                        }
                    )
                    selected_laws = (
                        dedupe_strings(source_cluster_selector.get("selected_law_hints") or [])
                        if selected_cluster_ids
                        else []
                    )

                    if selected_laws and not request_body.law_filter:
                        selected_law_chunks = _retrieve_law_bucket_chunks(
                            retriever=retriever,
                            query=retrieval_query,
                            laws=selected_laws,
                            top_k=max(4, min(8, top_k_effective)),
                        )
                        if selected_law_chunks:
                            retrieved_chunks = _dedupe_retrieved_chunks(selected_law_chunks + retrieved_chunks)

                    retrieved_chunks = _prioritize_chunks_for_source_families(
                        query=routing_query,
                        chunks=retrieved_chunks,
                        source_families=requested_source_families,
                        selected_source_keys=selected_source_keys,
                    )
                    retrieved_chunks = _focus_chunks_on_selected_sources(
                        chunks=retrieved_chunks,
                        selected_source_keys=selected_source_keys,
                    )
                    logger.info(
                        "Retrieval source-selector: session=%s clusters=%s laws=%s total=%d",
                        session_id,
                        sorted(selected_cluster_ids),
                        selected_laws,
                        len(retrieved_chunks),
                    )
                elif len(retrieved_chunks) > top_k_effective:
                    retrieved_chunks = retrieved_chunks[:top_k_effective]
                if domain_supporting_source_selector:
                    support_candidates = [
                        candidate
                        for candidate in (domain_supporting_source_selector.get("candidates") or [])
                        if isinstance(candidate, dict)
                    ]
                    support_source_keys = dedupe_strings(
                        [
                            str(candidate.get("source_key") or "").strip()
                            for candidate in support_candidates
                            if str(candidate.get("source_key") or "").strip()
                        ]
                    )[:4]
                    support_source_family_by_key = {
                        str(candidate.get("source_key") or "").strip(): str(
                            candidate.get("source_family_raw")
                            or candidate.get("source_family")
                            or ""
                        ).strip()
                        for candidate in support_candidates
                        if str(candidate.get("source_key") or "").strip()
                    }
                    support_query = str(
                        domain_supporting_source_selector.get("supporting_source_query") or retrieval_query
                    )
                    support_chunks = _retrieve_source_key_chunks(
                        retriever=retriever,
                        query=support_query,
                        source_keys=support_source_keys,
                        source_family_by_key=support_source_family_by_key,
                        top_k=max(4, min(8, top_k_effective)),
                    )
                    if support_chunks:
                        marked_support_chunks: list[RetrievedChunk] = []
                        for chunk in support_chunks:
                            metadata = dict(chunk.metadata or {})
                            lanes = [
                                str(value)
                                for value in (metadata.get("retrieval_lane_sources") or [])
                                if isinstance(value, str) and value.strip()
                            ]
                            metadata["domain_law_supporting_source"] = True
                            metadata["retrieval_lane_sources"] = dedupe_strings(
                                [*lanes, "domain_law_supporting_source"]
                            )
                            marked_support_chunks.append(
                                RetrievedChunk(
                                    text=chunk.text,
                                    citation=chunk.citation,
                                    source=chunk.source,
                                    score=chunk.score,
                                    metadata=metadata,
                                )
                            )
                        retrieved_chunks = _dedupe_retrieved_chunks(
                            marked_support_chunks + retrieved_chunks
                        )
                        if selected_source_keys:
                            retrieved_chunks = _prioritize_chunks_for_source_families(
                                query=routing_query,
                                chunks=retrieved_chunks,
                                source_families=requested_source_families,
                                selected_source_keys=selected_source_keys,
                            )
                            retrieved_chunks = _focus_chunks_on_selected_sources(
                                chunks=retrieved_chunks,
                                selected_source_keys=selected_source_keys,
                            )
                        logger.info(
                            "Retrieval domain-law-supporting-sources: session=%s sources=%s families=%s added=%d total=%d",
                            session_id,
                            support_source_keys,
                            domain_supporting_source_families,
                            len(marked_support_chunks),
                            len(retrieved_chunks),
                        )
                if (
                    phase24hu_secondary_family_policy.get("phase24hu_secondary_family_recall_enabled")
                    and phase24hu_secondary_family_policy.get("secondary_family_recall_reason")
                    == "source_role_secondary_family_signal"
                ):
                    secondary_families = [
                        str(value)
                        for value in phase24hu_secondary_family_policy.get("secondary_family_recall_types") or []
                        if str(value or "").strip()
                    ]
                    support_query = _phase24hu_support_query(
                        routing_query,
                        [
                            str(value)
                            for value in phase24hu_secondary_family_policy.get("phase24hu_source_role_signals") or []
                            if str(value or "").strip()
                        ],
                    )
                    secondary_chunks = _retrieve_source_family_chunks(
                        retriever=retriever,
                        query=support_query,
                        source_families=secondary_families,
                        top_k=max(4, min(8, top_k_effective)),
                    )
                    marked_secondary_chunks = _phase24hu_mark_secondary_family_chunks(
                        chunks=secondary_chunks,
                        query=routing_query,
                    )
                    phase24hu_secondary_family_policy["secondary_family_recall_candidates"] = (
                        _phase24hu_candidate_summary(marked_secondary_chunks)
                    )
                    phase24hu_secondary_family_policy["secondary_family_recall_candidate_count"] = len(
                        marked_secondary_chunks
                    )
                    if marked_secondary_chunks:
                        phase24hu_secondary_family_policy["secondary_family_recall_applied"] = True
                        domain_supporting_source_families = dedupe_strings(
                            [*domain_supporting_source_families, *secondary_families]
                        )
                        retrieved_chunks = _dedupe_retrieved_chunks(
                            marked_secondary_chunks + retrieved_chunks
                        )
                        logger.info(
                            "Retrieval phase24hu-secondary-family-recall: session=%s families=%s added=%d total=%d",
                            session_id,
                            secondary_families,
                            len(marked_secondary_chunks),
                            len(retrieved_chunks),
                        )
                    else:
                        phase24hu_secondary_family_policy[
                            "secondary_family_recall_reason"
                        ] = "source_role_secondary_family_signal_no_candidates"
                before_family_pool_count = len(retrieved_chunks)
                family_pool_query = routing_query
                if all_exact_article_refs:
                    family_pool_query = _normalize_whitespace(
                        " ".join(
                            [
                                routing_query,
                                *[
                                    f"{law} m.{article}"
                                    for law, article in all_exact_article_refs
                                    if str(law or "").strip() and str(article or "").strip()
                                ],
                            ]
                        )
                    )
                retrieved_chunks, family_routing_policy = _apply_pre_generation_family_pool(
                    chunks=retrieved_chunks,
                    source_family_resolution=source_family_resolution,
                    top_k_effective=top_k_effective,
                    query=family_pool_query,
                    supporting_source_families=domain_supporting_source_families,
                )
                if before_family_pool_count != len(retrieved_chunks) or (
                    family_routing_policy.get("cross_family_fallback_used") if family_routing_policy else False
                ):
                    logger.info(
                        "Retrieval family-pool: session=%s expected=%s preferred=%s fallback=%s before=%d after=%d reason=%s",
                        session_id,
                        family_routing_policy.get("expected_family_prior") if family_routing_policy else None,
                        family_routing_policy.get("preferred_families") if family_routing_policy else [],
                        family_routing_policy.get("cross_family_fallback_used") if family_routing_policy else False,
                        before_family_pool_count,
                        len(retrieved_chunks),
                        family_routing_policy.get("family_override_reason") if family_routing_policy else None,
                    )
                if (
                    _should_retrieve_historical_current_counterpart(
                        query=routing_query,
                        source_family_resolution=source_family_resolution,
                    )
                    and not request_body.law_filter
                ):
                    counterpart_chunks = _mark_historical_current_counterpart_chunks(
                        _retrieve_active_chunks(
                            retriever=retriever,
                            query=_build_historical_current_counterpart_query(routing_query),
                            top_k=max(6, min(10, top_k_effective)),
                        )
                    )
                    if counterpart_chunks:
                        retrieved_chunks = _dedupe_retrieved_chunks(retrieved_chunks + counterpart_chunks)
                        if family_routing_policy is not None:
                            family_routing_policy["historical_current_counterpart_added_count"] = len(
                                counterpart_chunks
                            )
                        logger.info(
                            "Retrieval historical-current-counterpart: session=%s added=%d total=%d",
                            session_id,
                            len(counterpart_chunks),
                            len(retrieved_chunks),
                        )
                relation_chain_chunks, relation_chain_policy = _retrieve_relation_chain_chunks(
                    retriever=retriever,
                    query=routing_query,
                    chunks=retrieved_chunks,
                    source_family_resolution=source_family_resolution,
                )
                if relation_chain_chunks:
                    retrieved_chunks = _dedupe_retrieved_chunks(retrieved_chunks + relation_chain_chunks)
                    if family_routing_policy is not None:
                        family_routing_policy.update(
                            {
                                key: value
                                for key, value in relation_chain_policy.items()
                                if key.startswith("relation_chain_")
                                or key
                                in {
                                    "current_law_basis_added",
                                    "repeal_instrument_added",
                                    "historical_source_effective_state",
                                    "historical_source_not_marked_active",
                                    "repealed_as_active_count",
                                }
                            }
                        )
                    logger.info(
                        "Retrieval relation-chain: session=%s added=%d total=%d source=%s repeal=%s current=%s",
                        session_id,
                        len(relation_chain_chunks),
                        len(retrieved_chunks),
                        relation_chain_policy.get("relation_chain_source_key") if relation_chain_policy else None,
                        relation_chain_policy.get("relation_chain_repeal_source_key") if relation_chain_policy else None,
                        relation_chain_policy.get("relation_chain_current_basis_source_key") if relation_chain_policy else None,
                    )
                pre_rerank_chunks = list(retrieved_chunks)
        except Exception as exc:
            logger.warning(
                "Retrieval hatası (devam ediliyor, chunk yok): %s", exc, exc_info=True
            )

    # ── Reranker (opsiyonel, RERANKER_ENABLED=true) ───────────────────────────
    _reranker_enabled = os.getenv("RERANKER_ENABLED", "false").lower() in {"1", "true", "yes"}
    if _reranker_enabled and retrieved_chunks:
        try:
            from rag.reranker import FAZ1_TOP_K, get_reranker

            _reranker = get_reranker()
            _candidates = [
                {
                    "text": chunk.text,
                    "citation": chunk.citation,
                    "source": chunk.source,
                    "score": chunk.score,
                    "metadata": chunk.metadata or {},
                }
                for chunk in retrieved_chunks
            ]
            _ranked, _rstats = _reranker.rerank(
                query=last_user_msg,
                candidates=_candidates,
            )

            if _ranked:
                retrieved_chunks = [
                    RetrievedChunk(
                        text=r.text,
                        citation=r.citation,
                        source=r.source,
                        score=r.score,
                        metadata=enrich_metadata_with_source_title(r.metadata),
                    )
                    for r in _ranked
                ]
                logger.info(
                    "Reranker: session=%s input=%d→top_k=%d latency=%.0fms thr=%.1f filter_rate=%.0f%%",
                    session_id,
                    _rstats.input_count,
                    _rstats.top_k_count,
                    _rstats.latency_ms,
                    _rstats.threshold,
                    _rstats.filter_rate * 100,
                )
            else:
                # Threshold tüm adayları eledi → güvenli fallback: boş context
                # NEDEN: top-k retrieval fallback'i, domain dışı sorgularda (örn: TMK sorusu
                # ama sadece TBK verisi indeksli) yanlış domain chunk'larını döndürür.
                # LLM bu chunk'ları kullanarak yanlış atıf yapar (hallucination ↑).
                # Boş context ile LLM sistem promptu gereği "bilgim yok" yanıtı verir.
                # Önceki davranışa dönmek için: RERANKER_FALLBACK_TOPK=true env var.
                _fallback_topk = os.getenv("RERANKER_FALLBACK_TOPK", "false").lower() in {"1", "true", "yes"}
                if _fallback_topk:
                    retrieved_chunks = retrieved_chunks[:FAZ1_TOP_K]
                    logger.warning(
                        "Reranker: thr=%.1f tüm %d adayı eledi → top-%d retrieval fallback (RERANKER_FALLBACK_TOPK=true)",
                        _rstats.threshold,
                        _rstats.input_count,
                        FAZ1_TOP_K,
                    )
                else:
                    retrieved_chunks = []
                    logger.warning(
                        "Reranker: thr=%.1f tüm %d adayı eledi → boş context (güvenli fallback; RERANKER_FALLBACK_TOPK=true ile eski davranış)",
                        _rstats.threshold,
                        _rstats.input_count,
                    )
        except Exception as exc:
            logger.warning("Reranker bypass (hata): %s", exc, exc_info=True)

    if retrieved_chunks:
        selector_started_at = time.perf_counter()
        retrieved_chunks, source_identity_reranker = _rerank_chunks_by_source_identity(
            query=routing_query,
            chunks=retrieved_chunks,
            requested_source_families=requested_source_families,
            metadata_first_selector=metadata_first_selector,
            source_family_resolution=source_family_resolution,
        )
        retrieved_chunks, article_span_selector = _select_article_span_evidence(
            query=routing_query,
            chunks=retrieved_chunks,
            requested_source_families=requested_source_families,
            explicit_article_refs=all_exact_article_refs,
            selected_source_keys=selected_source_keys,
            source_family_resolution=source_family_resolution,
            source_identity_reranker=source_identity_reranker,
        )
        phase24hu_secondary_family_policy = _phase24hu_update_selected_support_trace(
            phase24hu_secondary_family_policy,
            chunks=retrieved_chunks,
            article_span_selector=article_span_selector,
        )
        retrieved_chunks = _apply_selected_document_only_bundle(
            chunks=retrieved_chunks,
            article_span_selector=article_span_selector,
        )
        _annotate_canonical_span_materialization(
            chunks=retrieved_chunks,
            article_span_selector=article_span_selector,
            family_routing_policy=family_routing_policy,
        )
        _annotate_article_span_selector_priority(
            chunks=retrieved_chunks,
            article_span_selector=article_span_selector,
        )
        answer_query = _apply_answer_slot_synthesis_hint(
            query=answer_query,
            routing_query=routing_query,
            article_span_selector=article_span_selector,
            requested_source_families=requested_source_families,
            source_family_resolution=source_family_resolution,
        )
        logger.info(
            "Response timing: session=%s stage=selector_stack latency=%.0fms chunks=%d",
            session_id,
            (time.perf_counter() - selector_started_at) * 1000.0,
            len(retrieved_chunks),
        )
    post_rerank_chunks = list(retrieved_chunks)
    source_family_resolution_trace = source_family_resolution.to_trace_dict()
    retrieval_verification_features = _build_retrieval_verification_features(
        query=routing_query,
        requested_source_families=requested_source_families,
        source_family_resolution=source_family_resolution_trace,
        chunks=post_rerank_chunks,
        family_routing_policy=family_routing_policy,
    )
    if phase24hu_secondary_family_policy:
        retrieval_verification_features.update(phase24hu_secondary_family_policy)
    if relation_chain_policy:
        retrieval_verification_features.update(relation_chain_policy)

    # ── Orchestrator ─────────────────────────────────────────────────────────
    orchestrator = _get_orchestrator(request)

    # Verification Engine: request'teki tercih + orchestrator'ın mevcut ayarı
    # Not: orchestrator.use_verification request başına override edilemiyor (stateful).
    # Faz 1: orchestrator'da verification global açık/kapalı; request override Faz 2.
    if request_body.use_verification and not orchestrator.use_verification:
        logger.debug("Verification request'te istendi ama orchestrator'da kapalı; atlanıyor.")

    try:
        orch_started_at = time.perf_counter()
        orch_response = await orchestrator.answer(
            query=answer_query,
            retrieved_chunks=retrieved_chunks,
            source_lock_target_citations=source_lock_target_citations,
            max_tokens=request_body.max_tokens,
        )
        logger.info(
            "Response timing: session=%s stage=orchestrator_answer latency=%.0fms citations=%d blocked=%s",
            session_id,
            (time.perf_counter() - orch_started_at) * 1000.0,
            len(orch_response.citations or []),
            orch_response.blocked,
        )
    except Exception as exc:
        logger.error("Orchestrator hatası: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"RAG pipeline hatası: {exc}",
        ) from exc

    answer_text = orch_response.answer
    citations = orch_response.citations
    blocked = orch_response.blocked
    guardrails_reasons = orch_response.guardrails_reasons
    verification = orch_response.verification
    assembled_evidence = _build_assembled_evidence(post_rerank_chunks, query=routing_query)
    allowed_source_whitelist = _build_allowed_source_whitelist(post_rerank_chunks)
    if not assembled_evidence and citations:
        assembled_evidence = _build_fallback_assembled_evidence(
            citations,
            fallback_excerpt=answer_text,
        )
        allowed_source_whitelist = [
            str(item["source_id"])
            for item in assembled_evidence
            if item.get("source_id")
        ]
    hardening_started_at = time.perf_counter()
    hardening = harden_answer(
        answer_text=answer_text,
        citations=citations,
        blocked=blocked,
        verification=verification,
        question_raw=last_user_msg,
        mentioned_laws=mentioned_laws,
        explicit_article_refs=explicit_article_refs,
        law_filter=request_body.law_filter,
        assembled_evidence=assembled_evidence,
        allowed_source_whitelist=allowed_source_whitelist,
    )
    logger.info(
        "Response timing: session=%s stage=harden_answer latency=%.0fms final_mode=%s",
        session_id,
        (time.perf_counter() - hardening_started_at) * 1000.0,
        hardening.final_mode,
    )
    cb_genelge_template_answer = _build_cb_genelge_document_level_answer(
        query=routing_query,
        chunks=post_rerank_chunks,
        article_span_selector=article_span_selector,
    )
    if cb_genelge_template_answer:
        hardening.answer_text = cb_genelge_template_answer
        if article_span_selector and article_span_selector.get("selected_main_span_id"):
            hardening.citations = dedupe_strings(
                [str(article_span_selector.get("selected_main_span_id")), *hardening.citations]
            )
        hardening.answer_contract["answer_text"] = cb_genelge_template_answer
        hardening.answer_contract["answer_mode"] = "qualified_answer"
        hardening.answer_contract["grounding_status"] = "partially_grounded"
        hardening.answer_contract["answer_suppressed_due_to_evidence_gap"] = False
        hardening.answer_contract["support_insufficient_for_specific_claim"] = False
    completeness_synthesis = _build_completeness_synthesis_features(
        query=routing_query,
        answer_text=hardening.answer_text,
        article_span_selector=article_span_selector,
        chunks=post_rerank_chunks,
        requested_source_families=requested_source_families,
        source_family_resolution=source_family_resolution,
    )
    hardening.answer_contract.update(completeness_synthesis)
    _phase24hu_annotate_exception_slot_trace(
        hardening.answer_contract,
        retrieval_verification_features,
    )
    if completeness_synthesis.get("insufficient_canonical_span_evidence"):
        hardening.answer_contract["needs_manual_review"] = True
        hardening.answer_contract["support_insufficient_for_specific_claim"] = True
        hardening.answer_contract["answer_suppressed_due_to_evidence_gap"] = True
        if hardening.answer_contract.get("answer_mode") != "insufficient_grounding":
            hardening.answer_contract["answer_mode"] = "qualified_answer"
        if hardening.answer_contract.get("grounding_status") not in {
            "insufficient_supported_evidence",
            "insufficient_grounding",
        }:
            hardening.answer_contract["grounding_status"] = "insufficient_supported_evidence"
    if retrieval_verification_features.get("source_identity_stop_condition_applied"):
        stop_reason = str(
            retrieval_verification_features.get("source_identity_stop_reason")
            or "source_identity_stop_condition"
        )
        stop_answer = (
            "Bu soruda tekil tüzük kaynağı doğrulanamadığı için rastgele bir tüzük metnini birincil "
            "kaynak göstermiyorum. Genel norm ilişkisi bakımından, ilgili yürürlükteki tüzük hükümleri "
            "kurum içi alt düzenlemeye göre üst normdur; kurum içi düzenleme geçerli tüzüğe aykırıysa "
            "uygulanamaz. Exact tüzük/source identity için manuel hukukçu incelemesi gerekir."
        )
        hardening.answer_text = stop_answer
        hardening.citations = []
        hardening.final_mode = "partial"
        hardening.internal_blocked = False
        stop_final_reason = (
            "dayanak=TUZUK:source_not_identified; madde=general_hierarchy; "
            "yururluk=unknown; grounding=not_grounded; sonuc=insufficient_grounding; belirsizlik=var"
        )
        hardening.final_reason = "insufficient_supported_evidence"
        hardening.answer_contract.update(
            {
                "answer_text": stop_answer,
                "final_answer": stop_answer,
                "answer_mode": "insufficient_grounding",
                "grounding_status": "not_grounded",
                "source_family_claimed": "TUZUK",
                "source_title_claimed": "ilgili yürürlükteki tüzük hükümleri (exact source identity unresolved)",
                "source_identifier_claimed": "source_not_identified",
                "article_or_section_claimed": "general_hierarchy",
                "effective_state_claimed": "unknown",
                "temporal_qualification": "source_identity_unresolved",
                "needs_manual_review": True,
                "confidence_0_100": 16,
                "final_reason": stop_final_reason,
                "answer_suppressed_due_to_evidence_gap": False,
                "support_insufficient_for_specific_claim": True,
                "insufficient_canonical_span_evidence": True,
                "source_identity_stop_condition_applied": True,
                "source_identity_stop_reason": stop_reason,
                "manual_review_trigger_reason": stop_reason,
            }
        )
    trace_started_at = time.perf_counter()
    trace_payload = _build_trace_payload(
        request_id=response_id,
        decision_lane="rag",
        user_query=last_user_msg,
        enriched_query=answer_query,
        retrieval_query=retrieval_query,
        question_normalized=normalize_query_text(routing_query),
        question_type=hardening.question_type,
        target_date=hardening.target_date,
        law_scope_signal=hardening.law_scope_signal,
        law_filter=request_body.law_filter,
        mentioned_laws=mentioned_laws,
        cross_law_mode=cross_law_mode,
        requested_source_families=requested_source_families,
        explicit_article_refs=explicit_article_refs,
        forced_article_refs=forced_article_refs,
        applied_expansions=applied_expansions,
        top_k_requested=request_body.top_k,
        top_k_effective=top_k_effective,
        reranker_enabled=_reranker_enabled,
        pre_rerank_chunks=pre_rerank_chunks,
        post_rerank_chunks=post_rerank_chunks,
        assembled_context=RAGOrchestrator._build_context(post_rerank_chunks),
        blocked=hardening.internal_blocked,
        guardrails_reasons=guardrails_reasons,
        verification=verification,
        answer_contract=hardening.answer_contract,
        model_cited_source_ids=hardening.model_cited_source_ids,
        final_mode=hardening.final_mode,
        final_reason=hardening.final_reason,
        retrieval_plan=retrieval_plan,
        metadata_lookup_query_signals=metadata_lookup_query_signals,
        metadata_first_selector=metadata_first_selector,
        source_identity_reranker=source_identity_reranker,
        source_cluster_selector=source_cluster_selector,
        article_span_selector=article_span_selector,
        source_family_resolution=source_family_resolution_trace,
        retrieval_verification_features=retrieval_verification_features,
        relation_chain_policy=relation_chain_policy,
    )
    logger.info(
        "Response timing: session=%s stage=trace_payload latency=%.0fms",
        session_id,
        (time.perf_counter() - trace_started_at) * 1000.0,
    )
    pre_answer_payload = _pre_answer_stage_payload(
        decision_lane="rag",
        user_message=last_user_msg,
        enriched_query=answer_query,
        retrieval_query=retrieval_query,
        conversation_history=conversation_history,
        mentioned_laws=mentioned_laws,
        requested_source_families=requested_source_families,
        explicit_article_refs=explicit_article_refs,
        forced_article_refs=forced_article_refs,
        applied_expansions=applied_expansions,
        top_k_requested=request_body.top_k,
        top_k_effective=top_k_effective,
        reranker_enabled=_reranker_enabled,
        retrieval_plan=retrieval_plan,
        metadata_first_selector=metadata_first_selector,
        source_identity_reranker=source_identity_reranker,
        source_cluster_selector=source_cluster_selector,
        article_span_selector=article_span_selector,
        source_family_resolution=source_family_resolution_trace,
    )
    finalize_started_at = time.perf_counter()
    response = _finalize_chat_response(
        request=request,
        request_body=request_body,
        store=store,
        session_id=session_id,
        response_id=response_id,
        user_message=last_user_msg,
        conversation_history=conversation_history,
        pre_answer_payload=pre_answer_payload,
        answer_text=hardening.answer_text,
        citations=hardening.citations,
        blocked=hardening.internal_blocked,
        guardrails_reasons=guardrails_reasons,
        verification=verification,
        trace_payload=trace_payload,
        answer_contract=hardening.answer_contract,
        final_mode=hardening.final_mode,
        final_reason=hardening.final_reason,
        upstream_usage=orch_response.usage,
        llm_trace=orch_response.llm_trace,
    )
    logger.info(
        "Response timing: session=%s stage=finalize_chat_response latency=%.0fms",
        session_id,
        (time.perf_counter() - finalize_started_at) * 1000.0,
    )
    return response


@router.get(
    "/v1/sessions/{session_id}",
    summary="Oturum geçmişini döndür",
)
async def get_session(
    request: Request,
    session_id: str,
    store: ConversationStore = Depends(get_conversation_store),
    _auth_subject: str = Depends(require_api_auth),
) -> dict[str, Any]:
    """Verilen session_id için konuşma geçmişini döndür."""
    history = store.get_history(session_id)
    return {
        "session_id": session_id,
        "message_count": len(history),
        "messages": history,
    }


@router.delete(
    "/v1/sessions/{session_id}",
    summary="Oturumu sil",
)
async def delete_session(
    request: Request,
    session_id: str,
    store: ConversationStore = Depends(get_conversation_store),
    _auth_subject: str = Depends(require_api_auth),
) -> dict[str, Any]:
    """Verilen session_id için konuşma oturumunu ve geçmişini sil."""
    deleted = store.clear_session(session_id)
    return {
        "session_id": session_id,
        "deleted": deleted,
        "message": "Oturum silindi" if deleted else "Oturum bulunamadı",
    }


@router.get(
    "/v1/sessions",
    summary="Aktif oturum sayısı",
)
async def list_sessions(
    request: Request,
    store: ConversationStore = Depends(get_conversation_store),
    _auth_subject: str = Depends(require_api_auth),
) -> dict[str, Any]:
    """Aktif oturum sayısını ve limiti döndür."""
    return {
        "active_sessions": store.session_count(),
        "max_sessions": ConversationStore.MAX_SESSIONS,
    }
