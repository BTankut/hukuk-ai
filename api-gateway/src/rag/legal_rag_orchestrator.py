from __future__ import annotations

import os
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from data_pipeline.judicial import (
    JudicialHybridRetriever,
    PersistentJudicialExactLookupStore,
    query_judicial_lexical_index,
    validate_judicial_evidence_results,
)
from rag.query_analyzer import analyze_query
from rag.retriever import RetrievalResult


_TR_ASCII_TRANSLATION = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "İ": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "â": "a",
        "î": "i",
        "û": "u",
    }
)
_LEGAL_NO_RE = r"\d{4}/\d{1,8}"
_E_RE = re.compile(r"(?:\bE\.?|ESAS(?:\s+NO)?)[\s:.-]*(?P<value>" + _LEGAL_NO_RE + r")", re.IGNORECASE)
_K_RE = re.compile(r"(?:\bK\.?|KARAR(?:\s+NO)?)[\s:.-]*(?P<value>" + _LEGAL_NO_RE + r")", re.IGNORECASE)
_DATE_RE = re.compile(r"\b(?P<date>\d{4}-\d{2}-\d{2}|\d{1,2}[./]\d{1,2}[./]\d{4})\b")
_SHA256_RE = re.compile(r"\b[0-9a-f]{64}\b", re.IGNORECASE)
_CANONICAL_ID_RE = re.compile(r"\bjudicial_decision:[A-Za-z0-9_./:-]+\b")
_COURT_HINTS = (
    ("yargitay", "Yargıtay"),
    ("danistay", "Danıştay"),
    ("anayasa mahkemesi", "Anayasa Mahkemesi"),
    ("bolge adliye mahkemesi", "Bölge Adliye Mahkemesi"),
    ("bolge idare mahkemesi", "Bölge İdare Mahkemesi"),
)
_JUDICIAL_TERMS = {
    "emsal",
    "ictihat",
    "içtihat",
    "yargitay",
    "yargıtay",
    "danistay",
    "danıştay",
    "aym",
    "karar",
    "esas",
    "karar no",
    "hukuk dairesi",
    "ceza dairesi",
    "genel kurul",
}
_LEGISLATION_TERMS = {
    "kanun",
    "madde",
    "mevzuat",
    "tbk",
    "tmk",
    "tck",
    "hmk",
    "cmk",
    "ttk",
    "ik",
    "iik",
    "kvkk",
}


@dataclass(frozen=True, slots=True)
class LegalRuntimeConfig:
    judicial_runtime_enabled: bool
    processed_dir: Path
    exact_lookup_path: Path
    lexical_index_path: Path
    vector_collection: str = "judicial_decisions_v1_shadow"
    vector_enabled: bool = False
    mevzuat_top_k: int = 6
    judicial_top_k: int = 20
    max_judicial_decisions: int = 5
    max_chunks_per_decision: int = 2
    request_timeout_ms: int = 8000

    @classmethod
    def from_settings(cls, settings: Any) -> "LegalRuntimeConfig":
        processed_dir = Path(
            getattr(
                settings,
                "judicial_processed_dir",
                os.getenv("JUDICIAL_PROCESSED_DIR", "/Users/btmacstudio/Projects/yargi/_work/final_package/processed"),
            )
        )
        return cls(
            judicial_runtime_enabled=bool(getattr(settings, "judicial_runtime_enabled", False)),
            processed_dir=processed_dir,
            exact_lookup_path=Path(
                getattr(settings, "judicial_exact_lookup_path", processed_dir / "judicial_exact_lookup.sqlite")
            ),
            lexical_index_path=Path(
                getattr(settings, "judicial_lexical_index_path", processed_dir / "judicial_lexical_index.sqlite")
            ),
            vector_collection=str(getattr(settings, "judicial_vector_collection", "judicial_decisions_v1_shadow")),
            vector_enabled=bool(getattr(settings, "judicial_vector_enabled", False)),
        )


@dataclass(slots=True)
class LegalEvidence:
    source_type: str
    text: str
    citation: str
    metadata: dict[str, Any]
    score: float = 0.0
    retrieval_lane: str = "unknown"
    score_components: dict[str, float] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "text": self.text,
            "citation": self.citation,
            "metadata": self.metadata,
            "score": self.score,
            "retrieval_lane": self.retrieval_lane,
            "score_components": self.score_components,
        }


