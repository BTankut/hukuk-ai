"""Embedding Service — RAG Katmanı için Embedding Soyutlama Katmanı.

EmbeddingService Protocol ile farklı embedding backend'lerini tek arabirim altında sunar:

    - HashingEmbedder: Test / geliştirme için deterministik hashing (ML bağımlılığı yok)
    - RemoteEmbeddingService: HTTP API (DGX vLLM /v1/embeddings, OpenAI-compatible)
    - SentenceTransformerEmbedder: Lokal sentence-transformers modeli

Faz 1 deployment mimarisi:
    - Production: RemoteEmbeddingService → DGX /v1/embeddings
    - Test / Offline: HashingEmbedder (deterministik, sabit boyut)
    - Lokal geliştirme: SentenceTransformerEmbedder (opsiyonel)

Env değişkenleri:
    EMBEDDING_BACKEND: "hashing" | "remote" | "local" (default: "hashing")
    EMBEDDING_DIM: int (default: 768)
    EMBEDDING_MODEL: model adı
    DGX_BASE_URL: HTTP endpoint
    DGX_API_KEY: auth token
"""

from __future__ import annotations

import hashlib
import logging
import math
import os
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_DIM = 1024
DEFAULT_EMBEDDING_MODEL = "intfloat/multilingual-e5-large-instruct"


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class EmbeddingService(Protocol):
    """Embedding servis protokolü — tüm implementasyonlar bu interface'i karşılar."""

    @property
    def dimension(self) -> int:
        """Embedding vektörünün boyutu."""
        ...

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Metin listesini vektör listesine dönüştür."""
        ...

    def embed_query(self, query: str) -> list[float]:
        """Tek bir sorgu metnini vektöre dönüştür."""
        ...


# ---------------------------------------------------------------------------
# HashingEmbedder — Test / Geliştirme
# ---------------------------------------------------------------------------


class HashingEmbedder:
    """Harici embedding servisi olmadan deterministik vektör üretir.

    data_pipeline.indexing.HashingEmbedder ile aynı algoritma — RAG katmanı
    için bağımsız kopya (çapraz bağımlılıktan kaçınmak için).

    Production'da KULLANILMAZ — sadece test ve pipeline doğrulama içindir.
    """

    def __init__(self, *, dimension: int = DEFAULT_EMBEDDING_DIM) -> None:
        if dimension <= 0:
            raise ValueError(f"dimension pozitif olmalı, alınan: {dimension}")
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_single(t) for t in texts]

    def embed_query(self, query: str) -> list[float]:
        return self._embed_single(query)

    def _embed_single(self, text: str) -> list[float]:
        buckets = [0.0] * self._dimension
        words = text.split()
        if not words:
            return buckets

        for word in words:
            digest = hashlib.sha256(word.lower().encode("utf-8")).digest()
            # 2-byte index → daha iyi dağılım
            idx = int.from_bytes(digest[:2], "big") % self._dimension
            value = (digest[2] / 255.0) * 2 - 1  # [-1, 1]
            buckets[idx] += value

        norm = math.sqrt(sum(x * x for x in buckets))
        if norm <= 0:
            return buckets

        return [x / norm for x in buckets]


# ---------------------------------------------------------------------------
# RemoteEmbeddingService — HTTP / DGX vLLM
# ---------------------------------------------------------------------------


class RemoteEmbeddingService:
    """OpenAI-compatible /v1/embeddings HTTP endpoint kullanan embedding servisi.

    DGX vLLM, Ollama veya başka bir HTTP embedding sunucusuna bağlanır.
    Faz 1 production embedding backend'i.
    """

    def __init__(
        self,
        *,
        base_url: str,
        model: str = DEFAULT_EMBEDDING_MODEL,
        api_key: str = "not-needed",
        dimension: int = DEFAULT_EMBEDDING_DIM,
        timeout: float = 30.0,
        batch_size: int = 64,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._dimension = dimension
        self._timeout = timeout
        self._batch_size = batch_size

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def endpoint(self) -> str:
        return f"{self._base_url}/embeddings"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        try:
            import httpx
        except ImportError as e:
            raise RuntimeError(
                "httpx gerekli: pip install httpx (pyproject.toml'da zaten var)"
            ) from e

        all_embeddings: list[list[float]] = []

        # Büyük batch'leri böl
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            batch_embeddings = self._call_api(batch, httpx=httpx)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    def embed_query(self, query: str) -> list[float]:
        # multilingual-e5-large-instruct için sorgu tarafında instruction prefix ekle
        # Doküman tarafı prefix'siz indekslendi → asimetrik retrieval doğru çalışır
        if "instruct" in self._model.lower():
            prefixed = (
                "Instruct: Verilen Türk hukuku sorusuna yanıt verebilecek ilgili kanun "
                "maddelerini bul.\nQuery: " + query
            )
        else:
            prefixed = query
        result = self.embed_texts([prefixed])
        return result[0] if result else [0.0] * self._dimension

    def _call_api(self, texts: list[str], *, httpx: Any) -> list[list[float]]:
        """API çağrısı yap ve embedding'leri döndür."""
        payload = {"input": texts, "model": self._model}
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(self.endpoint, json=payload, headers=headers)
                response.raise_for_status()
        except Exception as exc:
            raise RuntimeError(
                f"Embedding API hatası ({self.endpoint}): {exc}"
            ) from exc

        data = response.json()
        return [item["embedding"] for item in data["data"]]

    def health_check(self) -> dict[str, Any]:
        """Embedding servisinin erişilebilirliğini kontrol et."""
        try:
            import httpx
            test_emb = self.embed_texts(["health check"])
            return {
                "status": "ok",
                "endpoint": self.endpoint,
                "model": self._model,
                "dimension": len(test_emb[0]) if test_emb else "unknown",
            }
        except Exception as exc:
            return {"status": "error", "endpoint": self.endpoint, "error": str(exc)}

    @classmethod
    def from_env(cls) -> "RemoteEmbeddingService":
        """Env değişkenlerinden Remote Embedding Service oluştur."""
        return cls(
            base_url=os.getenv("EMBEDDING_BASE_URL", os.getenv("DGX_BASE_URL", "http://127.0.0.1:8081/v1")),
            model=os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
            api_key=os.getenv("DGX_API_KEY", "not-needed"),
            dimension=int(os.getenv("EMBEDDING_DIM", str(DEFAULT_EMBEDDING_DIM))),
            timeout=float(os.getenv("EMBEDDING_TIMEOUT", "30")),
        )


