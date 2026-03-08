"""Token Limit Yöneticisi — Faz 1 RAG Pipeline.

Görev: Prompt'a girecek context'in model token limitini aşmamasını sağla.

Faz 1 varsayımları (backlog-draft.md):
    - LLM: Qwen/Qwen3.5-35B-A3B-FP8 (DGX vLLM)
    - Context window: 32768 token (varsayılan; env override destekleniyor)
    - Hedef kullanım: %80 doluluk (%20 output reserve)
    - Tokenizer: Kelime bazlı yaklaşık tahmin (bağımlılık eklemeden)
      Production'da tiktoken veya HF tokenizer ile değiştirilebilir.

NOT: GPT-3/4 tarzı modellerde 1 token ≈ 0.75 kelime ya da ≈4 karakter.
     Bu modül kelime-bazlı tahmin kullanır (1 kelime ≈ 1.35 token).
     Yeterli güvenlik payı ile çalışır; kritik değil, Faz 2'de iyileştir.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sabitler
# ---------------------------------------------------------------------------

DEFAULT_CONTEXT_WINDOW = 32768   # Qwen3.5 context window
OUTPUT_RESERVE_RATIO = 0.20      # %20 output için reserve
SYSTEM_PROMPT_RESERVE = 512      # System prompt token bütçesi
WORDS_PER_TOKEN = 0.74           # Türkçe için kelime/token oranı (yaklaşık)

# Minimum chunk sayısı — token limit nedeniyle 0 chunk'a düşmesin
MIN_CHUNKS_TO_KEEP = 2


# ---------------------------------------------------------------------------
# Token Estimation
# ---------------------------------------------------------------------------

def estimate_tokens(text: str) -> int:
    """Kelime sayısı bazlı token tahmini.

    Türkçe ortalama: 1 kelime ≈ 1.35 token (agglutinative dil).
    Güvenlik payı için biraz yüksek tutuyoruz.
    """
    if not text:
        return 0
    word_count = len(text.split())
    return max(1, int(word_count / WORDS_PER_TOKEN))


# ---------------------------------------------------------------------------
# TokenBudget — yönetim dataclass'ı
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class TokenBudget:
    """Token bütçesi hesabı."""

    context_window: int
    output_reserve: int
    system_reserve: int
    query_tokens: int
    available_for_chunks: int

    @classmethod
    def compute(
        cls,
        *,
        context_window: int = DEFAULT_CONTEXT_WINDOW,
        output_reserve_ratio: float = OUTPUT_RESERVE_RATIO,
        system_reserve: int = SYSTEM_PROMPT_RESERVE,
        query: str = "",
    ) -> "TokenBudget":
        output_reserve = int(context_window * output_reserve_ratio)
        query_tokens = estimate_tokens(query)
        available = context_window - output_reserve - system_reserve - query_tokens
        return cls(
            context_window=context_window,
            output_reserve=output_reserve,
            system_reserve=system_reserve,
            query_tokens=query_tokens,
            available_for_chunks=max(0, available),
        )

    @property
    def total_reserved(self) -> int:
        return self.output_reserve + self.system_reserve + self.query_tokens


# ---------------------------------------------------------------------------
# TokenLimitResult — kırpma sonucu
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class TokenLimitResult:
    """fit_chunks() çıktısı."""

    chunks: list[dict]     # Sığan chunk'lar (orijinal sıra korunur)
    token_budget: TokenBudget
    total_tokens_used: int
    chunks_dropped: int
    truncation_applied: bool

    @property
    def utilization_ratio(self) -> float:
        """Kullanılan token / mevcut bütçe."""
        if self.token_budget.available_for_chunks <= 0:
            return 1.0
        return self.total_tokens_used / self.token_budget.available_for_chunks


# ---------------------------------------------------------------------------
# TokenLimitManager — ana sınıf
# ---------------------------------------------------------------------------

class TokenLimitManager:
    """RAG context'ini model token limitine göre kırpar/sıralar.

    Kullanım:
        manager = TokenLimitManager()
        result = manager.fit_chunks(
            query="haksız fiil tazminatı",
            chunks=[{"text": "...", "citation": "TBK m.49", ...}, ...],
        )
        # result.chunks → prompt'a gönderilecek chunk listesi
    """

    def __init__(
        self,
        context_window: int = DEFAULT_CONTEXT_WINDOW,
        output_reserve_ratio: float = OUTPUT_RESERVE_RATIO,
        system_reserve: int = SYSTEM_PROMPT_RESERVE,
        min_chunks: int = MIN_CHUNKS_TO_KEEP,
    ) -> None:
        self.context_window = context_window
        self.output_reserve_ratio = output_reserve_ratio
        self.system_reserve = system_reserve
        self.min_chunks = min_chunks

    def fit_chunks(
        self,
        *,
        query: str,
        chunks: list[dict],
        truncate_long_chunks: bool = True,
    ) -> TokenLimitResult:
        """Token bütçesine sığan chunk'ları döndür.

        Strateji:
        1. Bütçeyi hesapla.
        2. Chunk'ları sırayla ekle; bütçe dolana kadar al.
        3. Son chunk'ı bütçeye tam sığacak şekilde kırp (truncate_long_chunks=True).
        4. Min chunk garantisi: en az min_chunks chunk alınır (bütçe aşılsa bile).

        Args:
            query: Kullanıcı sorgusu (token hesabı için)
            chunks: [{"text": str, "citation": str?, ...}]
            truncate_long_chunks: Son chunk kırpılsın mı?

        Returns:
            TokenLimitResult
        """
        budget = TokenBudget.compute(
            context_window=self.context_window,
            output_reserve_ratio=self.output_reserve_ratio,
            system_reserve=self.system_reserve,
            query=query,
        )

        if not chunks:
            return TokenLimitResult(
                chunks=[],
                token_budget=budget,
                total_tokens_used=0,
                chunks_dropped=0,
                truncation_applied=False,
            )

        selected: list[dict] = []
        used_tokens = 0
        truncation_applied = False
        chunks_dropped = 0

        for i, chunk in enumerate(chunks):
            text = chunk.get("text", "")
            chunk_tokens = estimate_tokens(text)
            remaining = budget.available_for_chunks - used_tokens

            if chunk_tokens <= remaining:
                # Chunk tamamen sığıyor
                selected.append(chunk)
                used_tokens += chunk_tokens
            elif i < self.min_chunks:
                # Minimum garantisi: sığmasa da al, gerekirse kırp
                if truncate_long_chunks and remaining > 50:
                    truncated_text = self._truncate_to_tokens(text, remaining)
                    truncated_chunk = dict(chunk)
                    truncated_chunk["text"] = truncated_text
                    selected.append(truncated_chunk)
                    used_tokens += estimate_tokens(truncated_text)
                    truncation_applied = True
                    logger.debug(
                        "Chunk %d (min_guarantee) kırpıldı: %d → %d token",
                        i,
                        chunk_tokens,
                        estimate_tokens(truncated_text),
                    )
                else:
                    selected.append(chunk)
                    used_tokens += chunk_tokens
            else:
                # Bütçe aştı — kalan chunk'lar düşürülüyor
                chunks_dropped = len(chunks) - len(selected)
                logger.info(
                    "Token limiti aşıldı: %d chunk'tan %d tanesi alındı, %d düşürüldü",
                    len(chunks),
                    len(selected),
                    chunks_dropped,
                )
                break

        return TokenLimitResult(
            chunks=selected,
            token_budget=budget,
            total_tokens_used=used_tokens,
            chunks_dropped=chunks_dropped,
            truncation_applied=truncation_applied,
        )

    @staticmethod
    def _truncate_to_tokens(text: str, max_tokens: int) -> str:
        """Metni belirtilen token limitine kırp (kelime bazlı)."""
        words = text.split()
        max_words = max(1, int(max_tokens * WORDS_PER_TOKEN))
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words]) + " [...]"

    def summary(self, result: TokenLimitResult) -> str:
        """İnsan okunabilir özet."""
        b = result.token_budget
        return (
            f"Token bütçesi: {b.context_window} "
            f"(output={b.output_reserve}, sys={b.system_reserve}, query={b.query_tokens}) "
            f"→ chunk bütçesi={b.available_for_chunks} | "
            f"kullanılan={result.total_tokens_used} "
            f"({result.utilization_ratio:.0%}) | "
            f"chunk={len(result.chunks)}/{len(result.chunks)+result.chunks_dropped} | "
            f"kırpma={'evet' if result.truncation_applied else 'hayır'}"
        )
