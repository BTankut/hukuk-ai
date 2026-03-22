"""Test Suite — Chat Router (Backlog #7).

Test kapsamı:
    - ConversationStore: get/add/clear, kapasite limitleri
    - _build_multiturn_query: geçmiş enjeksiyonu
    - _stream_sse_response: SSE format doğrulaması
    - POST /v1/chat/completions: non-streaming yanıt
    - POST /v1/chat/completions: streaming (SSE) yanıt
    - POST /v1/chat/completions: multi-turn konuşma
    - POST /v1/chat/completions: session_id davranışı
    - POST /v1/chat/completions: hata durumları
    - GET /v1/sessions/{id}: geçmiş okuma
    - DELETE /v1/sessions/{id}: oturum silme
    - GET /v1/sessions: aktif oturum sayısı
    - GET /v1/health: health endpoint
    - POST /v1/chat (legacy): backward compat
"""

from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from routers.chat import (
    ConversationStore,
    ChatCompletionRequest,
    ConversationMessage,
    _extract_explicit_article_refs,
    _extract_law_mentions,
    _should_use_cross_law_retrieval,
    _build_precise_tbk_answer,
    _detect_scope_refusal_reason,
    _build_multiturn_query,
    _stream_sse_response,
    get_conversation_store,
    router as chat_router,
)
from rag.orchestrator import OrchestratorResponse


# ---------------------------------------------------------------------------
# Fixtures & Helpers
# ---------------------------------------------------------------------------

def _make_orch_response(
    answer: str = "Test yanıtı.",
    citations: list[str] | None = None,
    blocked: bool = False,
    reasons: list[str] | None = None,
    verification: dict | None = None,
) -> OrchestratorResponse:
    return OrchestratorResponse(
        answer=answer,
        citations=citations or ["TBK m.49"],
        blocked=blocked,
        guardrails_reasons=reasons or [],
        verification=verification,
    )