@dataclass(slots=True)
class LegalRuntimeResponse:
    handled: bool
    answer: str
    citations: list[str]
    blocked: bool
    guardrails_reasons: list[str]
    verification: dict[str, Any] | None
    final_mode: str
    final_reason: str | None
    answer_contract: dict[str, Any]
    trace: dict[str, Any]
    usage: dict[str, int] | None = None


@dataclass(slots=True)
class LegalRoute:
    route: str
    confidence: float
    judicial_requested: bool
    legislation_requested: bool
    exact_key_type: str | None = None
    exact_key: str | None = None
    judicial_filters: dict[str, Any] = field(default_factory=dict)


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower().translate(_TR_ASCII_TRANSLATION)


def _parse_tr_date(value: str) -> str:
    match = _DATE_RE.search(value)
    if not match:
        return ""
    token = match.group("date")
    if "-" in token:
        return token
    day, month, year = re.split(r"[./]", token)
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _extract_court(query: str) -> str | None:
    normalized = _norm(query)
    for needle, court in _COURT_HINTS:
        if needle in normalized:
            return court
    trial_court = re.search(
        r"\b([A-ZÇĞİÖŞÜa-zçğıöşü]+(?:\s+\d+\.?)?\s+"
        r"(?:ASL[İI]YE|SULH|[İI]Ş|IS|T[İI]CARET|TICARET|AĞIR|AGIR|BÖLGE|BOLGE|"
        r"[İI]DARE|IDARE|HUKUK|CEZA)"
        r"[A-ZÇĞİÖŞÜa-zçğıöşü0-9.\s]*?MAHKEMES[İI])\b",
        query,
        flags=re.IGNORECASE,
    )
    if trial_court:
        cleaned = re.sub(r"\s+", " ", trial_court.group(1)).strip()
        return re.sub(r"^(?:ve|ile)\s+", "", cleaned, flags=re.IGNORECASE)
    court_match = re.search(
        r"([A-ZÇĞİÖŞÜa-zçğıöşü\s\d.]+MAHKEMES[İI])",
        query,
        flags=re.IGNORECASE,
    )
    if court_match:
        cleaned = re.sub(r"\s+", " ", court_match.group(1)).strip()
        return re.sub(r"^(?:ve|ile)\s+", "", cleaned, flags=re.IGNORECASE)
    return None


def _extract_chamber(query: str) -> str | None:
    normalized = _norm(query)
    compact = re.search(r"\b(?P<num>\d{1,2})\s*(?P<kind>hd|cd)\b", normalized, flags=re.IGNORECASE)
    if compact:
        return f"{compact.group('num')}{compact.group('kind').upper()}"
    verbose = re.search(
        r"\b(?P<num>\d{1,2})\.?\s*(?P<kind>hukuk|ceza)\s+dairesi\b",
        normalized,
        flags=re.IGNORECASE,
    )
    if verbose:
        suffix = "HD" if verbose.group("kind") == "hukuk" else "CD"
        return f"{verbose.group('num')}{suffix}"
    if "genel kurul" in normalized:
        return "GENEL KURUL"
    return None


def _extract_exact_lookup(query: str) -> tuple[str | None, str | None, dict[str, Any]]:
    canonical = _CANONICAL_ID_RE.search(query)
    if canonical:
        return "canonical_decision_id", canonical.group(0), {}
    sha = _SHA256_RE.search(query)
    if sha:
        return "document_hash", sha.group(0).lower(), {}
    url = re.search(r"https?://\S+", query)
    if url:
        return "source_url", url.group(0).rstrip(".,;)"), {}
    e_match = _E_RE.search(query)
    k_match = _K_RE.search(query)
    if e_match and k_match:
        court = _extract_court(query)
        chamber = _extract_chamber(query) or "GENEL"
        decision_date = _parse_tr_date(query)
        filters: dict[str, Any] = {
            "esas_no": e_match.group("value"),
            "karar_no": k_match.group("value"),
        }
        if court:
            filters["court"] = court
        if chamber:
            filters["chamber"] = chamber
        if decision_date:
            filters["decision_date"] = decision_date
        if court and chamber and decision_date:
            return (
                "court_chamber_date_esas_karar",
                _composite_lookup_key(court, chamber, decision_date, e_match.group("value"), k_match.group("value")),
                filters,
            )
        if court and chamber:
            return (
                "court_chamber_esas_karar",
                _composite_lookup_key(court, chamber, e_match.group("value"), k_match.group("value")),
                filters,
            )
    return None, None, {}


