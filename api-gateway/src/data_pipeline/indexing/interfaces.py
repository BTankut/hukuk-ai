from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from data_pipeline.models import ChunkDocument


@dataclass(slots=True)
class VectorRecord:
    id: str
    text: str
    embedding: list[float]
    metadata: dict


class Embedder(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...


class VectorStore(Protocol):
    def upsert(self, *, collection: str, records: list[VectorRecord]) -> int: ...

    def count(self, *, collection: str) -> int: ...


class ChunkToRecordConverter:
    """Chunk + embedding listesini store record'larına dönüştürür."""

    @staticmethod
    def convert(chunks: list[ChunkDocument], embeddings: list[list[float]]) -> list[VectorRecord]:
        if len(chunks) != len(embeddings):
            raise ValueError("Chunk ve embedding sayısı eşleşmiyor.")

        records: list[VectorRecord] = []
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            records.append(
                VectorRecord(
                    id=chunk.chunk_id,
                    text=chunk.text,
                    embedding=embedding,
                    metadata=chunk.metadata,
                )
            )
        return records
