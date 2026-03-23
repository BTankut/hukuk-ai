from __future__ import annotations

import re
from typing import Any

from data_pipeline.models import ChunkMetadata, LawDocument

HUKUK_DALI_MAP = {
    "6098": "borclar_hukuku",
}


class LegalMetadataExtractor:
    """Madde/fıkra bazlı metadata çıkarımı."""

    @staticmethod
    def build_source_id(*, document: LawDocument, madde_no: str, fikra_no: str) -> str:
        law_short_name = document.law_short_name or document.law_no or "unknown_law"
        return f"{law_short_name} m.{madde_no}"

    def extract(
        self,
        *,
        document: LawDocument,
        madde_no: str,
        fikra_no: str,
        chunk_id: str | None = None,
        source_id: str | None = None,
        yururluk_baslangic: str | None = None,
        yururluk_bitis: str | None = None,
        mulga: bool | None = None,
    ) -> ChunkMetadata:
        canonical_source_id = source_id or self.build_source_id(
            document=document,
            madde_no=madde_no,
            fikra_no=fikra_no,
        )

        metadata: ChunkMetadata = {
            "source_type": "mevzuat",
            "source_id": canonical_source_id,
            "chunk_id": chunk_id,
            "law_no": document.law_no,
            "law_short_name": document.law_short_name,
            "kanun_no": document.law_no,
            "kanun_adi": document.law_name,
            "kanun_kisa_adi": document.law_short_name,
            "madde_no": madde_no,
            "fikra_no": fikra_no,
            "yururluk_baslangic": yururluk_baslangic,
            "yururluk_bitis": yururluk_bitis,
            "mulga": mulga,
            "hukuk_dali": HUKUK_DALI_MAP.get(document.law_no, "genel_hukuk"),
            "kaynak_url": document.source_url,
        }

        return metadata

    @staticmethod
    def parse_madde_no_from_text(text: str) -> str | None:
        match = re.search(r"madde\s*(\d+)", text, flags=re.IGNORECASE)
        return match.group(1) if match else None