def _make_app(mock_orch: Any = None, mock_retriever: Any = None) -> FastAPI:
    """Test için minimal FastAPI app oluştur."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(chat_router)

    if mock_orch is not None:
        app.state.orchestrator = mock_orch
    if mock_retriever is not None:
        app.state.retriever = mock_retriever

    return app


@pytest.fixture
def mock_orchestrator():
    """Mock RAGOrchestrator."""
    orch = MagicMock()
    orch.use_verification = False
    orch.answer = AsyncMock(return_value=_make_orch_response())
    return orch


@pytest.fixture
def test_app(mock_orchestrator):
    """Test uygulaması (retriever yok)."""
    return _make_app(mock_orch=mock_orchestrator)


@pytest.fixture
def client(test_app):
    """Senkron TestClient."""
    # Yeni store ile her test izole çalışsın
    new_store = ConversationStore()
    test_app.dependency_overrides[get_conversation_store] = lambda: new_store
    with TestClient(test_app) as c:
        yield c
    test_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# ConversationStore Testleri
# ---------------------------------------------------------------------------


class TestConversationStore:

    def test_empty_store_returns_empty_list(self):
        store = ConversationStore()
        assert store.get_history("nonexistent") == []

    def test_add_turn_stores_messages(self):
        store = ConversationStore()
        store.add_turn("s1", "merhaba", "merhaba size de")
        history = store.get_history("s1")
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "merhaba"}
        assert history[1] == {"role": "assistant", "content": "merhaba size de"}

    def test_multiple_turns_accumulate(self):
        store = ConversationStore()
        store.add_turn("s1", "soru1", "cevap1")
        store.add_turn("s1", "soru2", "cevap2")
        history = store.get_history("s1")
        assert len(history) == 4

    def test_clear_existing_session(self):
        store = ConversationStore()
        store.add_turn("s1", "soru", "cevap")
        deleted = store.clear_session("s1")
        assert deleted is True
        assert store.get_history("s1") == []

    def test_clear_nonexistent_session(self):
        store = ConversationStore()
        deleted = store.clear_session("yok")
        assert deleted is False

    def test_session_count(self):
        store = ConversationStore()
        assert store.session_count() == 0
        store.add_turn("s1", "a", "b")
        store.add_turn("s2", "c", "d")
        assert store.session_count() == 2

    def test_max_session_capacity(self):
        store = ConversationStore()
        store.MAX_SESSIONS = 3  # Override test için
        for i in range(4):
            store.add_turn(f"sess-{i}", "q", "a")
        # 4. eklendiğinde 1. silinmeli → 3 oturum kalmalı
        assert store.session_count() == 3
        # En eski oturum sess-0 silinmiş olmalı
        assert store.get_history("sess-0") == []
        # sess-3 mevcut olmalı
        assert len(store.get_history("sess-3")) == 2

    def test_max_history_per_session_truncates(self):
        store = ConversationStore()
        store.MAX_MESSAGES_PER_SESSION = 4  # 2 tur maksimum
        for i in range(5):
            store.add_turn("s1", f"soru{i}", f"cevap{i}")
        history = store.get_history("s1")
        # En fazla 4 mesaj olmalı
        assert len(history) <= 4

    def test_get_history_returns_copy(self):
        """Dönüş değeri referans değil kopya olmalı."""
        store = ConversationStore()
        store.add_turn("s1", "q", "a")
        h1 = store.get_history("s1")
        h1.append({"role": "user", "content": "eklendi"})
        h2 = store.get_history("s1")
        assert len(h2) == 2  # Değişmemiş olmalı


# ---------------------------------------------------------------------------
# _build_multiturn_query Testleri
# ---------------------------------------------------------------------------


class TestBuildMultiturnQuery:

    def test_no_history_returns_query_unchanged(self):
        result = _build_multiturn_query(
            last_user_message="TBK nedir?",
            conversation_history=[],
        )
        assert result == "TBK nedir?"

    def test_with_history_includes_context(self):
        history = [
            {"role": "user", "content": "TBK nedir?"},
            {"role": "assistant", "content": "Türk Borçlar Kanunu'dur."},
        ]
        result = _build_multiturn_query(
            last_user_message="Kaçıncı madde?",
            conversation_history=history,
        )
        assert "Önceki Konuşma" in result
        assert "TBK nedir?" in result
        assert "Kaçıncı madde?" in result
        assert "[Mevcut Soru]" in result

    def test_long_history_truncated(self):
        # Çok uzun geçmiş
        long_content = "a" * 5000
        history = [{"role": "user", "content": long_content}]
        result = _build_multiturn_query(
            last_user_message="yeni soru",
            conversation_history=history,
            max_history_chars=100,
        )
        # Kısaltılmış olmalı
        assert "..." in result
        # Mevcut soru dahil olmalı
        assert "yeni soru" in result

    def test_assistant_role_labeled(self):
        history = [
            {"role": "assistant", "content": "Ben asistanım."},
        ]
        result = _build_multiturn_query(
            last_user_message="tamam",
            conversation_history=history,
        )
        assert "Asistan" in result


class TestScopeRefusalDetection:

    def test_ttk_query_detected_as_out_of_scope(self):
        reason = _detect_scope_refusal_reason(
            "Türk Ticaret Kanunu'na göre anonim şirket kuruluş asgari sermayesi nedir?"
        )
        assert reason == "Türk Ticaret Kanunu (TTK)"

    def test_tck_query_detected_as_out_of_scope(self):
        reason = _detect_scope_refusal_reason(
            "TCK m.141 neyi düzenler?"
        )
        assert reason == "Türk Ceza Kanunu (TCK)"

    def test_cross_law_family_query_does_not_trigger_scope_refusal(self):
        reason = _detect_scope_refusal_reason(
            "Boşanma davası açıldıktan sonra eşlerden biri aile konutu kira sözleşmesini "
            "feshedebilir mi? Mahkeme tedbir kararının yokluğu bu durumu değiştirir mi?"
        )
        assert reason is None

    def test_ttk_false_positive_substring_is_not_triggered_by_gercekte(self):
        reason = _detect_scope_refusal_reason(
            "Babam taşınmazını bana sattı; ancak gerçekte bağışlamak istediğini düşünüyorum. "
            "Muris muvazaası nedeniyle dava açabilir miyim?"
        )
        assert reason is None


class TestLawSignalParsing:

    def test_extract_explicit_article_refs_expands_ranges(self):
        refs = _extract_explicit_article_refs(
            "TBK m.397-398 kapsamında rekabet yasağına aykırılık halinde ne olur?"
        )
        assert ("TBK", "397") in refs
        assert ("TBK", "398") in refs

    def test_extract_explicit_article_refs_expands_lists(self):
        refs = _extract_explicit_article_refs(
            "TBK m.181, m.182 ve m.183 birlikte nasıl uygulanır?"
        )
        assert refs[:3] == [("TBK", "181"), ("TBK", "182"), ("TBK", "183")]

    def test_extract_law_mentions_supports_names_and_codes(self):
        laws = _extract_law_mentions(
            "Türk Borçlar Kanunu ile TMK birlikte nasıl uygulanır?"
        )
        assert laws == ["TBK", "TMK"]

    def test_extract_law_mentions_infers_tbk_tmk_for_cross_law_concepts(self):
        laws = _extract_law_mentions(
            "Evli bir kişinin kefalet sözleşmesi yapmasında eş rızası şartı aile birliğinin "
            "korunması ilkesiyle nasıl ilişkilidir?"
        )
        assert laws == ["TBK", "TMK"]

    def test_cross_law_retrieval_enabled_for_joint_scope_queries(self):
        laws = ["TBK", "TMK"]
        assert _should_use_cross_law_retrieval(
            "Paylı mülkiyette satış hükümleri ile TMK nasıl birlikte uygulanır?",
            laws,
        ) is True

    def test_cross_law_retrieval_enabled_for_conceptual_joint_scope_queries(self):
        laws = ["TBK", "TMK"]
        assert _should_use_cross_law_retrieval(
            "Eşin rızası alınmadan yapılan her sözleşme TMK m.194 gereği otomatik olarak "
            "batıldır ifadesi hukuken doğru mudur?",
            laws,
        ) is True

    def test_kefalet_scope_does_not_force_family_home_invalidity_anchor(self):
        laws = ["TBK", "TMK"]
        assert _should_use_cross_law_retrieval(
            "Kefalet sözleşmesinde eşin rızası hangi durumlarda aranmaz?",
            laws,
        ) is False


class TestPreciseDeterministicAnswers:

    def test_joint_debt_release_answer_anchors_to_tbk_166(self):
        precise = _build_precise_tbk_answer(
            "Müteselsil borçlulukta borçlulardan birinin ifası diğerlerini kurtarır mı?"
        )
        assert precise is not None
        answer, citations = precise
        assert citations == ["TBK m.166"]
        assert "TBK m.166" in answer

    @pytest.mark.parametrize(
        ("question", "expected_citations", "expected_fragments"),
        [
            (
                "Kira sözleşmesinde kiracının kira bedelini ödeme yükümlülüğü TBK'nın hangi maddesinde düzenlenmektedir? Ödeme günü ve yeri nedir?",
                ["TBK m.299", "TBK m.314"],
                ["ayın son günü", "kiraya verene"],
            ),
            (
                "Kira bedelinin yıllık artışında TBK hangi sınırlamayı öngörmektedir?",
                ["TBK m.344"],
                ["TÜFE", "on iki aylık ortalamalara göre değişim oranını"],
            ),
            (
                "TBK'ya göre kefalet sözleşmesi hangi şekil şartlarına tabidir ve geçerlilik koşulları nelerdir?",
                ["TBK m.582", "TBK m.583", "TBK m.584"],
                ["yazılı", "kendi el yazısıyla"],
            ),
            (
                "TBK'ya göre taşınmaz satış sözleşmesi hangi şekle tabidir ve noter onayı gerekir mi?",
                ["TBK m.237", "TMK m.706"],
                ["resmî şekilde", "tapu sicilinde tescil"],
            ),
            (
                "Satış sözleşmesinde satıcının ayıptan doğan sorumluluğu (ayıba karşı tekeffül) için alıcının gözden geçirme ve bildirim külfeti hangi sürelere tabidir?",
                ["TBK m.223"],
                ["gözden geçirmek", "hemen ve gecikmeksizin"],
            ),
            (
                "Kefalet sözleşmesinde eşin rızası hangi durumlarda aranmaz?",
                ["TBK m.584"],
                ["ticaret siciline kayıtlı", "esnaf ve sanatkârlar"],
            ),
            (
                "TBK'ya göre müteselsil kefaletin şartları nelerdir?",
                ["TBK m.586"],
                ["müteselsil kefil", "doğrudan kefile"],
            ),
            (
                "Alacaklının temerrüdü (alacaklı direnimi) hâlinde borçlu borcundan nasıl kurtulur?",
                ["TBK m.107", "TBK m.108"],
                ["tevdi", "hâkim izniyle"],
            ),
            (
                "Borçlunun sorumlu olmadığı sonraki imkânsızlık (ifa imkânsızlığı) durumunda borç sona erer mi?",
                ["TBK m.136"],
                ["sona erer", "sebepsiz zenginleşme"],
            ),
            (
                "Geri alma hakkı saklı tutulan bağışlamada bağışlayan hangi hallerde bağışlamayı geri alabilir?",
                ["TBK m.295"],
                ["ağır bir suç", "yüklemeyi yerine getirmemişse"],
            ),
            (
                "Borcun üstlenilmesi (nakli) sözleşmesinde alacaklının rızası gerekir mi?",
                ["TBK m.195", "TBK m.196"],
                ["alacaklının kabulü", "açık veya örtülü"],
            ),
            (
                "Garantörlük (garanti sözleşmesi) ile kefalet sözleşmesi arasındaki temel fark nedir?",
                ["TBK m.128", "TBK m.582"],
                ["bağımsız", "fer'î"],
            ),
        ],
    )
    def test_precise_answers_cover_high_risk_eval_questions(
        self,
        question: str,
        expected_citations: list[str],
        expected_fragments: list[str],
    ):
        precise = _build_precise_tbk_answer(question)
        assert precise is not None
        answer, citations = precise
        assert citations == expected_citations
        for citation in expected_citations:
            assert citation in answer
        for fragment in expected_fragments:
            assert fragment in answer


# ---------------------------------------------------------------------------
# _stream_sse_response Testleri
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sse_stream_format():
    """SSE chunk'larının OpenAI formatında olduğunu doğrula."""
    chunks = []
    async for chunk in _stream_sse_response(
        answer="Test yanıtı kelimeler içeriyor.",
        session_id="s1",
        model="hukuk-ai-poc",
        citations=["TBK m.49"],
        blocked=False,
        guardrails_reasons=[],
        verification=None,
        delay_between_chunks=0,
    ):
        chunks.append(chunk)

    # En az 3 chunk: role, content(lar), finish, metadata, DONE
    assert len(chunks) >= 3

    # Son chunk [DONE] olmalı
    assert chunks[-1] == "data: [DONE]\n\n"

    # İkinci son chunk metadata olmalı
    meta_chunk = chunks[-2]
    assert meta_chunk.startswith("data: ")
    meta_data = json.loads(meta_chunk[6:])
    assert meta_data["object"] == "chat.completion.metadata"
    assert "citations" in meta_data
    assert meta_data["session_id"] == "s1"
    assert meta_data["blocked"] is False

    # İlk data chunk role olmalı
    first_data = json.loads(chunks[0][6:])
    assert first_data["object"] == "chat.completion.chunk"
    assert first_data["choices"][0]["delta"] == {"role": "assistant"}


