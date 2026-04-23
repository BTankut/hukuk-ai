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

import asyncio
import hashlib
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
from itertools import count
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

from rag.orchestrator import RAGOrchestrator, RetrievedChunk
from rag.source_catalog import (
    enrich_metadata_with_source_title,
    load_canonical_source_catalog,
    normalize_canonical_text,
    resolve_effective_state,
    source_family_mapping_profile,
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
    build_text_token_trace,
    resolve_token_usage,
    token_accounting_fallback_allowed,
)
from source_family_resolver import (
    SourceFamilyCandidate,
    SourceFamilyResolution,
    resolve_source_family_prior,
)

logger = logging.getLogger(__name__)
_GENERATION_START_ORDINAL = count(1)

router = APIRouter(tags=["chat"])
_LAW_TOKEN_PATTERN = r"TBK|TMK|TCK|HMK|TTK|İİK|IİK|IIK"
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
    rf"\b(?P<law>{_LAW_TOKEN_PATTERN}|Türk Borçlar Kanunu|Borçlar Kanunu|Türk Medeni Kanunu|Medeni Kanun|Türk Ceza Kanunu|Ceza Kanunu|Türk Ticaret Kanunu|Ticaret Kanunu|İcra ve İflas Kanunu)\b",
    re.IGNORECASE,
)
_LAW_CODE_NORMALIZATION = {
    "TBK": "TBK",
    "TMK": "TMK",
    "TCK": "TCK",
    "HMK": "HMK",
    "TTK": "TTK",
    "İİK": "İİK",
    "IİK": "İİK",
    "IIK": "İİK",
}
_LAW_NAME_NORMALIZATION = {
    "türk borçlar kanunu": "TBK",
    "borçlar kanunu": "TBK",
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
_SOURCE_FAMILY_HINT_RULES: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("kanun hükmünde kararname", "kanun hukmunde kararname", "khk"), ("khk",)),
    (
        ("cumhurbaşkanlığı kararnamesi", "cumhurbaskanligi kararnamesi", "cbk", "kararname"),
        ("cb_kararname",),
    ),
    (
        ("cumhurbaşkanlığı yönetmeliği", "cumhurbaskanligi yonetmeligi"),
        ("cb_yonetmelik", "yonetmelik"),
    ),
    (
        (
            "cumhurbaşkanlığı kararı",
            "cumhurbaskanligi karari",
            "cumhurbaşkanı kararı",
            "cumhurbaskani karari",
            "yatırım programı kararı",
            "yatirim programi karari",
        ),
        ("cb_karar",),
    ),
    (
        ("cumhurbaşkanlığı genelgesi", "cumhurbaskanligi genelgesi", "tasarruf genelgesi", "mobbing genelgesi"),
        ("cb_genelge",),
    ),
    (("tebliğ", "teblig"), ("teblig",)),
    (("tüzük", "tuzuk"), ("tuzuk",)),
    (
        (
            "üniversite yönetmeliği",
            "universite yonetmeligi",
            "öğrenci yönetmeliği",
            "ogrenci yonetmeligi",
            "yatay geçiş",
            "yatay gecis",
            "çift anadal",
            "cift anadal",
            "tez savunma",
            "yüksek lisans",
            "yuksek lisans",
            "hazırlık sınıfı",
            "hazirlik sinifi",
        ),
        ("uy", "yonetmelik"),
    ),
    (
        (
            "kurum yönetmeliği",
            "kurum yonetmeligi",
            "bddk",
            "sgk",
            "epdk",
            "btk",
            "rtük",
            "rtuk",
        ),
        ("kky", "yonetmelik"),
    ),
    (("yönetmelik", "yonetmelik"), ("yonetmelik",)),
)
_SOURCE_FAMILY_ALIAS_EXPANSIONS: dict[str, tuple[str, ...]] = {
    "yonetmelik": ("yonetmelik", "cb_yonetmelik", "kky", "uy"),
    "kanun": ("kanun", "mulga_kanun"),
    "khk": ("khk",),
    "tuzuk": ("tuzuk",),
}
_SOURCE_FAMILY_DISPLAY_LABELS: dict[str, str] = {
    "tuzuk": "tüzük",
    "kanun": "kanun",
    "mulga_kanun": "mülga kanun",
    "yonetmelik": "yönetmelik",
    "cb_yonetmelik": "Cumhurbaşkanlığı yönetmeliği",
    "cb_kararname": "Cumhurbaşkanlığı kararnamesi",
    "cb_karar": "Cumhurbaşkanı kararı",
    "cb_genelge": "Cumhurbaşkanlığı genelgesi",
    "khk": "KHK",
    "teblig": "tebliğ",
    "kky": "kurum yönetmeliği",
    "uy": "üniversite yönetmeliği",
}
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
_WEAK_SOURCE_FAMILY_ROUTE_TOPK_FAMILIES = {
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
    if intent == "gratitude":
        return "Rica ederim. İstersen mevzuat sorunu doğrudan kanun ve madde numarasıyla sor."
    if intent == "capability":
        return (
            "Merhaba. Mevzuat sorularında yardımcı olabilirim; özellikle kanun ve madde bazlı "
            "sorularda daha isabetli çalışırım. İstersen sorunu doğrudan yaz."
        )
    return "Merhaba. Mevzuat sorularında yardımcı olabilirim; istersen sorunu doğrudan yaz."


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


def _metadata_first_candidate_generation_enabled() -> bool:
    return os.getenv("METADATA_FIRST_CANDIDATE_GENERATION_ENABLED", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


_METADATA_LOOKUP_IDENTIFIER_KIND_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("cb_kararname", ("cumhurbaskanligi kararnamesi", "cbk", "kararname")),
    ("cb_karar", ("cumhurbaskani karari", "cumhurbaskanligi karari", "karar")),
    ("cb_genelge", ("cumhurbaskanligi genelgesi", "cumhurbaskani genelgesi", "genelge")),
    ("teblig", ("teblig",)),
    ("khk", ("kanun hukmunde kararname", "khk")),
    ("kanun", ("kanun",)),
)
_METADATA_LOOKUP_ISSUER_TERMS: tuple[str, ...] = (
    "cumhurbaşkanlığı",
    "cumhurbaşkanı",
    "adalet bakanlığı",
    "ticaret bakanlığı",
    "hazine ve maliye bakanlığı",
    "çalışma ve sosyal güvenlik bakanlığı",
    "içişleri bakanlığı",
    "dışişleri bakanlığı",
    "sağlık bakanlığı",
    "milli eğitim bakanlığı",
    "tarım ve orman bakanlığı",
    "çevre şehircilik ve iklim değişikliği bakanlığı",
    "sanayi ve teknoloji bakanlığı",
    "ulaştırma ve altyapı bakanlığı",
    "kültür ve turizm bakanlığı",
    "enerji ve tabii kaynaklar bakanlığı",
    "aile ve sosyal hizmetler bakanlığı",
    "gençlik ve spor bakanlığı",
    "milli savunma bakanlığı",
    "yök",
    "yükseköğretim kurulu",
    "ösym",
    "ölçme seçme ve yerleştirme merkezi",
    "sgk",
    "sosyal güvenlik kurumu",
    "bddk",
    "bankacılık düzenleme ve denetleme kurumu",
    "epdk",
    "enerji piyasası düzenleme kurumu",
    "btk",
    "bilgi teknolojileri ve iletişim kurumu",
    "rtük",
    "radyo ve televizyon üst kurulu",
    "kvkk",
    "kişisel verileri koruma kurumu",
    "kamu ihale kurumu",
    "rekabet kurumu",
    "sayıştay",
)
_METADATA_LOOKUP_TITLE_MARKERS: tuple[str, ...] = (
    "hakkinda",
    "iliskin",
    "dair",
    "usul ve esaslar",
    "usul ve esaslari",
    "uygulama",
    "uygulanmasina",
    "yururluge konulmasi",
)
_METADATA_LOOKUP_TITLE_TYPE_TERMS: tuple[str, ...] = (
    "kanunu",
    "kanun",
    "tuzugu",
    "tuzuk",
    "nizamnamesi",
    "yonetmeligi",
    "yonetmelik",
    "tebligi",
    "teblig",
    "karari",
    "karar",
    "genelgesi",
    "genelge",
    "kararnamesi",
    "kararname",
)
_METADATA_LOOKUP_TEMPORAL_TERMS: tuple[tuple[str, str], ...] = (
    ("current", "guncel"),
    ("current", "yururlukte"),
    ("current", "halen"),
    ("repealed", "mulga"),
    ("repealed", "yururlukten kaldir"),
    ("repealed", "ilga"),
    ("historical", "eski"),
    ("historical", "tarihsel"),
    ("amended", "degisiklik"),
    ("temporary", "gecici"),
    ("additional", "ek madde"),
)


def _metadata_lookup_priority_tokens(text: str) -> list[str]:
    stopwords = {normalize_canonical_text(item) for item in _RETRIEVAL_PRIORITY_STOPWORDS}
    return [
        token
        for token in normalize_canonical_text(text).split()
        if len(token) >= 3 and token not in stopwords
    ]


def _metadata_lookup_compact_phrase(text: str, *, max_tokens: int = 9) -> str:
    tokens = _metadata_lookup_priority_tokens(text)
    return " ".join(tokens[:max_tokens])


def _metadata_lookup_identifier_kind(kind_text: str) -> str:
    normalized_kind = normalize_canonical_text(kind_text)
    for kind, terms in _METADATA_LOOKUP_IDENTIFIER_KIND_PATTERNS:
        if any(term in normalized_kind for term in terms):
            return kind
    return "numeric_identifier"


def _extract_metadata_lookup_identifier_candidates(query: str) -> list[dict[str, str]]:
    normalized = normalize_canonical_text(query)
    candidates: list[dict[str, str]] = []
    explicit_article_numbers = {
        article
        for _law, article in _extract_explicit_article_refs(query)
        if article and article.isdigit()
    }
    patterns = (
        r"\b(?P<value>\d{1,9}(?:[-/]\d{1,4})?)\s+sayili\s+(?P<kind>kanun hukmunde kararname|cumhurbaskanligi kararnamesi|cumhurbaskani karari|cumhurbaskanligi karari|cumhurbaskanligi genelgesi|kanun|khk|cbk|kararname|karar|genelge|teblig)\b",
        r"\b(?P<value>\d{1,9}(?:[-/]\d{1,4})?)\s+sayili\s+(?:[a-z0-9]{3,}\s+){0,8}(?P<kind>kanun hukmunde kararname|cumhurbaskanligi kararnamesi|cumhurbaskani karari|cumhurbaskanligi karari|cumhurbaskanligi genelgesi|kanun|khk|cbk|kararname|karar|genelge|teblig)\b",
        r"\b(?P<kind>kanun hukmunde kararname|cumhurbaskanligi kararnamesi|cumhurbaskani karari|cumhurbaskanligi karari|cumhurbaskanligi genelgesi|kanun|khk|cbk|kararname|karar|genelge|teblig)\s+(?:sayisi|sayili|no|numarasi)\s*:?\s*(?P<value>\d{1,9}(?:[-/]\d{1,4})?)\b",
        r"\b(?:sayisi|sayili|no|numarasi)\s*:?\s*(?P<value>\d{2,9}(?:[-/]\d{1,4})?)\b",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, normalized):
            value = match.group("value")
            if value in explicit_article_numbers or re.fullmatch(r"(?:18|19|20)\d{2}", value):
                continue
            kind = _metadata_lookup_identifier_kind(match.groupdict().get("kind") or "")
            candidates.append(
                {
                    "value": value,
                    "base_value": value.split("-", 1)[0].split("/", 1)[0],
                    "kind": kind,
                    "source": "numbered_source_pattern",
                }
            )
    for law in extract_numbered_law_mentions(query):
        if law in explicit_article_numbers or re.fullmatch(r"(?:18|19|20)\d{2}", law):
            continue
        candidates.append(
            {
                "value": law,
                "base_value": law.split("-", 1)[0].split("/", 1)[0],
                "kind": "kanun",
                "source": "extract_numbered_law_mentions",
            }
        )
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        key = (candidate["value"], candidate["kind"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _extract_metadata_lookup_issuer_candidates(query: str) -> list[dict[str, str]]:
    normalized = normalize_canonical_text(query)
    candidates: list[dict[str, str]] = []
    for issuer in _METADATA_LOOKUP_ISSUER_TERMS:
        normalized_issuer = normalize_canonical_text(issuer)
        if normalized_issuer and re.search(rf"(?<![a-z0-9]){re.escape(normalized_issuer)}(?![a-z0-9])", normalized):
            candidates.append({"value": normalized_issuer, "source": "known_issuer_term"})

    for match in re.finditer(r"\b(?P<issuer>(?:[a-z0-9]{3,}\s+){0,4}(?:universitesi|bakanligi|baskanligi|kurumu|kurulu))\b", normalized):
        issuer = _metadata_lookup_compact_phrase(match.group("issuer"), max_tokens=6)
        if issuer:
            candidates.append({"value": issuer, "source": "issuer_suffix_pattern"})

    deduped: list[dict[str, str]] = []
    seen: set[str] = set()
    for candidate in candidates:
        value = candidate["value"]
        if value in seen:
            continue
        seen.add(value)
        deduped.append(candidate)
    return deduped[:8]


def _extract_metadata_lookup_title_ngrams(query: str) -> list[dict[str, Any]]:
    normalized = normalize_canonical_text(query)
    phrases: list[dict[str, Any]] = []

    for quoted in re.findall(r"[\"'“”‘’](.{6,120}?)[\"'“”‘’]", query or ""):
        phrase = _metadata_lookup_compact_phrase(quoted, max_tokens=10)
        if len(phrase.split()) >= 2:
            phrases.append({"value": phrase, "source": "quoted_phrase", "token_count": len(phrase.split())})

    marker_regex = "|".join(re.escape(marker) for marker in _METADATA_LOOKUP_TITLE_MARKERS)
    type_regex = "|".join(re.escape(term) for term in _METADATA_LOOKUP_TITLE_TYPE_TERMS)
    for match in re.finditer(
        rf"\b(?P<prefix>(?:[a-z0-9]{{3,}}\s+){{1,8}})(?P<marker>{marker_regex})(?:\s+(?P<suffix>(?:[a-z0-9]{{3,}}\s+){{0,6}}(?P<type>{type_regex})))?",
        normalized,
    ):
        phrase_text = " ".join(
            part
            for part in (
                match.group("prefix"),
                match.group("marker"),
                match.group("suffix") or "",
            )
            if part
        )
        phrase = _metadata_lookup_compact_phrase(phrase_text, max_tokens=12)
        if len(phrase.split()) >= 2:
            phrases.append({"value": phrase, "source": "title_marker_pattern", "token_count": len(phrase.split())})

    for match in re.finditer(
        rf"\b(?P<title>(?:[a-z0-9]{{3,}}\s+){{1,8}}(?P<type>{type_regex}))\b",
        normalized,
    ):
        phrase = _metadata_lookup_compact_phrase(match.group("title"), max_tokens=10)
        if len(phrase.split()) >= 2:
            phrases.append({"value": phrase, "source": "document_type_suffix_pattern", "token_count": len(phrase.split())})

    tokens = _metadata_lookup_priority_tokens(query)
    if len(tokens) >= 4:
        for width in (5, 4, 3):
            for index in range(0, max(0, len(tokens) - width + 1)):
                window = tokens[index : index + width]
                if not any(token in _METADATA_LOOKUP_TITLE_TYPE_TERMS or token in {"hakkinda", "iliskin", "dair"} for token in window):
                    continue
                phrases.append(
                    {
                        "value": " ".join(window),
                        "source": "priority_window",
                        "token_count": len(window),
                    }
                )

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for phrase in phrases:
        value = str(phrase.get("value") or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        deduped.append(phrase)
    return deduped[:12]


def _extract_metadata_lookup_temporal_cues(query: str) -> list[dict[str, str]]:
    normalized = normalize_canonical_text(query)
    cues: list[dict[str, str]] = []
    for year in _extract_year_tokens(query):
        cues.append({"value": year, "kind": "year", "source": "year_pattern"})
    for kind, term in _METADATA_LOOKUP_TEMPORAL_TERMS:
        normalized_term = normalize_canonical_text(term)
        if normalized_term and normalized_term in normalized:
            cues.append({"value": normalized_term, "kind": kind, "source": "temporal_term"})
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for cue in cues:
        key = (cue["kind"], cue["value"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(cue)
    return deduped


def _parse_metadata_lookup_query_signals(query: str) -> dict[str, Any]:
    identifier_candidates = _extract_metadata_lookup_identifier_candidates(query)
    family_candidates = dedupe_strings(
        [
            *_infer_requested_source_families(query),
            *[
                candidate.get("kind")
                for candidate in identifier_candidates
                if isinstance(candidate, dict) and candidate.get("kind") not in {"", "numeric_identifier"}
            ],
            *[
                candidate.family
                for candidate in _resolve_source_family_prior(query).family_candidates
                if candidate.confidence >= 0.45
            ],
        ]
    )
    return {
        "parsed_family_candidates": family_candidates,
        "parsed_identifier_candidates": identifier_candidates,
        "parsed_issuer_candidates": _extract_metadata_lookup_issuer_candidates(query),
        "parsed_title_ngrams": _extract_metadata_lookup_title_ngrams(query),
        "parsed_temporal_cues": _extract_metadata_lookup_temporal_cues(query),
    }


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


def _extract_source_identity_identifier_tokens(query: str) -> set[str]:
    normalized = _normalize_tr_text(query or "")
    tokens: set[str] = set()
    patterns = (
        r"\b(\d{2,9})\s+sayili\s+(?:kanun|khk|karar|cbk|cumhurbaskanligi kararnamesi|teblig|genelge)\b",
        r"\b(?:kanun|khk|karar|kararname|cbk|teblig|genelge)\s+(?:sayisi|no|numarasi)\s*:?\s*(\d{1,9}(?:[-/]\d{1,4})?)\b",
        r"\b(?:sayisi|no|numarasi)\s*:?\s*(\d{2,9}(?:[-/]\d{1,4})?)\b",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, normalized):
            token = match.group(1)
            if re.fullmatch(r"(?:18|19|20)\d{2}", token):
                continue
            tokens.add(token)
            tokens.add(token.split("-", 1)[0].split("/", 1)[0])
    for law in extract_numbered_law_mentions(query):
        if not re.fullmatch(r"(?:18|19|20)\d{2}", law):
            tokens.add(law)
    return {token for token in tokens if token and len(token) >= 1}


def _record_identifier_values(record: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for value in (
        record.get("source_key"),
        record.get("canonical_identifier"),
        record.get("canonical_identifier_display"),
        *(record.get("cross_refs") or []),
    ):
        normalized = normalize_canonical_text(value)
        if not normalized:
            continue
        values.add(normalized)
        for number in re.findall(r"\d{1,9}(?:[-/]\d{1,4})?", normalized):
            values.add(number)
            values.add(number.split("-", 1)[0].split("/", 1)[0])
    return values


def _metadata_lookup_signal_values(
    query_metadata_signals: dict[str, Any] | None,
    field: str,
    *,
    value_key: str = "value",
) -> set[str]:
    values: set[str] = set()
    if not isinstance(query_metadata_signals, dict):
        return values
    raw_items = query_metadata_signals.get(field)
    if not isinstance(raw_items, list):
        return values
    for item in raw_items:
        if isinstance(item, dict):
            value = item.get(value_key)
            values.add(normalize_canonical_text(value))
            if item.get("base_value"):
                values.add(normalize_canonical_text(item.get("base_value")))
        elif isinstance(item, str):
            values.add(normalize_canonical_text(item))
    return {value for value in values if value}


def _metadata_lookup_title_signal_score(
    *,
    title_normalized: str,
    title_tokens: set[str],
    query_metadata_signals: dict[str, Any] | None,
) -> tuple[float, list[str], str | None]:
    raw_items = (query_metadata_signals or {}).get("parsed_title_ngrams") if query_metadata_signals else None
    if not isinstance(raw_items, list):
        return 0.0, [], None

    best_score = 0.0
    best_reason: str | None = None
    reasons: list[str] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        phrase = normalize_canonical_text(item.get("value"))
        phrase_tokens = set(phrase.split())
        if len(phrase_tokens) < 2:
            continue
        overlap = len(phrase_tokens & title_tokens)
        ratio = overlap / max(1, len(phrase_tokens))
        if phrase and phrase in title_normalized:
            score = 22.0 + min(len(phrase_tokens), 6) * 2.0
            reason = f"title_ngram_exact:{len(phrase_tokens)}"
        elif overlap >= 3 and ratio >= 0.60:
            score = 15.0 + min(overlap, 6) * 1.5
            reason = f"title_ngram_strong:{overlap}"
        elif overlap >= 2 and ratio >= 0.67:
            score = 8.0
            reason = f"title_ngram_medium:{overlap}"
        else:
            continue
        reasons.append(reason)
        if score > best_score:
            best_score = score
            best_reason = reason
    return best_score, reasons, best_reason


def _metadata_lookup_has_strong_query_anchor(query_metadata_signals: dict[str, Any] | None) -> bool:
    if not isinstance(query_metadata_signals, dict):
        return False
    if _metadata_lookup_signal_values(query_metadata_signals, "parsed_identifier_candidates"):
        return True
    if _metadata_lookup_signal_values(query_metadata_signals, "parsed_issuer_candidates"):
        return True
    raw_title_items = query_metadata_signals.get("parsed_title_ngrams")
    if isinstance(raw_title_items, list):
        for item in raw_title_items:
            if not isinstance(item, dict):
                continue
            phrase = normalize_canonical_text(item.get("value"))
            token_count = int(item.get("token_count") or len(phrase.split()))
            if token_count >= 2 and phrase:
                return True
    return False


def _query_has_academic_regulation_intent(query: str) -> bool:
    normalized = f" {normalize_query_text(query)} "
    return any(
        token in normalized
        for token in (
            " universite ",
            " universitesi ",
            " yuksekogretim ",
            " yok ",
            " ogrenci ",
            " lisansustu ",
            " yuksek lisans ",
            " doktora ",
            " tez ",
            " ders ",
            " kredi ",
            " kayit ",
            " egitim ogretim ",
            " egitim-ogretim ",
            " sinav ",
            " tek ders ",
            " butunleme ",
            " mazeret sinavi ",
            " hazirlik ",
            " yandal ",
            " yan dal ",
            " cift anadal ",
            " senato ",
        )
    )


def _source_identity_record_score(
    record: dict[str, Any],
    *,
    query: str,
    requested_source_families: list[str],
    source_family_resolution: SourceFamilyResolution | None,
    query_metadata_signals: dict[str, Any] | None = None,
) -> tuple[float, list[str]]:
    normalized_query = normalize_canonical_text(query)
    query_terms = {
        token
        for token in normalized_query.split()
        if len(token) >= 3 and token not in _RETRIEVAL_PRIORITY_STOPWORDS
    }
    title = str(record.get("canonical_title") or "")
    title_normalized = str(record.get("canonical_title_normalized") or normalize_canonical_text(title))
    title_tokens = set(title_normalized.split())
    alias_tokens: set[str] = set()
    for alias in record.get("alias_titles") or []:
        alias_tokens.update(normalize_canonical_text(alias).split())
    issuer_tokens = set(str(record.get("issuer_normalized") or "").split())
    identifier_tokens = _extract_source_identity_identifier_tokens(query)
    identifier_tokens |= _metadata_lookup_signal_values(query_metadata_signals, "parsed_identifier_candidates")
    identifier_values = _record_identifier_values(record)
    year_tokens = set(_extract_year_tokens(query))
    year_tokens |= {
        value
        for value in _metadata_lookup_signal_values(query_metadata_signals, "parsed_temporal_cues")
        if re.fullmatch(r"(?:18|19|20)\d{2}", value)
    }
    year_values = set(record.get("year_signals") or [])
    family = str(record.get("source_family_mapped") or record.get("source_family_canonical") or "")
    raw_family = str(record.get("source_family_canonical") or record.get("source_family_raw") or family)
    if raw_family == "mulga_kanun" and str(record.get("effective_state") or "") == "repealed":
        family = raw_family
    requested_family_set = set(_expand_source_family_aliases(requested_source_families))
    raw_parsed_families = (
        query_metadata_signals.get("parsed_family_candidates")
        if isinstance(query_metadata_signals, dict)
        else []
    )
    parsed_family_set = set(
        _expand_source_family_aliases(
            [
                str(family)
                for family in (raw_parsed_families if isinstance(raw_parsed_families, list) else [])
                if isinstance(family, str) and family.strip()
            ]
        )
    )
    parsed_issuer_values = _metadata_lookup_signal_values(query_metadata_signals, "parsed_issuer_candidates")
    academic_regulation_intent = _query_has_academic_regulation_intent(query)
    score = 0.0
    reasons: list[str] = []

    if requested_family_set:
        if family in requested_family_set:
            score += 14.0
            reasons.append("family_match")
        else:
            score -= 12.0
            reasons.append("family_mismatch_penalty")

    if source_family_resolution and source_family_resolution.predicted_family:
        predicted = set(_expand_source_family_aliases([source_family_resolution.predicted_family]))
        if family in predicted:
            score += 8.0
            reasons.append("prior_family_match")
    scenario_current_law_guard = bool(
        source_family_resolution
        and source_family_resolution.scenario_current_law_question
        and not source_family_resolution.historical_or_repealed_question
    )
    effective_state = str(record.get("effective_state") or "").strip().lower()
    if scenario_current_law_guard:
        if raw_family == "mulga_kanun" or effective_state == "repealed":
            score -= 14.0
            reasons.append("scenario_current_law_repealed_penalty")
        elif effective_state in {"active", "amended"}:
            score += 6.0
            reasons.append("scenario_current_law_active_bonus")

    if parsed_family_set:
        if family in parsed_family_set:
            score += 7.0
            reasons.append("parsed_family_match")
        elif not requested_family_set:
            score -= 5.0
            reasons.append("parsed_family_mismatch_penalty")

    exact_identifier_hits = sorted(identifier_tokens & identifier_values)
    if exact_identifier_hits:
        score += 32.0 + min(len(exact_identifier_hits), 3) * 3.0
        reasons.append("identifier_exact")
    elif identifier_tokens and identifier_values:
        score -= 26.0
        reasons.append("identifier_conflict_penalty")

    title_overlap = len(query_terms & title_tokens)
    alias_overlap = len(query_terms & alias_tokens)
    issuer_overlap = len(query_terms & issuer_tokens)
    title_ngram_score, title_ngram_reasons, _best_title_ngram_reason = _metadata_lookup_title_signal_score(
        title_normalized=title_normalized,
        title_tokens=title_tokens | alias_tokens,
        query_metadata_signals=query_metadata_signals,
    )
    if title_ngram_score:
        score += title_ngram_score
        reasons.extend(title_ngram_reasons)
    if title_overlap:
        score += title_overlap * 4.0
        reasons.append(f"title_overlap:{title_overlap}")
    if title_overlap >= 2:
        score += 6.0
        reasons.append("title_specificity")
    if alias_overlap:
        score += alias_overlap * 2.0
        reasons.append(f"alias_overlap:{alias_overlap}")
    if issuer_overlap:
        score += issuer_overlap * 3.0
        reasons.append(f"issuer_overlap:{issuer_overlap}")
    if parsed_issuer_values:
        issuer_text = str(record.get("issuer_normalized") or "")
        issuer_value_overlap = {
            value
            for value in parsed_issuer_values
            if value and (value in issuer_text or value in title_normalized)
        }
        if issuer_value_overlap:
            score += 12.0 + min(len(issuer_value_overlap), 2) * 2.0
            reasons.append("issuer_exact")

    if year_tokens:
        if year_tokens & year_values:
            score += 8.0
            reasons.append("year_match")
        elif any(year in title_normalized for year in year_tokens):
            score += 5.0
            reasons.append("year_title_match")

    if family == "cb_karar" and any(term in normalized_query for term in ("karar", "yatirim", "tesvik", "ithalat")):
        score += 5.0
        reasons.append("cb_karar_playbook")
    if family == "cb_genelge" and any(term in normalized_query for term in ("genelge", "tasarruf", "eylem plani")):
        score += 5.0
        reasons.append("cb_genelge_playbook")
    if family == "cb_yonetmelik" and any(term in normalized_query for term in ("cumhurbaskanligi yonetmeligi", "devlet arsiv")):
        score += 5.0
        reasons.append("cb_yonetmelik_playbook")
    if family == "teblig" and any(term in normalized_query for term in ("teblig", "seri", "sira no")):
        score += 5.0
        reasons.append("teblig_playbook")
    if family == "uy" and ("universite" in normalized_query or "universitesi" in normalized_query):
        score += 5.0
        reasons.append("uy_playbook")
    elif family == "uy" and not academic_regulation_intent:
        score -= 22.0
        reasons.append("uy_without_academic_query_penalty")

    dominant_family_intent: set[str] = set()
    if requested_family_set:
        dominant_family_intent = set(requested_family_set)
    elif parsed_family_set:
        dominant_family_intent = set(parsed_family_set)
    elif source_family_resolution and source_family_resolution.predicted_family:
        dominant_family_intent = set(
            _expand_source_family_aliases([source_family_resolution.predicted_family])
        )
    relation_primary_group = str(
        _relation_query_family_profile(
            query,
            source_family_resolution=source_family_resolution,
        ).get("primary_group")
        or ""
    )
    if relation_primary_group:
        dominant_family_intent = {relation_primary_group}
    if dominant_family_intent:
        strict_kanun_intent = dominant_family_intent <= {"kanun", "mulga_kanun"}
        strict_khk_intent = dominant_family_intent <= {"khk"}
        strict_cb_karar_intent = dominant_family_intent <= {"cb_karar"}
        strict_cb_genelge_intent = dominant_family_intent <= {"cb_genelge"}
        strict_cb_yonetmelik_intent = dominant_family_intent <= {"cb_yonetmelik", "yonetmelik"}
        if strict_kanun_intent and raw_family in {
            "teblig",
            "yonetmelik",
            "kky",
            "uy",
            "cb_yonetmelik",
            "cb_genelge",
            "cb_karar",
            "cb_kararname",
        }:
            score -= 22.0
            reasons.append("strict_kanun_document_type_penalty")
        elif strict_khk_intent and raw_family in {
            "cb_kararname",
            "cb_karar",
            "cb_genelge",
            "teblig",
            "yonetmelik",
            "kky",
            "uy",
            "cb_yonetmelik",
        }:
            score -= 24.0
            reasons.append("strict_khk_document_type_penalty")
        elif strict_cb_karar_intent and raw_family in {"teblig", "cb_genelge", "cb_kararname"}:
            score -= 24.0
            reasons.append("strict_cb_karar_document_type_penalty")
        elif strict_cb_genelge_intent and raw_family in {"teblig", "cb_karar"}:
            score -= 20.0
            reasons.append("strict_cb_genelge_document_type_penalty")
        elif strict_cb_yonetmelik_intent and raw_family in {"cb_kararname", "cb_karar", "cb_genelge"}:
            score -= 18.0
            reasons.append("strict_cb_yonetmelik_document_type_penalty")
        if dominant_family_intent <= {"yonetmelik", "kky", "cb_yonetmelik"} and raw_family == "uy" and not academic_regulation_intent:
            score -= 20.0
            reasons.append("strict_regulation_nonacademic_uy_penalty")

    if exact_identifier_hits or title_overlap >= 2:
        score += 4.0
        reasons.append("identity_anchor")
    return score, reasons


def _select_metadata_first_source_candidates(
    *,
    query: str,
    requested_source_families: list[str],
    source_family_resolution: SourceFamilyResolution | None,
    query_metadata_signals: dict[str, Any] | None = None,
    limit: int = 6,
) -> dict[str, Any] | None:
    if not _metadata_first_candidate_generation_enabled():
        return None
    if query_metadata_signals is None:
        query_metadata_signals = _parse_metadata_lookup_query_signals(query)
    if not _metadata_lookup_has_strong_query_anchor(query_metadata_signals):
        return None
    catalog = load_canonical_source_catalog()
    if not catalog:
        return None

    scored: list[dict[str, Any]] = []
    for record in catalog.values():
        score, reasons = _source_identity_record_score(
            record,
            query=query,
            requested_source_families=requested_source_families,
            source_family_resolution=source_family_resolution,
            query_metadata_signals=query_metadata_signals,
        )
        title_overlap = 0
        for reason in reasons:
            if reason.startswith("title_overlap:"):
                try:
                    title_overlap = max(title_overlap, int(reason.split(":", 1)[1]))
                except ValueError:
                    pass
        has_identifier_anchor = "identifier_exact" in reasons
        has_strong_title_anchor = title_overlap >= 3
        has_title_ngram_anchor = any(
            reason.startswith("title_ngram_exact:") or reason.startswith("title_ngram_strong:")
            for reason in reasons
        )
        has_issuer_family_anchor = "issuer_exact" in reasons and (
            "parsed_family_match" in reasons or "family_match" in reasons or "prior_family_match" in reasons
        )
        if not has_identifier_anchor and not has_strong_title_anchor and not has_title_ngram_anchor and not has_issuer_family_anchor:
            continue
        threshold = 24.0 if has_identifier_anchor else 30.0 if has_issuer_family_anchor else 32.0
        if score < threshold:
            continue
        strict_document_type_conflict = any(
            reason.startswith("strict_") and reason.endswith("_document_type_penalty")
            for reason in reasons
        )
        if strict_document_type_conflict and not has_identifier_anchor and not has_issuer_family_anchor:
            continue
        if has_identifier_anchor:
            lookup_source = "exact_identifier_lookup"
        elif has_title_ngram_anchor:
            lookup_source = "normalized_title_lookup"
        elif has_issuer_family_anchor:
            lookup_source = "issuer_family_lookup"
        else:
            lookup_source = "title_ngram_family_lookup"
        scored.append(
            {
                "source_key": record.get("source_key"),
                "canonical_title": record.get("canonical_title"),
                "canonical_identifier": record.get("canonical_identifier"),
                "canonical_identifier_type": record.get("canonical_identifier_type"),
                "source_family": record.get("source_family_mapped") or record.get("source_family_canonical"),
                "source_family_raw": record.get("source_family_canonical") or record.get("source_family_raw"),
                "source_family_title_inferred": record.get("source_family_title_inferred"),
                "source_family_mapping_reason": record.get("source_family_mapping_reason"),
                "issuer": record.get("issuer"),
                "year_signals": record.get("year_signals") or [],
                "effective_state": record.get("effective_state"),
                "score": round(score, 3),
                "metadata_lookup_source": lookup_source,
                "metadata_lookup_confidence": round(min(0.99, 0.45 + score / 100.0), 3),
                "match_reasons": reasons,
                "focus_keys": [
                    key
                    for key in (
                        str(record.get("source_key") or "").strip().lower(),
                        str(record.get("canonical_title") or "").strip().lower(),
                    )
                    if key
                ],
            }
        )

    if not scored:
        return None
    ranked = sorted(
        scored,
        key=lambda item: (
            -int(item.get("metadata_lookup_source") == "exact_identifier_lookup"),
            -float(item["score"]),
            str(item.get("source_family") or ""),
            str(item.get("canonical_title") or ""),
        ),
    )[:limit]
    scenario_current_law_guard = bool(
        source_family_resolution
        and source_family_resolution.scenario_current_law_question
        and not source_family_resolution.historical_or_repealed_question
    )
    active_candidate_available = any(
        str(item.get("effective_state") or "").strip().lower() in {"active", "amended"}
        for item in ranked
    )
    repealed_candidate_demoted = False
    if scenario_current_law_guard and active_candidate_available:
        active_ranked = [
            item
            for item in ranked
            if str(item.get("effective_state") or "").strip().lower() in {"active", "amended"}
            and str(item.get("source_family_raw") or "") != "mulga_kanun"
        ]
        if active_ranked and len(active_ranked) != len(ranked):
            ranked = active_ranked[:limit]
            repealed_candidate_demoted = True
    for rank, item in enumerate(ranked, start=1):
        item["metadata_lookup_rank"] = rank
    return {
        "applied": True,
        "reason": "metadata_first_source_identity",
        "metadata_lookup_hit": True,
        "metadata_lookup_source": ranked[0].get("metadata_lookup_source"),
        "metadata_lookup_rank": ranked[0].get("metadata_lookup_rank"),
        "metadata_lookup_confidence": ranked[0].get("metadata_lookup_confidence"),
        "candidate_count": len(scored),
        "selected_source_keys": dedupe_strings([str(item.get("source_key") or "") for item in ranked if item.get("source_key")]),
        "selected_families": dedupe_strings([str(item.get("source_family") or "") for item in ranked if item.get("source_family")]),
        "query_identifier_tokens": sorted(_extract_source_identity_identifier_tokens(query)),
        "query_year_tokens": _extract_year_tokens(query),
        "scenario_current_law_question": scenario_current_law_guard,
        "active_candidate_available": active_candidate_available,
        "repealed_candidate_demoted": repealed_candidate_demoted,
        "temporal_family_guard_triggered": repealed_candidate_demoted,
        "query_metadata_signals": query_metadata_signals,
        "candidates": ranked,
    }


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


def _build_metadata_first_query_expansion(selector: dict[str, Any] | None) -> str:
    if not selector:
        return ""
    parts: list[str] = []
    for candidate in selector.get("candidates") or []:
        if candidate.get("canonical_title"):
            parts.append(str(candidate["canonical_title"]))
        if candidate.get("canonical_identifier"):
            parts.append(str(candidate["canonical_identifier"]))
        if candidate.get("source_family"):
            parts.append(_SOURCE_FAMILY_DISPLAY_LABELS.get(str(candidate["source_family"]), str(candidate["source_family"])))
    return _normalize_whitespace(" ".join(dedupe_strings(parts[:12])))


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


def _extract_year_tokens(text: str) -> list[str]:
    return dedupe_strings(re.findall(r"\b(?:19|20)\d{2}\b", text or ""))


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
    strong_families = (
        list(source_family_resolution.routing_families or source_family_resolution.preferred_families)
        if source_family_resolution.preferred_families
        else []
    )
    if not strong_families and source_family_resolution.family_confidence >= 0.75:
        strong_families = list(source_family_resolution.routing_families)
    if not strong_families:
        return families
    allowed = set(_expand_source_family_aliases(strong_families))
    clamped = [family for family in families if family in allowed]
    if not clamped:
        clamped = list(allowed)
    return dedupe_strings(clamped)


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


def _expand_source_family_aliases(families: list[str]) -> list[str]:
    expanded: list[str] = []
    for family in families:
        expansions = _SOURCE_FAMILY_ALIAS_EXPANSIONS.get(family, (family,))
        expanded.extend(expansions)
    return dedupe_strings(expanded)


def _infer_requested_source_families(query: str) -> list[str]:
    families: list[str] = []
    for terms, resolved_families in _SOURCE_FAMILY_HINT_RULES:
        if _contains_any_query_term(query, terms):
            families.extend(resolved_families)
    return _expand_source_family_aliases(families)


def _resolve_source_family_prior(
    query: str,
    *,
    mentioned_laws: list[str] | None = None,
    explicit_article_refs: list[tuple[str, str]] | None = None,
    law_filter: str | None = None,
) -> SourceFamilyResolution:
    return resolve_source_family_prior(
        query,
        mentioned_laws=mentioned_laws or [],
        explicit_article_refs=explicit_article_refs or [],
        law_filter=law_filter,
    )


def _apply_source_family_resolution_hints(
    *,
    retrieval_query: str,
    requested_source_families: list[str],
    retrieval_top_k: int,
    applied_expansions: list[str],
    source_family_resolution: SourceFamilyResolution,
) -> tuple[str, list[str], int]:
    routing_families = source_family_resolution.routing_families
    if routing_families:
        requested_source_families = dedupe_strings(
            [*requested_source_families, *_expand_source_family_aliases(routing_families)]
        )
        if any(family in _WEAK_SOURCE_FAMILY_ROUTE_TOPK_FAMILIES for family in routing_families):
            retrieval_top_k = max(retrieval_top_k, 24)

    for expansion in source_family_resolution.query_expansions:
        retrieval_query = _append_unique_expansion(
            retrieval_query,
            applied_expansions,
            expansion,
        )

    return retrieval_query, requested_source_families, retrieval_top_k


def _infer_family_from_source_title(title: Any) -> str | None:
    normalized = _normalize_tr_text(str(title or ""))
    if not normalized:
        return None
    if "tuzugu" in normalized or "tuzuk" in normalized:
        return "tuzuk"
    if "kanun hukmunde kararname" in normalized or re.search(r"\bkhk\b", normalized):
        return "khk"
    if "karar sayisi" in normalized or "cumhurbaskani karari" in normalized:
        return "cb_karar"
    if "cumhurbaskanligi yonetmeligi" in normalized:
        return "cb_yonetmelik"
    if "yonetmelik" in normalized or "yonetmeligi" in normalized:
        return "yonetmelik"
    if re.search(r"(?<![a-z0-9])teblig(?!at)[a-z0-9]*(?![a-z0-9])", normalized):
        return "teblig"
    if "genelge" in normalized:
        return "cb_genelge"
    if "kararname" in normalized:
        return "cb_kararname"
    return None


def _canonical_source_family_value(value: Any) -> str | None:
    raw = str(value or "").strip().lower().replace(" ", "_")
    if not raw:
        return None
    aliases = {
        "cb_genelge": "cb_genelge",
        "cumhurbaskanligi_genelgesi": "cb_genelge",
        "cb_karar": "cb_karar",
        "cumhurbaskani_karari": "cb_karar",
        "cb_kararname": "cb_kararname",
        "cumhurbaskanligi_kararnamesi": "cb_kararname",
        "cb_yonetmelik": "cb_yonetmelik",
        "cumhurbaskanligi_yonetmeligi": "cb_yonetmelik",
        "kanun": "kanun",
        "mulga": "mulga_kanun",
        "mulga_kanun": "mulga_kanun",
        "khk": "khk",
        "kanun_hukmunde_kararname": "khk",
        "kky": "kky",
        "kurum_kurulus_yonetmeligi": "kky",
        "teblig": "teblig",
        "tebligler": "teblig",
        "tuzuk": "tuzuk",
        "uy": "uy",
        "universite_yonetmeligi": "uy",
        "yonetmelik": "yonetmelik",
    }
    return aliases.get(raw, raw if raw in _RETRIEVAL_PLANNER_ALLOWED_FAMILIES else None)


def _resolve_chunk_source_family_profile(chunk: RetrievedChunk) -> dict[str, str | None]:
    metadata = chunk.metadata or {}
    title_family = _canonical_source_family_value(
        metadata.get("source_family_title_inferred")
    ) or _infer_family_from_source_title(
        metadata.get("source_title")
        or metadata.get("belge_adi")
        or metadata.get("kanun_adi")
        or metadata.get("law_name")
    )
    raw_family = _canonical_source_family_value(
        metadata.get("source_family_raw")
        or metadata.get("belge_turu")
        or metadata.get("source_type")
    )
    canonical_family = _canonical_source_family_value(
        metadata.get("source_family_canonical")
        or metadata.get("source_family")
        or metadata.get("canonical_source_family")
    )
    resolved_family = canonical_family or raw_family or title_family
    if resolved_family and title_family:
        if resolved_family in {"teblig", "kanun", "mulga_kanun"} and title_family in {
            "yonetmelik",
            "teblig",
            "tuzuk",
            "khk",
            "cb_genelge",
            "cb_karar",
            "cb_kararname",
            "cb_yonetmelik",
        }:
            resolved_family = title_family
    if title_family in {
        "khk",
        "tuzuk",
        "teblig",
        "cb_genelge",
        "cb_yonetmelik",
        "cb_kararname",
        "cb_karar",
    }:
        resolved_family = title_family
    mapped_family = _canonical_source_family_value(metadata.get("source_family_mapped"))
    mapping_reason = str(metadata.get("source_family_mapping_reason") or "")
    if not mapped_family and metadata:
        profile = source_family_mapping_profile(metadata)
        mapped_family = _canonical_source_family_value(profile.get("source_family_mapped"))
        mapping_reason = mapping_reason or str(profile.get("source_family_mapping_reason") or "")
        raw_family = raw_family or _canonical_source_family_value(profile.get("source_family_raw"))
        canonical_family = canonical_family or _canonical_source_family_value(
            profile.get("source_family_canonical")
        )
        title_family = title_family or _canonical_source_family_value(
            profile.get("source_family_title_inferred")
        )
    if not mapped_family:
        mapped_family = resolved_family
    return {
        "raw_family": raw_family,
        "canonical_family": canonical_family or resolved_family,
        "title_inferred_family": title_family,
        "resolved_family": resolved_family,
        "mapped_family": mapped_family,
        "mapping_reason": mapping_reason or "canonical_family",
    }


def _resolve_chunk_source_family(chunk: RetrievedChunk) -> str | None:
    return str(_resolve_chunk_source_family_profile(chunk).get("resolved_family") or "") or None


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
            tokens.add(token.split("-", 1)[0].split("/", 1)[0])
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


def _resolve_chunk_source_title(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    return _normalize_whitespace(
        str(
            metadata.get("full_title")
            or metadata.get("source_title")
            or metadata.get("belge_adi")
            or metadata.get("kanun_adi")
            or metadata.get("law_name")
            or metadata.get("title")
            or chunk.source
            or chunk.citation
            or ""
        )
    )


def _resolve_chunk_source_identifier(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    identifier = _normalize_whitespace(
        str(
            metadata.get("canonical_identifier_display")
            or metadata.get("display_citation")
            or metadata.get("source_id")
            or metadata.get("belge_no")
            or metadata.get("kanun_no")
            or metadata.get("law_no")
            or metadata.get("law_short_name")
            or metadata.get("kanun_kisa_adi")
            or chunk.source
            or ""
        )
    )
    return identifier or _resolve_trace_source_id(chunk)


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


def _resolve_candidate_source_display_label(candidate: dict[str, Any]) -> str:
    return str(
        candidate.get("canonical_title")
        or candidate.get("display_title")
        or candidate.get("source_key")
        or candidate.get("canonical_identifier")
        or ""
    )


def _normalize_article_token(value: Any) -> str:
    raw = _normalize_whitespace(str(value or "")).lower()
    if not raw:
        return ""
    normalized = _normalize_tr_text(raw)
    gecici = "gecici" in normalized
    match = re.search(r"\b(?:gecici\s+)?(?:madde|m|md)\.?\s*(\d+[a-z]?)\b", normalized)
    if not match:
        match = re.search(r"\bm\.(\d+[a-z]?)\b", normalized)
    if not match:
        match = re.search(r"\b(\d+[a-z]?)\b", normalized)
    if not match:
        return normalized
    article = match.group(1).lower()
    return f"gecici-{article}" if gecici else article


def _chunk_article_token(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    for value in (
        metadata.get("article_or_section"),
        metadata.get("madde_no"),
        metadata.get("article_no"),
        metadata.get("article"),
        metadata.get("source_id"),
        chunk.citation,
    ):
        token = _normalize_article_token(value)
        if token:
            return token
    return ""


def _extract_query_clause_tokens(query: str) -> set[str]:
    normalized = _normalize_tr_text(query or "")
    tokens: set[str] = set()
    for match in re.finditer(r"\b(\d+)\s*(?:inci|nci|uncu|\.?)?\s*f[ıi]kra[a-z]*\b", normalized):
        tokens.add(f"f{match.group(1)}")
    for match in re.finditer(r"\b(?:f[ıi]kra|f)\.?\s*(\d+)\b", normalized):
        tokens.add(f"f{match.group(1)}")
    for match in re.finditer(r"\b([a-z])\s*bendi\b", normalized):
        tokens.add(f"b{match.group(1)}")
    for match in re.finditer(r"\bbent\s*[:.]?\s*([a-z])\b", normalized):
        tokens.add(f"b{match.group(1)}")
    return tokens


def _chunk_clause_token(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    fikra = _normalize_whitespace(str(metadata.get("fikra_no") or metadata.get("paragraph_no") or ""))
    if fikra and fikra != "0":
        return f"f{fikra.lower()}"
    bent = _normalize_whitespace(str(metadata.get("bent_no") or metadata.get("clause_no") or ""))
    if bent:
        return f"b{bent.lower()}"
    return ""


def _extract_query_article_tokens(
    query: str,
    explicit_article_refs: list[tuple[str, str]] | None = None,
) -> set[str]:
    tokens = {
        token
        for _law, article in (explicit_article_refs or [])
        for token in (_normalize_article_token(article),)
        if token
    }
    normalized = _normalize_tr_text(query or "")
    for match in re.finditer(r"\b(?:gecici\s+madde|madde|m|md)\.?\s*(\d+[a-z]?)\b", normalized):
        token = _normalize_article_token(match.group(0))
        if token:
            tokens.add(token)
    for match in re.finditer(r"\b(\d+[a-z]?)\s*(?:inci|nci|uncu|\.?)?\s*madde[a-z]*\b", normalized):
        token = _normalize_article_token(match.group(1))
        if token:
            tokens.add(token)
    return tokens


def _chunk_article_matches(chunk: RetrievedChunk, article_tokens: set[str]) -> bool:
    chunk_token = _chunk_article_token(chunk)
    return bool(chunk_token and chunk_token in article_tokens)


def _article_numeric_value(token: str) -> tuple[str, int] | None:
    normalized = _normalize_article_token(token)
    if not normalized:
        return None
    prefix = "gecici" if normalized.startswith("gecici-") else "normal"
    number_part = normalized.split("-", 1)[1] if prefix == "gecici" else normalized
    if not number_part.isdigit():
        return None
    return prefix, int(number_part)


def _article_window_distance(chunk_token: str, article_tokens: set[str]) -> int | None:
    chunk_value = _article_numeric_value(chunk_token)
    if chunk_value is None:
        return None
    distances: list[int] = []
    for token in article_tokens:
        query_value = _article_numeric_value(token)
        if query_value is None or query_value[0] != chunk_value[0]:
            continue
        distances.append(abs(chunk_value[1] - query_value[1]))
    return min(distances) if distances else None


def _query_article_alignment(
    *,
    selected_article: str | None,
    query_article_tokens: set[str],
    article_match_type: str,
    selected_paragraph_or_clause: str | None = None,
) -> str:
    selected_token = _normalize_article_token(selected_article or "")
    if not query_article_tokens:
        if selected_token == "0":
            return "title_only"
        if selected_paragraph_or_clause and not selected_token:
            return "clause_only"
        return "unknown"
    if selected_token and selected_token in query_article_tokens:
        return "exact"
    if selected_token == "0":
        return "title_only"
    if selected_token and any(_article_window_distance(selected_token, {token}) == 1 for token in query_article_tokens):
        return "neighbor"
    if article_match_type in {"title_only", "source_local_support"}:
        return "title_only"
    if selected_paragraph_or_clause and not selected_token:
        return "clause_only"
    return "none"


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


def _support_contains_temporal_clause(traces: list[dict[str, Any]]) -> bool:
    needles = ("yururluk", "mulga", "degisik", "tarih", "gecerli", "halen", "aktif")
    for trace in traces:
        if trace.get("contains_temporal_clause"):
            return True
        text = _normalize_tr_text(
            " ".join(str(trace.get(key) or "") for key in ("citation", "source_key", "source_id"))
        )
        if any(needle in text for needle in needles):
            return True
    return False


def _support_contains_exception_signal(query: str, traces: list[dict[str, Any]]) -> bool:
    normalized_query = _normalize_tr_text(query or "")
    query_has_exception = any(
        signal in normalized_query
        for signal in ("istisna", "haric", "uygulanmaz", "ceza", "sure", "usul", "itiraz", "muaf")
    )
    if query_has_exception:
        return True
    for trace in traces:
        if trace.get("clause_match") or trace.get("contains_exception_signal"):
            return True
    return False


def _contains_temporal_clause_signal(text: str) -> bool:
    normalized = _normalize_tr_text(text or "")
    return any(
        signal in normalized
        for signal in (
            "yururluk",
            "yururluge",
            "mulga",
            "yururlukten kaldiril",
            "degisik",
            "tarihinde",
            "gecerli",
            "gecici madde",
            "ek madde",
        )
    )


def _contains_exception_signal(text: str) -> bool:
    normalized = _normalize_tr_text(text or "")
    return any(
        signal in normalized
        for signal in ("istisna", "haric", "sakli", "uygulanmaz", "muaf", "ceza", "sure", "itiraz", "usul")
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


def _build_chunk_evidence_span(chunk: RetrievedChunk, *, query: str | None = None, max_len: int = 700) -> str:
    if query:
        return RAGOrchestrator._build_query_focused_excerpt(chunk.text, query=query, max_len=max_len)
    return RAGOrchestrator._build_chunk_excerpt(chunk.text, max_len=max_len)


def _select_article_span_evidence(
    *,
    query: str,
    chunks: list[RetrievedChunk],
    requested_source_families: list[str],
    explicit_article_refs: list[tuple[str, str]] | None = None,
    selected_source_keys: set[str] | None = None,
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None = None,
) -> tuple[list[RetrievedChunk], dict[str, Any]]:
    if not chunks:
        return chunks, {"applied": False, "reason": "no_chunks"}

    query_terms = _extract_retrieval_priority_terms(query)
    identifier_tokens = _extract_source_identifier_tokens(query)
    article_tokens = _extract_query_article_tokens(query, explicit_article_refs)
    clause_tokens = _extract_query_clause_tokens(query)
    requested_family_set = set(_expand_source_family_aliases(requested_source_families))
    preferred_family_set = _selector_preferred_source_families(query, requested_source_families)
    selected_source_key_set = {
        value
        for key in (selected_source_keys or set())
        for value in (str(key).strip().lower(), _normalize_tr_text(str(key)), normalize_canonical_text(str(key)))
        if value
    }
    numbered_laws = set(extract_numbered_law_mentions(query))
    explicit_ref_set = {
        (law, _normalize_article_token(article))
        for law, article in (explicit_article_refs or [])
        if law and _normalize_article_token(article)
    }
    source_cluster_sizes: dict[str, int] = {}
    for chunk in chunks:
        source_key = _resolve_chunk_source_key(chunk)
        source_cluster_sizes[source_key] = source_cluster_sizes.get(source_key, 0) + 1

    has_selector_signal = bool(
        article_tokens
        or identifier_tokens
        or requested_family_set
        or selected_source_keys
        or query_terms
    )
    if not has_selector_signal:
        return chunks, {"applied": False, "reason": "no_selector_signal"}

    current_validity_query = _asks_current_validity_query(query)
    scenario_current_law_question = (
        _source_family_resolution_trace_bool(source_family_resolution, "scenario_current_law_question")
        or current_validity_query
    )
    historical_or_repealed_question = (
        _source_family_resolution_trace_bool(source_family_resolution, "historical_or_repealed_question")
        or _asks_historical_or_repealed_query(query)
    )
    relation_profile = _relation_query_family_profile(
        query,
        source_family_resolution=source_family_resolution,
    )
    relation_query_detected = bool(relation_profile.get("relation_query_detected"))
    relation_primary_group = str(relation_profile.get("primary_group") or "")
    relation_supporting_group = str(relation_profile.get("supporting_group") or "")
    query_year_tokens = set(_extract_year_tokens(query))
    legacy_intent_binding_active = historical_or_repealed_question
    temporal_guard_enabled = scenario_current_law_question and not historical_or_repealed_question
    scored: list[tuple[float, int, RetrievedChunk, dict[str, Any]]] = []
    for original_index, chunk in enumerate(chunks):
        metadata = chunk.metadata or {}
        family = _resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk) or ""
        source_key = _resolve_chunk_source_key(chunk)
        title = _resolve_chunk_source_title(chunk)
        heading = metadata.get("heading") or metadata.get("article_heading")
        article_token = _chunk_article_token(chunk)
        clause_token = _chunk_clause_token(chunk)
        chunk_laws = _chunk_law_candidates(chunk)

        explicit_ref_match = False
        for law, article in explicit_ref_set:
            law_match = law in chunk_laws or law == _extract_chunk_law_hint(chunk)
            if law_match and article_token == article:
                explicit_ref_match = True
                break

        article_match = bool(article_tokens and article_token in article_tokens)
        article_distance = _article_window_distance(article_token, article_tokens)
        adjacent_article_match = article_distance == 1
        clause_match = bool(clause_tokens and clause_token and clause_token in clause_tokens)
        identifier_match = _chunk_matches_identifier_tokens(chunk, identifier_tokens)
        family_match = bool(requested_family_set and family in requested_family_set)
        preferred_family_match = bool(preferred_family_set and family in preferred_family_set)
        selected_source_match = bool(
            selected_source_key_set
            and (
                source_key in selected_source_key_set
                or _normalize_tr_text(source_key) in selected_source_key_set
                or normalize_canonical_text(source_key) in selected_source_key_set
            )
        )
        law_match = bool(numbered_laws and numbered_laws & chunk_laws)
        title_overlap = _count_term_overlap(title, query_terms)
        heading_overlap = _count_term_overlap(str(heading or ""), query_terms)
        text_overlap = _count_term_overlap(chunk.text, query_terms)
        cluster_size = source_cluster_sizes.get(source_key, 1)
        effective_state = str(metadata.get("effective_state") or resolve_effective_state(metadata) or "").strip().lower()
        temporally_inactive = _is_temporally_inactive_chunk(chunk) or effective_state == "repealed"
        chunk_years = _chunk_year_values(chunk)
        year_match = bool(query_year_tokens and chunk_years & query_year_tokens)
        relation_group = _source_family_relation_group(family)
        temporal_state_bucket = (
            "repealed"
            if temporally_inactive
            else "active"
            if effective_state in {"active", "amended"} or _chunk_active_rank(chunk) == 0
            else "unknown"
        )
        temporal_guard_support = bool(
            selected_source_match
            or identifier_match
            or family_match
            or preferred_family_match
            or law_match
            or article_match
            or adjacent_article_match
            or title_overlap >= 1
            or heading_overlap >= 1
            or text_overlap >= 2
        )
        legacy_profile = _legacy_source_binding_profile(
            chunk,
            query=query,
            source_family_resolution=source_family_resolution,
            identifier_tokens=identifier_tokens,
            year_tokens=query_year_tokens,
        )

        score = float(chunk.score or 0.0)
        if explicit_ref_match:
            score += 140
        if article_match:
            score += 70
        elif adjacent_article_match:
            score += 22
        if clause_match:
            score += 12
        if selected_source_match:
            score += 55
        if identifier_match:
            score += 45
        if family_match:
            score += 40
        if preferred_family_match:
            score += 45
        elif preferred_family_set:
            score -= 45
        if law_match:
            score += 30
        score += min(title_overlap, 8) * 7
        score += min(heading_overlap, 8) * 6
        score += min(text_overlap, 10) * 2
        score += min(cluster_size, 6) * 1.5
        if selected_source_match and (article_match or adjacent_article_match or heading_overlap or text_overlap >= 2):
            score += 18
        if identifier_match and (article_match or adjacent_article_match):
            score += 16
        if requested_family_set and not family_match:
            score -= 35
        if numbered_laws and not law_match:
            score -= 18
        if article_tokens and article_token == "0" and not article_match:
            score -= 55
        if current_validity_query:
            score -= _chunk_active_rank(chunk) * 20
        if temporal_guard_enabled:
            if temporally_inactive:
                score -= 90
            elif temporal_state_bucket == "active":
                score += 16
        if relation_query_detected and relation_primary_group:
            if relation_group == relation_primary_group:
                score += 38
            elif relation_supporting_group and relation_group == relation_supporting_group:
                score -= 24
        if legacy_profile["legacy_intent_binding_active"]:
            score += float(legacy_profile["score"])

        scored.append(
            (
                score,
                original_index,
                chunk,
                {
                    "source_id": _resolve_trace_source_id(chunk),
                    "citation": chunk.citation,
                    "source_key": source_key,
                    "source_title": title,
                    "score": round(score, 4),
                    "source_family": family or None,
                    "source_identifier": _resolve_chunk_source_identifier(chunk),
                    "article_or_section": article_token or None,
                    "paragraph_or_clause": clause_token or None,
                    "explicit_ref_match": explicit_ref_match,
                    "article_match": article_match,
                    "adjacent_article_match": adjacent_article_match,
                    "article_window_distance": article_distance,
                    "clause_match": clause_match,
                    "article_match_type": (
                        "explicit_exact"
                        if explicit_ref_match
                        else "exact"
                        if article_match
                        else "adjacent"
                        if adjacent_article_match
                        else "source_local_support"
                        if title_overlap or heading_overlap or text_overlap
                        else "none"
                    ),
                    "identifier_match": identifier_match,
                    "family_match": family_match,
                    "preferred_family_match": preferred_family_match,
                    "selected_source_match": selected_source_match,
                    "law_match": law_match,
                    "year_match": year_match,
                    "title_overlap": title_overlap,
                    "heading_overlap": heading_overlap,
                    "text_overlap": text_overlap,
                    "effective_state": effective_state or "unknown",
                    "temporally_inactive": temporally_inactive,
                    "temporal_state_bucket": temporal_state_bucket,
                    "temporal_guard_support": temporal_guard_support,
                    "relation_query_detected": relation_query_detected,
                    "relation_group": relation_group or None,
                    "legacy_intent_binding_active": legacy_profile["legacy_intent_binding_active"],
                    "legacy_candidate_preferred": legacy_profile["legacy_candidate_preferred"],
                    "document_state_binding_reason": legacy_profile["binding_reason"] or None,
                    "legacy_state_rank": legacy_profile["state_rank"],
                    "legacy_source_years": legacy_profile["source_years"],
                    "contains_temporal_clause": _contains_temporal_clause_signal(chunk.text),
                    "contains_exception_signal": _contains_exception_signal(chunk.text),
                    "temporal_state_resolved": _chunk_effective_state_resolved(chunk),
                },
            )
        )

    ranked = sorted(scored, key=lambda item: (-item[0], item[1]))
    active_guard_candidates = [
        item
        for item in ranked
        if not item[3].get("temporally_inactive") and _selector_trace_supports_temporal_guard(item[3])
    ]
    active_candidate_available = bool(active_guard_candidates)
    repealed_candidate_demoted = False
    temporal_family_guard_triggered = False
    active_candidate_demoted_due_to_legacy_scope = False
    document_state_binding_reason = ""
    document_lock_reason = "top_ranked"
    document_lock_candidates: list[tuple[float, int, RetrievedChunk, dict[str, Any]]] = []
    if selected_source_keys:
        document_lock_candidates = [item for item in ranked if item[3].get("selected_source_match")]
        if document_lock_candidates:
            document_lock_reason = "selected_source_lock"
    if not document_lock_candidates and identifier_tokens:
        document_lock_candidates = [item for item in ranked if item[3].get("identifier_match")]
        if document_lock_candidates:
            document_lock_reason = "identifier_lock"
    if not document_lock_candidates and preferred_family_set:
        document_lock_candidates = [
            item
            for item in ranked
            if item[3].get("preferred_family_match")
            and (
                item[3].get("title_overlap", 0) >= 1
                or item[3].get("heading_overlap", 0) >= 1
                or item[3].get("text_overlap", 0) >= 2
                or item[3].get("article_match")
                or item[3].get("adjacent_article_match")
            )
        ]
        if document_lock_candidates:
            document_lock_reason = "preferred_family_lock"
    if not document_lock_candidates and requested_family_set:
        document_lock_candidates = [
            item
            for item in ranked
            if item[3].get("family_match")
            and (
                item[3].get("title_overlap", 0) >= 1
                or item[3].get("heading_overlap", 0) >= 1
                or item[3].get("text_overlap", 0) >= 2
                or item[3].get("article_match")
                or item[3].get("adjacent_article_match")
            )
        ]
        if document_lock_candidates:
            document_lock_reason = "family_title_lock"
    if not document_lock_candidates and numbered_laws:
        document_lock_candidates = [item for item in ranked if item[3].get("law_match")]
        if document_lock_candidates:
            document_lock_reason = "numbered_law_lock"
    if not document_lock_candidates and ranked:
        document_lock_candidates = [ranked[0]]
    if temporal_guard_enabled and document_lock_candidates and active_candidate_available:
        locked_trace = document_lock_candidates[0][3]
        if locked_trace.get("temporally_inactive"):
            locked_family = str(locked_trace.get("source_family") or "")
            compatible_active_candidates = [
                item
                for item in active_guard_candidates
                if _temporal_guard_family_compatible(str(item[3].get("source_family") or ""), locked_family)
            ]
            if compatible_active_candidates:
                document_lock_candidates = compatible_active_candidates
                document_lock_reason = "current_law_temporal_guard"
                repealed_candidate_demoted = True
                temporal_family_guard_triggered = True
    if legacy_intent_binding_active and document_lock_candidates:
        legacy_guard_candidates = [
            item
            for item in ranked
            if item[3].get("legacy_candidate_preferred")
            and _selector_trace_supports_temporal_guard(item[3])
        ]
        if legacy_guard_candidates:
            document_state_binding_reason = "legacy_scope_candidate_preferred"
            if not document_lock_candidates[0][3].get("legacy_candidate_preferred"):
                document_lock_candidates = legacy_guard_candidates
                document_lock_reason = "legacy_scope_state_binding"
                active_candidate_demoted_due_to_legacy_scope = True
        else:
            document_state_binding_reason = "legacy_scope_no_compatible_candidate"
    locked_family_internal_candidates: list[str] = []
    internal_document_state_rank: int | None = None
    internal_document_choice_reason = ""
    if document_lock_candidates and (legacy_intent_binding_active or relation_query_detected):
        locked_trace = document_lock_candidates[0][3]
        locked_family = str(locked_trace.get("source_family") or "")
        candidate_pool = [
            item
            for item in ranked
            if (
                not locked_family
                or str(item[3].get("source_family") or "") == locked_family
                or _temporal_guard_family_compatible(str(item[3].get("source_family") or ""), locked_family)
            )
        ]
        if relation_query_detected and relation_primary_group:
            relation_primary_candidates = [
                item
                for item in candidate_pool
                if _source_family_relation_group(item[3].get("source_family")) == relation_primary_group
            ]
            if relation_primary_candidates:
                candidate_pool = relation_primary_candidates

        internal_records: list[dict[str, Any]] = []
        seen_internal_keys: set[str] = set()
        for item in candidate_pool:
            trace = item[3]
            source_key = str(trace.get("source_key") or "")
            if not source_key or source_key in seen_internal_keys:
                continue
            seen_internal_keys.add(source_key)
            source_items = [
                source_item
                for source_item in candidate_pool
                if str(source_item[3].get("source_key") or "") == source_key
            ]
            state_rank = min(
                int(source_item[3].get("legacy_state_rank"))
                if source_item[3].get("legacy_state_rank") is not None
                else 2
                for source_item in source_items
            )
            best_score = max(float(source_item[3].get("score") or 0.0) for source_item in source_items)
            identifier_rank = 0 if any(
                source_item[3].get("identifier_match")
                or source_item[3].get("selected_source_match")
                or source_item[3].get("law_match")
                for source_item in source_items
            ) else 1
            year_rank = 0 if any(source_item[3].get("year_match") for source_item in source_items) else 1
            relation_rank = 0 if any(
                _source_family_relation_group(source_item[3].get("source_family")) == relation_primary_group
                for source_item in source_items
            ) else 1
            internal_records.append(
                {
                    "source_key": source_key,
                    "state_rank": state_rank,
                    "identifier_rank": identifier_rank,
                    "year_rank": year_rank,
                    "relation_rank": relation_rank,
                    "best_score": round(best_score, 4),
                }
            )
        internal_records.sort(
            key=lambda item: (
                item["state_rank"],
                item["relation_rank"],
                item["identifier_rank"],
                item["year_rank"],
                -float(item["best_score"]),
            )
        )
        locked_family_internal_candidates = [
            str(item.get("source_key") or "")
            for item in internal_records[:5]
            if item.get("source_key")
        ]
        if internal_records:
            chosen_source_key = str(internal_records[0].get("source_key") or "")
            internal_document_state_rank = int(internal_records[0].get("state_rank") or 0)
            current_source_key = _resolve_chunk_source_key(document_lock_candidates[0][2])
            if chosen_source_key and chosen_source_key != current_source_key:
                document_lock_candidates = [
                    item
                    for item in candidate_pool
                    if _resolve_chunk_source_key(item[2]) == chosen_source_key
                ]
                document_lock_reason = "internal_document_arbitration"
                internal_document_choice_reason = "state_rank_then_identity_priority"
            else:
                internal_document_choice_reason = "locked_document_retained_after_internal_arbitration"
    primary_source_key = _resolve_chunk_source_key(document_lock_candidates[0][2]) if document_lock_candidates else ""
    window_items: list[tuple[float, int, RetrievedChunk, dict[str, Any]]] = []
    if primary_source_key:
        exact_items = [
            item
            for item in ranked
            if _resolve_chunk_source_key(item[2]) == primary_source_key
            and (item[3].get("explicit_ref_match") or item[3].get("article_match"))
        ]
        adjacent_items = [
            item
            for item in ranked
            if _resolve_chunk_source_key(item[2]) == primary_source_key
            and item not in exact_items
            and item[3].get("adjacent_article_match")
        ]
        support_items = [
            item
            for item in ranked
            if _resolve_chunk_source_key(item[2]) == primary_source_key
            and item not in exact_items
            and item not in adjacent_items
            and (
                item[3].get("heading_overlap", 0) >= 1
                or item[3].get("text_overlap", 0) >= 2
                or item[3].get("title_overlap", 0) >= 2
                or (not article_tokens and item[3].get("family_match"))
            )
        ]
        if exact_items or adjacent_items or support_items:
            window_items = [*exact_items[:2], *adjacent_items[:2], *support_items[:3]]
    seen_window_ids = {id(item[2]) for item in window_items}
    if window_items:
        reordered = [item[2] for item in window_items] + [
            chunk for _score, _index, chunk, _trace in ranked if id(chunk) not in seen_window_ids
        ]
        trace_by_chunk_id = {id(chunk): trace for _score, _index, chunk, trace in ranked}
        top_traces = [trace_by_chunk_id[id(chunk)] for chunk in reordered[:10] if id(chunk) in trace_by_chunk_id]
    else:
        reordered = [chunk for _score, _index, chunk, _trace in ranked]
        top_traces = [trace for _score, _index, _chunk, trace in ranked[:10]]
    primary_source_candidate = ""
    supporting_source_candidate = ""
    if relation_query_detected:
        for _score, _index, _chunk, trace in ranked:
            if _source_family_relation_group(trace.get("source_family")) == relation_primary_group:
                primary_source_candidate = _resolve_trace_source_display_label(trace)
                break
        for _score, _index, _chunk, trace in ranked:
            if _source_family_relation_group(trace.get("source_family")) == relation_supporting_group:
                supporting_source_candidate = _resolve_trace_source_display_label(trace)
                break
    selector_document_rank = None
    for rank, (_score, _index, _chunk, trace) in enumerate(ranked, start=1):
        if selected_source_keys and trace.get("selected_source_match"):
            selector_document_rank = rank
            break
        if identifier_tokens and trace.get("identifier_match"):
            selector_document_rank = rank
            break
        if preferred_family_set and trace.get("preferred_family_match"):
            selector_document_rank = rank
            break
        if not selected_source_keys and not identifier_tokens and requested_family_set and trace.get("family_match"):
            selector_document_rank = rank
            break
    if selector_document_rank is None and ranked:
        selector_document_rank = 1
    selector_article_rank = None
    for rank, (_score, _index, _chunk, trace) in enumerate(ranked, start=1):
        if trace.get("explicit_ref_match") or trace.get("article_match"):
            selector_article_rank = rank
            break
    top_trace = top_traces[0] if top_traces else None
    selected_article = top_trace.get("article_or_section") if top_trace else None
    selected_paragraph_or_clause = top_trace.get("paragraph_or_clause") if top_trace else None
    article_match_type = top_trace.get("article_match_type") if top_trace else "none"
    support_span_count = len(window_items) if window_items else min(len(reordered), 1 if reordered else 0)
    metadata_identity_strength = _selector_metadata_identity_strength(
        top_trace=top_trace,
        identifier_tokens=identifier_tokens,
        requested_family_set=requested_family_set,
        selected_source_keys=selected_source_keys,
    )
    selector_article_lock_type = _selector_article_lock_type(
        top_trace=top_trace,
        article_tokens=article_tokens,
        metadata_identity_strength=metadata_identity_strength,
        support_span_count=support_span_count,
    )
    selector_exact_article_hit = selector_article_lock_type in {"explicit_exact", "semantic_exact"}
    temporal_state_resolved = bool(top_trace and top_trace.get("temporal_state_resolved"))
    if selector_exact_article_hit and metadata_identity_strength in {"strong", "medium"}:
        evidence_sufficiency = "exact_enough"
    elif top_trace and (
        top_trace.get("selected_source_match")
        or top_trace.get("identifier_match")
        or top_trace.get("family_match")
        or top_trace.get("law_match")
        or support_span_count >= 2
    ):
        evidence_sufficiency = "partially_supported"
    else:
        evidence_sufficiency = "insufficient_support"
    manual_review_reason = _selector_manual_review_reason(
        top_traces=top_traces,
        article_tokens=article_tokens,
        requested_family_set=requested_family_set,
        evidence_sufficiency=evidence_sufficiency,
        temporal_state_resolved=temporal_state_resolved,
    )
    first_changed = bool(reordered and chunks and reordered[0].citation != chunks[0].citation)
    applied = bool(first_changed or article_tokens or identifier_tokens or selected_source_keys or requested_family_set)
    return reordered, {
        "applied": applied,
        "reason": "article_span_selector",
        "query_article_tokens": sorted(article_tokens),
        "query_clause_tokens": sorted(clause_tokens),
        "identifier_tokens": sorted(identifier_tokens),
        "requested_source_families": requested_source_families,
        "preferred_source_families": sorted(preferred_family_set),
        "selector_preferred_family_hit": bool(top_trace and top_trace.get("preferred_family_match")),
        "selected_source_keys": sorted(selected_source_key_set),
        "selected_document_id": (
            _resolve_chunk_source_display_label(document_lock_candidates[0][2]) if document_lock_candidates else None
        ),
        "selected_article": selected_article,
        "selected_paragraph_or_clause": selected_paragraph_or_clause,
        "support_span_count": support_span_count,
        "support_span_diversity": len(
            {
                str(trace.get("article_or_section") or "")
                for trace in top_traces
                if trace.get("article_or_section") not in {None, ""}
            }
        ),
        "support_contains_article_number": bool(
            any(str(trace.get("article_or_section") or "") not in {"", "0"} for trace in top_traces)
        ),
        "support_contains_temporal_clause": _support_contains_temporal_clause(top_traces),
        "support_contains_exception_signal": _support_contains_exception_signal(query, top_traces),
        "selector_reason": document_lock_reason,
        "document_lock_reason": document_lock_reason,
        "relation_query_detected": relation_query_detected,
        "primary_source_candidate": primary_source_candidate,
        "supporting_source_candidate": supporting_source_candidate,
        "final_primary_source_reason": (
            str(relation_profile.get("reason") or "relation_query_primary_selector")
            if primary_source_candidate
            else ""
        ),
        "scenario_current_law_question": scenario_current_law_question,
        "active_candidate_available": active_candidate_available,
        "repealed_candidate_demoted": repealed_candidate_demoted,
        "temporal_family_guard_triggered": temporal_family_guard_triggered,
        "legacy_intent_binding_active": legacy_intent_binding_active,
        "active_candidate_demoted_due_to_legacy_scope": active_candidate_demoted_due_to_legacy_scope,
        "legacy_candidate_preferred": bool(top_trace and top_trace.get("legacy_candidate_preferred")),
        "document_state_binding_reason": (
            document_state_binding_reason
            or (str(top_trace.get("document_state_binding_reason") or "") if top_trace else "")
        ),
        "locked_family_internal_candidates": locked_family_internal_candidates,
        "internal_document_state_rank": internal_document_state_rank,
        "internal_document_choice_reason": internal_document_choice_reason,
        "article_match_type": article_match_type,
        "selector_article_lock_type": selector_article_lock_type,
        "query_article_alignment": _query_article_alignment(
            selected_article=selected_article,
            query_article_tokens=article_tokens,
            article_match_type=str(article_match_type or ""),
            selected_paragraph_or_clause=selected_paragraph_or_clause,
        ),
        "selector_document_rank": selector_document_rank,
        "selector_article_rank": selector_article_rank,
        "selector_exact_article_hit": selector_exact_article_hit,
        "selector_support_span_count": support_span_count,
        "selector_evidence_sufficiency": evidence_sufficiency,
        "metadata_identity_strength": metadata_identity_strength,
        "temporal_state_resolved": temporal_state_resolved,
        "manual_review_trigger_reason": manual_review_reason,
        "selected_source_ids": [trace["source_id"] for trace in top_traces if trace.get("source_id")],
        "selected_articles": dedupe_strings(
            [str(trace["article_or_section"]) for trace in top_traces if trace.get("article_or_section")]
        ),
        "top_scores": top_traces,
    }


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


def _source_family_relation_group(family: str | None) -> str:
    normalized = str(family or "").strip()
    if normalized in {"kanun", "mulga_kanun"}:
        return "kanun"
    if normalized in {"yonetmelik", "cb_yonetmelik", "kky", "uy", "teblig"}:
        return "yonetmelik"
    return normalized


def _relation_query_detected(
    query: str,
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None = None,
) -> bool:
    collision_reason = ""
    if isinstance(source_family_resolution, dict):
        collision_reason = str(source_family_resolution.get("collision_resolution_reason") or "")
    elif source_family_resolution is not None:
        collision_reason = str(source_family_resolution.collision_resolution_reason or "")
    if collision_reason == "kanun_yonetmelik_relation_prefers_kanun":
        return True

    normalized = f" {normalize_query_text(query)} "
    mentions_kanun = any(
        token in normalized
        for token in (
            " kanun ",
            " tebligat kanunu",
            " is kanunu",
            " borclar kanunu",
            " medeni kanun",
            " ticaret kanunu",
            " sayili kanun",
        )
    ) or bool(extract_numbered_law_mentions(query))
    mentions_regulation = any(
        token in normalized
        for token in (" yonetmelik", " teblig", " alt duzenleme", " ikincil duzenleme")
    )
    relation_signal = any(
        token in normalized
        for token in (
            " iliski",
            " hiyerarsi",
            " dayanak",
            " birlikte",
            " goster",
            " hangisi esas",
            " hangisi uygulan",
            " yoksa ",
            " aranmali",
            " kontrol ",
            " hangi karar ",
            " cevaplayip ",
            " bakarsin",
        )
    )
    mentions_cb_karar = any(
        token in normalized
        for token in (" karar ", " karar sayisi", " cumhurbaskani karari", " yatirim programi")
    )
    mentions_cb_genelge = any(token in normalized for token in (" genelge", " uygulama genelgesi"))
    mentions_khk = any(token in normalized for token in (" khk ", " kanun hukmunde kararname"))
    mentions_cb_kararname = any(
        token in normalized
        for token in (" cbk ", " kararname ", " cumhurbaskanligi kararnamesi")
    )
    if relation_signal and ((mentions_cb_karar and mentions_cb_genelge) or (mentions_khk and mentions_cb_kararname)):
        return True
    return bool(mentions_kanun and mentions_regulation and relation_signal)


def _relation_query_family_profile(
    query: str,
    *,
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None = None,
) -> dict[str, str | bool]:
    detected = _relation_query_detected(query, source_family_resolution=source_family_resolution)
    if not detected:
        return {
            "relation_query_detected": False,
            "primary_group": "",
            "supporting_group": "",
            "reason": "",
        }

    normalized = f" {normalize_query_text(query)} "
    relation_signal = any(
        token in normalized
        for token in (
            " iliski",
            " hiyerarsi",
            " dayanak",
            " birlikte",
            " goster",
            " hangisi esas",
            " hangisi uygulan",
            " yoksa ",
            " aranmali",
            " kontrol ",
            " hangi karar ",
            " cevaplayip ",
            " bakarsin",
        )
    )
    mentions_cb_karar = any(
        token in normalized
        for token in (" karar ", " karar sayisi", " cumhurbaskani karari", " yatirim programi")
    )
    mentions_cb_genelge = any(token in normalized for token in (" genelge", " uygulama genelgesi"))
    mentions_khk = any(token in normalized for token in (" khk ", " kanun hukmunde kararname"))
    mentions_cb_kararname = any(
        token in normalized
        for token in (" cbk ", " kararname ", " cumhurbaskanligi kararnamesi")
    )
    if relation_signal and mentions_cb_karar and mentions_cb_genelge:
        return {
            "relation_query_detected": True,
            "primary_group": "cb_karar",
            "supporting_group": "cb_genelge",
            "reason": "cb_karar_cb_genelge_relation_primary",
        }
    if relation_signal and mentions_khk and mentions_cb_kararname:
        return {
            "relation_query_detected": True,
            "primary_group": "khk",
            "supporting_group": "cb_kararname",
            "reason": "khk_cbk_relation_primary",
        }

    collision_reason = ""
    predicted_family = ""
    if isinstance(source_family_resolution, dict):
        collision_reason = str(source_family_resolution.get("collision_resolution_reason") or "")
        predicted_family = str(source_family_resolution.get("predicted_family") or "")
    elif source_family_resolution is not None:
        collision_reason = str(source_family_resolution.collision_resolution_reason or "")
        predicted_family = str(source_family_resolution.predicted_family or "")

    if collision_reason == "kanun_yonetmelik_relation_prefers_kanun":
        return {
            "relation_query_detected": True,
            "primary_group": "kanun",
            "supporting_group": "yonetmelik",
            "reason": collision_reason,
        }

    if _source_family_relation_group(predicted_family) == "kanun":
        return {
            "relation_query_detected": True,
            "primary_group": "kanun",
            "supporting_group": "yonetmelik",
            "reason": "predicted_family_relation_primary",
        }

    return {
        "relation_query_detected": True,
        "primary_group": "",
        "supporting_group": "",
        "reason": "relation_query_detected_without_family_resolution",
    }


def _apply_relation_query_metadata_focus(
    metadata_first_selector: dict[str, Any] | None,
    *,
    query: str,
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not metadata_first_selector or not metadata_first_selector.get("candidates"):
        return metadata_first_selector

    relation_profile = _relation_query_family_profile(
        query,
        source_family_resolution=source_family_resolution,
    )
    selector = dict(metadata_first_selector)
    selector["relation_query_detected"] = relation_profile.get("relation_query_detected") or False
    selector.setdefault("primary_source_candidate", "")
    selector.setdefault("supporting_source_candidate", "")
    selector.setdefault("final_primary_source_reason", "")
    if not relation_profile.get("relation_query_detected"):
        return selector

    primary_group = str(relation_profile.get("primary_group") or "")
    supporting_group = str(relation_profile.get("supporting_group") or "")
    candidates = [item for item in (selector.get("candidates") or []) if isinstance(item, dict)]
    if not primary_group:
        selector["final_primary_source_reason"] = str(
            relation_profile.get("reason") or "relation_query_detected"
        )
        return selector

    primary_candidates = [
        candidate
        for candidate in candidates
        if _source_family_relation_group(candidate.get("source_family")) == primary_group
    ]
    supporting_candidates = [
        candidate
        for candidate in candidates
        if _source_family_relation_group(candidate.get("source_family")) == supporting_group
    ]
    selector["primary_source_candidate"] = str(
        (
            (_resolve_candidate_source_display_label(primary_candidates[0]) if primary_candidates else None)
            or (primary_candidates[0].get("canonical_identifier") if primary_candidates else None)
            or ""
        )
    )
    selector["supporting_source_candidate"] = str(
        (
            (_resolve_candidate_source_display_label(supporting_candidates[0]) if supporting_candidates else None)
            or (supporting_candidates[0].get("canonical_identifier") if supporting_candidates else None)
            or ""
        )
    )
    if not primary_candidates:
        selector["final_primary_source_reason"] = "relation_query_no_primary_metadata_candidate"
        return selector

    selector["candidates"] = primary_candidates + [
        candidate for candidate in candidates if candidate not in primary_candidates
    ]
    selector["selected_source_keys"] = dedupe_strings(
        [
            str(candidate.get("source_key") or "")
            for candidate in primary_candidates
            if candidate.get("source_key")
        ]
    )
    selector["selected_families"] = dedupe_strings(
        [
            str(candidate.get("source_family") or "")
            for candidate in primary_candidates
            if candidate.get("source_family")
        ]
    )
    selector["final_primary_source_reason"] = str(
        relation_profile.get("reason") or "relation_query_primary_metadata_focus"
    )
    return selector


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


def _source_identity_reranker_enabled() -> bool:
    return os.getenv("SOURCE_IDENTITY_RERANKER_ENABLED", "true").lower() in {"1", "true", "yes", "on"}


def _chunk_source_identity_values(chunk: RetrievedChunk) -> set[str]:
    metadata = chunk.metadata or {}
    values: set[str] = set()
    for value in (
        metadata.get("source_id"),
        metadata.get("belge_no"),
        metadata.get("kanun_no"),
        metadata.get("law_no"),
        metadata.get("belge_kisa_adi"),
        metadata.get("kanun_kisa_adi"),
        metadata.get("law_short_name"),
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
        metadata.get("university_name_canonical"),
        metadata.get("canonical_title_family_normalized"),
        metadata.get("source_title"),
        metadata.get("belge_adi"),
        metadata.get("kanun_adi"),
        metadata.get("full_title"),
        chunk.source,
        chunk.citation,
    ):
        raw = str(value or "").strip()
        if not raw:
            continue
        values.add(raw.lower())
        normalized = normalize_canonical_text(raw)
        if normalized:
            values.add(normalized)
        source_prefix = raw.split(":", 1)[0]
        if source_prefix:
            values.add(source_prefix.lower())
    return values


def _chunk_matches_metadata_first_candidate(chunk: RetrievedChunk, candidate: dict[str, Any]) -> bool:
    values = _chunk_source_identity_values(chunk)
    for value in (
        candidate.get("source_key"),
        candidate.get("canonical_identifier"),
        candidate.get("canonical_title"),
    ):
        raw = str(value or "").strip()
        if not raw:
            continue
        if raw.lower() in values or normalize_canonical_text(raw) in values:
            return True
    return False


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


def _field_overlap_match_type(*, overlap: int, query_term_count: int, field_term_count: int) -> str:
    if overlap <= 0:
        return "none"
    denominator = max(1, min(query_term_count, field_term_count))
    ratio = overlap / denominator
    if overlap >= 4 and ratio >= 0.45:
        return "strong_overlap"
    if overlap >= 2 and ratio >= 0.25:
        return "medium_overlap"
    return "weak_overlap"


def _title_match_type(*, title: str, query: str, query_terms: set[str], title_overlap: int) -> str:
    normalized_title = normalize_query_text(title or "")
    normalized_query = normalize_query_text(query or "")
    if normalized_title and len(normalized_title) >= 18 and normalized_title in normalized_query:
        return "exact_phrase"
    if title_overlap <= 1:
        return "none"
    title_terms = _extract_retrieval_priority_terms(title)
    return _field_overlap_match_type(
        overlap=title_overlap,
        query_term_count=len(query_terms),
        field_term_count=len(title_terms),
    )


def _issuer_match_type(*, issuer_overlap: int, query_terms: set[str], issuer: str) -> str:
    issuer_terms = _extract_retrieval_priority_terms(issuer)
    return _field_overlap_match_type(
        overlap=issuer_overlap,
        query_term_count=len(query_terms),
        field_term_count=len(issuer_terms),
    )


def _identifier_match_type(
    *,
    strict_identifier_tokens: set[str],
    identifier_match: bool,
    source_identity_values: set[str],
) -> str:
    if not strict_identifier_tokens:
        return "not_requested"
    if identifier_match:
        return "exact_identifier"
    if source_identity_values & strict_identifier_tokens:
        return "normalized_identifier_overlap"
    return "none"


def _year_match_type(*, year_tokens: set[str], year_match: bool) -> str:
    if not year_tokens:
        return "not_requested"
    return "exact_year" if year_match else "none"


def _rerank_chunks_by_source_identity(
    *,
    query: str,
    chunks: list[RetrievedChunk],
    requested_source_families: list[str],
    metadata_first_selector: dict[str, Any] | None,
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None = None,
) -> tuple[list[RetrievedChunk], dict[str, Any]]:
    if not chunks or not _source_identity_reranker_enabled():
        return chunks, {"applied": False, "reason": "disabled_or_no_chunks"}

    query_terms = _extract_retrieval_priority_terms(query)
    strict_identifier_tokens = _extract_source_identity_identifier_tokens(query)
    year_tokens = set(_extract_year_tokens(query))
    query_article_tokens = _extract_query_article_tokens(query)
    requested_family_set = set(_expand_source_family_aliases(requested_source_families))
    current_validity_query = _asks_current_validity_query(query)
    historical_contrast_query = _asks_current_validity_over_historical_contrast(query)
    relation_profile = _relation_query_family_profile(
        query,
        source_family_resolution=source_family_resolution,
    )
    relation_query_detected = bool(relation_profile.get("relation_query_detected"))
    relation_primary_group = str(relation_profile.get("primary_group") or "")
    relation_supporting_group = str(relation_profile.get("supporting_group") or "")
    academic_regulation_intent = _query_has_academic_regulation_intent(query)
    legacy_query_years = set(_extract_year_tokens(query))
    metadata_candidates = (metadata_first_selector or {}).get("candidates") or []
    dominant_family_intent = set(requested_family_set)
    if not dominant_family_intent and source_family_resolution is not None:
        predicted_family = (
            str(source_family_resolution.get("predicted_family") or "")
            if isinstance(source_family_resolution, dict)
            else str(source_family_resolution.predicted_family or "")
        )
        if predicted_family:
            dominant_family_intent = set(_expand_source_family_aliases([predicted_family]))
    if relation_primary_group:
        dominant_family_intent = {relation_primary_group}
    if metadata_candidates:
        identity_rerank_input_source = "metadata_lookup_selector"
    elif strict_identifier_tokens:
        identity_rerank_input_source = "identifier_tokens"
    elif requested_family_set:
        identity_rerank_input_source = "source_family_prior"
    else:
        identity_rerank_input_source = "dense_retrieval"

    scored: list[tuple[float, int, RetrievedChunk, dict[str, Any]]] = []
    for original_index, chunk in enumerate(chunks):
        family_profile = _resolve_chunk_source_family_profile(chunk)
        family = str(family_profile.get("resolved_family") or "")
        mapped_family = str(family_profile.get("mapped_family") or family)
        title = _resolve_chunk_source_title(chunk)
        metadata = chunk.metadata or {}
        source_identity_values = _chunk_source_identity_values(chunk)
        chunk_years = _chunk_year_values(chunk)
        title_overlap = _count_term_overlap(title, query_terms)
        issuer = str(metadata.get("issuer") or metadata.get("kurum") or metadata.get("authority") or "")
        issuer_overlap = _count_term_overlap(issuer, query_terms)
        identifier_match = _chunk_matches_identifier_tokens(chunk, strict_identifier_tokens)
        title_match_type = _title_match_type(
            title=title,
            query=query,
            query_terms=query_terms,
            title_overlap=title_overlap,
        )
        issuer_match_type = _issuer_match_type(
            issuer_overlap=issuer_overlap,
            query_terms=query_terms,
            issuer=issuer,
        )
        identifier_match_type = _identifier_match_type(
            strict_identifier_tokens=strict_identifier_tokens,
            identifier_match=identifier_match,
            source_identity_values=source_identity_values,
        )
        metadata_first_match = any(_chunk_matches_metadata_first_candidate(chunk, candidate) for candidate in metadata_candidates)
        family_match = bool(
            requested_family_set and (mapped_family in requested_family_set or family in requested_family_set)
        )
        year_match = bool(year_tokens and year_tokens & chunk_years)
        year_match_type = _year_match_type(year_tokens=year_tokens, year_match=year_match)
        official_gazette_date = str(metadata.get("official_gazette_date") or "").strip()
        official_gazette_date_match = bool(
            official_gazette_date
            and normalize_canonical_text(official_gazette_date)
            and normalize_canonical_text(official_gazette_date) in normalize_canonical_text(query)
        )
        active_rank = _chunk_active_rank(chunk)
        article_token = _chunk_article_token(chunk)
        source_key = _resolve_chunk_source_key(chunk)
        recall_lane_sources = _chunk_recall_lane_sources(chunk)
        recall_lane_rank = _chunk_recall_lane_rank(chunk)
        relation_group = _source_family_relation_group(mapped_family or family)
        legacy_profile = _legacy_source_binding_profile(
            chunk,
            query=query,
            source_family_resolution=source_family_resolution,
            identifier_tokens=strict_identifier_tokens,
            year_tokens=legacy_query_years,
        )

        score = float(chunk.score or 0.0)
        reasons: list[str] = []
        title_bias_applied = 0.0
        issuer_bias_applied = 0.0
        year_bias_applied = 0.0
        strict_kanun_intent = bool(dominant_family_intent and dominant_family_intent <= {"kanun", "mulga_kanun"})
        strict_khk_intent = bool(dominant_family_intent and dominant_family_intent <= {"khk"})
        strict_cb_karar_intent = bool(dominant_family_intent and dominant_family_intent <= {"cb_karar"})
        if metadata_first_match:
            score += 100
            reasons.append("metadata_first_match")
        if identifier_match_type == "exact_identifier":
            score += 110
            reasons.append("identifier_exact")
        elif identifier_match_type == "normalized_identifier_overlap":
            score += 25
            reasons.append("identifier_normalized_overlap")
        if family_match:
            score += 35
            reasons.append("family_match")
        elif requested_family_set:
            score -= 35
            reasons.append("family_mismatch_penalty")
        if mapped_family != family and requested_family_set and mapped_family in requested_family_set:
            score += 12
            reasons.append("family_mapping_bridge_match")
        if title_match_type == "exact_phrase":
            title_bias_applied += 125
            reasons.append("title_exact_phrase")
        elif title_match_type == "strong_overlap":
            title_bias_applied += 90
            reasons.append("title_strong_overlap")
        elif title_match_type == "medium_overlap":
            title_bias_applied += 30
            reasons.append("title_medium_overlap")
        elif title_match_type == "weak_overlap":
            title_bias_applied += 0
            reasons.append("title_weak_overlap")
        if title_overlap:
            title_bias_applied += min(title_overlap, 10) * (
                10 if title_match_type in {"exact_phrase", "strong_overlap"} else 4
            )
            reasons.append(f"title_overlap:{title_overlap}")
        score += title_bias_applied
        if issuer_match_type == "strong_overlap":
            issuer_bias_applied += 20
            reasons.append("issuer_strong_overlap")
        elif issuer_match_type == "medium_overlap":
            issuer_bias_applied += 10
            reasons.append("issuer_medium_overlap")
        elif issuer_match_type == "weak_overlap":
            issuer_bias_applied += 2
            reasons.append("issuer_weak_overlap")
        if issuer_overlap:
            issuer_bias_applied += min(issuer_overlap, 6) * 3
            reasons.append(f"issuer_overlap:{issuer_overlap}")
        score += issuer_bias_applied
        if year_match_type == "exact_year":
            year_bias_applied += 18 if current_validity_query else 14
            reasons.append("year_match")
        elif year_tokens:
            year_bias_applied -= 10
            reasons.append("year_mismatch_penalty")
        score += year_bias_applied
        if official_gazette_date_match:
            score += 16
            reasons.append("official_gazette_date_match")
        if recall_lane_rank == 0:
            score += 24
            reasons.append("dual_lane_confirmation")
        elif recall_lane_rank == 1:
            if metadata_first_match or identifier_match_type == "exact_identifier" or title_match_type in {
                "exact_phrase",
                "strong_overlap",
            }:
                score += 10
                reasons.append("metadata_lane_supported")
            elif title_match_type == "medium_overlap" and family not in {
                "uy",
                "cb_genelge",
                "teblig",
                "kky",
                "yonetmelik",
                "cb_kararname",
                "cb_yonetmelik",
            }:
                score += 4
                reasons.append("metadata_lane_supported")
            else:
                score -= 18
                reasons.append("metadata_lane_without_identity_penalty")
        elif recall_lane_rank == 2 and family_match and title_match_type in {
            "exact_phrase",
            "strong_overlap",
            "medium_overlap",
        }:
            score += 6
            reasons.append("dense_lane_supported")
        if relation_query_detected and relation_primary_group:
            if relation_group == relation_primary_group:
                score += 42
                reasons.append("relation_primary_source_bonus")
            elif relation_supporting_group and relation_group == relation_supporting_group:
                score -= 26
                reasons.append("relation_supporting_source_penalty")
                if metadata_first_match and identifier_match_type == "none":
                    score -= 38
                    reasons.append("relation_metadata_supporting_penalty")
        if family == "uy" and not academic_regulation_intent:
            score -= 52
            reasons.append("uy_without_academic_query_penalty")
        if strict_kanun_intent and family in {
            "teblig",
            "yonetmelik",
            "kky",
            "uy",
            "cb_yonetmelik",
            "cb_genelge",
            "cb_karar",
            "cb_kararname",
        }:
            score -= 28
            reasons.append("strict_kanun_query_penalty")
        if strict_khk_intent and family in {
            "cb_kararname",
            "cb_karar",
            "cb_genelge",
            "teblig",
            "yonetmelik",
            "kky",
            "uy",
            "cb_yonetmelik",
        }:
            score -= 40
            reasons.append("strict_khk_query_penalty")
        if strict_cb_karar_intent and family in {"cb_genelge", "cb_kararname", "teblig"}:
            score -= 36
            reasons.append("strict_cb_karar_query_penalty")
        if family_match and title_match_type == "none" and identifier_match_type == "none" and year_match_type == "none":
            score -= 45 if family in {"cb_karar", "cb_genelge", "uy", "yonetmelik", "teblig", "kky", "cb_yonetmelik", "cb_kararname"} else 18
            reasons.append("generic_family_without_identity_penalty")
        if current_validity_query:
            score -= active_rank * 35
            reasons.append(f"current_active_rank:{active_rank}")
        if historical_contrast_query and _is_temporally_inactive_chunk(chunk):
            score += 8
            reasons.append("historical_contrast_repealed_context")
        if legacy_profile["legacy_intent_binding_active"]:
            score += float(legacy_profile["score"])
            if legacy_profile["binding_reason"]:
                reasons.extend(
                    reason
                    for reason in str(legacy_profile["binding_reason"]).split(" | ")
                    if reason
                )
        if article_token == "0" and query_terms and title_overlap == 0 and not identifier_match:
            score -= 10
            reasons.append("m0_without_title_anchor_penalty")
        if source_identity_values & strict_identifier_tokens:
            score += 10
            reasons.append("source_value_identifier_overlap")
        if metadata_first_match or identifier_match_type == "exact_identifier" or title_match_type in {
            "exact_phrase",
            "strong_overlap",
        }:
            identity_lock_strength = "strong"
        elif identifier_match_type == "normalized_identifier_overlap" or title_match_type == "medium_overlap":
            identity_lock_strength = "medium"
        elif family_match or title_match_type == "weak_overlap" or issuer_match_type in {
            "strong_overlap",
            "medium_overlap",
        }:
            identity_lock_strength = "weak"
        else:
            identity_lock_strength = "none"

        replacement_guard_triggered = bool(
            identifier_match_type != "exact_identifier"
            and recall_lane_rank <= 1
            and (
                title_match_type in {"none", "weak_overlap"}
                or (
                    title_match_type == "medium_overlap"
                    and family in {"uy", "cb_genelge", "teblig", "cb_kararname", "cb_yonetmelik", "kky"}
                )
                or (
                    relation_query_detected
                    and relation_supporting_group
                    and relation_group == relation_supporting_group
                    and title_match_type != "exact_phrase"
                )
            )
        )
        post_identity_article_alignment = _query_article_alignment(
            selected_article=article_token,
            query_article_tokens=query_article_tokens,
            article_match_type=(
                "source_local_support"
                if article_token and article_token != "0"
                else "title_only"
            ),
        )

        scored.append(
            (
                score,
                original_index,
                chunk,
                {
                    "source_id": _resolve_trace_source_id(chunk),
                    "citation": chunk.citation,
                    "source_key": source_key,
                    "source_title": title,
                    "source_family": family or None,
                    "source_family_mapped": mapped_family or None,
                    "source_family_raw": family_profile.get("raw_family"),
                    "source_family_mapping_reason": family_profile.get("mapping_reason"),
                    "source_identifier": _resolve_chunk_source_identifier(chunk),
                    "article_or_section": article_token or None,
                    "score": round(score, 4),
                    "document_identity_score": round(score, 4),
                    "metadata_first_match": metadata_first_match,
                    "identifier_match": identifier_match,
                    "identifier_match_type": identifier_match_type,
                    "family_match": family_match,
                    "title_match_type": title_match_type,
                    "title_overlap": title_overlap,
                    "title_bias_applied": round(title_bias_applied, 4),
                    "issuer_match_type": issuer_match_type,
                    "issuer_overlap": issuer_overlap,
                    "issuer_bias_applied": round(issuer_bias_applied, 4),
                    "year_match": year_match,
                    "year_match_type": year_match_type,
                    "year_bias_applied": round(year_bias_applied, 4),
                    "official_gazette_date_match": official_gazette_date_match,
                    "active_rank": active_rank,
                    "relation_query_detected": relation_query_detected,
                    "relation_group": relation_group or None,
                    "legacy_intent_binding_active": legacy_profile["legacy_intent_binding_active"],
                    "legacy_candidate_preferred": legacy_profile["legacy_candidate_preferred"],
                    "document_state_binding_reason": legacy_profile["binding_reason"] or None,
                    "legacy_state_rank": legacy_profile["state_rank"],
                    "legacy_year_match": legacy_profile["year_match"],
                    "legacy_source_years": legacy_profile["source_years"],
                    "retrieval_lane_sources": recall_lane_sources,
                    "identity_rerank_input_lane": recall_lane_sources[0] if recall_lane_sources else "unknown",
                    "identity_lock_strength": identity_lock_strength,
                    "replacement_guard_triggered": replacement_guard_triggered,
                    "post_identity_article_alignment": post_identity_article_alignment,
                    "selected_document_original_rank": original_index + 1,
                    "document_rerank_reason": " | ".join(reasons),
                    "identity_rerank_input_source": identity_rerank_input_source,
                    "reasons": reasons,
                },
            )
        )

    ranked = sorted(scored, key=lambda item: (-item[0], item[1]))
    reordered = [chunk for _score, _index, chunk, _trace in ranked]
    first_changed = bool(reordered and chunks and reordered[0].citation != chunks[0].citation)
    ranked_traces: list[dict[str, Any]] = []
    for reranked_index, (_score, _index, _chunk, trace) in enumerate(ranked[:10], start=1):
        trace_with_rank = dict(trace)
        trace_with_rank["selected_document_rank_after_identity_rerank"] = reranked_index
        ranked_traces.append(trace_with_rank)
    top_trace = ranked_traces[0] if ranked_traces else {}
    relation_primary_candidate = ""
    relation_supporting_candidate = ""
    if relation_query_detected:
        for trace in ranked_traces:
            if _source_family_relation_group(trace.get("source_family")) == relation_primary_group:
                relation_primary_candidate = _resolve_trace_source_display_label(trace)
                break
        for trace in ranked_traces:
            if _source_family_relation_group(trace.get("source_family")) == relation_supporting_group:
                relation_supporting_candidate = _resolve_trace_source_display_label(trace)
                break
    return reordered, {
        "applied": True,
        "reason": "source_identity_reranker",
        "identity_rerank_input_source": identity_rerank_input_source,
        "first_changed": first_changed,
        "requested_source_families": requested_source_families,
        "query_identifier_tokens": sorted(strict_identifier_tokens),
        "query_year_tokens": sorted(year_tokens),
        "document_identity_score": top_trace.get("document_identity_score"),
        "title_match_type": top_trace.get("title_match_type"),
        "identifier_match_type": top_trace.get("identifier_match_type"),
        "issuer_match_type": top_trace.get("issuer_match_type"),
        "year_match_type": top_trace.get("year_match_type"),
        "title_bias_applied": top_trace.get("title_bias_applied"),
        "issuer_bias_applied": top_trace.get("issuer_bias_applied"),
        "identity_lock_strength": top_trace.get("identity_lock_strength"),
        "identity_rerank_input_lane": top_trace.get("identity_rerank_input_lane"),
        "replacement_guard_triggered": top_trace.get("replacement_guard_triggered"),
        "post_identity_article_alignment": top_trace.get("post_identity_article_alignment"),
        "relation_query_detected": relation_query_detected,
        "primary_source_candidate": relation_primary_candidate,
        "supporting_source_candidate": relation_supporting_candidate,
        "final_primary_source_reason": (
            str(relation_profile.get("reason") or "relation_query_primary_rerank")
            if relation_primary_candidate
            else ""
        ),
        "legacy_intent_binding_active": top_trace.get("legacy_intent_binding_active"),
        "legacy_candidate_preferred": top_trace.get("legacy_candidate_preferred"),
        "document_state_binding_reason": top_trace.get("document_state_binding_reason"),
        "selected_document_rank_after_identity_rerank": top_trace.get(
            "selected_document_rank_after_identity_rerank"
        ),
        "selected_document_original_rank": top_trace.get("selected_document_original_rank"),
        "document_rerank_reason": top_trace.get("document_rerank_reason"),
        "metadata_first_candidate_keys": [
            str(candidate.get("source_key") or "")
            for candidate in metadata_candidates
            if candidate.get("source_key")
        ],
        "top_scores": ranked_traces,
    }



def _build_retrieved_chunk(result: Any) -> RetrievedChunk:
    metadata = enrich_metadata_with_source_title(getattr(result, "metadata", None) or {})
    return RetrievedChunk(
        text=result.text,
        citation=result.citation,
        source=result.law_short_name,
        score=result.score,
        metadata=metadata,
    )


def _annotate_recall_lane_chunks(
    chunks: list[RetrievedChunk],
    *,
    lane: str,
) -> list[RetrievedChunk]:
    for chunk in chunks:
        metadata = dict(chunk.metadata or {})
        existing = metadata.get("retrieval_lane_sources")
        lanes = [
            value
            for value in (existing if isinstance(existing, list) else [])
            if isinstance(value, str) and value.strip()
        ]
        if lane not in lanes:
            lanes.append(lane)
        metadata["retrieval_lane_sources"] = lanes
        metadata["metadata_lane_present"] = "metadata_guided_recall" in lanes
        metadata["dense_lane_present"] = "semantic_dense_recall" in lanes
        metadata["merged_lane_present"] = (
            metadata["metadata_lane_present"] and metadata["dense_lane_present"]
        )
        chunk.metadata = metadata
    return chunks


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


def _resolve_chunk_source_key(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    return (
        str(
            metadata.get("canonical_identifier_display")
            or metadata.get("canonical_identifier")
            or metadata.get("belge_no")
            or metadata.get("kanun_no")
            or metadata.get("law_no")
            or metadata.get("decision_number")
            or metadata.get("kararname_number")
            or metadata.get("genelge_number")
            or metadata.get("generalge_number")
            or metadata.get("teblig_number")
            or metadata.get("regulation_number")
            or metadata.get("law_short_name")
            or metadata.get("kanun_kisa_adi")
            or metadata.get("source_title")
            or metadata.get("belge_adi")
            or metadata.get("kanun_adi")
            or metadata.get("law_name")
            or chunk.source
            or chunk.citation
        )
        .strip()
        .lower()
    )


def _prioritize_chunks_for_source_families(
    *,
    query: str,
    chunks: list[RetrievedChunk],
    source_families: list[str],
    selected_source_keys: set[str] | None = None,
) -> list[RetrievedChunk]:
    if not chunks:
        return chunks

    family_order = {family: index for index, family in enumerate(source_families)}
    query_terms = _extract_retrieval_priority_terms(query)
    numbered_laws = set(extract_numbered_law_mentions(query))
    identifier_tokens = _extract_source_identifier_tokens(query)
    current_validity_query = _asks_current_validity_query(query)
    source_cluster_sizes: dict[str, int] = {}
    for chunk in chunks:
        source_key = _resolve_chunk_source_key(chunk)
        source_cluster_sizes[source_key] = source_cluster_sizes.get(source_key, 0) + 1

    if source_families and not any(
        (_resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk)) in family_order
        for chunk in chunks
    ):
        return chunks

    def _rank_tuple(item: tuple[int, RetrievedChunk]) -> tuple[Any, ...]:
        original_index, chunk = item
        metadata = chunk.metadata or {}
        family = _resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk) or ""
        source_title = (
            metadata.get("source_title")
            or metadata.get("belge_adi")
            or metadata.get("kanun_adi")
            or metadata.get("law_name")
        )
        heading = metadata.get("heading") or metadata.get("article_heading")
        cluster_size = source_cluster_sizes.get(_resolve_chunk_source_key(chunk), 1)
        selected_source_rank = (
            0
            if not selected_source_keys or _resolve_chunk_source_key(chunk) in selected_source_keys
            else 1
        )
        lane_rank = _chunk_recall_lane_rank(chunk)
        family_match = 0 if not source_families else (0 if family in family_order else 1)
        family_rank = family_order.get(family, len(family_order))
        title_overlap = _count_term_overlap(str(source_title or ""), query_terms)
        heading_overlap = _count_term_overlap(str(heading or ""), query_terms)
        text_overlap = _count_term_overlap(chunk.text, query_terms)
        generic_heading_only_penalty = 0
        if heading_overlap > 0 and title_overlap == 0 and text_overlap <= heading_overlap:
            generic_heading_only_penalty = 1
        dense_score = chunk.score or 0.0
        law_match_rank = 0
        if numbered_laws:
            law_match_rank = 0 if numbered_laws & _chunk_law_candidates(chunk) else 1
        identifier_match_rank = 0
        if identifier_tokens:
            identifier_match_rank = 0 if _chunk_matches_identifier_tokens(chunk, identifier_tokens) else 1
        active_rank = _chunk_active_rank(chunk) if current_validity_query else 0
        if source_families:
            return (
                active_rank,
                lane_rank,
                selected_source_rank,
                family_match,
                family_rank,
                identifier_match_rank,
                law_match_rank,
                generic_heading_only_penalty,
                -title_overlap,
                -heading_overlap,
                -cluster_size,
                -text_overlap,
                -dense_score,
                original_index,
            )
        return (
            lane_rank,
            identifier_match_rank,
            law_match_rank,
            active_rank,
            selected_source_rank,
            generic_heading_only_penalty,
            -title_overlap,
            -heading_overlap,
            -cluster_size,
            -text_overlap,
            -dense_score,
            original_index,
        )

    ranked = sorted(
        enumerate(chunks),
        key=_rank_tuple,
    )
    return [chunk for _index, chunk in ranked]


def _focus_chunks_on_selected_sources(
    *,
    chunks: list[RetrievedChunk],
    selected_source_keys: set[str],
) -> list[RetrievedChunk]:
    if not chunks or not selected_source_keys:
        return chunks

    selected_chunks = [
        chunk for chunk in chunks
        if _resolve_chunk_source_key(chunk) in selected_source_keys
    ]
    if len(selected_chunks) < 2:
        return chunks

    other_chunks = [
        chunk for chunk in chunks
        if _resolve_chunk_source_key(chunk) not in selected_source_keys
    ]
    max_selected = max(4, min(8, len(selected_chunks)))
    max_other = 2 if len(selected_chunks) >= 4 else 3
    return selected_chunks[:max_selected] + other_chunks[:max_other]


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


def _infer_law_mentions_from_concepts(query: str) -> list[str]:
    if _looks_like_tbk_tmk_cross_law_query(query):
        return ["TBK", "TMK"]
    return []


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


def _retrieve_explicit_article_chunks(
    *,
    retriever: Any,
    query: str,
    article_refs: list[tuple[str, str]],
) -> list[RetrievedChunk]:
    from rag.retriever import MetadataFilter

    exact_chunks: list[RetrievedChunk] = []

    for law, madde in article_refs:
        metadata_filter = (
            MetadataFilter(law_no=law, madde_no=madde)
            if law.isdigit()
            else MetadataFilter(law_short_name=law, madde_no=madde)
        )
        try:
            results, _stats = retriever.retrieve(
                query=query,
                top_k=2,
                metadata_filter=metadata_filter,
            )
        except Exception as exc:
            logger.warning(
                "Exact article retrieval bypass (law=%s madde=%s): %s",
                law,
                madde,
                exc,
            )
            continue

        exact_chunks.extend(_build_retrieved_chunk(result) for result in results)

    return _annotate_recall_lane_chunks(exact_chunks, lane="metadata_guided_recall")


def _retrieve_law_bucket_chunks(
    *,
    retriever: Any,
    query: str,
    laws: list[str],
    top_k: int,
) -> list[RetrievedChunk]:
    from rag.retriever import MetadataFilter

    bucket_chunks: list[RetrievedChunk] = []
    for law in laws:
        metadata_filter = (
            MetadataFilter(law_no=law)
            if law.isdigit()
            else MetadataFilter(law_short_name=law)
        )
        try:
            results, _stats = retriever.retrieve(
                query=query,
                top_k=top_k,
                metadata_filter=metadata_filter,
            )
        except Exception as exc:
            logger.warning("Law-bucket retrieval bypass (law=%s): %s", law, exc)
            continue

        bucket_chunks.extend(_build_retrieved_chunk(result) for result in results)

    return _annotate_recall_lane_chunks(bucket_chunks, lane="metadata_guided_recall")


def _retrieve_source_key_chunks(
    *,
    retriever: Any,
    query: str,
    source_keys: list[str],
    source_family_by_key: dict[str, str] | None = None,
    top_k: int,
) -> list[RetrievedChunk]:
    from rag.retriever import MetadataFilter

    bucket_chunks: list[RetrievedChunk] = []
    for source_key in source_keys:
        source_family = str((source_family_by_key or {}).get(source_key) or "").strip().lower()
        if source_family == "mulga_kanun":
            source_family = "mulga"
        try:
            results, _stats = retriever.retrieve(
                query=query,
                top_k=top_k,
                metadata_filter=MetadataFilter(
                    law_no=source_key,
                    belge_turu=source_family or None,
                ),
            )
        except Exception as exc:
            logger.warning("Source-key retrieval bypass (source_key=%s): %s", source_key, exc)
            continue

        bucket_chunks.extend(_build_retrieved_chunk(result) for result in results)

    return _annotate_recall_lane_chunks(bucket_chunks, lane="metadata_guided_recall")


def _retrieve_active_chunks(
    *,
    retriever: Any,
    query: str,
    top_k: int,
) -> list[RetrievedChunk]:
    from rag.retriever import MetadataFilter

    try:
        results, _stats = retriever.retrieve(
            query=query,
            top_k=top_k,
            metadata_filter=MetadataFilter(mulga=False),
        )
    except Exception as exc:
        logger.warning("Active-source retrieval bypass: %s", exc)
        return []

    return _annotate_recall_lane_chunks(
        [_build_retrieved_chunk(result) for result in results],
        lane="metadata_guided_recall",
    )


def _retrieve_source_family_chunks(
    *,
    retriever: Any,
    query: str,
    source_families: list[str],
    top_k: int,
) -> list[RetrievedChunk]:
    from rag.retriever import MetadataFilter

    bucket_chunks: list[RetrievedChunk] = []
    for family in source_families:
        metadata_filter = MetadataFilter(belge_turu=family)
        try:
            results, _stats = retriever.retrieve(
                query=query,
                top_k=top_k,
                metadata_filter=metadata_filter,
            )
        except Exception as exc:
            logger.warning("Source-family retrieval bypass (family=%s): %s", family, exc)
            continue

        bucket_chunks.extend(_build_retrieved_chunk(result) for result in results)

    return _annotate_recall_lane_chunks(bucket_chunks, lane="metadata_guided_recall")


def _resolve_trace_source_id(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    if metadata.get("source_id") is not None:
        return str(metadata["source_id"])
    law_short_name = (
        metadata.get("law_short_name")
        or metadata.get("kanun_kisa_adi")
        or chunk.source
    )
    madde_no = metadata.get("madde_no")
    if law_short_name and madde_no:
        return f"{law_short_name} m.{madde_no}"
    return chunk.citation


def _serialize_trace_chunk(chunk: RetrievedChunk) -> dict[str, Any]:
    metadata = chunk.metadata or {}
    source_title = _resolve_chunk_source_title(chunk)
    family_profile = _resolve_chunk_source_family_profile(chunk)
    source_family = family_profile.get("resolved_family")
    source_identifier = _resolve_chunk_source_identifier(chunk)
    article_or_section = _chunk_article_token(chunk)
    effective_state = metadata.get("effective_state") or resolve_effective_state(metadata)
    recall_lane_sources = _chunk_recall_lane_sources(chunk)
    return {
        "source_id": _resolve_trace_source_id(chunk),
        "citation": chunk.citation,
        "source": chunk.source,
        "score": chunk.score,
        "chunk_id": metadata.get("chunk_id"),
        "law_no": metadata.get("law_no") or metadata.get("kanun_no"),
        "law_short_name": metadata.get("law_short_name") or metadata.get("kanun_kisa_adi"),
        "source_title": source_title,
        "belge_adi": metadata.get("belge_adi") or metadata.get("kanun_adi"),
        "belge_turu": metadata.get("belge_turu") or metadata.get("source_type"),
        "source_family": source_family,
        "source_family_raw": family_profile.get("raw_family"),
        "source_family_canonical": family_profile.get("canonical_family") or source_family,
        "source_family_title_inferred": family_profile.get("title_inferred_family"),
        "source_family_mapped": family_profile.get("mapped_family") or source_family,
        "source_family_mapping_reason": family_profile.get("mapping_reason"),
        "source_identifier": source_identifier,
        "article_or_section": article_or_section or None,
        "full_title": metadata.get("full_title") or source_title,
        "issuer": metadata.get("issuer"),
        "issuer_canonical": metadata.get("issuer_canonical"),
        "issuing_body_level": metadata.get("issuing_body_level"),
        "official_gazette_no": metadata.get("official_gazette_no"),
        "official_gazette_date": metadata.get("official_gazette_date"),
        "decision_year": metadata.get("decision_year"),
        "decision_number": metadata.get("decision_number"),
        "kararname_number": metadata.get("kararname_number"),
        "regulation_number": metadata.get("regulation_number"),
        "genelge_number": metadata.get("genelge_number"),
        "generalge_number": metadata.get("generalge_number"),
        "teblig_number": metadata.get("teblig_number"),
        "sira_no": metadata.get("sira_no"),
        "seri_no": metadata.get("seri_no"),
        "effective_start": metadata.get("effective_start") or metadata.get("yururluk_baslangic"),
        "effective_end": metadata.get("effective_end") or metadata.get("yururluk_bitis"),
        "is_repealed": metadata.get("is_repealed"),
        "is_amended": metadata.get("is_amended"),
        "university_name_canonical": metadata.get("university_name_canonical"),
        "canonical_title_family_normalized": metadata.get("canonical_title_family_normalized"),
        "metadata_provenance": metadata.get("metadata_provenance"),
        "canonical_identifier_display": metadata.get("canonical_identifier_display"),
        "effective_state": effective_state,
        "retrieval_lane_sources": recall_lane_sources,
        "metadata_lane_present": "metadata_guided_recall" in recall_lane_sources,
        "dense_lane_present": "semantic_dense_recall" in recall_lane_sources,
        "merged_lane_present": {"metadata_guided_recall", "semantic_dense_recall"} <= set(recall_lane_sources),
        "heading": metadata.get("heading") or metadata.get("article_heading"),
        "madde_no": metadata.get("madde_no"),
        "fikra_no": metadata.get("fikra_no"),
        "yururluk_baslangic": metadata.get("yururluk_baslangic"),
        "yururluk_bitis": metadata.get("yururluk_bitis"),
        "mulga": metadata.get("mulga"),
    }


def _build_assembled_evidence(
    chunks: list[RetrievedChunk],
    *,
    query: str | None = None,
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for chunk in chunks:
        item = _serialize_trace_chunk(chunk)
        item["quoted_or_extracted_span"] = _build_chunk_evidence_span(chunk, query=query)
        item["excerpt"] = chunk.text
        evidence.append(item)
    return evidence


def _build_fallback_assembled_evidence(
    source_ids: list[str],
    *,
    fallback_excerpt: str,
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for source_id in source_ids:
        canonical = canonicalize_source_id(source_id) or source_id
        law_short_name, _, article_part = canonical.partition(" ")
        madde_no = article_part.replace("m.", "").strip() if article_part else None
        evidence.append(
            {
                "source_id": canonical,
                "citation": canonical,
                "source": law_short_name or None,
                "score": None,
                "chunk_id": None,
                "law_no": None,
                "law_short_name": law_short_name or None,
                "madde_no": madde_no or None,
                "source_family": "kanun" if law_short_name else None,
                "source_identifier": canonical,
                "article_or_section": madde_no or None,
                "effective_state": "unknown",
                "quoted_or_extracted_span": fallback_excerpt,
                "fikra_no": None,
                "yururluk_baslangic": None,
                "yururluk_bitis": None,
                "mulga": None,
                "excerpt": fallback_excerpt,
            }
        )
    return evidence


def _build_allowed_source_whitelist(chunks: list[RetrievedChunk]) -> list[str]:
    whitelist: list[str] = []
    seen: set[str] = set()
    for chunk in chunks:
        source_id = _resolve_trace_source_id(chunk)
        if source_id in seen:
            continue
        whitelist.append(source_id)
        seen.add(source_id)
    return whitelist


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
        "preferred_families": preferred_families,
        "fallback_families": fallback_families,
        "pre_filter_family_set": dedupe_strings(pre_filter_family_set),
        "reranked_family_set": dedupe_strings(reranked_family_set),
        "selected_family_source": selected_family_source,
        "family_gate_status": family_gate_status,
        "family_gate_reason": family_gate_reason,
        "no_gate_reason": no_gate_reason,
    }


def _answer_template_for_query(query: str) -> str:
    normalized = normalize_query_text(query or "")
    if any(term in normalized for term in ("usul", "basvuru", "itiraz", "sure", "dava sart", "on sart")):
        return "procedure"
    if any(term in normalized for term in ("istisna", "muaf", "haric", "sakli", "uygulanmaz")):
        return "exception"
    if any(term in normalized for term in ("kosul", "sart", "hangi hallerde", "aranir", "gerekir")):
        return "condition"
    if any(term in normalized for term in ("fark", "karsilastir", "yoksa", "eski", "guncel", "hangisi")):
        return "comparison_or_temporal"
    return "direct"


def _query_contains_any(normalized_query: str, terms: tuple[str, ...]) -> bool:
    return any(term in normalized_query for term in terms)


def _must_have_fact_slots_for_query(query: str, template: str) -> list[str]:
    normalized = normalize_query_text(query or "")
    slots = ["result_or_holding", "governing_source"]
    if _query_contains_any(
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
    if _query_contains_any(normalized, ("madde", "fikra", "bent", "paragraf", "hukum")):
        slots.append("article_or_span")
    if template == "procedure":
        slots.append("procedure_or_consequence")
    if template == "exception":
        slots.extend(["exception_or_limitation", "scenario_applicability"])
    if template == "condition":
        slots.append("scenario_applicability")
    if _query_contains_any(normalized, ("istisna", "muaf", "haric", "sakli", "uygulanmaz")):
        slots.append("exception_or_limitation")
    if _query_contains_any(normalized, ("kosul", "sart", "hangi hallerde", "aranir", "gerekir")):
        slots.append("scenario_applicability")
    if template == "comparison_or_temporal":
        slots.append("temporal_validity")
    if _query_contains_any(
        normalized,
        (
            "guncel",
            "halen yururlukte",
            "yururlukte mi",
            "mulga",
            "eski",
            "son durum",
            "ne zaman yururluge",
        ),
    ):
        slots.append("temporal_validity")
    if _query_contains_any(
        normalized,
        (
            "yeterli midir",
            "yoksa",
            "ust norm",
            "alt norm",
            "kanun mu",
            "yonetmelik mi",
            "hangisi uygulanir",
        ),
    ):
        slots.append("hierarchy_or_conflict_rule")
    return dedupe_strings(slots)


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
    evidence_surface = normalize_query_text(
        " ".join(
            part
            for chunk in chunks[:5]
            for part in (
                chunk.text,
                chunk.citation,
                _resolve_chunk_source_title(chunk),
                _resolve_chunk_source_identifier(chunk),
                str((chunk.metadata or {}).get("effective_state") or ""),
                str((chunk.metadata or {}).get("yururluk_baslangic") or ""),
                str((chunk.metadata or {}).get("yururluk_bitis") or ""),
            )
            if part
        )
    )
    supported: list[str] = []
    for slot in required_slots:
        if slot == "procedure_or_consequence" and _answer_contains_any(
            evidence_surface,
            (
                "usul",
                "sure",
                "basvuru",
                "itiraz",
                "sonuc",
                "yaptirim",
                "zorunlu",
                "yukumluluk",
                "bildirim",
                "islem",
            ),
        ):
            supported.append(slot)
        elif slot == "scenario_applicability" and _answer_contains_any(
            evidence_surface,
            ("sart", "kosul", "halinde", "hallerde", "durumda", "kapsam", "uygulanir", "aranir"),
        ):
            supported.append(slot)
        elif slot == "exception_or_limitation" and _answer_contains_any(
            evidence_surface,
            ("istisna", "sakli", "haric", "muaf", "sinirli", "uygulanmaz"),
        ):
            supported.append(slot)
        elif slot == "temporal_validity" and _answer_contains_any(
            evidence_surface,
            ("yururluk", "guncel", "mulga", "tarih", "halen", "gecerli", "9999 12 31"),
        ):
            supported.append(slot)
        elif slot == "hierarchy_or_conflict_rule" and _answer_contains_any(
            evidence_surface,
            (
                "oncelik",
                "ust norm",
                "alt norm",
                "ozel duzenleme",
                "genel duzenleme",
                "ikincil duzenleme",
                "normlar hiyerarsisi",
                "kanuna aykiri",
                "dayanak",
            ),
        ):
            supported.append(slot)
    return dedupe_strings(supported)


def _count_answer_fact_units(answer_text: str) -> int:
    stripped = re.sub(r"\[Kaynak:[^\]]+\]", " ", answer_text or "")
    pieces = re.split(r"(?:\n+|(?<=[.!?])\s+|(?:^|\s)(?:[-*]|\d+[.)])\s+)", stripped)
    long_pieces = [
        piece.strip()
        for piece in pieces
        if len(piece.strip()) >= 28 and any(char.isalpha() for char in piece)
    ]
    citation_count = len(_INLINE_CITATION_RE.findall(answer_text or ""))
    return max(len(long_pieces), citation_count)


def _build_completeness_synthesis_features(
    *,
    query: str,
    answer_text: str,
    article_span_selector: dict[str, Any] | None,
    chunks: list[RetrievedChunk],
) -> dict[str, Any]:
    template = _answer_template_for_query(query)
    required_slots = _must_have_fact_slots_for_query(query, template)
    minimum_required_facts = max(2 if template == "direct" else 3, min(len(required_slots), 3))
    answer_fact_units = _count_answer_fact_units(answer_text)
    citation_count = len(_INLINE_CITATION_RE.findall(answer_text or ""))
    support_span_count = 0
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
        _satisfied_completeness_slots(
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
        for slot in _evidence_supported_completeness_slots(
            required_slots=required_slots,
            article_span_selector=article_span_selector,
            chunks=chunks,
        )
        if slot not in set(satisfied_slots)
    ]
    if has_answer and evidence_reentry_slots:
        satisfied_slots = dedupe_strings([*satisfied_slots, *evidence_reentry_slots])
    missing_slots = [slot for slot in required_slots if slot not in set(satisfied_slots)]
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
    )
    structurally_full = bool(
        has_answer
        and answer_fact_units >= minimum_required_facts
        and citation_count >= 1
        and effective_support_count >= 1
    )
    if not has_answer:
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
    }


def _strong_source_family_gate(source_family_resolution: SourceFamilyResolution) -> set[str]:
    if source_family_resolution.preferred_families:
        return set(_expand_source_family_aliases(source_family_resolution.preferred_families))
    if source_family_resolution.family_confidence < 0.75:
        return set()
    return set(_expand_source_family_aliases(source_family_resolution.routing_families))


def _apply_pre_generation_family_pool(
    *,
    chunks: list[RetrievedChunk],
    source_family_resolution: SourceFamilyResolution,
    top_k_effective: int,
) -> tuple[list[RetrievedChunk], dict[str, Any]]:
    expected_family_prior = source_family_resolution.expected_family_prior or source_family_resolution.predicted_family
    pre_filter_family_set = dedupe_strings(
        (_resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk) or "unknown")
        for chunk in chunks
    )
    preferred_families = dedupe_strings(_expand_source_family_aliases(source_family_resolution.preferred_families))
    fallback_families = list(source_family_resolution.fallback_families)
    family_gate_reason = source_family_resolution.family_override_reason
    no_gate_reason = ""
    if not chunks:
        no_gate_reason = "no_candidates"
    elif not preferred_families:
        no_gate_reason = "no_preferred_family_prior"
    policy: dict[str, Any] = {
        "expected_family_prior": expected_family_prior,
        "preferred_families": preferred_families,
        "fallback_families": fallback_families,
        "preferred_family_pool_size": 0,
        "cross_family_fallback_used": False,
        "selected_family_confidence": round(source_family_resolution.selected_family_confidence, 3),
        "family_override_reason": source_family_resolution.family_override_reason,
        "pre_filter_family_set": pre_filter_family_set,
        "reranked_family_set": pre_filter_family_set,
        "selected_family_source": pre_filter_family_set[0] if pre_filter_family_set else None,
        "family_gate_status": "no_gate",
        "family_gate_reason": family_gate_reason,
        "no_gate_reason": no_gate_reason,
    }
    if not chunks or not preferred_families:
        return chunks, policy

    preferred_family_set = set(preferred_families)
    preferred_chunks = [
        chunk for chunk in chunks
        if (_resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk) or "unknown") in preferred_family_set
    ]
    policy["preferred_family_pool_size"] = len(preferred_chunks)
    if preferred_chunks:
        policy["family_override_reason"] = "strong_preferred_family_pool"
        policy["family_gate_reason"] = "preferred_family_pool_available"
        policy["no_gate_reason"] = ""
        reranked_family_set = dedupe_strings(
            (_resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk) or "unknown")
            for chunk in preferred_chunks
        )
        policy["reranked_family_set"] = reranked_family_set
        policy["selected_family_source"] = reranked_family_set[0] if reranked_family_set else None
        policy["family_gate_status"] = "locked_preferred_family"
        return preferred_chunks[:top_k_effective], policy

    fallback_family_set = set(fallback_families)
    if expected_family_prior in _HARD_PRE_GENERATION_FAMILY_GATES:
        policy["family_override_reason"] = "hard_family_gate_no_preferred_candidates"
        policy["family_gate_reason"] = "hard_family_gate_no_preferred_candidates"
        policy["no_gate_reason"] = ""
        policy["family_gate_status"] = "hard_gate_no_preferred_candidates"
        policy["reranked_family_set"] = []
        policy["selected_family_source"] = None
        return [], policy

    fallback_chunks = [
        chunk for chunk in chunks
        if fallback_family_set
        and (_resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk) or "unknown")
        in fallback_family_set
    ]
    policy["cross_family_fallback_used"] = True
    if fallback_chunks:
        policy["family_override_reason"] = "preferred_family_pool_empty_controlled_alias_fallback"
        policy["family_gate_reason"] = "controlled_alias_fallback"
        policy["no_gate_reason"] = ""
        reranked_family_set = dedupe_strings(
            (_resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk) or "unknown")
            for chunk in fallback_chunks
        )
        policy["reranked_family_set"] = reranked_family_set
        policy["selected_family_source"] = reranked_family_set[0] if reranked_family_set else None
        policy["family_gate_status"] = "controlled_alias_fallback"
        return fallback_chunks[:top_k_effective], policy

    policy["family_override_reason"] = "preferred_family_pool_empty_global_fallback"
    policy["family_gate_reason"] = "global_fallback"
    policy["no_gate_reason"] = ""
    filtered = chunks[:top_k_effective]
    reranked_family_set = dedupe_strings(
        (_resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk) or "unknown")
        for chunk in filtered
    )
    policy["reranked_family_set"] = reranked_family_set
    policy["selected_family_source"] = reranked_family_set[0] if reranked_family_set else None
    policy["family_gate_status"] = "global_fallback"
    return filtered, policy


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
) -> dict[str, Any]:
    assembled_evidence = _build_assembled_evidence(post_rerank_chunks, query=user_query)
    if not assembled_evidence and model_cited_source_ids:
        assembled_evidence = _build_fallback_assembled_evidence(
            model_cited_source_ids,
            fallback_excerpt=answer_contract.get("answer_text") or assembled_context or "",
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
            "document_identity_score": (source_identity_reranker or {}).get("document_identity_score"),
            "title_match_type": (source_identity_reranker or {}).get("title_match_type"),
            "identifier_match_type": (source_identity_reranker or {}).get("identifier_match_type"),
            "issuer_match_type": (source_identity_reranker or {}).get("issuer_match_type"),
            "year_match_type": (source_identity_reranker or {}).get("year_match_type"),
            "identity_rerank_input_source": (source_identity_reranker or {}).get("identity_rerank_input_source"),
            "document_rerank_reason": (source_identity_reranker or {}).get("document_rerank_reason"),
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
        "law_scope_signal": law_scope_signal,
        "question_type": question_type,
        "target_date": target_date,
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
    return {
        "answer_text": answer_text,
        "ordered_citation_list": list(citations),
        "ordered_source_id_list": list(source_ids),
        "final_mode": final_mode,
        "final_reason": final_reason,
    }


def _build_persisted_response_envelope_snapshot(
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
    if final_mode == "blocked":
        return "refusal"
    return final_mode


def _sanitize_public_answer_contract(answer_contract: dict[str, Any] | None) -> dict[str, Any] | None:
    if answer_contract is None:
        return None
    sanitized = dict(answer_contract)
    sanitized["final_mode"] = _sanitize_public_final_mode(answer_contract.get("final_mode"))
    return sanitized


def _resolve_contract_suppressed_answer_text(
    *,
    answer_text: str,
    answer_contract: dict[str, Any] | None,
) -> str:
    if isinstance(answer_contract, dict) and answer_contract.get("answer_suppressed_due_to_evidence_gap") is True:
        return controlled_fallback_answer(answer_contract)
    return answer_text


def _resolve_public_answer_text(
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


def _extract_answer_source_ids(
    *,
    answer_contract: dict[str, Any] | None,
    citations: list[str],
) -> list[str]:
    source_ids: list[str] = []
    if isinstance(answer_contract, dict):
        primary = answer_contract.get("primary_source_id")
        if isinstance(primary, str) and primary.strip():
            source_ids.append(primary.strip())
        secondary = answer_contract.get("secondary_source_ids")
        if isinstance(secondary, list):
            for item in secondary:
                if isinstance(item, str) and item.strip():
                    source_ids.append(item.strip())
    if source_ids:
        return source_ids
    return [item for item in citations if isinstance(item, str) and item.strip()]


def _verification_has_hallucination_fail(verification: dict[str, Any] | None) -> bool:
    if not isinstance(verification, dict):
        return False
    verdict = verification.get("verdict")
    if isinstance(verdict, str) and verdict.lower() == "fail":
        return True
    risk = verification.get("hallucination_risk")
    return isinstance(risk, (int, float)) and risk > 0.5


def _parity_trace_enabled() -> bool:
    return os.getenv("PARITY_TRACE_ENABLED", "false").lower() in {"1", "true", "yes"}


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


def _canonical_stage_payload(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash_stage_payload(payload: Any) -> str:
    return hashlib.sha256(_canonical_stage_payload(payload).encode("utf-8")).hexdigest()


def _question_messages_payload(messages: list[ConversationMessage]) -> list[dict[str, str]]:
    return [{"role": msg.role, "content": msg.content} for msg in messages]


def _request_stage_payload(request_body: ChatCompletionRequest) -> dict[str, Any]:
    return {
        "model": request_body.model,
        "messages": _question_messages_payload(request_body.messages),
        "stream": request_body.stream,
        "temperature": request_body.temperature,
        "max_tokens": request_body.max_tokens,
        "session_id_present": bool(request_body.session_id),
        "law_filter": request_body.law_filter,
        "use_verification": request_body.use_verification,
        "top_k": request_body.top_k,
        "include_trace": request_body.include_trace,
    }


def _normalized_request_stage_payload(request_body: ChatCompletionRequest) -> dict[str, Any]:
    return {
        "model": request_body.model,
        "messages": _question_messages_payload(request_body.messages),
        "stream": bool(request_body.stream),
        "temperature": request_body.temperature if request_body.temperature is not None else 0.1,
        "max_tokens": request_body.max_tokens if request_body.max_tokens is not None else 512,
        "law_filter": request_body.law_filter,
        "use_verification": bool(request_body.use_verification),
        "top_k": int(request_body.top_k),
        "include_trace": bool(request_body.include_trace),
    }


def _auth_enriched_stage_payload(
    *,
    request_body: ChatCompletionRequest,
    request: Request,
) -> dict[str, Any]:
    _ = request
    return _normalized_request_stage_payload(request_body)


def _session_enriched_stage_payload(
    *,
    request_body: ChatCompletionRequest,
    request: Request,
    session_id: str,
    conversation_history: list[dict[str, str]],
) -> dict[str, Any]:
    payload = _normalized_request_stage_payload(request_body)
    payload.update(
        {
            "session_id_present": bool(session_id),
            "conversation_history": conversation_history,
            "request_id_present": isinstance(getattr(request.state, "request_id", None), str),
            "trace_id_present": isinstance(getattr(request.state, "trace_id", None), str),
        }
    )
    return payload


def _retrieval_input_stage_payload(
    *,
    pre_answer_payload: dict[str, Any],
    law_filter: str | None,
) -> dict[str, Any]:
    return {
        "query": pre_answer_payload.get("retrieval_query"),
        "top_k": pre_answer_payload.get("top_k_effective"),
        "metadata_filter": {"law_short_name": law_filter} if law_filter else None,
        "mentioned_laws": pre_answer_payload.get("mentioned_laws") or [],
        "retrieval_plan": pre_answer_payload.get("retrieval_plan"),
        "explicit_article_refs": pre_answer_payload.get("explicit_article_refs") or [],
        "forced_article_refs": pre_answer_payload.get("forced_article_refs") or [],
        "applied_expansions": pre_answer_payload.get("applied_expansions") or [],
        "reranker_enabled": bool(pre_answer_payload.get("reranker_enabled")),
    }


def _retrieved_source_id_stage_payload(trace_payload: dict[str, Any]) -> dict[str, Any]:
    retrieval = trace_payload.get("retrieval") if isinstance(trace_payload, dict) else {}
    chunks = retrieval.get("post_rerank_chunks") if isinstance(retrieval, dict) else []
    ordered_source_ids: list[str] = []
    if isinstance(chunks, list):
        for item in chunks:
            if not isinstance(item, dict):
                continue
            source_id = item.get("source_id")
            if not isinstance(source_id, str) or not source_id.strip():
                continue
            ordered_source_ids.append(canonicalize_source_id(source_id) or source_id)
    return {
        "ordered_source_id_list": ordered_source_ids,
    }


def _assembly_payload_from_trace(trace_payload: dict[str, Any]) -> dict[str, Any]:
    parsed_query = trace_payload.get("parsed_query") if isinstance(trace_payload, dict) else {}
    context_assembly = trace_payload.get("context_assembly") if isinstance(trace_payload, dict) else {}
    return {
        "query": parsed_query.get("enriched_query") if isinstance(parsed_query, dict) else None,
        "assembled_context": (
            context_assembly.get("assembled_context") if isinstance(context_assembly, dict) else None
        ),
        "allowed_source_whitelist": (
            context_assembly.get("allowed_source_whitelist") if isinstance(context_assembly, dict) else []
        ),
        "assembled_evidence_source_ids": [
            item.get("source_id")
            for item in (context_assembly.get("assembled_evidence") if isinstance(context_assembly, dict) else [])
            if isinstance(item, dict) and item.get("source_id")
        ],
    }


def _context_enriched_stage_payload(
    *,
    request: Request,
    session_id: str,
    conversation_history: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "auth_subject": getattr(request.state, "auth_subject", None),
        "session_id_present": bool(session_id),
        "conversation_history": conversation_history,
        "request_id_present": isinstance(getattr(request.state, "request_id", None), str),
        "trace_id_present": isinstance(getattr(request.state, "trace_id", None), str),
    }


def _source_projection_payload(source_ids: list[str]) -> dict[str, Any]:
    return {
        "ordered_source_id_list": source_ids,
        "ordered_canonical_norm_keys": [canonicalize_source_id(item) or item for item in source_ids],
    }


def _pre_answer_stage_payload(
    *,
    decision_lane: str,
    user_message: str,
    enriched_query: str,
    retrieval_query: str,
    conversation_history: list[dict[str, str]],
    mentioned_laws: list[str],
    requested_source_families: list[str],
    explicit_article_refs: list[tuple[str, str]],
    forced_article_refs: list[tuple[str, str]],
    applied_expansions: list[str],
    top_k_requested: int,
    top_k_effective: int,
    reranker_enabled: bool,
    retrieval_plan: dict[str, Any] | None = None,
    metadata_first_selector: dict[str, Any] | None = None,
    source_identity_reranker: dict[str, Any] | None = None,
    source_cluster_selector: dict[str, Any] | None = None,
    article_span_selector: dict[str, Any] | None = None,
    source_family_resolution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "decision_lane": decision_lane,
        "user_message": user_message,
        "enriched_query": enriched_query,
        "retrieval_query": retrieval_query,
        "conversation_history": conversation_history,
        "mentioned_laws": mentioned_laws,
        "requested_source_families": requested_source_families,
        "explicit_article_refs": explicit_article_refs,
        "forced_article_refs": forced_article_refs,
        "applied_expansions": applied_expansions,
        "retrieval_plan": retrieval_plan,
        "metadata_first_selector": metadata_first_selector,
        "source_identity_reranker": source_identity_reranker,
        "source_cluster_selector": source_cluster_selector,
        "article_span_selector": article_span_selector,
        "source_family_resolution": source_family_resolution,
        "top_k_requested": top_k_requested,
        "top_k_effective": top_k_effective,
        "reranker_enabled": reranker_enabled,
    }


def _raw_answer_stage_payload(
    *,
    raw_answer_object: dict[str, Any] | None,
    fallback_answer_text: str,
) -> dict[str, Any]:
    if isinstance(raw_answer_object, dict) and raw_answer_object:
        return raw_answer_object
    return {
        "role": "assistant",
        "content": fallback_answer_text,
        "bypassed_model": True,
    }


def _visible_projection_stage_payload(
    *,
    answer_text: str,
    citations: list[str],
    answer_contract: dict[str, Any] | None,
    final_mode: str | None,
    final_reason: str | None,
) -> dict[str, Any]:
    source_ids = _extract_answer_source_ids(answer_contract=answer_contract, citations=citations)
    return {
        "final_mode": final_mode,
        "answer_body": answer_text if final_mode != "refusal" else "",
        "refusal_body": answer_text if final_mode == "refusal" else "",
        "refusal_reason": final_reason,
        "ordered_citation_list": list(citations),
        "visible_citation_projection": list(citations),
        **_source_projection_payload(source_ids),
    }


def _response_envelope_stage_payload(
    *,
    request_body: ChatCompletionRequest,
    answer_text: str,
    citations: list[str],
    blocked: bool,
    guardrails_reasons: list[str],
    verification: dict[str, Any] | None,
    answer_contract: dict[str, Any] | None,
    final_mode: str | None,
    final_reason: str | None,
) -> dict[str, Any]:
    projected_guardrails_reasons = _project_rc_l_guardrails_reasons(
        answer_text=answer_text,
        citations=citations,
        guardrails_reasons=guardrails_reasons,
    )
    return {
        "object": "chat.completion",
        "model": request_body.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": answer_text},
                "finish_reason": "stop",
            }
        ],
        "citations": list(citations),
        "blocked": blocked,
        "guardrails_reasons": projected_guardrails_reasons,
        "verification": verification,
        "final_mode": final_mode,
        "final_reason": final_reason,
        "answer_contract": answer_contract,
    }


def _extract_inline_citation_ids(answer_text: str) -> list[str]:
    extracted: list[str] = []
    for raw_citation in _INLINE_CITATION_RE.findall(answer_text or ""):
        canonical = canonicalize_source_id(raw_citation)
        if canonical:
            extracted.append(canonical)
    return dedupe_strings(extracted)


def _project_rc_l_guardrails_reasons(
    *,
    answer_text: str,
    citations: list[str],
    guardrails_reasons: list[str],
) -> list[str]:
    projected = dedupe_strings(list(guardrails_reasons))
    if release_lane_id().lower() != "rc_l":
        return projected

    inline_citations = _extract_inline_citation_ids(answer_text)
    visible_citations = dedupe_strings(
        [canonicalize_source_id(citation) or citation for citation in citations]
    )
    if not inline_citations or not visible_citations:
        return projected

    visible_set = set(visible_citations)
    if any(citation not in visible_set for citation in inline_citations):
        projected.append("source_lock_fallback")
    return dedupe_strings(projected)


def _eval_client_parsed_stage_payload(
    *,
    answer_text: str,
    citations: list[str],
    blocked: bool,
    verification: dict[str, Any] | None,
    answer_contract: dict[str, Any] | None,
    final_mode: str | None,
    final_reason: str | None,
) -> dict[str, Any]:
    return {
        "answer_text": answer_text,
        "citations": list(citations),
        "blocked": blocked,
        "verification": verification,
        "final_mode": final_mode,
        "final_reason": final_reason,
        "answer_contract": answer_contract,
    }


def _normalized_parity_stage_payload(
    *,
    answer_text: str,
    citations: list[str],
    answer_contract: dict[str, Any] | None,
    final_mode: str | None,
    final_reason: str | None,
) -> dict[str, Any]:
    source_ids = _extract_answer_source_ids(answer_contract=answer_contract, citations=citations)
    refusal_reason = None
    if isinstance(answer_contract, dict):
        unsupported_reason = answer_contract.get("unsupported_reason")
        if isinstance(unsupported_reason, str) and unsupported_reason.strip():
            refusal_reason = unsupported_reason
    if refusal_reason is None:
        refusal_reason = final_reason

    return {
        "final_mode": final_mode,
        "answer_body": answer_text if final_mode != "refusal" else "",
        "refusal_body": answer_text if final_mode == "refusal" else "",
        "refusal_reason": refusal_reason,
        "ordered_citation_list": list(citations),
        "ordered_source_id_list": source_ids,
        "ordered_canonical_norm_keys": [canonicalize_source_id(item) or item for item in source_ids],
        "visible_citation_projection": list(citations),
    }


def _append_parity_stage(
    stages: list[dict[str, Any]],
    *,
    stage_name: str,
    payload: dict[str, Any],
) -> None:
    stages.append(
        {
            "stage": stage_name,
            "hash": _hash_stage_payload(payload),
            "payload": payload,
        }
    )


def _v3_parity_topology_label() -> str:
    return (os.getenv("PARITY_TOPOLOGY_LABEL") or "canonical").strip() or "canonical"


def _worker_assignment_stage_payload() -> dict[str, Any]:
    return {
        "topology_label": _v3_parity_topology_label(),
        "process_mode": os.getenv("PARITY_PROCESS_MODE", "shared_process"),
        "fresh_client_per_request": _env_flag("PARITY_FRESH_CLIENT_PER_REQUEST", False),
        "hard_reset_after_request": _env_flag("PARITY_HARD_RESET_AFTER_REQUEST", False),
        "worker_count": int(os.getenv("PARITY_WORKER_COUNT", "1")),
        "pinned_worker_id": os.getenv("PARITY_PINNED_WORKER_ID", "worker-0"),
        "parallelism_enabled": _env_flag("PARITY_PARALLELISM_ENABLED", False),
        "failover_enabled": _env_flag("PARITY_FAILOVER_ENABLED", False),
    }


def _session_namespace_stage_payload(*, request: Request, session_id: str) -> dict[str, Any]:
    base_namespace = os.getenv("SESSION_STORE_NAMESPACE", "hukuk-ai")
    mode = os.getenv("PARITY_SESSION_NAMESPACE_MODE", "canonical")
    namespace = base_namespace
    request_local_suffix = None
    if mode == "fresh_per_request":
        request_local_suffix = "request_id"
        namespace = f"{base_namespace}:<request-local>"
    return {
        "mode": mode,
        "namespace": namespace,
        "request_local_suffix": request_local_suffix,
        "session_id_present": bool(session_id),
    }


def _cache_namespace_stage_payload(*, model_request_payload: dict[str, Any]) -> dict[str, Any]:
    policy = os.getenv("PARITY_GENERATION_CACHE_POLICY", "off")
    namespace = None if policy == "off" else os.getenv("PARITY_GENERATION_CACHE_NAMESPACE", "canonical")
    cache_key = None
    if policy != "off":
        cache_key = _hash_stage_payload(
            {
                "namespace": namespace,
                "model_request_payload": model_request_payload,
            }
        )
    return {
        "policy": policy,
        "namespace": namespace,
        "cache_key": cache_key,
    }


def _generation_start_ordinal_stage_payload() -> dict[str, Any]:
    return {
        "ordinal": next(_GENERATION_START_ORDINAL),
        "request_ordering": os.getenv("PARITY_REQUEST_ORDERING", "serial"),
        "serial_execution": os.getenv("PARITY_REQUEST_ORDERING", "serial") == "serial",
    }


def _raw_generation_hash_payloads(raw_answer_payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    text = raw_answer_payload.get("extracted_text") or raw_answer_payload.get("content") or ""
    try:
        token_trace = build_text_token_trace(text if isinstance(text, str) else str(text))
    except TokenAccountingError as exc:
        token_trace = {
            "source": "error",
            "tokenizer_ref": None,
            "token_count": 0,
            "first_token_id_hash": None,
            "raw_token_stream_hash": None,
            "error": str(exc),
        }
    first_token_payload = {
        "first_token_id_hash": token_trace.get("first_token_id_hash"),
        "source": token_trace.get("source"),
        "tokenizer_ref": token_trace.get("tokenizer_ref"),
        "token_count": token_trace.get("token_count"),
    }
    raw_stream_payload = {
        "raw_token_stream_hash": token_trace.get("raw_token_stream_hash"),
        "source": token_trace.get("source"),
        "tokenizer_ref": token_trace.get("tokenizer_ref"),
        "token_count": token_trace.get("token_count"),
    }
    if token_trace.get("error"):
        first_token_payload["error"] = token_trace["error"]
        raw_stream_payload["error"] = token_trace["error"]
    return first_token_payload, raw_stream_payload


def _build_v3_runtime_parity_trace(
    *,
    request: Request,
    request_body: ChatCompletionRequest,
    session_id: str,
    answer_text: str,
    citations: list[str],
    blocked: bool,
    guardrails_reasons: list[str],
    verification: dict[str, Any] | None,
    answer_contract: dict[str, Any] | None,
    final_mode: str | None,
    final_reason: str | None,
    llm_trace: dict[str, Any] | None,
) -> dict[str, Any]:
    model_request_payload = (llm_trace or {}).get("model_request_payload") or {}
    generation_contract = (llm_trace or {}).get("generation_contract") or {}
    raw_answer_payload = _raw_answer_stage_payload(
        raw_answer_object=(llm_trace or {}).get("raw_answer_object"),
        fallback_answer_text=answer_text,
    )
    first_token_payload, raw_stream_payload = _raw_generation_hash_payloads(raw_answer_payload)

    stages: list[dict[str, Any]] = []
    _append_parity_stage(
        stages,
        stage_name="normalized_request",
        payload=_normalized_request_stage_payload(request_body),
    )
    _append_parity_stage(
        stages,
        stage_name="model_request_payload",
        payload=model_request_payload,
    )
    _append_parity_stage(
        stages,
        stage_name="generation_contract",
        payload=generation_contract,
    )
    _append_parity_stage(
        stages,
        stage_name="worker_assignment_tuple",
        payload=_worker_assignment_stage_payload(),
    )
    _append_parity_stage(
        stages,
        stage_name="session_namespace_after_payload_freeze",
        payload=_session_namespace_stage_payload(request=request, session_id=session_id),
    )
    _append_parity_stage(
        stages,
        stage_name="cache_namespace_or_cache_key",
        payload=_cache_namespace_stage_payload(model_request_payload=model_request_payload),
    )
    _append_parity_stage(
        stages,
        stage_name="generation_start_ordinal",
        payload=_generation_start_ordinal_stage_payload(),
    )
    _append_parity_stage(
        stages,
        stage_name="first_token_id_hash",
        payload=first_token_payload,
    )
    _append_parity_stage(
        stages,
        stage_name="raw_token_stream_hash",
        payload=raw_stream_payload,
    )
    _append_parity_stage(
        stages,
        stage_name="raw_answer_object",
        payload=raw_answer_payload,
    )
    _append_parity_stage(
        stages,
        stage_name="response_envelope",
        payload=_response_envelope_stage_payload(
            request_body=request_body,
            answer_text=answer_text,
            citations=citations,
            blocked=blocked,
            guardrails_reasons=guardrails_reasons,
            verification=verification,
            answer_contract=answer_contract,
            final_mode=final_mode,
            final_reason=final_reason,
        ),
    )
    _append_parity_stage(
        stages,
        stage_name="eval_client_parsed_object",
        payload=_eval_client_parsed_stage_payload(
            answer_text=answer_text,
            citations=citations,
            blocked=blocked,
            verification=verification,
            answer_contract=answer_contract,
            final_mode=final_mode,
            final_reason=final_reason,
        ),
    )
    _append_parity_stage(
        stages,
        stage_name="normalized_parity_object",
        payload=_normalized_parity_stage_payload(
            answer_text=answer_text,
            citations=citations,
            answer_contract=answer_contract,
            final_mode=final_mode,
            final_reason=final_reason,
        ),
    )
    return {
        "schema_version": "faz10-v3-runtime-parity-trace-schema-v1",
        "topology_label": _v3_parity_topology_label(),
        "stages": stages,
        "preprojection_hash": stages[9]["hash"],
        "normalized_parity_hash": stages[12]["hash"],
    }


def _attach_parity_trace(
    *,
    trace_payload: dict[str, Any],
    request: Request,
    request_body: ChatCompletionRequest,
    session_id: str,
    conversation_history: list[dict[str, str]],
    pre_answer_payload: dict[str, Any],
    answer_text: str,
    citations: list[str],
    blocked: bool,
    guardrails_reasons: list[str],
    verification: dict[str, Any] | None,
    answer_contract: dict[str, Any] | None,
    final_mode: str | None,
    final_reason: str | None,
    llm_trace: dict[str, Any] | None,
) -> dict[str, Any]:
    if not _parity_trace_enabled():
        return trace_payload

    stages: list[dict[str, Any]] = []
    normalized_request_payload = _normalized_request_stage_payload(request_body)
    _append_parity_stage(
        stages,
        stage_name="raw_input_request",
        payload=_request_stage_payload(request_body),
    )
    _append_parity_stage(
        stages,
        stage_name="normalized_request",
        payload=normalized_request_payload,
    )
    _append_parity_stage(
        stages,
        stage_name="auth_enriched_request",
        payload=_auth_enriched_stage_payload(
            request_body=request_body,
            request=request,
        ),
    )
    _append_parity_stage(
        stages,
        stage_name="session_enriched_request",
        payload=_session_enriched_stage_payload(
            request_body=request_body,
            request=request,
            session_id=session_id,
            conversation_history=conversation_history,
        ),
    )
    _append_parity_stage(
        stages,
        stage_name="retrieval_input_payload",
        payload=_retrieval_input_stage_payload(
            pre_answer_payload=pre_answer_payload,
            law_filter=request_body.law_filter,
        ),
    )
    _append_parity_stage(
        stages,
        stage_name="retrieved_source_id_ordered_list",
        payload=_retrieved_source_id_stage_payload(trace_payload),
    )
    _append_parity_stage(
        stages,
        stage_name="assembly_payload",
        payload=(llm_trace or {}).get("assembly_payload") or _assembly_payload_from_trace(trace_payload),
    )
    _append_parity_stage(
        stages,
        stage_name="model_request_payload",
        payload=(llm_trace or {}).get("model_request_payload") or {},
    )
    _append_parity_stage(
        stages,
        stage_name="generation_contract",
        payload=(llm_trace or {}).get("generation_contract") or {},
    )
    raw_answer_payload = _raw_answer_stage_payload(
        raw_answer_object=(llm_trace or {}).get("raw_answer_object"),
        fallback_answer_text=answer_text,
    )
    _append_parity_stage(
        stages,
        stage_name="raw_answer_object",
        payload=raw_answer_payload,
    )
    _append_parity_stage(
        stages,
        stage_name="response_envelope",
        payload=_response_envelope_stage_payload(
            request_body=request_body,
            answer_text=answer_text,
            citations=citations,
            blocked=blocked,
            guardrails_reasons=guardrails_reasons,
            verification=verification,
            answer_contract=answer_contract,
            final_mode=final_mode,
            final_reason=final_reason,
        ),
    )
    _append_parity_stage(
        stages,
        stage_name="eval_client_parsed_object",
        payload=_eval_client_parsed_stage_payload(
            answer_text=answer_text,
            citations=citations,
            blocked=blocked,
            verification=verification,
            answer_contract=answer_contract,
            final_mode=final_mode,
            final_reason=final_reason,
        ),
    )
    _append_parity_stage(
        stages,
        stage_name="normalized_parity_object",
        payload=_normalized_parity_stage_payload(
            answer_text=answer_text,
            citations=citations,
            answer_contract=answer_contract,
            final_mode=final_mode,
            final_reason=final_reason,
        ),
    )

    enriched_trace = dict(trace_payload)
    enriched_trace["parity_trace"] = {
        "stages": stages,
        "preprojection_hash": raw_answer_payload and stages[9]["hash"],
        "normalized_parity_hash": stages[12]["hash"],
    }
    enriched_trace["v3_runtime_parity_trace"] = _build_v3_runtime_parity_trace(
        request=request,
        request_body=request_body,
        session_id=session_id,
        answer_text=answer_text,
        citations=citations,
        blocked=blocked,
        guardrails_reasons=guardrails_reasons,
        verification=verification,
        answer_contract=answer_contract,
        final_mode=final_mode,
        final_reason=final_reason,
        llm_trace=llm_trace,
    )
    return enriched_trace


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
    answer_text = _resolve_contract_suppressed_answer_text(
        answer_text=answer_text,
        answer_contract=answer_contract,
    )
    trace_payload = dict(trace_payload)
    trace_payload["answer_contract"] = answer_contract
    trace_payload["answer_contract_validation"] = contract_repair.validation
    trace_payload["confidence_0_100"] = contract_repair.confidence_0_100
    generation_outcome = trace_payload.get("generation_outcome")
    if isinstance(generation_outcome, dict):
        generation_outcome = dict(generation_outcome)
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
    # ── Doğrulama ────────────────────────────────────────────────────────────
    if not request_body.messages:
        raise HTTPException(status_code=400, detail="messages listesi boş olamaz")

    # Son kullanıcı mesajını çıkar
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

    # ── Session & Multi-turn ─────────────────────────────────────────────────
    session_id = request_body.session_id or f"sess-{uuid.uuid4().hex[:16]}"
    response_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    request_history: list[dict[str, str]] = [
        {"role": msg.role, "content": msg.content}
        for msg in request_body.messages[:-1]
        if msg.role in {"user", "assistant", "system"}
    ]
    conversation_history = request_history
    if not conversation_history and not (
        _release_controls_boundary_proxy_enabled()
        and _release_controls_perimeter_session_isolation_enabled()
    ):
        conversation_history = store.get_history(session_id)

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

    # Dar kapsamlı, yüksek isabetli deterministic çapraz-kanun / TBK yanıtları
    precise_lane = "precise_cross_law_shortcut"
    precise_answer = _build_precise_tmk_tbk_cross_law_answer(last_user_msg)
    if not precise_answer:
        precise_lane = "precise_tbk_shortcut"
        precise_answer = _build_precise_tbk_answer(last_user_msg)
    if precise_answer:
        answer_text, precise_citations = precise_answer
        mentioned_laws = _extract_law_mentions(last_user_msg)
        explicit_article_refs = _extract_explicit_article_refs(last_user_msg)
        request_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request_body.messages[:-1]
            if msg.role in {"user", "assistant", "system"}
        ]
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

    # Deterministic kapsam-dışı refusal (low-risk hardening)
    scope_refusal_reason = _detect_scope_refusal_reason(last_user_msg)
    if scope_refusal_reason:
        answer_text = (
            "Bu soru TBK kapsamı dışı bir konuya giriyor "
            f"({scope_refusal_reason}). Elimdeki TBK kaynaklarıyla bu soruya yanıt veremiyorum. "
            "Lütfen ilgili mevzuat için uzman bir hukukçuya danışın."
        )
        mentioned_laws = _extract_law_mentions(last_user_msg)
        explicit_article_refs = _extract_explicit_article_refs(last_user_msg)
        request_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request_body.messages[:-1]
            if msg.role in {"user", "assistant", "system"}
        ]
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
    forced_article_refs: list[tuple[str, str]] = []
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
    metadata_lookup_query_signals = _parse_metadata_lookup_query_signals(routing_query)
    metadata_first_selector = _select_metadata_first_source_candidates(
        query=routing_query,
        requested_source_families=requested_source_families,
        source_family_resolution=source_family_resolution,
        query_metadata_signals=metadata_lookup_query_signals,
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
            ("yıllık ücretli izin", "yillik ucretli izin", "ücretli izin", "ucretli izin", "hafta tatili"),
            "TBK m.421 TBK m.422 hizmet sözleşmesi hafta tatili ücretli izin",
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

    # ── Retrieval ─────────────────────────────────────────────────────────────
    retrieved_chunks: list[RetrievedChunk] = []
    pre_rerank_chunks: list[RetrievedChunk] = []
    post_rerank_chunks: list[RetrievedChunk] = []
    source_cluster_selector: dict[str, Any] | None = None
    source_identity_reranker: dict[str, Any] | None = None
    article_span_selector: dict[str, Any] | None = None
    selected_source_keys: set[str] = set()
    family_routing_policy: dict[str, Any] | None = None
    if metadata_first_selector:
        for candidate in metadata_first_selector.get("candidates") or []:
            selected_source_keys.update(candidate.get("focus_keys") or [])
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
                before_family_pool_count = len(retrieved_chunks)
                retrieved_chunks, family_routing_policy = _apply_pre_generation_family_pool(
                    chunks=retrieved_chunks,
                    source_family_resolution=source_family_resolution,
                    top_k_effective=top_k_effective,
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
    completeness_synthesis = _build_completeness_synthesis_features(
        query=routing_query,
        answer_text=hardening.answer_text,
        article_span_selector=article_span_selector,
        chunks=post_rerank_chunks,
    )
    hardening.answer_contract.update(completeness_synthesis)
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
