from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from typing import Any

from rag.retriever import RetrievalResult, RetrievalStats


JUDICIAL_RUNTIME_ENABLED_ENV = "JUDICIAL_RUNTIME_ENABLED"
DEFAULT_JUDICIAL_COLLECTION = "judicial_decisions_pending"


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


def build_indexable_documents(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for chunk in chunks:
        metadata = dict(chunk.get("metadata") or {})
        documents.append(
            {
                "id": metadata.get("chunk_key") or chunk.get("chunk_id"),
                "text": chunk.get("text") or "",
                "metadata": metadata,
            }
        )
    return documents


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
