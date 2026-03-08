from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from guardrails.actions import extract_citations
from guardrails.pipeline import GuardrailsPipeline
from llm.client import LLMClient

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RetrievedChunk:
    text: str
    citation: str
    source: str | None = None
    score: float | None = None
    metadata: dict[str, Any] | None = None

    def to_guardrails_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "citation": self.citation,
            "source": self.source or self.citation,
            "score": self.score,
            "metadata": self.metadata or {},
        }


@dataclass(slots=True)
class OrchestratorResponse:
    answer: str
    citations: list[str]
    blocked: bool
    guardrails_reasons: list[str]
    # Verification engine sonucu (Backlog #6) — opsiyonel
    verification: dict[str, Any] | None = None


class RAGOrchestrator:
    """Faz 1 RAG pipeline orchestrator.

    Pipeline sırası:
        1. Retrieval (dışarıdan sağlanır)
        2. LLM draft generation
        3. NeMo Guardrails post-processing (citation check + PII mask)
        4. Verification Engine (claim/citation grounding — Backlog #6)

    VerificationEngine kullanımı için `use_verification=True` (varsayılan).
    Strict modda verification "fail" → yanıt bloklanır.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        guardrails: GuardrailsPipeline,
        *,
        use_verification: bool = False,
        verification_strict: bool = True,
        verification_blocking: bool = True,
    ) -> None:
        """
        Args:
            llm_client: LLM generate istemcisi
            guardrails: NeMo Guardrails pipeline'ı
            use_verification: Verification Engine'i etkinleştir (default: False)
                - True → VerificationEngine her yanıt için çalışır
                - False → Verificaton devre dışı (backward-compatible default)
            verification_strict: Strict citation matching (default: True)
                - True → context dışı atıf → fail
            verification_blocking: Fail verdict'te yanıtı blokla (default: True)
                - False → sadece log/raporlama; yanıt yine de dönülür
        """
        self.llm_client = llm_client
        self.guardrails = guardrails
        self.use_verification = use_verification
        self.verification_strict = verification_strict
        self.verification_blocking = verification_blocking

        self._verification_engine = None
        if use_verification:
            from rag.verification_engine import VerificationEngine
            self._verification_engine = VerificationEngine(strict_mode=verification_strict)

    async def answer(
        self,
        query: str,
        retrieved_chunks: list[RetrievedChunk],
    ) -> OrchestratorResponse:
        """Sorguyu yanıtla.

        Args:
            query: Kullanıcı sorusu
            retrieved_chunks: Retriever'dan gelen chunk'lar

        Returns:
            OrchestratorResponse
        """
        context = self._build_context(retrieved_chunks)
        draft = await self.llm_client.generate_rag_draft(query=query, context=context)

        guardrails_result = await self.guardrails.run(
            user_query=query,
            draft_answer=draft,
            retrieved_chunks=[chunk.to_guardrails_dict() for chunk in retrieved_chunks],
        )

        citations = extract_citations(guardrails_result.answer)
        final_answer = guardrails_result.answer
        blocked = guardrails_result.blocked
        reasons = guardrails_result.reasons
        verification_dict: dict[str, Any] | None = None

        # Verification Engine (Backlog #6)
        if self._verification_engine and not blocked:
            context_dicts = [c.to_guardrails_dict() for c in retrieved_chunks]
            verification_result = self._verification_engine.verify(
                answer=final_answer,
                context_chunks=context_dicts,
            )
            verification_dict = verification_result.to_dict()

            logger.info(
                "Verification verdict=%s risk=%.2f claim=%d/%d",
                verification_result.verdict,
                verification_result.hallucination_risk,
                verification_result.grounded_count,
                verification_result.claim_count,
            )

            if verification_result.verdict == "fail" and self.verification_blocking:
                blocked = True
                reasons = reasons + ["verification_failed", verification_result.verdict_reason]
                final_answer = (
                    "Bu konuda elimdeki kaynaklarda yeterli doğrulanmış bilgi bulamadım. "
                    "Lütfen daha spesifik bir mevzuat sorusu sorun."
                )

        return OrchestratorResponse(
            answer=final_answer,
            citations=citations,
            blocked=blocked,
            guardrails_reasons=reasons,
            verification=verification_dict,
        )

    @staticmethod
    def _build_context(chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return ""

        formatted = []
        for chunk in chunks:
            citation = chunk.citation
            # Format: kaynak etiketi önce, ardından metin.
            # LLM'in "[Kaynak: X]" formatını doğrudan kopyalaması için
            # numeric prefix KULLANILMIYOR — sadece kaynak etiketi.
            formatted.append(f"[Kaynak: {citation}]\n{chunk.text}")
        return "\n\n---\n\n".join(formatted)
