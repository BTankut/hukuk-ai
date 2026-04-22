"""Shared article-alignment semantics for hukuk-ai benchmark reports."""

from __future__ import annotations

import re
from typing import Literal

from evaluation.hukuk_ai_100_source_schema import normalize_text


ArticleAlignment = Literal["exact", "neighbor", "title_only", "clause_only", "none", "unknown"]
ARTICLE_ALIGNMENTS: tuple[str, ...] = ("exact", "neighbor", "title_only", "clause_only", "none", "unknown")


def canonical_article_token(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    normalized = normalize_text(text)
    if normalized in {"unknown", "none", "null", "yok"}:
        return ""

    patterns = (
        r"\bgecici\s+madde\s+([0-9]+[a-z]?)\b",
        r"\bgecici_madde\s+([0-9]+[a-z]?)\b",
        r"\bmadde\s+([0-9]+[a-z]?)\b",
        r"\bm\s+([0-9]+[a-z]?)\b",
        r"\bm([0-9]+[a-z]?)\b",
        r"\b([0-9]+[a-z]?)\b",
    )
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            prefix = "gecici-" if pattern.startswith(r"\bgecici") else ""
            return f"{prefix}{match.group(1)}"
    return ""


def article_distance(left: object, right: object) -> int | None:
    left_token = canonical_article_token(left)
    right_token = canonical_article_token(right)
    if not left_token or not right_token:
        return None
    left_prefix, left_number = _numeric_article_parts(left_token)
    right_prefix, right_number = _numeric_article_parts(right_token)
    if left_number is None or right_number is None or left_prefix != right_prefix:
        return None
    return abs(left_number - right_number)


def articles_equal(left: object, right: object) -> bool:
    left_token = canonical_article_token(left)
    right_token = canonical_article_token(right)
    return bool(left_token and right_token and left_token == right_token)


def classify_article_alignment(
    *,
    selected_article: object = "",
    claimed_article: object = "",
    article_match_type: object = "",
    selected_paragraph_or_clause: object = "",
) -> ArticleAlignment:
    selected_token = canonical_article_token(selected_article)
    claimed_token = canonical_article_token(claimed_article)
    match_type = normalize_text(str(article_match_type or ""))

    if selected_token and claimed_token:
        if selected_token == claimed_token and selected_token != "0":
            return "exact"
        if selected_token == "0" or claimed_token == "0":
            return "title_only"
        distance = article_distance(selected_token, claimed_token)
        if distance == 1:
            return "neighbor"
        return "none"

    if match_type in {"explicit_exact", "exact"}:
        return "exact"
    if match_type in {"adjacent", "neighbor"}:
        return "neighbor"
    if selected_token == "0" or match_type in {"title_only", "source_local_support"}:
        return "title_only"
    if str(selected_paragraph_or_clause or "").strip() and not selected_token:
        return "clause_only"
    if selected_token or claimed_token:
        return "none"
    return "unknown"


def classify_query_article_alignment(
    *,
    selected_article: object = "",
    query_article_tokens: object = None,
    article_match_type: object = "",
    selected_paragraph_or_clause: object = "",
) -> ArticleAlignment:
    selected_token = canonical_article_token(selected_article)
    tokens = [canonical_article_token(token) for token in _iter_tokens(query_article_tokens)]
    tokens = [token for token in tokens if token]
    match_type = normalize_text(str(article_match_type or ""))

    if not tokens:
        if selected_token == "0":
            return "title_only"
        if str(selected_paragraph_or_clause or "").strip() and not selected_token:
            return "clause_only"
        return "unknown"
    if selected_token and selected_token in tokens:
        return "exact"
    if selected_token == "0":
        return "title_only"
    if selected_token and any(article_distance(selected_token, token) == 1 for token in tokens):
        return "neighbor"
    if match_type in {"title_only", "source_local_support"}:
        return "title_only"
    if str(selected_paragraph_or_clause or "").strip() and not selected_token:
        return "clause_only"
    return "none"


def _iter_tokens(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    text = str(value)
    return [part for part in re.split(r"\s*\|\s*|\s*,\s*", text) if part.strip()]


def _numeric_article_parts(token: str) -> tuple[str, int | None]:
    normalized = canonical_article_token(token)
    prefix = "gecici" if normalized.startswith("gecici-") else "normal"
    number_part = normalized.split("-", 1)[1] if prefix == "gecici" else normalized
    match = re.fullmatch(r"([0-9]+)[a-z]?", number_part)
    if not match:
        return prefix, None
    return prefix, int(match.group(1))
