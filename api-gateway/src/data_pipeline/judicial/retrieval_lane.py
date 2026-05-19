from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from typing import Any

from data_pipeline.judicial.corpus import JudicialExactLookup
from rag.retriever import RetrievalResult, RetrievalStats


JUDICIAL_RUNTIME_ENABLED_ENV = "JUDICIAL_RUNTIME_ENABLED"
DEFAULT_JUDICIAL_COLLECTION = "judicial_decisions_v1_shadow"


class DisabledJudicialRuntimeError(RuntimeError):
    """Raised when runtime tries to use judicial evidence before closure."""


def judicial_runtime_enabled() -> bool:
    return os.getenv(JUDICIAL_RUNTIME_ENABLED_ENV, "false").lower() in {"1", "true", "yes", "on"}


def assert_judicial_runtime_disabled() -> dict[str, Any]:
    enabled = judicial_runtime_enabled()
    return {
        "runtime_enabled": enabled,
        "pass": not enabled,
        "env_var": JUDICIAL_RUNTIME_ENABLED_ENV,
        "required_state": "false until judicial corpus closure gate passes",
    }


def build_indexable_documents(
    chunks: list[dict[str, Any]],
    *,
    include_metadata_header: bool = False,
) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for chunk in chunks:
        metadata = dict(chunk.get("metadata") or {})
        if not include_metadata_header and metadata.get("vector_index_eligible") is False:
            continue
        documents.append(
            {
                "id": metadata.get("chunk_key") or chunk.get("chunk_id"),
                "text": chunk.get("text") or "",
                "metadata": metadata,
            }
        )
    return documents


def build_shadow_index_plan(
    *,
    chunk_count: int | None = None,
    chunks: list[dict[str, Any]] | None = None,
    embedding_dim: int = 1536,
    vector_bytes: int = 4,
    index_overhead_ratio: float = 1.35,
    batch_size: int = 256,
    estimated_seconds_per_batch: float | None = None,
    collection: str = DEFAULT_JUDICIAL_COLLECTION,
) -> dict[str, Any]:
    if chunk_count is None:
        chunk_count = len(build_indexable_documents(chunks or []))
    vector_storage_bytes = int(chunk_count * embedding_dim * vector_bytes)
    total_estimated_bytes = int(vector_storage_bytes * index_overhead_ratio)
    batches = (chunk_count + batch_size - 1) // batch_size if chunk_count else 0
    estimated_embedding_runtime_seconds = (
        round(batches * estimated_seconds_per_batch, 3)
        if estimated_seconds_per_batch is not None
        else None
    )
    return {
        "collection": collection,
        "runtime_enabled": False,
        "chunk_count": chunk_count,
        "embedding_dim": embedding_dim,
        "vector_bytes": vector_bytes,
        "vector_storage_bytes": vector_storage_bytes,
        "index_overhead_ratio": index_overhead_ratio,
        "total_estimated_bytes": total_estimated_bytes,
        "batch_size": batch_size,
        "estimated_batches": batches,
        "estimated_embedding_runtime_seconds": estimated_embedding_runtime_seconds,
        "checkpoint_required": chunk_count > batch_size,
        "checkpoint_strategy": "persist batch cursor and completed chunk_key set before embedding writes",
        "resume_behavior": "skip existing chunk_key entries and resume from last committed batch",
        "metadata_filters": [
            "source_type",
            "source_authority",
            "court",
            "chamber",
            "decision_date",
            "year",
            "case_no",
            "esas_no",
            "decision_no",
            "karar_no",
            "citation_key",
            "canonical_decision_id",
            "related_law_refs",
        ],
        "status": "plan_only_no_embedding_started",
    }


def _terms(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9çğıöşü]{3,}", text.lower())}


