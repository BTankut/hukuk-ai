from __future__ import annotations

import re
from typing import Any

from rag.orchestrator import RetrievedChunk
from rag.source_identity import (
    _chunk_article_token,
    _chunk_clause_token,
    _normalize_article_token,
    _normalize_tr_text,
    _resolve_chunk_document_key,
)


def _resolve_chunk_span_id(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    chunk_id = metadata.get("chunk_id")
    if chunk_id:
        return str(chunk_id)
    citation = re.sub(r"\s+", " ", chunk.citation or "").strip()
    if citation:
        return citation
    document_key = _resolve_chunk_document_key(chunk)
    article = _chunk_article_token(chunk)
    clause = _chunk_clause_token(chunk)
    parts = [part for part in (document_key, article, clause) if part]
    return ":".join(parts)


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


def _strip_chunk_citation_prefix(text: str, chunk: RetrievedChunk) -> str:
    lines = [line for line in str(text or "").splitlines()]
    while lines:
        first = lines[0].strip()
        if not first:
            lines.pop(0)
            continue
        normalized_first = _normalize_tr_text(first)
        normalized_citation = _normalize_tr_text(chunk.citation or "")
        normalized_span_id = _normalize_tr_text(_resolve_chunk_span_id(chunk))
        citation_like = bool(
            normalized_first
            and (
                normalized_first in {normalized_citation, normalized_span_id}
                or re.fullmatch(r"[\w./:-]+\s+m\.?\s*[\w./:-]+(?:\s*/?\s*f\.?\s*[\w./:-]+)?", normalized_first)
                or re.fullmatch(r"[\w./:-]+:[\w./:-]+:m?[\w./:-]+(?::f?[\w./:-]+)?", normalized_first)
            )
        )
        if citation_like:
            lines.pop(0)
            continue
        break
    return "\n".join(lines).strip()


def _chunk_body_text_for_quality(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    for key in ("body", "article_body", "article_text", "content", "metin"):
        value = metadata.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return _strip_chunk_citation_prefix(chunk.text or "", chunk)


def _chunk_body_text_quality(chunk: RetrievedChunk) -> dict[str, Any]:
    body = _chunk_body_text_for_quality(chunk)
    stripped = body.strip()
    if not stripped:
        return {
            "body_text_length": 0,
            "body_printable_ratio": 0.0,
            "body_alpha_count": 0,
            "body_control_count": 0,
            "body_text_available": False,
        }
    printable_or_whitespace = sum(1 for char in stripped if char.isprintable() or char in "\n\r\t")
    control_count = sum(1 for char in stripped if not char.isprintable() and char not in "\n\r\t")
    alpha_count = sum(1 for char in stripped if char.isalpha())
    printable_ratio = printable_or_whitespace / len(stripped)
    control_ratio = control_count / len(stripped)
    return {
        "body_text_length": len(stripped),
        "body_printable_ratio": round(printable_ratio, 4),
        "body_alpha_count": alpha_count,
        "body_control_count": control_count,
        "body_text_available": bool(
            len(stripped) >= 40
            and printable_ratio >= 0.85
            and alpha_count >= 20
            and (control_count <= 3 or control_ratio <= 0.08)
        ),
    }


def _chunk_has_selectable_body_span(chunk: RetrievedChunk) -> bool:
    return bool(_chunk_body_text_quality(chunk).get("body_text_available"))


def _chunk_has_non_title_body_span(chunk: RetrievedChunk) -> bool:
    return bool(_chunk_article_token(chunk) not in {"", "0"} and _chunk_has_selectable_body_span(chunk))
