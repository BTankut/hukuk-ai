"""RAG Retriever — Faz 1 Mevzuat Retrieval Katmanı.

Faz 1 frozen scope:
    - dense-only retrieval + metadata filter
    - Milvus backend (pymilvus)
    - MockRetriever: test / no-Milvus ortamı için

Metadata filter'lanabilir alanlar (Milvus JSON field'dan):
    - law_no: Kanun numarası ("6098", "4721", ...)
    - law_short_name: Kısa kanun adı ("TBK", "TMK", ...)
    - madde_no: Madde numarası ("1", "23", ...)
    - fikra_no: Fıkra numarası ("1", "2", ...)
    - domain: Hukuk alanı ("sozlesmeler", "borclar_hukuku", ...)
    - mülga: Mülga madde mi? (True/False) — Faz 1'de her zaman False

NOT: Milvus JSON field üzerinden filtreleme JSON path expr ile yapılır.
    Desteklenen operator'lar: eq, ne, gt, gte, lt, lte, in, not_in.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sabitler — backlog-draft.md "Frozen Scope Faz 1" ile uyumlu
# ---------------------------------------------------------------------------

DEFAULT_TOP_K = 20          # Reranker'a gidecek candidate sayısı
DEFAULT_EMBEDDING_DIM = 16  # HashingEmbedder varsayılanı (production'da farklı)
MILVUS_METRIC_TYPE = "COSINE"


# ---------------------------------------------------------------------------
# Metadata Filter
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class MetadataFilter:
    """Retrieval için metadata filtresi.

    Tüm alanlar opsiyonel. None → filtre uygulanmaz.
    """

    law_no: str | None = None           # "6098" (TBK), "4721" (TMK), ...
    law_short_name: str | None = None   # "TBK", "TMK", "TCK", ...
    madde_no: str | None = None         # Belirli bir madde
    fikra_no: str | None = None         # Belirli bir fıkra
    domain: str | None = None           # Hukuk alanı (serbest metin)
    mulga: bool | None = None           # Mülga madde filtresi — None = filtre yok (alan Milvus'ta yoksa)
    belge_turu: str | None = None       # "kanun", "tuzuk", "yonetmelik", ...
    source_family: str | None = None    # normalize edilmiş source family

    # Madde aralığı filtresi
    madde_no_min: int | None = None     # Madde no ≥ min
    madde_no_max: int | None = None     # Madde no ≤ max

    def to_milvus_expr(self) -> str | None:
        """Milvus JSON field filter expression'a dönüştür.

        Milvus syntax: metadata["field"] == value
        """
        clauses: list[str] = []

        if self.law_no is not None:
            # Hem İngilizce (law_no) hem Türkçe (kanun_no) alan adı desteği
            clauses.append(
                f'(metadata["law_no"] == "{self.law_no}" || metadata["kanun_no"] == "{self.law_no}")'
            )

        if self.law_short_name is not None:
            # Hem İngilizce (law_short_name) hem Türkçe (kanun_kisa_adi) alan adı desteği
            clauses.append(
                f'(metadata["law_short_name"] == "{self.law_short_name}" || metadata["kanun_kisa_adi"] == "{self.law_short_name}")'
            )

        if self.madde_no is not None:
            clauses.append(f'metadata["madde_no"] == "{self.madde_no}"')

        if self.fikra_no is not None:
            clauses.append(f'metadata["fikra_no"] == "{self.fikra_no}"')

        if self.domain is not None:
            clauses.append(
                f'(metadata["domain"] == "{self.domain}" || metadata["hukuk_dali"] == "{self.domain}")'
            )

        if self.belge_turu is not None:
            clauses.append(
                f'(metadata["belge_turu"] == "{self.belge_turu}" || metadata["source_family"] == "{self.belge_turu}" || metadata["source_type"] == "{self.belge_turu}")'
            )

        if self.source_family is not None:
            clauses.append(
                f'(metadata["source_family"] == "{self.source_family}" || metadata["belge_turu"] == "{self.source_family}" || metadata["raw_source_family"] == "{self.source_family}")'
            )

        if self.mulga is not None:
            mulga_val = "true" if self.mulga else "false"
            clauses.append(f'metadata["mulga"] == {mulga_val}')

        if self.madde_no_min is not None:
            clauses.append(f'metadata["madde_no_int"] >= {self.madde_no_min}')

        if self.madde_no_max is not None:
            clauses.append(f'metadata["madde_no_int"] <= {self.madde_no_max}')

        if not clauses:
            return None

        return " && ".join(clauses)

    def is_empty(self) -> bool:
        """Tüm filtre alanları boşsa True."""
        return self.to_milvus_expr() is None


# ---------------------------------------------------------------------------
# Retrieval Result
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class RetrievalResult:
    """Tek bir retrieved chunk ve ilgili metadata."""

    chunk_id: str
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def law_no(self) -> str | None:
        # Hem İngilizce hem Türkçe alan adlarını destekle
        return self.metadata.get("law_no") or self.metadata.get("kanun_no")

    @property
    def law_short_name(self) -> str | None:
        # Hem İngilizce hem Türkçe alan adlarını destekle
        return self.metadata.get("law_short_name") or self.metadata.get("kanun_kisa_adi")

    @property
    def madde_no(self) -> str | None:
        return self.metadata.get("madde_no")

    @property
    def fikra_no(self) -> str | None:
        return self.metadata.get("fikra_no")

    @property
    def citation(self) -> str:
        """Otomatik citation formatı: 'TBK m.23/f.1'."""
        parts = []
        name = self.law_short_name or self.law_no or "?"
        madde = self.madde_no
        fikra = self.fikra_no

        if madde:
            if fikra and fikra != "1":
                parts.append(f"{name} m.{madde}/f.{fikra}")
            else:
                parts.append(f"{name} m.{madde}")
        else:
            parts.append(name)

        return " ".join(parts)

    def to_candidate_dict(self) -> dict[str, Any]:
        """Reranker'ın beklediği format."""
        return {
            "text": self.text,
            "citation": self.citation,
            "source": self.law_short_name or self.law_no,
            "score": self.score,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Retrieval Stats
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class RetrievalStats:
    collection: str
    query_preview: str
    top_k: int
    filter_expr: str | None
    hit_count: int
    latency_ms: float


# ---------------------------------------------------------------------------
# Mock Retriever (test / offline kullanım)
# ---------------------------------------------------------------------------

class MockRetriever:
    """Milvus bağlantısı olmadan çalışan bellek içi retriever.

    Test fixture'ları veya smoke testleri için kullanılır.
    """

    def __init__(self, *, fixture_chunks: list[dict[str, Any]] | None = None) -> None:
        self._chunks: list[dict[str, Any]] = fixture_chunks or []

    def add_chunks(self, chunks: list[dict[str, Any]]) -> None:
        """Chunk ekle: {"id", "text", "embedding", "metadata"}."""
        self._chunks.extend(chunks)

    def retrieve(
        self,
        *,
        query_vector: list[float],
        collection: str = "mock",
        top_k: int = DEFAULT_TOP_K,
        metadata_filter: MetadataFilter | None = None,
    ) -> tuple[list[RetrievalResult], RetrievalStats]:
        t0 = time.perf_counter()

        # Metadata filter uygula (in-memory)
        candidates = self._chunks
        if metadata_filter and not metadata_filter.is_empty():
            candidates = [c for c in candidates if self._matches_filter(c, metadata_filter)]

        # Cosine similarity hesapla
        scored: list[tuple[float, dict]] = []
        for chunk in candidates:
            emb = chunk.get("embedding", [])
            score = self._cosine(query_vector, emb) if emb else 0.0
            scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_k]

        results = [
            RetrievalResult(
                chunk_id=c.get("id", ""),
                text=c.get("text", ""),
                score=s,
                metadata=c.get("metadata", {}),
            )
            for s, c in top
        ]

        latency_ms = (time.perf_counter() - t0) * 1000

        stats = RetrievalStats(
            collection=collection,
            query_preview=str(query_vector[:2]) + "...",
            top_k=top_k,
            filter_expr=metadata_filter.to_milvus_expr() if metadata_filter else None,
            hit_count=len(results),
            latency_ms=latency_ms,
        )

        return results, stats

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a <= 0 or norm_b <= 0:
            return 0.0
        return dot / (norm_a * norm_b)

    @staticmethod
    def _matches_filter(chunk: dict[str, Any], f: MetadataFilter) -> bool:
        meta = chunk.get("metadata", {})

        if f.law_no is not None and meta.get("law_no") != f.law_no:
            return False
        if f.law_short_name is not None and meta.get("law_short_name") != f.law_short_name:
            return False
        if f.madde_no is not None and meta.get("madde_no") != f.madde_no:
            return False
        if f.fikra_no is not None and meta.get("fikra_no") != f.fikra_no:
            return False
        if f.domain is not None and meta.get("domain") != f.domain:
            return False
        if f.belge_turu is not None:
            belge_turu = meta.get("belge_turu") or meta.get("source_family") or meta.get("source_type")
            if belge_turu != f.belge_turu:
                return False
        if f.source_family is not None:
            source_family = meta.get("source_family") or meta.get("belge_turu") or meta.get("raw_source_family")
            if source_family != f.source_family:
                return False
        if f.mulga is not None and meta.get("mulga", False) != f.mulga:
            return False
        if f.madde_no_min is not None:
            try:
                if int(meta.get("madde_no", 0)) < f.madde_no_min:
                    return False
            except (ValueError, TypeError):
                return False
        if f.madde_no_max is not None:
            try:
                if int(meta.get("madde_no", 0)) > f.madde_no_max:
                    return False
            except (ValueError, TypeError):
                return False

        return True


