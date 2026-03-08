"""Verification Engine Testleri — Backlog #6.

Test kapsamı:
    1. CitationSpan ve bracket citation çıkarımı
    2. ClaimSpan ve cümle ayrıştırma
    3. GroundingResult — grounded / ungrounded durumları
    4. VerificationResult — verdict, hallucination_risk, to_dict()
    5. Strict mode vs relaxed mode farklılıkları
    6. Citation matching (exact, normalize, prefix)
    7. Boş answer / empty context edge case'leri
    8. Gerçekçi hukuk metni senaryoları (TBK, TMK)
    9. HashingEmbedder testleri
    10. RemoteEmbeddingService (mock) testleri
    11. get_verification_engine singleton
    12. MilvusRetriever health_check (mock client)
    13. EmbeddingService Protocol compliance
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from rag.embedding import HashingEmbedder, RemoteEmbeddingService, get_default_embedder
from rag.retriever import MilvusRetriever, MetadataFilter, MockRetriever
from rag.verification_engine import (
    CitationSpan,
    ClaimSpan,
    GroundingResult,
    VerificationEngine,
    VerificationResult,
    get_verification_engine,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_CHUNKS: list[dict[str, Any]] = [
    {
        "text": (
            "Haksız fiille başkasına zarar veren, bu zararı gidermek zorundadır. "
            "Haksız fiil sorumluluğunun doğması için kusur, zarar ve illiyet bağı şarttır."
        ),
        "citation": "TBK m.49",
        "source": "TBK",
        "metadata": {"law_short_name": "TBK", "madde_no": "49"},
    },
    {
        "text": (
            "Kişilik hakkı hukuka aykırı olarak saldırıya uğrayan kimse, hâkimden, "
            "saldırıda bulunanlara karşı korunmasını isteyebilir."
        ),
        "citation": "TMK m.24",
        "source": "TMK",
        "metadata": {"law_short_name": "TMK", "madde_no": "24"},
    },
    {
        "text": (
            "Sözleşmeden doğan borç ilişkisinde borçlu, alacaklıya karşı borcunu "
            "gereği gibi ifa etmekle yükümlüdür."
        ),
        "citation": "TBK m.97",
        "source": "TBK",
        "metadata": {"law_short_name": "TBK", "madde_no": "97"},
    },
]


@pytest.fixture
def engine() -> VerificationEngine:
    return VerificationEngine(strict_mode=True)


@pytest.fixture
def relaxed_engine() -> VerificationEngine:
    return VerificationEngine(strict_mode=False, warn_threshold=0.5, fail_threshold=0.8)


# ===========================================================================
# 1. Citation Extraction
# ===========================================================================


def test_extract_bracket_citations_basic(engine: VerificationEngine) -> None:
    answer = "TBK m.49 uyarınca zarar verme yasağı uygulanır [Kaynak: TBK m.49]."
    spans = engine._extract_bracket_citations(answer)
    assert len(spans) == 1
    assert spans[0].citation == "TBK m.49"
    assert spans[0].raw == "[Kaynak: TBK m.49]"


def test_extract_bracket_citations_multiple(engine: VerificationEngine) -> None:
    answer = (
        "Haksız fiil [Kaynak: TBK m.49] gereği tazminat borcu doğar. "
        "Kişilik hakkı koruması da uygulanır [Kaynak: TMK m.24]."
    )
    spans = engine._extract_bracket_citations(answer)
    assert len(spans) == 2
    citations = {s.citation for s in spans}
    assert "TBK m.49" in citations
    assert "TMK m.24" in citations


def test_extract_bracket_citations_none(engine: VerificationEngine) -> None:
    answer = "Haksız fiil sorumluluğu genel hukuk ilkesine dayanır."
    spans = engine._extract_bracket_citations(answer)
    assert spans == []


def test_extract_bracket_citations_fıkra(engine: VerificationEngine) -> None:
    answer = "Bu kural uygulanır [Kaynak: TBK m.49/f.1]."
    spans = engine._extract_bracket_citations(answer)
    assert len(spans) == 1
    assert spans[0].citation == "TBK m.49/f.1"


# ===========================================================================
# 2. Citation Matching
# ===========================================================================


def test_citation_in_allowed_exact(engine: VerificationEngine) -> None:
    allowed = {"TBK m.49", "TMK m.24"}
    assert engine._citation_in_allowed("TBK m.49", allowed) is True
    assert engine._citation_in_allowed("TCK m.243", allowed) is False


def test_citation_in_allowed_normalize_fikra(engine: VerificationEngine) -> None:
    allowed = {"TBK m.49"}
    # "TBK m.49/f.1" normalize edilince "TBK m.49" → allowed'da var
    assert engine._citation_in_allowed("TBK m.49/f.1", allowed) is True


def test_citation_in_allowed_prefix_match(engine: VerificationEngine) -> None:
    allowed = {"TBK m.49"}
    # "TBK" prefix → allowed'da "TBK m.49" var → True
    assert engine._citation_in_allowed("TBK", allowed) is True


def test_citation_in_allowed_empty_allowed(engine: VerificationEngine) -> None:
    assert engine._citation_in_allowed("TBK m.49", set()) is False


def test_build_allowed_citation_set_from_chunks(engine: VerificationEngine) -> None:
    allowed = engine._build_allowed_citation_set(SAMPLE_CHUNKS)
    assert "TBK m.49" in allowed
    assert "TMK m.24" in allowed
    assert "TBK m.97" in allowed
    assert "TBK" in allowed  # source field


# ===========================================================================
# 3. Claim Extraction
# ===========================================================================


def test_extract_claims_basic(engine: VerificationEngine) -> None:
    answer = (
        "TBK m.49 uyarınca haksız fiil sorumluluğu doğar. "
        "Bu durumda tazminat borcu oluşur."
    )
    claims = engine._extract_claims(answer)
    assert len(claims) >= 1


def test_extract_claims_short_sentences_filtered(engine: VerificationEngine) -> None:
    answer = "Evet. TBK m.49 uyarınca haksız fiil sorumluluğu için kusur, zarar ve illiyet bağı şarttır."
    claims = engine._extract_claims(answer)
    # "Evet." kısa olduğu için filtrelenmiş olmalı
    assert all(len(c.text) >= 12 for c in claims)


def test_extract_claims_inline_refs(engine: VerificationEngine) -> None:
    answer = "TBK m.49 uyarınca haksız fiil sorumluluğu, kusur ve zarar gerektirir."
    claims = engine._extract_claims(answer)
    assert len(claims) >= 1
    # En az bir claim'de inline ref bulunmalı
    has_inline = any("TBK m.49" in c.inline_refs for c in claims)
    assert has_inline


def test_extract_claims_boilerplate_filtered(engine: VerificationEngine) -> None:
    answer = (
        "Haksız fiil sorumluluğu TBK m.49 kapsamındadır.\n"
        "Bu bilgi genel hukuki bilgi amaçlıdır; hukuki tavsiye niteliği taşımaz."
    )
    claims = engine._extract_claims(answer)
    # Boilerplate satırı filtre edilmeli
    texts = [c.text for c in claims]
    assert not any("hukuki tavsiye" in t.lower() for t in texts)


# ===========================================================================
# 4. Grounding
# ===========================================================================


def test_ground_claim_grounded(engine: VerificationEngine) -> None:
    claim = ClaimSpan(
        text="Haksız fiille zarar veren kimse bu zararı gidermek zorundadır.",
        bracket_citations=["TBK m.49"],
        inline_refs=["TBK m.49"],
        sentence_idx=0,
    )
    allowed = {"TBK m.49", "TBK"}
    result = engine._ground_claim(claim, SAMPLE_CHUNKS, allowed)

    assert isinstance(result, GroundingResult)
    assert result.is_grounded is True
    assert result.best_match_score > 0
    assert result.best_match_chunk_id is not None


def test_ground_claim_ungrounded_no_context(engine: VerificationEngine) -> None:
    claim = ClaimSpan(
        text="Faiz oranı yüzde on beşi geçemez.",
        bracket_citations=["TCK m.999"],
        sentence_idx=0,
    )
    allowed = {"TBK m.49"}
    result = engine._ground_claim(claim, SAMPLE_CHUNKS, allowed)

    # TCK m.999 SAMPLE_CHUNKS'ta yok → unverified citation → ungrounded
    assert result.is_grounded is False
    assert "TCK m.999" in result.unverified_citations


def test_ground_claim_empty_chunks(engine: VerificationEngine) -> None:
    claim = ClaimSpan(text="Haksız fiil sorumluluğu doğar.", sentence_idx=0)
    result = engine._ground_claim(claim, [], set())
    assert result.is_grounded is False
    assert result.best_match_score == 0.0


def test_ground_claim_citation_bonus_applied(engine: VerificationEngine) -> None:
    """Citation eşleşmesi bonus puanı vermelidir."""
    claim_with_cite = ClaimSpan(
        text="Zarar veren tazminat ödemek zorundadır.",
        bracket_citations=["TBK m.49"],
        sentence_idx=0,
    )
    claim_without_cite = ClaimSpan(
        text="Zarar veren tazminat ödemek zorundadır.",
        bracket_citations=[],
        sentence_idx=1,
    )
    allowed = {"TBK m.49", "TBK"}

    result_with = engine._ground_claim(claim_with_cite, SAMPLE_CHUNKS, allowed)
    result_without = engine._ground_claim(claim_without_cite, SAMPLE_CHUNKS, allowed)

    # Citation bonus → cite'li versiyonun skoru daha yüksek olmalı
    assert result_with.best_match_score >= result_without.best_match_score


# ===========================================================================
# 5. Full Verify — Pass / Warn / Fail
# ===========================================================================


def test_verify_pass_grounded_answer(engine: VerificationEngine) -> None:
    """Context'ten gelen bilgiler kullanan yanıt → pass."""
    answer = (
        "Haksız fiille başkasına zarar veren kimse bu zararı gidermek zorundadır "
        "[Kaynak: TBK m.49]. Kusur, zarar ve illiyet bağı unsurları şarttır."
    )
    result = engine.verify(answer=answer, context_chunks=SAMPLE_CHUNKS)

    assert isinstance(result, VerificationResult)
    assert result.verdict in ("pass", "warn")  # Yeterli grounding
    assert result.hallucination_risk < 0.6
    assert result.claim_count > 0


