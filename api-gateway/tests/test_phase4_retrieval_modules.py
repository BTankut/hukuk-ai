from __future__ import annotations

from rag.evidence_selector import group_candidates_by_article, select_evidence_chunks
from rag.orchestrator import RetrievedChunk
from rag.query_analyzer import QueryAnalyzer
from rag.retrieval_plan import build_retrieval_plan
from rag.retriever import MetadataFilter, MockRetriever
from routers import chat


def test_query_analyzer_extracts_law_article_family_temporal_and_domain() -> None:
    analysis = QueryAnalyzer().analyze(
        "Güncel Türk Borçlar Kanunu TBK m.49/1 haksız fiil tazminatında ne der?"
    )

    assert "TBK" in analysis.law_mentions
    assert [(ref.law, ref.article_no, ref.paragraph_no) for ref in analysis.article_refs] == [("TBK", "49", "1")]
    assert "kanun" in analysis.source_families
    assert analysis.temporal_intent == "current"
    assert "ozel_hukuk" in analysis.domain_signals
    assert analysis.out_of_scope is False
    assert analysis.insufficient_query is False


def test_query_analyzer_detects_numeric_law_range_and_historical_intent() -> None:
    analysis = QueryAnalyzer().analyze(
        "15.03.2020 tarihinde 3194 sayılı Kanun m.32-33 hangi usule tabiydi?"
    )

    assert analysis.law_numbers == ["3194"]
    assert [(item.law, item.start_article_no, item.end_article_no) for item in analysis.article_ranges] == [
        ("3194", "32", "33")
    ]
    assert analysis.date_filters == ["15.03.2020"]
    assert analysis.temporal_intent == "historical"
    assert "usul" in analysis.domain_signals


def test_retrieval_plan_uses_required_order_and_evidence_budgets() -> None:
    analysis = QueryAnalyzer().analyze("TBK m.49 ve TBK m.50 haksız fiil için nasıl uygulanır?")
    plan = build_retrieval_plan(analysis).to_router_plan()

    assert plan["law_hints"] == ["TBK"]
    assert [step["name"] for step in plan["steps"]][:4] == [
        "exact_source_article_lookup",
        "lexical_sparse_retrieval",
        "dense_vector_retrieval",
        "metadata_filtered_retrieval",
    ]
    assert plan["steps"][-1]["name"] == "deterministic_rrf_merge"
    assert set(plan["evidence_budget"]) == {
        "exact_reference_hits",
        "high_lexical_overlap_hits",
        "dense_semantic_hits",
        "metadata_filtered_hits",
        "related_article_hits",
    }


def test_evidence_selector_groups_by_source_article_and_prefers_active_exact_hits() -> None:
    analysis = QueryAnalyzer().analyze("TBK m.49 haksız fiil için güncel cevap nedir?")
    chunks = [
        RetrievedChunk(
            text="Eski haksız fiil metni",
            citation="TBK m.49",
            source="TBK",
            score=0.99,
            metadata={"law_short_name": "TBK", "madde_no": "49", "effective_state": "repealed"},
        ),
        RetrievedChunk(
            text="Kusurlu ve hukuka aykırı fiil haksız fiil sorumluluğunu doğurur.",
            citation="TBK m.49",
            source="TBK",
            score=0.80,
            metadata={"law_short_name": "TBK", "madde_no": "49", "effective_state": "active"},
        ),
        RetrievedChunk(
            text="İspat yükü",
            citation="TBK m.50",
            source="TBK",
            score=0.90,
            metadata={"law_short_name": "TBK", "madde_no": "50", "effective_state": "active"},
        ),
    ]

    selected = select_evidence_chunks(query=analysis.raw_query, chunks=chunks, analysis=analysis, limit=2)

    assert len(group_candidates_by_article(chunks)) == 2
    assert selected[0].text.startswith("Kusurlu")
    assert selected[0].metadata["effective_state"] == "active"


def test_source_family_filter_supports_article_first_metadata() -> None:
    retriever = MockRetriever(
        fixture_chunks=[
            {
                "id": "a",
                "text": "kanun",
                "embedding": [1.0, 0.0],
                "metadata": {"source_family": "kanun", "belge_turu": "kanun"},
            },
            {
                "id": "b",
                "text": "tebliğ",
                "embedding": [1.0, 0.0],
                "metadata": {"source_family": "teblig", "belge_turu": "teblig"},
            },
        ]
    )

    results, _stats = retriever.retrieve(
        query_vector=[1.0, 0.0],
        metadata_filter=MetadataFilter(source_family="teblig"),
    )

    assert [result.chunk_id for result in results] == ["b"]


def test_llm_retrieval_planner_and_source_selector_default_off(monkeypatch) -> None:
    monkeypatch.delenv("RETRIEVAL_PLANNER_ENABLED", raising=False)
    monkeypatch.delenv("SOURCE_CLUSTER_SELECTOR_ENABLED", raising=False)

    assert chat._retrieval_planner_enabled() is False
    assert chat._source_cluster_selector_enabled() is False
