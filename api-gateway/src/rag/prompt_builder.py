"""Prompt Builder — Faz 1 Hukuk RAG Pipeline.

Görev: Retrieved chunk'ları + kullanıcı sorgusunu LLM'e gidecek
prompt'a dönüştür.

Faz 1 gereksinimleri (backlog-draft.md):
    - Citation zorunlu: Her claim'de kaynak gösterilmeli
    - Out-of-domain durumunda refusal
    - Mülga madde bildirilmeli
    - Strict verification mode
    - Context window: token_manager ile yönetiliyor
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from rag.token_manager import TokenLimitManager, TokenLimitResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sistem Prompt Templates
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_STRICT = """\
Sen bir Türk hukuku asistan sisteminin retrieval-augmented generation (RAG) bileşenisin.

GÖREV:
Kullanıcının sorusunu, aşağıda sağlanan kaynak metin parçalarına (chunk) dayanarak yanıtla.

ZORUNLU KURALLAR:
1. KAYNAK ZORUNLU: Her iddia için "[Kaynak: <citation>]" formatında kaynak göster.
2. KAPSAM SINIRI: Yalnızca sağlanan kaynak metin parçalarında geçen bilgileri kullan.
   Kendi bilginden tahmin veya yorum ekleme.
3. REFUSAL: Eğer sağlanan kaynaklarda soruyu yanıtlayacak bilgi yoksa:
   "Bu soruyu mevcut belgeler kapsamında yanıtlayamıyorum." de.
4. MÜLGA UYARI: Kaynak metinde "mülga" veya "yürürlükten kaldırılmış" ifadesi geçiyorsa
   kullanıcıyı açıkça uyar.
5. HUKUK UYARISI: Yanıtın sonunda şu notu ekle:
   "Bu bilgi genel hukuki bilgi amaçlıdır; hukuki tavsiye niteliği taşımaz."
6. KONTROLLÜ BELİRSİZLİK: Kaynak ailesi, belge kimliği, madde veya yürürlük durumu
   net değilse kesin konuşma; belirsizliği kısa ve açık biçimde belirt.
7. GEREKÇE DİSİPLİNİ: Yanıtında kısa sonuç, kısa gerekçe, dayanak kaynak ve varsa
   yürürlük/güncellik notu ayrıştırılabilir şekilde yer alsın.

FORMAT:
- Türkçe yanıt ver
- Mümkünse madde numarasını belirt: "TBK m.49 uyarınca..."
- Belirsiz durumlarda kesin yargı verme; "hüküm uyarınca" ifadesi yerine
  "ilgili düzenleme uyarınca değerlendirilebilir" gibi ifadeler kullan