def test_verify_fail_wrong_citation_strict(engine: VerificationEngine) -> None:
    """Context'te olmayan atıf → strict mode → fail."""
    answer = (
        "Bu durum TCK m.99 uyarınca suç teşkil eder [Kaynak: TCK m.99]."
    )
    result = engine.verify(answer=answer, context_chunks=SAMPLE_CHUNKS)

    # TCK m.99 context'te yok → strict mode → fail
    assert result.verdict == "fail"
    assert "TCK m.99" in result.citation_mismatches


def test_verify_warn_relaxed_mode(relaxed_engine: VerificationEngine) -> None:
    """Relaxed mode'da citation mismatch strict_mode=False olduğu için
    'fail' yalnızca ungrounded_ratio > fail_threshold ise tetiklenir.
    Tek cümle + sıfır overlap → ungrounded_ratio=1.0 > 0.8 → fail, ancak
    citation mismatch tek başına bloklamaz.
    """
    answer = "Bu durum TCK m.99 uyarınca değerlendirilebilir [Kaynak: TCK m.99]."
    result = relaxed_engine.verify(answer=answer, context_chunks=SAMPLE_CHUNKS)

    # Strict mode olmadığı için citation_mismatches tek başına fail tetiklemez,
    # ama ungrounded_ratio yüksekse engine yine fail diyebilir.
    # Önemli kontrol: verdict strict moddan daha tolerant olmalı.
    assert result.verdict in ("warn", "fail")  # strict moda göre daha tolerant
    # citation_mismatches → verdict_reason'da strict_mode flag yok
    if result.verdict == "fail":
        assert "Context dışı atıf" not in result.verdict_reason  # strict mode fail reason'ı değil