@pytest.mark.asyncio
async def test_sse_stream_content_complete():
    """Tüm kelimeler SSE chunk'larında bulunmalı."""
    answer = "Bu bir test cümlesidir ve birden fazla kelime içerir."
    collected_words: list[str] = []

    async for chunk in _stream_sse_response(
        answer=answer,
        session_id="s1",
        model="test",
        citations=[],
        blocked=False,
        guardrails_reasons=[],
        verification=None,
        words_per_chunk=2,
        delay_between_chunks=0,
    ):
        if chunk.startswith("data: [DONE]") or chunk.startswith("data: "):
            if "[DONE]" in chunk:
                continue
            try:
                data = json.loads(chunk[6:])
                if data.get("object") == "chat.completion.chunk":
                    content = data["choices"][0]["delta"].get("content", "")
                    collected_words.extend(content.split())
            except (json.JSONDecodeError, KeyError):
                pass

    reconstructed = " ".join(collected_words)
    # Orijinal kelimelerin tamamı reconstructed içinde olmalı
    for word in answer.split():
        assert word in reconstructed, f"Kelime bulunamadı: {word}"


@pytest.mark.asyncio
async def test_sse_stream_metadata_carries_optional_trace():
    chunks = []
    async for chunk in _stream_sse_response(
        answer="Test yanıtı",
        session_id="s1",
        model="test",
        citations=["TBK m.49"],
        blocked=False,
        guardrails_reasons=[],
        verification={"verdict": "pass"},
        trace={"query_signals": {"user_query": "TBK m.49 nedir?"}},
        delay_between_chunks=0,
    ):
        chunks.append(chunk)

    meta_data = json.loads(chunks[-2][6:])
    assert meta_data["object"] == "chat.completion.metadata"
    assert meta_data["trace"]["query_signals"]["user_query"] == "TBK m.49 nedir?"


# ---------------------------------------------------------------------------
# POST /v1/chat/completions — Non-streaming Testleri
# ---------------------------------------------------------------------------