@dataclass(slots=True)
class JudicialRetrievalLane:
    """Offline judicial retrieval lane; runtime use is disabled by default."""

    chunks: list[dict[str, Any]]
    collection: str = DEFAULT_JUDICIAL_COLLECTION
    runtime_enabled: bool | None = None

    def _runtime_enabled(self) -> bool:
        if self.runtime_enabled is not None:
            return self.runtime_enabled
        return judicial_runtime_enabled()

    def retrieve(
        self,
        *,
        query: str,
        top_k: int = 20,
        runtime: bool = False,
    ) -> tuple[list[RetrievalResult], RetrievalStats]:
        if runtime and not self._runtime_enabled():
            raise DisabledJudicialRuntimeError(
                "Judicial retrieval is disabled until judicial corpus closure gate passes."
            )

        t0 = time.perf_counter()
        query_terms = _terms(query)
        scored: list[tuple[int, int, dict[str, Any]]] = []
        for index, chunk in enumerate(self.chunks):
            text = str(chunk.get("text") or "")
            score = len(query_terms & _terms(text))
            scored.append((score, -index, chunk))
        scored.sort(reverse=True)

        selected = [chunk for score, _index, chunk in scored if score > 0][:top_k]
        if not selected:
            selected = [chunk for _score, _index, chunk in scored[:top_k]]

        results = [
            RetrievalResult(
                chunk_id=str(chunk.get("chunk_id") or (chunk.get("metadata") or {}).get("chunk_key") or ""),
                text=str(chunk.get("text") or ""),
                score=float(score),
                metadata=dict(chunk.get("metadata") or {}),
            )
            for score, _index, chunk in scored
            if chunk in selected
        ][:top_k]
        stats = RetrievalStats(
            collection=self.collection,
            query_preview=query[:80],
            top_k=top_k,
            filter_expr='metadata["source_type"] == "judicial_decision"',
            hit_count=len(results),
            latency_ms=(time.perf_counter() - t0) * 1000,
        )
        return results, stats


def _format_offline_result(
    *,
    text: str,
    metadata: dict[str, Any],
    score: float,
    lane: str,
) -> dict[str, Any]:
    return {
        "text": text,
        "selected_chunk_text": text,
        "citation_key": metadata.get("citation_key"),
        "court": metadata.get("court"),
        "chamber": metadata.get("chamber"),
        "decision_date": metadata.get("decision_date"),
        "esas_no": metadata.get("esas_no"),
        "karar_no": metadata.get("karar_no"),
        "paragraph_start": metadata.get("paragraph_start"),
        "paragraph_end": metadata.get("paragraph_end"),
        "source_url": metadata.get("source_url"),
        "score": score,
        "retrieval_score": score,
        "metadata_filters_applied": {},
        "retrieval_lane": lane,
        "lane": lane,
    }


@dataclass(slots=True)
class JudicialOfflineRetrievalPath:
    """Two-lane offline retrieval path; runtime calls remain fail-closed."""

    records: list[dict[str, Any]]
    chunks: list[dict[str, Any]]
    runtime_enabled: bool | None = None

    def _runtime_enabled(self) -> bool:
        if self.runtime_enabled is not None:
            return self.runtime_enabled
        return judicial_runtime_enabled()

    def retrieve_exact(
        self,
        *,
        key_type: str,
        key: str,
        top_k: int = 20,
        runtime: bool = False,
    ) -> list[dict[str, Any]]:
        if runtime and not self._runtime_enabled():
            raise DisabledJudicialRuntimeError(
                "Judicial retrieval is disabled until judicial corpus closure gate passes."
            )
        lookup = JudicialExactLookup.from_records(self.records)
        record = lookup.lookup(key_type, key)
        if record is None:
            return []
        canonical_id = record.get("canonical_decision_id")
        selected = [
            chunk
            for chunk in self.chunks
            if (chunk.get("metadata") or {}).get("canonical_decision_id") == canonical_id
        ][:top_k]
        return [
            _format_offline_result(
                text=str(chunk.get("text") or ""),
                metadata=dict(chunk.get("metadata") or {}),
                score=1.0,
                lane="exact",
            )
            for chunk in selected
        ]

    def retrieve_semantic(
        self,
        *,
        query: str,
        top_k: int = 20,
        runtime: bool = False,
    ) -> list[dict[str, Any]]:
        lane = JudicialRetrievalLane(
            chunks=self.chunks,
            runtime_enabled=self.runtime_enabled,
        )
        results, _stats = lane.retrieve(query=query, top_k=top_k, runtime=runtime)
        return [
            _format_offline_result(
                text=result.text,
                metadata=dict(result.metadata or {}),
                score=result.score,
                lane="semantic",
            )
            for result in results
        ]

    def retrieve(
        self,
        *,
        query: str,
        top_k: int = 20,
        exact_key_type: str | None = None,
        exact_key: str | None = None,
        runtime: bool = False,
    ) -> list[dict[str, Any]]:
        if exact_key_type and exact_key:
            exact_results = self.retrieve_exact(
                key_type=exact_key_type,
                key=exact_key,
                top_k=top_k,
                runtime=runtime,
            )
            if exact_results:
                return exact_results
        semantic_results = self.retrieve_semantic(query=query, top_k=top_k, runtime=runtime)
        if exact_key_type or exact_key:
            for result in semantic_results:
                result["retrieval_lane"] = "hybrid"
                result["lane"] = "hybrid"
        return semantic_results