def test_verify_empty_answer(engine: VerificationEngine) -> None:
    result = engine.verify(answer="", context_chunks=SAMPLE_CHUNKS)
    assert result.verdict == "pass"
    assert result.claim_count == 0
    assert result.hallucination_risk == 0.0


def test_verify_empty_chunks(engine: VerificationEngine) -> None:
    answer = "TBK m.49 uyarınca tazminat borcu doğar [Kaynak: TBK m.49]."
    result = engine.verify(answer=answer, context_chunks=[])
    # Context yok → citation allowed seti boş → citation mismatch → fail
    assert result.verdict == "fail"
    assert result.citation_mismatches


def test_verify_no_citations_high_overlap(relaxed_engine: VerificationEngine) -> None:
    """Citation yoksa ama içerik örtüşüyorsa grounded sayılmalı."""
    # SAMPLE_CHUNKS[0] ile aynı kelimeler
    answer = (
        "Haksız fiille başkasına zarar veren kimse bu zararı gidermek zorundadır. "
        "Kusur, zarar ve illiyet bağı unsurları şarttır."
    )
    result = relaxed_engine.verify(answer=answer, context_chunks=SAMPLE_CHUNKS)
    assert result.verdict in ("pass", "warn")
    assert result.grounded_count > 0


def test_verify_refusal_text(engine: VerificationEngine) -> None:
    """Refusal yanıtı: citation yok, ama tek cümle overlap < threshold olabilir.

    Engine refusal cümlesini claim olarak görür; context'e overlap yoksa
    ungrounded sayılabilir. Temel beklenti: citation mismatch yok.
    """
    answer = "Bu soruyu mevcut belgeler kapsamında yanıtlayamıyorum."
    result = engine.verify(answer=answer, context_chunks=SAMPLE_CHUNKS)
    # Citation yok → citation_mismatches boş olmalı
    assert result.citation_mismatches == []
    # Refusal için context içeriğiyle overlap beklemek doğru değil;
    # verdict ne olursa olsun citation problemi yoktur.
    assert result.has_citation_mismatches is False


