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
import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from observability import get_metrics_registry
from llm.client import LLMResult, TokenUsage
from routers.chat import (
    ConversationStore,
    ChatCompletionRequest,
    ConversationMessage,
    _apply_source_cluster_deterministic_overrides,
    _apply_retrieval_plan_hints,
    _build_assembled_evidence,
    _build_annual_investment_program_expansion,
    _build_numbered_law_reference_expansion,
    _build_retrieval_plan_expansion,
    _build_source_cluster_candidates,
    _select_article_span_evidence,
    _clamp_families_to_strong_resolution,
    _build_precise_tmk_tbk_cross_law_answer,
    _contains_query_term,
    _extract_json_object,
    _extract_explicit_article_refs,
    _extract_law_mentions,
    _infer_requested_source_families,
    _prioritize_chunks_for_source_families,
    _resolve_chunk_source_family,
    _resolve_source_family_prior,
    _resolve_public_answer_text,
    _sanitize_source_cluster_selector_payload,
    _sanitize_retrieval_plan_payload,
    _should_use_cross_law_retrieval,
    _build_precise_tbk_answer,
    _detect_scope_refusal_reason,
    _build_multiturn_query,
    _stream_sse_response,
    get_conversation_store,
    router as chat_router,
)
from rag.orchestrator import OrchestratorResponse, RetrievedChunk
from session_store import RedisSessionBackend


# ---------------------------------------------------------------------------
# Fixtures & Helpers
# ---------------------------------------------------------------------------

