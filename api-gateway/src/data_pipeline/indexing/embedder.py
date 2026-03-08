from __future__ import annotations

import hashlib
import math


class HashingEmbedder:
    """Harici embedding servisi yokken deterministik smoke embedder.

    Gerçek production embedding'i temsil etmez; sadece pipeline akışını
    doğrulamak için kullanılır.
    """

    def __init__(self, *, dimension: int = 16) -> None:
        if dimension <= 0:
            raise ValueError("dimension pozitif olmalı")
        self.dimension = dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_single(text) for text in texts]

    def _embed_single(self, text: str) -> list[float]:
        buckets = [0.0] * self.dimension
        words = text.split()
        if not words:
            return buckets

        for word in words:
            digest = hashlib.sha256(word.lower().encode("utf-8")).digest()
            idx = digest[0] % self.dimension
            value = (digest[1] / 255.0) * 2 - 1
            buckets[idx] += value

        norm = math.sqrt(sum(x * x for x in buckets))
        if norm <= 0:
            return buckets

        return [x / norm for x in buckets]