class TestChatCompletionsNonStreaming:

    def test_basic_request(self, client, mock_orchestrator):
        mock_orchestrator.answer = AsyncMock(
            return_value=_make_orch_response("TBK m.49 haksız fiili düzenler.")
        )
        resp = client.post(
            "/v1/chat/completions",
            json={
                "model": "hukuk-ai-poc",
                "messages": [{"role": "user", "content": "Haksız fiil nedir?"}],
                "stream": False,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["object"] == "chat.completion"
        assert data["choices"][0]["message"]["role"] == "assistant"
        assert "TBK m.49" in data["choices"][0]["message"]["content"]
        assert "session_id" in data
        assert data["session_id"].startswith("sess-")

    def test_response_includes_citations(self, client, mock_orchestrator):
        mock_orchestrator.answer = AsyncMock(
            return_value=_make_orch_response(citations=["TBK m.49", "TBK m.50"])
        )
        resp = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "soru"}]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "TBK m.49" in data["citations"]
        assert "TBK m.50" in data["citations"]

    def test_session_id_preserved(self, client, mock_orchestrator):
        mock_orchestrator.answer = AsyncMock(return_value=_make_orch_response())
        resp = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "test"}],
                "session_id": "ozel-session-123",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["session_id"] == "ozel-session-123"

    def test_blocked_response(self, client, mock_orchestrator):
        mock_orchestrator.answer = AsyncMock(
            return_value=_make_orch_response(
                blocked=True,
                reasons=["pii_detected"],
            )
        )
        resp = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "soru"}]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["blocked"] is True
        assert "pii_detected" in data["guardrails_reasons"]

    def test_usage_fields_present(self, client, mock_orchestrator):
        mock_orchestrator.answer = AsyncMock(return_value=_make_orch_response())
        resp = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "test soru"}]},
        )
        data = resp.json()
        usage = data["usage"]
        assert "prompt_tokens" in usage
        assert "completion_tokens" in usage
        assert "total_tokens" in usage
        assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]

    def test_400_on_empty_messages(self, client):
        resp = client.post(
            "/v1/chat/completions",
            json={"messages": []},
        )
        assert resp.status_code == 400

    def test_400_on_no_user_message(self, client):
        resp = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "assistant", "content": "Ben asistanım"}]},
        )
        assert resp.status_code == 400

    def test_400_on_empty_user_content(self, client):
        resp = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "   "}]},
        )
        assert resp.status_code == 400

    def test_503_when_no_orchestrator(self):
        """Orchestrator app.state'te yoksa 503 döndürmeli."""
        app = FastAPI()
        app.include_router(chat_router)
        # app.state.orchestrator set edilmemiş
        with TestClient(app) as c:
            resp = c.post(
                "/v1/chat/completions",
                json={"messages": [{"role": "user", "content": "soru"}]},
            )
        assert resp.status_code == 503

    def test_verification_field_in_response(self, client, mock_orchestrator):
        verification_data = {
            "verdict": "pass",
            "hallucination_risk": 0.0,
            "claim_count": 2,
        }
        mock_orchestrator.answer = AsyncMock(
            return_value=_make_orch_response(verification=verification_data)
        )
        resp = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "soru"}]},
        )
        assert resp.status_code == 200
        assert resp.json()["verification"] == verification_data


# ---------------------------------------------------------------------------
# POST /v1/chat/completions — Streaming Testleri
# ---------------------------------------------------------------------------


class TestChatCompletionsStreaming:

    def test_streaming_returns_event_stream(self, client, mock_orchestrator):
        mock_orchestrator.answer = AsyncMock(
            return_value=_make_orch_response("Bu bir stream testi yanıtıdır.")
        )
        resp = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "stream testi"}],
                "stream": True,
            },
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

    def test_streaming_contains_done_sentinel(self, client, mock_orchestrator):
        mock_orchestrator.answer = AsyncMock(
            return_value=_make_orch_response("yanıt")
        )
        resp = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "test"}],
                "stream": True,
            },
        )
        assert "[DONE]" in resp.text

    def test_streaming_contains_role_chunk(self, client, mock_orchestrator):
        mock_orchestrator.answer = AsyncMock(return_value=_make_orch_response("test"))
        resp = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "test"}],
                "stream": True,
            },
        )
        lines = [l for l in resp.text.split("\n") if l.startswith("data:") and "[DONE]" not in l]
        chunks = [json.loads(l[6:]) for l in lines]

        role_chunks = [
            c for c in chunks
            if c.get("object") == "chat.completion.chunk"
            and c.get("choices", [{}])[0].get("delta", {}).get("role") == "assistant"
        ]
        assert len(role_chunks) >= 1

    def test_streaming_metadata_chunk(self, client, mock_orchestrator):
        mock_orchestrator.answer = AsyncMock(
            return_value=_make_orch_response(citations=["TMK m.1"])
        )
        resp = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "evlilik kanunu"}],
                "stream": True,
            },
        )
        lines = [l for l in resp.text.split("\n") if l.startswith("data:") and "[DONE]" not in l]
        meta_chunks = []
        for l in lines:
            try:
                d = json.loads(l[6:])
                if d.get("object") == "chat.completion.metadata":
                    meta_chunks.append(d)
            except json.JSONDecodeError:
                pass

        assert len(meta_chunks) == 1
        assert "TMK m.1" in meta_chunks[0]["citations"]

    def test_streaming_session_header(self, client, mock_orchestrator):
        mock_orchestrator.answer = AsyncMock(return_value=_make_orch_response())
        resp = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "test"}],
                "stream": True,
                "session_id": "stream-sess-001",
            },
        )
        assert resp.headers.get("x-session-id") == "stream-sess-001"


# ---------------------------------------------------------------------------
# Multi-turn Konuşma Testleri
# ---------------------------------------------------------------------------