# ===========================================================================
# 6. VerificationResult API
# ===========================================================================


def test_verification_result_to_dict(engine: VerificationEngine) -> None:
    answer = "Haksız fiil sorumluluğu TBK m.49 kapsamındadır [Kaynak: TBK m.49]."
    result = engine.verify(answer=answer, context_chunks=SAMPLE_CHUNKS)
    d = result.to_dict()

    assert "verdict" in d
    assert "hallucination_risk" in d
    assert "claim_count" in d
    assert "grounded_count" in d
    assert "ungrounded_count" in d
    assert "citation_mismatches" in d
    assert "groundings" in d
    assert isinstance(d["groundings"], list)


def test_verification_result_overall_grounded_pass(engine: VerificationEngine) -> None:
    result = engine._empty_result("test")
    assert result.overall_grounded is True


def test_verification_result_grounding_ratio_no_claims(engine: VerificationEngine) -> None:
    result = engine._empty_result("test")
    assert result.grounding_ratio == 1.0


def test_verification_result_grounding_ratio_partial() -> None:
    from rag.verification_engine import ClaimSpan, GroundingResult

    dummy_claim = ClaimSpan(text="test", sentence_idx=0)
    dummy_grounding_pass = GroundingResult(
        claim=dummy_claim,
        is_grounded=True,
        best_match_chunk_id="TBK m.49",
        best_match_score=0.5,
        grounding_evidence="test evidence",
    )
    dummy_grounding_fail = GroundingResult(
        claim=dummy_claim,
        is_grounded=False,
        best_match_chunk_id=None,
        best_match_score=0.0,
        grounding_evidence=None,
    )
    result = VerificationResult(
        claim_count=2,
        grounded_count=1,
        ungrounded_count=1,
        groundings=[dummy_grounding_pass, dummy_grounding_fail],
        citation_mismatches=[],
        hallucination_risk=0.4,
        verdict="warn",
        verdict_reason="test",
    )
    assert result.grounding_ratio == 0.5
    assert result.has_citation_mismatches is False
    assert result.overall_grounded is False