"""

SYSTEM_PROMPT_RELAXED = """\
Sen bir Türk hukuku yardım asistanısın.
Sağlanan kaynak metin parçalarını kullanarak kullanıcının sorusunu yanıtla.
Her iddia için kaynak göster. Kaynaklarda bilgi yoksa bunu belirt.
"""

CONTEXT_HEADER = "=== KAYNAK METINLER ===\n"
CONTEXT_FOOTER = "\n=== KAYNAK METINLER SONU ===\n"
NO_CONTEXT_MSG = "[Kaynak metin bulunamadı — refusal gerekli]"
QUERY_HEADER = "\nKULLANICI SORUSU:\n"


# ---------------------------------------------------------------------------
# BuiltPrompt
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class BuiltPrompt:
    """prompt_builder.build() çıktısı."""

    system_prompt: str
    user_message: str
    context_chunk_count: int
    token_limit_result: TokenLimitResult
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_estimated_tokens(self) -> int:
        return (
            self.token_limit_result.token_budget.system_reserve
            + self.token_limit_result.token_budget.query_tokens
            + self.token_limit_result.total_tokens_used
        )

    def to_messages(self) -> list[dict[str, str]]:
        """OpenAI-compatible messages formatı."""
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.user_message},
        ]


# ---------------------------------------------------------------------------
# PromptBuilder
# ---------------------------------------------------------------------------

class PromptBuilder:
    """RAG prompt oluşturucu.

    1. Token bütçesine göre chunk listesini kırpar (TokenLimitManager).
    2. Context bloğunu formatlar.
    3. System + User message üretir.

    Kullanım:
        builder = PromptBuilder()
        prompt = builder.build(query=q, chunks=retrieval_results)
        messages = prompt.to_messages()
    """

    def __init__(
        self,
        strict_mode: bool = True,
        token_manager: TokenLimitManager | None = None,
        context_window: int | None = None,
    ) -> None:
        self.strict_mode = strict_mode

        if token_manager is not None:
            self.token_manager = token_manager
        elif context_window is not None:
            self.token_manager = TokenLimitManager(context_window=context_window)
        else:
            self.token_manager = TokenLimitManager()

        self.system_prompt = SYSTEM_PROMPT_STRICT if strict_mode else SYSTEM_PROMPT_RELAXED

    def build(
        self,
        *,
        query: str,
        chunks: list[dict[str, Any]],
        extra_system_notes: str | None = None,
    ) -> BuiltPrompt:
        """Prompt oluştur.

        Args:
            query: Kullanıcı sorgusu
            chunks: [{"text": str, "citation": str, ...}] — retriever/reranker çıktısı
            extra_system_notes: System prompt'a eklenecek ek notlar (opsiyonel)

        Returns:
            BuiltPrompt
        """
        # Token limit yönetimi
        token_result = self.token_manager.fit_chunks(query=query, chunks=chunks)

        if token_result.chunks_dropped > 0:
            logger.info(
                "Token limit: %d/%d chunk alındı, %d düşürüldü",
                len(token_result.chunks),
                len(chunks),
                token_result.chunks_dropped,
            )

        # System prompt hazırla
        system = self.system_prompt
        if extra_system_notes:
            system = system + "\nEK NOTLAR:\n" + extra_system_notes

        # Context bloğu formatla
        context_block = self._format_context(token_result.chunks)

        # User message oluştur
        user_message = f"{context_block}{QUERY_HEADER}{query}"

        return BuiltPrompt(
            system_prompt=system,
            user_message=user_message,
            context_chunk_count=len(token_result.chunks),
            token_limit_result=token_result,
            metadata={
                "strict_mode": self.strict_mode,
                "chunks_dropped": token_result.chunks_dropped,
                "truncation_applied": token_result.truncation_applied,
            },
        )

    @staticmethod
    def _format_context(chunks: list[dict[str, Any]]) -> str:
        """Chunk'ları prompt context bloğuna dönüştür."""
        if not chunks:
            return CONTEXT_HEADER + NO_CONTEXT_MSG + CONTEXT_FOOTER

        formatted_parts: list[str] = []
        for i, chunk in enumerate(chunks, start=1):
            citation = chunk.get("citation", f"Kaynak {i}")
            text = chunk.get("text", "").strip()
            score = chunk.get("score")

            score_note = f" [skor: {score:.3f}]" if score is not None else ""
            header = f"[{i}] Kaynak: {citation}{score_note}"
            formatted_parts.append(f"{header}\n{text}")

        context_body = "\n\n".join(formatted_parts)
        return CONTEXT_HEADER + context_body + CONTEXT_FOOTER

    def build_refusal_prompt(self, *, query: str, reason: str = "") -> BuiltPrompt:
        """Hiç kaynak bulunamadığında refusal prompt'u oluştur."""
        from rag.token_manager import TokenBudget, TokenLimitResult

        budget = TokenBudget.compute(query=query)
        empty_result = TokenLimitResult(
            chunks=[],
            token_budget=budget,
            total_tokens_used=0,
            chunks_dropped=0,
            truncation_applied=False,
        )

        refusal_note = reason or "İlgili kaynak belgeler bulunamadı."
        context_block = CONTEXT_HEADER + f"[{refusal_note}]" + CONTEXT_FOOTER
        user_message = f"{context_block}{QUERY_HEADER}{query}"

        return BuiltPrompt(
            system_prompt=self.system_prompt,
            user_message=user_message,
            context_chunk_count=0,
            token_limit_result=empty_result,
            metadata={"refusal": True, "reason": refusal_note},
        )


# ---------------------------------------------------------------------------
# Factory helper
# ---------------------------------------------------------------------------

_default_builder: PromptBuilder | None = None


def get_prompt_builder(*, strict_mode: bool = True) -> PromptBuilder:
    """Process-wide singleton prompt builder."""
    global _default_builder
    if _default_builder is None or _default_builder.strict_mode != strict_mode:
        import os
        ctx_window = int(os.getenv("LLM_CONTEXT_WINDOW", "32768"))
        _default_builder = PromptBuilder(strict_mode=strict_mode, context_window=ctx_window)
    return _default_builder
