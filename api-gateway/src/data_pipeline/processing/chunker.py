from __future__ import annotations

from dataclasses import dataclass, field
import re

from data_pipeline.models import ChunkDocument, LawArticle, LawDocument
from data_pipeline.processing.metadata import LegalMetadataExtractor


@dataclass(slots=True)
class LegalChunker:
    """Hukuki metinleri madde/fıkra odaklı chunk'lar.

    Tokenizer bağımlılığı eklememek için kelime bazlı yaklaşık chunking uygulanır.
    """

    max_words: int = 180
    overlap_words: int = 24
    metadata_extractor: LegalMetadataExtractor = field(default_factory=LegalMetadataExtractor)

    def chunk_document(self, document: LawDocument) -> list[ChunkDocument]:
        chunks: list[ChunkDocument] = []

        for article in document.articles:
            fikralar = self._split_fikralar(article)
            for fikra_no, fikra_text in fikralar:
                parts = self._split_long_text(fikra_text)
                for idx, part in enumerate(parts, start=1):
                    suffix = "" if len(parts) == 1 else f"_p{idx}"
                    chunk_id = f"{document.law_short_name}_m{article.madde_no}_f{fikra_no}{suffix}"
                    source_id = self.metadata_extractor.build_source_id(
                        document=document,
                        madde_no=article.madde_no,
                        fikra_no=fikra_no,
                    )
                    metadata = self.metadata_extractor.extract(
                        document=document,
                        madde_no=article.madde_no,
                        fikra_no=fikra_no,
                        chunk_id=chunk_id,
                        source_id=source_id,
                        yururluk_baslangic=article.yururluk_baslangic,
                        yururluk_bitis=article.yururluk_bitis,
                        mulga=article.mulga,
                    )
                    metadata["article_heading"] = article.heading
                    metadata["chunk_part"] = idx
                    metadata["chunk_part_total"] = len(parts)

                    # Chunk text'ine madde başlığı + numarasını ekle
                    # → Embedding kalitesini artırır; fragmentary chunk sorununu düzeltir.
                    law_prefix = f"{document.law_short_name} m.{article.madde_no}"
                    if article.heading and article.heading.strip():
                        chunk_text = f"{law_prefix} - {article.heading.strip()}\n{part}"
                    else:
                        chunk_text = f"{law_prefix}\n{part}"

                    chunks.append(
                        ChunkDocument(
                            chunk_id=chunk_id,
                            text=chunk_text,
                            metadata=metadata,
                        )
                    )

        return chunks

    @staticmethod
    def _split_fikralar(article: LawArticle) -> list[tuple[str, str]]:
        pattern = re.compile(r"\((\d+)\)\s*(.*?)(?=(?:\(\d+\))|\Z)", flags=re.DOTALL)
        matches = pattern.findall(article.body)
        if not matches:
            cleaned = article.body.strip()
            return [("1", cleaned)] if cleaned else []

        fikralar: list[tuple[str, str]] = []
        for fikra_no, fikra_text in matches:
            normalized = " ".join(fikra_text.strip().split())
            if normalized:
                fikralar.append((fikra_no, normalized))
        return fikralar

    def _split_long_text(self, text: str) -> list[str]:
        words = text.split()
        if len(words) <= self.max_words:
            return [text.strip()]

        result: list[str] = []
        step = max(1, self.max_words - self.overlap_words)
        start = 0
        while start < len(words):
            end = min(start + self.max_words, len(words))
            result.append(" ".join(words[start:end]))
            if end >= len(words):
                break
            start += step

        return result
