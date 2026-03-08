"""Cross-encoder reranker — Faz 1 RAG pipeline.

Faz 1 frozen scope (D-2):
    Karar: Cross-encoder, CPU inference (M4 Max).
    Primary candidate: cross-encoder/mmarco-mMiniLMv2-L12-H384-v1

    Threshold: 0.7 (default). Grid search ile 0.5/0.6/0.7 test edilir
    (bkz. evaluation/reranker_ab_eval.py).

A/B spike için desteklenen modeller:
    MODEL_A = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"  # Çok dilli, primary
    MODEL_B = "cross-encoder/ms-marco-MiniLM-L-6-v2"         # İngilizce baseline
    MODEL_C = "BAAI/bge-reranker-v2-m3"                       # Güçlü alternatif (yedek)

Bağımlılık:
    sentence-transformers>=3.0.0   (pyproject.toml'e eklendi)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Faz 1 model sabit listesi — değiştirmek için koordinatör onayı gerekir
# ---------------------------------------------------------------------------

MODEL_A = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"  # D-2 primary
MODEL_B = "cross-encoder/ms-marco-MiniLM-L-6-v2"         # İngilizce kontrol grubu
MODEL_C = "BAAI/bge-reranker-v2-m3"                       # Yedek — A başarısız olursa

FAZ1_DEFAULT_MODEL = MODEL_A
FAZ1_DEFAULT_THRESHOLD = 0.7
FAZ1_TOP_K = 5  # top-20 → top-5


@dataclass(slots=True)
class RankedResult:
    text: str
    citation: str
    score: float
    source: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(slots=True)
class RerankerStats:
    model_id: str
    threshold: float
    input_count: int
    output_count: int           # threshold geçen
    top_k_count: int            # final top-k
    latency_ms: float
    scores: list[float] = field(default_factory=list)

    @property
    def filter_rate(self) -> float:
        """Threshold tarafından elenen oranı (0.0-1.0)."""
        if self.input_count == 0:
            return 0.0
        return 1.0 - (self.output_count / self.input_count)


class Reranker:
    """Sentence-Transformers CrossEncoder wrapper.

    Lazy-load: model ilk çağrıda yüklenir. M4 Max CPU'da
    mmarco-mMiniLMv2-L12-H384-v1 için ilk yükleme ~4s,
    sonraki her batch ~200ms (10 passage).
    """

    def __init__(
        self,
        model_id: str = FAZ1_DEFAULT_MODEL,
        threshold: float = FAZ1_DEFAULT_THRESHOLD,
        top_k: int = FAZ1_TOP_K,
        device: str = "cpu",
    ) -> None:
        self.model_id = model_id
        self.threshold = threshold
        self.top_k = top_k
        self.device = device
        self._model = None  # lazy-loaded

    def _load_model(self):
        """İlk kullanımda model yükle."""
        if self._model is not None:
            return
        try:
            from sentence_transformers import CrossEncoder  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers kurulu değil. "
                "pip install sentence-transformers>=3.0.0"
            ) from exc

        logger.info("Reranker modeli yükleniyor: %s (device=%s)", self.model_id, self.device)
        t0 = time.perf_counter()
        self._model = CrossEncoder(self.model_id, device=self.device)
        logger.info("Reranker yüklendi: %.1fs", time.perf_counter() - t0)

    def rerank(
        self,
        query: str,
        candidates: list[dict],
        *,
        threshold: float | None = None,
        top_k: int | None = None,
    ) -> tuple[list[RankedResult], RerankerStats]:
        """
        Adayları rerank et.

        Args:
            query: Kullanıcı sorgusu
            candidates: [{"text": str, "citation": str, "source"?: str, ...}]
            threshold: Override; None → self.threshold
            top_k: Override; None → self.top_k

        Returns:
            (ranked_results, stats)
            ranked_results: Threshold geçen ve top_k ile kırpılmış sonuçlar
            stats: Latency, filter rate vb.
        """
        self._load_model()

        _threshold = threshold if threshold is not None else self.threshold
        _top_k = top_k if top_k is not None else self.top_k

        if not candidates:
            stats = RerankerStats(
                model_id=self.model_id,
                threshold=_threshold,
                input_count=0,
                output_count=0,
                top_k_count=0,
                latency_ms=0.0,
            )
            return [], stats

        pairs = [[query, c["text"]] for c in candidates]

        t0 = time.perf_counter()
        raw_scores: list[float] = self._model.predict(pairs).tolist()
        latency_ms = (time.perf_counter() - t0) * 1000

        scored = sorted(
            zip(raw_scores, candidates),
            key=lambda x: x[0],
            reverse=True,
        )

        above_threshold = [
            (score, c) for score, c in scored if score >= _threshold
        ]
        final = above_threshold[:_top_k]

        results = [
            RankedResult(
                text=c["text"],
                citation=c.get("citation", ""),
                score=score,
                source=c.get("source"),
                metadata=c.get("metadata", {}),
            )
            for score, c in final
        ]

        stats = RerankerStats(
            model_id=self.model_id,
            threshold=_threshold,
            input_count=len(candidates),
            output_count=len(above_threshold),
            top_k_count=len(results),
            latency_ms=latency_ms,
            scores=raw_scores,
        )

        logger.debug(
            "Rerank: model=%s thr=%.1f input=%d above_thr=%d top_k=%d latency=%.0fms",
            self.model_id,
            _threshold,
            len(candidates),
            len(above_threshold),
            len(results),
            latency_ms,
        )

        return results, stats


# ---------------------------------------------------------------------------
# Singleton factory — production kullanımı için
# ---------------------------------------------------------------------------
_reranker_instance: Reranker | None = None


def get_reranker() -> Reranker:
    """Process-wide singleton. Config'den model ve threshold okur."""
    global _reranker_instance
    if _reranker_instance is None:
        import os
        model_id = os.getenv("RERANKER_MODEL", FAZ1_DEFAULT_MODEL)
        threshold = float(os.getenv("RERANKER_THRESHOLD", str(FAZ1_DEFAULT_THRESHOLD)))
        _reranker_instance = Reranker(model_id=model_id, threshold=threshold)
    return _reranker_instance
