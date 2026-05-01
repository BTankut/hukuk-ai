"""Evidence bundle serialization helpers for RAG responses."""

from __future__ import annotations

from typing import Any

from faz2a_hardening import canonicalize_source_id, normalize_query_text
from rag.article_span_selection import (
    _chunk_body_text_quality as _chunk_body_text_quality_impl,
    _resolve_chunk_span_id as _resolve_chunk_span_id_impl,
)
from rag.orchestrator import RAGOrchestrator, RetrievedChunk
from rag.source_catalog import resolve_effective_state
from rag.source_identity import (
    _chunk_article_token,
    _normalize_whitespace,
    _resolve_chunk_document_key,
    _resolve_chunk_source_family_profile,
    _resolve_chunk_source_title,
)


_TRUTHY_METADATA_FLAGS = {"1", "true", "yes", "y", "evet"}


def _metadata_flag_is_true(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return normalize_query_text(value) in _TRUTHY_METADATA_FLAGS
    return False


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


def _build_chunk_evidence_span(
    chunk: RetrievedChunk,
    *,
    query: str | None = None,
    max_len: int = 700,
) -> str:
    if query:
        return RAGOrchestrator._build_query_focused_excerpt(chunk.text, query=query, max_len=max_len)
    return RAGOrchestrator._build_chunk_excerpt(chunk.text, max_len=max_len)


def _serialize_trace_chunk(chunk: RetrievedChunk) -> dict[str, Any]:
    metadata = chunk.metadata or {}
    source_title = _resolve_chunk_source_title(chunk)
    family_profile = _resolve_chunk_source_family_profile(chunk)
    source_family = family_profile.get("resolved_family")
    source_identifier = _resolve_chunk_source_identifier(chunk)
    article_or_section = _chunk_article_token(chunk)
    body_quality = _chunk_body_text_quality_impl(chunk)
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
        "document_key": _resolve_chunk_document_key(chunk),
        "span_id": _resolve_chunk_span_id_impl(chunk),
        "article_or_section": article_or_section or None,
        "body_text_available": body_quality["body_text_available"],
        "body_text_length": body_quality["body_text_length"],
        "body_text_printable_ratio": body_quality["body_printable_ratio"],
        "body_text_alpha_count": body_quality["body_alpha_count"],
        "body_text_control_count": body_quality["body_control_count"],
        "title_only": bool(article_or_section in {"", "0"} or not body_quality["body_text_available"]),
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
        "historical_current_counterpart": _chunk_is_historical_current_counterpart(chunk),
        "metadata_lane_present": "metadata_guided_recall" in recall_lane_sources,
        "dense_lane_present": "semantic_dense_recall" in recall_lane_sources,
        "merged_lane_present": {"metadata_guided_recall", "semantic_dense_recall"} <= set(recall_lane_sources),
        "heading": metadata.get("heading") or metadata.get("article_heading"),
        "madde_no": metadata.get("madde_no"),
        "fikra_no": metadata.get("fikra_no"),
        "yururluk_baslangic": metadata.get("yururluk_baslangic"),
        "yururluk_bitis": metadata.get("yururluk_bitis"),
        "mulga": metadata.get("mulga"),
        "relation_chain_role": metadata.get("relation_chain_role"),
        "relation_chain_expansion_applied": metadata.get("relation_chain_expansion_applied"),
        "relation_chain_source_key": metadata.get("relation_chain_source_key"),
        "relation_chain_repeal_source_key": metadata.get("relation_chain_repeal_source_key"),
        "relation_chain_current_basis_source_key": metadata.get("relation_chain_current_basis_source_key"),
        "relation_chain_span_keys": metadata.get("relation_chain_span_keys"),
        "relation_chain_missing_reason": metadata.get("relation_chain_missing_reason"),
        "historical_source_effective_state": metadata.get("historical_source_effective_state"),
        "current_law_basis_added": metadata.get("current_law_basis_added"),
        "repeal_instrument_added": metadata.get("repeal_instrument_added"),
        "historical_source_not_marked_active": metadata.get("historical_source_not_marked_active"),
        "repealed_as_active_count": metadata.get("repealed_as_active_count"),
        "temporal_claim_alignment_applied": metadata.get("temporal_claim_alignment_applied"),
        "temporal_claim_primary_role": metadata.get("temporal_claim_primary_role"),
        "temporal_claim_historical_source_key": metadata.get("temporal_claim_historical_source_key"),
        "temporal_claim_repeal_source_key": metadata.get("temporal_claim_repeal_source_key"),
        "temporal_claim_current_basis_source_key": metadata.get("temporal_claim_current_basis_source_key"),
        "temporal_claim_consistency_status": metadata.get("temporal_claim_consistency_status"),
        "temporal_claim_missing_reason": metadata.get("temporal_claim_missing_reason"),
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
        metadata = chunk.metadata or {}
        for source_id in (
            _resolve_trace_source_id(chunk),
            chunk.citation,
            chunk.source,
            _resolve_chunk_source_identifier(chunk),
            str(metadata.get("canonical_identifier_display") or ""),
            str(metadata.get("display_citation") or ""),
        ):
            normalized = str(source_id or "").strip()
            if not normalized or normalized in seen:
                continue
            whitelist.append(normalized)
            seen.add(normalized)
    return whitelist