# ---------------------------------------------------------------------------
# SentenceTransformerEmbedder — Lokal model
# ---------------------------------------------------------------------------


class SentenceTransformerEmbedder:
    """Lokal sentence-transformers modeli ile embedding.

    DGX yokken veya lokal geliştirme/test ortamında kullanılabilir.
    sentence-transformers paketi kurulu olmalı.
    """

    def __init__(
        self,
        *,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
        device: str = "cpu",
        normalize: bool = True,
    ) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise RuntimeError(
                "sentence-transformers gerekli: pip install sentence-transformers"
            ) from e

        logger.info("SentenceTransformerEmbedder yükleniyor: %s (device=%s)", model_name, device)
        self._model = SentenceTransformer(model_name, device=device)
        self._normalize = normalize
        self._model_name = model_name
        raw_dim = self._model.get_sentence_embedding_dimension()
        self._dimension: int = raw_dim if raw_dim is not None else DEFAULT_EMBEDDING_DIM

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(texts, normalize_embeddings=self._normalize)
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_default_embedder(backend: str | None = None) -> Any:
    """Env değişkenine göre varsayılan embedder döndür.

    EMBEDDING_BACKEND env var:
        "hashing" → HashingEmbedder (test/offline, default)
        "remote"  → RemoteEmbeddingService (DGX/HTTP, Faz 1 production)
        "local"   → SentenceTransformerEmbedder (lokal model)
    """
    _backend = backend or os.getenv("EMBEDDING_BACKEND", "hashing")
    dim = int(os.getenv("EMBEDDING_DIM", str(DEFAULT_EMBEDDING_DIM)))

    if _backend == "remote":
        logger.info("Embedding backend: remote (DGX)")
        return RemoteEmbeddingService.from_env()

    if _backend == "local":
        model = os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
        logger.info("Embedding backend: local (%s)", model)
        return SentenceTransformerEmbedder(model_name=model)

    # Default: hashing (güvenli fallback)
    logger.debug("Embedding backend: hashing (dim=%d)", dim)
    return HashingEmbedder(dimension=dim)
