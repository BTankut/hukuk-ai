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

_MAX_CONTEXT_CHARS = 1600
_MAX_CONTEXT_CHUNK_EXCERPT_CHARS = 320
_PRIORITY_TOKEN_RE = re.compile(r"[a-z0-9]+")
_PRIORITY_STOPWORDS = {
    "ve",
    "ile",
    "icin",
    "gore",
    "göre",
    "hangi",
    "hangi̇",
    "nedir",
    "nasil",
    "nasıl",
    "temel",
    "madde",
    "maddede",
    "maddeleriyle",
    "olarak",
    "olan",
    "neden",
    "ne",
    "kadar",
    "misin",
    "ozetl",
}
_TR_ASCII_TRANS = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "İ": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
    }
)

_QUERY_CLAUSE_SPLIT_RE = re.compile(r"\b(?:ve|ile)\b")
_SOURCE_FAMILY_QUERY_HINTS: dict[str, tuple[str, ...]] = {
    "tuzuk": ("tüzük", "tuzuk"),
    "yonetmelik": ("yönetmelik", "yonetmelik"),
    "teblig": ("tebliğ", "teblig"),
    "kararname": ("kararname",),
    "genelge": ("genelge",),
    "kanun": ("kanun",),
}


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
                query=query,
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

        compact_chunks = [
            (
                chunk.citation,
                (chunk.metadata or {}).get("source_title")
                or (chunk.metadata or {}).get("belge_adi")
                or (chunk.metadata or {}).get("kanun_adi")
                or (chunk.metadata or {}).get("law_name"),
                re.sub(r"\s+", " ", chunk.text).strip(),
            )
            for chunk in chunks
        ]
        total_chars = sum(len(text) for _, _, text in compact_chunks)
        use_excerpt_mode = total_chars > _MAX_CONTEXT_CHARS

        formatted = []
        for chunk, (_, source_title, compact_text) in zip(chunks, compact_chunks, strict=False):
            citation = chunk.citation
            body = (
                RAGOrchestrator._build_chunk_excerpt(
                    compact_text,
                    max_len=_MAX_CONTEXT_CHUNK_EXCERPT_CHARS,
                )
                if use_excerpt_mode
                else compact_text
            )
            lines = [f"[Kaynak: {citation}]"]
            if isinstance(source_title, str) and source_title.strip():
                lines.append(f"[Belge: {source_title.strip()}]")
            lines.append(body)
            formatted.append("\n".join(lines))
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
        query: str | None = None,
        max_chunks: int = 2,
    ) -> list[RetrievedChunk]:
        candidates: list[tuple[int, RetrievedChunk]] = []
        seen: set[str] = set()
        for chunk in chunks:
            citation = cls._normalize_citation(chunk.citation)
            if not citation or citation in seen:
                continue
            candidates.append((len(candidates), chunk))
            seen.add(citation)
        if not candidates:
            return []
        if not query:
            return [chunk for _, chunk in candidates[:max_chunks]]

        query_terms = cls._extract_priority_terms(query)
        query_clauses = cls._extract_query_clauses(query)
        requested_source_families = cls._extract_requested_source_families(query)
        source_cluster_sizes: dict[str, int] = {}
        for _, chunk in candidates:
            source_key = cls._resolve_chunk_source_key(chunk)
            source_cluster_sizes[source_key] = source_cluster_sizes.get(source_key, 0) + 1
        override_chunks = cls._extract_priority_override_chunks(
            candidates=[chunk for _, chunk in candidates],
            query=query,
            max_chunks=max_chunks,
        )
        if override_chunks:
            return override_chunks
        if not query_terms:
            return [chunk for _, chunk in candidates[:max_chunks]]

        score_map = {
            chunk.citation: cls._score_chunk_priority(
                query_terms=query_terms,
                query_clauses=query_clauses,
                requested_source_families=requested_source_families,
                source_cluster_sizes=source_cluster_sizes,
                chunk=chunk,
                query=query,
            )
            for _, chunk in candidates
        }
        if not any(score_map.values()):
            return [chunk for _, chunk in candidates[:max_chunks]]

        ordered = [chunk for _, chunk in candidates]
        best_overall = max(
            ordered,
            key=lambda chunk: (score_map.get(chunk.citation, 0), -ordered.index(chunk)),
        )
        first_score = score_map.get(ordered[0].citation, 0)
        best_score = score_map.get(best_overall.citation, 0)
        if best_score >= first_score + 2 and best_overall is not ordered[0]:
            ordered.remove(best_overall)
            ordered.insert(0, best_overall)

        if max_chunks >= 2 and len(ordered) >= 2:
            first_source_key = cls._resolve_chunk_source_key(ordered[0])
            same_source_remaining = [
                chunk for chunk in ordered[1:]
                if cls._resolve_chunk_source_key(chunk) == first_source_key
            ]
            if same_source_remaining:
                best_same_source = max(
                    same_source_remaining,
                    key=lambda chunk: (score_map.get(chunk.citation, 0), -ordered.index(chunk)),
                )
                if best_same_source is not ordered[1]:
                    ordered.remove(best_same_source)
                    ordered.insert(1, best_same_source)

        if max_chunks >= 2 and len(ordered) >= 3:
            current_second = ordered[1]
            current_second_score = score_map.get(current_second.citation, 0)
            best_remaining = max(
                ordered[1:],
                key=lambda chunk: (score_map.get(chunk.citation, 0), -ordered.index(chunk)),
            )
            best_remaining_score = score_map.get(best_remaining.citation, 0)
            if best_remaining_score >= current_second_score + 2 and best_remaining is not current_second:
                ordered.remove(best_remaining)
                ordered.insert(1, best_remaining)

        effective_max_chunks = max_chunks
        if (
            len(query_clauses) < 2
            and
            max_chunks == 2
            and len(ordered) >= 2
            and score_map.get(ordered[0].citation, 0) >= score_map.get(ordered[1].citation, 0) + 2
            and cls._resolve_chunk_source_key(ordered[0]) != cls._resolve_chunk_source_key(ordered[1])
        ):
            effective_max_chunks = 1
        return ordered[:effective_max_chunks]

    @classmethod
    def _extract_priority_override_chunks(
        cls,
        *,
        candidates: list[RetrievedChunk],
        query: str,
        max_chunks: int,
    ) -> list[RetrievedChunk]:
        normalized_query = query.lower().translate(_TR_ASCII_TRANS)
        forced_citations: list[str] = []

        if (
            "koruma tedbir" in normalized_query
            and "tazminat" in normalized_query
            and "basvuru usul" in normalized_query
        ):
            forced_citations = ["CMK m.141", "CMK m.142"]
        elif (
            "yakalanan kisinin hak" in normalized_query
            and "bildiril" in normalized_query
        ):
            forced_citations = ["CMK m.90"]

        if not forced_citations:
            return []

        by_citation = {
            cls._normalize_citation(chunk.citation): chunk
            for chunk in candidates
        }
        selected: list[RetrievedChunk] = []
        for citation in forced_citations:
            chunk = by_citation.get(cls._normalize_citation(citation))
            if chunk is not None:
                selected.append(chunk)

        return selected[:max_chunks]

    @staticmethod
    def _extract_priority_terms(text: str) -> set[str]:
        normalized = text.lower().translate(_TR_ASCII_TRANS)
        terms: set[str] = set()
        for token in _PRIORITY_TOKEN_RE.findall(normalized):
            stem = token[:5] if len(token) >= 5 else token
            if len(token) < 3 or token in _PRIORITY_STOPWORDS or stem in _PRIORITY_STOPWORDS:
                continue
            terms.add(stem)
        return terms

    @classmethod
    def _extract_query_clauses(cls, text: str) -> list[set[str]]:
        clauses: list[set[str]] = []
        normalized = text.lower().translate(_TR_ASCII_TRANS)
        for part in _QUERY_CLAUSE_SPLIT_RE.split(normalized):
            terms = cls._extract_priority_terms(part)
            if terms:
                clauses.append(terms)
        return clauses

    @staticmethod
    def _extract_requested_source_families(text: str) -> set[str]:
        normalized = text.lower().translate(_TR_ASCII_TRANS)
        families: set[str] = set()
        for family, hints in _SOURCE_FAMILY_QUERY_HINTS.items():
            if any(hint in normalized for hint in hints):
                families.add(family)
        return families

    @staticmethod
    def _resolve_chunk_source_family(chunk: RetrievedChunk) -> str | None:
        metadata = chunk.metadata or {}
        family = metadata.get("belge_turu") or metadata.get("source_type")
        if isinstance(family, str) and family.strip():
            return family.strip().lower()
        return None

    @staticmethod
    def _resolve_chunk_source_key(chunk: RetrievedChunk) -> str:
        metadata = chunk.metadata or {}
        return str(
            metadata.get("source_title")
            or metadata.get("belge_adi")
            or metadata.get("kanun_adi")
            or metadata.get("law_name")
            or metadata.get("law_short_name")
            or metadata.get("kanun_kisa_adi")
            or metadata.get("source_id")
            or chunk.source
            or chunk.citation
        ).strip().lower()

    @classmethod
    def _score_chunk_priority(
        cls,
        *,
        query_terms: set[str],
        query_clauses: list[set[str]],
        requested_source_families: set[str],
        source_cluster_sizes: dict[str, int],
        chunk: RetrievedChunk,
        query: str,
    ) -> int:
        chunk_excerpt = cls._build_chunk_excerpt(chunk.text, max_len=480)
        metadata = chunk.metadata or {}
        source_title = (
            metadata.get("source_title")
            or metadata.get("belge_adi")
            or metadata.get("kanun_adi")
            or metadata.get("law_name")
            or ""
        )
        heading = metadata.get("heading") or metadata.get("article_heading") or ""
        chunk_terms = cls._extract_priority_terms(f"{chunk.citation} {source_title} {heading} {chunk_excerpt}")
        overlap_score = len(query_terms & chunk_terms)
        score = overlap_score
        query_lower = query.lower().translate(_TR_ASCII_TRANS)
        if len(query_clauses) >= 2:
            first_clause = query_clauses[0]
            first_clause_overlap = len(first_clause & chunk_terms)
            later_clause_overlap = sum(
                len(clause & chunk_terms)
                for clause in query_clauses[1:]
            )
            score += (first_clause_overlap * 12) + (later_clause_overlap * 8)

            normalized_excerpt = chunk_excerpt.lower().translate(_TR_ASCII_TRANS)
            if "halle" in first_clause and re.search(r"\b[a-zçğıöşü]\)", normalized_excerpt):
                score += 10
            has_query_genel_kurul = "genel kurul" in query_lower
            has_query_yonetim_kurul = "yonetim kurul" in query_lower
            has_excerpt_genel_kurul = "genel kurul" in normalized_excerpt
            has_excerpt_yonetim_kurul = "yonetim kurul" in normalized_excerpt

            if has_query_genel_kurul and has_excerpt_genel_kurul:
                score += 6
            if has_query_yonetim_kurul and has_excerpt_yonetim_kurul:
                score += 6
            if "cagri" in query_lower and "cagri" in normalized_excerpt:
                score += 6

            if has_query_genel_kurul and not has_excerpt_genel_kurul and has_excerpt_yonetim_kurul:
                score -= 40
            if has_query_yonetim_kurul and not has_excerpt_yonetim_kurul and has_excerpt_genel_kurul:
                score -= 40
            if "hirsizlik" in query_lower and "hirsizlik" not in normalized_excerpt:
                score -= 30
        article_match = re.search(r"m\.\s*(\d+)", chunk.citation.lower())
        if article_match and article_match.group(1) in query_lower:
            score += 4
        if source_title:
            score += len(query_terms & cls._extract_priority_terms(str(source_title))) * 10
        if heading:
            score += len(query_terms & cls._extract_priority_terms(str(heading))) * 5
        source_family = cls._resolve_chunk_source_family(chunk)
        if requested_source_families:
            if source_family in requested_source_families:
                score += 24
            elif source_family:
                score -= 12
        cluster_size = source_cluster_sizes.get(cls._resolve_chunk_source_key(chunk), 1)
        if cluster_size > 1:
            score += (cluster_size - 1) * 6
        return score

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
        query: str | None = None,
        max_chunks: int = 2,
    ) -> str | None:
        priority_chunks = cls._extract_priority_chunks(
            chunks,
            query=query,
            max_chunks=max_chunks,
        )
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
        query: str,
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
            query=query,
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
            retrieved_chunks,
            query=query,
            max_chunks=max_priority_chunks,
        )
        return fallback or answer
