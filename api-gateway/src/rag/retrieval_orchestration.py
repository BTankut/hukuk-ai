"""Retriever call wrappers for chat route orchestration."""

from __future__ import annotations

import json
import logging
from typing import Any

from rag.orchestrator import RetrievedChunk
from rag.source_catalog import enrich_metadata_with_source_title


logger = logging.getLogger("routers.chat")


_RELATION_CHAIN_INACTIVE_STATES = {"historical", "repealed", "historical_repealed"}
_RELATION_CHAIN_ANCHOR_ROLES = {
    "historical_repealed_source",
    "repeal_instrument",
    "current_law_basis",
}
_RELATION_CHAIN_TYPES = {
    "historical_repealed_to_current_bridge",
    "repeals_historical_regulation",
    "current_law_basis_for_repealed_discipline_regulation",
    "repealed_by",
    "repeals",
    "current_law_basis",
    "replaced_by",
    "transition_rule",
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


def _metadata_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _relation_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return _metadata_dict(metadata.get("relation_metadata"))


def _clean_relation_value(value: Any) -> str:
    return str(value or "").strip()


def _relation_value_set(*values: Any) -> set[str]:
    return {
        cleaned
        for cleaned in (_clean_relation_value(value) for value in values)
        if cleaned
    }


def _milvus_string_literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _relation_chain_effective_state(metadata: dict[str, Any]) -> str:
    return str(metadata.get("effective_state") or "").strip().lower()


def _relation_chain_anchor_reason(chunk: RetrievedChunk) -> str | None:
    metadata = chunk.metadata or {}
    relation_metadata = _relation_metadata(metadata)
    relation_type = str(relation_metadata.get("relation_type") or "").strip()
    effective_state = _relation_chain_effective_state(metadata)
    bridge_role = str(metadata.get("bridge_role") or "").strip()
    if not relation_metadata:
        return None
    if effective_state in _RELATION_CHAIN_INACTIVE_STATES:
        return "historical_or_repealed_effective_state"
    if bridge_role in _RELATION_CHAIN_ANCHOR_ROLES:
        return "bridge_role_relation_metadata"
    if relation_type in _RELATION_CHAIN_TYPES:
        return "relation_type_metadata"
    return None


def _relation_chain_chunk_key(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    for key in (
        "span_id",
        "canonical_span_key",
        "canonical_source_key_v2",
        "source_key_v2",
        "source_key",
        "chunk_id",
    ):
        value = str(metadata.get(key) or "").strip()
        if value:
            return value
    source_identifier = str(
        metadata.get("source_identifier")
        or metadata.get("law_no")
        or metadata.get("kanun_no")
        or metadata.get("belge_no")
        or chunk.source
        or ""
    ).strip()
    article = str(metadata.get("madde_no") or "").strip()
    paragraph = str(metadata.get("fikra_no") or "").strip()
    if source_identifier or article or paragraph:
        return f"{source_identifier}:m{article}:f{paragraph}"
    return f"{chunk.citation}:{hash(chunk.text)}"


def _relation_chain_source_key(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    for key in (
        "canonical_document_key_v2",
        "binding_source_key",
        "source_key_v2",
        "source_key",
        "source_identifier",
        "law_no",
        "kanun_no",
        "belge_no",
        "law_short_name",
        "kanun_kisa_adi",
    ):
        value = str(metadata.get(key) or "").strip()
        if value:
            return value
    return str(chunk.source or chunk.citation or "").strip()


def _relation_chain_citation(metadata: dict[str, Any], *, fallback_id: str) -> str:
    display = str(
        metadata.get("canonical_identifier_display")
        or metadata.get("display_citation")
        or ""
    ).strip()
    if display:
        return display
    source_name = str(
        metadata.get("law_short_name")
        or metadata.get("kanun_kisa_adi")
        or metadata.get("source_identifier")
        or metadata.get("law_no")
        or metadata.get("kanun_no")
        or metadata.get("belge_no")
        or fallback_id
        or "?"
    ).strip()
    article = str(metadata.get("madde_no") or "").strip()
    paragraph = str(metadata.get("fikra_no") or "").strip()
    if article:
        citation = f"{source_name} m.{article}"
        if paragraph and paragraph not in {"0", "1"}:
            citation = f"{citation}/f.{paragraph}"
        return citation
    return source_name


def _relation_chain_source(metadata: dict[str, Any], *, fallback_id: str) -> str:
    return str(
        metadata.get("law_short_name")
        or metadata.get("kanun_kisa_adi")
        or metadata.get("source_identifier")
        or metadata.get("law_no")
        or metadata.get("kanun_no")
        or metadata.get("belge_no")
        or fallback_id
        or ""
    ).strip()


def _relation_chain_role(metadata: dict[str, Any]) -> str:
    bridge_role = str(metadata.get("bridge_role") or "").strip()
    relation_type = str(_relation_metadata(metadata).get("relation_type") or "").strip()
    if bridge_role == "current_law_basis" or relation_type == "current_law_basis_for_repealed_discipline_regulation":
        return "current_law_basis"
    if bridge_role == "repeal_instrument" or relation_type == "repeals_historical_regulation":
        return "repeal_instrument"
    if bridge_role == "historical_repealed_source" or _relation_chain_effective_state(metadata) in _RELATION_CHAIN_INACTIVE_STATES:
        return "historical_rule"
    return "transition_rule"


def _relation_chain_rows_to_chunks(
    rows: list[dict[str, Any]],
    *,
    anchor: RetrievedChunk,
    role_override: str | None = None,
) -> list[RetrievedChunk]:
    chunks: list[RetrievedChunk] = []
    anchor_score = float(anchor.score or 0.0)
    for index, row in enumerate(rows):
        entity = row.get("entity") if isinstance(row.get("entity"), dict) else row
        row_id = str(row.get("id") or entity.get("id") or "").strip()
        raw_metadata = entity.get("metadata") if isinstance(entity, dict) else {}
        metadata = enrich_metadata_with_source_title(_metadata_dict(raw_metadata))
        if row_id and not metadata.get("chunk_id"):
            metadata["chunk_id"] = row_id
        text = str(entity.get("text") or "")
        role = role_override or _relation_chain_role(metadata)
        metadata["relation_chain_role"] = role
        metadata["relation_chain_expansion_applied"] = True
        metadata["relation_chain_retrieval_lane"] = "relation_metadata_source_chain"
        metadata["domain_law_supporting_source"] = role in {"current_law_basis", "repeal_instrument", "transition_rule"}
        metadata["historical_source_not_marked_active"] = (
            _relation_chain_effective_state(metadata) not in _RELATION_CHAIN_INACTIVE_STATES
            or role != "historical_rule"
        )
        chunks.append(
            RetrievedChunk(
                text=text,
                citation=_relation_chain_citation(metadata, fallback_id=row_id),
                source=_relation_chain_source(metadata, fallback_id=row_id),
                score=max(anchor_score, 1.0) + max(0.0, 0.03 - (index * 0.001)),
                metadata=metadata,
            )
        )
    return _annotate_recall_lane_chunks(chunks, lane="relation_chain_recall")


def _relation_chain_query_rows(
    *,
    retriever: Any,
    filter_expr: str,
    limit: int,
) -> list[dict[str, Any]]:
    client = getattr(retriever, "client", None)
    collection = getattr(retriever, "collection", None)
    if client is None or not collection or not hasattr(client, "query"):
        return []
    try:
        rows = client.query(
            collection_name=collection,
            filter=filter_expr,
            output_fields=["id", "text", "metadata"],
            limit=limit,
        )
    except Exception as exc:
        logger.warning("Relation-chain metadata query bypass (filter=%s): %s", filter_expr, exc)
        return []
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _relation_chain_query_by_relation_field(
    *,
    retriever: Any,
    field: str,
    value: str,
    limit: int,
) -> list[dict[str, Any]]:
    escaped = _milvus_string_literal(value)
    return _relation_chain_query_rows(
        retriever=retriever,
        filter_expr=f'metadata["relation_metadata"]["{field}"] == "{escaped}"',
        limit=limit,
    )


def _annotate_relation_chain_chunk(
    chunk: RetrievedChunk,
    *,
    policy: dict[str, Any],
    span_keys: list[str],
) -> None:
    metadata = dict(chunk.metadata or {})
    metadata["relation_chain_expansion_applied"] = policy["relation_chain_expansion_applied"]
    metadata["relation_chain_source_key"] = policy.get("relation_chain_source_key")
    metadata["relation_chain_repeal_source_key"] = policy.get("relation_chain_repeal_source_key")
    metadata["relation_chain_current_basis_source_key"] = policy.get("relation_chain_current_basis_source_key")
    metadata["relation_chain_span_keys"] = span_keys
    metadata["relation_chain_missing_reason"] = policy.get("relation_chain_missing_reason")
    metadata["historical_source_effective_state"] = policy.get("historical_source_effective_state")
    metadata["current_law_basis_added"] = policy.get("current_law_basis_added")
    metadata["repeal_instrument_added"] = policy.get("repeal_instrument_added")
    metadata["historical_source_not_marked_active"] = policy.get("historical_source_not_marked_active")
    metadata["repealed_as_active_count"] = policy.get("repealed_as_active_count")
    chunk.metadata = metadata


def _retrieve_relation_chain_chunks(
    *,
    retriever: Any,
    query: str,
    chunks: list[RetrievedChunk],
    source_family_resolution: Any | None = None,
    max_anchors: int = 4,
    max_repeal_chunks_per_chain: int = 3,
    max_current_basis_chunks_per_chain: int = 3,
    max_total_added_chunks: int = 8,
) -> tuple[list[RetrievedChunk], dict[str, Any]]:
    """Retrieve relation-metadata source-chain support without benchmark/QID rules."""

    del query, source_family_resolution  # Expansion is intentionally metadata-driven.
    policy: dict[str, Any] = {
        "relation_chain_expansion_applied": False,
        "relation_chain_source_key": None,
        "relation_chain_repeal_source_key": None,
        "relation_chain_current_basis_source_key": None,
        "relation_chain_span_keys": [],
        "relation_chain_missing_reason": "no_relation_metadata_anchor",
        "historical_source_effective_state": None,
        "current_law_basis_added": False,
        "repeal_instrument_added": False,
        "historical_source_not_marked_active": True,
        "repealed_as_active_count": 0,
        "relation_chain_anchor_count": 0,
        "relation_chain_added_count": 0,
    }
    if not chunks:
        policy["relation_chain_missing_reason"] = "no_candidate_chunks"
        return [], policy
    if not hasattr(getattr(retriever, "client", None), "query"):
        policy["relation_chain_missing_reason"] = "retriever_query_unavailable"
        return [], policy

    anchors: list[tuple[RetrievedChunk, str]] = []
    for chunk in chunks:
        reason = _relation_chain_anchor_reason(chunk)
        if reason:
            anchors.append((chunk, reason))
        if len(anchors) >= max_anchors:
            break

    if not anchors:
        return [], policy

    policy["relation_chain_anchor_count"] = len(anchors)
    added_chunks: list[RetrievedChunk] = []
    seen_keys = {_relation_chain_chunk_key(chunk) for chunk in chunks}
    anchor_chunks: list[RetrievedChunk] = []

    for anchor, reason in anchors:
        anchor_metadata = anchor.metadata or {}
        relation_metadata = _relation_metadata(anchor_metadata)
        historical_state = _relation_chain_effective_state(anchor_metadata)
        source_key = _relation_chain_source_key(anchor)
        historical_source_ids = _relation_value_set(
            relation_metadata.get("historical_source_id"),
            relation_metadata.get("repealed_source_id"),
        )
        repeal_source_ids = _relation_value_set(
            relation_metadata.get("repealed_by_source_id"),
            relation_metadata.get("repeal_source_id"),
        )
        current_basis_chunks: list[RetrievedChunk] = []
        for repeal_source_id in sorted(repeal_source_ids):
            rows = _relation_chain_query_by_relation_field(
                retriever=retriever,
                field="repeal_source_id",
                value=repeal_source_id,
                limit=max_current_basis_chunks_per_chain,
            )
            current_basis_chunks.extend(
                _relation_chain_rows_to_chunks(rows, anchor=anchor, role_override="current_law_basis")
            )
        for current_chunk in current_basis_chunks:
            current_relation_metadata = _relation_metadata(current_chunk.metadata or {})
            historical_source_ids.update(
                _relation_value_set(current_relation_metadata.get("historical_source_id"))
            )

        repeal_chunks: list[RetrievedChunk] = []
        for historical_source_id in sorted(historical_source_ids):
            rows = _relation_chain_query_by_relation_field(
                retriever=retriever,
                field="repealed_source_id",
                value=historical_source_id,
                limit=max_repeal_chunks_per_chain,
            )
            repeal_chunks.extend(
                _relation_chain_rows_to_chunks(rows, anchor=anchor, role_override="repeal_instrument")
            )
            if not current_basis_chunks:
                rows = _relation_chain_query_by_relation_field(
                    retriever=retriever,
                    field="historical_source_id",
                    value=historical_source_id,
                    limit=max_current_basis_chunks_per_chain,
                )
                current_basis_chunks.extend(
                    _relation_chain_rows_to_chunks(rows, anchor=anchor, role_override="current_law_basis")
                )

        anchor_chunks.append(anchor)
        for candidate in [*repeal_chunks, *current_basis_chunks]:
            key = _relation_chain_chunk_key(candidate)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            added_chunks.append(candidate)
            if len(added_chunks) >= max_total_added_chunks:
                break
        if added_chunks:
            policy["relation_chain_missing_reason"] = None
            policy["relation_chain_source_key"] = policy["relation_chain_source_key"] or source_key
            policy["historical_source_effective_state"] = (
                policy["historical_source_effective_state"] or historical_state or "unknown"
            )
            policy["relation_chain_anchor_reason"] = reason
        if len(added_chunks) >= max_total_added_chunks:
            break

    if not added_chunks:
        policy["relation_chain_missing_reason"] = "relation_metadata_present_but_related_rows_not_found"
        return [], policy

    repeal_source_keys = [
        _relation_chain_source_key(chunk)
        for chunk in added_chunks
        if (chunk.metadata or {}).get("relation_chain_role") == "repeal_instrument"
    ]
    current_source_keys = [
        _relation_chain_source_key(chunk)
        for chunk in added_chunks
        if (chunk.metadata or {}).get("relation_chain_role") == "current_law_basis"
    ]
    span_keys = [_relation_chain_chunk_key(chunk) for chunk in [*anchor_chunks, *added_chunks]]
    repeated_as_active_count = sum(
        1
        for chunk in [*anchor_chunks, *added_chunks]
        if (chunk.metadata or {}).get("relation_chain_role") == "historical_rule"
        and _relation_chain_effective_state(chunk.metadata or {}) not in _RELATION_CHAIN_INACTIVE_STATES
    )
    policy.update(
        {
            "relation_chain_expansion_applied": True,
            "relation_chain_repeal_source_key": repeal_source_keys[0] if repeal_source_keys else None,
            "relation_chain_current_basis_source_key": current_source_keys[0] if current_source_keys else None,
            "relation_chain_span_keys": span_keys,
            "relation_chain_missing_reason": None,
            "current_law_basis_added": bool(current_source_keys),
            "repeal_instrument_added": bool(repeal_source_keys),
            "historical_source_not_marked_active": repeated_as_active_count == 0,
            "repealed_as_active_count": repeated_as_active_count,
            "relation_chain_added_count": len(added_chunks),
        }
    )
    for anchor in anchor_chunks:
        anchor_metadata = dict(anchor.metadata or {})
        anchor_metadata.setdefault("relation_chain_role", "historical_rule")
        anchor.metadata = anchor_metadata
    for chunk in [*anchor_chunks, *added_chunks]:
        _annotate_relation_chain_chunk(chunk, policy=policy, span_keys=span_keys)
    return added_chunks, policy


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
