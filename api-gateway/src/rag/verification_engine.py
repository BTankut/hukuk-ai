"""Verification Engine — Claim/Citation Grounding (Hallüsinasyon Önleyici).

LLM çıktısındaki hukuki iddiaları ve atıfları retrieved context ile karşılaştırarak
groundedness (zemine oturma) kontrolü yapar.

Algoritma (Faz 1, lexical/offline — ML bağımlılığı yok):
    1. Answer'daki [Kaynak: ...] atıflarını çıkar.
    2. Her atıfı context chunk'larının citation seti ile karşılaştır (exact + fuzzy).
    3. Answer cümlelerini context chunk'ları ile token Jaccard overlap üzerinden ground et.
    4. Hukuki referans kalıplarını (TBK m.49 gibi) atıf seti ile doğrula.
    5. Genel halüsinasyon riski skoru ve verdict üret: "pass" | "warn" | "fail".

Faz 2 için: dense embedding ile semantic grounding ve claim-level NLI eklenebilir.

Integration noktaları:
    - RAGOrchestrator.answer() → verify() ile post-processing
    - GuardrailsPipeline → verify() ile ek doğrulama katmanı
    - Standalone: evaluation, logging, monitoring için
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Regex Patterns — Türk Hukuk Metni
# ---------------------------------------------------------------------------

# [Kaynak: TBK m.49] veya [Kaynak: TBK m.49/f.1] veya [Kaynak: TMK m.185]
CITATION_BRACKET_PATTERN = re.compile(r"\[Kaynak:\s*([^\]]+)\]")

# "TBK m.49", "TMK md.185", "TCK m.243/3", "İİK m.67" gibi inline atıflar
LEGAL_REF_INLINE_PATTERN = re.compile(
    r"\b([A-ZİĞÜŞÇÖa-zığüşçö]{2,6})\s+"
    r"(?:m(?:adde)?\.?\s*|md\.?\s*)(\d+)"
    r"(?:[/,\s](?:f(?:ıkra)?\.?\s*)?(\d+))?"
    r"\b"
)

# Cümle sınırı (Türkçe metin için)
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-ZÇĞİÖŞÜ\[\"])")

# Türkçe stop words (minimal)
_STOP_WORDS = frozenset(
    {
        "ve", "veya", "ile", "bir", "bu", "şu", "o", "da", "de",
        "ki", "için", "olan", "olarak", "ise", "en", "biz", "siz",
        "ben", "sen", "göre", "kadar", "sonra", "önce", "ancak",
        "fakat", "ama", "lakin", "eğer", "ise", "ya", "ne", "mi",
        "mı", "mu", "mü", "her", "bazı", "çok", "az", "daha",
        "en", "hem", "de", "da",
    }
)

# Minimum grounding threshold-ları
DEFAULT_OVERLAP_THRESHOLD = 0.12   # Jaccard token overlap eşiği
CITATION_BONUS = 0.30              # Citation eşleşmesi bonus puanı
WARN_THRESHOLD = 0.25              # ungrounded_ratio > warn → "warn"
FAIL_THRESHOLD = 0.55              # ungrounded_ratio > fail → "fail"
MIN_SENTENCE_LENGTH = 12           # Bu karakter sayısının altındaki cümleler atlanır


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class CitationSpan:
    """Answer'da tespit edilen tek bir bracket atıf [Kaynak: ...]."""

    raw: str        # "[Kaynak: TBK m.49]"
    citation: str   # "TBK m.49"
    char_start: int
    char_end: int


@dataclass(slots=True)
class ClaimSpan:
    """Answer'daki tek bir hukuki iddia cümlesi."""

    text: str
    bracket_citations: list[str] = field(default_factory=list)  # [Kaynak: ...] içerikleri
    inline_refs: list[str] = field(default_factory=list)         # "TBK m.49" gibi inline ref'ler
    sentence_idx: int = 0

    @property
    def all_referenced_sources(self) -> list[str]:
        """Hem bracket hem inline atıfları birleştir."""
        return list(dict.fromkeys(self.bracket_citations + self.inline_refs))