def _make_orch_response(
    answer: str = "Test yanıtı.",
    citations: list[str] | None = None,
    blocked: bool = False,
    reasons: list[str] | None = None,
    verification: dict | None = None,
    usage: dict[str, int] | None = None,
) -> OrchestratorResponse:
    return OrchestratorResponse(
        answer=answer,
        citations=citations or ["TBK m.49"],
        blocked=blocked,
        guardrails_reasons=reasons or [],
        verification=verification,
        usage=usage,
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


@pytest.fixture(autouse=True)
def _trace_log_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("TRACE_LOG_DIR", str(tmp_path / "traces"))


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

    def test_redis_backend_roundtrip_and_eviction(self):
        class FakeRedis:
            def __init__(self):
                self.lists: dict[str, list[str]] = {}
                self.sorted_sets: dict[str, dict[str, float]] = {}

            def lrange(self, key, start, end):
                values = self.lists.get(key, [])
                if end == -1:
                    end = len(values) - 1
                return values[start : end + 1]

            def rpush(self, key, *values):
                self.lists.setdefault(key, []).extend(values)

            def ltrim(self, key, start, end):
                values = self.lists.get(key, [])
                if start < 0:
                    start = len(values) + start
                if end < 0:
                    end = len(values) + end
                self.lists[key] = values[max(start, 0) : end + 1]

            def zadd(self, key, mapping):
                self.sorted_sets.setdefault(key, {}).update(mapping)

            def zcard(self, key):
                return len(self.sorted_sets.get(key, {}))

            def zrange(self, key, start, end):
                items = sorted(self.sorted_sets.get(key, {}).items(), key=lambda item: item[1])
                if end == -1:
                    end = len(items) - 1
                return [member for member, _score in items[start : end + 1]]

            def delete(self, key):
                existed = key in self.lists
                self.lists.pop(key, None)
                return 1 if existed else 0

            def zrem(self, key, member):
                bucket = self.sorted_sets.get(key, {})
                existed = member in bucket
                bucket.pop(member, None)
                return 1 if existed else 0

        backend = RedisSessionBackend(
            redis_url="redis://example",
            namespace="test",
            max_sessions=2,
            max_messages_per_session=4,
            client=FakeRedis(),
        )
        store = ConversationStore(backend=backend)
        store.MAX_SESSIONS = 2
        store.MAX_MESSAGES_PER_SESSION = 4

        store.add_turn("s1", "soru1", "cevap1")
        store.add_turn("s2", "soru2", "cevap2")
        store.add_turn("s3", "soru3", "cevap3")

        assert store.session_count() == 2
        assert store.get_history("s1") == []
        assert len(store.get_history("s3")) == 2


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

    def test_ttk_query_is_no_longer_forced_out_of_scope(self):
        reason = _detect_scope_refusal_reason(
            "Türk Ticaret Kanunu'na göre anonim şirket kuruluş asgari sermayesi nedir?"
        )
        assert reason is None

    def test_tck_query_is_no_longer_forced_out_of_scope(self):
        reason = _detect_scope_refusal_reason(
            "TCK m.141 neyi düzenler?"
        )
        assert reason is None

    def test_tmk_query_is_no_longer_forced_out_of_scope(self):
        reason = _detect_scope_refusal_reason(
            "TMK'ya göre iyiniyet karinesi nedir ve hangi maddede düzenlenmiştir?"
        )
        assert reason is None

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

    def test_contains_query_term_matches_inflected_turkish_phrase_endings(self):
        assert _contains_query_term(
            "Eşler arasında yapılan bağışlamanın edinilmiş mallara katılma rejiminin tasfiyesindeki etkisi nasıldır?",
            "katılma rejimi",
        ) is True
        assert _contains_query_term(
            "Nafaka yükümlülüğü zamanaşımına uğrar mı?",
            "zamanaşımı",
        ) is True

    def test_contains_query_term_keeps_short_token_false_positive_guard(self):
        assert _contains_query_term(
            "Babam taşınmazını bana sattı; ancak gerçekte bağışlamak istediğini düşünüyorum.",
            "çek",
        ) is False

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

    def test_extract_explicit_article_refs_supports_numeric_law_ids(self):
        refs = _extract_explicit_article_refs(
            "3224 m.1 ile 8913838 m.1 birlikte nasıl okunur?"
        )
        assert ("3224", "1") in refs
        assert ("8913838", "1") in refs

    def test_extract_law_mentions_supports_names_and_codes(self):
        laws = _extract_law_mentions(
            "Türk Borçlar Kanunu ile TMK birlikte nasıl uygulanır?"
        )
        assert laws == ["TBK", "TMK"]

    def test_extract_law_mentions_supports_numeric_law_ids_from_article_refs(self):
        laws = _extract_law_mentions("3224 m.1 metni ile 126 m.1 birlikte değerlendirilsin.")
        assert laws == ["3224", "126"]

    def test_extract_law_mentions_infers_tbk_tmk_for_cross_law_concepts(self):
        laws = _extract_law_mentions(
            "Evli bir kişinin kefalet sözleşmesi yapmasında eş rızası şartı aile birliğinin "
            "korunması ilkesiyle nasıl ilişkilidir?"
        )
        assert laws == ["TBK", "TMK"]

    def test_extract_law_mentions_infers_tbk_tmk_for_nafaka_zamanasimi_family(self):
        laws = _extract_law_mentions(
            "Aile hukukunda öngörülen nafaka yükümlülüğü sözleşmeden doğan alacak gibi "
            "zamanaşımına uğrar mı, özel bir süre var mıdır?"
        )
        assert laws == ["TBK", "TMK"]

    def test_extract_law_mentions_infers_tbk_tmk_for_bagislama_tasfiye_family(self):
        laws = _extract_law_mentions(
            "Eşler arasında yapılan bağışlamanın edinilmiş mallara katılma rejiminin "
            "tasfiyesindeki etkisi nasıldır? Bu bağışlama denkleştirmeye tabi midir?"
        )
        assert laws == ["TBK", "TMK"]

    def test_infer_requested_source_families_detects_tuzuk(self):
        families = _infer_requested_source_families(
            "Tapu kütüğü, yevmiye defteri ve resmi belgeler için hangi tüzük merkezde olmalıdır?"
        )
        assert "tuzuk" in families

    def test_infer_requested_source_families_detects_university_and_regulation_family(self):
        families = _infer_requested_source_families(
            "Bir yüksek lisans öğrencisinin tez savunma jürisi için hangi üniversite yönetmeliği aranmalıdır?"
        )
        assert "uy" in families
        assert "yonetmelik" in families

    def test_source_family_prior_detects_cb_karar_from_karar_sayisi(self):
        resolution = _resolve_source_family_prior(
            "Karar Sayısı: 3350 olan İthalat Rejimi Kararı hangi belge ailesindedir?"
        )

        assert resolution.predicted_family == "cb_karar"
        assert resolution.family_confidence >= 0.75
        assert "cb_karar" in resolution.routing_families

    def test_source_family_prior_keeps_investment_program_decision_as_cb_karar_candidate(self):
        resolution = _resolve_source_family_prior(
            "Yatırım programı kararı mı, yoksa yıl içi işlemleri düzenleyen genelge de mi aranmalı?"
        )
        families = [candidate.family for candidate in resolution.family_candidates]

        assert "cb_karar" in families
        assert "cb_genelge" in families
        assert resolution.family_confidence < 0.75
        assert resolution.routing_families == []

    def test_source_family_prior_detects_investment_incentive_decision_terms(self):
        resolution = _resolve_source_family_prior(
            "Yatırım teşvik belgesi başvurusu 2026'da yapılıyor; eski 2012/3305 rejimi mi, "
            "yoksa 30.05.2025 tarihli yeni sistem mi esas alınmalı?"
        )

        assert resolution.predicted_family == "cb_karar"
        assert "cb_karar" in resolution.routing_families

    def test_source_family_prior_detects_cbk_abbreviation(self):
        resolution = _resolve_source_family_prior(
            "3 sayılı CBK'nın güncel adı ve 19.02.2026 tarihli değişikliği atlanabilir mi?"
        )

        assert resolution.predicted_family == "cb_kararname"
        assert "cb_kararname" in resolution.routing_families

    def test_source_family_prior_detects_archive_cb_regulation_terms(self):
        resolution = _resolve_source_family_prior(
            "Arşiv mevzuatı sorusunda 1988 tarihli eski metin mi, yoksa 2019 tarihli güncel metin mi kullanılmalı?"
        )

        assert resolution.predicted_family == "cb_yonetmelik"
        assert "cb_yonetmelik" in resolution.routing_families

    def test_source_family_prior_keeps_multi_family_for_university_regulation(self):
        resolution = _resolve_source_family_prior(
            "Bir yüksek lisans öğrencisinin tez savunması için üniversite yönetmeliği ne der?"
        )

        assert resolution.predicted_family == "uy"
        assert "uy" in resolution.routing_families
        assert "yonetmelik" in resolution.routing_families

    def test_source_family_prior_uses_law_reference_as_kanun_signal(self):
        resolution = _resolve_source_family_prior(
            "TBK m.49 haksız fiil bakımından ne düzenler?",
            mentioned_laws=["TBK"],
            explicit_article_refs=[("TBK", "49")],
        )

        assert resolution.predicted_family == "kanun"
        assert resolution.family_confidence >= 0.75
        assert resolution.routing_families == []

    def test_source_family_prior_prefers_specific_document_type_over_number_reference(self):
        resolution = _resolve_source_family_prior(
            "551, 554, 555 ve 556 sayılı KHK'lara dayanmak güvenli midir?",
            mentioned_laws=["551", "554", "555", "556"],
        )

        assert resolution.predicted_family == "khk"
        assert resolution.family_confidence >= 0.75
        assert resolution.routing_families == ["khk"]

    def test_numbered_law_reference_expansion_handles_comma_and_ve_lists(self):
        expansion = _build_numbered_law_reference_expansion(
            "551, 554, 555 ve 556 sayılı KHK'lara dayanmak güvenli midir?"
        )

        assert "551 sayılı KHK" in expansion
        assert "554 sayılı KHK" in expansion
        assert "555 sayılı KHK" in expansion
        assert "556 sayılı KHK" in expansion

    def test_annual_investment_program_expansion_uses_reference_year_without_hardcoded_decision_no(self):
        expansion = _build_annual_investment_program_expansion(
            "Bu soruyu 2026-04-19 tarihindeki yürürlük durumuna göre cevapla. "
            "Kamu yatırım projesinin tutarı değişecekse yatırım programı kararı mı aranmalı?"
        )

        assert "2026 yılı kamu yatırım programı" in expansion
        assert "karar sayısı" in expansion
        assert "10868" not in expansion

    def test_chunk_source_family_prefers_khk_title_over_generic_metadata(self):
        chunk = RetrievedChunk(
            text="Markalar hakkında KHK",
            citation="556 m.82/f.0",
            source="556",
            score=0.9,
            metadata={
                "source_title": "MARKALARIN KORUNMASI HAKKINDA KANUN HÜKMÜNDE KARARNAME",
                "belge_turu": "kanun",
            },
        )

        assert _resolve_chunk_source_family(chunk) == "khk"

    def test_prioritize_chunks_for_source_families_prefers_matching_family(self):
        from rag.orchestrator import RetrievedChunk

        chunks = [
            RetrievedChunk(
                text="Kanun chunk",
                citation="TMK m.997",
                source="TMK",
                score=0.95,
                metadata={"belge_turu": "kanun"},
            ),
            RetrievedChunk(
                text="Tüzük chunk",
                citation="20135150 m.2",
                source="20135150",
                score=0.75,
                metadata={"belge_turu": "tuzuk"},
            ),
        ]

        prioritized = _prioritize_chunks_for_source_families(
            query="Tapu kütüğü ve yardımcı siciller için hangi tüzük merkezde olmalıdır?",
            chunks=chunks,
            source_families=["tuzuk"],
        )

        assert prioritized[0].citation == "20135150 m.2"

    def test_prioritize_chunks_uses_source_cluster_and_text_overlap_without_family_hint(self):
        from rag.orchestrator import RetrievedChunk

        chunks = [
            RetrievedChunk(
                text="Çanakkale alan başkanlığında personel çalışma usulü düzenlenir.",
                citation="20008 m.41",
                source="20008",
                score=0.95,
                metadata={"source_title": "ÇANAKKALE ... PERSONELİ HAKKINDA YÖNETMELİK", "belge_turu": "kky"},
            ),
            RetrievedChunk(
                text="İşe iade davası, fesih bildiriminin tebliğinden itibaren bir ay içinde açılır.",
                citation="IK m.20",
                source="IK",
                score=0.90,
                metadata={"source_title": "İŞ KANUNU", "belge_turu": "kanun"},
            ),
            RetrievedChunk(
                text="Otuz veya daha fazla işçi çalıştırılan işyerinde altı ay kıdemi olan işçinin feshi geçerli sebebe dayanmalıdır.",
                citation="IK m.18",
                source="IK",
                score=0.89,
                metadata={"source_title": "İŞ KANUNU", "belge_turu": "kanun"},
            ),
        ]

        prioritized = _prioritize_chunks_for_source_families(
            query="42 çalışanlı bir işyerinde 8 aylık kıdemi bulunan işçi işe iade yoluna gidebilir mi?",
            chunks=chunks,
            source_families=[],
        )

        assert prioritized[0].citation == "IK m.20"

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

    def test_cross_law_retrieval_enabled_for_nafaka_zamanasimi_family(self):
        laws = ["TBK", "TMK"]
        assert _should_use_cross_law_retrieval(
            "Aile hukukunda öngörülen nafaka yükümlülüğü TBK'daki sözleşmeden doğan alacak "
            "gibi zamanaşımına uğrar mı?",
            laws,
        ) is True

    def test_kefalet_scope_does_not_force_family_home_invalidity_anchor(self):
        laws = ["TBK", "TMK"]
        assert _should_use_cross_law_retrieval(
            "Kefalet sözleşmesinde eşin rızası hangi durumlarda aranmaz?",
            laws,
        ) is False

    def test_extract_json_object_parses_fenced_json(self):
        payload = _extract_json_object(
            '```json\n{"law_hints":["IK"],"source_family_hints":["kanun"],"term_hints":["işe iade"]}\n```'
        )
        assert payload == {
            "law_hints": ["IK"],
            "source_family_hints": ["kanun"],
            "term_hints": ["işe iade"],
        }

    def test_sanitize_retrieval_plan_payload_normalizes_laws_families_and_terms(self):
        payload = _sanitize_retrieval_plan_payload(
            {
                "law_hints": ["İK", "Türk Medeni Kanunu", "3194", "233 sayılı KHK", "uydurma"],
                "source_family_hints": ["Tüzük", "Üniversite Yönetmeliği"],
                "term_hints": [" işe iade ", "geçerli sebep", "x"],
            }
        )

        assert payload == {
            "law_hints": ["IK", "TMK", "3194", "233"],
            "source_family_hints": ["tuzuk", "uy"],
            "term_hints": ["işe iade", "geçerli sebep"],
        }

    def test_build_retrieval_plan_expansion_includes_numeric_law_hints_as_search_terms(self):
        expansion = _build_retrieval_plan_expansion(
            {
                "law_hints": ["3194", "IK"],
                "source_family_hints": ["kanun"],
                "term_hints": ["yapı tatil tutanağı"],
            }
        )

        assert "3194 sayılı kanun" in expansion
        assert "IK" in expansion
        assert "yapı tatil tutanağı" in expansion

    def test_build_numbered_law_reference_expansion_adds_khk_reference_variants(self):
        expansion = _build_numbered_law_reference_expansion(
            "666 sayılı KHK'nın hâlâ referans değeri var mıdır?"
        )

        assert "666 sayılı KHK" in expansion
        assert "KHK-666" in expansion
        assert "KHK/666" in expansion
        assert "KHK-666/1 md" in expansion

    def test_apply_retrieval_plan_hints_merges_query_laws_and_families(self):
        retrieval_query, mentioned_laws, requested_source_families, retrieval_top_k = _apply_retrieval_plan_hints(
            retrieval_query="İşe iade davası açabilir mi?",
            mentioned_laws=[],
            requested_source_families=[],
            applied_expansions=[],
            retrieval_top_k=8,
            retrieval_plan={
                "law_hints": ["IK"],
                "source_family_hints": ["kanun"],
                "term_hints": ["işe iade", "geçerli sebep"],
            },
        )

        assert mentioned_laws == []
        assert "kanun" in requested_source_families
        assert "işe iade" in retrieval_query
        assert "geçerli sebep" in retrieval_query
        assert retrieval_top_k == 20

    def test_build_source_cluster_candidates_groups_chunks_by_source_key(self):
        chunks = [
            RetrievedChunk(
                text="İş güvencesi",
                citation="IK m.21/f.0",
                source="IK",
                score=0.91,
                metadata={"source_title": "İŞ KANUNU", "law_short_name": "IK", "belge_turu": "kanun"},
            ),
            RetrievedChunk(
                text="Toplu işçi çıkarma",
                citation="1475 m.24/f.0",
                source="1475",
                score=0.89,
                metadata={"source_title": "İŞ KANUNU", "law_short_name": "1475", "belge_turu": "mulga_kanun"},
            ),
            RetrievedChunk(
                text="Tapu sicili",
                citation="20135150 m.7/f.0",
                source="20135150",
                score=0.93,
                metadata={"source_title": "TAPU SİCİLİ TÜZÜĞÜ", "law_short_name": "20135150", "belge_turu": "tuzuk"},
            ),
        ]

        candidates = _build_source_cluster_candidates(chunks, limit=8)

        assert [item["cluster_id"] for item in candidates] == ["C1", "C2"]
        assert candidates[0]["display_title"] == "İŞ KANUNU"
        assert candidates[0]["laws"] == ["IK", "1475"]
        assert candidates[0]["chunk_count"] == 2
        assert candidates[1]["display_title"] == "TAPU SİCİLİ TÜZÜĞÜ"

    def test_sanitize_source_cluster_selector_payload_keeps_only_known_clusters_and_laws(self):
        candidates = [
            {
                "cluster_id": "C1",
                "source_key": "iş kanunu",
                "display_title": "İŞ KANUNU",
                "source_family": "kanun",
                "laws": ["IK", "1475"],
            },
            {
                "cluster_id": "C2",
                "source_key": "tapu sicili tüzüğü",
                "display_title": "TAPU SİCİLİ TÜZÜĞÜ",
                "source_family": "tuzuk",
                "laws": ["20135150"],
            },
        ]

        payload = _sanitize_source_cluster_selector_payload(
            {
                "selected_cluster_ids": ["C2", "C9", "C1"],
                "selected_law_hints": ["20135150", "IK", "TBK"],
            },
            candidates=candidates,
        )

        assert payload == {
            "selected_cluster_ids": ["C2", "C1"],
            "selected_law_hints": ["20135150", "IK"],
        }

    def test_source_cluster_overrides_prefer_identifier_match_inside_requested_family(self):
        candidates = [
            {
                "cluster_id": "C1",
                "source_key": "markalarin korunmasi hakkinda kanun hükmünde kararname",
                "display_title": "MARKALARIN KORUNMASI HAKKINDA KANUN HÜKMÜNDE KARARNAME",
                "source_family": "khk",
                "laws": ["556"],
                "citations": ["556 m.82/f.0"],
            },
            {
                "cluster_id": "C2",
                "source_key": "sanayi bakanligi khk",
                "display_title": "SANAYİ VE TEKNOLOJİ BAKANLIĞI HAKKINDA KHK",
                "source_family": "khk",
                "laws": ["635"],
                "citations": ["635 m.1/f.0"],
            },
            {
                "cluster_id": "C3",
                "source_key": "yükseköğretim kanunu",
                "display_title": "YÜKSEKÖĞRETİM KANUNU",
                "source_family": "kanun",
                "laws": ["2547"],
                "citations": ["2547 m.44/f.0"],
            },
        ]

        payload = _apply_source_cluster_deterministic_overrides(
            payload={"selected_cluster_ids": ["C2"], "selected_law_hints": ["635"]},
            candidates=candidates,
            user_query="551, 554, 555 ve 556 sayılı KHK'lara dayanmak güvenli midir?",
            requested_source_families=["khk"],
        )

        assert payload["selected_cluster_ids"] == ["C1"]
        assert payload["selected_law_hints"] == ["556"]

    def test_source_cluster_overrides_do_not_let_law_number_escape_requested_family(self):
        candidates = [
            {
                "cluster_id": "C1",
                "source_key": "yükseköğretim kanunu",
                "display_title": "YÜKSEKÖĞRETİM KANUNU",
                "source_family": "kanun",
                "laws": ["2547"],
                "citations": ["2547 m.44/f.0"],
            },
            {
                "cluster_id": "C2",
                "source_key": "kırklareli üniversitesi lisansüstü eğitim yönetmeliği",
                "display_title": "KIRKLARELİ ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ",
                "source_family": "uy",
                "laws": ["40969"],
                "citations": ["40969 m.27/f.0"],
            },
        ]

        payload = _apply_source_cluster_deterministic_overrides(
            payload={"selected_cluster_ids": ["C1"], "selected_law_hints": ["2547"]},
            candidates=candidates,
            user_query="Yalnız 2547 yeterli midir, yoksa hangi üniversite yönetmeliği merkezde olmalıdır?",
            requested_source_families=["uy", "yonetmelik"],
        )

        assert payload["selected_cluster_ids"] == ["C2"]
        assert payload["selected_law_hints"] == ["40969"]

    def test_source_cluster_overrides_prefer_reference_year_for_annual_investment_programs(self):
        candidates = [
            {
                "cluster_id": "C1",
                "source_key": "2019 yatirim programi karari",
                "display_title": "2019 YILI YATIRIM PROGRAMININ KABULÜNE DAİR KARAR",
                "source_family": "cb_karar",
                "laws": ["767"],
                "citations": ["767 m.2/f.0"],
                "excerpts": ["2019 Yılı Yatırım Programı"],
            },
            {
                "cluster_id": "C2",
                "source_key": "2026 yatirim programi karari",
                "display_title": "2026 YILI YATIRIM PROGRAMININ KABULÜNE DAİR KARAR",
                "source_family": "cb_karar",
                "laws": ["10868"],
                "citations": ["10868 m.0/f.0"],
                "excerpts": ["Karar Sayısı: 10868 15 Ocak 2026"],
            },
        ]

        payload = _apply_source_cluster_deterministic_overrides(
            payload={"selected_cluster_ids": ["C1"], "selected_law_hints": ["767"]},
            candidates=candidates,
            user_query="2026 yılında kamu yatırım projesi için yatırım programı kararı mı aranmalı?",
            requested_source_families=["cb_karar"],
        )

        assert payload["selected_cluster_ids"] == ["C2"]
        assert payload["selected_law_hints"] == ["10868"]

    def test_source_cluster_overrides_reject_weak_llm_cluster_without_title_or_identifier_support(self):
        candidates = [
            {
                "cluster_id": "C1",
                "source_key": "bedelsiz arsa devri yonetmeligi",
                "display_title": "HAZİNE ARAZİLERİNİN BEDELSİZ DEVRİNE İLİŞKİN YÖNETMELİK",
                "source_family": "yonetmelik",
                "laws": ["20047114"],
                "citations": ["20047114 m.0/f.0"],
                "excerpts": ["Arazi veya arsaların gerçek kişilere devrine ilişkin usuller."],
            },
            {
                "cluster_id": "C2",
                "source_key": "yatirimlarda devlet yardimlari karari",
                "display_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR",
                "source_family": "cb_karar",
                "laws": ["9903"],
                "citations": ["9903 m.1/f.0"],
                "excerpts": ["Yatırım teşvik belgesi başvuruları ve geçiş hükümleri."],
            },
        ]

        payload = _apply_source_cluster_deterministic_overrides(
            payload={"selected_cluster_ids": ["C1"], "selected_law_hints": ["20047114"]},
            candidates=candidates,
            user_query="Yatırım teşvik belgesi başvurusu 2026'da yapılıyor; yeni sistem mi esas alınmalı?",
            requested_source_families=["cb_karar"],
        )

        assert payload["selected_cluster_ids"] == ["C2"]
        assert payload["selected_law_hints"] == ["9903"]

    def test_clamp_families_removes_planner_family_that_conflicts_with_strong_resolution(self):
        resolution = _resolve_source_family_prior(
            "Yalnız 2547 yeterli midir, yoksa hangi üniversite yönetmeliği merkezde olmalıdır?"
        )
        families = _clamp_families_to_strong_resolution(
            ["uy", "yonetmelik", "kanun", "mulga_kanun"],
            resolution,
        )

        assert "uy" in families
        assert "yonetmelik" in families
        assert "kanun" not in families
        assert "mulga_kanun" not in families

    def test_resolve_public_answer_text_prefers_hardened_contract_projection(self):
        resolved = _resolve_public_answer_text(
            answer_text="Bu soru bakımından doğrudan değerlendirilmesi gereken başlıca hükümler şunlardır:\n- ...",
            answer_contract={
                "answer_text": "Tapu sicili bakımından merkez tüzük Tapu Sicili Tüzüğü'dür. [Kaynak: 20135150 m.7/f.0]",
                "final_mode": "answer",
            },
            final_mode="answer",
        )

        assert resolved == "Tapu sicili bakımından merkez tüzük Tapu Sicili Tüzüğü'dür. [Kaynak: 20135150 m.7/f.0]"

    def test_prioritize_chunks_prefers_selected_source_cluster(self):
        chunks = [
            RetrievedChunk(
                text="İade hükümleri",
                citation="7088 m.2/f.0",
                source="7088",
                score=0.99,
                metadata={"source_title": "7088 SAYILI KARAR", "belge_turu": "kanun"},
            ),
            RetrievedChunk(
                text="Geçersiz sebeple yapılan feshin sonuçları",
                citation="IK m.21/f.0",
                source="IK",
                score=0.90,
                metadata={"source_title": "İŞ KANUNU", "law_short_name": "IK", "belge_turu": "kanun"},
            ),
        ]

        prioritized = _prioritize_chunks_for_source_families(
            query="Performans gerekçesiyle işten çıkarılan işçi işe iade davası açabilir mi?",
            chunks=chunks,
            source_families=["kanun"],
            selected_source_keys={"İŞ KANUNU".strip().lower()},
        )

        assert prioritized[0].citation == "IK m.21/f.0"

    def test_article_span_selector_prioritizes_explicit_article_in_same_document(self):
        chunks = [
            RetrievedChunk(
                text="Başvuru usulü madde 8 kapsamında açıklanır.",
                citation="40969 m.8/f.0",
                source="40969",
                score=0.98,
                metadata={
                    "source_title": "KIRKLARELİ ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ",
                    "belge_turu": "uy",
                    "law_no": "40969",
                    "madde_no": "8",
                },
            ),
            RetrievedChunk(
                text="Tez danışmanı atanması madde 12 kapsamında düzenlenir.",
                citation="40969 m.12/f.0",
                source="40969",
                score=0.77,
                metadata={
                    "source_title": "KIRKLARELİ ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ",
                    "belge_turu": "uy",
                    "law_no": "40969",
                    "madde_no": "12",
                },
            ),
        ]

        selected, selector = _select_article_span_evidence(
            query="40969 sayılı yönetmeliğin 12. maddesinde tez danışmanı nasıl düzenlenir?",
            chunks=chunks,
            requested_source_families=["uy", "yonetmelik"],
            explicit_article_refs=[],
        )

        assert selected[0].citation == "40969 m.12/f.0"
        assert selector["applied"] is True
        assert selector["query_article_tokens"] == ["12"]
        assert "12" in selector["selected_articles"]

    def test_article_span_selector_keeps_requested_family_ahead_of_cross_family_article_hit(self):
        chunks = [
            RetrievedChunk(
                text="Kanun madde 12 metni.",
                citation="2547 m.12/f.0",
                source="2547",
                score=0.99,
                metadata={"source_title": "YÜKSEKÖĞRETİM KANUNU", "belge_turu": "kanun", "madde_no": "12"},
            ),
            RetrievedChunk(
                text="Üniversite yönetmeliğinde tez danışmanı usulü düzenlenir.",
                citation="40969 m.27/f.0",
                source="40969",
                score=0.70,
                metadata={
                    "source_title": "KIRKLARELİ ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ",
                    "belge_turu": "uy",
                    "madde_no": "27",
                },
            ),
        ]

        selected, selector = _select_article_span_evidence(
            query="Yalnız kanun değil, üniversite yönetmeliğine göre tez danışmanı usulü nedir?",
            chunks=chunks,
            requested_source_families=["uy", "yonetmelik"],
            explicit_article_refs=[],
        )

        assert selected[0].citation == "40969 m.27/f.0"
        assert selector["top_scores"][0]["source_family"] == "uy"

    def test_assembled_evidence_exposes_phase4_canonical_span_fields(self):
        chunk = RetrievedChunk(
            text=(
                "Tez danışmanı, öğrencinin programı ve çalışmanın niteliği dikkate alınarak atanır. "
                "Danışman değişikliği ilgili enstitü kurulunca sonuçlandırılır."
            ),
            citation="40969 m.12/f.0",
            source="40969",
            score=0.84,
            metadata={
                "full_title": "KIRKLARELİ ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ",
                "source_title": "KIRKLARELİ ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ",
                "belge_turu": "uy",
                "law_no": "40969",
                "madde_no": "12",
                "effective_state": "active",
                "canonical_identifier_display": "40969 m.12",
            },
        )

        evidence = _build_assembled_evidence([chunk], query="Tez danışmanı nasıl atanır?")

        assert evidence[0]["source_family"] == "uy"
        assert evidence[0]["source_title"].startswith("KIRKLARELİ ÜNİVERSİTESİ")
        assert evidence[0]["source_identifier"] == "40969 m.12"
        assert evidence[0]["article_or_section"] == "12"
        assert evidence[0]["effective_state"] == "active"
        assert "Tez danışmanı" in evidence[0]["quoted_or_extracted_span"]


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
            (
                "İşçinin sadakat ve özen borcu TBK kapsamında nasıl düzenlenmiştir?",
                ["TBK m.396"],
                ["sadakatle davranmak", "iş sırlarını"],
            ),
            (
                "İş yerinde işveren tarafından sürekli hakarete uğratılan işçi, bunu gerekçe göstererek sözleşmesini derhal feshedebilir mi?",
                ["TBK m.435", "TBK m.417"],
                ["kişiliğini korumak", "haklı sebeple derhâl feshedebilir"],
            ),
            (
                "İşverenim 3 aydır ücretimi ödemiyor. TBK'ya göre bu durumda hangi hakları kullanabilirim?",
                ["TBK m.401", "TBK m.435", "TBK m.437"],
                ["ücret alacağını talep", "zararın tamamen giderilmesi"],
            ),
            (
                "TBK m.504 kapsamında vekil, müvekkilin talimatlarına uymak zorunda mıdır? Talimat dışı hareket ettiğinde sorumluluk nasıl doğar?",
                ["TBK m.504", "TBK m.502"],
                ["Vekalet iliskisinin temel cercevesi", "vekaletin kapsamini"],
            ),
            (
                "'Vekalet sözleşmesi yazılı şekle tabi olmadığından sözlü da kurulabilir; sözlü vekil yaptığı işleri ispat edemezse ücret alamaz' iddiası doğru mudur?",
                ["TBK m.502", "TBK m.510", "TBK m.12"],
                ["hiçbir şekle bağlı değildir", "sözleşme veya teamül varsa vekil ücrete hak kazanır"],
            ),
            (
                "Ücretli vekalet sözleşmesinde müvekkil haklı bir neden olmaksızın azil yaparsa vekilin tazminat hakları nelerdir?",
                ["TBK m.511", "TBK m.512"],
                ["uygun olmayan zamanda", "zararını gidermekle yükümlüdür"],
            ),
            (
                "TBK m.512 uyarınca vekalet sözleşmesi hangi hallerde kendiliğinden sona erer ve azil bildirimi için özel bir şekil şartı öngörülmüş müdür?",
                ["TBK m.512", "TBK m.513"],
                ["özel bir şekil şartı öngörülmemiştir", "ölümü, ehliyetini kaybetmesi veya iflası"],
            ),
            (
                "TBK m.509 kapsamında vekilin özen borcunu ihlal etmesi halinde müvekkile karşı sorumluluğunun koşulları ve kapsamı nedir?",
                ["TBK m.509", "TBK m.504"],
                ["vekâletin kapsamı", "müvekkili zarara uğratıyorsa"],
            ),
            (
                "TBK m.508 uyarınca vekilin işi başkasına (alt vekil) bırakabilmesi hangi koşullara tabidir ve alt vekil aracılığıyla oluşan zarardan asıl vekilin sorumluluğu devam eder mi?",
                ["TBK m.508"],
                ["alt vekâlet", "alt vekil seçimi"],
            ),
            (
                "Azil ve istifanın vekâlet sözleşmesine etkisi TBK'da nasıl düzenlenmiştir?",
                ["TBK m.512", "TBK m.513"],
                ["Azil ve istifa", "kendiliğinden sona ermesine yol açar"],
            ),
            (
                "TBK m.507 uyarınca müvekkil aynı iş için birden fazla vekil atamışsa bu vekillerin birbirine ve müvekkile karşı sorumluluğu nasıl belirlenir?",
                ["TBK m.507", "TBK m.162"],
                ["birden çok vekilin müvekkile verdikleri zarar", "müteselsil sorumluluk"],
            ),
            (
                "Vekilim benim adıma imzaladığı sözleşmede verdiğim yetkinin sınırlarını aştı; bu sözleşmeyi geçersiz sayabilir miyim?",
                ["TBK m.504", "TBK m.46"],
                ["yetkisiz temsil", "onay verirse sözleşme hüküm doğurur"],
            ),
            (
                "TBK m.513 uyarınca müvekkilin ölümü veya iflası halinde vekalet ilişkisinin sona ermesiyle birlikte vekilin başlatılmış işleri tamamlama yükümlülüğü devam eder mi?",
                ["TBK m.513", "TBK m.512"],
                ["başlatılmış işleri sürdürmek", "zarar önlemek"],
            ),
            (
                "TBK m.514 kapsamında vekalet sona erdiğinden haberdar olmayan vekil üçüncü kişilerle işlem yapmayı sürdürürse bu işlemler geçerli midir?",
                ["TBK m.514", "TBK m.512"],
                ["vekâlet devam ediyormuş gibi sonuç doğurur", "iyiniyetli işlem güvenliğinin korunması"],
            ),
            (
                "TBK m.503 kapsamında vekilin özen borcunun standartı nasıl belirlenir? Avukatlık gibi serbest meslek vekâletlerinde bu standart farklı mıdır?",
                ["TBK m.503", "TBK m.509"],
                ["basiretli ve mesleki özeni yüksek", "avukatlık gibi serbest meslek vekâletlerinde"],
            ),
            (
                "Bir arkadaşımın bankaya olan borcuna kefil oldum; asıl borçlu ödeme yapamıyor. Kefil olarak hangi aşamaları izlemeliyim?",
                ["TBK m.587", "TBK m.586", "TBK m.596"],
                ["doğrudan kefile başvurabilir", "halef olur"],
            ),
            (
                "TBK m.586 kapsamında müteselsil kefalette kefilin alacaklıya karşı sorumluluğu nasıl belirlenir ve adi kefaletle temel farkı nedir?",
                ["TBK m.585", "TBK m.586"],
                ["doğrudan kefile", "önce asıl borçluya başvurur"],
            ),
            (
                "TBK m.401-402 kapsamında işçinin ücret alacaklarının korunmasına yönelik özel güvenceler nelerdir?",
                ["TBK m.401", "TBK m.402"],
                ["emsal ücreti", "yüzde elli fazlasıyla"],
            ),
            (
                "TBK m.587 uyarınca adi kefalet ile müteselsil kefaletın farkı nedir? Adi kefalette alacaklının asıl borçluya önce başvurma zorunluluğu ne zaman geçerlidir?",
                ["TBK m.587", "TBK m.586"],
                ["kendi payı için adi kefil gibi", "asıl borçluya önce başvurmadan"],
            ),
            (
                "TBK m.589 kapsamında kefilin asıl borçluya ait def'ileri kullanabilmesinin sınırları nelerdir? Hangi def'ileri kefil kesinlikle kullanamaz?",
                ["TBK m.589", "TBK m.590"],
                ["şahsına sıkı sıkıya bağlı", "takibin durdurulmasını"],
            ),
            (
                "TBK m.598 kapsamında kefil, asıl borçlu ödeme yapmadan önce ona karşı hangi durumlarda rücu hakkını kullanabilir?",
                ["TBK m.598", "TBK m.596"],
                ["on yıllık azamî süreyi", "ödeme sonrası halefiyet"],
            ),
            (
                "'TBK m.584'teki eş rızası şartı yalnızca konut amaçlı kiralama için verilen kefalet sözleşmelerinde uygulanır' iddiası doğru mudur?",
                ["TBK m.584", "TBK m.583"],
                ["genel olarak evli kişinin kefil olmasına", "kendi el yazısıyla"],
            ),
            (
                "TBK m.603 kapsamında kefalet sözleşmesinden doğan alacaklarda zamanaşımı nasıl düzenlenmiştir? Asıl borç zamanaşımına uğrasa dahi kefalet alacağı devam eder mi?",
                ["TBK m.603", "TBK m.125"],
                ["uygulama alanını genişletir", "otomatik olarak sınırsız"],
            ),
            (
                "Kiracım sözleşmeyi erken feshetti; sözleşmede 10.000 TL cezai şart var ama bu çok yüksek. Mahkeme bu miktarı indirebilir mi?",
                ["TBK m.182", "TBK m.27"],
                ["kendiliğinden indirir", "kesin hükümsüzdür"],
            ),
            (
                "TBK m.181 uyarınca cayma akçesi nedir ve kümülatif ceza şartından farkı nedir? Cayma akçesi ödendikten sonra sözleşmeden dönülmüş sayılır mı?",
                ["TBK m.181", "TBK m.179"],
                ["ceza koşulu hükümlerinin uygulanacağını", "dönme sonucunu"],
            ),
            (
                "TBK m.180 kapsamında bağımsız (kümülatif) ceza şartında alacaklı hem borcun ifasını hem de ceza şartını aynı anda talep edebilir mi?",
                ["TBK m.179", "TBK m.180"],
                ["birlikte isteme imkânına", "bağımsız ceza şartında"],
            ),
            (
                "TBK m.179 uyarınca seçimlik ceza şartında alacaklı hem asıl borcun ifasını hem de ceza şartını eş zamanlı talep edebilir mi?",
                ["TBK m.179", "TBK m.180"],
                ["seçimlik ceza şartında", "istisnadır"],
            ),
            (
                "Ceza şartı miktarı asıl borç miktarını çok aşan bir sözleşmede bu ceza şartının hukuki geçerliliği nasıldır?",
                ["TBK m.182", "TBK m.27"],
                ["Fahiş ceza şartı", "indirim müdahalesidir"],
            ),
            (
                "Ceza şartının kararlaştırıldığı asıl sözleşme geçersiz sayılırsa ceza şartının akıbeti ne olur?",
                ["TBK m.179", "TBK m.182"],
                ["asıl borç ilişkisine bağlıdır", "ifası talep edilemez"],
            ),
            (
                "'Ceza şartının ödenmesi borçluyu asıl borcun ifasından tamamen kurtarır' iddiası TBK kapsamında doğru mudur?",
                ["TBK m.179", "TBK m.180"],
                ["genel kural olarak doğru değildir", "bağımsız (kümülatif) ceza şartında"],
            ),
            (
                "Eser sözleşmesinde yüklenicinin işi geç teslim etmesi durumunda kararlaştırılan ceza şartının hâkim tarafından TBK m.182/3 uyarınca indirilmesi için yüklenicinin kısmi ifası ve özenle çalışması gibi faktörler göz önünde tutulur mu?",
                ["TBK m.181", "TBK m.182", "TBK m.183"],
                ["fahiş ceza koşulunu", "kısmi ifa"],
            ),
            (
                "TBK m.181 uyarınca cayma akçesi kararlaştırılan bir sözleşmede her iki taraf da cayma hakkını kullanabilir mi, yoksa bu hak yalnızca belirli bir tarafa mı tanınabilir? Cayma akçesinin yalnızca bir taraf için öngörülmesinin hukuki geçerliliği nedir?",
                ["TBK m.181", "TBK m.26"],
                ["sözleşme serbestisinin", "tek taraflı cayma hakkı"],
            ),
            (
                "TBK m.396 kapsamında hizmet sözleşmesinde düzenlenen rekabet yasağının coğrafi kapsam, süre ve alan bakımından sınırları nasıl belirlenir ve aşırı rekabet yasağının sonucu nedir?",
                ["TBK m.396", "TBK m.397"],
                ["coğrafi alan", "hakkaniyete aykırı"],
            ),
            (
                "Rekabet yasağı anlaşmasının geçerliliği için TBK'da aranan şartlar nelerdir?",
                ["TBK m.444", "TBK m.445", "TBK m.446"],
                ["fiil ehliyetine sahip", "iki yılı"],
            ),
            (
                "TBK m.397-398 kapsamında rekabet yasağına aykırılık halinde uygulanabilecek yaptırımlar nelerdir?",
                ["TBK m.397", "TBK m.398", "TBK m.399"],
                ["ceza şartını", "durdurulmasını"],
            ),
            (
                "TBK m.432 kapsamında belirsiz süreli hizmet sözleşmelerinde fesih bildirim (ihbar) süreleri nasıl belirlenir ve bu sürelere uyulmamasının sonuçları nelerdir?",
                ["TBK m.432", "TBK m.433"],
                ["hizmet süresine göre", "tazminat sonuçlarını"],
            ),
            (
                "'İşçi istifa etmişse işveren hiçbir koşulda tazminat ödemeye yükümlü değildir' iddiası TBK açısından doğru mudur?",
                ["TBK m.438", "TBK m.439"],
                ["mutlak ifade doğru değildir", "işverenin tazminat isteme hakkı"],
            ),
            (
                "TBK m.438 uyarınca hizmet sözleşmesinin kötü niyetle feshinde işçinin talep edebileceği tazminatın hesaplanma esasları nelerdir?",
                ["TBK m.438", "TBK m.440"],
                ["bakiye süre", "hakkaniyet ölçütleri"],
            ),
            (
                "TBK m.401 kapsamında işçinin ücret alacaklarının korunmasına yönelik hangi mekanizmalar öngörülmüş ve ücretin ödenmemesi halinde işçinin başvurabileceği hukuki yollar nelerdir?",
                ["TBK m.401", "TBK m.408"],
                ["ücret alacağının", "kabul temerrüdüne"],
            ),
            (
                "TBK m.393 uyarınca hizmet sözleşmesinin tanımı nedir ve eser sözleşmesinden temel farkı nasıl belirlenir?",
                ["TBK m.393", "TBK m.470"],
                ["bağımlı biçimde iş görmeyi", "sonuç taahhüdüne"],
            ),
            (
                "TBK m.421 uyarınca işverenin çalışana yıllık ücretli izin kullandırma yükümlülüğü var mıdır? Bu yükümlülüğün ihlalinin sonuçları nelerdir?",
                ["TBK m.421", "TBK m.422"],
                ["dinlenme ve izin rejimine", "yıllık ücretli izin"],
            ),
            (
                "TBK m.420 uyarınca belirli süreli hizmet sözleşmesinin geçerli kurulabilmesi için hangi koşullar aranır? Koşullar yoksa ne tür sözleşme sayılır?",
                ["TBK m.420", "TBK m.421"],
                ["objektif ve makul", "belirsiz süreli hizmet sözleşmesi"],
            ),
            (
                "TBK m.417 kapsamında işverenin işçiyi psikolojik tacizden (mobbing) koruma yükümlülüğü nedir ve bu yükümlülüğün ihlali halinde uygulanacak yaptırımlar nelerdir?",
                ["TBK m.417", "TBK m.49"],
                ["psikolojik tacizden korumak", "manevi zararlarının"],
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


class TestPreciseCrossLawDeterministicAnswers:

    @pytest.mark.parametrize(
        ("question", "expected_citations", "expected_fragments"),
        [
            (
                "Aile konutu şerhi bulunan taşınmazın satışında eşin rızası yoksa alıcının hukuki durumu hangi maddelerle değerlendirilir?",
                ["TBK m.27", "TMK m.194", "TMK m.1023"],
                ["aile konutu şerhi", "iyi niyeti"],
            ),
            (
                "TMK'da aile konutu serhi ile esin rizasinin sonuclarini maddeleriyle anlatir misin?",
                ["TMK m.194", "TMK m.1023"],
                ["aile konutu", "tapu siciline güven"],
            ),
            (
                "Evlilik birliği içinde bir eşin diğerinin rızası olmadan aile konutu üzerinde ipotek tesis etmesi mümkün müdür? Bu işlemin TBK m.27 çerçevesindeki geçersizlik sonuçları ve TMK'nın aile konutuna ilişkin güvencesi birlikte nasıl değerlendirilir?",
                ["TMK m.194", "TMK m.240", "TBK m.27"],
                ["ipotek", "aile konutu güvencesine"],
            ),
            (
                "Aile konutu şerhi tapu siciline işlenmemiş olsa bile eşin rızası aranır mı? Şerhin yokluğuna rağmen yapılan kira sözleşmesinin TBK m.27 bağlamındaki geçersizlik sonuçları ve tapu aleniyeti ilkesiyle bu koşulun bağdaşması nasıl değerlendirilir?",
                ["TMK m.194", "TMK m.1023", "TBK m.27"],
                ["tapu aleniyeti", "şerh yokluğu"],
            ),
            (
                "Boşanma davası açıldıktan sonra eşlerden biri aile konutu kira sözleşmesini feshedebilir mi? Mahkeme tedbir kararının yokluğu bu durumu değiştirir mi?",
                ["TMK m.169", "TMK m.197", "TBK m.349"],
                ["geçici önlemlerine", "tedbir kararı olmasa bile"],
            ),
        ],
    )
    def test_precise_cross_law_answers(self, question, expected_citations, expected_fragments):
        result = _build_precise_tmk_tbk_cross_law_answer(question)

        assert result is not None
        answer, citations = result
        assert citations == expected_citations
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
        include_metadata_chunk=True,
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
        include_metadata_chunk=True,
        delay_between_chunks=0,
    ):
        chunks.append(chunk)

    meta_data = json.loads(chunks[-2][6:])
    assert meta_data["object"] == "chat.completion.metadata"
    assert meta_data["trace"]["query_signals"]["user_query"] == "TBK m.49 nedir?"


@pytest.mark.asyncio
async def test_sse_stream_omits_metadata_by_default():
    chunks = []
    async for chunk in _stream_sse_response(
        answer="Test yanıtı",
        session_id="s1",
        model="test",
        citations=["TBK m.49"],
        blocked=False,
        guardrails_reasons=[],
        verification=None,
        delay_between_chunks=0,
    ):
        chunks.append(chunk)

    assert chunks[-1] == "data: [DONE]\n\n"
    assert not any("chat.completion.metadata" in chunk for chunk in chunks)


# ---------------------------------------------------------------------------
# POST /v1/chat/completions — Non-streaming Testleri
# ---------------------------------------------------------------------------


class TestChatCompletionsNonStreaming:

    def test_native_dialog_shortcut_returns_non_empty_answer(self, client, mock_orchestrator):
        mock_llm_client = MagicMock()
        mock_llm_client.chat = AsyncMock(
            return_value=LLMResult(
                text="Merhaba. Sorunu doğrudan yazabilirsin.",
                usage=TokenUsage(prompt_tokens=5, completion_tokens=6, total_tokens=11),
                trace={"native_dialog": True},
            )
        )
        mock_orchestrator.llm_client = mock_llm_client

        resp = client.post(
            "/v1/chat/completions",
            json={
                "model": "hukuk-ai-poc",
                "messages": [{"role": "user", "content": "merhaba"}],
                "stream": False,
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["choices"][0]["message"]["content"] == "Merhaba. Sorunu doğrudan yazabilirsin."
        assert data["final_mode"] == "answer"
        assert data["citations"] == []
        mock_orchestrator.answer.assert_not_called()
        mock_llm_client.chat.assert_awaited_once()

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

    def test_usage_prefers_orchestrator_usage(self, client, mock_orchestrator):
        mock_orchestrator.answer = AsyncMock(
            return_value=_make_orch_response(
                usage={"prompt_tokens": 123, "completion_tokens": 45, "total_tokens": 168}
            )
        )
        resp = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "test soru"}]},
        )
        assert resp.status_code == 200
        assert resp.json()["usage"] == {
            "prompt_tokens": 123,
            "completion_tokens": 45,
            "total_tokens": 168,
        }

    def test_chat_completions_requires_auth_when_enabled(self, mock_orchestrator, monkeypatch):
        monkeypatch.setenv("API_AUTH_ENABLED", "true")
        monkeypatch.setenv("API_AUTH_KEYS", "secret-key")
        app = _make_app(mock_orch=mock_orchestrator)
        new_store = ConversationStore()
        app.dependency_overrides[get_conversation_store] = lambda: new_store
        with TestClient(app) as c:
            resp = c.post(
                "/v1/chat/completions",
                json={"messages": [{"role": "user", "content": "soru"}]},
            )
            assert resp.status_code == 401

            ok = c.post(
                "/v1/chat/completions",
                headers={"Authorization": "Bearer secret-key"},
                json={"messages": [{"role": "user", "content": "soru"}]},
            )
            assert ok.status_code == 200
        app.dependency_overrides.clear()

    def test_chat_completion_writes_audit_event(self, client, mock_orchestrator, monkeypatch, tmp_path):
        audit_path = tmp_path / "audit.jsonl"
        monkeypatch.setenv("AUDIT_LOG_ENABLED", "true")
        monkeypatch.setenv("AUDIT_LOG_PATH", str(audit_path))
        get_metrics_registry().reset()
        mock_orchestrator.answer = AsyncMock(
            return_value=_make_orch_response(
                usage={"prompt_tokens": 12, "completion_tokens": 5, "total_tokens": 17}
            )
        )
        resp = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "test soru"}]},
        )
        assert resp.status_code == 200
        assert audit_path.exists()
        lines = audit_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        event = json.loads(lines[0])
        assert event["event_type"] == "chat_completion"
        assert event["session_id"] == resp.json()["session_id"]
        assert event["usage"] == {"prompt_tokens": 12, "completion_tokens": 5, "total_tokens": 17}
        assert event["usage_source"] == "upstream"
        assert event["auth_subject"] == "anonymous"
        metrics = get_metrics_registry().render_prometheus()
        assert 'hukuk_ai_audit_events_total 1' in metrics

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
                "include_trace": True,
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

    def test_streaming_omits_metadata_chunk_by_default(self, client, mock_orchestrator):
        mock_orchestrator.answer = AsyncMock(return_value=_make_orch_response("test"))
        resp = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "test"}],
                "stream": True,
            },
        )
        assert resp.status_code == 200
        assert "chat.completion.metadata" not in resp.text

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

    def test_source_family_bucket_retrieval_triggered_for_tuzuk_queries(self, mock_orchestrator):
        mock_retriever = MagicMock()

        from rag.retriever import RetrievalStats
        mock_stats = RetrievalStats(
            collection="test",
            query_preview="tüzük",
            top_k=20,
            filter_expr=None,
            hit_count=0,
            latency_ms=10.0,
        )
        mock_retriever.retrieve = MagicMock(return_value=([], mock_stats))
        mock_orchestrator.answer = AsyncMock(
            return_value=_make_orch_response("RAG cevabı", citations=[])
        )

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
                            "content": "Tapu kütüğü ve yardımcı siciller için hangi tüzük merkezde olmalıdır?",
                        }
                    ],
                },
            )

        assert resp.status_code == 200
        assert mock_retriever.retrieve.call_count >= 2
        assert any(
            getattr(call.kwargs.get("metadata_filter"), "belge_turu", None) == "tuzuk"
            for call in mock_retriever.retrieve.call_args_list
        )

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
        assert orch_call.kwargs["source_lock_target_citations"] == 2

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
                ([], stats),
                ([], stats),
                ([], stats),
                ([], stats),
            ]
        )
        mock_orchestrator.answer = AsyncMock(return_value=_make_orch_response("RAG cevabı"))

        app = _make_app(mock_orch=mock_orchestrator, mock_retriever=mock_retriever)
        new_store = ConversationStore()
        app.dependency_overrides[get_conversation_store] = lambda: new_store

        with patch.dict(
            os.environ,
            {
                "SOURCE_CLUSTER_SELECTOR_ENABLED": "false",
                "LEGACY_QUERY_EXPANSIONS_ENABLED": "true",
            },
            clear=False,
        ):
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
        assert mock_retriever.retrieve.call_count == 7

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
        assert orch_call.kwargs["source_lock_target_citations"] == 4

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
        assert trace["query_signals"]["predicted_family"] == "kanun"
        assert trace["query_signals"]["family_confidence"] >= 0.75
        assert trace["query_signals"]["family_candidates"][0]["family"] == "kanun"
        assert trace["query_signals"]["explicit_article_refs"] == [{"law": "TBK", "madde": "49"}]
        assert trace["query_signals"]["forced_article_refs"] == []
        assert trace["retrieval"]["top_k_requested"] == 20
        assert trace["retrieval"]["top_k_effective"] == 20
        assert trace["retrieval"]["pre_rerank_chunks"][0]["source_id"] == "tbk-49-f1"
        assert trace["context_assembly"]["context_chunk_citations"] == ["TBK m.49"]
        assert "Haksız fiil metni" in trace["context_assembly"]["assembled_context"]
        assert trace["context_assembly"]["assembled_evidence"][0]["source_id"] == "tbk-49-f1"
        assert trace["context_assembly"]["assembled_evidence"][0]["excerpt"] == "Haksız fiil metni"
        assert trace["context_assembly"]["allowed_source_whitelist"] == ["tbk-49-f1"]
        assert trace["generation_outcome"]["verification"]["verdict"] == "pass"
        assert resp.json()["final_mode"] == "answer"
        assert resp.json()["answer_contract"]["primary_source_id"] == "TBK m.49"

    def test_single_law_scope_mismatch_returns_blocked_refusal(self, mock_orchestrator):
        mock_retriever = MagicMock()

        from rag.retriever import RetrievalResult, RetrievalStats

        results = [
            RetrievalResult(
                chunk_id="tmk-194",
                text="Aile konutu metni",
                score=0.9,
                metadata={
                    "source_id": "TMK m.194",
                    "law_short_name": "TMK",
                    "madde_no": "194",
                    "fikra_no": "1",
                },
            )
        ]
        stats = RetrievalStats(
            collection="test",
            query_preview="tbk",
            top_k=20,
            filter_expr=None,
            hit_count=1,
            latency_ms=10.0,
        )
        mock_retriever.retrieve = MagicMock(return_value=(results, stats))
        mock_orchestrator.answer = AsyncMock(
            return_value=_make_orch_response(
                "Aile konutu koruması vardır [Kaynak: TMK m.194]",
                citations=["TMK m.194"],
                verification={"verdict": "pass"},
            )
        )

        app = _make_app(mock_orch=mock_orchestrator, mock_retriever=mock_retriever)
        new_store = ConversationStore()
        app.dependency_overrides[get_conversation_store] = lambda: new_store

        with TestClient(app) as c:
            resp = c.post(
                "/v1/chat/completions",
                json={"messages": [{"role": "user", "content": "TBK m.349 nedir?"}], "include_trace": True},
            )

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["blocked"] is False
        assert payload["final_mode"] == "refusal"
        assert payload["final_reason"] == "law_scope_mismatch"
        assert payload["citations"] == []
        assert payload["answer_contract"]["unsupported_reason"] == "law_scope_mismatch"
        assert payload["answer_contract"]["final_mode"] == "refusal"
        assert payload["trace"]["final_mode"] == "refusal"
        assert payload["trace"]["answer_contract"]["final_mode"] == "refusal"

    def test_serialization_whitelist_violation_returns_blocked_refusal(self, mock_orchestrator):
        mock_retriever = MagicMock()

        from rag.retriever import RetrievalResult, RetrievalStats

        results = [
            RetrievalResult(
                chunk_id="tbk-49",
                text="Haksız fiil metni",
                score=0.9,
                metadata={
                    "source_id": "TBK m.49",
                    "law_short_name": "TBK",
                    "madde_no": "49",
                    "fikra_no": "1",
                },
            )
        ]
        stats = RetrievalStats(
            collection="test",
            query_preview="tbk",
            top_k=20,
            filter_expr=None,
            hit_count=1,
            latency_ms=10.0,
        )
        mock_retriever.retrieve = MagicMock(return_value=(results, stats))
        mock_orchestrator.answer = AsyncMock(
            return_value=_make_orch_response(
                "Yanlış atıf [Kaynak: TBK m.50]",
                citations=["TBK m.50"],
                verification={"verdict": "pass"},
            )
        )

        app = _make_app(mock_orch=mock_orchestrator, mock_retriever=mock_retriever)
        new_store = ConversationStore()
        app.dependency_overrides[get_conversation_store] = lambda: new_store

        with TestClient(app) as c:
            resp = c.post(
                "/v1/chat/completions",
                json={"messages": [{"role": "user", "content": "TBK m.49 nedir?"}]},
            )

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["blocked"] is True
        assert payload["final_mode"] == "refusal"
        assert payload["final_reason"] == "citation_out_of_whitelist"
        assert payload["citations"] == []
        assert payload["answer_contract"]["unsupported_reason"] == "citation_out_of_whitelist"
        assert payload["answer_contract"]["final_mode"] == "refusal"

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

        with patch.dict(os.environ, {"LEGACY_QUERY_EXPANSIONS_ENABLED": "true"}, clear=False):
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

    def test_death_regime_query_does_not_pull_interspousal_loan_refs(
        self,
        mock_orchestrator,
    ):
        mock_retriever = MagicMock()

        from rag.retriever import RetrievalResult, RetrievalStats

        semantic_results = [
            RetrievalResult(
                chunk_id="tmk-226",
                text="Sağ kalan eşin katılma alacağı tasfiyede dikkate alınır.",
                score=0.93,
                metadata={"law_short_name": "TMK", "madde_no": "226", "fikra_no": "1"},
            )
        ]
        stats = RetrievalStats(
            collection="test",
            query_preview="hayatta kalan eş",
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

        with patch.dict(os.environ, {"LEGACY_QUERY_EXPANSIONS_ENABLED": "true"}, clear=False):
            with TestClient(app) as c:
                resp = c.post(
                    "/v1/chat/completions",
                    json={
                        "messages": [
                            {
                                "role": "user",
                                "content": (
                                    "Eşlerden birinin ölümü halinde hayatta kalan eşin edinilmiş "
                                    "mallara katılma rejimi çerçevesinde borçlara karşı kişisel "
                                    "sorumluluğu nasıl belirlenir? Ölen eşin alacaklısı, TBK m.77 "
                                    "kapsamında sebepsiz zenginleşme iddiasıyla hayatta kalan eşin "
                                    "elde ettiği katılma alacağına başvurabilir mi?"
                                ),
                            }
                        ],
                        "include_trace": True,
                    },
                )

        assert resp.status_code == 200
        orch_call = mock_orchestrator.answer.call_args
        assert orch_call.kwargs["source_lock_target_citations"] == 4

        trace = resp.json()["trace"]
        assert trace["query_signals"]["forced_article_refs"] == [
            {"law": "TBK", "madde": "77"},
            {"law": "TMK", "madde": "226"},
            {"law": "TMK", "madde": "240"},
            {"law": "TMK", "madde": "499"},
        ]
        assert trace["query_signals"]["applied_expansions"] == [
            "TBK m.77 TMK m.226 TMK m.240 TMK m.499 hayatta kalan eş katılma alacağı sebepsiz zenginleşme"
        ]

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
