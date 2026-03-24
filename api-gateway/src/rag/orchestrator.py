from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from guardrails.actions import extract_citations
from guardrails.pipeline import GuardrailsPipeline
from llm.client import LLMClient

logger = logging.getLogger(__name__)

_GENERIC_ASSISTANT_HINTS = (
    "hello! i'm your helpful ai assistant",
    "what would you like to know or discuss today",
    "ready to chat and share specific details",
)


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
    usage: dict[str, int] | None = None
    llm_trace: dict[str, Any] | None = None


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
        *,
        source_lock_target_citations: int | None = None,
        max_tokens: int | None = None,
    ) -> OrchestratorResponse:
        """Sorguyu yanıtla.

        Args:
            query: Kullanıcı sorusu
            retrieved_chunks: Retriever'dan gelen chunk'lar

        Returns:
            OrchestratorResponse
        """
        context = self._build_context(retrieved_chunks)
        if max_tokens is None:
            draft_result = await self.llm_client.generate_rag_draft(
                query=query,
                context=context,
            )
        else:
            draft_result = await self.llm_client.generate_rag_draft(
                query=query,
                context=context,
                max_tokens=max_tokens,
            )
        draft_usage: dict[str, int] | None = None
        draft_trace: dict[str, Any] | None = None
        if isinstance(draft_result, str):
            draft = draft_result
        else:
            draft = draft_result.text
            if draft_result.usage is not None:
                draft_usage = {
                    "prompt_tokens": draft_result.usage.prompt_tokens,
                    "completion_tokens": draft_result.usage.completion_tokens,
                    "total_tokens": draft_result.usage.total_tokens,
                }
            draft_trace = draft_result.trace

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

        if not blocked:
            source_locked_answer = self._maybe_source_lock_answer(
                answer=final_answer,
                retrieved_chunks=retrieved_chunks,
                source_lock_target_citations=source_lock_target_citations,
            )
            if source_locked_answer != final_answer:
                final_answer = source_locked_answer
                citations = extract_citations(final_answer)
                reasons = reasons + ["source_lock_fallback"]

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
            usage=draft_usage,
            llm_trace=draft_trace,
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

    @staticmethod
    def _normalize_citation(citation: str) -> str:
        normalized = citation.strip()
        normalized = re.sub(r"\bmd\.\s*", "m.", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"\bm\.\s*", "m.", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"/f\.\d+$", "", normalized, flags=re.IGNORECASE)
        return normalized

    @staticmethod
    def _looks_like_generic_assistant_reply(answer: str) -> bool:
        lowered = answer.strip().lower()
        return any(hint in lowered for hint in _GENERIC_ASSISTANT_HINTS)

    @classmethod
    def _extract_priority_chunks(
        cls,
        chunks: list[RetrievedChunk],
        *,
        max_chunks: int = 2,
    ) -> list[RetrievedChunk]:
        selected: list[RetrievedChunk] = []
        seen: set[str] = set()
        for chunk in chunks:
            citation = cls._normalize_citation(chunk.citation)
            if not citation or citation in seen:
                continue
            selected.append(chunk)
            seen.add(citation)
            if len(selected) >= max_chunks:
                break
        return selected

    @classmethod
    def _has_priority_citation_overlap(
        cls,
        citations: list[str],
        priority_chunks: list[RetrievedChunk],
    ) -> bool:
        priority = {
            cls._normalize_citation(chunk.citation)
            for chunk in priority_chunks
            if chunk.citation
        }
        cited = {cls._normalize_citation(citation) for citation in citations if citation}
        return bool(priority & cited)

    @classmethod
    def _has_partial_priority_mismatch(
        cls,
        citations: list[str],
        priority_chunks: list[RetrievedChunk],
    ) -> bool:
        priority = {
            cls._normalize_citation(chunk.citation)
            for chunk in priority_chunks
            if chunk.citation
        }
        cited = {cls._normalize_citation(citation) for citation in citations if citation}
        if len(priority) < 2 or not cited:
            return False

        overlap = priority & cited
        missing_priority = priority - cited
        extra_citations = cited - priority
        return bool(overlap) and bool(missing_priority) and bool(extra_citations)

    @staticmethod
    def _has_incomplete_priority_coverage(
        citations: list[str],
        priority_chunks: list[RetrievedChunk],
        *,
        required_count: int,
    ) -> bool:
        priority = {
            RAGOrchestrator._normalize_citation(chunk.citation)
            for chunk in priority_chunks
            if chunk.citation
        }
        cited = {
            RAGOrchestrator._normalize_citation(citation)
            for citation in citations
            if citation
        }
        if not priority or not cited:
            return False

        required_overlap = min(required_count, len(priority))
        if required_overlap <= 2:
            return False

        overlap_count = len(priority & cited)
        return 0 < overlap_count < required_overlap

    @staticmethod
    def _build_chunk_excerpt(text: str, *, max_len: int = 220) -> str:
        compact = re.sub(r"\s+", " ", text).strip()
        if len(compact) <= max_len:
            return compact

        sentences = re.split(r"(?<=[.!?])\s+", compact)
        excerpt = ""
        for sentence in sentences:
            if not sentence:
                continue
            candidate = f"{excerpt} {sentence}".strip()
            if len(candidate) > max_len and excerpt:
                break
            excerpt = candidate
            if len(excerpt) >= max_len:
                break

        if excerpt:
            return excerpt[:max_len].rstrip()
        return compact[:max_len].rstrip()

    @classmethod
    def _build_source_locked_fallback(
        cls,
        chunks: list[RetrievedChunk],
        *,
        max_chunks: int = 2,
    ) -> str | None:
        priority_chunks = cls._extract_priority_chunks(chunks, max_chunks=max_chunks)
        if not priority_chunks:
            return None

        intro = (
            "Bu soru bakımından doğrudan değerlendirilmesi gereken başlıca hükümler şunlardır:"
        )
        lines = [intro]
        for chunk in priority_chunks:
            excerpt = cls._build_chunk_excerpt(chunk.text)
            lines.append(f"- [Kaynak: {chunk.citation}] {excerpt}")
        return "\n".join(lines)

    @classmethod
    def _maybe_source_lock_answer(
        cls,
        *,
        answer: str,
        retrieved_chunks: list[RetrievedChunk],
        source_lock_target_citations: int | None = None,
    ) -> str:
        if not retrieved_chunks:
            return answer

        max_priority_chunks = 2 if source_lock_target_citations is None else max(
            2,
            min(source_lock_target_citations, 4),
        )
        priority_chunks = cls._extract_priority_chunks(
            retrieved_chunks,
            max_chunks=max_priority_chunks,
        )
        if not priority_chunks:
            return answer

        citations = extract_citations(answer)
        needs_fallback = (
            cls._looks_like_generic_assistant_reply(answer)
            or not citations
            or not cls._has_priority_citation_overlap(citations, priority_chunks)
            or cls._has_partial_priority_mismatch(citations, priority_chunks)
            or (
                source_lock_target_citations is not None
                and cls._has_incomplete_priority_coverage(
                    citations,
                    priority_chunks,
                    required_count=max_priority_chunks,
                )
            )
        )
        if not needs_fallback:
            return answer

        fallback = cls._build_source_locked_fallback(
            priority_chunks,
            max_chunks=max_priority_chunks,
        )
        return fallback or answer
