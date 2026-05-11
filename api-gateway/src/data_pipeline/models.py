from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TypedDict


class ChunkMetadata(TypedDict, total=False):
    source_type: str
    source_id: str
    chunk_id: str
    law_no: str
    law_short_name: str
    kanun_no: str
    kanun_kisa_adi: str
    kanun_adi: str
    madde_no: str
    fikra_no: str
    yururluk_baslangic: str | None
    yururluk_bitis: str | None
    mulga: bool | None
    hukuk_dali: str
    kaynak_url: str | None
    article_heading: str
    chunk_part: int
    chunk_part_total: int
    canonical_decision_id: str
    citation_key: str
    source_authority: str
    court: str
    chamber: str
    decision_date: str
    case_no: str
    esas_no: str
    decision_no: str
    karar_no: str
    paragraph_index: int
    paragraph_start: int
    paragraph_end: int
    source_url: str
    document_hash: str
    normalized_text_hash: str
    chunk_hash: str
    chunk_key: str
    duplicate_status: str


@dataclass(slots=True)
class LawArticle:
    madde_no: str
    heading: str
    body: str
    yururluk_baslangic: str | None = None
    yururluk_bitis: str | None = None
    mulga: bool | None = None


@dataclass(slots=True)
class LawDocument:
    law_no: str
    law_short_name: str
    law_name: str
    source_url: str | None
    fetched_at: datetime
    raw_text: str
    articles: list[LawArticle]


@dataclass(slots=True)
class ChunkDocument:
    chunk_id: str
    text: str
    metadata: ChunkMetadata = field(default_factory=dict)


@dataclass(slots=True)
class IndexedDocument:
    doc_id: str
    text: str
    embedding: list[float]
    metadata: ChunkMetadata


@dataclass(slots=True)
class IngestSummary:
    source_kind: str
    source_url: str | None
    law_no: str
    article_count: int
    chunk_count: int
    indexed_count: int
    warnings: list[str] = field(default_factory=list)
