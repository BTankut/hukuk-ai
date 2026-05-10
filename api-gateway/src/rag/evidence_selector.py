from __future__ import annotations

import re
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

from rag.orchestrator import RetrievedChunk
from rag.query_analyzer import QueryAnalysis


ACTIVE_END_SENTINELS = {"", "9999-12-31", "9999-12-31T00:00:00", "9999-12-31 00:00:00"}
TOKEN_RE = re.compile(r"[a-z0-9]{3,}")
TR_ASCII_TRANS = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "İ": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
    }
)
STOPWORDS = {
    "ve",
    "ile",
    "icin",
    "gore",
    "hangi",
    "nedir",
    "nasil",
    "madde",
    "kanun",
    "olarak",
    "kisa",
    "cevap",
}


@dataclass(frozen=True, slots=True)
class EvidenceGroup:
    key: str
    chunks: list[RetrievedChunk]
    rank_score: tuple[Any, ...]


def normalize_text(text: str) -> str:
    return text.translate(TR_ASCII_TRANS).lower()


def query_terms(text: str) -> set[str]:
    return {
        token
        for token in TOKEN_RE.findall(normalize_text(text or ""))
        if token not in STOPWORDS
    }


def _metadata(chunk: RetrievedChunk) -> dict[str, Any]:
    return chunk.metadata or {}


def source_id(chunk: RetrievedChunk) -> str:
    metadata = _metadata(chunk)
    return str(
        metadata.get("source_id")
        or metadata.get("document_source_id")
        or metadata.get("article_source_id")
        or metadata.get("law_short_name")
        or metadata.get("kanun_kisa_adi")
        or metadata.get("law_no")
        or metadata.get("kanun_no")
        or chunk.source
        or chunk.citation
        or ""
    ).strip()


def article_no(chunk: RetrievedChunk) -> str:
    metadata = _metadata(chunk)
    return str(metadata.get("article_no") or metadata.get("madde_no") or "").strip()


def paragraph_no(chunk: RetrievedChunk) -> str:
    metadata = _metadata(chunk)
    return str(metadata.get("paragraph_no") or metadata.get("fikra_no") or "").strip()


def group_key(chunk: RetrievedChunk) -> str:
    return f"{source_id(chunk)}|m:{article_no(chunk)}"


def effective_state(chunk: RetrievedChunk) -> str:
    metadata = _metadata(chunk)
    state = str(metadata.get("effective_state") or "").strip().lower()
    if state:
        return state
    if metadata.get("mulga") is True:
        return "repealed"
    family = str(metadata.get("source_family") or metadata.get("belge_turu") or "").lower()
    if family.startswith("mulga"):
        return "repealed"
    end = str(metadata.get("effective_end_date") or metadata.get("yururluk_bitis") or "").strip()
    if end and end not in ACTIVE_END_SENTINELS:
        return "historical"
    return "active"


def _active_rank(chunk: RetrievedChunk, analysis: QueryAnalysis | None) -> int:
    if analysis and analysis.wants_historical_law:
        return 0
    state = effective_state(chunk)
    return 1 if state in {"repealed", "historical"} else 0


def _chunk_text_for_overlap(chunk: RetrievedChunk) -> str:
    metadata = _metadata(chunk)
    parts = [
        chunk.text or "",
        chunk.citation or "",
        str(metadata.get("canonical_citation") or ""),
        str(metadata.get("title") or metadata.get("source_title") or metadata.get("belge_adi") or ""),
        str(metadata.get("article_heading") or metadata.get("heading") or ""),
    ]
    return " ".join(parts)


def _overlap(chunk: RetrievedChunk, terms: set[str]) -> int:
    return len(query_terms(_chunk_text_for_overlap(chunk)) & terms)


def _exact_ref_rank(chunk: RetrievedChunk, analysis: QueryAnalysis | None) -> int:
    if not analysis or not analysis.article_refs:
        return 1
    candidates = {
        str(_metadata(chunk).get("law_short_name") or ""),
        str(_metadata(chunk).get("kanun_kisa_adi") or ""),
        str(_metadata(chunk).get("law_no") or ""),
        str(_metadata(chunk).get("kanun_no") or ""),
        str(chunk.source or ""),
        source_id(chunk).split(":", 1)[-1],
    }
    current_article = article_no(chunk)
    for ref in analysis.article_refs:
        if ref.article_no == current_article and ref.law in candidates:
            if ref.paragraph_no and ref.paragraph_no != paragraph_no(chunk):
                continue
            return 0
    return 1


def _source_family_rank(chunk: RetrievedChunk, analysis: QueryAnalysis | None) -> int:
    if not analysis or not analysis.source_families:
        return 0
    metadata = _metadata(chunk)
    family = str(metadata.get("source_family") or metadata.get("belge_turu") or "").strip().lower()
    return 0 if family in set(analysis.source_families) else 1


def group_candidates_by_article(chunks: list[RetrievedChunk]) -> list[list[RetrievedChunk]]:
    groups: OrderedDict[str, list[RetrievedChunk]] = OrderedDict()
    for chunk in chunks:
        key = group_key(chunk)
        if not key.strip("|m:"):
            key = f"fallback:{len(groups)}:{chunk.citation}"
        groups.setdefault(key, []).append(chunk)
    return list(groups.values())


def select_evidence_chunks(
    *,
    query: str,
    chunks: list[RetrievedChunk],
    analysis: QueryAnalysis | None = None,
    limit: int = 20,
    max_chunks_per_article: int = 2,
) -> list[RetrievedChunk]:
    if not chunks:
        return []

    terms = query_terms(query)
    groups: list[EvidenceGroup] = []
    for original_index, grouped_chunks in enumerate(group_candidates_by_article(chunks)):
        ranked_group_chunks = sorted(
            enumerate(grouped_chunks),
            key=lambda item: (
                _exact_ref_rank(item[1], analysis),
                _active_rank(item[1], analysis),
                -_overlap(item[1], terms),
                -(item[1].score or 0.0),
                item[0],
            ),
        )
        best = ranked_group_chunks[0][1]
        group_score = (
            _exact_ref_rank(best, analysis),
            _active_rank(best, analysis),
            _source_family_rank(best, analysis),
            -max(_overlap(chunk, terms) for chunk in grouped_chunks),
            -max((chunk.score or 0.0) for chunk in grouped_chunks),
            original_index,
        )
        groups.append(
            EvidenceGroup(
                key=group_key(best),
                chunks=[chunk for _idx, chunk in ranked_group_chunks[:max_chunks_per_article]],
                rank_score=group_score,
            )
        )

    selected: list[RetrievedChunk] = []
    for group in sorted(groups, key=lambda item: item.rank_score):
        selected.extend(group.chunks)
        if len(selected) >= limit:
            break
    return selected[:limit]


def evidence_selection_trace(
    *,
    chunks: list[RetrievedChunk],
    analysis: QueryAnalysis | None,
) -> dict[str, Any]:
    state_counts: dict[str, int] = {}
    for chunk in chunks:
        state = effective_state(chunk)
        state_counts[state] = state_counts.get(state, 0) + 1
    return {
        "selector": "deterministic_article_grouping_v1",
        "group_count": len(group_candidates_by_article(chunks)),
        "selected_chunk_count": len(chunks),
        "temporal_intent": analysis.temporal_intent if analysis else None,
        "effective_state_counts": state_counts,
    }
