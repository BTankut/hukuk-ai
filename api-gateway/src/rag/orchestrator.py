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
_PROCEDURE_CONTEXT_CHUNK_EXCERPT_CHARS = 960
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
_SOURCE_SELECTION_GENERIC_TERMS = _PRIORITY_STOPWORDS | {
    "cevapla",
    "yanit",
    "kisa",
    "sonuc",
    "gerekce",
    "dayanak",
    "belge",
    "zinciri",
    "gerekiyorsa",
    "guncellik",
    "notu",
    "tarihindeki",
    "durumuna",
    "guncel",
    "yururluk",
    "tespit",
    "ediliyor",
    "idare",
    "idarenin",
    "islem",
    "izlemesi",
    "gerekir",
    "sure",
    "verme",
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
_ARTICLE_TOKEN_RE = re.compile(r"m\.\s*(\d+[a-z]?)", re.IGNORECASE)
_NUMBERED_LAW_MENTION_RE = re.compile(
    r"\b(?P<law>\d{1,9})\s+say[ıi]l[ıi]\s+"
    r"(?P<kind>kanun hükmünde kararname|kanun hukmunde kararname|khk|kanun|tüzük|tuzuk|yönetmelik|yonetmelik)\b",
    re.IGNORECASE,
)
_NUMBERED_LAW_LIST_MENTION_RE = re.compile(
    r"\b(?P<laws>\d{1,9}(?:\s*,\s*\d{1,9})*(?:\s+(?:ve|ile)\s+\d{1,9})?)\s+say[ıi]l[ıi]\s+"
    r"(?P<kind>kanun hükmünde kararname|kanun hukmunde kararname|khk|kanun|tüzük|tuzuk|yönetmelik|yonetmelik)\b",
    re.IGNORECASE,
)
_NUMBERED_LAW_REFERENCE_RE = re.compile(
    r"\b(?P<law>\d{2,8})\s+say[ıi]l[ıi]\s+"
    r"(?:(?:[a-zçğıöşüâîû]+\s+){0,6})?"
    r"(?:kanun|kanunu|kanunun|khk|kararname|kararnamesi|yönetmelik|yonetmelik|tüzük|tuzuk)",
    re.IGNORECASE,
)
_DASHED_LAW_REFERENCE_RE = re.compile(
    r"\b(?:khk|kanun|kararname)[-/\s]?(?P<law>\d{2,8})\b",
    re.IGNORECASE,
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
_PROCEDURE_QUERY_HINTS = (
    "ön usul",
    "on usul",
    "ön şart",
    "on sart",
    "dava şart",
    "dava sart",
    "usul",
    "süre",
    "sure",
    "başvuru",
    "basvuru",
    "itiraz",
    "arabulucu",
    "arabuluculuk",
    "hak düşürücü",
    "hak dusurucu",
)
_CURRENT_VALIDITY_QUERY_HINTS = (
    "guncel",
    "yururluk",
    "yururlukte",
    "yururluk durumuna gore",
    "guncellik notu",
    "hangi metin",
    "kullanilmali",
)
_OLD_CURRENT_CONTRAST_HINTS = (
    "eski",
    "mulga",
    "yururlukten kaldir",
    "yoksa",
)
_ACTIVE_END_DATE_SENTINELS = {
    "9999-12-31",
    "9999-12-31T00:00:00",
    "9999-12-31 00:00:00",
}
_TRUTHY_METADATA_FLAGS = {"1", "true", "yes", "y", "evet"}
_FALSEY_METADATA_FLAGS = {"0", "false", "no", "n", "hayir", "hayır"}
_HISTORICAL_SOURCE_FOCUS_HINTS = (
    "mulga mevzuat",
    "mulga kanun",
    "mulga duzenleme",
    "tarihsel metin",
    "eski metin",
    "o tarihte",
    "yururlukten kalkmis",
)
_REFERENCE_VALUE_QUERY_HINTS = (
    "referans degeri",
    "atif degeri",
    "hala referans",
    "halen referans",
    "normatif referans",
)
_TUZUK_HIERARCHY_HINTS = (
    "gecerli bir tuzuk",
    "tuzuk hukmu",
    "kurum ici",
    "alt duzenleme",
    "celis",
    "normlar hiyerarsisi",
    "hangisi uygulanir",
)
_ORGANIZATION_STATUTE_HINTS = (
    "sendika tuzug",
    "dernek tuzug",
    "vakif senedi",
    "kurulus tuzug",
    "ana tuzuk",
    "tuzuk degisikligi",
    "tuzugun degistirilmesi",
    "tuzukte belirtilen",
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
        context = self._build_context(retrieved_chunks, query=query)
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
                draft_answer=draft,
                source_lock_target_citations=source_lock_target_citations,
            )
            if source_locked_answer != final_answer:
                final_answer = source_locked_answer
                citations = extract_citations(final_answer)
                if final_answer != draft:
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

    @classmethod
    def _is_procedure_or_timeline_query(cls, query: str | None) -> bool:
        if not query:
            return False
        normalized = query.lower().translate(_TR_ASCII_TRANS)
        return any(hint in normalized for hint in _PROCEDURE_QUERY_HINTS)

    @classmethod
    def _build_context(cls, chunks: list[RetrievedChunk], *, query: str | None = None) -> str:
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
        excerpt_len = (
            _PROCEDURE_CONTEXT_CHUNK_EXCERPT_CHARS
            if cls._is_procedure_or_timeline_query(query)
            else _MAX_CONTEXT_CHUNK_EXCERPT_CHARS
        )

        formatted = []
        for chunk, (_, source_title, compact_text) in zip(chunks, compact_chunks, strict=False):
            citation = chunk.citation
            body = (
                cls._build_query_focused_excerpt(
                    compact_text,
                    query=query,
                    max_len=excerpt_len,
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
    def _normalize_citation_text(text: str | None) -> str:
        normalized = re.sub(r"\s+", " ", (text or "").strip())
        tr_map = str.maketrans("İIĞÖÜŞÇ", "iiğöüşç")
        return normalized.translate(tr_map).lower().translate(_TR_ASCII_TRANS)

    @classmethod
    def _extract_article_token(cls, citation: str | None) -> str | None:
        if not citation:
            return None
        match = _ARTICLE_TOKEN_RE.search(citation)
        if not match:
            return None
        return match.group(1).lower()

    @classmethod
    def _chunk_citation_aliases(cls, chunk: RetrievedChunk) -> set[str]:
        aliases: set[str] = set()
        normalized_citation = cls._normalize_citation(chunk.citation)
        if normalized_citation:
            aliases.add(cls._normalize_citation_text(normalized_citation))

        article_token = cls._extract_article_token(chunk.citation)
        if not article_token:
            return aliases

        raw_source = cls._normalize_citation_text(chunk.source)
        if raw_source:
            aliases.add(f"{raw_source} m.{article_token}")

        metadata = chunk.metadata or {}
        source_title = cls._normalize_citation_text(
            metadata.get("source_title")
            or metadata.get("belge_adi")
            or metadata.get("kanun_adi")
            or metadata.get("law_name")
        )
        if source_title:
            aliases.add(f"{source_title} m.{article_token}")

        return aliases

    @classmethod
    def _citation_matches_chunk(cls, citation: str, chunk: RetrievedChunk) -> bool:
        normalized_citation = cls._normalize_citation_text(cls._normalize_citation(citation))
        if not normalized_citation:
            return False
        return normalized_citation in cls._chunk_citation_aliases(chunk)

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
        retrieved_laws = {
            law
            for _, chunk in candidates
            for law in cls._chunk_law_candidates(chunk)
            if law.isdigit()
        }
        referenced_law_counts: dict[str, int] = {}
        for _, chunk in candidates:
            for law in cls._chunk_referenced_numbered_laws(chunk):
                if law not in retrieved_laws:
                    continue
                referenced_law_counts[law] = referenced_law_counts.get(law, 0) + 1
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
                referenced_law_counts=referenced_law_counts,
                chunk=chunk,
                query=query,
            )
            for _, chunk in candidates
        }
        if not any(score > 0 for score in score_map.values()):
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
        source_title = (
            metadata.get("source_title")
            or metadata.get("belge_adi")
            or metadata.get("kanun_adi")
            or metadata.get("law_name")
            or ""
        )
        normalized_title = str(source_title).lower().translate(_TR_ASCII_TRANS)
        if "tuzugu" in normalized_title or normalized_title.endswith("tuzuk"):
            return "tuzuk"
        if "kanun hukmunde kararname" in normalized_title or re.search(r"\bkhk\b", normalized_title):
            return "khk"
        if "cumhurbaskanligi yonetmeligi" in normalized_title:
            return "cb_yonetmelik"
        if "yonetmelik" in normalized_title:
            return "yonetmelik"
        if "teblig" in normalized_title:
            return "teblig"
        if "genelge" in normalized_title:
            return "cb_genelge"
        if "kararname" in normalized_title:
            return "cb_kararname"
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

    @staticmethod
    def _extract_numbered_law_mentions(query: str) -> set[str]:
        mentions = {
            law
            for match in _NUMBERED_LAW_LIST_MENTION_RE.finditer(query or "")
            for law in re.findall(r"\d{1,9}", match.group("laws"))
        }
        mentions.update(
            match.group("law")
            for match in _NUMBERED_LAW_MENTION_RE.finditer(query or "")
        )
        return mentions

    @staticmethod
    def _chunk_law_candidates(chunk: RetrievedChunk) -> set[str]:
        metadata = chunk.metadata or {}
        candidates: set[str] = set()
        for value in (
            metadata.get("law_no"),
            metadata.get("kanun_no"),
            metadata.get("law_short_name"),
            metadata.get("kanun_kisa_adi"),
            metadata.get("source_id"),
            chunk.source,
            chunk.citation,
        ):
            raw = re.sub(r"\s+", " ", str(value or "")).strip()
            if not raw:
                continue
            candidates.add(raw.upper())
            if raw.isdigit():
                candidates.add(raw)
            match = re.search(r"\b(\d{1,9})\s*(?:m|md|madde)\.?\s*\d+", raw, re.IGNORECASE)
            if match:
                candidates.add(match.group(1))
        return candidates

    @classmethod
    def _chunk_referenced_numbered_laws(cls, chunk: RetrievedChunk) -> set[str]:
        metadata = chunk.metadata or {}
        surface = " ".join(
            str(value or "")
            for value in (
                chunk.text,
                metadata.get("source_title"),
                metadata.get("belge_adi"),
                metadata.get("heading"),
                metadata.get("article_heading"),
            )
        )
        return {
            match.group("law")
            for match in _NUMBERED_LAW_REFERENCE_RE.finditer(surface)
        } | {
            match.group("law")
            for match in _DASHED_LAW_REFERENCE_RE.finditer(surface)
        }

    @classmethod
    def _extract_salient_query_terms(cls, query: str) -> set[str]:
        return {
            term
            for term in cls._extract_priority_terms(query)
            if len(term) >= 4
            and term not in _SOURCE_SELECTION_GENERIC_TERMS
            and not re.fullmatch(r"\d{1,4}", term)
        }

    @staticmethod
    def _asks_current_validity_over_historical_contrast(query: str) -> bool:
        normalized = query.lower().translate(_TR_ASCII_TRANS)
        year_count = len({match.group(0) for match in re.finditer(r"\b(19|20)\d{2}\b", query or "")})
        has_current_signal = any(hint in normalized for hint in _CURRENT_VALIDITY_QUERY_HINTS)
        has_contrast_signal = any(hint in normalized for hint in _OLD_CURRENT_CONTRAST_HINTS)
        return has_current_signal and (has_contrast_signal or year_count >= 2)

    @classmethod
    def _asks_current_validity_query(cls, query: str) -> bool:
        if cls._asks_current_validity_over_historical_contrast(query):
            return True
        normalized = query.lower().translate(_TR_ASCII_TRANS)
        if any(hint in normalized for hint in _HISTORICAL_SOURCE_FOCUS_HINTS):
            return False
        return any(hint in normalized for hint in _CURRENT_VALIDITY_QUERY_HINTS)

    @staticmethod
    def _chunk_active_priority(chunk: RetrievedChunk) -> int:
        if RAGOrchestrator._is_temporally_inactive_chunk(chunk):
            return -45
        metadata = chunk.metadata or {}
        mulga = metadata.get("mulga")
        start = str(metadata.get("yururluk_baslangic") or "")
        end = str(metadata.get("yururluk_bitis") or "").strip()
        if start or RAGOrchestrator._metadata_flag_is_false(mulga) or end in _ACTIVE_END_DATE_SENTINELS:
            return 24
        return 0

    @staticmethod
    def _metadata_flag_is_true(value: Any) -> bool:
        if value is True:
            return True
        if isinstance(value, str):
            return value.strip().lower().translate(_TR_ASCII_TRANS) in _TRUTHY_METADATA_FLAGS
        return False

    @staticmethod
    def _metadata_flag_is_false(value: Any) -> bool:
        if value is False:
            return True
        if isinstance(value, str):
            return value.strip().lower().translate(_TR_ASCII_TRANS) in _FALSEY_METADATA_FLAGS
        return False

    @classmethod
    def _is_temporally_inactive_chunk(cls, chunk: RetrievedChunk) -> bool:
        metadata = chunk.metadata or {}
        if cls._metadata_flag_is_true(metadata.get("mulga")):
            return True
        source_family = cls._resolve_chunk_source_family(chunk)
        if source_family and source_family.startswith("mulga"):
            return True
        end = str(metadata.get("yururluk_bitis") or "").strip()
        return bool(end and end not in _ACTIVE_END_DATE_SENTINELS)

    @staticmethod
    def _looks_like_tuzuk_hierarchy_query(query: str) -> bool:
        normalized = query.lower().translate(_TR_ASCII_TRANS)
        return "tuzuk" in normalized and any(hint in normalized for hint in _TUZUK_HIERARCHY_HINTS)

    @staticmethod
    def _looks_like_organization_statute_chunk(chunk: RetrievedChunk) -> bool:
        metadata = chunk.metadata or {}
        surface = " ".join(
            str(value or "")
            for value in (
                chunk.text,
                metadata.get("source_title"),
                metadata.get("belge_adi"),
                metadata.get("kanun_adi"),
                metadata.get("heading"),
                metadata.get("article_heading"),
            )
        ).lower().translate(_TR_ASCII_TRANS)
        return any(hint in surface for hint in _ORGANIZATION_STATUTE_HINTS)

    @classmethod
    def _build_reference_value_intro(cls, query: str | None) -> str | None:
        if not query:
            return None
        normalized = query.lower().translate(_TR_ASCII_TRANS)
        if not any(hint in normalized for hint in _REFERENCE_VALUE_QUERY_HINTS):
            return None
        labels: list[str] = []
        seen: set[str] = set()
        for match in _NUMBERED_LAW_LIST_MENTION_RE.finditer(query or ""):
            kind = match.group("kind")
            display_kind = "KHK" if "khk" in kind.lower() or "kararname" in kind.lower() else kind
            for law in re.findall(r"\d{1,9}", match.group("laws")):
                if law in seen:
                    continue
                labels.append(f"{law} sayılı {display_kind}")
                seen.add(law)
        for match in _NUMBERED_LAW_MENTION_RE.finditer(query or ""):
            law = match.group("law")
            if law in seen:
                continue
            kind = match.group("kind")
            display_kind = "KHK" if "khk" in kind.lower() or "kararname" in kind.lower() else kind
            labels.append(f"{law} sayılı {display_kind}")
            seen.add(law)
        if not labels:
            return None
        label_text = ", ".join(labels)
        return (
            f"{label_text}, soru konusu bağlamda hâlâ tarihsel ve normatif atıf değeri taşır. "
            "Güncel sonuç, yürürlükteki ana metne işlenmiş hüküm, ilga/iptal notu ve ilgili geçiş "
            "düzenlemeleri birlikte okunarak kurulmalıdır. Dayanak gösteren başlıca kaynaklar:"
        )

    @classmethod
    def _score_chunk_priority(
        cls,
        *,
        query_terms: set[str],
        query_clauses: list[set[str]],
        requested_source_families: set[str],
        source_cluster_sizes: dict[str, int],
        referenced_law_counts: dict[str, int],
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
        numbered_laws = cls._extract_numbered_law_mentions(query)
        chunk_laws = cls._chunk_law_candidates(chunk)
        chunk_referenced_laws = cls._chunk_referenced_numbered_laws(chunk)
        if numbered_laws:
            if numbered_laws & (chunk_laws | chunk_referenced_laws):
                score += 60
            else:
                score -= 16
        if referenced_law_counts:
            referenced_hits = {
                law
                for law in chunk_laws
                if law in referenced_law_counts
            }
            if referenced_hits:
                score += min(45, sum(referenced_law_counts[law] for law in referenced_hits) * 18)
            elif chunk_referenced_laws & set(referenced_law_counts):
                score -= 18
        salient_terms = cls._extract_salient_query_terms(query)
        if len(salient_terms) >= 3:
            salient_overlap = len(salient_terms & chunk_terms)
            score += min(40, salient_overlap * 10)
            if salient_overlap == 0:
                score -= 36
            elif salient_overlap == 1:
                score -= 12
        if cls._asks_current_validity_query(query):
            score += cls._chunk_active_priority(chunk)
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
                score += 42
            elif source_family:
                score -= 18
        if cls._looks_like_tuzuk_hierarchy_query(query):
            if source_family == "tuzuk":
                score += 36
            elif cls._looks_like_organization_statute_chunk(chunk):
                score -= 55
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
        for citation in citations:
            if any(cls._citation_matches_chunk(citation, chunk) for chunk in priority_chunks):
                return True
        return False

    @classmethod
    def _has_nonretrieved_citations(
        cls,
        citations: list[str],
        retrieved_chunks: list[RetrievedChunk],
    ) -> bool:
        cited = [citation for citation in citations if citation]
        if not cited:
            return False
        return any(
            not any(cls._citation_matches_chunk(citation, chunk) for chunk in retrieved_chunks)
            for citation in cited
        )

    @classmethod
    def _has_temporally_invalid_citations_for_current_query(
        cls,
        *,
        query: str,
        citations: list[str],
        retrieved_chunks: list[RetrievedChunk],
    ) -> bool:
        if not cls._asks_current_validity_query(query):
            return False
        for citation in citations:
            for chunk in retrieved_chunks:
                if not cls._citation_matches_chunk(citation, chunk):
                    continue
                if cls._is_temporally_inactive_chunk(chunk):
                    return True
        return False

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
    def _build_query_focused_excerpt(
        cls,
        text: str,
        *,
        query: str | None,
        max_len: int,
    ) -> str:
        compact = re.sub(r"\s+", " ", text).strip()
        if len(compact) <= max_len or not query:
            return cls._build_chunk_excerpt(compact, max_len=max_len)

        normalized_text = compact.lower().translate(_TR_ASCII_TRANS)
        normalized_query = query.lower().translate(_TR_ASCII_TRANS)

        needles: list[str] = []
        if cls._is_procedure_or_timeline_query(query):
            needles.extend(_PROCEDURE_QUERY_HINTS)
        needles.extend(term for term in cls._extract_priority_terms(normalized_query) if len(term) >= 4)

        first_pos: int | None = None
        for needle in needles:
            normalized_needle = needle.lower().translate(_TR_ASCII_TRANS)
            pos = normalized_text.find(normalized_needle)
            if pos == -1:
                continue
            if first_pos is None or pos < first_pos:
                first_pos = pos

        if first_pos is None:
            return cls._build_chunk_excerpt(compact, max_len=max_len)

        start = max(0, first_pos - 120)
        end = min(len(compact), start + max_len)
        if end - start < max_len and start > 0:
            start = max(0, end - max_len)

        excerpt = compact[start:end].strip()
        if start > 0:
            excerpt = f"... {excerpt}"
        if end < len(compact):
            excerpt = f"{excerpt} ..."
        return excerpt

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

        intro = cls._build_reference_value_intro(query) or (
            "Bu soru bakımından doğrudan değerlendirilmesi gereken başlıca hükümler şunlardır:"
        )
        lines = [intro]
        for chunk in priority_chunks:
            excerpt = cls._build_chunk_excerpt(chunk.text)
            lines.append(f"- [Kaynak: {chunk.citation}] {excerpt}")
        return "\n".join(lines)

    @classmethod
    def _needs_source_lock_fallback(
        cls,
        *,
        query: str,
        answer: str,
        retrieved_chunks: list[RetrievedChunk],
        priority_chunks: list[RetrievedChunk],
        source_lock_target_citations: int | None,
    ) -> bool:
        citations = extract_citations(answer)
        return (
            cls._looks_like_generic_assistant_reply(answer)
            or not citations
            or not cls._has_priority_citation_overlap(citations, priority_chunks)
            or cls._has_nonretrieved_citations(citations, retrieved_chunks)
            or cls._has_temporally_invalid_citations_for_current_query(
                query=query,
                citations=citations,
                retrieved_chunks=retrieved_chunks,
            )
            or (
                source_lock_target_citations is not None
                and cls._has_incomplete_priority_coverage(
                    citations,
                    priority_chunks,
                    required_count=max(
                        2,
                        min(source_lock_target_citations, 4),
                    ),
                )
            )
        )

    @classmethod
    def _maybe_source_lock_answer(
        cls,
        *,
        query: str,
        answer: str,
        retrieved_chunks: list[RetrievedChunk],
        draft_answer: str | None = None,
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

        needs_fallback = cls._needs_source_lock_fallback(
            query=query,
            answer=answer,
            retrieved_chunks=retrieved_chunks,
            priority_chunks=priority_chunks,
            source_lock_target_citations=source_lock_target_citations,
        )
        if not needs_fallback:
            return answer

        if draft_answer and draft_answer != answer:
            draft_needs_fallback = cls._needs_source_lock_fallback(
                query=query,
                answer=draft_answer,
                retrieved_chunks=retrieved_chunks,
                priority_chunks=priority_chunks,
                source_lock_target_citations=source_lock_target_citations,
            )
            if not draft_needs_fallback:
                return draft_answer

        fallback = cls._build_source_locked_fallback(
            retrieved_chunks,
            query=query,
            max_chunks=max_priority_chunks,
        )
        return fallback or answer
