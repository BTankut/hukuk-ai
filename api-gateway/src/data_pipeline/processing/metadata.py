from __future__ import annotations

import re
from typing import Any

from data_pipeline.models import LawDocument

HUKUK_DALI_MAP = {
    "6098": "borclar_hukuku",
}


class LegalMetadataExtractor:
    """Madde/fıkra bazlı metadata çıkarımı."""

    def extract(self, *, document: LawDocument, madde_no: str, fikra_no: str) -> dict[str, Any]:
        return {
            "source_type": "mevzuat",
            "kanun_no": document.law_no,
            "kanun_adi": document.law_name,
            "kanun_kisa_adi": document.law_short_name,
            "madde_no": madde_no,
            "fikra_no": fikra_no,
            "hukuk_dali": HUKUK_DALI_MAP.get(document.law_no, "genel_hukuk"),
            "kaynak_url": document.source_url,
        }

    @staticmethod
    def parse_madde_no_from_text(text: str) -> str | None:
        match = re.search(r"madde\s*(\d+)", text, flags=re.IGNORECASE)
        return match.group(1) if match else None