def _composite_lookup_key(*values: Any) -> str:
    return "|".join(re.sub(r"\s+", " ", str(value).strip()).lower() for value in values)


def _build_mevzuat_citation(result: RetrievalResult) -> str:
    metadata = dict(result.metadata or {})
    if getattr(result, "citation", None):
        return str(result.citation)
    law = (
        metadata.get("law_short_name")
        or metadata.get("kanun_kisa_adi")
        or metadata.get("law_no")
        or metadata.get("kanun_no")
        or metadata.get("source_title")
        or metadata.get("belge_adi")
        or "Mevzuat"
    )
    article = metadata.get("madde_no") or metadata.get("article_no")
    return f"{law} m.{article}" if article else str(law)


def _build_judicial_citation(result: dict[str, Any]) -> str:
    court = re.sub(r"\s+", " ", str(result.get("court") or "")).strip()
    chamber = re.sub(r"\s+", " ", str(result.get("chamber") or "")).strip()
    return (
        f"{court} {chamber}, {result.get('decision_date')}, "
        f"E. {result.get('esas_no')} K. {result.get('karar_no')}, "
        f"p.{result.get('paragraph_start')}-{result.get('paragraph_end')}, "
        f"{result.get('citation_key')}"
    )


class LegalRagOrchestrator:
    def __init__(self, *, config: LegalRuntimeConfig, mevzuat_retriever: Any | None = None) -> None:
        self.config = config
        self.mevzuat_retriever = mevzuat_retriever
        self._exact_store: PersistentJudicialExactLookupStore | None = None
        self._hybrid: JudicialHybridRetriever | None = None
        self._status = self._validate_status()
        if self._status["judicial_ready"]:
            self._exact_store = PersistentJudicialExactLookupStore(config.exact_lookup_path, read_only=True)
            self._hybrid = JudicialHybridRetriever(
                exact_store=self._exact_store,
                lexical_index_path=config.lexical_index_path,
                vector_ready=False,
            )

    @classmethod
    def from_settings(cls, settings: Any, *, mevzuat_retriever: Any | None = None) -> "LegalRagOrchestrator":
        return cls(config=LegalRuntimeConfig.from_settings(settings), mevzuat_retriever=mevzuat_retriever)

    def health(self) -> dict[str, Any]:
        return dict(self._status)

    def should_handle(self, query: str) -> bool:
        route = self.route_query(query)
        return route.route != "unsupported_or_out_of_scope"

    def route_query(self, query: str) -> LegalRoute:
        normalized = _norm(query)
        analysis = analyze_query(query)
        exact_key_type, exact_key, filters = _extract_exact_lookup(query)
        has_exact = exact_key_type is not None and exact_key is not None
        judicial_score = sum(1 for term in _JUDICIAL_TERMS if term in normalized)
        legislation_score = (
            len(analysis.article_refs)
            + len(analysis.law_mentions)
            + len(analysis.law_numbers)
            + sum(1 for term in _LEGISLATION_TERMS if term in normalized)
        )
        if has_exact:
            return LegalRoute(
                route="exact_judicial_decision_lookup",
                confidence=0.95,
                judicial_requested=True,
                legislation_requested=bool(legislation_score),
                exact_key_type=exact_key_type,
                exact_key=exact_key,
                judicial_filters=filters,
            )
        if judicial_score and legislation_score:
            return LegalRoute("mixed_legislation_and_judicial", 0.82, True, True, judicial_filters=filters)
        if judicial_score:
            return LegalRoute("judicial_only", 0.78, True, False, judicial_filters=filters)
        if legislation_score:
            return LegalRoute("legislation_only", 0.74, False, True)
        if analysis.insufficient_query:
            return LegalRoute("unsupported_or_out_of_scope", 0.6, False, False)
        return LegalRoute("legislation_only", 0.52, False, True)

    def answer(self, *, query: str, top_k: int = 20, law_filter: str | None = None) -> LegalRuntimeResponse:
        started = time.perf_counter()
        route = self.route_query(query)
        if route.route == "unsupported_or_out_of_scope":
            return self._response(
                answer="Bu soru için güvenilir hukuki kaynak tespiti yapamadım. Daha somut bir mevzuat maddesi veya karar bilgisi verirseniz kaynaklı yanıt verebilirim.",
                citations=[],
                blocked=True,
                final_mode="refusal",
                final_reason="unsupported_or_out_of_scope",
                route=route,
                mevzuat_evidence=[],
                judicial_evidence=[],
                started=started,
            )

        mevzuat_evidence: list[LegalEvidence] = []
        judicial_evidence: list[LegalEvidence] = []
        if route.legislation_requested:
            mevzuat_evidence = self._retrieve_mevzuat(query=query, top_k=min(top_k, self.config.mevzuat_top_k), law_filter=law_filter)
        if route.judicial_requested:
            if not self.config.judicial_runtime_enabled:
                return self._response(
                    answer=(
                        "Yargı kararı veya içtihat gerektiren bu soruda yargısal runtime kapalı olduğu için "
                        "karar dayanağı üretmiyorum. Mevzuat sorusu olarak yeniden sorarsanız mevzuat kaynaklarıyla yanıtlayabilirim."
                    ),
                    citations=[],
                    blocked=True,
                    final_mode="refusal",
                    final_reason="judicial_runtime_disabled",
                    route=route,
                    mevzuat_evidence=mevzuat_evidence,
                    judicial_evidence=[],
                    started=started,
                )
            if not self._status["judicial_ready"]:
                return self._response(
                    answer="Yargısal runtime etkin görünüyor ancak gerekli persistent karar indeksleri hazır değil; yargı kararı dayanaklı yanıt vermiyorum.",
                    citations=[],
                    blocked=True,
                    final_mode="refusal",
                    final_reason="judicial_indexes_unavailable",
                    route=route,
                    mevzuat_evidence=mevzuat_evidence,
                    judicial_evidence=[],
                    started=started,
                )
            judicial_evidence = self._retrieve_judicial(query=query, route=route, top_k=min(top_k, self.config.judicial_top_k))
            if not judicial_evidence:
                return self._response(
                    answer="Bu yargı kararı/içtihat sorusu için seçilebilir, tam metadata taşıyan yargısal kanıt bulunamadı; karar sonucu veya içtihat iddiası üretmiyorum.",
                    citations=[evidence.citation for evidence in mevzuat_evidence],
                    blocked=True,
                    final_mode="refusal",
                    final_reason="judicial_evidence_not_found",
                    route=route,
                    mevzuat_evidence=mevzuat_evidence,
                    judicial_evidence=[],
                    started=started,
                )

        if route.legislation_requested and not mevzuat_evidence and not judicial_evidence:
            return self._response(
                answer="Bu mevzuat sorusu için runtime içinde yeterli mevzuat kanıtı bulunamadı; kaynak göstermeden hukuki sonuç üretmiyorum.",
                citations=[],
                blocked=True,
                final_mode="refusal",
                final_reason="mevzuat_evidence_not_found",
                route=route,
                mevzuat_evidence=[],
                judicial_evidence=[],
                started=started,
            )

        verification = self._verify_evidence(route=route, mevzuat_evidence=mevzuat_evidence, judicial_evidence=judicial_evidence)
        if not verification["pass"]:
            return self._response(
                answer="Seçilen kanıtlar cevap sözleşmesini karşılamadığı için kaynaklı yanıt üretmiyorum.",
                citations=[],
                blocked=True,
                final_mode="refusal",
                final_reason="evidence_contract_failed",
                route=route,
                mevzuat_evidence=mevzuat_evidence,
                judicial_evidence=judicial_evidence,
                verification=verification,
                started=started,
            )

        answer = self._compose_answer(
            query=query,
            route=route,
            mevzuat_evidence=mevzuat_evidence,
            judicial_evidence=judicial_evidence,
        )
        citations = [evidence.citation for evidence in [*mevzuat_evidence, *judicial_evidence]]
        return self._response(
            answer=answer,
            citations=citations,
            blocked=False,
            final_mode="answer",
            final_reason=None,
            route=route,
            mevzuat_evidence=mevzuat_evidence,
            judicial_evidence=judicial_evidence,
            verification=verification,
            started=started,
        )

    def _validate_status(self) -> dict[str, Any]:
        exact_exists = self.config.exact_lookup_path.exists()
        lexical_exists = self.config.lexical_index_path.exists()
        processed_exists = self.config.processed_dir.exists()
        return {
            "runtime": "legal_rag",
            "judicial_runtime_enabled": self.config.judicial_runtime_enabled,
            "processed_dir": str(self.config.processed_dir),
            "exact_lookup_path": str(self.config.exact_lookup_path),
            "lexical_index_path": str(self.config.lexical_index_path),
            "processed_dir_exists": processed_exists,
            "exact_lookup_exists": exact_exists,
            "lexical_index_exists": lexical_exists,
            "judicial_ready": processed_exists and exact_exists and lexical_exists,
            "vector_index_status": "unavailable" if not self.config.vector_enabled else "not_built",
            "mevzuat_retriever": "available" if self.mevzuat_retriever is not None else "unavailable",
        }

    def _retrieve_mevzuat(self, *, query: str, top_k: int, law_filter: str | None) -> list[LegalEvidence]:
        if self.mevzuat_retriever is None:
            return []
        metadata_filter = None
        if law_filter:
            from rag.retriever import MetadataFilter

            metadata_filter = MetadataFilter(law_short_name=law_filter)
        try:
            results, _stats = self.mevzuat_retriever.retrieve(query=query, top_k=top_k, metadata_filter=metadata_filter)
        except TypeError:
            results, _stats = self.mevzuat_retriever.retrieve(query=query, top_k=top_k)
        evidence: list[LegalEvidence] = []
        seen: set[str] = set()
        for result in results:
            citation = _build_mevzuat_citation(result)
            if citation in seen:
                continue
            seen.add(citation)
            metadata = dict(result.metadata or {})
            metadata["source_type"] = metadata.get("source_type") or "legislation"
            evidence.append(
                LegalEvidence(
                    source_type="legislation",
                    text=str(result.text),
                    citation=citation,
                    metadata=metadata,
                    score=float(result.score or 0.0),
                    retrieval_lane="mevzuat",
                    score_components={"mevzuat": float(result.score or 0.0)},
                )
            )
            if len(evidence) >= self.config.mevzuat_top_k:
                break
        return evidence

    def _retrieve_judicial(self, *, query: str, route: LegalRoute, top_k: int) -> list[LegalEvidence]:
        if self._hybrid is None:
            return []
        filters = dict(route.judicial_filters)
        results: list[dict[str, Any]]
        if route.exact_key_type and route.exact_key:
            results = self._hybrid.retrieve(
                query=query,
                exact_key_type=route.exact_key_type,
                exact_key=route.exact_key,
                filters={
                    key: value
                    for key, value in filters.items()
                    if key in {"court", "chamber", "year", "decision_date", "esas_no", "karar_no"}
                },
                top_k=top_k,
            )
            results = [
                result
                for result in results
                if {"exact", "exact_metadata"} & set((result.get("score_components") or {}).keys())
            ]
        else:
            results = query_judicial_lexical_index(
                self.config.lexical_index_path,
                query,
                filters={key: value for key, value in filters.items() if key in {"court", "chamber", "year", "decision_date", "esas_no", "karar_no"}},
                top_k=top_k,
            )
            for result in results:
                result["score_components"] = {"lexical": float(result.get("score") or 0.0)}
        validation = validate_judicial_evidence_results(results)
        if not validation["pass"]:
            return []
        by_decision: Counter[str] = Counter()
        selected: list[LegalEvidence] = []
        decision_order: list[str] = []
        for result in results:
            canonical_id = str(result.get("canonical_decision_id") or "")
            if by_decision[canonical_id] == 0:
                decision_order.append(canonical_id)
            if len(decision_order) > self.config.max_judicial_decisions and by_decision[canonical_id] == 0:
                continue
            if by_decision[canonical_id] >= self.config.max_chunks_per_decision:
                continue
            by_decision[canonical_id] += 1
            citation = _build_judicial_citation(result)
            metadata = dict(result.get("metadata") or {})
            metadata["source_type"] = "judicial_decision"
            selected.append(
                LegalEvidence(
                    source_type="judicial_decision",
                    text=str(result.get("selected_chunk_text") or result.get("text") or ""),
                    citation=citation,
                    metadata=metadata,
                    score=float(result.get("final_score") or result.get("score") or 0.0),
                    retrieval_lane=str(result.get("retrieval_lane") or "lexical"),
                    score_components=dict(result.get("score_components") or {"lexical": float(result.get("score") or 0.0)}),
                )
            )
        return selected

    def _verify_evidence(
        self,
        *,
        route: LegalRoute,
        mevzuat_evidence: list[LegalEvidence],
        judicial_evidence: list[LegalEvidence],
    ) -> dict[str, Any]:
        failures: list[str] = []
        if route.legislation_requested and not mevzuat_evidence:
            failures.append("statutory_claim_without_mevzuat_evidence")
        if route.judicial_requested and not judicial_evidence:
            failures.append("judicial_claim_without_judicial_evidence")
        if route.judicial_requested and not self.config.judicial_runtime_enabled:
            failures.append("judicial_claim_runtime_disabled")
        for evidence in mevzuat_evidence:
            if evidence.source_type != "legislation":
                failures.append("mevzuat_source_type_confusion")
            if not (evidence.metadata.get("madde_no") or evidence.metadata.get("article_no")):
                failures.append("mevzuat_article_metadata_missing")
        for evidence in judicial_evidence:
            if evidence.source_type != "judicial_decision":
                failures.append("judicial_source_type_confusion")
            for field_name in ("court", "chamber", "decision_date", "esas_no", "karar_no", "citation_key"):
                if not evidence.metadata.get(field_name):
                    failures.append(f"judicial_{field_name}_missing")
        return {
            "pass": not failures,
            "failures": sorted(set(failures)),
            "source_type_confusion": any("confusion" in failure for failure in failures),
            "mevzuat_evidence_count": len(mevzuat_evidence),
            "judicial_evidence_count": len(judicial_evidence),
        }

    def _compose_answer(
        self,
        *,
        query: str,
        route: LegalRoute,
        mevzuat_evidence: list[LegalEvidence],
        judicial_evidence: list[LegalEvidence],
    ) -> str:
        lines = [f"1. Kısa sonuç\nSoru, `{route.route}` kapsamında kaynaklı olarak değerlendirildi."]
        if mevzuat_evidence:
            lines.append("2. Mevzuat dayanağı")
            for evidence in mevzuat_evidence[: self.config.mevzuat_top_k]:
                excerpt = re.sub(r"\s+", " ", evidence.text).strip()[:360]
                lines.append(f"- {excerpt} [Kaynak: {evidence.citation}]")
        elif route.legislation_requested:
            lines.append("2. Mevzuat dayanağı\n- Seçilebilir mevzuat kanıtı bulunamadı; kanun maddesi iddiası kurulmadı.")
        if judicial_evidence:
            lines.append("3. Yargı kararları / içtihat değerlendirmesi")
            for evidence in judicial_evidence:
                excerpt = re.sub(r"\s+", " ", evidence.text).strip()[:360]
                lines.append(f"- {excerpt} [Karar: {evidence.citation}]")
        elif route.judicial_requested:
            lines.append("3. Yargı kararları / içtihat değerlendirmesi\n- Seçilebilir yargı kararı kanıtı bulunamadı; içtihat iddiası kurulmadı.")
        lines.append(
            "4. Uygulama sonucu ve riskler\n"
            "Mevzuat hükümleri bağlayıcı kural olarak, yargı kararları ise somut olay uygulaması ve yorum desteği olarak ayrı değerlendirilmelidir."
        )
        return "\n\n".join(lines)

    def _response(
        self,
        *,
        answer: str,
        citations: list[str],
        blocked: bool,
        final_mode: str,
        final_reason: str | None,
        route: LegalRoute,
        mevzuat_evidence: list[LegalEvidence],
        judicial_evidence: list[LegalEvidence],
        started: float,
        verification: dict[str, Any] | None = None,
    ) -> LegalRuntimeResponse:
        evidence = [*mevzuat_evidence, *judicial_evidence]
        contract = {
            "answer_text": answer,
            "final_mode": final_mode,
            "route": route.route,
            "source_types": sorted({item.source_type for item in evidence}),
            "mevzuat_evidence_count": len(mevzuat_evidence),
            "judicial_evidence_count": len(judicial_evidence),
            "judicial_runtime_enabled": self.config.judicial_runtime_enabled,
            "citation_contract": "complete" if citations or blocked else "no_evidence",
        }
        trace = {
            "decision_lane": "legal_rag_runtime",
            "route": route.route,
            "route_confidence": route.confidence,
            "judicial_runtime_enabled": self.config.judicial_runtime_enabled,
            "judicial_index_status": self._status,
            "evidence": [item.to_public() for item in evidence],
            "answer_contract": contract,
            "final_mode": final_mode,
            "final_reason": final_reason,
            "latency_ms": round((time.perf_counter() - started) * 1000.0, 3),
        }
        return LegalRuntimeResponse(
            handled=True,
            answer=answer,
            citations=citations,
            blocked=blocked,
            guardrails_reasons=[final_reason] if blocked and final_reason else [],
            verification=verification,
            final_mode=final_mode,
            final_reason=final_reason,
            answer_contract=contract,
            trace=trace,
            usage=None,
        )