class TestMultiTurn:

    def test_multiturn_history_passed_to_orchestrator(self, client, mock_orchestrator):
        """Konuşma geçmişi orchestrator'a iletilmeli."""
        session_id = "multiturn-sess"

        # Birinci tur
        client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "TBK nedir?"}],
                "session_id": session_id,
            },
        )

        # İkinci tur — client geçmiş göndermiyor, session store kullanılmalı
        mock_orchestrator.answer = AsyncMock(return_value=_make_orch_response("İkinci cevap"))
        client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Kaçıncı madde?"}],
                "session_id": session_id,
            },
        )

        # İkinci turda orchestrator'a verilen query'de önceki konuşma olmalı
        call_args = mock_orchestrator.answer.call_args
        # keyword args ile çağrıldığında args tuple boş, kwargs'tan al
        query_arg = call_args.kwargs.get("query") or (call_args.args[0] if call_args.args else "")
        # Multiturn query formatı: "[Önceki..." içermeli
        assert "Önceki Konuşma" in query_arg or "TBK nedir?" in query_arg

    def test_client_provided_history_used(self, client, mock_orchestrator):
        """Client geçmişi request'te gönderirse, bu kullanılmalı."""
        mock_orchestrator.answer = AsyncMock(return_value=_make_orch_response())
        client.post(
            "/v1/chat/completions",
            json={
                "messages": [
                    {"role": "user", "content": "TBK nedir?"},
                    {"role": "assistant", "content": "Türk Borçlar Kanunu'dur."},
                    {"role": "user", "content": "Kaç maddeden oluşuyor?"},
                ],
                "session_id": "client-hist-sess",
            },
        )
        call_args = mock_orchestrator.answer.call_args
        query_arg = call_args.kwargs.get("query") or (call_args.args[0] if call_args.args else "")
        # Request'teki önceki mesajlar query'ye dahil edilmeli
        assert "TBK nedir?" in query_arg or "Önceki Konuşma" in query_arg

    def test_session_history_accumulates(self, client, mock_orchestrator):
        """Her turdan sonra session geçmişi büyümeli."""
        session_id = "accum-sess"
        mock_orchestrator.answer = AsyncMock(return_value=_make_orch_response("cevap"))

        for i in range(3):
            client.post(
                "/v1/chat/completions",
                json={
                    "messages": [{"role": "user", "content": f"soru{i}"}],
                    "session_id": session_id,
                },
            )

        resp = client.get(f"/v1/sessions/{session_id}")
        assert resp.status_code == 200
        data = resp.json()
        # 3 tur × 2 mesaj = 6
        assert data["message_count"] == 6


# ---------------------------------------------------------------------------
# Session Yönetim Endpoint Testleri
# ---------------------------------------------------------------------------


class TestSessionEndpoints:

    def test_get_session_empty(self, client):
        resp = client.get("/v1/sessions/yok")
        assert resp.status_code == 200
        assert resp.json()["message_count"] == 0
        assert resp.json()["messages"] == []

    def test_get_session_after_chat(self, client, mock_orchestrator):
        session_id = "sess-get-test"
        mock_orchestrator.answer = AsyncMock(return_value=_make_orch_response("cevap1"))
        client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "soru1"}],
                "session_id": session_id,
            },
        )
        resp = client.get(f"/v1/sessions/{session_id}")
        data = resp.json()
        assert data["session_id"] == session_id
        assert data["message_count"] == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["role"] == "assistant"

    def test_delete_existing_session(self, client, mock_orchestrator):
        session_id = "sess-delete"
        mock_orchestrator.answer = AsyncMock(return_value=_make_orch_response())
        client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "test"}],
                "session_id": session_id,
            },
        )
        resp = client.delete(f"/v1/sessions/{session_id}")
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

        # Silme sonrası geçmiş boş olmalı
        resp2 = client.get(f"/v1/sessions/{session_id}")
        assert resp2.json()["message_count"] == 0

    def test_delete_nonexistent_session(self, client):
        resp = client.delete("/v1/sessions/yok-session")
        assert resp.status_code == 200
        assert resp.json()["deleted"] is False

    def test_list_sessions(self, client, mock_orchestrator):
        mock_orchestrator.answer = AsyncMock(return_value=_make_orch_response())
        resp = client.get("/v1/sessions")
        initial_count = resp.json()["active_sessions"]

        client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "test"}],
                "session_id": "list-test-s1",
            },
        )
        client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "test"}],
                "session_id": "list-test-s2",
            },
        )

        resp2 = client.get("/v1/sessions")
        assert resp2.json()["active_sessions"] == initial_count + 2
        assert resp2.json()["max_sessions"] == ConversationStore.MAX_SESSIONS


# ---------------------------------------------------------------------------
# Law Filter & Retriever Entegrasyonu
# ---------------------------------------------------------------------------