# ===========================================================================
# 7. Tokenize & Jaccard
# ===========================================================================


def test_tokenize_basic(engine: VerificationEngine) -> None:
    tokens = engine._tokenize("Haksız fiil tazminat davası")
    assert "haksız" in tokens
    assert "fiil" in tokens
    assert "tazminat" in tokens


def test_tokenize_stop_words_removed(engine: VerificationEngine) -> None:
    tokens = engine._tokenize("ve bir bu ile için")
    # Tüm stop words → boş set
    assert len(tokens) == 0


def test_jaccard_identical(engine: VerificationEngine) -> None:
    a = {"haksız", "fiil", "zarar"}
    assert engine._jaccard_overlap(a, a) == 1.0


def test_jaccard_disjoint(engine: VerificationEngine) -> None:
    a = {"haksız", "fiil"}
    b = {"sözleşme", "borç"}
    assert engine._jaccard_overlap(a, b) == 0.0


def test_jaccard_partial(engine: VerificationEngine) -> None:
    a = {"haksız", "fiil", "zarar"}
    b = {"haksız", "fiil", "tazminat"}
    # intersection = 2, union = 4 → 0.5
    assert engine._jaccard_overlap(a, b) == 0.5


def test_jaccard_empty_sets(engine: VerificationEngine) -> None:
    assert engine._jaccard_overlap(set(), {"a"}) == 0.0
    assert engine._jaccard_overlap({"a"}, set()) == 0.0


# ===========================================================================
# 8. Singleton Factory
# ===========================================================================


def test_get_verification_engine_singleton() -> None:
    e1 = get_verification_engine(strict_mode=True)
    e2 = get_verification_engine(strict_mode=True)
    assert e1 is e2


def test_get_verification_engine_new_on_mode_change() -> None:
    # strict → relaxed yeni instance
    e_strict = get_verification_engine(strict_mode=True)
    e_relaxed = get_verification_engine(strict_mode=False)
    assert e_strict is not e_relaxed
    # Geri strict
    get_verification_engine(strict_mode=True)


# ===========================================================================
# 9. HashingEmbedder
# ===========================================================================


def test_hashing_embedder_dimension() -> None:
    emb = HashingEmbedder(dimension=16)
    assert emb.dimension == 16
    vec = emb.embed_query("test metin")
    assert len(vec) == 16


def test_hashing_embedder_normalized() -> None:
    import math

    emb = HashingEmbedder(dimension=768)
    vec = emb.embed_query("haksız fiil tazminat")
    norm = math.sqrt(sum(x * x for x in vec))
    assert abs(norm - 1.0) < 1e-6


def test_hashing_embedder_deterministic() -> None:
    emb = HashingEmbedder(dimension=64)
    v1 = emb.embed_query("TBK m.49 haksız fiil")
    v2 = emb.embed_query("TBK m.49 haksız fiil")
    assert v1 == v2


def test_hashing_embedder_different_texts() -> None:
    emb = HashingEmbedder(dimension=64)
    v1 = emb.embed_query("haksız fiil")
    v2 = emb.embed_query("sözleşme borcu")
    # Farklı metinler farklı vektör üretmeli
    assert v1 != v2


