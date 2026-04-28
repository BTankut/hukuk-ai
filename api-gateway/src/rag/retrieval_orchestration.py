"""Retriever call wrappers for chat route orchestration."""

from __future__ import annotations

import logging
from typing import Any

from rag.orchestrator import RetrievedChunk
from rag.source_catalog import enrich_metadata_with_source_title


logger = logging.getLogger("routers.chat")


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
