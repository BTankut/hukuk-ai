from __future__ import annotations

from collections import defaultdict
from typing import Any

from data_pipeline.indexing.interfaces import VectorRecord


class InMemoryVectorStore:
    """Milvus yerine smoke/test için kullanılan basit in-memory store."""

    def __init__(self) -> None:
        self._collections: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)

    def upsert(self, *, collection: str, records: list[VectorRecord]) -> int:
        bucket = self._collections[collection]
        for record in records:
            bucket[record.id] = {
                "id": record.id,
                "text": record.text,
                "embedding": record.embedding,
                "metadata": record.metadata,
            }
        return len(records)

    def count(self, *, collection: str) -> int:
        return len(self._collections.get(collection, {}))

    def dump_collection(self, *, collection: str) -> list[dict[str, Any]]:
        return list(self._collections.get(collection, {}).values())


class MilvusVectorStore:
    """Milvus entegrasyon arayüzü (client dışarıdan enjekte edilir).

    Not: Faz 1 TBK spike için gerçek Milvus bağlantısı opsiyonel.
    Bu sınıf, testlerde fake client ile contract doğrulamak için eklendi.
    """

    def __init__(self, *, client: Any) -> None:
        self.client = client

    def upsert(self, *, collection: str, records: list[VectorRecord]) -> int:
        payload = [
            {
                "id": record.id,
                "text": record.text,
                "embedding": record.embedding,
                "metadata": record.metadata,
            }
            for record in records
        ]
        self.client.upsert(collection_name=collection, data=payload)
        return len(payload)

    def count(self, *, collection: str) -> int:
        if hasattr(self.client, "count"):
            return int(self.client.count(collection_name=collection))

        if hasattr(self.client, "get_collection_stats"):
            stats = self.client.get_collection_stats(collection_name=collection)
            if isinstance(stats, dict) and "row_count" in stats:
                return int(stats["row_count"])

        raise AttributeError("Milvus client count API bulunamadı (count/get_collection_stats).")
