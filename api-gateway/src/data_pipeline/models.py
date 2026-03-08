from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class LawArticle:
    madde_no: str
    heading: str
    body: str


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
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class IndexedDocument:
    doc_id: str
    text: str
    embedding: list[float]
    metadata: dict[str, Any]


@dataclass(slots=True)
class IngestSummary:
    source_kind: str
    source_url: str | None
    law_no: str
    article_count: int
    chunk_count: int
    indexed_count: int
    warnings: list[str] = field(default_factory=list)
