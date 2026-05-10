from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rag.query_analyzer import QueryAnalysis


@dataclass(frozen=True, slots=True)
class RetrievalStep:
    name: str
    reason: str
    budget: int

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "reason": self.reason, "budget": self.budget}


@dataclass(frozen=True, slots=True)
class RetrievalPlan:
    law_hints: list[str] = field(default_factory=list)
    source_family_hints: list[str] = field(default_factory=list)
    term_hints: list[str] = field(default_factory=list)
    exact_article_refs: list[dict[str, str | None]] = field(default_factory=list)
    article_ranges: list[dict[str, str]] = field(default_factory=list)
    temporal_intent: str = "current"
    date_filters: list[str] = field(default_factory=list)
    domain_signals: list[str] = field(default_factory=list)
    out_of_scope: bool = False
    insufficient_query: bool = False
    evidence_budget: dict[str, int] = field(default_factory=dict)
    steps: list[RetrievalStep] = field(default_factory=list)

    def to_router_plan(self) -> dict[str, Any]:
        return {
            "planner": "deterministic_query_analyzer_v1",
            "law_hints": self.law_hints,
            "source_family_hints": self.source_family_hints,
            "term_hints": self.term_hints,
            "exact_article_refs": self.exact_article_refs,
            "article_ranges": self.article_ranges,
            "temporal_intent": self.temporal_intent,
            "date_filters": self.date_filters,
            "domain_signals": self.domain_signals,
            "out_of_scope": self.out_of_scope,
            "insufficient_query": self.insufficient_query,
            "evidence_budget": self.evidence_budget,
            "steps": [step.to_dict() for step in self.steps],
        }


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value or value in seen:
            continue
        result.append(value)
        seen.add(value)
    return result


def build_retrieval_plan(analysis: QueryAnalysis) -> RetrievalPlan:
    law_hints = _dedupe([*analysis.law_mentions, *analysis.law_numbers])[:8]
    exact_refs = [
        {
            "law": ref.law,
            "article_no": ref.article_no,
            "paragraph_no": ref.paragraph_no,
        }
        for ref in analysis.article_refs
    ]
    article_ranges = [
        {
            "law": article_range.law,
            "start_article_no": article_range.start_article_no,
            "end_article_no": article_range.end_article_no,
        }
        for article_range in analysis.article_ranges
    ]

    evidence_budget = {
        "exact_reference_hits": 6,
        "high_lexical_overlap_hits": 6,
        "dense_semantic_hits": 8,
        "metadata_filtered_hits": 6,
        "related_article_hits": 4,
    }

    steps: list[RetrievalStep] = []
    if exact_refs or article_ranges:
        steps.append(
            RetrievalStep(
                name="exact_source_article_lookup",
                reason="explicit law/article reference present",
                budget=evidence_budget["exact_reference_hits"],
            )
        )
    steps.extend(
        [
            RetrievalStep(
                name="lexical_sparse_retrieval",
                reason="term overlap over source titles, article headings, and chunk text",
                budget=evidence_budget["high_lexical_overlap_hits"],
            ),
            RetrievalStep(
                name="dense_vector_retrieval",
                reason="semantic candidate recall",
                budget=evidence_budget["dense_semantic_hits"],
            ),
            RetrievalStep(
                name="metadata_filtered_retrieval",
                reason="law/source-family/effective-state filters from deterministic analysis",
                budget=evidence_budget["metadata_filtered_hits"],
            ),
            RetrievalStep(
                name="related_article_expansion",
                reason="nearby or cross-referenced article evidence after primary hits",
                budget=evidence_budget["related_article_hits"],
            ),
            RetrievalStep(
                name="deterministic_rrf_merge",
                reason="merge exact, lexical, dense, metadata, and related candidates before evidence selection",
                budget=sum(evidence_budget.values()),
            ),
        ]
    )

    return RetrievalPlan(
        law_hints=law_hints,
        source_family_hints=analysis.source_families[:6],
        term_hints=analysis.term_hints[:8],
        exact_article_refs=exact_refs,
        article_ranges=article_ranges,
        temporal_intent=analysis.temporal_intent,
        date_filters=analysis.date_filters,
        domain_signals=analysis.domain_signals,
        out_of_scope=analysis.out_of_scope,
        insufficient_query=analysis.insufficient_query,
        evidence_budget=evidence_budget,
        steps=steps,
    )


def build_plan_focus_query(plan: RetrievalPlan | dict[str, Any] | None) -> str:
    if plan is None:
        return ""
    payload = plan.to_router_plan() if isinstance(plan, RetrievalPlan) else plan
    parts: list[str] = []
    for value in payload.get("term_hints") or []:
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
    for value in payload.get("source_family_hints") or []:
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
    return " ".join(_dedupe(parts))