# ---------------------------------------------------------------------------
# Milvus Retriever
# ---------------------------------------------------------------------------

class MilvusRetriever:
    """Milvus dense retrieval + metadata filter.

    Embedding servisi dışarıdan enjekte edilir (embedder.embed_texts / embed_query).

    Kullanım (production):
        retriever = MilvusRetriever.from_env()
        results, stats = retriever.retrieve(query="haksız fiil tazminatı")

    Kullanım (test):
        retriever = MilvusRetriever(
            client=mock_client,
            embedder=HashingEmbedder(),
            collection="test_coll",
        )
    """

    def __init__(
        self,
        *,
        client: Any,
        embedder: Any,
        collection: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> None:
        self.client = client
        self.embedder = embedder
        self.collection = collection
        self.top_k = top_k

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_env(
        cls,
        *,
        collection: str | None = None,
        top_k: int = DEFAULT_TOP_K,
        embedder: Any = None,
    ) -> "MilvusRetriever":
        """Env değişkenlerinden MilvusRetriever oluştur.

        Env değişkenleri:
            MILVUS_URI: Milvus endpoint (default: http://localhost:19530)
            MILVUS_TOKEN: Auth token (default: boş)
            MILVUS_COLLECTION: Collection adı (default: hukuk_chunks)
            EMBEDDING_BACKEND: "hashing" | "remote" | "local" (default: hashing)
        """
        from rag.embedding import get_default_embedder

        milvus_uri = os.getenv("MILVUS_URI", "http://localhost:19530")
        milvus_token = os.getenv("MILVUS_TOKEN") or None
        coll = collection or os.getenv("MILVUS_COLLECTION", "hukuk_chunks")
        _embedder = embedder if embedder is not None else get_default_embedder()

        try:
            from pymilvus import MilvusClient

            kwargs: dict[str, Any] = {"uri": milvus_uri}
            if milvus_token:
                kwargs["token"] = milvus_token
            client = MilvusClient(**kwargs)
            logger.info(
                "MilvusRetriever.from_env: uri=%s collection=%s embedding_backend=%s",
                milvus_uri,
                coll,
                os.getenv("EMBEDDING_BACKEND", "hashing"),
            )
        except ImportError as exc:
            raise RuntimeError(
                "pymilvus kurulu değil: pip install 'hukuk-ai-api-gateway[milvus]'"
            ) from exc

        return cls(client=client, embedder=_embedder, collection=coll, top_k=top_k)

    # ------------------------------------------------------------------
    # Health Check
    # ------------------------------------------------------------------

    def health_check(self) -> dict[str, Any]:
        """Milvus bağlantısını ve collection durumunu kontrol et.

        Returns:
            {
                "status": "ok" | "error",
                "collection": str,
                "num_entities": int,
                "index_status": str,
                "error": str (varsa),
            }
        """
        result: dict[str, Any] = {"collection": self.collection}

        try:
            # Collection varlığı
            has_coll = self.client.has_collection(collection_name=self.collection)
            if not has_coll:
                return {
                    **result,
                    "status": "error",
                    "error": f"Collection '{self.collection}' bulunamadı",
                }

            # Entity sayısı
            stats = self.client.get_collection_stats(collection_name=self.collection)
            num_entities = int(stats.get("row_count", stats.get("num_entities", -1)))

            result.update(
                {
                    "status": "ok",
                    "num_entities": num_entities,
                    "index_status": "ready",
                }
            )
            logger.info(
                "Milvus health OK: collection=%s entities=%d",
                self.collection,
                num_entities,
            )
        except Exception as exc:
            result.update({"status": "error", "error": str(exc)})
            logger.warning("Milvus health check başarısız: %s", exc)

        return result

    # ------------------------------------------------------------------
    # Retrieve
    # ------------------------------------------------------------------

    def retrieve(
        self,
        *,
        query: str,
        top_k: int | None = None,
        metadata_filter: MetadataFilter | None = None,
    ) -> tuple[list[RetrievalResult], RetrievalStats]:
        """Sorguyu embed et, Milvus'tan top-k chunk çek.

        Args:
            query: Kullanıcı sorgusu (ham metin)
            top_k: Override; None → self.top_k
            metadata_filter: Opsiyonel metadata filtresi

        Returns:
            (results, stats)
        """
        _top_k = top_k if top_k is not None else self.top_k
        filter_expr = metadata_filter.to_milvus_expr() if metadata_filter else None

        # Query embedding — embed_query (single text) varsa tercih et
        t0 = time.perf_counter()
        if hasattr(self.embedder, "embed_query"):
            query_vector = self.embedder.embed_query(query)
        else:
            query_vector = self.embedder.embed_texts([query])[0]

        search_kwargs: dict[str, Any] = {
            "collection_name": self.collection,
            "data": [query_vector],
            "limit": _top_k,
            "output_fields": ["id", "text", "metadata"],
        }

        if filter_expr:
            search_kwargs["filter"] = filter_expr

        search_result = self.client.search(**search_kwargs)
        latency_ms = (time.perf_counter() - t0) * 1000

        results = self._parse_search_result(search_result)

        stats = RetrievalStats(
            collection=self.collection,
            query_preview=query[:80],
            top_k=_top_k,
            filter_expr=filter_expr,
            hit_count=len(results),
            latency_ms=latency_ms,
        )

        logger.debug(
            "Retrieve: collection=%s top_k=%d filter=%r hits=%d latency=%.0fms",
            self.collection,
            _top_k,
            filter_expr,
            len(results),
            latency_ms,
        )

        return results, stats

    @staticmethod
    def _parse_search_result(search_result: Any) -> list[RetrievalResult]:
        """Milvus search response'u RetrievalResult listesine dönüştür."""
        results: list[RetrievalResult] = []

        if not search_result:
            return results

        first_batch = search_result[0] if isinstance(search_result, list) else []
        if not first_batch:
            return results

        for hit in first_batch:
            if isinstance(hit, dict):
                chunk_id = str(hit.get("id", ""))
                score = float(hit.get("distance", hit.get("score", 0.0)))
                entity = hit.get("entity", hit)
            else:
                # Obje tabanlı hit formatı
                chunk_id = str(getattr(hit, "id", ""))
                score = float(getattr(hit, "distance", getattr(hit, "score", 0.0)))
                entity = getattr(hit, "entity", {})

            text = entity.get("text", "") if isinstance(entity, dict) else ""
            metadata = entity.get("metadata", {}) if isinstance(entity, dict) else {}
            if not isinstance(metadata, dict):
                metadata = {}

            results.append(
                RetrievalResult(
                    chunk_id=chunk_id,
                    text=text,
                    score=score,
                    metadata=metadata,
                )
            )

        return results