@dataclass(slots=True)
class GroundingResult:
    """Tek bir claim için grounding değerlendirme sonucu."""

    claim: ClaimSpan
    is_grounded: bool
    best_match_chunk_id: str | None
    best_match_score: float
    grounding_evidence: str | None  # Destekleyen chunk'dan kısa alıntı
    unverified_citations: list[str] = field(default_factory=list)  # Context'te olmayan atıflar


@dataclass(slots=True)
class VerificationResult:
    """Tüm LLM yanıtı için doğrulama sonucu."""

    claim_count: int
    grounded_count: int
    ungrounded_count: int
    groundings: list[GroundingResult]
    citation_mismatches: list[str]  # Context'te olmayan bracket atıflar
    hallucination_risk: float       # 0.0 (güvenli) → 1.0 (yüksek risk)
    verdict: str                    # "pass" | "warn" | "fail"
    verdict_reason: str

    @property
    def overall_grounded(self) -> bool:
        return self.verdict == "pass"

    @property
    def has_citation_mismatches(self) -> bool:
        return bool(self.citation_mismatches)

    @property
    def grounding_ratio(self) -> float:
        if self.claim_count == 0:
            return 1.0
        return self.grounded_count / self.claim_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "verdict_reason": self.verdict_reason,
            "hallucination_risk": round(self.hallucination_risk, 3),
            "grounding_ratio": round(self.grounding_ratio, 3),
            "claim_count": self.claim_count,
            "grounded_count": self.grounded_count,
            "ungrounded_count": self.ungrounded_count,
            "citation_mismatches": self.citation_mismatches,
            "groundings": [
                {
                    "sentence_idx": g.claim.sentence_idx,
                    "sentence_preview": g.claim.text[:100] + ("..." if len(g.claim.text) > 100 else ""),
                    "is_grounded": g.is_grounded,
                    "overlap_score": round(g.best_match_score, 3),
                    "best_chunk": g.best_match_chunk_id,
                    "unverified_citations": g.unverified_citations,
                }
                for g in self.groundings
            ],
        }


# ---------------------------------------------------------------------------
# Verification Engine
# ---------------------------------------------------------------------------