def test_hashing_embedder_embed_texts_batch() -> None:
    emb = HashingEmbedder(dimension=32)
    texts = ["metin bir", "metin iki", "metin üç"]
    vecs = emb.embed_texts(texts)
    assert len(vecs) == 3
    assert all(len(v) == 32 for v in vecs)


def test_hashing_embedder_empty_text() -> None:
    emb = HashingEmbedder(dimension=16)
    vec = emb.embed_query("")
    assert len(vec) == 16


def test_hashing_embedder_invalid_dimension() -> None:
    with pytest.raises(ValueError, match="pozitif"):
        HashingEmbedder(dimension=0)


# ===========================================================================
# 10. RemoteEmbeddingService (Mock)
# ===========================================================================


def test_remote_embedding_from_env() -> None:
    import os

    with patch.dict(
        os.environ,
        {
            "DGX_BASE_URL": "http://test-dgx:30000/v1",
            "EMBEDDING_MODEL": "test-model",
            "DGX_API_KEY": "test-key",
            "EMBEDDING_DIM": "512",
        },
    ):
        service = RemoteEmbeddingService.from_env()
    assert service._base_url == "http://test-dgx:30000/v1"
    assert service._model == "test-model"
    assert service._dimension == 512


def test_remote_embedding_endpoint() -> None:
    service = RemoteEmbeddingService(
        base_url="http://localhost:30000/v1",
        model="test-model",
    )
    assert service.endpoint == "http://localhost:30000/v1/embeddings"


def test_remote_embedding_empty_texts() -> None:
    service = RemoteEmbeddingService(base_url="http://localhost/v1")
    result = service.embed_texts([])
    assert result == []


def test_remote_embedding_health_check_error() -> None:
    service = RemoteEmbeddingService(base_url="http://nonexistent:99999/v1")
    health = service.health_check()
    assert health["status"] == "error"
    assert "endpoint" in health


# ===========================================================================
# 11. get_default_embedder Factory
# ===========================================================================


def test_get_default_embedder_hashing() -> None:
    import os

    with patch.dict(os.environ, {"EMBEDDING_BACKEND": "hashing"}):
        emb = get_default_embedder()
    assert isinstance(emb, HashingEmbedder)


def test_get_default_embedder_remote() -> None:
    import os

    with patch.dict(
        os.environ,
        {"EMBEDDING_BACKEND": "remote", "DGX_BASE_URL": "http://test/v1"},
    ):
        emb = get_default_embedder()
    assert isinstance(emb, RemoteEmbeddingService)


def test_get_default_embedder_default_is_hashing() -> None:
    import os

    env_copy = {k: v for k, v in os.environ.items() if k != "EMBEDDING_BACKEND"}
    with patch.dict(os.environ, env_copy, clear=True):
        emb = get_default_embedder()
    assert isinstance(emb, HashingEmbedder)


# ===========================================================================
# 12. MilvusRetriever health_check (mock client)
# ===========================================================================


def test_milvus_retriever_health_check_ok() -> None:
    mock_client = MagicMock()
    mock_client.has_collection.return_value = True
    mock_client.get_collection_stats.return_value = {"row_count": 656}

    emb = HashingEmbedder(dimension=16)
    retriever = MilvusRetriever(
        client=mock_client, embedder=emb, collection="hukuk_chunks"
    )
    health = retriever.health_check()

    assert health["status"] == "ok"
    assert health["num_entities"] == 656
    assert health["collection"] == "hukuk_chunks"


def test_milvus_retriever_health_check_no_collection() -> None:
    mock_client = MagicMock()
    mock_client.has_collection.return_value = False

    emb = HashingEmbedder(dimension=16)
    retriever = MilvusRetriever(
        client=mock_client, embedder=emb, collection="missing_coll"
    )
    health = retriever.health_check()

    assert health["status"] == "error"
    assert "bulunamadı" in health["error"]