class TestLawFilterAndRetrieval:

    def test_request_default_top_k_is_20(self):
        request = ChatCompletionRequest(
            messages=[ConversationMessage(role="user", content="soru")]
        )
        assert request.top_k == 20

    def test_law_filter_passed_to_retriever(self, mock_orchestrator):
        """law_filter MetadataFilter olarak retriever'a iletilmeli."""
        mock_retriever = MagicMock()
        mock_results = MagicMock()
        mock_results.text = "TBK m.49 metni"
        mock_results.citation = "TBK m.49"
        mock_results.law_short_name = "TBK"
        mock_results.score = 0.9
        mock_results.metadata = {}

        from rag.retriever import RetrievalStats
        mock_stats = RetrievalStats(
            collection="test",
            query_preview="haksız",
            top_k=5,
            filter_expr=None,
            hit_count=1,
            latency_ms=10.0,
        )
        mock_retriever.retrieve = MagicMock(return_value=([mock_results], mock_stats))
        mock_orchestrator.answer = AsyncMock(
            return_value=_make_orch_response("RAG cevabı")
        )

        app = _make_app(mock_orch=mock_orchestrator, mock_retriever=mock_retriever)
        new_store = ConversationStore()
        app.dependency_overrides[get_conversation_store] = lambda: new_store

        with TestClient(app) as c:
            resp = c.post(
                "/v1/chat/completions",
                json={
                    "messages": [{"role": "user", "content": "haksız fiil nedir?"}],
                    "law_filter": "TBK",
                },
            )

        assert resp.status_code == 200
        # Retriever çağrılmış mı?
        mock_retriever.retrieve.assert_called_once()
        call_kwargs = mock_retriever.retrieve.call_args.kwargs
        assert call_kwargs.get("metadata_filter") is not None
        assert call_kwargs["metadata_filter"].law_short_name == "TBK"

    def test_explicit_article_refs_are_force_included(self, mock_orchestrator):
        mock_retriever = MagicMock()

        from rag.retriever import RetrievalResult, RetrievalStats

        semantic_results = [
            RetrievalResult(
                chunk_id="semantic",
                text="Genel tasinmaz satis aciklamasi",
                score=0.9,
                metadata={"law_short_name": "TBK", "madde_no": "237", "fikra_no": "1"},
            )
        ]
        exact_tbk = [
            RetrievalResult(
                chunk_id="tbk-237",
                text="Tasinmaz satisi resmi sekle tabidir.",
                score=0.95,
                metadata={"law_short_name": "TBK", "madde_no": "237", "fikra_no": "1"},
            )
        ]
        exact_tmk = [
            RetrievalResult(
                chunk_id="tmk-706",
                text="Tasinmaz mulkiyetinin devri resmi sekle baglidir.",
                score=0.94,
                metadata={"law_short_name": "TMK", "madde_no": "706", "fikra_no": "1"},
            )
        ]

        semantic_stats = RetrievalStats(
            collection="test",
            query_preview="tasinmaz",
            top_k=20,
            filter_expr=None,
            hit_count=1,
            latency_ms=10.0,
        )
        exact_stats = RetrievalStats(
            collection="test",
            query_preview="tasinmaz",
            top_k=2,
            filter_expr='metadata["madde_no"] == "237"',
            hit_count=1,
            latency_ms=2.0,
        )

        mock_retriever.retrieve = MagicMock(
            side_effect=[
                (semantic_results, semantic_stats),
                (exact_tbk, exact_stats),
                (exact_tmk, exact_stats),
            ]
        )
        mock_orchestrator.answer = AsyncMock(return_value=_make_orch_response("RAG cevabı"))

        app = _make_app(mock_orch=mock_orchestrator, mock_retriever=mock_retriever)
        new_store = ConversationStore()
        app.dependency_overrides[get_conversation_store] = lambda: new_store

        with TestClient(app) as c:
            resp = c.post(
                "/v1/chat/completions",
                json={
                    "messages": [
                        {
                            "role": "user",
                            "content": "TBK m.237 ile TMK m.706 arasindaki iliski nedir?",
                        }
                    ],
                },
            )

        assert resp.status_code == 200
        assert mock_retriever.retrieve.call_count == 3

        first_call = mock_retriever.retrieve.call_args_list[0].kwargs
        second_call = mock_retriever.retrieve.call_args_list[1].kwargs
        third_call = mock_retriever.retrieve.call_args_list[2].kwargs

        assert first_call["top_k"] == 20
        assert second_call["metadata_filter"].law_short_name == "TBK"
        assert second_call["metadata_filter"].madde_no == "237"
        assert third_call["metadata_filter"].law_short_name == "TMK"
        assert third_call["metadata_filter"].madde_no == "706"

        orch_call = mock_orchestrator.answer.call_args
        citations = [chunk.citation for chunk in orch_call.kwargs["retrieved_chunks"]]
        assert "TBK m.237" in citations
        assert "TMK m.706" in citations

    def test_cross_law_questions_trigger_per_law_candidate_generation(self, mock_orchestrator):
        mock_retriever = MagicMock()

        from rag.retriever import RetrievalResult, RetrievalStats

        global_results = [
            RetrievalResult(
                chunk_id="global-tbk",
                text="Aile konutu kira metni",
                score=0.91,
                metadata={"law_short_name": "TBK", "madde_no": "349", "fikra_no": "1"},
            )
        ]
        tbk_results = [
            RetrievalResult(
                chunk_id="tbk-349",
                text="TBK aile konutu kira metni",
                score=0.93,
                metadata={"law_short_name": "TBK", "madde_no": "349", "fikra_no": "1"},
            )
        ]
        tmk_results = [
            RetrievalResult(
                chunk_id="tmk-194",
                text="TMK aile konutu metni",
                score=0.92,
                metadata={"law_short_name": "TMK", "madde_no": "194", "fikra_no": "1"},
            )
        ]
        stats = RetrievalStats(
            collection="test",
            query_preview="aile konutu",
            top_k=20,
            filter_expr=None,
            hit_count=1,
            latency_ms=10.0,
        )
        mock_retriever.retrieve = MagicMock(
            side_effect=[
                (global_results, stats),
                (tbk_results, stats),
                (tmk_results, stats),
            ]
        )
        mock_orchestrator.answer = AsyncMock(return_value=_make_orch_response("RAG cevabı"))

        app = _make_app(mock_orch=mock_orchestrator, mock_retriever=mock_retriever)
        new_store = ConversationStore()
        app.dependency_overrides[get_conversation_store] = lambda: new_store

        with TestClient(app) as c:
            resp = c.post(
                "/v1/chat/completions",
                json={
                    "messages": [
                        {
                            "role": "user",
                            "content": "Aile konutu olarak kullanılan kiralananda TBK ve TMK nasıl birlikte uygulanır?",
                        }
                    ],
                },
            )

        assert resp.status_code == 200
        assert mock_retriever.retrieve.call_count == 3

        first_call = mock_retriever.retrieve.call_args_list[0].kwargs
        second_call = mock_retriever.retrieve.call_args_list[1].kwargs
        third_call = mock_retriever.retrieve.call_args_list[2].kwargs
        assert first_call["metadata_filter"] is None
        assert second_call["metadata_filter"].law_short_name == "TBK"
        assert third_call["metadata_filter"].law_short_name == "TMK"

        orch_call = mock_orchestrator.answer.call_args
        citations = [chunk.citation for chunk in orch_call.kwargs["retrieved_chunks"]]
        assert "TBK m.349" in citations
        assert "TMK m.194" in citations

    def test_cross_law_concept_query_bypasses_scope_refusal_and_hits_retriever(self, mock_orchestrator):
        mock_retriever = MagicMock()

        from rag.retriever import RetrievalResult, RetrievalStats

        results = [
            RetrievalResult(
                chunk_id="tbk-349",
                text="Aile konutu kira feshi metni",
                score=0.91,
                metadata={"law_short_name": "TBK", "madde_no": "349", "fikra_no": "1"},
            )
        ]
        stats = RetrievalStats(
            collection="test",
            query_preview="aile konutu",
            top_k=20,
            filter_expr=None,
            hit_count=1,
            latency_ms=10.0,
        )
        mock_retriever.retrieve = MagicMock(return_value=(results, stats))
        mock_orchestrator.answer = AsyncMock(return_value=_make_orch_response("RAG cevabı"))

        app = _make_app(mock_orch=mock_orchestrator, mock_retriever=mock_retriever)
        new_store = ConversationStore()
        app.dependency_overrides[get_conversation_store] = lambda: new_store

        with TestClient(app) as c:
            resp = c.post(
                "/v1/chat/completions",
                json={
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                "Boşanma davası açıldıktan sonra eşlerden biri aile konutu kira "
                                "sözleşmesini feshedebilir mi?"
                            ),
                        }
                    ],
                    "include_trace": True,
                },
            )

        assert resp.status_code == 200
        assert mock_retriever.retrieve.call_count >= 1
        assert resp.json()["trace"]["generation_outcome"]["decision_lane"] == "rag"

    def test_trace_is_not_returned_by_default(self, mock_orchestrator):
        mock_retriever = MagicMock()

        from rag.retriever import RetrievalResult, RetrievalStats

        results = [
            RetrievalResult(
                chunk_id="tbk-49",
                text="Haksız fiil metni",
                score=0.9,
                metadata={"law_short_name": "TBK", "madde_no": "49", "fikra_no": "1"},
            )
        ]
        stats = RetrievalStats(
            collection="test",
            query_preview="haksız",
            top_k=20,
            filter_expr=None,
            hit_count=1,
            latency_ms=10.0,
        )
        mock_retriever.retrieve = MagicMock(return_value=(results, stats))
        mock_orchestrator.answer = AsyncMock(return_value=_make_orch_response("RAG cevabı"))

        app = _make_app(mock_orch=mock_orchestrator, mock_retriever=mock_retriever)
        new_store = ConversationStore()
        app.dependency_overrides[get_conversation_store] = lambda: new_store

        with TestClient(app) as c:
            resp = c.post(
                "/v1/chat/completions",
                json={"messages": [{"role": "user", "content": "TBK m.49 nedir?"}]},
            )

        assert resp.status_code == 200
        assert "trace" not in resp.json()

    def test_include_trace_returns_retrieval_context_trace(self, mock_orchestrator):
        mock_retriever = MagicMock()

        from rag.retriever import RetrievalResult, RetrievalStats

        results = [
            RetrievalResult(
                chunk_id="tbk-49",
                text="Haksız fiil metni",
                score=0.9,
                metadata={
                    "source_id": "tbk-49-f1",
                    "law_short_name": "TBK",
                    "madde_no": "49",
                    "fikra_no": "1",
                },
            )
        ]
        stats = RetrievalStats(
            collection="test",
            query_preview="haksız",
            top_k=20,
            filter_expr=None,
            hit_count=1,
            latency_ms=10.0,
        )
        mock_retriever.retrieve = MagicMock(return_value=(results, stats))
        mock_orchestrator.answer = AsyncMock(
            return_value=_make_orch_response(
                "TBK m.49 haksız fiili düzenler [Kaynak: TBK m.49]",
                citations=["TBK m.49"],
                verification={"verdict": "pass"},
            )
        )

        app = _make_app(mock_orch=mock_orchestrator, mock_retriever=mock_retriever)
        new_store = ConversationStore()
        app.dependency_overrides[get_conversation_store] = lambda: new_store

        with TestClient(app) as c:
            resp = c.post(
                "/v1/chat/completions",
                json={
                    "messages": [{"role": "user", "content": "TBK m.49 nedir?"}],
                    "include_trace": True,
                },
            )

        assert resp.status_code == 200
        trace = resp.json()["trace"]
        assert trace["query_signals"]["user_query"] == "TBK m.49 nedir?"
        assert trace["query_signals"]["mentioned_laws"] == ["TBK"]
        assert trace["query_signals"]["cross_law_mode"] is False
        assert trace["query_signals"]["explicit_article_refs"] == [{"law": "TBK", "madde": "49"}]
        assert trace["query_signals"]["forced_article_refs"] == []
        assert trace["retrieval"]["top_k_requested"] == 20
        assert trace["retrieval"]["top_k_effective"] == 20
        assert trace["retrieval"]["pre_rerank_chunks"][0]["source_id"] == "tbk-49-f1"
        assert trace["context_assembly"]["context_chunk_citations"] == ["TBK m.49"]
        assert "Haksız fiil metni" in trace["context_assembly"]["assembled_context"]
        assert trace["generation_outcome"]["verification"]["verdict"] == "pass"

    def test_concept_anchor_rules_force_include_exact_articles(self, mock_orchestrator):
        mock_retriever = MagicMock()

        from rag.retriever import RetrievalResult, RetrievalStats

        semantic_results = [
            RetrievalResult(
                chunk_id="semantic",
                text="Muvazaa genel açıklaması",
                score=0.9,
                metadata={"law_short_name": "TBK", "madde_no": "18", "fikra_no": "1"},
            )
        ]
        exact_tbk_19 = [
            RetrievalResult(
                chunk_id="tbk-19",
                text="Muvazaa hükümleri",
                score=0.95,
                metadata={"law_short_name": "TBK", "madde_no": "19", "fikra_no": "1"},
            )
        ]
        exact_tbk_285 = [
            RetrievalResult(
                chunk_id="tbk-285",
                text="Bağışlama hükümleri",
                score=0.94,
                metadata={"law_short_name": "TBK", "madde_no": "285", "fikra_no": "1"},
            )
        ]
        exact_tmk_561 = [
            RetrievalResult(
                chunk_id="tmk-561",
                text="Miras hükmü",
                score=0.93,
                metadata={"law_short_name": "TMK", "madde_no": "561", "fikra_no": "1"},
            )
        ]
        stats = RetrievalStats(
            collection="test",
            query_preview="muvazaa",
            top_k=20,
            filter_expr=None,
            hit_count=1,
            latency_ms=10.0,
        )
        exact_stats = RetrievalStats(
            collection="test",
            query_preview="muvazaa",
            top_k=2,
            filter_expr='metadata["madde_no"] == "19"',
            hit_count=1,
            latency_ms=2.0,
        )
        mock_retriever.retrieve = MagicMock(
            side_effect=[
                (semantic_results, stats),
                (exact_tbk_19, exact_stats),
                (exact_tbk_285, exact_stats),
                (exact_tmk_561, exact_stats),
            ]
        )
        mock_orchestrator.answer = AsyncMock(return_value=_make_orch_response("RAG cevabı"))

        app = _make_app(mock_orch=mock_orchestrator, mock_retriever=mock_retriever)
        new_store = ConversationStore()
        app.dependency_overrides[get_conversation_store] = lambda: new_store

        with TestClient(app) as c:
            resp = c.post(
                "/v1/chat/completions",
                json={
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                "Babam taşınmazını bana sattı; ancak gerçekte bağışlamak "
                                "istediğini düşünüyorum. Muris muvazaası nedeniyle dava "
                                "açabilir miyim?"
                            ),
                        }
                    ],
                    "include_trace": True,
                },
            )

        assert resp.status_code == 200
        assert mock_retriever.retrieve.call_count == 4
        calls = mock_retriever.retrieve.call_args_list
        assert calls[1].kwargs["metadata_filter"].law_short_name == "TBK"
        assert calls[1].kwargs["metadata_filter"].madde_no == "19"
        assert calls[2].kwargs["metadata_filter"].law_short_name == "TBK"
        assert calls[2].kwargs["metadata_filter"].madde_no == "285"
        assert calls[3].kwargs["metadata_filter"].law_short_name == "TMK"
        assert calls[3].kwargs["metadata_filter"].madde_no == "561"
        trace = resp.json()["trace"]
        assert trace["query_signals"]["forced_article_refs"] == [
            {"law": "TBK", "madde": "19"},
            {"law": "TBK", "madde": "285"},
            {"law": "TMK", "madde": "561"},
        ]
        assert trace["query_signals"]["applied_expansions"] == [
            "TBK m.19 TBK m.285 TMK m.561 muris muvazaası görünürde satış gizli bağış ispat"
        ]

    def test_concept_anchor_rules_do_not_force_irrelevant_exact_articles(
        self,
        mock_orchestrator,
    ):
        mock_retriever = MagicMock()

        from rag.retriever import RetrievalResult, RetrievalStats

        semantic_results = [
            RetrievalResult(
                chunk_id="tbk-584",
                text="Kefalet hükümleri",
                score=0.9,
                metadata={"law_short_name": "TBK", "madde_no": "584", "fikra_no": "1"},
            )
        ]
        stats = RetrievalStats(
            collection="test",
            query_preview="kefalet",
            top_k=20,
            filter_expr=None,
            hit_count=1,
            latency_ms=10.0,
        )
        mock_retriever.retrieve = MagicMock(return_value=(semantic_results, stats))
        mock_orchestrator.answer = AsyncMock(return_value=_make_orch_response("RAG cevabı"))

        app = _make_app(mock_orch=mock_orchestrator, mock_retriever=mock_retriever)
        new_store = ConversationStore()
        app.dependency_overrides[get_conversation_store] = lambda: new_store

        with TestClient(app) as c:
            resp = c.post(
                "/v1/chat/completions",
                json={
                    "messages": [
                        {
                            "role": "user",
                            "content": "Eş rızası olmadan verilen kefaletin geçerlilik değerlendirmesi nasıl yapılır?",
                        }
                    ],
                    "include_trace": True,
                },
            )

        assert resp.status_code == 200
        trace = resp.json()["trace"]
        assert trace["query_signals"]["forced_article_refs"] == []

    def test_no_retriever_still_works(self, client, mock_orchestrator):
        """Retriever yokken orchestrator boş chunk ile çağrılmalı."""
        mock_orchestrator.answer = AsyncMock(
            return_value=_make_orch_response("Direkt LLM cevabı")
        )
        resp = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "soru"}]},
        )
        assert resp.status_code == 200
        # Orchestrator çağrısındaki retrieved_chunks boş olmalı
        call_args = mock_orchestrator.answer.call_args
        retrieved = call_args.kwargs.get("retrieved_chunks", [])
        assert retrieved == []


# ---------------------------------------------------------------------------
# Health ve Legacy Endpoint Testleri
# ---------------------------------------------------------------------------


class TestMainApp:
    """main.py'deki health ve legacy endpoint testleri."""

    @pytest.fixture
    def main_client(self):
        # Direkt main.py app'ini import et
        from unittest.mock import patch, AsyncMock, MagicMock

        with patch("llm.client.LLMClient.chat", new=AsyncMock(return_value="ok")):
            with patch("guardrails.pipeline.GuardrailsPipeline.run") as mock_run:
                mock_gr = MagicMock()
                mock_gr.answer = "test yanıtı"
                mock_gr.blocked = False
                mock_gr.reasons = []
                mock_run.return_value = mock_gr
                import main
                with TestClient(main.app) as c:
                    yield c

    def test_health_endpoint(self, main_client):
        resp = main_client.get("/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "service" in data
        assert "guardrails" in data
        assert "retriever" in data
        assert "verification" in data

    def test_models_endpoint(self, main_client):
        resp = main_client.get("/v1/models")
        assert resp.status_code == 200
        data = resp.json()
        assert data["object"] == "list"
        assert len(data["data"]) >= 1
        assert data["data"][0]["id"] == "hukuk-ai-poc"
