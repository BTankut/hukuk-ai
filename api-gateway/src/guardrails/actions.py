from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from config import Settings

try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
except Exception:  # pragma: no cover - optional during local skeleton setup
    AnalyzerEngine = None
    AnonymizerEngine = None


CITATION_PATTERN = re.compile(r"\[Kaynak:\s*([^\]]+)\]")
TR_ID_PATTERN = re.compile(r"\b\d{11}\b")

# Presidio'nun yanlışlıkla maskelemesini önlemek için citation marker'ları
# maskeleme öncesinde placeholder ile değiştirilir, sonra geri yüklenir.
_CITE_PLACEHOLDER_TPL = "CITATIONPLACEHOLDER{i}"
_CITE_PLACEHOLDER_RE = re.compile(r"CITATIONPLACEHOLDER(\d+)")


@dataclass(slots=True)
class PresidioMasker:
    settings: Settings
    _entities: list[str] | None = None
    _analyzer: Any | None = None
    _anonymizer: Any | None = None

    def __post_init__(self) -> None:
        self._entities = [e.strip() for e in self.settings.presidio_entities.split(",") if e.strip()]
        if self.settings.presidio_enabled and AnalyzerEngine and AnonymizerEngine:
            self._analyzer = AnalyzerEngine()
            self._anonymizer = AnonymizerEngine()
        else:
            self._analyzer = None
            self._anonymizer = None

    def mask(self, text: str) -> str:
        if not text:
            return text

        # ── Adım 1: Citation marker'larını koru ──────────────────────────────
        # "[Kaynak: TBK md.49]" gibi kalıpları Presidio'dan önce placeholder ile
        # değiştiriyoruz; maskeleme sonrasında geri yüklenir.
        citations_found: list[str] = CITATION_PATTERN.findall(text)
        protected = text
        citation_map: dict[str, str] = {}
        for i, full_match in enumerate(CITATION_PATTERN.finditer(text)):
            placeholder = _CITE_PLACEHOLDER_TPL.format(i=i)
            citation_map[placeholder] = full_match.group(0)
            protected = protected.replace(full_match.group(0), placeholder, 1)

        masked = protected

        # ── Adım 2: TC Kimlik No regex (dil bağımsız) ────────────────────────
        if "TR_ID_NUMBER" in self._entities:
            masked = TR_ID_PATTERN.sub("[TR_ID_NUMBER_MASKED]", masked)

        # ── Adım 3: Presidio NER (opsiyonel) ─────────────────────────────────
        if self.settings.presidio_enabled and self._analyzer and self._anonymizer:
            entities = [e for e in self._entities if e != "TR_ID_NUMBER"]
            if entities:
                # Presidio'nun standart tanıyıcıları yalnızca "en" dilini destekler.
                # Türkçe metinde de genel PII kalıpları (EMAIL, PHONE) İngilizce
                # tanıyıcılarla yeterli doğrulukta çalışır.
                try:
                    results = self._analyzer.analyze(
                        text=masked,
                        entities=entities,
                        language="en",
                    )
                    if results:
                        masked = self._anonymizer.anonymize(
                            text=masked, analyzer_results=results
                        ).text
                except ValueError:
                    # Hiçbir recognizer bulunamazsa sessizce geç.
                    pass

        # ── Adım 4: Citation placeholder'larını geri yükle ───────────────────
        def _restore(m: re.Match) -> str:
            return citation_map.get(m.group(0), m.group(0))

        return _CITE_PLACEHOLDER_RE.sub(_restore, masked)


def extract_citations(answer: str) -> list[str]:
    return [m.strip() for m in CITATION_PATTERN.findall(answer or "") if m.strip()]


def build_allowed_citation_set(retrieved_chunks: list[dict[str, Any]]) -> set[str]:
    allowed: set[str] = set()
    for chunk in retrieved_chunks:
        citation = chunk.get("citation") or chunk.get("source") or ""
        citation = str(citation).strip()
        if citation:
            allowed.add(citation)
    return allowed


def validate_citations(answer: str, retrieved_chunks: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    citations = extract_citations(answer)
    if not citations:
        return False, []

    allowed = build_allowed_citation_set(retrieved_chunks)
    invalid = [c for c in citations if c not in allowed]
    return len(invalid) == 0, invalid