def test_milvus_retriever_health_check_exception() -> None:
    mock_client = MagicMock()
    mock_client.has_collection.side_effect = ConnectionError("Milvus down")

    emb = HashingEmbedder(dimension=16)
    retriever = MilvusRetriever(
        client=mock_client, embedder=emb, collection="hukuk_chunks"
    )
    health = retriever.health_check()

    assert health["status"] == "error"
    assert "Milvus down" in health["error"]


# ===========================================================================
# 13. MilvusRetriever.retrieve (mock client)
# ===========================================================================


def test_milvus_retriever_retrieve_mock() -> None:
    mock_client = MagicMock()
    # Milvus search response formatı: [[{id, distance, entity: {text, metadata}}]]
    mock_client.search.return_value = [
        [
            {
                "id": "TBK_m49_f1",
                "distance": 0.95,
                "entity": {
                    "text": "Haksız fiille zarar veren tazminat ödemek zorundadır.",
                    "metadata": {"law_short_name": "TBK", "madde_no": "49"},
                },
            }
        ]
    ]

    emb = HashingEmbedder(dimension=16)
    retriever = MilvusRetriever(
        client=mock_client, embedder=emb, collection="hukuk_chunks"
    )
    results, stats = retriever.retrieve(query="haksız fiil tazminat")

    assert len(results) == 1
    assert results[0].chunk_id == "TBK_m49_f1"
    assert results[0].score == pytest.approx(0.95)
    assert stats.hit_count == 1
    assert stats.collection == "hukuk_chunks"


def test_milvus_retriever_retrieve_with_filter_mock() -> None:
    mock_client = MagicMock()
    mock_client.search.return_value = [[]]

    emb = HashingEmbedder(dimension=16)
    retriever = MilvusRetriever(
        client=mock_client, embedder=emb, collection="hukuk_chunks"
    )
    filt = MetadataFilter(law_short_name="TBK", mulga=False)
    results, stats = retriever.retrieve(query="sözleşme", metadata_filter=filt)

    # Filter expr search kwargs'a geçmeli
    call_kwargs = mock_client.search.call_args[1]
    assert "filter" in call_kwargs
    assert "TBK" in call_kwargs["filter"]

    assert results == []
    assert stats.filter_expr is not None


# ===========================================================================
# 14. Integration Smoke: verify → full pipeline
# ===========================================================================


def test_full_pipeline_smoke() -> None:
    """Gerçekçi TBK haksız fiil senaryosu — end-to-end smoke."""
    engine = VerificationEngine(strict_mode=True)

    answer = (
        "TBK m.49 uyarınca, haksız fiille başkasına zarar veren kimse "
        "bu zararı gidermek zorundadır [Kaynak: TBK m.49]. "
        "Sorumluluğun doğması için kusur, zarar ve illiyet bağı şarttır."
    )

    result = engine.verify(answer=answer, context_chunks=SAMPLE_CHUNKS)

    # Temel kontroller
    assert isinstance(result, VerificationResult)
    assert result.verdict in ("pass", "warn")
    assert result.claim_count > 0
    assert result.hallucination_risk < 0.7

    # to_dict() çalışmalı
    d = result.to_dict()
    assert d["verdict"] == result.verdict
    assert d["claim_count"] == result.claim_count
    assert isinstance(d["groundings"], list)


def test_full_pipeline_smoke_hallucination() -> None:
    """Tamamen uydurulmuş madde numarası → fail verdict."""
    engine = VerificationEngine(strict_mode=True)

    answer = (
        "Bu durumda TBK m.9999 açıkça yasaklamaktadır [Kaynak: TBK m.9999]. "
        "Ayrıca TMK m.8888 de uygulanır [Kaynak: TMK m.8888]."
    )

    result = engine.verify(answer=answer, context_chunks=SAMPLE_CHUNKS)

    assert result.verdict == "fail"
    assert len(result.citation_mismatches) >= 2
    assert result.hallucination_risk > 0.3
