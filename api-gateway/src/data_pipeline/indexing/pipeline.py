from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from data_pipeline.indexing.interfaces import ChunkToRecordConverter, Embedder, VectorStore
from data_pipeline.loaders import TBKMevzuatLoader
from data_pipeline.models import ChunkDocument, IngestSummary
from data_pipeline.processing import LegalChunker


@dataclass(slots=True)
class TBKIngestPipeline:
    loader: TBKMevzuatLoader
    chunker: LegalChunker
    embedder: Embedder
    vector_store: VectorStore
    collection_name: str = "mevzuat"

    def run(
        self,
        *,
        prefer_online: bool = True,
        fixture_path: str | Path | None = None,
        html_cache_path: str | Path | None = None,
    ) -> tuple[IngestSummary, list[ChunkDocument]]:
        load_result = self.loader.load(
            prefer_online=prefer_online,
            fixture_path=fixture_path,
            html_cache_path=html_cache_path,
        )
        document = load_result.document

        chunks = self.chunker.chunk_document(document)
        texts = [chunk.text for chunk in chunks]
        embeddings = self.embedder.embed_texts(texts)
        records = ChunkToRecordConverter.convert(chunks, embeddings)

        indexed_count = self.vector_store.upsert(collection=self.collection_name, records=records)

        summary = IngestSummary(
            source_kind=load_result.source_kind,
            source_url=document.source_url,
            law_no=document.law_no,
            article_count=len(document.articles),
            chunk_count=len(chunks),
            indexed_count=indexed_count,
            warnings=load_result.warnings,
        )
        return summary, chunks
