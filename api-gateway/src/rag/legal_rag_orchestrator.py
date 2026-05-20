from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sqlite3
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from data_pipeline.judicial import (
    JudicialHybridRetriever,
    PersistentJudicialExactLookupStore,
    query_judicial_lexical_index,
    validate_judicial_evidence_results,
)
from rag.query_analyzer import analyze_query
from rag.retriever import RetrievalResult


logger = logging.getLogger(__name__)

_TR_ASCII_TRANSLATION = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "İ": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "â": "a",
        "î": "i",
        "û": "u",
    }
)
_LEGAL_NO_RE = r"\d{4}/\d{1,8}"
_E_RE = re.compile(r"(?:\bE\.?|ESAS(?:\s+NO)?)[\s:.-]*(?P<value>" + _LEGAL_NO_RE + r")", re.IGNORECASE)
_K_RE = re.compile(r"(?:\bK\.?|KARAR(?:\s+NO)?)[\s:.-]*(?P<value>" + _LEGAL_NO_RE + r")", re.IGNORECASE)
_E_SUFFIX_RE = re.compile(r"(?P<value>" + _LEGAL_NO_RE + r")\s*E\.?", re.IGNORECASE)
_K_SUFFIX_RE = re.compile(r"(?P<value>" + _LEGAL_NO_RE + r")\s*K\.?", re.IGNORECASE)
_DATE_RE = re.compile(r"\b(?P<date>\d{4}-\d{2}-\d{2}|\d{1,2}[./]\d{1,2}[./]\d{4})\b")
_YEAR_RE = re.compile(r"\b(?P<year>19\d{2}|20\d{2})\b")
_SHA256_RE = re.compile(r"\b[0-9a-f]{64}\b", re.IGNORECASE)
_CANONICAL_ID_RE = re.compile(r"\bjudicial_decision:[A-Za-z0-9_./:-]+\b")
_JUDICIAL_COVERAGE_AUDIT_FILENAME = "judicial_processed_coverage_audit.json"
_SQLITE_BUSY_TIMEOUT_MS = 5000
_EXACT_LOOKUP_REQUIRED_TABLES = ("decisions", "lookup", "chunk_refs")
_LEXICAL_REQUIRED_TABLES = ("chunks", "chunks_fts")
_EXACT_DECISION_REQUIRED_FIELDS = (
    "canonical_decision_id",
    "citation_key",
    "court",
    "chamber",
    "decision_date",
    "esas_no",
    "karar_no",
    "source_url",
)
_LEXICAL_CHUNK_REQUIRED_FIELDS = (
    "chunk_key",
    "canonical_decision_id",
    "citation_key",
    "court",
    "chamber",
    "decision_date",
    "esas_no",
    "karar_no",
    "paragraph_start",
    "paragraph_end",
    "source_url",
    "source_type",
)
_COURT_HINTS = (
    ("yargitay", "Yargıtay"),
    ("danistay", "Danıştay"),
    ("anayasa mahkemesi", "Anayasa Mahkemesi"),
    ("bolge adliye mahkemesi", "Bölge Adliye Mahkemesi"),
    ("bolge idare mahkemesi", "Bölge İdare Mahkemesi"),
)
_NATIVE_DIALOG_TERMS = {
    "merhaba",
    "selam",
    "günaydın",
    "gunaydin",
    "iyi akşamlar",
    "iyi aksamlar",
    "teşekkür",
    "tesekkur",
}
_JUDICIAL_TERMS = {
    "emsal",
    "ictihat",
    "içtihat",
    "yargitay",
    "yargıtay",
    "danistay",
    "danıştay",
    "aym",
    "karar",
    "esas",
    "karar no",
    "hukuk dairesi",
    "ceza dairesi",
    "genel kurul",
}
_LEGISLATION_TERMS = {
    "kanun",
    "madde",
    "mevzuat",
    "tbk",
    "tmk",
    "tck",
    "hmk",
    "cmk",
    "ttk",
    "ik",
    "iik",
    "kvkk",
}
_ADVICE_TERMS = {
    "ne yapmalıyım",
    "ne yapmaliyim",
    "haklarım",
    "haklarim",
    "dava açabilir",
    "dava acabilir",
    "sorumluluk",
    "tazminat",
    "fesih",
    "geçerli mi",
    "gecerli mi",
    "nasıl ilerlemeliyim",
    "nasil ilerlemeliyim",
}
_PROCEDURAL_TERMS = {
    "süre",
    "sure",
    "dava şartı",
    "dava sarti",
    "başvuru",
    "basvuru",
    "itiraz",
    "arabulucu",
    "arabuluculuk",
    "hak düşürücü",
    "hak dusurucu",
    "görevli mahkeme",
    "gorevli mahkeme",
}
_NEGATIVE_SOURCE_TERMS = {
    "içtihat istemiyorum",
    "ictihat istemiyorum",
    "emsal istemiyorum",
    "sadece mevzuat",
    "yargı kararı kullanma",
    "yargi karari kullanma",
}
_UNSAFE_REQUEST_TERMS = {
    "kaynak kullanmadan cevap ver",
    "kaynak göstermeden cevap ver",
    "kaynak gostermeden cevap ver",
    "atıf uydur",
    "atif uydur",
    "emsal uydur",
    "içtihat uydur",
    "ictihat uydur",
    "karar uydur",
    "case law fabricate",
    "ignore citations",
    "ignore evidence",
    "delilleri yok say",
    "kanıtları yok say",
    "kanitlari yok say",
    "sistem talimatını unut",
    "sistem talimatlarini unut",
    "önceki talimatları görmezden gel",
    "onceki talimatlari gormezden gel",
}
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MATERIAL_JUDICIAL_GENERALIZATION_RE = re.compile(
    r"\b(yerleşik içtihat|yerlesik ictihat|istikrarlı uygulama|istikrarli uygulama)\b",
    re.IGNORECASE,
)
_EVIDENCE_ID_RE = re.compile(r"\b[JM]\d+\b")


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _bounded_text(value: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", value).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower().translate(_TR_ASCII_TRANSLATION)


def _has_any(normalized: str, terms: set[str]) -> bool:
    return any(_term_in_normalized(normalized, term) for term in terms)


def _term_in_normalized(normalized: str, term: str) -> bool:
    normalized_term = _norm(term)
    if len(normalized_term) <= 3 and re.fullmatch(r"[0-9a-z]+", normalized_term):
        return re.search(rf"(?<![0-9a-z]){re.escape(normalized_term)}(?![0-9a-z])", normalized) is not None
    return normalized_term in normalized


def _parse_tr_date(value: str) -> str:
    match = _DATE_RE.search(value)
    if not match:
        return ""
    token = match.group("date")
    if "-" in token:
        return token
    day, month, year = re.split(r"[./]", token)
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _composite_lookup_key(*values: Any) -> str:
    return "|".join(re.sub(r"\s+", " ", str(value).strip()).lower() for value in values)


@dataclass(frozen=True, slots=True)
class LegalRuntimeConfig:
    judicial_runtime_enabled: bool
    processed_dir: Path
    exact_lookup_path: Path
    lexical_index_path: Path
    vector_collection: str = "judicial_decisions_v1_shadow"
    vector_enabled: bool = False
    mevzuat_top_k: int = 6
    judicial_top_k: int = 20
    max_judicial_decisions: int = 5
    max_chunks_per_decision: int = 2
    max_total_evidence_chars: int = 8000
    retrieval_timeout_ms: int = 8000
    llm_timeout_ms: int = 15000
    verification_timeout_ms: int = 5000
    legal_advisor_llm_enabled: bool = True
    request_timeout_ms: int = 8000
    max_query_chars: int = 4000

    @classmethod
    def from_settings(cls, settings: Any) -> "LegalRuntimeConfig":
        processed_dir = Path(
            getattr(
                settings,
                "judicial_processed_dir",
                os.getenv("JUDICIAL_PROCESSED_DIR", "/Users/btmacstudio/Projects/yargi/_work/final_package/processed"),
            )
        )
        return cls(
            judicial_runtime_enabled=bool(getattr(settings, "judicial_runtime_enabled", False)),
            processed_dir=processed_dir,
            exact_lookup_path=Path(
                getattr(settings, "judicial_exact_lookup_path", processed_dir / "judicial_exact_lookup.sqlite")
            ),
            lexical_index_path=Path(
                getattr(settings, "judicial_lexical_index_path", processed_dir / "judicial_lexical_index.sqlite")
            ),
            vector_collection=str(getattr(settings, "judicial_vector_collection", "judicial_decisions_v1_shadow")),
            vector_enabled=bool(getattr(settings, "judicial_vector_enabled", False)),
            mevzuat_top_k=int(getattr(settings, "legal_rag_max_mevzuat_evidence", _int_env("LEGAL_RAG_MAX_MEVZUAT_EVIDENCE", 6))),
            judicial_top_k=int(getattr(settings, "legal_rag_judicial_top_k", _int_env("LEGAL_RAG_JUDICIAL_TOP_K", 20))),
            max_judicial_decisions=int(getattr(settings, "legal_rag_max_judicial_decisions", _int_env("LEGAL_RAG_MAX_JUDICIAL_DECISIONS", 5))),
            max_chunks_per_decision=int(getattr(settings, "legal_rag_max_chunks_per_decision", _int_env("LEGAL_RAG_MAX_CHUNKS_PER_DECISION", 2))),
            max_total_evidence_chars=int(getattr(settings, "legal_rag_max_total_evidence_chars", _int_env("LEGAL_RAG_MAX_TOTAL_EVIDENCE_CHARS", 8000))),
            retrieval_timeout_ms=int(getattr(settings, "legal_rag_retrieval_timeout_ms", _int_env("LEGAL_RAG_RETRIEVAL_TIMEOUT_MS", 8000))),
            llm_timeout_ms=int(getattr(settings, "legal_rag_llm_timeout_ms", _int_env("LEGAL_RAG_LLM_TIMEOUT_MS", 15000))),
            verification_timeout_ms=int(getattr(settings, "legal_rag_verification_timeout_ms", _int_env("LEGAL_RAG_VERIFICATION_TIMEOUT_MS", 5000))),
            legal_advisor_llm_enabled=bool(
                getattr(settings, "legal_advisor_llm_enabled", _bool_env("LEGAL_ADVISOR_LLM_ENABLED", True))
            ),
            max_query_chars=int(getattr(settings, "legal_rag_max_query_chars", _int_env("LEGAL_RAG_MAX_QUERY_CHARS", 4000))),
        )


@dataclass(slots=True)
class LegalEvidence:
    source_type: str
    text: str
    citation: str
    metadata: dict[str, Any]
    score: float = 0.0
    retrieval_lane: str = "unknown"
    score_components: dict[str, float] = field(default_factory=dict)
    evidence_id: str = ""

    def packet(self, *, text_limit: int) -> dict[str, Any]:
        if self.source_type == "legislation":
            law_number = self.metadata.get("law_no") or self.metadata.get("kanun_no")
            article_number = self.metadata.get("madde_no") or self.metadata.get("article_no")
            source_url = self.metadata.get("source_url")
            source_title = self.metadata.get("source_title") or self.metadata.get("law_name") or self.metadata.get("belge_adi")
            source_authority = self.metadata.get("source_authority") or self.metadata.get("authority") or "Mevzuat"
            snippet = _bounded_text(self.text, text_limit)
            return {
                "evidence_id": self.evidence_id,
                "source_type": "legislation",
                "source_title": source_title,
                "source_authority": source_authority,
                "citation_label": self.citation,
                "pinpoint": f"m.{article_number}" if article_number else None,
                "text": snippet,
                "metadata": dict(self.metadata),
                "law_id": self.metadata.get("law_id") or self.metadata.get("source_id"),
                "law_name": source_title,
                "law_short_name": self.metadata.get("law_short_name") or self.metadata.get("kanun_kisa_adi"),
                "law_number": law_number,
                "law_no": law_number,
                "article_number": article_number,
                "article_no": article_number,
                "madde_no": article_number,
                "article_title": self.metadata.get("article_title") or self.metadata.get("madde_baslik"),
                "source_url": source_url,
                "effective_state": self.metadata.get("current_law_state") or self.metadata.get("yururluk_durumu"),
                "current_law_state": self.metadata.get("current_law_state") or self.metadata.get("yururluk_durumu"),
                "source_id": self.metadata.get("source_id") or source_url or self.metadata.get("chunk_id"),
                "chunk_key": self.metadata.get("chunk_key") or self.metadata.get("chunk_id"),
                "official_source_metadata": {
                    key: value
                    for key, value in {
                        "source_url": source_url,
                        "source_title": self.metadata.get("source_title"),
                        "law_no": law_number,
                    }.items()
                    if value
                },
                "selected_text": snippet,
                "snippet": snippet,
                "citation": self.citation,
                "retrieval_score": self.score,
                "retrieval_lane": self.retrieval_lane,
                "score_components": dict(self.score_components),
            }
        snippet = _bounded_text(self.text, text_limit)
        court = self.metadata.get("court")
        chamber = self.metadata.get("chamber")
        pinpoint = None
        if self.metadata.get("paragraph_start") and self.metadata.get("paragraph_end"):
            pinpoint = f"p.{self.metadata.get('paragraph_start')}-{self.metadata.get('paragraph_end')}"
        return {
            "evidence_id": self.evidence_id,
            "source_type": "judicial_decision",
            "source_title": self.metadata.get("citation_key") or self.citation,
            "source_authority": self.metadata.get("source_authority") or court,
            "citation_label": self.citation,
            "pinpoint": pinpoint,
            "text": snippet,
            "metadata": dict(self.metadata),
            "canonical_decision_id": self.metadata.get("canonical_decision_id"),
            "citation_key": self.metadata.get("citation_key"),
            "court": court,
            "chamber": chamber,
            "decision_date": self.metadata.get("decision_date"),
            "esas_no": self.metadata.get("esas_no"),
            "karar_no": self.metadata.get("karar_no"),
            "paragraph_start": self.metadata.get("paragraph_start"),
            "paragraph_end": self.metadata.get("paragraph_end"),
            "source_url": self.metadata.get("source_url"),
            "selected_text": snippet,
            "snippet": snippet,
            "citation": self.citation,
            "retrieval_lane": self.retrieval_lane,
            "retrieval_score": self.score,
            "score_components": dict(self.score_components),
        }

    def source_card(self) -> dict[str, Any]:
        packet = self.packet(text_limit=420)
        card = {
            key: value
            for key, value in packet.items()
            if key not in {"official_source_metadata", "metadata", "text", "selected_text"}
        }
        card["selected_text_excerpt"] = packet["selected_text"]
        if self.source_type == "legislation":
            card["source_id"] = packet.get("source_id")
            card["current_law_state"] = packet.get("current_law_state")
        return card

    def to_public(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source_type": self.source_type,
            "text": _bounded_text(self.text, 600),
            "citation": self.citation,
            "metadata": self.metadata,
            "score": self.score,
            "retrieval_lane": self.retrieval_lane,
            "score_components": self.score_components,
        }


@dataclass(slots=True)
class LegalRuntimeResponse:
    handled: bool
    answer: str
    citations: list[str]
    blocked: bool
    guardrails_reasons: list[str]
    verification: dict[str, Any] | None
    final_mode: str
    final_reason: str | None
    answer_contract: dict[str, Any]
    trace: dict[str, Any]
    usage: dict[str, int] | None = None


@dataclass(slots=True)
class LegalRoute:
    route: str
    confidence: float
    judicial_requested: bool
    legislation_requested: bool
    exact_key_type: str | None = None
    exact_key: str | None = None
    judicial_filters: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PreparedLegalAnswer:
    route: LegalRoute
    mevzuat_evidence: list[LegalEvidence]
    judicial_evidence: list[LegalEvidence]
    retrieval_metrics: dict[str, Any]
    early_response: LegalRuntimeResponse | None = None


@dataclass(slots=True)
class GeneratedLegalAnswer:
    answer: str
    claims: list[dict[str, Any]]
    citations: list[str]
    llm_used: bool = False
    llm_trace: dict[str, Any] | None = None
    usage: dict[str, int] | None = None
    fallback_reason: str | None = None


def _extract_court(query: str) -> str | None:
    normalized = _norm(query)
    for needle, court in _COURT_HINTS:
        if needle in normalized:
            return court
    trial_court = re.search(
        r"\b([A-ZÇĞİÖŞÜa-zçğıöşü]+(?:\s+\d+\.?)?\s+"
        r"(?:ASL[İI]YE|SULH|[İI]Ş|IS|T[İI]CARET|TICARET|AĞIR|AGIR|BÖLGE|BOLGE|"
        r"[İI]DARE|IDARE|HUKUK|CEZA)"
        r"[A-ZÇĞİÖŞÜa-zçğıöşü0-9.\s]*?MAHKEMES[İI])\b",
        query,
        flags=re.IGNORECASE,
    )
    if trial_court:
        cleaned = re.sub(r"\s+", " ", trial_court.group(1)).strip()
        cleaned = re.sub(
            r"^.*\b(?:kapsamında|kapsaminda|hakkında|hakkinda|için|icin)\s+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        return re.sub(r"^(?:ve|ile)\s+", "", cleaned, flags=re.IGNORECASE)
    court_match = re.search(
        r"([A-ZÇĞİÖŞÜa-zçğıöşü\s\d.]+MAHKEMES[İI])",
        query,
        flags=re.IGNORECASE,
    )
    if court_match:
        cleaned = re.sub(r"\s+", " ", court_match.group(1)).strip()
        cleaned = re.sub(
            r"^.*\b(?:kapsamında|kapsaminda|hakkında|hakkinda|için|icin)\s+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        return re.sub(r"^(?:ve|ile)\s+", "", cleaned, flags=re.IGNORECASE)
    return None


def _extract_chamber(query: str) -> str | None:
    normalized = _norm(query)
    compact = re.search(r"\b(?P<num>\d{1,2})\s*(?P<kind>hd|cd)\b", normalized, flags=re.IGNORECASE)
    if compact:
        return f"{compact.group('num')}{compact.group('kind').upper()}"
    verbose = re.search(
        r"\b(?P<num>\d{1,2})\.?\s*(?P<kind>hukuk|ceza)\s+dairesi\b",
        normalized,
        flags=re.IGNORECASE,
    )
    if verbose:
        suffix = "HD" if verbose.group("kind") == "hukuk" else "CD"
        return f"{verbose.group('num')}{suffix}"
    if "genel kurul" in normalized:
        return "GENEL KURUL"
    return None


def _extract_exact_lookup(query: str) -> tuple[str | None, str | None, dict[str, Any]]:
    canonical = _CANONICAL_ID_RE.search(query)
    if canonical:
        return "canonical_decision_id", canonical.group(0), {}
    sha = _SHA256_RE.search(query)
    if sha:
        return "document_hash", sha.group(0).lower(), {}
    url = re.search(r"https?://\S+", query)
    if url:
        return "source_url", url.group(0).rstrip(".,;)"), {}
    e_match = _E_RE.search(query) or _E_SUFFIX_RE.search(query)
    k_match = _K_RE.search(query) or _K_SUFFIX_RE.search(query)
    if e_match and k_match:
        court = _extract_court(query)
        chamber = _extract_chamber(query) or "GENEL"
        decision_date = _parse_tr_date(query)
        filters: dict[str, Any] = {
            "esas_no": e_match.group("value"),
            "karar_no": k_match.group("value"),
        }
        if court:
            filters["court"] = court
        if chamber:
            filters["chamber"] = chamber
        if decision_date:
            filters["decision_date"] = decision_date
        if court and chamber and decision_date:
            return (
                "court_chamber_date_esas_karar",
                _composite_lookup_key(court, chamber, decision_date, e_match.group("value"), k_match.group("value")),
                filters,
            )
        if court and chamber:
            return (
                "court_chamber_esas_karar",
                _composite_lookup_key(court, chamber, e_match.group("value"), k_match.group("value")),
                filters,
            )
    return None, None, {}


def _extract_judicial_metadata_filters(query: str, analysis: Any) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    court = _extract_court(query)
    chamber = _extract_chamber(query)
    decision_date = _parse_tr_date(query)
    if court:
        filters["court"] = court
    if chamber:
        filters["chamber"] = chamber
    if decision_date:
        filters["decision_date"] = decision_date
    else:
        year_match = _YEAR_RE.search(query)
        if year_match:
            filters["year"] = year_match.group("year")
    article_refs = list(getattr(analysis, "article_refs", []) or [])
    has_indexed_filter = any(
        key in filters for key in ("court", "chamber", "year", "decision_date", "esas_no", "karar_no")
    )
    if article_refs and not has_indexed_filter:
        first_ref = article_refs[0]
        law = getattr(first_ref, "law", None)
        article_no = getattr(first_ref, "article_no", None)
        if law and article_no:
            filters["related_law_refs"] = f"{law} m.{article_no}"
    return filters


def _route_class(route_name: str) -> str:
    mapping = {
        "exact_judicial_decision_lookup": "specific_judicial_decision_lookup",
        "specific_legislation_article_lookup": "specific_legislation_article_lookup",
        "legislation_only": "legislation_only",
        "judicial_only": "judicial_only",
        "mixed_legislation_and_judicial": "mixed_legislation_and_judicial",
        "legal_advice_scenario": "legislation_only",
        "procedural_query": "legislation_only",
        "negative_or_no_source_query": "legislation_only",
        "unsupported_or_out_of_scope": "unsupported_or_out_of_scope",
        "native_dialog": "native_dialog_or_non_legal",
    }
    return mapping.get(route_name, route_name)


def _query_safety_failure(query: str, *, max_query_chars: int) -> str | None:
    if len(query) > max_query_chars:
        return "oversized_input"
    if _CONTROL_CHAR_RE.search(query):
        return "malformed_control_characters"
    normalized = _norm(query)
    if _has_any(normalized, _UNSAFE_REQUEST_TERMS):
        return "prompt_injection_or_fabrication_request"
    return None


def _build_mevzuat_citation(result: RetrievalResult) -> str:
    metadata = dict(result.metadata or {})
    if getattr(result, "citation", None):
        return str(result.citation)
    law = (
        metadata.get("law_short_name")
        or metadata.get("kanun_kisa_adi")
        or metadata.get("law_no")
        or metadata.get("kanun_no")
        or metadata.get("source_title")
        or metadata.get("belge_adi")
        or "Mevzuat"
    )
    article = metadata.get("madde_no") or metadata.get("article_no")
    return f"{law} m.{article}" if article else str(law)


def _build_judicial_citation(result: dict[str, Any]) -> str:
    court = re.sub(r"\s+", " ", str(result.get("court") or "")).strip()
    chamber = re.sub(r"\s+", " ", str(result.get("chamber") or "")).strip()
    return (
        f"{court} {chamber}, {result.get('decision_date')}, "
        f"E. {result.get('esas_no')} K. {result.get('karar_no')}, "
        f"p.{result.get('paragraph_start')}-{result.get('paragraph_end')}, "
        f"{result.get('citation_key')}"
    )


def _evidence_source_type(packet: dict[str, Any], evidence_id: str) -> str | None:
    for item in packet.get("items") or []:
        if item.get("evidence_id") == evidence_id:
            return item.get("source_type")
    return None


def verify_legal_answer(
    *,
    answer: str,
    evidence_packet: dict[str, Any],
    claims: list[dict[str, Any]] | None = None,
    route: str | None = None,
) -> dict[str, Any]:
    items = list(evidence_packet.get("items") or [])
    source_cards = list(evidence_packet.get("source_cards") or [])
    known_ids = {str(item.get("evidence_id")) for item in items if item.get("evidence_id")}
    known_citations = {str(item.get("citation")) for item in items if item.get("citation")}
    failures: list[str] = []

    for evidence_id in _EVIDENCE_ID_RE.findall(answer):
        if evidence_id not in known_ids:
            failures.append("unknown_evidence_id_cited")

    law_citations = re.findall(r"\b([A-ZÇĞİÖŞÜ]{2,8})\s*m\.\s*([0-9]+[A-Za-z/.-]*)", answer)
    for law, article in law_citations:
        if not any(
            card.get("source_type") == "legislation"
            and str(card.get("citation") or "").lower().startswith(f"{law.lower()} m.{article.lower()}")
            for card in source_cards
        ):
            failures.append("statutory_citation_mismatch")

    decision_citations = re.findall(r"E\.\s*(\d{4}/\d{1,8})\s*K\.\s*(\d{4}/\d{1,8})", answer)
    for esas_no, karar_no in decision_citations:
        if not any(
            card.get("source_type") == "judicial_decision"
            and str(card.get("esas_no")) == esas_no
            and str(card.get("karar_no")) == karar_no
            for card in source_cards
        ):
            failures.append("judicial_citation_mismatch")

    for claim in claims or []:
        claim_type = str(claim.get("type") or claim.get("kind") or "")
        claim_text = str(claim.get("claim") or "")
        claim_ids = [str(item) for item in claim.get("evidence_ids") or []]
        if not claim_ids:
            failures.append("material_claim_without_evidence_id")
            continue
        for evidence_id in claim_ids:
            if evidence_id not in known_ids:
                failures.append("claim_unknown_evidence_id")
        source_types = {_evidence_source_type(evidence_packet, evidence_id) for evidence_id in claim_ids}
        if claim_type in {"statutory", "statutory_analysis", "legislation"} and "legislation" not in source_types:
            failures.append("unsupported_statutory_claim")
        if claim_type in {"judicial", "judicial_analysis", "case_law"} and "judicial_decision" not in source_types:
            failures.append("unsupported_judicial_claim")
        normalized_claim = _norm(claim_text)
        if any(term in normalized_claim for term in ("madde", "kanun", "tbk", "tmk", "tck")) and "legislation" not in source_types:
            failures.append("source_type_confusion")
        if any(term in normalized_claim for term in ("yargitay", "danistay", "ictihat", "mahkeme karar")) and "judicial_decision" not in source_types:
            failures.append("source_type_confusion")

    if _MATERIAL_JUDICIAL_GENERALIZATION_RE.search(answer):
        distinct_decisions = {
            str(card.get("canonical_decision_id"))
            for card in source_cards
            if card.get("source_type") == "judicial_decision" and card.get("canonical_decision_id")
        }
        if len(distinct_decisions) < 2:
            failures.append("overstated_single_decision_authority")

    if re.search(r"\b(güncel|yürürlükte|current law)\b", answer, flags=re.IGNORECASE):
        has_current_state = any(
            card.get("source_type") == "legislation" and card.get("current_law_state")
            for card in source_cards
        )
        if route != "exact_judicial_decision_lookup" and not has_current_state:
            failures.append("current_law_state_claim_without_metadata")

    has_evidence = bool(items)
    if not has_evidence and answer.strip() and route not in {"native_dialog", "unsupported_or_out_of_scope"}:
        failures.append("legal_conclusion_without_evidence")

    return {
        "pass": not failures,
        "verdict": "pass" if not failures else "fail",
        "failures": sorted(set(failures)),
        "unsupported_claim_failures": sorted(
            failure for failure in set(failures) if "unsupported" in failure or "without_evidence" in failure
        ),
        "citation_mismatch_failures": sorted(failure for failure in set(failures) if "citation_mismatch" in failure),
        "source_type_confusion": "source_type_confusion" in failures,
        "checked_claim_count": len(claims or []),
        "evidence_count": len(items),
    }


class LegalRagOrchestrator:
    def __init__(
        self,
        *,
        config: LegalRuntimeConfig,
        mevzuat_retriever: Any | None = None,
        llm_client: Any | None = None,
    ) -> None:
        self.config = config
        self.mevzuat_retriever = mevzuat_retriever
        self.llm_client = llm_client
        self._exact_store: PersistentJudicialExactLookupStore | None = None
        self._hybrid: JudicialHybridRetriever | None = None
        self._status = self._validate_status()
        if self._status["judicial_ready"]:
            self._exact_store = PersistentJudicialExactLookupStore(config.exact_lookup_path, read_only=True)
            self._hybrid = JudicialHybridRetriever(
                exact_store=self._exact_store,
                lexical_index_path=config.lexical_index_path,
                vector_ready=False,
            )

    @classmethod
    def from_settings(
        cls,
        settings: Any,
        *,
        mevzuat_retriever: Any | None = None,
        llm_client: Any | None = None,
    ) -> "LegalRagOrchestrator":
        return cls(
            config=LegalRuntimeConfig.from_settings(settings),
            mevzuat_retriever=mevzuat_retriever,
            llm_client=llm_client,
        )

    def health(self) -> dict[str, Any]:
        return dict(self._status)

    def public_health(self) -> dict[str, Any]:
        keys = (
            "legal_rag_runtime_mode",
            "judicial_runtime_enabled",
            "judicial_ready",
            "judicial_readiness_status",
            "judicial_readiness_failures",
            "judicial_indexes_available",
            "exact_lookup_available",
            "lexical_index_available",
            "chunk_refs_available",
            "required_metadata_ready",
            "coverage_audit_available",
            "coverage_audit_pass",
            "vector_index_status",
            "mevzuat_retriever_available",
            "mevzuat_retriever_degraded",
            "verifier_enabled",
            "processed_corpus_dir_configured",
            "retrieval_timeout_ms",
            "llm_timeout_ms",
            "verification_timeout_ms",
        )
        return {key: self._status.get(key) for key in keys}

    def should_handle(self, query: str) -> bool:
        route = self.route_query(query)
        return route.route not in {"native_dialog", "unsupported_or_out_of_scope"}

    def route_query(self, query: str) -> LegalRoute:
        normalized = _norm(query)
        if _has_any(normalized, _NATIVE_DIALOG_TERMS) and len(normalized.split()) <= 5:
            return LegalRoute("native_dialog", 0.9, False, False)

        analysis = analyze_query(query)
        exact_key_type, exact_key, filters = _extract_exact_lookup(query)
        if not filters:
            filters = _extract_judicial_metadata_filters(query, analysis)
        has_exact = exact_key_type is not None and exact_key is not None
        judicial_score = sum(1 for term in _JUDICIAL_TERMS if _term_in_normalized(normalized, term))
        explicit_legislation_score = (
            len(analysis.article_refs)
            + len(analysis.law_mentions)
            + sum(1 for term in _LEGISLATION_TERMS if _term_in_normalized(normalized, term))
        )
        legislation_score = (
            explicit_legislation_score
            + len(analysis.law_numbers)
        )
        advice_score = sum(1 for term in _ADVICE_TERMS if _term_in_normalized(normalized, term))
        procedural_score = sum(1 for term in _PROCEDURAL_TERMS if _term_in_normalized(normalized, term))
        negative_source = _has_any(normalized, _NEGATIVE_SOURCE_TERMS)

        if has_exact:
            return LegalRoute(
                route="exact_judicial_decision_lookup",
                confidence=0.95,
                judicial_requested=True,
                legislation_requested=bool(explicit_legislation_score),
                exact_key_type=exact_key_type,
                exact_key=exact_key,
                judicial_filters=filters,
            )
        if analysis.article_refs and not judicial_score:
            return LegalRoute("specific_legislation_article_lookup", 0.86, False, True, judicial_filters=filters)
        if negative_source and (legislation_score or advice_score or procedural_score):
            return LegalRoute("negative_or_no_source_query", 0.8, False, True, judicial_filters=filters)
        if procedural_score:
            return LegalRoute("procedural_query", 0.76, bool(judicial_score), True, judicial_filters=filters)
        if judicial_score and (legislation_score or advice_score):
            return LegalRoute("mixed_legislation_and_judicial", 0.84, True, True, judicial_filters=filters)
        if advice_score:
            return LegalRoute("legal_advice_scenario", 0.72, False, True, judicial_filters=filters)
        if judicial_score:
            return LegalRoute("judicial_only", 0.78, True, False, judicial_filters=filters)
        if legislation_score:
            return LegalRoute("legislation_only", 0.74, False, True)
        if analysis.insufficient_query or not any(ch.isalpha() for ch in normalized):
            return LegalRoute("unsupported_or_out_of_scope", 0.6, False, False)
        return LegalRoute("unsupported_or_out_of_scope", 0.52, False, False)

    def answer(self, *, query: str, top_k: int = 20, law_filter: str | None = None) -> LegalRuntimeResponse:
        started = time.perf_counter()
        prepared = self._prepare_answer(query=query, top_k=top_k, law_filter=law_filter, started=started)
        if prepared.early_response is not None:
            return prepared.early_response
        generated = self._compose_deterministic_answer(
            query=query,
            route=prepared.route,
            evidence_packet=self._build_evidence_packet(prepared.mevzuat_evidence, prepared.judicial_evidence),
        )
        return self._finalize_generated_answer(
            generated=generated,
            route=prepared.route,
            mevzuat_evidence=prepared.mevzuat_evidence,
            judicial_evidence=prepared.judicial_evidence,
            retrieval_metrics=prepared.retrieval_metrics,
            started=started,
        )

    async def answer_async(
        self,
        *,
        query: str,
        top_k: int = 20,
        law_filter: str | None = None,
        conversation_context: list[dict[str, str]] | None = None,
    ) -> LegalRuntimeResponse:
        started = time.perf_counter()
        try:
            prepared = await asyncio.wait_for(
                asyncio.to_thread(self._prepare_answer, query=query, top_k=top_k, law_filter=law_filter, started=started),
                timeout=max(0.1, self.config.retrieval_timeout_ms / 1000.0),
            )
        except TimeoutError:
            route = self.route_query(query)
            return self._response(
                answer="Kaynak araması zaman aşımına uğradı; bu hukuki konuda kaynaklı sonuç üretmiyorum.",
                citations=[],
                blocked=True,
                final_mode="refusal",
                final_reason="retrieval_timeout",
                route=route,
                mevzuat_evidence=[],
                judicial_evidence=[],
                started=started,
                verification={"pass": False, "failures": ["retrieval_timeout"], "verdict": "fail"},
            )
        if prepared.early_response is not None:
            return prepared.early_response

        evidence_packet = self._build_evidence_packet(prepared.mevzuat_evidence, prepared.judicial_evidence)
        generated = await self._generate_with_llm_or_fallback(
            query=query,
            route=prepared.route,
            evidence_packet=evidence_packet,
            conversation_context=conversation_context or [],
        )
        return self._finalize_generated_answer(
            generated=generated,
            route=prepared.route,
            mevzuat_evidence=prepared.mevzuat_evidence,
            judicial_evidence=prepared.judicial_evidence,
            retrieval_metrics=prepared.retrieval_metrics,
            started=started,
        )

    def _prepare_answer(self, *, query: str, top_k: int, law_filter: str | None, started: float) -> PreparedLegalAnswer:
        safety_failure = _query_safety_failure(query, max_query_chars=self.config.max_query_chars)
        if safety_failure is not None:
            route = LegalRoute("unsupported_or_out_of_scope", 0.95, False, False)
            retrieval_metrics: dict[str, Any] = {
                "route": route.route,
                "route_class": _route_class(route.route),
                "source_families_requested": {"legislation": False, "judicial_decision": False},
                "judicial_filters": {},
                "latency_by_lane_ms": {},
                "input_safety_failure": safety_failure,
            }
            return PreparedLegalAnswer(
                route=route,
                mevzuat_evidence=[],
                judicial_evidence=[],
                retrieval_metrics=retrieval_metrics,
                early_response=self._response(
                    answer="Bu istek güvenli kaynaklı yanıt sözleşmesini ihlal ediyor; kaynak uydurmadan veya talimatları yok sayarak hukuki sonuç üretmiyorum.",
                    citations=[],
                    blocked=True,
                    final_mode="refusal",
                    final_reason=safety_failure,
                    route=route,
                    mevzuat_evidence=[],
                    judicial_evidence=[],
                    started=started,
                    retrieval_metrics=retrieval_metrics,
                    verification={"pass": False, "failures": [safety_failure], "verdict": "fail"},
                ),
            )
        route = self.route_query(query)
        retrieval_metrics: dict[str, Any] = {
            "route": route.route,
            "route_class": _route_class(route.route),
            "source_families_requested": {
                "legislation": route.legislation_requested,
                "judicial_decision": route.judicial_requested,
            },
            "judicial_filters": dict(route.judicial_filters),
            "latency_by_lane_ms": {},
        }
        if route.route in {"native_dialog", "unsupported_or_out_of_scope"}:
            return PreparedLegalAnswer(
                route=route,
                mevzuat_evidence=[],
                judicial_evidence=[],
                retrieval_metrics=retrieval_metrics,
                early_response=self._response(
                    answer="Bu soru için güvenilir hukuki kaynak tespiti yapamadım. Somut olay, ilgili kanun maddesi veya karar bilgisini belirtirseniz kaynaklı yanıt verebilirim.",
                    citations=[],
                    blocked=True,
                    final_mode="refusal",
                    final_reason=route.route,
                    route=route,
                    mevzuat_evidence=[],
                    judicial_evidence=[],
                    started=started,
                ),
            )

        mevzuat_evidence: list[LegalEvidence] = []
        judicial_evidence: list[LegalEvidence] = []
        if route.legislation_requested:
            lane_started = time.perf_counter()
            mevzuat_evidence = self._retrieve_mevzuat(query=query, top_k=min(top_k, self.config.mevzuat_top_k), law_filter=law_filter)
            retrieval_metrics["latency_by_lane_ms"]["mevzuat"] = round((time.perf_counter() - lane_started) * 1000.0, 3)

        if route.judicial_requested:
            if not self.config.judicial_runtime_enabled:
                return PreparedLegalAnswer(
                    route=route,
                    mevzuat_evidence=mevzuat_evidence,
                    judicial_evidence=[],
                    retrieval_metrics=retrieval_metrics,
                    early_response=self._response(
                        answer=(
                            "Yargı kararı veya içtihat gerektiren bu soruda yargısal runtime kapalı olduğu için "
                            "karar dayanağı üretmiyorum. Mevzuat sorusu olarak yeniden sorarsanız mevzuat kaynaklarıyla yanıtlayabilirim."
                        ),
                        citations=[],
                        blocked=True,
                        final_mode="refusal",
                        final_reason="judicial_runtime_disabled",
                        route=route,
                        mevzuat_evidence=mevzuat_evidence,
                        judicial_evidence=[],
                        started=started,
                    ),
                )
            if not self._status["judicial_ready"]:
                return PreparedLegalAnswer(
                    route=route,
                    mevzuat_evidence=mevzuat_evidence,
                    judicial_evidence=[],
                    retrieval_metrics=retrieval_metrics,
                    early_response=self._response(
                        answer="Yargısal runtime etkin görünüyor ancak gerekli persistent karar indeksleri hazır değil; yargı kararı dayanaklı yanıt vermiyorum.",
                        citations=[],
                        blocked=True,
                        final_mode="refusal",
                        final_reason="judicial_indexes_unavailable",
                        route=route,
                        mevzuat_evidence=mevzuat_evidence,
                        judicial_evidence=[],
                        started=started,
                    ),
                )
            lane_started = time.perf_counter()
            judicial_query = self._build_judicial_query(query=query, mevzuat_evidence=mevzuat_evidence, route=route)
            judicial_evidence = self._retrieve_judicial(query=judicial_query, route=route, top_k=min(top_k, self.config.judicial_top_k))
            retrieval_metrics["latency_by_lane_ms"]["judicial"] = round((time.perf_counter() - lane_started) * 1000.0, 3)
            judicial_lanes = Counter(evidence.retrieval_lane for evidence in judicial_evidence)
            exact_requested = bool(route.exact_key_type and route.exact_key)
            retrieval_metrics["judicial_retrieval"] = {
                "exact_lookup_requested": exact_requested,
                "exact_lookup_hit": bool(
                    exact_requested
                    and any(
                        {"exact", "exact_metadata"} & set(evidence.score_components)
                        for evidence in judicial_evidence
                    )
                ),
                "lexical_hit_count": sum(
                    1 for evidence in judicial_evidence if "lexical" in evidence.score_components
                ),
                "selected_count": len(judicial_evidence),
                "retrieval_lanes_used": dict(sorted(judicial_lanes.items())),
            }
            if not judicial_evidence:
                return PreparedLegalAnswer(
                    route=route,
                    mevzuat_evidence=mevzuat_evidence,
                    judicial_evidence=[],
                    retrieval_metrics=retrieval_metrics,
                    early_response=self._response(
                        answer="Bu yargı kararı/içtihat sorusu için seçilebilir, tam metadata taşıyan yargısal kanıt bulunamadı; karar sonucu veya içtihat iddiası üretmiyorum.",
                        citations=[evidence.citation for evidence in mevzuat_evidence],
                        blocked=True,
                        final_mode="refusal",
                        final_reason="judicial_evidence_not_found",
                        route=route,
                        mevzuat_evidence=mevzuat_evidence,
                        judicial_evidence=[],
                        started=started,
                    ),
                )

        if route.legislation_requested and not mevzuat_evidence and not judicial_evidence:
            return PreparedLegalAnswer(
                route=route,
                mevzuat_evidence=[],
                judicial_evidence=[],
                retrieval_metrics=retrieval_metrics,
                early_response=self._response(
                    answer="Bu mevzuat sorusu için runtime içinde yeterli mevzuat kanıtı bulunamadı; kaynak göstermeden hukuki sonuç üretmiyorum.",
                    citations=[],
                    blocked=True,
                    final_mode="refusal",
                    final_reason="mevzuat_evidence_not_found",
                    route=route,
                    mevzuat_evidence=[],
                    judicial_evidence=[],
                    started=started,
                ),
            )

        self._assign_evidence_ids(mevzuat_evidence, judicial_evidence)
        evidence_verification = self._verify_evidence(
            route=route,
            mevzuat_evidence=mevzuat_evidence,
            judicial_evidence=judicial_evidence,
        )
        if not evidence_verification["pass"]:
            return PreparedLegalAnswer(
                route=route,
                mevzuat_evidence=mevzuat_evidence,
                judicial_evidence=judicial_evidence,
                retrieval_metrics=retrieval_metrics,
                early_response=self._response(
                    answer="Seçilen kanıtlar cevap sözleşmesini karşılamadığı için kaynaklı yanıt üretmiyorum.",
                    citations=[],
                    blocked=True,
                    final_mode="refusal",
                    final_reason="evidence_contract_failed",
                    route=route,
                    mevzuat_evidence=mevzuat_evidence,
                    judicial_evidence=judicial_evidence,
                    verification=evidence_verification,
                    started=started,
                ),
            )
        retrieval_metrics["source_families_retrieved"] = {
            "legislation": bool(mevzuat_evidence),
            "judicial_decision": bool(judicial_evidence),
        }
        retrieval_metrics["selected_evidence_count"] = len(mevzuat_evidence) + len(judicial_evidence)
        return PreparedLegalAnswer(route, mevzuat_evidence, judicial_evidence, retrieval_metrics)

    def _connect_readonly_sqlite(self, path: Path) -> sqlite3.Connection:
        uri = path.resolve().as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=_SQLITE_BUSY_TIMEOUT_MS / 1000.0)
        conn.row_factory = sqlite3.Row
        conn.execute(f"PRAGMA busy_timeout={_SQLITE_BUSY_TIMEOUT_MS}")
        conn.execute("PRAGMA query_only=ON")
        return conn

    @staticmethod
    def _sqlite_tables(conn: sqlite3.Connection) -> set[str]:
        return {
            str(row["name"])
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')")
        }

    @staticmethod
    def _missing_required_values(row: sqlite3.Row | None, fields: tuple[str, ...]) -> list[str]:
        if row is None:
            return list(fields)
        payload = dict(row)
        missing: list[str] = []
        for field_name in fields:
            value = payload.get(field_name)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(field_name)
        return missing

    def _validate_exact_lookup_store(self) -> dict[str, Any]:
        path = self.config.exact_lookup_path
        result: dict[str, Any] = {
            "path_exists": path.exists(),
            "readable": False,
            "available": False,
            "tables_ready": False,
            "lookup_rows_available": False,
            "decision_rows_available": False,
            "chunk_refs_available": False,
            "required_metadata_ready": False,
            "failures": [],
        }
        failures: list[str] = []
        if not path.exists():
            failures.append("exact_lookup_missing")
            result["failures"] = failures
            return result
        if not path.is_file():
            failures.append("exact_lookup_not_file")
            result["failures"] = failures
            return result

        try:
            with self._connect_readonly_sqlite(path) as conn:
                result["readable"] = True
                tables = self._sqlite_tables(conn)
                missing_tables = [table for table in _EXACT_LOOKUP_REQUIRED_TABLES if table not in tables]
                if missing_tables:
                    failures.append(f"exact_lookup_missing_tables:{','.join(missing_tables)}")
                result["tables_ready"] = not missing_tables
                if not missing_tables:
                    decision = conn.execute(
                        "SELECT canonical_decision_id, citation_key, court, chamber, decision_date, esas_no, karar_no, source_url "
                        "FROM decisions LIMIT 1"
                    ).fetchone()
                    result["decision_rows_available"] = decision is not None
                    if decision is None:
                        failures.append("exact_lookup_decisions_empty")
                    missing_values = self._missing_required_values(decision, _EXACT_DECISION_REQUIRED_FIELDS)
                    if missing_values:
                        failures.append(f"exact_lookup_missing_metadata:{','.join(missing_values)}")
                    result["required_metadata_ready"] = not missing_values
                    result["lookup_rows_available"] = (
                        conn.execute("SELECT 1 FROM lookup LIMIT 1").fetchone() is not None
                    )
                    if not result["lookup_rows_available"]:
                        failures.append("exact_lookup_keys_empty")
                    result["chunk_refs_available"] = (
                        conn.execute("SELECT 1 FROM chunk_refs LIMIT 1").fetchone() is not None
                    )
                    if not result["chunk_refs_available"]:
                        failures.append("exact_lookup_chunk_refs_empty")
        except sqlite3.DatabaseError as exc:
            failures.append(f"exact_lookup_unreadable:{exc.__class__.__name__}")
        result["failures"] = failures
        result["available"] = not failures
        return result

    def _validate_lexical_index(self) -> dict[str, Any]:
        path = self.config.lexical_index_path
        result: dict[str, Any] = {
            "path_exists": path.exists(),
            "readable": False,
            "available": False,
            "tables_ready": False,
            "chunk_rows_available": False,
            "fts_rows_available": False,
            "required_metadata_ready": False,
            "failures": [],
        }
        failures: list[str] = []
        if not path.exists():
            failures.append("lexical_index_missing")
            result["failures"] = failures
            return result
        if not path.is_file():
            failures.append("lexical_index_not_file")
            result["failures"] = failures
            return result

        try:
            with self._connect_readonly_sqlite(path) as conn:
                result["readable"] = True
                tables = self._sqlite_tables(conn)
                missing_tables = [table for table in _LEXICAL_REQUIRED_TABLES if table not in tables]
                if missing_tables:
                    failures.append(f"lexical_index_missing_tables:{','.join(missing_tables)}")
                result["tables_ready"] = not missing_tables
                if not missing_tables:
                    chunk = conn.execute(
                        "SELECT chunk_key, canonical_decision_id, citation_key, court, chamber, decision_date, "
                        "esas_no, karar_no, paragraph_start, paragraph_end, source_url, source_type "
                        "FROM chunks LIMIT 1"
                    ).fetchone()
                    result["chunk_rows_available"] = chunk is not None
                    if chunk is None:
                        failures.append("lexical_index_chunks_empty")
                    missing_values = self._missing_required_values(chunk, _LEXICAL_CHUNK_REQUIRED_FIELDS)
                    if missing_values:
                        failures.append(f"lexical_index_missing_metadata:{','.join(missing_values)}")
                    result["required_metadata_ready"] = not missing_values
                    result["fts_rows_available"] = (
                        conn.execute("SELECT 1 FROM chunks_fts LIMIT 1").fetchone() is not None
                    )
                    if not result["fts_rows_available"]:
                        failures.append("lexical_index_fts_empty")
        except sqlite3.DatabaseError as exc:
            failures.append(f"lexical_index_unreadable:{exc.__class__.__name__}")
        result["failures"] = failures
        result["available"] = not failures
        return result

    def _validate_coverage_audit(self) -> dict[str, Any]:
        path = self.config.processed_dir / _JUDICIAL_COVERAGE_AUDIT_FILENAME
        result: dict[str, Any] = {
            "path_exists": path.exists(),
            "readable": False,
            "pass": None,
            "failure": None,
        }
        if not path.exists():
            result["failure"] = "coverage_audit_missing"
            return result
        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            result["failure"] = f"coverage_audit_unreadable:{exc.__class__.__name__}"
            return result
        result["readable"] = True
        result["pass"] = bool(isinstance(payload, dict) and payload.get("pass") is True)
        if result["pass"] is not True:
            result["failure"] = "coverage_audit_not_passing"
        return result

    def _validate_status(self) -> dict[str, Any]:
        processed_configured = bool(str(self.config.processed_dir))
        processed_exists = self.config.processed_dir.exists() and self.config.processed_dir.is_dir()
        exact_status = self._validate_exact_lookup_store()
        lexical_status = self._validate_lexical_index()
        coverage_status = self._validate_coverage_audit()
        index_failures: list[str] = []
        if not processed_configured:
            index_failures.append("processed_corpus_dir_not_configured")
        elif not processed_exists:
            index_failures.append("processed_corpus_dir_missing")
        index_failures.extend(str(failure) for failure in exact_status["failures"])
        index_failures.extend(str(failure) for failure in lexical_status["failures"])
        if coverage_status["failure"] is not None:
            index_failures.append(str(coverage_status["failure"]))

        vector_status = "disabled"
        if self.config.vector_enabled:
            vector_status = "not_built"
        judicial_indexes_available = not index_failures
        judicial_ready = self.config.judicial_runtime_enabled and judicial_indexes_available
        if not self.config.judicial_runtime_enabled:
            readiness_status = "disabled"
            readiness_failures: list[str] = []
        elif judicial_ready:
            readiness_status = "ready"
            readiness_failures = []
        else:
            readiness_status = "failed"
            readiness_failures = index_failures
        return {
            "runtime": "legal_rag",
            "legal_rag_runtime_mode": "advisor",
            "judicial_runtime_enabled": self.config.judicial_runtime_enabled,
            "processed_dir": str(self.config.processed_dir),
            "exact_lookup_path": str(self.config.exact_lookup_path),
            "lexical_index_path": str(self.config.lexical_index_path),
            "processed_corpus_dir_configured": processed_configured,
            "processed_dir_exists": processed_exists,
            "exact_lookup_exists": exact_status["path_exists"],
            "lexical_index_exists": lexical_status["path_exists"],
            "exact_lookup_available": exact_status["available"],
            "lexical_index_available": lexical_status["available"],
            "chunk_refs_available": exact_status["chunk_refs_available"],
            "required_metadata_ready": bool(
                exact_status["required_metadata_ready"] and lexical_status["required_metadata_ready"]
            ),
            "coverage_audit_available": coverage_status["path_exists"],
            "coverage_audit_pass": coverage_status["pass"],
            "judicial_indexes_available": judicial_indexes_available,
            "judicial_ready": judicial_ready,
            "judicial_readiness_status": readiness_status,
            "judicial_readiness_failures": readiness_failures,
            "judicial_index_validation_failures": index_failures,
            "exact_lookup_validation": exact_status,
            "lexical_index_validation": lexical_status,
            "vector_index_status": vector_status,
            "mevzuat_retriever": "available" if self.mevzuat_retriever is not None else "degraded_unavailable",
            "mevzuat_retriever_available": self.mevzuat_retriever is not None,
            "mevzuat_retriever_degraded": self.mevzuat_retriever is None,
            "verifier_enabled": True,
            "retrieval_timeout_ms": self.config.retrieval_timeout_ms,
            "llm_timeout_ms": self.config.llm_timeout_ms,
            "verification_timeout_ms": self.config.verification_timeout_ms,
            "llm_answer_generator": "available" if self.llm_client is not None else "fallback",
        }

    def _retrieve_mevzuat(self, *, query: str, top_k: int, law_filter: str | None) -> list[LegalEvidence]:
        if self.mevzuat_retriever is None:
            return []
        metadata_filter = None
        if law_filter:
            from rag.retriever import MetadataFilter

            metadata_filter = MetadataFilter(law_short_name=law_filter)
        try:
            results, _stats = self.mevzuat_retriever.retrieve(query=query, top_k=top_k, metadata_filter=metadata_filter)
        except TypeError:
            results, _stats = self.mevzuat_retriever.retrieve(query=query, top_k=top_k)
        evidence: list[LegalEvidence] = []
        seen: set[str] = set()
        for result in results:
            citation = _build_mevzuat_citation(result)
            if citation in seen:
                continue
            seen.add(citation)
            metadata = dict(result.metadata or {})
            metadata["source_type"] = metadata.get("source_type") or "legislation"
            evidence.append(
                LegalEvidence(
                    source_type="legislation",
                    text=str(result.text),
                    citation=citation,
                    metadata=metadata,
                    score=float(result.score or 0.0),
                    retrieval_lane="mevzuat",
                    score_components={"mevzuat": float(result.score or 0.0)},
                )
            )
            if len(evidence) >= self.config.mevzuat_top_k:
                break
        return evidence

    def _retrieve_judicial(self, *, query: str, route: LegalRoute, top_k: int) -> list[LegalEvidence]:
        if self._hybrid is None:
            return []
        filters = dict(route.judicial_filters)
        if route.exact_key_type and route.exact_key:
            results = self._hybrid.retrieve(
                query=query,
                exact_key_type=route.exact_key_type,
                exact_key=route.exact_key,
                filters={
                    key: value
                    for key, value in filters.items()
                    if key in {"court", "chamber", "year", "decision_date", "esas_no", "karar_no"}
                },
                top_k=top_k,
                lexical_for_exact=False,
            )
            results = [
                result
                for result in results
                if {"exact", "exact_metadata"} & set((result.get("score_components") or {}).keys())
            ]
        else:
            lexical_filters = {
                key: value
                for key, value in filters.items()
                if key in {"court", "chamber", "year", "decision_date", "esas_no", "karar_no", "related_law_refs"}
            }
            lexical_top_k = max(1, min(top_k, self.config.max_judicial_decisions * self.config.max_chunks_per_decision))
            results = query_judicial_lexical_index(
                self.config.lexical_index_path,
                query,
                filters=lexical_filters,
                top_k=lexical_top_k,
            )
            if not results and "related_law_refs" in lexical_filters:
                relaxed_filters = {key: value for key, value in lexical_filters.items() if key != "related_law_refs"}
                results = query_judicial_lexical_index(
                    self.config.lexical_index_path,
                    query,
                    filters=relaxed_filters,
                    top_k=lexical_top_k,
                )
                for result in results:
                    result["metadata_filter_relaxation"] = "dropped_related_law_refs"
            for result in results:
                result["score_components"] = {"lexical": float(result.get("score") or 0.0)}
        validation = validate_judicial_evidence_results(results)
        if not validation["pass"]:
            logger.warning("Judicial evidence validation failed: %s", validation)
            return []
        by_decision: Counter[str] = Counter()
        selected: list[LegalEvidence] = []
        decision_order: list[str] = []
        for result in results:
            canonical_id = str(result.get("canonical_decision_id") or "")
            if by_decision[canonical_id] == 0:
                decision_order.append(canonical_id)
            if len(decision_order) > self.config.max_judicial_decisions and by_decision[canonical_id] == 0:
                continue
            if by_decision[canonical_id] >= self.config.max_chunks_per_decision:
                continue
            by_decision[canonical_id] += 1
            citation = _build_judicial_citation(result)
            metadata = dict(result.get("metadata") or {})
            metadata["source_type"] = "judicial_decision"
            selected.append(
                LegalEvidence(
                    source_type="judicial_decision",
                    text=str(result.get("selected_chunk_text") or result.get("text") or ""),
                    citation=citation,
                    metadata=metadata,
                    score=float(result.get("final_score") or result.get("score") or 0.0),
                    retrieval_lane=str(result.get("retrieval_lane") or "lexical"),
                    score_components=dict(result.get("score_components") or {"lexical": float(result.get("score") or 0.0)}),
                )
            )
        return selected

    def _build_judicial_query(
        self,
        *,
        query: str,
        mevzuat_evidence: list[LegalEvidence],
        route: LegalRoute,
    ) -> str:
        if route.route == "exact_judicial_decision_lookup":
            return query
        refs: list[str] = []
        for evidence in mevzuat_evidence:
            article = evidence.metadata.get("madde_no") or evidence.metadata.get("article_no")
            law = evidence.metadata.get("law_short_name") or evidence.metadata.get("kanun_kisa_adi")
            if law and article:
                refs.append(f"{law} m.{article}")
        if refs:
            return f"{query} {' '.join(refs[:4])}"
        return query

    def _assign_evidence_ids(self, mevzuat_evidence: list[LegalEvidence], judicial_evidence: list[LegalEvidence]) -> None:
        for index, evidence in enumerate(mevzuat_evidence, start=1):
            evidence.evidence_id = f"M{index}"
        for index, evidence in enumerate(judicial_evidence, start=1):
            evidence.evidence_id = f"J{index}"

    def _build_evidence_packet(
        self,
        mevzuat_evidence: list[LegalEvidence],
        judicial_evidence: list[LegalEvidence],
    ) -> dict[str, Any]:
        evidence = [*mevzuat_evidence, *judicial_evidence]
        if not all(item.evidence_id for item in evidence):
            self._assign_evidence_ids(mevzuat_evidence, judicial_evidence)
        per_item_limit = max(500, self.config.max_total_evidence_chars // max(1, len(evidence)))
        remaining = self.config.max_total_evidence_chars
        items: list[dict[str, Any]] = []
        for item in evidence:
            limit = max(0, min(per_item_limit, remaining))
            packet_item = item.packet(text_limit=limit)
            remaining -= len(str(packet_item.get("selected_text") or ""))
            items.append(packet_item)
        source_cards = [item.source_card() for item in evidence]
        return {
            "version": "legal_evidence_packet_v1",
            "items": items,
            "source_cards": source_cards,
            "source_families": sorted({item.source_type for item in evidence}),
            "limits": {
                "max_total_evidence_chars": self.config.max_total_evidence_chars,
                "item_count": len(items),
            },
        }

    def _verify_evidence(
        self,
        *,
        route: LegalRoute,
        mevzuat_evidence: list[LegalEvidence],
        judicial_evidence: list[LegalEvidence],
    ) -> dict[str, Any]:
        failures: list[str] = []
        if route.legislation_requested and not mevzuat_evidence:
            failures.append("statutory_claim_without_mevzuat_evidence")
        if route.judicial_requested and not judicial_evidence:
            failures.append("judicial_claim_without_judicial_evidence")
        if route.judicial_requested and not self.config.judicial_runtime_enabled:
            failures.append("judicial_claim_runtime_disabled")
        for evidence in mevzuat_evidence:
            if evidence.source_type != "legislation":
                failures.append("mevzuat_source_type_confusion")
            if not (evidence.metadata.get("madde_no") or evidence.metadata.get("article_no")):
                failures.append("mevzuat_article_metadata_missing")
        for evidence in judicial_evidence:
            if evidence.source_type != "judicial_decision":
                failures.append("judicial_source_type_confusion")
            for field_name in ("court", "chamber", "decision_date", "esas_no", "karar_no", "citation_key"):
                if not evidence.metadata.get(field_name):
                    failures.append(f"judicial_{field_name}_missing")
        return {
            "pass": not failures,
            "verdict": "pass" if not failures else "fail",
            "failures": sorted(set(failures)),
            "source_type_confusion": any("confusion" in failure for failure in failures),
            "mevzuat_evidence_count": len(mevzuat_evidence),
            "judicial_evidence_count": len(judicial_evidence),
        }

    async def _generate_with_llm_or_fallback(
        self,
        *,
        query: str,
        route: LegalRoute,
        evidence_packet: dict[str, Any],
        conversation_context: list[dict[str, str]],
    ) -> GeneratedLegalAnswer:
        if not self.config.legal_advisor_llm_enabled or self.llm_client is None:
            return self._compose_deterministic_answer(query=query, route=route, evidence_packet=evidence_packet)
        try:
            generated = await asyncio.wait_for(
                self._generate_with_llm(
                    query=query,
                    route=route,
                    evidence_packet=evidence_packet,
                    conversation_context=conversation_context,
                ),
                timeout=max(0.1, self.config.llm_timeout_ms / 1000.0),
            )
            verification = verify_legal_answer(
                answer=generated.answer,
                evidence_packet=evidence_packet,
                claims=generated.claims,
                route=route.route,
            )
            if verification["pass"]:
                return generated
            logger.warning("Legal LLM answer failed verification, using fallback: %s", verification["failures"])
            fallback = self._compose_deterministic_answer(query=query, route=route, evidence_packet=evidence_packet)
            fallback.fallback_reason = "llm_verification_failed"
            return fallback
        except Exception as exc:
            logger.warning("Legal LLM answer generation failed, using fallback: %s", exc, exc_info=True)
            fallback = self._compose_deterministic_answer(query=query, route=route, evidence_packet=evidence_packet)
            fallback.fallback_reason = "llm_generation_failed"
            return fallback

    async def _generate_with_llm(
        self,
        *,
        query: str,
        route: LegalRoute,
        evidence_packet: dict[str, Any],
        conversation_context: list[dict[str, str]],
    ) -> GeneratedLegalAnswer:
        from llm.client import ChatMessage

        system_prompt = (
            "Sen Türk hukuku için kaynakla sınırlı cevap üreten bir hukuk danışmanı motorusun. "
            "Yalnızca verilen evidence_packet içindeki kanıtlara dayan. Mevzuat ile yargı kararlarını ayır. "
            "Kanıt dışı kanun, madde, mahkeme, tarih, E/K veya içtihat iddiası kurma. "
            "Tek kararı yerleşik içtihat gibi sunma. Sonucu garanti etme. "
            "JSON döndür: summary, statutory_analysis, judicial_analysis, application, limitations, citations."
        )
        safe_context = [
            {"role": item.get("role"), "content": _bounded_text(str(item.get("content") or ""), 600)}
            for item in conversation_context[-4:]
            if item.get("role") in {"user", "assistant"}
        ]
        user_payload = {
            "question": query,
            "route": route.route,
            "conversation_context": safe_context,
            "evidence_packet": evidence_packet,
            "citation_contract": "Citations must be copied from evidence_packet.source_cards only; claims must cite evidence_ids.",
        }
        result = await self.llm_client.chat(
            messages=[
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=json.dumps(user_payload, ensure_ascii=False, sort_keys=True)),
            ],
            temperature=0.0,
            max_tokens=1600,
        )
        parsed = self._parse_llm_json(result.text)
        rendered = self._render_structured_answer(parsed=parsed, route=route, evidence_packet=evidence_packet)
        usage = None
        if getattr(result, "usage", None) is not None:
            usage = {
                "prompt_tokens": result.usage.prompt_tokens,
                "completion_tokens": result.usage.completion_tokens,
                "total_tokens": result.usage.total_tokens,
            }
        return GeneratedLegalAnswer(
            answer=rendered["answer"],
            claims=rendered["claims"],
            citations=rendered["citations"],
            llm_used=True,
            llm_trace=getattr(result, "trace", None),
            usage=usage,
        )

    def _parse_llm_json(self, text: str) -> dict[str, Any]:
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
            stripped = re.sub(r"```$", "", stripped).strip()
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            stripped = stripped[start : end + 1]
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError("LLM JSON payload is not an object")
        return payload

    def _render_structured_answer(
        self,
        *,
        parsed: dict[str, Any],
        route: LegalRoute,
        evidence_packet: dict[str, Any],
    ) -> dict[str, Any]:
        claims: list[dict[str, Any]] = []
        citations = [str(card["citation"]) for card in evidence_packet.get("source_cards") or [] if card.get("citation")]
        judicial = [
            item
            for item in evidence_packet.get("items") or []
            if item.get("source_type") == "judicial_decision"
        ]

        def _claim_lines(key: str, claim_type: str) -> list[str]:
            lines: list[str] = []
            rows = parsed.get(key) or []
            if isinstance(rows, list):
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    claim = str(row.get("claim") or "").strip()
                    ids = [str(item) for item in row.get("evidence_ids") or []]
                    if not claim or not ids:
                        continue
                    claims.append({"type": claim_type, "claim": claim, "evidence_ids": ids})
                    lines.append(f"- {claim} [{' ,'.join(ids)}]".replace(" ,", ", "))
            return lines

        lines = [
            "1. Kısa sonuç",
            _bounded_text(str(parsed.get("summary") or "Seçilen kaynaklara göre sınırlı bir hukuki değerlendirme yapılabilir."), 900),
            "",
            "2. Dayanak mevzuat",
        ]
        statutory_lines = _claim_lines("statutory_analysis", "statutory")
        lines.extend(statutory_lines or ["- Seçilen mevzuat kanıtı bulunmadığı için kanun hükmü sonucu kurulmadı."])
        if route.judicial_requested or judicial:
            lines.extend(["", "3. Yargı kararları / içtihat değerlendirmesi"])
            judicial_lines = _claim_lines("judicial_analysis", "judicial")
            if judicial_lines:
                lines.extend(judicial_lines)
            elif route.judicial_requested:
                lines.append("- Seçilen yargı kararı kanıtı bulunmadığı için içtihat sonucu kurulmadı.")
        lines.extend(["", "4. Somut olaya uygulama"])
        application_lines = _claim_lines("application", "application")
        lines.extend(application_lines or ["- Somut olay bilgileri sınırlı olduğu için uygulama sonucu varsayıma bağlanmalıdır."])
        lines.extend(["", "5. Sınırlar ve dikkat edilmesi gerekenler"])
        limitations = parsed.get("limitations") or []
        if isinstance(limitations, list) and limitations:
            lines.extend(f"- {_bounded_text(str(item), 420)}" for item in limitations[:5])
        else:
            lines.append("- Eksik olay bilgisi veya seçilmemiş kaynak varsa kesin hukuki sonuç kurulamaz.")
        lines.extend(["", "6. Kaynaklar"])
        source_lines = [f"- {card.get('evidence_id')}: {card.get('citation')}" for card in evidence_packet.get("source_cards") or []]
        lines.extend(source_lines or ["- Kaynak seçilmedi."])
        return {"answer": "\n".join(lines), "claims": claims, "citations": citations}

    def _compose_deterministic_answer(
        self,
        *,
        query: str,
        route: LegalRoute,
        evidence_packet: dict[str, Any],
    ) -> GeneratedLegalAnswer:
        items = evidence_packet.get("items") or []
        legislation = [item for item in items if item.get("source_type") == "legislation"]
        judicial = [item for item in items if item.get("source_type") == "judicial_decision"]
        claims: list[dict[str, Any]] = []
        citations = [str(card["citation"]) for card in evidence_packet.get("source_cards") or [] if card.get("citation")]

        lines = [
            "1. Kısa sonuç",
            "Seçilen kaynaklar, sorunun kaynakla sınırlı biçimde değerlendirilebileceğini gösteriyor. "
            "Mevzuat bağlayıcı kural olarak, yargı kararları ise somut olay uygulamasını gösteren destek olarak ayrı ele alınmıştır.",
            "",
            "2. Dayanak mevzuat",
        ]
        if legislation:
            for item in legislation:
                evidence_id = str(item["evidence_id"])
                law = item.get("law_short_name") or item.get("law_name") or "Mevzuat"
                article = item.get("article_no") or item.get("madde_no")
                claim = f"{law} m.{article} kapsamında seçilen metin, sorudaki hukuki değerlendirmenin bağlayıcı mevzuat dayanağıdır."
                claims.append({"type": "statutory", "claim": claim, "evidence_ids": [evidence_id]})
                lines.append(f"- {claim} [{evidence_id}]")
        else:
            lines.append("- Seçilen mevzuat kanıtı bulunmadığı için kanun hükmü sonucu kurulmadı.")

        if route.judicial_requested or judicial:
            lines.extend(["", "3. Yargı kararları / içtihat değerlendirmesi"])
        if judicial:
            distinct_decisions = {item.get("canonical_decision_id") for item in judicial}
            for item in judicial:
                evidence_id = str(item["evidence_id"])
                claim = (
                    f"{item.get('court')} {item.get('chamber')} kararında E. {item.get('esas_no')} "
                    f"K. {item.get('karar_no')} bilgisiyle seçilen paragraf, uyuşmazlığın mahkemece nasıl uygulandığını gösterir."
                )
                claims.append({"type": "judicial", "claim": claim, "evidence_ids": [evidence_id]})
                lines.append(f"- {claim} [{evidence_id}]")
            if len(distinct_decisions) == 1:
                lines.append("- Bu tek karar, yalnız başına genel ve sürekli yargı uygulaması iddiası için kullanılmadı.")
        elif route.judicial_requested:
            lines.append("- Seçilen yargı kararı kanıtı bulunmadığı için içtihat sonucu kurulmadı.")

        lines.extend(["", "4. Somut olaya uygulama"])
        application_ids = [str(item["evidence_id"]) for item in items[:3]]
        if application_ids:
            claim = (
                "Kullanıcı anlatımı, seçilen kaynaklardaki unsurlarla sınırlı eşleştirilebilir; eksik vakıalar "
                "tamamlanmadan kesin dava sonucu veya garanti edilen hukuki sonuç söylenemez."
            )
            claims.append({"type": "application", "claim": claim, "evidence_ids": application_ids})
            lines.append(f"- {claim} [{', '.join(application_ids)}]")
        else:
            lines.append("- Somut uygulama için seçilmiş kaynak bulunmadığından hukuki sonuç kurulmadı.")

        lines.extend(
            [
                "",
                "5. Sınırlar ve dikkat edilmesi gerekenler",
                "- Bu yanıt yalnızca seçilen kanıtlara dayanır; kaynak paketinde olmayan madde, karar veya olgu hakkında sonuç kurulmadı.",
                "- Taraf sıfatı, süreler, görevli mahkeme, deliller ve özel kanun hükümleri somut dosyada ayrıca kontrol edilmelidir.",
                "",
                "6. Kaynaklar",
            ]
        )
        source_lines = [f"- {card.get('evidence_id')}: {card.get('citation')}" for card in evidence_packet.get("source_cards") or []]
        lines.extend(source_lines or ["- Kaynak seçilmedi."])
        return GeneratedLegalAnswer(answer="\n".join(lines), claims=claims, citations=citations)

    def _finalize_generated_answer(
        self,
        *,
        generated: GeneratedLegalAnswer,
        route: LegalRoute,
        mevzuat_evidence: list[LegalEvidence],
        judicial_evidence: list[LegalEvidence],
        retrieval_metrics: dict[str, Any],
        started: float,
    ) -> LegalRuntimeResponse:
        evidence_packet = self._build_evidence_packet(mevzuat_evidence, judicial_evidence)
        verification_started = time.perf_counter()
        verification = verify_legal_answer(
            answer=generated.answer,
            evidence_packet=evidence_packet,
            claims=generated.claims,
            route=route.route,
        )
        verification["latency_ms"] = round((time.perf_counter() - verification_started) * 1000.0, 3)
        if not verification["pass"]:
            return self._response(
                answer="Üretilen cevap kaynak ve atıf denetimini geçmediği için hukuki sonuç döndürmüyorum. Daha somut olay bilgisi veya kaynak sınırlamasıyla tekrar deneyin.",
                citations=[],
                blocked=True,
                final_mode="refusal",
                final_reason="post_generation_verification_failed",
                route=route,
                mevzuat_evidence=mevzuat_evidence,
                judicial_evidence=judicial_evidence,
                started=started,
                verification=verification,
                retrieval_metrics=retrieval_metrics,
                generated=generated,
            )
        return self._response(
            answer=generated.answer,
            citations=generated.citations,
            blocked=False,
            final_mode="answer",
            final_reason=None,
            route=route,
            mevzuat_evidence=mevzuat_evidence,
            judicial_evidence=judicial_evidence,
            started=started,
            verification=verification,
            retrieval_metrics=retrieval_metrics,
            generated=generated,
        )

    def _response(
        self,
        *,
        answer: str,
        citations: list[str],
        blocked: bool,
        final_mode: str,
        final_reason: str | None,
        route: LegalRoute,
        mevzuat_evidence: list[LegalEvidence],
        judicial_evidence: list[LegalEvidence],
        started: float,
        verification: dict[str, Any] | None = None,
        retrieval_metrics: dict[str, Any] | None = None,
        generated: GeneratedLegalAnswer | None = None,
    ) -> LegalRuntimeResponse:
        evidence = [*mevzuat_evidence, *judicial_evidence]
        evidence_packet = self._build_evidence_packet(mevzuat_evidence, judicial_evidence)
        source_cards = evidence_packet["source_cards"]
        source_types = sorted({item.source_type for item in evidence})
        public_health = self.public_health()
        source_card_counts = dict(sorted(Counter(card.get("source_type") for card in source_cards).items()))
        retrieval_lanes = sorted({item.retrieval_lane for item in evidence if item.retrieval_lane})
        verification_status = (verification or {}).get("verdict") or ("not_run" if verification is None else "unknown")
        claims = generated.claims if generated else []
        latency_breakdown = dict((retrieval_metrics or {}).get("latency_by_lane_ms") or {})
        if isinstance(verification, dict) and verification.get("latency_ms") is not None:
            latency_breakdown["verification"] = verification["latency_ms"]
        evidence_summary = {
            "total": len(evidence),
            "by_source_type": source_card_counts,
            "mevzuat_evidence_count": len(mevzuat_evidence),
            "judicial_evidence_count": len(judicial_evidence),
            "retrieval_lanes": retrieval_lanes,
        }
        contract = {
            "answer_text": answer,
            "final_mode": final_mode,
            "legal_rag_runtime_mode": public_health["legal_rag_runtime_mode"],
            "route": route.route,
            "route_class": _route_class(route.route),
            "source_types": source_types,
            "source_cards": source_cards,
            "evidence_packet": evidence_packet,
            "claim_map": claims,
            "mevzuat_evidence_count": len(mevzuat_evidence),
            "judicial_evidence_count": len(judicial_evidence),
            "judicial_runtime_enabled": self.config.judicial_runtime_enabled,
            "judicial_ready": public_health["judicial_ready"],
            "citation_contract": "complete" if citations or blocked else "no_evidence",
            "primary_source_id": source_cards[0]["evidence_id"] if source_cards else None,
            "secondary_source_ids": [card["evidence_id"] for card in source_cards[1:]],
            "llm_answer_generation": bool(generated.llm_used) if generated else False,
            "fallback_reason": generated.fallback_reason if generated else None,
            "retrieval_mode_metadata": dict(retrieval_metrics or {}),
            "verification_metadata": verification,
            "verification_status": verification_status,
            "claims_verified": bool(verification and verification.get("pass") is True),
            "runtime_health": public_health,
            "degraded_mode": {
                "mevzuat_retriever_degraded": public_health["mevzuat_retriever_degraded"],
                "judicial_readiness_status": public_health["judicial_readiness_status"],
            },
            "source_card_count_by_source_type": source_card_counts,
            "evidence_summary": evidence_summary,
            "retrieval_lanes": retrieval_lanes,
            "latency_breakdown_ms": latency_breakdown,
            "verifier_enabled": public_health["verifier_enabled"],
        }
        metrics = dict(retrieval_metrics or {})
        metrics.update(
            {
                "llm_generation_latency_ms": None,
                "verification_latency_ms": verification.get("latency_ms") if isinstance(verification, dict) else None,
                "final_mode": final_mode,
                "final_reason": final_reason,
                "unsupported_claim_failures": (verification or {}).get("unsupported_claim_failures", []),
                "citation_mismatch_failures": (verification or {}).get("citation_mismatch_failures", []),
                "source_type_confusion_failures": ["source_type_confusion"]
                if (verification or {}).get("source_type_confusion")
                else [],
                "source_card_count_by_source_type": source_card_counts,
                "streaming_mode": "set_by_chat_router",
            }
        )
        trace = {
            "decision_lane": "legal_rag_runtime",
            "route": route.route,
            "route_class": _route_class(route.route),
            "route_confidence": route.confidence,
            "judicial_runtime_enabled": self.config.judicial_runtime_enabled,
            "judicial_index_status": public_health,
            "evidence": [item.to_public() for item in evidence],
            "evidence_packet": evidence_packet,
            "source_cards": source_cards,
            "answer_contract": contract,
            "verification": verification,
            "runtime_quality_metrics": metrics,
            "final_mode": final_mode,
            "final_reason": final_reason,
            "latency_ms": round((time.perf_counter() - started) * 1000.0, 3),
        }
        logger.info(
            "legal_rag_response route=%s final_mode=%s reason=%s blocked=%s sources=%s verification=%s fallback=%s latency_ms=%.3f",
            route.route,
            final_mode,
            final_reason,
            blocked,
            source_card_counts,
            (verification or {}).get("verdict"),
            generated.fallback_reason if generated else None,
            trace["latency_ms"],
        )
        return LegalRuntimeResponse(
            handled=True,
            answer=answer,
            citations=citations,
            blocked=blocked,
            guardrails_reasons=[final_reason] if blocked and final_reason else [],
            verification=verification,
            final_mode=final_mode,
            final_reason=final_reason,
            answer_contract=contract,
            trace=trace,
            usage=generated.usage if generated else None,
        )