class VerificationEngine:
    """LLM çıktısı için hallüsinasyon önleyici claim/citation doğrulama motoru.

    Kullanım:
        engine = VerificationEngine(strict_mode=True)
        result = engine.verify(answer=llm_output, context_chunks=retrieved_chunks)

        if result.verdict == "fail":
            # Yanıtı blokla veya refusal yap
        elif result.verdict == "warn":
            # Uyarı ekle

    context_chunks formatı:
        [
            {
                "text": str,
                "citation": str,  # "TBK m.49"
                "source": str,    # opsiyonel, "TBK"
                "metadata": {...},
            },
            ...
        ]
    """

    def __init__(
        self,
        *,
        overlap_threshold: float = DEFAULT_OVERLAP_THRESHOLD,
        strict_mode: bool = True,
        warn_threshold: float = WARN_THRESHOLD,
        fail_threshold: float = FAIL_THRESHOLD,
    ) -> None:
        self.overlap_threshold = overlap_threshold
        self.strict_mode = strict_mode
        self.warn_threshold = warn_threshold
        self.fail_threshold = fail_threshold

    # ------------------------------------------------------------------
    # Ana Doğrulama Fonksiyonu
    # ------------------------------------------------------------------

    def verify(
        self,
        *,
        answer: str,
        context_chunks: list[dict[str, Any]],
    ) -> VerificationResult:
        """LLM yanıtını context chunk'larına karşı doğrula.

        Args:
            answer: LLM'in ürettiği yanıt metni
            context_chunks: Retrieved chunk'lar [{text, citation, ...}, ...]

        Returns:
            VerificationResult
        """
        if not answer or not answer.strip():
            return self._empty_result("Boş yanıt")

        # 1. Context'ten izin verilen atıf setini oluştur
        allowed_citations = self._build_allowed_citation_set(context_chunks)

        # 2. Answer'daki bracket atıfları çıkar ve context ile karşılaştır
        bracket_spans = self._extract_bracket_citations(answer)
        citation_mismatches = [
            span.citation
            for span in bracket_spans
            if not self._citation_in_allowed(span.citation, allowed_citations)
        ]

        # 3. Cümle bazlı claim'leri çıkar
        claims = self._extract_claims(answer)

        if not claims:
            # Claim yok — sadece citation mismatch'e göre karar ver
            risk = min(1.0, len(citation_mismatches) * 0.3)
            verdict = "fail" if (self.strict_mode and citation_mismatches) else (
                "warn" if citation_mismatches else "pass"
            )
            return VerificationResult(
                claim_count=0,
                grounded_count=0,
                ungrounded_count=0,
                groundings=[],
                citation_mismatches=citation_mismatches,
                hallucination_risk=risk,
                verdict=verdict,
                verdict_reason=(
                    f"Context dışı atıf: {citation_mismatches}"
                    if citation_mismatches else "Doğrulanabilir claim bulunamadı"
                ),
            )

        # 4. Her claim için grounding kontrolü
        groundings = [
            self._ground_claim(claim, context_chunks, allowed_citations)
            for claim in claims
        ]

        # 5. Metrikler
        grounded_count = sum(1 for g in groundings if g.is_grounded)
        ungrounded_count = sum(1 for g in groundings if not g.is_grounded)
        total = len(claims)

        ungrounded_ratio = ungrounded_count / total if total > 0 else 0.0
        citation_penalty = min(0.45, len(citation_mismatches) * 0.15)
        hallucination_risk = min(1.0, ungrounded_ratio * 0.75 + citation_penalty)

        # 6. Verdict
        verdict, reason = self._compute_verdict(
            ungrounded_ratio=ungrounded_ratio,
            citation_mismatches=citation_mismatches,
            groundings=groundings,
        )

        logger.info(
            "Verification sonucu: claims=%d grounded=%d ungrounded=%d "
            "citation_mismatch=%d verdict=%s risk=%.2f",
            total,
            grounded_count,
            ungrounded_count,
            len(citation_mismatches),
            verdict,
            hallucination_risk,
        )

        return VerificationResult(
            claim_count=total,
            grounded_count=grounded_count,
            ungrounded_count=ungrounded_count,
            groundings=groundings,
            citation_mismatches=citation_mismatches,
            hallucination_risk=hallucination_risk,
            verdict=verdict,
            verdict_reason=reason,
        )

    # ------------------------------------------------------------------
    # Citation Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_allowed_citation_set(context_chunks: list[dict[str, Any]]) -> set[str]:
        """Context chunk'larından izin verilen atıf setini oluştur."""
        allowed: set[str] = set()
        for chunk in context_chunks:
            for key in ("citation", "source", "law_short_name"):
                # Doğrudan field veya metadata içinde
                val = chunk.get(key)
                if not val and isinstance(chunk.get("metadata"), dict):
                    val = chunk["metadata"].get(key)
                if val:
                    allowed.add(str(val).strip())
        return allowed

    @staticmethod
    def _normalize_citation(citation: str) -> str:
        """Atıfı normalize et: boşlukları düzelt, fıkra kısmını düşür."""
        c = citation.strip()
        # "TBK m. 49" → "TBK m.49"
        c = re.sub(r"m\.\s+", "m.", c)
        c = re.sub(r"md\.\s+", "m.", c)
        # "TBK m.49/f.1" → fıkra olmadan compare için
        return re.sub(r"/f\.\d+$", "", c)

    def _citation_in_allowed(self, citation: str, allowed: set[str]) -> bool:
        """Atıf izin verilen sette mi? (tam + normalize + spesifik prefix matching).

        Matching kuralları:
            A) Tam eşleşme:          "TBK m.49" ∈ allowed → True
            B) Fıkra normalizasyon:  "TBK m.49/f.1" → "TBK m.49" ∈ allowed → True
            C) Yalnızca kanun adı:   c="TBK" (madde numarası yok) → allowed "TBK m.49" → True
            D) Fıkra özelleştirme:   c="TBK m.49/f.1" → allowed "TBK m.49" → c.startswith(...+"/") → True

        Yanlış eşleşmeye izin vermez:
            - "TBK m.9999" → allowed "TBK m.49" → False  (farklı madde numarası!)
            - "TCK m.99"   → allowed {"TBK m.49"} → False
        """
        if not allowed:
            return False

        c = citation.strip()

        # A) Tam eşleşme
        if c in allowed:
            return True

        # B) Fıkra bilgisini düşürerek normalize et
        norm = self._normalize_citation(c)
        if norm in allowed:
            return True

        for allowed_c in allowed:
            # C) Sadece kanun adı (boşluk içermiyor): c="TBK", allowed_c="TBK m.49"
            #    Madde numarası olmayan genel kanun atıfları → izin ver
            if " " not in c and allowed_c.startswith(c + " "):
                return True

            # D) Fıkra ile daha spesifik: c="TBK m.49/f.1", allowed_c="TBK m.49"
            if c.startswith(allowed_c + "/"):
                return True

        return False

    @staticmethod
    def _extract_bracket_citations(answer: str) -> list[CitationSpan]:
        """[Kaynak: ...] kalıplarını çıkar."""
        spans = []
        for m in CITATION_BRACKET_PATTERN.finditer(answer):
            spans.append(
                CitationSpan(
                    raw=m.group(0),
                    citation=m.group(1).strip(),
                    char_start=m.start(),
                    char_end=m.end(),
                )
            )
        return spans

    # ------------------------------------------------------------------
    # Claim Extraction
    # ------------------------------------------------------------------

    def _extract_claims(self, answer: str) -> list[ClaimSpan]:
        """Answer'ı anlamlı claim cümlelerine ayır."""
        # [Kaynak: ...] kalıpları olmadan temiz metin
        clean = CITATION_BRACKET_PATTERN.sub(" ", answer)
        # Hukuki uyarı notu satırlarını atla (sadece boilerplate)
        lines = clean.split("\n")
        non_boilerplate = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("Bu bilgi genel hukuki bilgi") or not stripped:
                continue
            non_boilerplate.append(stripped)
        clean = " ".join(non_boilerplate)

        # Cümlelere böl
        raw_sentences = SENTENCE_BOUNDARY.split(clean)
        claims: list[ClaimSpan] = []

        for idx, sentence in enumerate(raw_sentences):
            sentence = sentence.strip()
            if len(sentence) < MIN_SENTENCE_LENGTH:
                continue

            # Bu cümleye ait bracket atıfları bul (orijinal answer'dan)
            bracket_cites = self._find_bracket_cites_for_sentence(answer, sentence)

            # Inline hukuki referansları bul
            inline_refs = [
                f"{m.group(1)} m.{m.group(2)}"
                for m in LEGAL_REF_INLINE_PATTERN.finditer(sentence)
            ]

            claims.append(
                ClaimSpan(
                    text=sentence,
                    bracket_citations=bracket_cites,
                    inline_refs=inline_refs,
                    sentence_idx=idx,
                )
            )

        return claims

    @staticmethod
    def _find_bracket_cites_for_sentence(answer: str, sentence: str) -> list[str]:
        """Cümleye ait bracket citation'ları orijinal answer'dan bul."""
        # Cümlenin ilk 40 karakterlik penceresini al (context içinde ara)
        sentence_key = sentence[:40]
        citations_near: list[str] = []

        # Cümlenin pozisyonunu bul
        pos = answer.find(sentence_key)
        if pos < 0:
            return citations_near

        # Cümlenin etrafındaki ±300 karakter penceresi
        window_start = max(0, pos - 30)
        window_end = min(len(answer), pos + len(sentence) + 150)
        window = answer[window_start:window_end]

        for m in CITATION_BRACKET_PATTERN.finditer(window):
            citations_near.append(m.group(1).strip())

        return list(dict.fromkeys(citations_near))

    # ------------------------------------------------------------------
    # Grounding
    # ------------------------------------------------------------------

    def _ground_claim(
        self,
        claim: ClaimSpan,
        context_chunks: list[dict[str, Any]],
        allowed_citations: set[str],
    ) -> GroundingResult:
        """Tek bir claim'i context'e ground et (lexical overlap)."""
        if not context_chunks:
            return GroundingResult(
                claim=claim,
                is_grounded=False,
                best_match_chunk_id=None,
                best_match_score=0.0,
                grounding_evidence=None,
                unverified_citations=claim.all_referenced_sources,
            )

        # Doğrulanamayan atıflar
        unverified = [
            c for c in claim.all_referenced_sources
            if not self._citation_in_allowed(c, allowed_citations)
        ]

        claim_tokens = self._tokenize(claim.text)
        best_chunk_id: str | None = None
        best_score = 0.0
        best_evidence: str | None = None

        for chunk in context_chunks:
            chunk_text = str(chunk.get("text", ""))
            chunk_citation = str(chunk.get("citation") or chunk.get("source") or "")
            chunk_tokens = self._tokenize(chunk_text)

            score = self._jaccard_overlap(claim_tokens, chunk_tokens)

            # Citation bonus: claim'de bu chunk'un citation'ı varsa bonus ekle
            chunk_allowed = {chunk_citation} if chunk_citation else set()
            has_cite_match = any(
                self._citation_in_allowed(c, chunk_allowed)
                for c in claim.all_referenced_sources
                if c
            )
            if has_cite_match:
                score = min(1.0, score + CITATION_BONUS)

            if score > best_score:
                best_score = score
                best_chunk_id = chunk_citation or chunk.get("id", "")
                best_evidence = chunk_text[:200] + ("..." if len(chunk_text) > 200 else "")

        # Grounding kararı: overlap yeterli VE doğrulanamayan atıf yok
        is_grounded = best_score >= self.overlap_threshold

        # Strict mode: herhangi bir unverified citation → grounded değil
        if self.strict_mode and unverified:
            is_grounded = False

        return GroundingResult(
            claim=claim,
            is_grounded=is_grounded,
            best_match_chunk_id=best_chunk_id,
            best_match_score=best_score,
            grounding_evidence=best_evidence,
            unverified_citations=unverified,
        )

    # ------------------------------------------------------------------
    # Verdict
    # ------------------------------------------------------------------

    def _compute_verdict(
        self,
        *,
        ungrounded_ratio: float,
        citation_mismatches: list[str],
        groundings: list[GroundingResult],
    ) -> tuple[str, str]:
        """Verdict ve gerekçeyi hesapla."""

        # Strict mode: herhangi bir citation mismatch → fail
        if self.strict_mode and citation_mismatches:
            return (
                "fail",
                f"Context dışı atıf tespit edildi: {citation_mismatches[:3]}"
                + (" vd." if len(citation_mismatches) > 3 else ""),
            )

        if ungrounded_ratio >= self.fail_threshold:
            return (
                "fail",
                f"Yanıtın %{ungrounded_ratio:.0%}'i context'e dayanmıyor.",
            )

        if ungrounded_ratio >= self.warn_threshold or citation_mismatches:
            parts: list[str] = []
            if citation_mismatches:
                parts.append(f"geçersiz atıf ({len(citation_mismatches)} adet)")
            if ungrounded_ratio > 0:
                parts.append(f"ungrounded claim oranı %{ungrounded_ratio:.0%}")
            return "warn", "Uyarı: " + ", ".join(parts)

        return "pass", "Tüm iddialar bağlamla destekleniyor."

    # ------------------------------------------------------------------
    # Metin Yardımcıları
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """Metni kelime token set'ine dönüştür (lowercase, stop word'suz)."""
        tokens = re.findall(r"[a-zA-ZçğıöşüÇĞİÖŞÜ0-9]{2,}", text.lower())
        return {t for t in tokens if t not in _STOP_WORDS}

    @staticmethod
    def _jaccard_overlap(a: set[str], b: set[str]) -> float:
        """Jaccard benzerlik skoru (0–1)."""
        if not a or not b:
            return 0.0
        intersection = len(a & b)
        union = len(a | b)
        return intersection / union if union else 0.0

    @staticmethod
    def _empty_result(reason: str) -> VerificationResult:
        return VerificationResult(
            claim_count=0,
            grounded_count=0,
            ungrounded_count=0,
            groundings=[],
            citation_mismatches=[],
            hallucination_risk=0.0,
            verdict="pass",
            verdict_reason=reason,
        )


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------


_default_engine: VerificationEngine | None = None


def get_verification_engine(*, strict_mode: bool = True) -> VerificationEngine:
    """Process-wide singleton verification engine."""
    global _default_engine
    if _default_engine is None or _default_engine.strict_mode != strict_mode:
        _default_engine = VerificationEngine(strict_mode=strict_mode)
    return _default_engine
