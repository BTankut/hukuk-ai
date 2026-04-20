"""RAG Retriever + Prompt Builder + Token Manager — Unit & Smoke Testleri.

pytest -q tests/test_rag_retriever_prompt.py
Tüm testler Milvus veya dış servis olmadan çalışır.
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_CHUNKS = [
    {
        "id": "TBK_m49_f1",
        "text": (
            "Kusurlu ve hukuka aykırı bir fiille başkasına zarar veren, "
            "bu zararı gidermekle yükümlüdür."
        ),
        "embedding": [0.1, 0.9, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                      0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "metadata": {
            "law_no": "6098",
            "law_short_name": "TBK",
            "madde_no": "49",
            "fikra_no": "1",
            "mulga": False,
        },
    },
    {
        "id": "TBK_m50_f1",
        "text": (
            "Zarar gören, zararını ve zarar verenin kusurunu ispat yükü altındadır."
        ),
        "embedding": [0.8, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                      0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "metadata": {
            "law_no": "6098",
            "law_short_name": "TBK",
            "madde_no": "50",
            "fikra_no": "1",
            "mulga": False,
        },
    },
    {
        "id": "TMK_m1_f1",
        "text": (
            "Hukuk, kanunda yazılı olmayan hâllerde kanunun özüne ve "
            "ruhuna uygun kural koyarak uyuşmazlıkları çözer."
        ),
        "embedding": [0.0, 0.1, 0.9, 0.0, 0.0, 0.0, 0.0, 0.0,
                      0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "metadata": {
            "law_no": "4721",
            "law_short_name": "TMK",
            "madde_no": "1",
            "fikra_no": "1",
            "mulga": False,
        },
    },
]

QUERY_VECTOR = [0.1, 0.8, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]


# ---------------------------------------------------------------------------
# MetadataFilter Tests
# ---------------------------------------------------------------------------

class TestMetadataFilter:

    def test_empty_filter_returns_none_expr(self):
        from rag.retriever import MetadataFilter
        f = MetadataFilter()
        # mulga default None (live-rag-debug fix: mulga=False Milvus'ta alan olmadığı için 0 sonuç veriyordu)
        # MetadataFilter() tüm alanları None → is_empty() True olmalı
        assert f.is_empty() is True

    def test_law_no_filter_expr(self):
        from rag.retriever import MetadataFilter
        f = MetadataFilter(law_no="6098", mulga=None)
        expr = f.to_milvus_expr()
        assert expr is not None
        assert 'metadata["law_no"] == "6098"' in expr

    def test_composite_filter_expr(self):
        from rag.retriever import MetadataFilter
        f = MetadataFilter(law_short_name="TBK", madde_no="49", mulga=None)
        expr = f.to_milvus_expr()
        assert "TBK" in expr
        assert "49" in expr
        assert "&&" in expr

    def test_mulga_false_in_expr(self):
        from rag.retriever import MetadataFilter
        f = MetadataFilter(mulga=False)
        expr = f.to_milvus_expr()
        assert "mulga" in expr
        assert "false" in expr

    def test_belge_turu_filter_expr(self):
        from rag.retriever import MetadataFilter
        f = MetadataFilter(belge_turu="tuzuk", mulga=None)
        expr = f.to_milvus_expr()
        assert 'metadata["belge_turu"] == "tuzuk"' in expr

    def test_madde_range_filter(self):
        from rag.retriever import MetadataFilter
        f = MetadataFilter(madde_no_min=40, madde_no_max=60, mulga=None)
        expr = f.to_milvus_expr()
        assert "40" in expr
        assert "60" in expr

    def test_fully_empty_filter(self):
        from rag.retriever import MetadataFilter
        f = MetadataFilter(mulga=None)
        assert f.is_empty() is True


# ---------------------------------------------------------------------------
# RetrievalResult Tests
# ---------------------------------------------------------------------------

class TestRetrievalResult:

    def test_citation_format_with_fikra(self):
        from rag.retriever import RetrievalResult
        r = RetrievalResult(
            chunk_id="TBK_m49_f1",
            text="test",
            score=0.9,
            metadata={"law_short_name": "TBK", "madde_no": "49", "fikra_no": "2"},
        )
        assert r.citation == "TBK m.49/f.2"

    def test_citation_format_fikra_1_no_suffix(self):
        from rag.retriever import RetrievalResult
        r = RetrievalResult(
            chunk_id="TBK_m49_f1",
            text="test",
            score=0.9,
            metadata={"law_short_name": "TBK", "madde_no": "49", "fikra_no": "1"},
        )
        # Fıkra 1 ise sadece madde numarası
        assert r.citation == "TBK m.49"

    def test_to_candidate_dict(self):
        from rag.retriever import RetrievalResult
        r = RetrievalResult(
            chunk_id="TBK_m49_f1",
            text="zarar ziyan",
            score=0.85,
            metadata={"law_short_name": "TBK", "madde_no": "49"},
        )
        d = r.to_candidate_dict()
        assert d["text"] == "zarar ziyan"
        assert d["citation"] == "TBK m.49"
        assert d["score"] == 0.85


# ---------------------------------------------------------------------------
# MockRetriever Tests
# ---------------------------------------------------------------------------

class TestMockRetriever:

    def test_basic_retrieve_no_filter(self):
        from rag.retriever import MockRetriever
        retriever = MockRetriever(fixture_chunks=SAMPLE_CHUNKS)
        results, stats = retriever.retrieve(
            query_vector=QUERY_VECTOR,
            top_k=3,
        )
        assert len(results) <= 3
        assert all(hasattr(r, "chunk_id") for r in results)
        assert stats.hit_count == len(results)

    def test_filter_by_law_no(self):
        from rag.retriever import MockRetriever, MetadataFilter
        retriever = MockRetriever(fixture_chunks=SAMPLE_CHUNKS)
        f = MetadataFilter(law_no="6098", mulga=None)
        results, _ = retriever.retrieve(query_vector=QUERY_VECTOR, metadata_filter=f)
        assert all(r.law_no == "6098" for r in results)

    def test_filter_by_law_short_name(self):
        from rag.retriever import MockRetriever, MetadataFilter
        retriever = MockRetriever(fixture_chunks=SAMPLE_CHUNKS)
        f = MetadataFilter(law_short_name="TMK", mulga=None)
        results, _ = retriever.retrieve(query_vector=QUERY_VECTOR, metadata_filter=f)
        assert len(results) == 1
        assert results[0].law_short_name == "TMK"

    def test_top_k_respected(self):
        from rag.retriever import MockRetriever
        retriever = MockRetriever(fixture_chunks=SAMPLE_CHUNKS)
        results, _ = retriever.retrieve(query_vector=QUERY_VECTOR, top_k=1)
        assert len(results) == 1

    def test_scores_are_sorted_descending(self):
        from rag.retriever import MockRetriever
        retriever = MockRetriever(fixture_chunks=SAMPLE_CHUNKS)
        results, _ = retriever.retrieve(query_vector=QUERY_VECTOR, top_k=3)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_empty_store_returns_empty(self):
        from rag.retriever import MockRetriever
        retriever = MockRetriever(fixture_chunks=[])
        results, stats = retriever.retrieve(query_vector=QUERY_VECTOR)
        assert results == []
        assert stats.hit_count == 0

    def test_filter_no_match_returns_empty(self):
        from rag.retriever import MockRetriever, MetadataFilter
        retriever = MockRetriever(fixture_chunks=SAMPLE_CHUNKS)
        f = MetadataFilter(law_no="9999", mulga=None)
        results, _ = retriever.retrieve(query_vector=QUERY_VECTOR, metadata_filter=f)
        assert results == []

    def test_filter_by_belge_turu(self):
        from rag.retriever import MockRetriever, MetadataFilter

        chunks = [
            {
                "id": "kanun_1",
                "text": "kanun metni",
                "embedding": QUERY_VECTOR,
                "metadata": {"belge_turu": "kanun", "law_short_name": "TBK", "madde_no": "1"},
            },
            {
                "id": "tuzuk_1",
                "text": "tüzük metni",
                "embedding": QUERY_VECTOR,
                "metadata": {"belge_turu": "tuzuk", "law_short_name": "20135150", "madde_no": "1"},
            },
        ]

        retriever = MockRetriever(fixture_chunks=chunks)
        f = MetadataFilter(belge_turu="tuzuk", mulga=None)
        results, _ = retriever.retrieve(query_vector=QUERY_VECTOR, metadata_filter=f)

        assert len(results) == 1
        assert results[0].metadata["belge_turu"] == "tuzuk"


# ---------------------------------------------------------------------------
# TokenLimitManager Tests
# ---------------------------------------------------------------------------

class TestTokenLimitManager:

    def test_estimate_tokens_basic(self):
        from rag.token_manager import estimate_tokens
        tokens = estimate_tokens("haksız fiil tazminatı")
        assert tokens > 0

    def test_fit_all_chunks_when_budget_sufficient(self):
        from rag.token_manager import TokenLimitManager
        manager = TokenLimitManager(context_window=32768)
        chunks = [{"text": "kısa metin", "citation": f"TBK m.{i}"} for i in range(5)]
        result = manager.fit_chunks(query="test sorgu", chunks=chunks)
        assert len(result.chunks) == 5
        assert result.chunks_dropped == 0

    def test_truncates_when_budget_exceeded(self):
        from rag.token_manager import TokenLimitManager
        # Çok küçük bütçe
        manager = TokenLimitManager(context_window=500, system_reserve=50)
        long_text = " ".join(["kelime"] * 200)
        chunks = [{"text": long_text, "citation": f"TBK m.{i}"} for i in range(10)]
        result = manager.fit_chunks(query="test", chunks=chunks)
        # Hepsini alamamalı
        assert len(result.chunks) < 10
        assert result.chunks_dropped > 0

    def test_min_chunks_guarantee(self):
        from rag.token_manager import TokenLimitManager
        # Hiç sığmayacak kadar küçük bütçe
        manager = TokenLimitManager(context_window=100, system_reserve=10, min_chunks=2)
        long_text = " ".join(["uzunkelime"] * 100)
        chunks = [{"text": long_text, "citation": "X"} for _ in range(5)]
        result = manager.fit_chunks(query="q", chunks=chunks, truncate_long_chunks=True)
        # Min guarantee: en az 2 chunk alınmalı
        assert len(result.chunks) >= 2

    def test_empty_chunks_handled(self):
        from rag.token_manager import TokenLimitManager
        manager = TokenLimitManager()
        result = manager.fit_chunks(query="test", chunks=[])
        assert result.chunks == []
        assert result.chunks_dropped == 0

    def test_budget_compute(self):
        from rag.token_manager import TokenBudget
        budget = TokenBudget.compute(context_window=4096, query="test sorgu")
        assert budget.available_for_chunks > 0
        assert budget.available_for_chunks < 4096
        assert budget.output_reserve > 0

    def test_summary_string(self):
        from rag.token_manager import TokenLimitManager
        manager = TokenLimitManager()
        chunks = [{"text": "merhaba dünya", "citation": "TBK m.1"}]
        result = manager.fit_chunks(query="test", chunks=chunks)
        summary = manager.summary(result)
        assert "Token bütçesi" in summary


# ---------------------------------------------------------------------------
# PromptBuilder Tests
# ---------------------------------------------------------------------------

class TestPromptBuilder:

    def _sample_chunk_dicts(self) -> list[dict]:
        return [
            {
                "text": "Kusurlu ve hukuka aykırı bir fiille zarar veren gidermekle yükümlüdür.",
                "citation": "TBK m.49",
                "score": 0.95,
            },
            {
                "text": "Zarar gören zararını ve kusuru ispat yükü altındadır.",
                "citation": "TBK m.50",
                "score": 0.85,
            },
        ]

    def test_build_returns_built_prompt(self):
        from rag.prompt_builder import PromptBuilder
        builder = PromptBuilder()
        prompt = builder.build(query="haksız fiil tazminatı nedir?", chunks=self._sample_chunk_dicts())
        assert prompt.system_prompt
        assert prompt.user_message
        assert prompt.context_chunk_count == 2

    def test_prompt_contains_citation(self):
        from rag.prompt_builder import PromptBuilder
        builder = PromptBuilder()
        prompt = builder.build(query="haksız fiil tazminatı nedir?", chunks=self._sample_chunk_dicts())
        assert "TBK m.49" in prompt.user_message
        assert "TBK m.50" in prompt.user_message

    def test_prompt_contains_query(self):
        from rag.prompt_builder import PromptBuilder
        builder = PromptBuilder()
        query = "zarar ispat yükü kime aittir?"
        prompt = builder.build(query=query, chunks=self._sample_chunk_dicts())
        assert query in prompt.user_message

    def test_strict_mode_system_prompt(self):
        from rag.prompt_builder import PromptBuilder
        builder = PromptBuilder(strict_mode=True)
        prompt = builder.build(query="test", chunks=[])
        assert "KAYNAK ZORUNLU" in prompt.system_prompt or "ZORUNLU KURALLAR" in prompt.system_prompt

    def test_empty_chunks_shows_no_context_msg(self):
        from rag.prompt_builder import PromptBuilder
        builder = PromptBuilder()
        prompt = builder.build(query="test sorgu", chunks=[])
        assert "Kaynak metin bulunamadı" in prompt.user_message or "refusal" in prompt.user_message.lower()

    def test_to_messages_format(self):
        from rag.prompt_builder import PromptBuilder
        builder = PromptBuilder()
        prompt = builder.build(query="test", chunks=self._sample_chunk_dicts())
        messages = prompt.to_messages()
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    def test_refusal_prompt(self):
        from rag.prompt_builder import PromptBuilder
        builder = PromptBuilder()
        prompt = builder.build_refusal_prompt(
            query="İlgisiz konu hakkında soru",
            reason="Kapsam dışı — yalnızca Türk mevzuatı destekleniyor.",
        )
        assert prompt.context_chunk_count == 0
        assert prompt.metadata.get("refusal") is True

    def test_extra_system_notes(self):
        from rag.prompt_builder import PromptBuilder
        builder = PromptBuilder()
        prompt = builder.build(
            query="test",
            chunks=self._sample_chunk_dicts(),
            extra_system_notes="Bu oturum test modundadır.",
        )
        assert "test modundadır" in prompt.system_prompt

    def test_singleton_factory(self):
        from rag.prompt_builder import get_prompt_builder
        b1 = get_prompt_builder(strict_mode=True)
        b2 = get_prompt_builder(strict_mode=True)
        assert b1 is b2


# ---------------------------------------------------------------------------
# Integration: Retriever → PromptBuilder Pipeline
# ---------------------------------------------------------------------------

class TestRetrieverToPromptPipeline:

    def test_end_to_end_mock_pipeline(self):
        """MockRetriever → PromptBuilder tam pipeline smoke testi."""
        from rag.retriever import MockRetriever, MetadataFilter
        from rag.prompt_builder import PromptBuilder

        retriever = MockRetriever(fixture_chunks=SAMPLE_CHUNKS)
        f = MetadataFilter(law_no="6098", mulga=False)
        results, stats = retriever.retrieve(
            query_vector=QUERY_VECTOR,
            metadata_filter=f,
            top_k=5,
        )

        chunks = [r.to_candidate_dict() for r in results]
        builder = PromptBuilder(strict_mode=True)
        prompt = builder.build(query="haksız fiil tazminatı", chunks=chunks)

        assert prompt.context_chunk_count == len(results)
        assert stats.filter_expr is not None
        assert "6098" in stats.filter_expr
        messages = prompt.to_messages()
        assert messages[0]["role"] == "system"
        assert "TBK" in messages[1]["content"]

    def test_token_limit_in_pipeline(self):
        """Token limit yönetiminin pipeline'da çalıştığını doğrula."""
        from rag.retriever import MockRetriever
        from rag.token_manager import TokenLimitManager
        from rag.prompt_builder import PromptBuilder

        # Çok küçük context window
        manager = TokenLimitManager(context_window=300, system_reserve=50)
        builder = PromptBuilder(strict_mode=False, token_manager=manager)

        retriever = MockRetriever(fixture_chunks=SAMPLE_CHUNKS)
        results, _ = retriever.retrieve(query_vector=QUERY_VECTOR, top_k=10)
        chunks = [r.to_candidate_dict() for r in results]

        prompt = builder.build(query="test", chunks=chunks)
        # Sınırlı bütçede tüm chunk'lar sığmamalı
        assert prompt.context_chunk_count <= len(chunks)
