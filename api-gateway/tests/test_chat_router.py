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
    _apply_answer_slot_synthesis_hint,
    _apply_retrieval_plan_hints,
    _apply_metadata_lookup_family_prior,
    _apply_relation_query_metadata_focus,
    _apply_pre_generation_family_pool,
    _apply_selected_document_only_bundle,
    _annotate_canonical_span_materialization,
    _build_assembled_evidence,
    _build_annual_investment_program_expansion,
    _build_numbered_law_reference_expansion,
    _build_completeness_synthesis_features,
    _build_retrieval_verification_features,
    _build_retrieval_plan_expansion,
    _build_metadata_first_query_expansion,
    _build_source_cluster_candidates,
    _metadata_lookup_has_strong_query_anchor,
    _parse_metadata_lookup_query_signals,
    _annotate_recall_lane_chunks,
    _dedupe_retrieved_chunks,
    _extract_effective_legal_query,
    _retrieve_source_key_chunks,
    _select_metadata_first_source_candidates,
    _select_article_span_evidence,
    _clamp_families_to_strong_resolution,
    _build_precise_tmk_tbk_cross_law_answer,
    _contains_query_term,
    _extract_json_object,
    _extract_explicit_article_refs,
    _extract_law_mentions,
    _extract_source_identifier_tokens,
    _focus_chunks_on_selected_sources,
    _infer_requested_source_families,
    _prioritize_chunks_for_source_families,
    _rerank_chunks_by_source_identity,
    _resolve_chunk_source_family,
    _resolve_chunk_source_family_profile,
    _resolve_chunk_routing_family,
    _resolve_chunk_canonical_source_key_v2,
    _resolve_source_family_prior,
    _source_key_v2_collision_profile,
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
from rag.source_catalog import load_canonical_source_catalog
from rag.retriever import MetadataFilter, MockRetriever
from session_store import RedisSessionBackend
from source_family_resolver import SourceFamilyCandidate, SourceFamilyResolution


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

    def test_source_family_prior_exports_phase9_trace_policy(self):
        resolution = _resolve_source_family_prior(
            "Karar Sayısı: 3350 olan İthalat Rejimi Kararı hangi belge ailesindedir?"
        )
        trace = resolution.to_trace_dict()

        assert trace["expected_family_prior"] == "cb_karar"
        assert trace["preferred_families"] == ["cb_karar"]
        assert trace["selected_family_confidence"] >= 0.75
        assert trace["family_override_reason"] == "strong_family_prior"

    def test_retrieval_verification_features_export_phase9_family_pool_fields(self):
        resolution = _resolve_source_family_prior(
            "Karar Sayısı: 3350 olan İthalat Rejimi Kararı hangi belge ailesindedir?"
        )
        chunks = [
            RetrievedChunk(
                text="İthalat Rejimi Kararı madde metni",
                citation="3350 m.1",
                source="3350",
                score=1.0,
                metadata={
                    "belge_turu": "cb_karar",
                    "belge_adi": "İTHALAT REJİMİ KARARI",
                    "belge_no": "3350",
                    "madde_no": "1",
                },
            )
        ]

        features = _build_retrieval_verification_features(
            query="Karar Sayısı: 3350 olan İthalat Rejimi Kararı hangi belge ailesindedir?",
            requested_source_families=["cb_karar"],
            source_family_resolution=resolution.to_trace_dict(),
            chunks=chunks,
        )

        assert features["expected_family_prior"] == "cb_karar"
        assert features["preferred_family_pool_size"] == 1
        assert features["cross_family_fallback_used"] is False
        assert features["family_override_reason"] == "strong_family_prior"

    def test_retrieval_verification_features_export_current_law_scenario_flags(self):
        resolution = _resolve_source_family_prior(
            "İşveren performans gerekçesiyle işçiyi işten çıkarırsa işe iade davası açılabilir mi?"
        )
        chunks = [
            RetrievedChunk(
                text="Geçersiz nedenle fesih halinde işçi işe iade talep edebilir.",
                citation="4857 m.21/f.0",
                source="4857",
                score=1.0,
                metadata={
                    "belge_turu": "kanun",
                    "belge_adi": "İŞ KANUNU",
                    "belge_no": "4857",
                    "madde_no": "21",
                    "effective_state": "active",
                },
            )
        ]

        features = _build_retrieval_verification_features(
            query="İşveren performans gerekçesiyle işçiyi işten çıkarırsa işe iade davası açılabilir mi?",
            requested_source_families=["kanun"],
            source_family_resolution=resolution.to_trace_dict(),
            chunks=chunks,
        )

        assert features["scenario_current_law_question"] is True
        assert features["scenario_current_law_prior"] is True
        assert features["historical_or_repealed_question"] is False

    def test_retrieval_verification_features_export_historical_and_collision_flags(self):
        resolution = _resolve_source_family_prior(
            "1475 sayılı mülga İş Kanunu ile 2026'da doğrudan hüküm kurmak neden risklidir?"
        )

        features = _build_retrieval_verification_features(
            query="1475 sayılı mülga İş Kanunu ile 2026'da doğrudan hüküm kurmak neden risklidir?",
            requested_source_families=["mulga_kanun"],
            source_family_resolution=resolution.to_trace_dict(),
            chunks=[],
        )

        assert features["historical_scope_detected"] is True
        assert features["repealed_scope_detected"] is True
        assert features["current_law_prior_blocked_by_historical_scope"] is True
        assert features["family_collision_detected"] is True
        assert features["family_collision_pair"] == "kanun|mulga_kanun"

    def test_completeness_synthesis_flags_short_complex_answer(self):
        features = _build_completeness_synthesis_features(
            query="Başvuru usulü ve süresi nedir?",
            answer_text="Başvuru yapılır [Kaynak: X m.1].",
            article_span_selector={"support_span_count": 1},
            chunks=[
                RetrievedChunk(
                    text="Başvuru usulü ve süre koşulları.",
                    citation="X m.1",
                    source="X",
                    score=1.0,
                    metadata={},
                )
            ],
        )

        assert features["task_type_answer_template_used"] == "procedure"
        assert features["minimum_answer_facts_present"] is False
        assert features["completeness_degrade_reason"] == "answer_too_short_for_template"
        assert "procedure_or_consequence" in features["must_have_fact_slots"]
        assert features["rubric_aligned_completeness_class"] == "insufficient_both"

    def test_completeness_synthesis_accepts_multi_fact_grounded_answer(self):
        features = _build_completeness_synthesis_features(
            query="Hangi hallerde başvuru yapılır, istisnası var mı?",
            answer_text=(
                "Başvuru, kaynakta sayılan şartlar gerçekleşirse yapılır [Kaynak: X m.1]. "
                "İkinci olarak süre şartına uyulmalıdır [Kaynak: X m.2]. "
                "İstisna kaynağın saklı tuttuğu hallerle sınırlıdır [Kaynak: X m.3]."
            ),
            article_span_selector={"support_span_count": 3},
            chunks=[
                RetrievedChunk(text="Şart", citation="X m.1", source="X", score=1.0, metadata={}),
                RetrievedChunk(text="Süre", citation="X m.2", source="X", score=1.0, metadata={}),
                RetrievedChunk(text="İstisna", citation="X m.3", source="X", score=1.0, metadata={}),
            ],
        )

        assert features["task_type_answer_template_used"] == "procedure"
        assert features["minimum_answer_facts_present"] is True
        assert features["required_fact_coverage_score"] == 1.0
        assert features["missing_fact_slots"] == []
        assert features["rubric_aligned_completeness_class"] == "rubric_sufficient"
        slot_map = {
            item["answer_slot"]: item
            for item in features["answer_slot_evidence_map"]
        }
        assert slot_map["procedure_or_consequence"]["evidence_span_id"] == "X m.2"
        assert slot_map["exception_or_limitation"]["evidence_span_id"] == "X m.3"
        assert features["answer_slot_coverage_score"] > 0.70

    def test_answer_slot_synthesis_hint_names_required_slots_and_selector_state(self):
        hinted = _apply_answer_slot_synthesis_hint(
            query="Başvuru usulü ve süresi nedir?",
            routing_query="Başvuru usulü ve süresi nedir?",
            article_span_selector={
                "selected_article": "7",
                "support_span_count": 2,
                "selector_evidence_sufficiency": "partially_supported",
            },
        )

        assert "[KANIT-CEVAP SLOT TALİMATI]" in hinted
        assert "procedure_or_consequence" in hinted
        assert "Secili madde/span: 7" in hinted
        assert "Destek span sayisi: 2" in hinted

    def test_answer_slot_synthesis_hint_adds_mulga_temporal_instruction(self):
        hinted = _apply_answer_slot_synthesis_hint(
            query="Mülga kanun bugün doğrudan uygulanabilir mi?",
            routing_query="Mülga kanun bugün doğrudan uygulanabilir mi?",
            article_span_selector={
                "selected_article": "3",
                "support_span_count": 1,
                "selector_evidence_sufficiency": "partially_supported",
            },
            requested_source_families=["mulga_kanun"],
            source_family_resolution={
                "predicted_family": "mulga_kanun",
                "historical_or_repealed_question": True,
                "repealed_scope_detected": True,
            },
        )

        assert "[MULGA/TARIHSEL CEVAP TALIMATI]" in hinted
        assert "cevabi bugunku aktif hukuk gibi kurma" in hinted
        assert "bugun dogrudan uygulanip uygulanamayacagini" in hinted

    def test_answer_slot_synthesis_hint_detects_historical_year_risk_question(self):
        hinted = _apply_answer_slot_synthesis_hint(
            query="1988 tarihli yönetmeliği esas almak neden hatalıdır?",
            routing_query="1988 tarihli yönetmeliği esas almak neden hatalıdır?",
            article_span_selector={"support_span_count": 1},
        )

        assert "[MULGA/TARIHSEL CEVAP TALIMATI]" in hinted
        assert "temporal_validity" in hinted

    def test_completeness_synthesis_gates_missing_temporal_slot(self):
        features = _build_completeness_synthesis_features(
            query="Bu düzenleme halen yürürlükte mi, güncel durum nedir?",
            answer_text=(
                "Düzenleme kaynakta yer alan kurala dayanır [Kaynak: X m.1]. "
                "Uygulanacak sonuç kaynak kapsamıyla sınırlıdır [Kaynak: X m.1]."
            ),
            article_span_selector={"support_span_count": 2},
            chunks=[RetrievedChunk(text="Kural", citation="X m.1", source="X", score=1.0, metadata={})],
        )

        assert features["minimum_answer_facts_present"] is False
        assert "temporal_validity" in features["missing_fact_slots"]
        assert features["completeness_degrade_reason"].startswith("missing_required_fact_slots:")

    def test_completeness_synthesis_accepts_citation_backed_chunks_without_selector_spans(self):
        features = _build_completeness_synthesis_features(
            query="Bu düzenleme ne sonuç doğurur?",
            answer_text=(
                "Düzenleme ilgili işlem bakımından uygulanacak sonucu belirler [Kaynak: X m.1]. "
                "Dayanak metin, bu sonucun kapsamını ayrıca sınırlar [Kaynak: X m.2]."
            ),
            article_span_selector={"support_span_count": 0},
            chunks=[
                RetrievedChunk(text="Sonuç", citation="X m.1", source="X", score=1.0, metadata={}),
                RetrievedChunk(text="Kapsam", citation="X m.2", source="X", score=1.0, metadata={}),
            ],
        )

        assert features["minimum_answer_facts_present"] is True
        assert features["missing_fact_slots"] == []
        assert features["completeness_degrade_reason"] == "complete_enough"

    def test_completeness_synthesis_reenters_evidence_slots_when_selector_identity_is_strong(self):
        features = _build_completeness_synthesis_features(
            query="Başvuru usulü ve süresi nedir?",
            answer_text=(
                "Kaynakta belirtilen birinci kural uygulanır [Kaynak: X m.1]. "
                "İkinci kural kapsamı belirler [Kaynak: X m.2]. "
                "Üçüncü kural dayanak oluşturur [Kaynak: X m.3]."
            ),
            article_span_selector={
                "support_span_count": 2,
                "metadata_identity_strength": "strong",
                "selector_evidence_sufficiency": "partially_supported",
            },
            chunks=[
                RetrievedChunk(text="Başvuru usulü ve süre koşulları düzenlenir.", citation="X m.1", source="X", score=1.0, metadata={}),
                RetrievedChunk(text="Başvuruda bildirim ve işlem adımları gösterilir.", citation="X m.2", source="X", score=1.0, metadata={}),
            ],
        )

        assert "procedure_or_consequence" in features["satisfied_fact_slots"]
        assert features["evidence_slot_reentry_applied"] is True
        assert features["evidence_slot_reentry_slots"] == ["procedure_or_consequence"]
        assert features["completeness_degrade_reason"] == "complete_enough"
        slot_map = {
            item["answer_slot"]: item
            for item in features["answer_slot_evidence_map"]
        }
        assert slot_map["procedure_or_consequence"]["slot_confidence"] == 0.65
        assert slot_map["procedure_or_consequence"]["slot_missing_reason"] == "evidence_reentry_support"

    def test_completeness_synthesis_does_not_reenter_slots_when_selector_identity_is_weak(self):
        features = _build_completeness_synthesis_features(
            query="Başvuru usulü ve süresi nedir?",
            answer_text=(
                "Kaynakta belirtilen birinci kural uygulanır [Kaynak: X m.1]. "
                "İkinci kural kapsamı belirler [Kaynak: X m.2]. "
                "Üçüncü kural dayanak oluşturur [Kaynak: X m.3]."
            ),
            article_span_selector={
                "support_span_count": 2,
                "metadata_identity_strength": "none",
                "selector_evidence_sufficiency": "insufficient_support",
            },
            chunks=[
                RetrievedChunk(text="Başvuru usulü ve süre koşulları düzenlenir.", citation="X m.1", source="X", score=1.0, metadata={}),
            ],
        )

        assert "procedure_or_consequence" in features["missing_fact_slots"]
        assert features["evidence_slot_reentry_applied"] is False

    def test_completeness_synthesis_degrades_insufficient_canonical_span_evidence(self):
        features = _build_completeness_synthesis_features(
            query="9903 sayılı karar kapsamında faiz desteği şartı nedir?",
            answer_text=(
                "Karar, yatırım teşvik şartları bakımından uygulanır [Kaynak: 9903 m.0]. "
                "Uygulama kaynak metindeki sınırlara göre değerlendirilir [Kaynak: 9903 m.0]. "
                "Sonuç bakımından özel koşullar ayrıca kontrol edilir [Kaynak: 9903 m.0]."
            ),
            article_span_selector={
                "support_span_count": 1,
                "metadata_identity_strength": "strong",
                "selector_evidence_sufficiency": "partially_supported",
                "candidate_completeness_score": 0.2,
                "selected_document_has_body_span": False,
                "selected_document_has_non_title_span": False,
                "title_only_answer_degraded": True,
                "insufficient_canonical_span_evidence": True,
            },
            chunks=[
                RetrievedChunk(
                    text="9903 m.0\n" + ("\x00" * 80),
                    citation="9903 m.0/f.0",
                    source="9903",
                    score=1.0,
                    metadata={"belge_turu": "cb_karar", "belge_no": "9903", "madde_no": "0"},
                )
            ],
        )

        assert features["minimum_answer_facts_present"] is False
        assert features["completeness_degrade_reason"] == "insufficient_canonical_span_evidence"
        assert features["rubric_aligned_completeness_class"] == "legally_aligned_but_partial"
        assert features["candidate_completeness_score"] == 0.2
        assert features["selected_document_has_non_title_span"] is False

    def test_source_family_prior_does_not_treat_tebligat_as_teblig(self):
        resolution = _resolve_source_family_prior(
            "Elektronik tebligat yönetmeliği kapsamında muhatabın bildirim yükümlülüğü nedir?"
        )

        assert resolution.predicted_family == "yonetmelik"
        assert "teblig" not in resolution.routing_families

    def test_source_family_prior_detects_legal_teblig_but_not_tebligat(self):
        resolution = _resolve_source_family_prior(
            "Vergi Usul Kanunu Genel Tebliği (Sıra No: 431) hangi usulü getiriyor?"
        )

        assert resolution.predicted_family == "teblig"
        assert "teblig" in resolution.routing_families

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

    def test_source_family_prior_detects_cb_genelge_specific_terms(self):
        resolution = _resolve_source_family_prior(
            "Tasarruf Genelgesi kapsamında kamu idaresinin harcama kısıtları nasıl uygulanır?"
        )

        assert resolution.predicted_family == "cb_genelge"
        assert resolution.family_confidence >= 0.75
        assert resolution.preferred_families == ["cb_genelge"]

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

    def test_source_family_prior_uses_current_law_scenario_fallback_for_natural_language_query(self):
        resolution = _resolve_source_family_prior(
            "İşveren performans gerekçesiyle işçiyi işten çıkarırsa işe iade davası açılabilir mi?"
        )

        assert resolution.predicted_family == "kanun"
        assert resolution.preferred_families == ["kanun"]
        assert "kanun" in resolution.routing_families
        assert "yonetmelik" in resolution.routing_families
        assert resolution.scenario_current_law_question is True
        assert resolution.scenario_current_law_prior is True
        assert resolution.historical_or_repealed_question is False
        assert resolution.family_override_reason == "scenario_current_law_prior"

    def test_source_family_prior_blocks_current_law_fallback_when_historical_scope_is_explicit(self):
        resolution = _resolve_source_family_prior(
            "1475 sayılı mülga İş Kanunu ile 2026'da doğrudan hüküm kurmak neden risklidir?"
        )

        assert resolution.scenario_current_law_question is False
        assert resolution.scenario_current_law_prior is False
        assert resolution.historical_scope_detected is True
        assert resolution.repealed_scope_detected is True
        assert resolution.current_law_prior_blocked_by_historical_scope is True
        assert resolution.predicted_family == "mulga_kanun"
        assert resolution.family_collision_detected is True
        assert resolution.family_collision_pair == "kanun|mulga_kanun"

    def test_source_family_prior_detects_old_year_historical_scope_for_legacy_tuzuk_query(self):
        resolution = _resolve_source_family_prior(
            "Tapu işlemlerinde 1994 tarihli Tapu Sicili Tüzüğünü kullanmak neden doğrudan hata üretir?"
        )

        assert resolution.historical_scope_detected is True
        assert resolution.current_law_prior_blocked_by_historical_scope is False
        assert resolution.predicted_family == "mulga_kanun"
        assert resolution.family_collision_pair == "tuzuk|mulga_kanun"

    def test_source_family_prior_prefers_mulga_for_still_relying_on_old_regulation_risk(self):
        resolution = _resolve_source_family_prior(
            "Yükseköğretim öğrencisine disiplin cezası verilirken hâlâ eski yönetmeliğe dayanmak güvenli midir?"
        )

        assert resolution.historical_scope_detected is True
        assert resolution.predicted_family == "mulga_kanun"
        assert "legacy_source_risk_signal" in resolution.family_candidates[0].signals

    def test_source_family_prior_prefers_kanun_when_teblig_is_passive_verb_and_query_names_kanun_yonetmelik(self):
        resolution = _resolve_source_family_prior(
            "Elektronik tebligat muhatabın elektronik adresine ulaştığı anda mı, yoksa daha sonraki bir tarihte mi tebliğ edilmiş sayılır? Kanun ve yönetmelik ilişkisini de göster."
        )

        assert resolution.predicted_family == "kanun"
        assert resolution.preferred_families == ["kanun"]
        assert "yonetmelik" in resolution.routing_families
        assert resolution.family_collision_detected is True
        assert resolution.family_collision_pair == "kanun|yonetmelik"

    def test_source_family_prior_prefers_yonetmelik_for_yonetmelik_duzeyinde_tebligat_question(self):
        resolution = _resolve_source_family_prior(
            "Elektronik tebligatın hangi tarihte tebliğ edilmiş sayılacağını yönetmelik düzeyinde açıkla."
        )

        assert resolution.predicted_family == "yonetmelik"
        assert resolution.preferred_families == ["yonetmelik"]
        assert resolution.family_collision_detected is False

    def test_source_family_prior_resolves_cb_yonetmelik_vs_cb_genelge_public_admin_collision(self):
        resolution = _resolve_source_family_prior(
            "Kamu kurumunun personel servis hizmeti kurması veya kiralama yoluyla yürütmesi sorusunda hangi CB/BK yönetmeliği ve hangi güncel tasarruf genelgesi birlikte kontrol edilmelidir?"
        )

        assert resolution.predicted_family == "cb_yonetmelik"
        assert resolution.preferred_families == ["cb_yonetmelik"]
        assert "cb_genelge" in resolution.fallback_families
        assert resolution.family_collision_detected is True
        assert resolution.family_collision_pair == "cb_genelge|cb_yonetmelik"
        assert resolution.collision_resolution_reason == "public_administration_prefers_cb_yonetmelik"

    def test_source_family_prior_prefers_cb_karar_for_gtip_change_decision_query(self):
        resolution = _resolve_source_family_prior(
            "2026'da belirli bir GTİP için ithalat vergisi veya ek mali yükümlülük soruluyor. Hangi ana karar ve değişiklik kararları takip edilmelidir?"
        )

        assert resolution.predicted_family == "cb_karar"
        assert resolution.preferred_families == ["cb_karar"]
        assert resolution.family_collision_detected is True
        assert resolution.family_collision_pair == "cb_karar|yonetmelik"

    def test_source_family_prior_prefers_cb_karar_for_decision_vs_genelge_relation_query(self):
        resolution = _resolve_source_family_prior(
            "2026 Yılı Kamu Yatırım Programında yer almayan bir proje için ihale yapılabilir mi? "
            "Soruyu hangi karar üzerinden cevaplayıp hangi uygulama genelgesine bakarsın?"
        )

        assert resolution.predicted_family == "cb_karar"
        assert resolution.preferred_families == ["cb_karar"]
        assert "cb_genelge" in resolution.fallback_families
        assert resolution.family_collision_detected is True
        assert resolution.family_collision_pair == "cb_genelge|cb_karar"
        assert resolution.collision_resolution_reason == "cb_karar_relation_prefers_primary_decision"

    def test_source_family_prior_prefers_khk_for_transition_relation_query(self):
        resolution = _resolve_source_family_prior(
            "Mevzuat hâlâ Bakanlar Kurulu veya eski teşkilat isimlerine atıf yapıyorsa, "
            "Cumhurbaşkanlığı Hükümet Sistemine geçiş bakımından hangi KHK ve hangi CBK bağlantısı kontrol edilmelidir?"
        )

        assert resolution.predicted_family == "khk"
        assert resolution.preferred_families == ["khk"]
        assert "cb_kararname" in resolution.fallback_families
        assert resolution.family_collision_detected is True
        assert resolution.family_collision_pair == "khk|cb_kararname"
        assert resolution.collision_resolution_reason == "khk_cbk_transition_prefers_khk"

    def test_source_family_prior_does_not_treat_sector_license_terms_as_university_signal(self):
        resolution = _resolve_source_family_prior(
            "Elektrik piyasasında önlisans/lisans başvurusu ve lisans sahibinin hak-yükümlülükleri sorusunda "
            "hangi kurum yönetmeliği ana eksendir?"
        )

        assert resolution.predicted_family == "yonetmelik"
        assert "uy" not in [candidate.family for candidate in resolution.family_candidates]

    def test_source_family_prior_prefers_kky_for_rtuk_broadcast_license_query(self):
        resolution = _resolve_source_family_prior(
            "Bir platform internet üzerinden isteğe bağlı yayın hizmeti sunmak istiyor. "
            "İnternet yayın lisansı ve iletim yetkisi bakımından hangi RTÜK yönetmeliği aranmalı?"
        )

        assert resolution.predicted_family == "kky"
        assert resolution.preferred_families == ["kky"]

    def test_pre_generation_family_pool_locks_strong_preferred_family(self):
        resolution = _resolve_source_family_prior(
            "Karar Sayısı: 3350 olan İthalat Rejimi Kararı hangi belge ailesindedir?"
        )
        chunks = [
            RetrievedChunk(
                text="Yönetmelik parçası",
                citation="Yönetmelik m.1",
                source="Yönetmelik",
                score=2.0,
                metadata={"belge_turu": "yonetmelik", "belge_adi": "GENEL YÖNETMELİK"},
            ),
            RetrievedChunk(
                text="İthalat Rejimi Kararı parçası",
                citation="3350 m.1",
                source="3350",
                score=1.0,
                metadata={"belge_turu": "cb_karar", "belge_adi": "İTHALAT REJİMİ KARARI"},
            ),
        ]

        filtered, policy = _apply_pre_generation_family_pool(
            chunks=chunks,
            source_family_resolution=resolution,
            top_k_effective=10,
        )

        assert [chunk.metadata["belge_turu"] for chunk in filtered] == ["cb_karar"]
        assert policy["preferred_family_pool_size"] == 1
        assert policy["cross_family_fallback_used"] is False
        assert policy["family_override_reason"] == "strong_preferred_family_pool"
        assert policy["family_gate_status"] == "locked_preferred_family"
        assert policy["pre_filter_family_set"] == ["yonetmelik", "cb_karar"]
        assert policy["reranked_family_set"] == ["cb_karar"]
        assert policy["selected_family_source"] == "cb_karar"

    def test_pre_generation_family_pool_blocks_cross_family_for_hard_family(self):
        resolution = _resolve_source_family_prior(
            "Devlet Arşivleri yönetmeliği kapsamında saklama yükümlülüğü nedir?"
        )
        chunks = [
            RetrievedChunk(
                text="Genel yönetmelik parçası",
                citation="Yönetmelik m.1",
                source="Yönetmelik",
                score=1.0,
                metadata={"belge_turu": "yonetmelik", "belge_adi": "ARŞİV HİZMETLERİ YÖNETMELİĞİ"},
            )
        ]

        filtered, policy = _apply_pre_generation_family_pool(
            chunks=chunks,
            source_family_resolution=resolution,
            top_k_effective=10,
        )

        assert filtered == []
        assert policy["preferred_family_pool_size"] == 0
        assert policy["cross_family_fallback_used"] is False
        assert policy["family_override_reason"] == "hard_family_gate_no_preferred_candidates"
        assert policy["family_gate_status"] == "hard_gate_no_preferred_candidates"

    def test_pre_generation_family_pool_honors_policy_preferred_family_at_070(self):
        resolution = SourceFamilyResolution(
            predicted_family="yonetmelik",
            family_confidence=0.70,
            routing_families=["yonetmelik"],
            expected_family_prior="yonetmelik",
            preferred_families=["yonetmelik"],
            selected_family_confidence=0.70,
            family_override_reason="strong_family_prior",
        )
        chunks = [
            RetrievedChunk(
                text="Kanun parçası",
                citation="6502 m.1",
                source="6502",
                score=2.0,
                metadata={"source_family_canonical": "kanun", "source_title": "TÜKETİCİNİN KORUNMASI HAKKINDA KANUN"},
            ),
            RetrievedChunk(
                text="Yönetmelik parçası",
                citation="20237 m.1",
                source="20237",
                score=1.0,
                metadata={"source_family_canonical": "yonetmelik", "source_title": "MESAFELİ SÖZLEŞMELER YÖNETMELİĞİ"},
            ),
        ]

        filtered, policy = _apply_pre_generation_family_pool(
            chunks=chunks,
            source_family_resolution=resolution,
            top_k_effective=10,
        )

        assert [chunk.citation for chunk in filtered] == ["20237 m.1"]
        assert policy["family_gate_status"] == "locked_preferred_family"
        assert policy["no_gate_reason"] == ""

    def test_pre_generation_family_pool_reports_source_key_collision_before_family_lock(self):
        resolution = SourceFamilyResolution(
            predicted_family="cb_karar",
            family_confidence=0.90,
            routing_families=["cb_karar"],
            expected_family_prior="cb_karar",
            preferred_families=["cb_karar"],
            selected_family_confidence=0.90,
            family_override_reason="strong_family_prior",
        )
        chunks = [
            RetrievedChunk(
                text="9903 m.0\n" + ("\x00" * 80),
                citation="9903 m.0/f.0",
                source="9903",
                score=1.0,
                metadata={
                    "belge_turu": "cb_karar",
                    "belge_no": "9903",
                    "source_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR",
                    "madde_no": "0",
                },
            ),
            RetrievedChunk(
                text="Garanti belgesi süreleri tebliğ madde metni seçilebilir durumdadır.",
                citation="9903 m.1/f.0",
                source="9903",
                score=0.9,
                metadata={
                    "belge_turu": "teblig",
                    "belge_no": "9903",
                    "source_title": "GARANTİ BELGESİ SÜRELERİNİN UZATILMASINA İLİŞKİN TEBLİĞ",
                    "madde_no": "1",
                },
            ),
        ]

        filtered, policy = _apply_pre_generation_family_pool(
            chunks=chunks,
            source_family_resolution=resolution,
            top_k_effective=10,
        )

        assert [chunk.metadata["belge_turu"] for chunk in filtered] == ["cb_karar"]
        assert policy["source_key_collision_detected"] is True
        assert policy["source_key_collision_keys"] == ["9903"]
        assert "cb_karar" in policy["source_key_collision_pair"]
        assert "teblig" in policy["source_key_collision_pair"]

    def test_canonical_source_key_v2_separates_numeric_cross_family_collision(self):
        karar_chunk = RetrievedChunk(
            text="Yatırımlarda devlet yardımları kararı metni.",
            citation="9903 m.0/f.0",
            source="9903",
            score=1.0,
            metadata={
                "belge_turu": "cb_karar",
                "belge_no": "9903",
                "source_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR",
                "madde_no": "0",
            },
        )
        teblig_chunk = RetrievedChunk(
            text="Garanti belgesi süreleri tebliğ metni.",
            citation="9903 m.1/f.0",
            source="9903",
            score=0.9,
            metadata={
                "belge_turu": "teblig",
                "belge_no": "9903",
                "source_title": "GARANTİ BELGESİ SÜRELERİNİN UZATILMASINA İLİŞKİN TEBLİĞ",
                "madde_no": "1",
            },
        )

        karar_key = _resolve_chunk_canonical_source_key_v2(karar_chunk, include_span=False)
        teblig_key = _resolve_chunk_canonical_source_key_v2(teblig_chunk, include_span=False)
        v2_profile = _source_key_v2_collision_profile([karar_chunk, teblig_chunk])

        assert "fam=cb_karar" in karar_key
        assert "fam=teblig" in teblig_key
        assert "id=9903" in karar_key
        assert "id=9903" in teblig_key
        assert karar_key != teblig_key
        assert v2_profile["source_key_v2_collision_detected"] is False

    def test_article_span_selector_writes_legacy_and_canonical_source_keys(self):
        chunk = RetrievedChunk(
            text="Yatırım teşvik başvurusu için karar kapsamındaki destek unsurları düzenlenir.",
            citation="9903 m.1/f.0",
            source="9903",
            score=1.0,
            metadata={
                "belge_turu": "cb_karar",
                "belge_no": "9903",
                "source_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR",
                "madde_no": "1",
            },
        )

        _chunks, selector = _select_article_span_evidence(
            query="9903 sayılı Cumhurbaşkanı Kararı yatırım teşvik başvurusu ne der?",
            chunks=[chunk],
            requested_source_families=["cb_karar"],
        )

        assert selector["legacy_source_key"] == "9903"
        assert selector["selected_canonical_source_key_v2"].startswith("fam=cb_karar|id=9903")
        assert selector["top_scores"][0]["legacy_source_key"] == "9903"
        assert selector["top_scores"][0]["canonical_source_key_v2"].startswith("fam=cb_karar|id=9903")

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

    def test_chunk_source_family_prefers_canonical_family_for_university_regulation(self):
        chunk = RetrievedChunk(
            text="Üniversite yönetmeliği parçası.",
            citation="31299 m.1/f.0",
            source="31299",
            score=0.9,
            metadata={
                "source_family_canonical": "uy",
                "source_title": "IŞIK ÜNİVERSİTESİ YATAY GEÇİŞ, ÇİFT ANADAL, YAN DAL VE KREDİ TRANSFERİ YÖNETMELİĞİ",
                "belge_turu": "yonetmelik",
            },
        )

        assert _resolve_chunk_source_family(chunk) == "uy"

    def test_chunk_source_family_does_not_treat_tebligat_yonetmeligi_as_teblig(self):
        chunk = RetrievedChunk(
            text="Elektronik tebligat yönetmeliği parçası.",
            citation="29033 m.1/f.0",
            source="29033",
            score=0.9,
            metadata={
                "source_family_canonical": "teblig",
                "source_title": "ELEKTRONİK TEBLİGAT YÖNETMELİĞİ",
                "belge_turu": "teblig",
            },
        )

        assert _resolve_chunk_source_family(chunk) == "yonetmelik"

    def test_chunk_source_family_profile_keeps_raw_kky_but_maps_routing_family_to_generic_regulation(self):
        chunk = RetrievedChunk(
            text="Mesafeli sözleşmeler yönetmeliği parçası.",
            citation="20237 m.1/f.0",
            source="20237",
            score=0.9,
            metadata={
                "source_family_canonical": "kky",
                "source_family_raw": "kky",
                "source_family_mapped": "yonetmelik",
                "source_family_mapping_reason": "kky_to_yonetmelik",
                "source_title": "MESAFELİ SÖZLEŞMELER YÖNETMELİĞİ",
                "belge_turu": "kky",
            },
        )

        profile = _resolve_chunk_source_family_profile(chunk)
        assert profile["raw_family"] == "kky"
        assert profile["resolved_family"] == "kky"
        assert profile["mapped_family"] == "yonetmelik"
        assert _resolve_chunk_routing_family(chunk) == "yonetmelik"

    def test_chunk_routing_family_does_not_bridge_repealed_mulga_into_active_kanun_pool(self):
        chunk = RetrievedChunk(
            text="Mülga iş kanunu hükmü.",
            citation="1475 m.98/f.0",
            source="1475",
            score=0.9,
            metadata={
                "source_family_canonical": "mulga_kanun",
                "source_family_raw": "mulga_kanun",
                "source_family_mapped": "kanun",
                "source_family_mapping_reason": "mulga_to_kanun",
                "source_title": "İŞ KANUNUNUN YÜRÜRLÜKTEN KALDIRILMIŞ HÜKÜMLERİ",
                "mulga": True,
            },
        )

        assert _resolve_chunk_source_family(chunk) == "mulga_kanun"
        assert _resolve_chunk_routing_family(chunk) == "mulga_kanun"

    def test_dedupe_retrieved_chunks_merges_recall_lane_sources(self):
        dense_chunk = RetrievedChunk(
            text="Aynı metin",
            citation="20237 m.1/f.0",
            source="20237",
            score=0.5,
            metadata={"source_title": "MESAFELİ SÖZLEŞMELER YÖNETMELİĞİ"},
        )
        metadata_chunk = RetrievedChunk(
            text="Aynı metin",
            citation="20237 m.1/f.0",
            source="20237",
            score=0.8,
            metadata={"source_title": "MESAFELİ SÖZLEŞMELER YÖNETMELİĞİ"},
        )

        _annotate_recall_lane_chunks([dense_chunk], lane="semantic_dense_recall")
        _annotate_recall_lane_chunks([metadata_chunk], lane="metadata_guided_recall")
        deduped = _dedupe_retrieved_chunks([dense_chunk, metadata_chunk])

        assert len(deduped) == 1
        merged = deduped[0]
        assert merged.score == 0.8
        assert set((merged.metadata or {}).get("retrieval_lane_sources") or []) == {
            "semantic_dense_recall",
            "metadata_guided_recall",
        }
        assert (merged.metadata or {}).get("merged_lane_present") is True

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

    def test_sanitize_retrieval_plan_payload_drops_fabricated_long_title_terms(self):
        payload = _sanitize_retrieval_plan_payload(
            {
                "law_hints": ["4857"],
                "source_family_hints": ["kanun"],
                "term_hints": [
                    "işçi haklarının korunması hakkında kanun",
                    "işe iade",
                ],
            },
            user_query=(
                "42 çalışanlı bir işyerinde 8 aylık kıdemi bulunan personel işe iade "
                "yoluna gidebilir mi?"
            ),
        )

        assert payload == {
            "law_hints": ["4857"],
            "source_family_hints": ["kanun", "mulga_kanun"],
            "term_hints": ["işe iade"],
        }

    def test_metadata_lookup_anchor_gate_skips_generic_scenario_query(self):
        signals = _parse_metadata_lookup_query_signals(
            "42 çalışanlı işyerinde 8 aylık kıdemi bulunan personel işe iade davası açabilir mi?"
        )

        assert _metadata_lookup_has_strong_query_anchor(signals) is False

    def test_extract_effective_legal_query_strips_benchmark_scaffolding(self):
        query = (
            "Bu soruyu 2026-04-19 tarihindeki yururluk durumuna gore cevapla. "
            "Yaniti kisa sonuc, kisa gerekce, dayanak belge zinciri ve gerekiyorsa "
            "yururluk/guncellik notu seklinde ver.\n"
            "Beklenen çıktı tipi: Kısa sonuç + gerekçe + dayanak belge zinciri.\n\n"
            "42 çalışanlı bir işyerinde 8 aylık kıdemi bulunan personel işe iade "
            "davası açabilir mi?"
        )

        assert _extract_effective_legal_query(query) == (
            "42 çalışanlı bir işyerinde 8 aylık kıdemi bulunan personel işe iade "
            "davası açabilir mi?"
        )

    def test_extract_source_identifier_tokens_ignores_plain_scenario_numbers(self):
        tokens = _extract_source_identifier_tokens(
            "42 çalışanlı bir işyerinde 8 aylık kıdemi bulunan personel işe iade davası açabilir mi?"
        )

        assert tokens == set()

    def test_extract_source_identifier_tokens_keeps_explicit_legal_identifiers(self):
        tokens = _extract_source_identifier_tokens(
            "4857 sayılı İş Kanunu ile Karar Sayısı: 3350 olan düzenleme birlikte nasıl uygulanır?"
        )

        assert {"4857", "3350"} <= tokens

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
                metadata={
                    "source_title": "İŞ KANUNU",
                    "law_short_name": "IK",
                    "law_no": "4857",
                    "belge_turu": "kanun",
                    "effective_state": "active",
                },
            ),
            RetrievedChunk(
                text="Toplu işçi çıkarma",
                citation="1475 m.24/f.0",
                source="1475",
                score=0.89,
                metadata={
                    "source_title": "İŞ KANUNU",
                    "law_short_name": "1475",
                    "law_no": "1475",
                    "belge_turu": "mulga_kanun",
                    "effective_state": "repealed",
                    "mulga": True,
                    "yururluk_bitis": "2003-06-10",
                },
            ),
            RetrievedChunk(
                text="Tapu sicili",
                citation="20135150 m.7/f.0",
                source="20135150",
                score=0.93,
                metadata={
                    "source_title": "TAPU SİCİLİ TÜZÜĞÜ",
                    "law_short_name": "20135150",
                    "belge_turu": "tuzuk",
                },
            ),
        ]

        candidates = _build_source_cluster_candidates(chunks, limit=8)

        assert len(candidates) == 3
        candidate_by_key = {item["source_key"]: item for item in candidates}
        assert candidate_by_key["4857"]["display_title"] == "İŞ KANUNU"
        assert candidate_by_key["4857"]["laws"] == ["IK"]
        assert candidate_by_key["4857"]["effective_state"] == "active"
        assert candidate_by_key["1475"]["display_title"] == "İŞ KANUNU"
        assert candidate_by_key["1475"]["laws"] == ["1475"]
        assert candidate_by_key["1475"]["effective_state"] == "repealed"
        assert candidate_by_key["20135150"]["display_title"] == "TAPU SİCİLİ TÜZÜĞÜ"

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

    def test_source_cluster_overrides_prefers_active_planner_law_in_current_law_scenario(self):
        candidates = [
            {
                "cluster_id": "C1",
                "source_key": "1475",
                "display_title": "İŞ KANUNU",
                "source_family": "mulga_kanun",
                "laws": ["1475"],
                "citations": ["1475 m.24/f.0"],
                "excerpts": ["Toplu işçi çıkarma ve eski fesih rejimi."],
                "state_rank": 2,
                "effective_state": "repealed",
            },
            {
                "cluster_id": "C2",
                "source_key": "4857",
                "display_title": "İŞ KANUNU",
                "source_family": "kanun",
                "laws": ["4857", "IK"],
                "citations": ["4857 m.21/f.0"],
                "excerpts": ["İşe iade, fesih bildirimi ve geçerli sebep rejimi."],
                "state_rank": 0,
                "effective_state": "active",
            },
        ]

        payload = _apply_source_cluster_deterministic_overrides(
            payload={"selected_cluster_ids": ["C1"], "selected_law_hints": ["1475"]},
            candidates=candidates,
            user_query=(
                "42 çalışanlı işyerinde 8 aylık kıdemi bulunan personel performans gerekçesiyle "
                "işten çıkarılırsa işe iade yoluna gidebilir mi?"
            ),
            requested_source_families=["kanun", "mulga_kanun"],
            source_family_resolution=_resolve_source_family_prior(
                "42 çalışanlı işyerinde 8 aylık kıdemi bulunan personel performans gerekçesiyle "
                "işten çıkarılırsa işe iade yoluna gidebilir mi?"
            ),
            planner_law_hints={"4857"},
        )

        assert payload["selected_cluster_ids"] == ["C2"]
        assert payload["selected_law_hints"] == ["4857", "IK"]

    def test_metadata_first_source_candidates_rank_title_identifier_and_family(self, tmp_path, monkeypatch):
        article_rows = tmp_path / "article_rows.jsonl"
        article_rows.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "source_id": "9903:9903:m1:f0:from2025-05-30:to9999-12-31",
                            "belge_turu": "cb_karar",
                            "belge_no": "9903",
                            "belge_kisa_adi": "9903",
                            "belge_adi": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR (KARAR SAYISI: 9903)",
                            "resmi_gazete_tarih": "2025-05-30",
                            "yururluk_baslangic": "2025-05-30",
                            "yururluk_bitis": "9999-12-31",
                        },
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        {
                            "source_id": "20047114:20047114:m0:f0:from2004-04-21:to9999-12-31",
                            "belge_turu": "yonetmelik",
                            "belge_no": "20047114",
                            "belge_kisa_adi": "20047114",
                            "belge_adi": "HAZİNE ARAZİLERİNİN BEDELSİZ DEVRİNE İLİŞKİN YÖNETMELİK",
                        },
                        ensure_ascii=False,
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("MEVZUAT_ARTICLE_ROWS_PATH", str(article_rows))
        load_canonical_source_catalog.cache_clear()

        selector = _select_metadata_first_source_candidates(
            query="Yatırım teşvik belgesi için 2026'da 9903 sayılı karar mı uygulanır?",
            requested_source_families=["cb_karar"],
            source_family_resolution=_resolve_source_family_prior("Yatırım teşvik belgesi için karar sorusu"),
        )

        assert selector is not None
        assert selector["selected_source_keys"] == ["9903"]
        assert selector["selected_families"] == ["cb_karar"]
        assert selector["candidates"][0]["canonical_identifier"] == "9903"
        assert selector["metadata_lookup_hit"] is True
        assert selector["metadata_lookup_source"] == "exact_identifier_lookup"
        assert selector["metadata_lookup_rank"] == 1
        assert selector["metadata_lookup_confidence"] >= 0.80
        assert "identifier_exact" in selector["candidates"][0]["match_reasons"]
        assert "YATIRIMLARDA DEVLET YARDIMLARI" in _build_metadata_first_query_expansion(selector)
        load_canonical_source_catalog.cache_clear()

    def test_metadata_lookup_parser_extracts_family_identifier_title_and_temporal_signals(self):
        signals = _parse_metadata_lookup_query_signals(
            "2026'da 9903 sayılı Yatırımlarda Devlet Yardımları Hakkında Karar halen yürürlükte mi?"
        )

        assert "cb_karar" in signals["parsed_family_candidates"]
        assert any(item["value"] == "9903" and item["kind"] == "cb_karar" for item in signals["parsed_identifier_candidates"])
        assert any(
            "yatirimlarda devlet yardimlari" in item["value"]
            for item in signals["parsed_title_ngrams"]
        )
        assert {"value": "2026", "kind": "year", "source": "year_pattern"} in signals["parsed_temporal_cues"]
        assert any(item["kind"] == "current" for item in signals["parsed_temporal_cues"])

    def test_metadata_lookup_parser_extracts_issuer_and_regulation_title_without_qid_rules(self):
        signals = _parse_metadata_lookup_query_signals(
            "Ticaret Bakanlığı ithalat rejimi tebliği kapsamındaki başvuru usulünü açıklar mısın?"
        )

        assert "teblig" in signals["parsed_family_candidates"]
        assert any(item["value"] == "ticaret bakanligi" for item in signals["parsed_issuer_candidates"])
        assert any("ithalat rejimi tebligi" in item["value"] for item in signals["parsed_title_ngrams"])

    def test_metadata_first_uses_parser_issuer_family_anchor_for_catalog_lookup(self, tmp_path, monkeypatch):
        article_rows = tmp_path / "article_rows.jsonl"
        article_rows.write_text(
            json.dumps(
                {
                    "source_id": "AU-DISIPLIN:AU-DISIPLIN:m1:f0:from2024-01-01:to9999-12-31",
                    "belge_turu": "uy",
                    "belge_no": "AU-DISIPLIN",
                    "belge_kisa_adi": "AU-DISIPLIN",
                    "belge_adi": "ANKARA ÜNİVERSİTESİ DİSİPLİN YÖNETMELİĞİ",
                    "issuer": "Ankara Üniversitesi",
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("MEVZUAT_ARTICLE_ROWS_PATH", str(article_rows))
        load_canonical_source_catalog.cache_clear()

        selector = _select_metadata_first_source_candidates(
            query="Ankara Üniversitesi öğrencileri için yaptırım kuralları hangi yönetmelikte?",
            requested_source_families=[],
            source_family_resolution=_resolve_source_family_prior(
                "Ankara Üniversitesi öğrencileri için yaptırım kuralları hangi yönetmelikte?"
            ),
        )

        assert selector is not None
        assert selector["selected_source_keys"] == ["AU-DISIPLIN"]
        assert selector["metadata_lookup_source"] == "issuer_family_lookup"
        assert "issuer_exact" in selector["candidates"][0]["match_reasons"]
        assert "parsed_family_match" in selector["candidates"][0]["match_reasons"]
        load_canonical_source_catalog.cache_clear()

    def test_metadata_lookup_family_prior_closes_no_gate_from_selector_family(self):
        base_resolution = SourceFamilyResolution(
            predicted_family=None,
            family_confidence=0.0,
            family_candidates=[],
            routing_families=[],
            query_expansions=[],
            expected_family_prior=None,
            preferred_families=[],
            fallback_families=[],
            selected_family_confidence=0.0,
            family_override_reason="no_family_prior",
        )
        selector = {
            "metadata_lookup_hit": True,
            "metadata_lookup_confidence": 0.78,
            "metadata_lookup_source": "issuer_family_lookup",
            "candidates": [
                {
                    "source_family": "uy",
                    "metadata_lookup_confidence": 0.78,
                    "metadata_lookup_source": "issuer_family_lookup",
                    "score": 33.0,
                }
            ],
        }

        enriched = _apply_metadata_lookup_family_prior(base_resolution, selector)

        assert enriched.expected_family_prior == "uy"
        assert enriched.preferred_families == ["uy"]
        assert "uy" in enriched.routing_families
        assert enriched.family_override_reason == "metadata_lookup_family_prior"

    def test_metadata_lookup_family_prior_allows_controlled_negative_transition(self):
        base_resolution = SourceFamilyResolution(
            predicted_family="cb_karar",
            family_confidence=0.86,
            family_candidates=[
                SourceFamilyCandidate(
                    family="cb_karar",
                    score=6.0,
                    confidence=0.86,
                    signals=["cb_karar_document_type"],
                )
            ],
            routing_families=["cb_karar"],
            query_expansions=["Cumhurbaşkanı kararı karar sayısı madde"],
            expected_family_prior="cb_karar",
            preferred_families=["cb_karar"],
            fallback_families=[],
            selected_family_confidence=0.86,
            family_override_reason="strong_family_prior",
        )
        selector = {
            "metadata_lookup_hit": True,
            "metadata_lookup_confidence": 0.74,
            "metadata_lookup_source": "normalized_title_lookup",
            "candidates": [
                {
                    "source_family": "teblig",
                    "metadata_lookup_confidence": 0.74,
                    "metadata_lookup_source": "normalized_title_lookup",
                    "score": 29.0,
                }
            ],
        }

        enriched = _apply_metadata_lookup_family_prior(base_resolution, selector)

        assert enriched.expected_family_prior == "teblig"
        assert enriched.preferred_families == ["teblig"]
        assert enriched.family_override_reason == "metadata_lookup_negative_transition"

    def test_metadata_lookup_family_prior_keeps_current_law_guard_against_repealed_mulga(self):
        base_resolution = _resolve_source_family_prior(
            "İşveren performans gerekçesiyle işçiyi işten çıkarırsa işe iade davası açılabilir mi?"
        )
        selector = {
            "metadata_lookup_hit": True,
            "metadata_lookup_confidence": 0.91,
            "metadata_lookup_source": "normalized_title_lookup",
            "candidates": [
                {
                    "source_family": "kanun",
                    "source_family_raw": "mulga_kanun",
                    "effective_state": "repealed",
                    "metadata_lookup_confidence": 0.91,
                    "metadata_lookup_source": "normalized_title_lookup",
                    "score": 41.0,
                }
            ],
        }

        enriched = _apply_metadata_lookup_family_prior(base_resolution, selector)

        assert enriched.predicted_family == "kanun"
        assert enriched.preferred_families == ["kanun"]
        assert enriched.scenario_current_law_question is True
        assert enriched.scenario_current_law_prior is True
        assert enriched.family_override_reason == "scenario_current_law_prior"

    def test_metadata_lookup_family_prior_keeps_relation_primary_kanun_against_regulation_metadata(self):
        query = (
            "Elektronik tebligat muhatabın elektronik adresine ulaştığı anda mı, "
            "yoksa daha sonraki bir tarihte mi tebliğ edilmiş sayılır? "
            "Kanun ve yönetmelik ilişkisini de göster."
        )
        base_resolution = _resolve_source_family_prior(query)
        selector = {
            "metadata_lookup_hit": True,
            "metadata_lookup_confidence": 0.91,
            "metadata_lookup_source": "normalized_title_lookup",
            "candidates": [
                {
                    "source_key": "20631",
                    "source_family": "yonetmelik",
                    "source_family_raw": "teblig",
                    "effective_state": "active",
                    "metadata_lookup_confidence": 0.91,
                    "metadata_lookup_source": "normalized_title_lookup",
                    "score": 41.0,
                }
            ],
        }

        enriched = _apply_metadata_lookup_family_prior(
            base_resolution,
            selector,
            query=query,
        )

        assert base_resolution.collision_resolution_reason == "kanun_yonetmelik_relation_prefers_kanun"
        assert enriched.predicted_family == "kanun"
        assert enriched.preferred_families == ["kanun"]

    def test_metadata_lookup_family_prior_rejects_nonacademic_uy_title_lookup_transition(self):
        query = (
            "Sosyal medya içerik üreticisinin örtülü reklam yapıp yapmadığı sorusunda "
            "hangi yönetmelik ana uygulama metni olarak aranmalıdır?"
        )
        base_resolution = _resolve_source_family_prior(query)
        selector = {
            "metadata_lookup_hit": True,
            "metadata_lookup_confidence": 0.93,
            "metadata_lookup_source": "title_ngram_family_lookup",
            "candidates": [
                {
                    "source_key": "31497",
                    "source_family": "uy",
                    "source_family_raw": "uy",
                    "effective_state": "active",
                    "metadata_lookup_confidence": 0.93,
                    "metadata_lookup_source": "title_ngram_family_lookup",
                    "score": 41.0,
                }
            ],
        }

        enriched = _apply_metadata_lookup_family_prior(
            base_resolution,
            selector,
            query=query,
        )

        assert base_resolution.predicted_family == "yonetmelik"
        assert enriched.predicted_family == "yonetmelik"
        assert enriched.preferred_families == ["yonetmelik"]
        assert enriched.family_override_reason == base_resolution.family_override_reason

    def test_relation_query_metadata_focus_promotes_primary_kanun_candidate(self):
        query = (
            "Elektronik tebligat muhatabın elektronik adresine ulaştığı anda mı, "
            "yoksa daha sonraki bir tarihte mi tebliğ edilmiş sayılır? "
            "Kanun ve yönetmelik ilişkisini de göster."
        )
        resolution = _resolve_source_family_prior(query)
        selector = {
            "metadata_lookup_hit": True,
            "candidates": [
                {
                    "source_key": "20631",
                    "canonical_identifier": "20631",
                    "source_family": "yonetmelik",
                },
                {
                    "source_key": "7201",
                    "canonical_identifier": "7201",
                    "source_family": "kanun",
                },
            ],
            "selected_source_keys": ["20631", "7201"],
            "selected_families": ["yonetmelik", "kanun"],
        }

        focused = _apply_relation_query_metadata_focus(
            selector,
            query=query,
            source_family_resolution=resolution,
        )

        assert focused["relation_query_detected"] is True
        assert focused["primary_source_candidate"] == "7201"
        assert focused["supporting_source_candidate"] == "20631"
        assert focused["selected_source_keys"] == ["7201"]
        assert focused["selected_families"] == ["kanun"]

    @patch("routers.chat.load_canonical_source_catalog")
    def test_metadata_first_selector_prefers_cb_karar_over_cb_kararname_for_decision_query(
        self, mock_catalog
    ):
        mock_catalog.return_value = {
            "9903": {
                "source_key": "9903",
                "canonical_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR (KARAR SAYISI: 9903)",
                "canonical_title_normalized": "yatirimlarda devlet yardimlari hakkinda karar karar sayisi 9903",
                "canonical_identifier": "9903",
                "canonical_identifier_type": "decision_number",
                "source_family_canonical": "cb_karar",
                "source_family_mapped": "cb_karar",
                "source_family_raw": "cb_karar",
                "source_family_title_inferred": "cb_karar",
                "source_family_mapping_reason": "native_family",
                "issuer": "Cumhurbaşkanı",
                "issuer_normalized": "cumhurbaskani",
                "year_signals": ["2025"],
                "effective_state": "active",
                "alias_titles": [],
            },
            "95": {
                "source_key": "95",
                "canonical_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ",
                "canonical_title_normalized": "yatirimlarda devlet yardimlari hakkinda cumhurbaskanligi kararnamesi",
                "canonical_identifier": "95",
                "canonical_identifier_type": "kararname_number",
                "source_family_canonical": "cb_kararname",
                "source_family_mapped": "cb_kararname",
                "source_family_raw": "cb_kararname",
                "source_family_title_inferred": "cb_kararname",
                "source_family_mapping_reason": "native_family",
                "issuer": "Cumhurbaşkanlığı",
                "issuer_normalized": "cumhurbaskanligi",
                "year_signals": ["2025"],
                "effective_state": "active",
                "alias_titles": [],
            },
        }

        selector = _select_metadata_first_source_candidates(
            query="Yatırımlarda devlet yardımları hakkında karar uygulanır mı?",
            requested_source_families=["cb_karar"],
            source_family_resolution=None,
            query_metadata_signals=_parse_metadata_lookup_query_signals(
                "Yatırımlarda devlet yardımları hakkında karar uygulanır mı?"
            ),
        )

        assert selector is not None
        assert selector["candidates"][0]["source_family"] == "cb_karar"
        assert selector["candidates"][0]["source_key"] == "9903"

    @patch("routers.chat.load_canonical_source_catalog")
    def test_metadata_first_selector_prioritizes_exact_identifier_over_noisy_title_overlap(
        self, mock_catalog
    ):
        mock_catalog.return_value = {
            "9903": {
                "source_key": "9903",
                "canonical_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR (KARAR SAYISI: 9903)",
                "canonical_title_normalized": "yatirimlarda devlet yardimlari hakkinda karar karar sayisi 9903",
                "canonical_identifier": "9903",
                "canonical_identifier_type": "decision_number",
                "source_family_canonical": "cb_karar",
                "source_family_mapped": "cb_karar",
                "source_family_raw": "cb_karar",
                "source_family_title_inferred": "cb_karar",
                "source_family_mapping_reason": "native_family",
                "issuer": "Cumhurbaşkanı",
                "issuer_normalized": "cumhurbaskani",
                "year_signals": ["2025", "2026"],
                "effective_state": "active",
                "alias_titles": [],
            },
            "10019": {
                "source_key": "10019",
                "canonical_title": "7452 SAYILI OLAĞANÜSTÜ HAL KAPSAMINDA YERLEŞME VE YAPILAŞMAYA İLİŞKİN CUMHURBAŞKANLIĞI KARARNAMESİNİN KABUL EDİLMESİNE DAİR KANUNUN EK 1 İNCİ MADDESİ KAPSAMINDA YAPILACAK YENİ YAPILARIN BULUNDUĞU PARSELLERİN MALİKİ OLAN GERÇEK VEYA TÜZEL KİŞİLERE HİBE VE YAPIM KREDİSİ VERİLMESİNE İLİŞKİN 5/10/2023 TARİHLİ VE 7700 SAYILI CUMHURBAŞKANI KARARINDA DEĞİŞİKLİK YAPILMASINA DAİR KARAR (KARAR SAYISI: 10019)",
                "canonical_title_normalized": "7452 sayili olaganustu hal kapsaminda yerlesme ve yapilasmaya iliskin cumhurbaskanligi kararnamesinin kabul edilmesine dair kanunun ek 1 inci maddesi kapsaminda yapilacak yeni yapilarin bulundugu parsellerin maliki olan gercek veya tuzel kisilere hibe ve yapim kredisi verilmesine iliskin 5 10 2023 tarihli ve 7700 sayili cumhurbaskani kararinda degisiklik yapilmasina dair karar karar sayisi 10019",
                "canonical_identifier": "10019",
                "canonical_identifier_type": "decision_number",
                "source_family_canonical": "cb_karar",
                "source_family_mapped": "cb_karar",
                "source_family_raw": "cb_karar",
                "source_family_title_inferred": "cb_karar",
                "source_family_mapping_reason": "native_family",
                "issuer": "Cumhurbaşkanı",
                "issuer_normalized": "cumhurbaskani",
                "year_signals": ["2025", "2026"],
                "effective_state": "active",
                "alias_titles": [],
            },
        }

        query = (
            "Bir yatırımcı 20.05.2025'te yaptığı başvuru için 2026'da işlem tesis ettiriyor. "
            "Yeni 9903 sayılı karar mı uygulanır, yoksa geçiş nedeniyle eski rejim de devrede kalabilir mi?"
        )
        selector = _select_metadata_first_source_candidates(
            query=query,
            requested_source_families=[],
            source_family_resolution=None,
            query_metadata_signals=_parse_metadata_lookup_query_signals(query),
        )

        assert selector is not None
        assert selector["candidates"][0]["source_key"] == "9903"
        assert selector["metadata_lookup_source"] == "exact_identifier_lookup"
        assert "identifier_exact" in selector["candidates"][0]["match_reasons"]
        noisy_candidate = next(item for item in selector["candidates"] if item["source_key"] == "10019")
        assert "identifier_conflict_penalty" in noisy_candidate["match_reasons"]

    def test_metadata_first_identifier_tokens_ignore_article_only_numbers(self, tmp_path, monkeypatch):
        article_rows = tmp_path / "article_rows.jsonl"
        article_rows.write_text(
            json.dumps(
                {
                    "source_id": "107:107:m1:f0:from2020-01-01:to9999-12-31",
                    "belge_turu": "cb_kararname",
                    "belge_no": "107",
                    "belge_kisa_adi": "107",
                    "belge_adi": "107 SAYILI CUMHURBAŞKANLIĞI KARARNAMESİ",
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("MEVZUAT_ARTICLE_ROWS_PATH", str(article_rows))
        load_canonical_source_catalog.cache_clear()

        selector = _select_metadata_first_source_candidates(
            query="HMK m.107 nedir?",
            requested_source_families=[],
            source_family_resolution=_resolve_source_family_prior("HMK m.107 nedir?"),
        )

        assert selector is None
        load_canonical_source_catalog.cache_clear()

    def test_metadata_first_rejects_weak_title_overlap_without_identifier(self, tmp_path, monkeypatch):
        article_rows = tmp_path / "article_rows.jsonl"
        article_rows.write_text(
            json.dumps(
                {
                    "source_id": "3082:3082:m1:f0:from1984-01-01:to9999-12-31",
                    "belge_turu": "kanun",
                    "belge_no": "3082",
                    "belge_kisa_adi": "3082",
                    "belge_adi": "KAMU YARARININ ZORUNLU KILDIĞI HALLERDE KAMU HİZMETİ NİTELİĞİ TAŞIYAN ÖZEL TEŞEBBÜSLERİN DEVLETLEŞTİRİLMESİ USUL VE ESASLARI HAKKINDA KANUN",
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("MEVZUAT_ARTICLE_ROWS_PATH", str(article_rows))
        load_canonical_source_catalog.cache_clear()

        selector = _select_metadata_first_source_candidates(
            query="42 çalışanlı işyerinde performans gerekçesiyle fesihte işe iade olur mu?",
            requested_source_families=["kanun"],
            source_family_resolution=_resolve_source_family_prior("işe iade fesih kanun sorusu"),
        )

        assert selector is None
        load_canonical_source_catalog.cache_clear()

    def test_metadata_filter_law_no_matches_general_belge_no(self):
        metadata_filter = MetadataFilter(law_no="3350")
        expr = metadata_filter.to_milvus_expr()
        assert 'metadata["belge_no"] == "3350"' in (expr or "")
        retriever = MockRetriever(
            fixture_chunks=[
                {
                    "id": "c1",
                    "text": "İthalat rejimi kararı",
                    "embedding": [1.0, 0.0],
                    "metadata": {"belge_no": "3350", "madde_no": "1"},
                }
            ]
        )

        results, stats = retriever.retrieve(
            query_vector=[1.0, 0.0],
            metadata_filter=metadata_filter,
        )

        assert stats.hit_count == 1
        assert results[0].metadata["belge_no"] == "3350"

    def test_source_key_recall_uses_general_belge_no_filter_for_non_numeric_catalog_keys(self):
        mock_retriever = MagicMock()
        from rag.retriever import RetrievalResult, RetrievalStats

        stats = RetrievalStats(
            collection="test",
            query_preview="ankara",
            top_k=4,
            filter_expr=None,
            hit_count=1,
            latency_ms=1.0,
        )
        mock_retriever.retrieve = MagicMock(
            return_value=(
                [
                    RetrievalResult(
                        chunk_id="au",
                        text="Disiplin yönetmeliği metni",
                        score=0.8,
                        metadata={"belge_no": "AU-DISIPLIN", "madde_no": "1"},
                    )
                ],
                stats,
            )
        )

        chunks = _retrieve_source_key_chunks(
            retriever=mock_retriever,
            query="Ankara Üniversitesi yaptırım kuralları",
            source_keys=["AU-DISIPLIN"],
            top_k=4,
        )

        assert chunks[0].metadata["belge_no"] == "AU-DISIPLIN"
        metadata_filter = mock_retriever.retrieve.call_args.kwargs["metadata_filter"]
        assert metadata_filter.law_no == "AU-DISIPLIN"
        assert metadata_filter.law_short_name is None
        assert metadata_filter.belge_turu is None

    def test_source_key_recall_can_bind_family_to_avoid_cross_family_numeric_noise(self):
        from rag.retriever import RetrievalResult, RetrievalStats

        class FakeRetriever:
            def __init__(self) -> None:
                self.last_filters: list[MetadataFilter] = []

            def retrieve(self, *, query, top_k, metadata_filter=None):
                self.last_filters.append(metadata_filter)
                fixtures = [
                    RetrievalResult(
                        chunk_id="9903-cb",
                        text="Yatırımlarda Devlet Yardımları Hakkında Karar.",
                        score=0.80,
                        metadata={
                            "source_id": "9903:9903:m0:f0",
                            "belge_no": "9903",
                            "kanun_no": "9903",
                            "belge_turu": "cb_karar",
                            "madde_no": "0",
                            "source_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR (KARAR SAYISI: 9903)",
                        },
                    ),
                    RetrievalResult(
                        chunk_id="9903-teblig",
                        text="Garanti belgesi sürelerinin uzatılmasına ilişkin tebliğ.",
                        score=0.95,
                        metadata={
                            "source_id": "9903:9903:m1:f0",
                            "belge_no": "9903",
                            "kanun_no": "9903",
                            "belge_turu": "teblig",
                            "madde_no": "1",
                            "source_title": "GARANTİ BELGESİ SÜRELERİNİN UZATILMASINA İLİŞKİN TEBLİĞ",
                        },
                    ),
                ]
                filtered = []
                for item in fixtures:
                    if metadata_filter and not MockRetriever._matches_filter(
                        {"metadata": item.metadata},
                        metadata_filter,
                    ):
                        continue
                    filtered.append(item)
                stats = RetrievalStats(
                    collection="test",
                    query_preview=query,
                    top_k=top_k,
                    filter_expr=metadata_filter.to_milvus_expr() if metadata_filter else None,
                    hit_count=len(filtered),
                    latency_ms=1.0,
                )
                return filtered[:top_k], stats

        retriever = FakeRetriever()
        chunks = _retrieve_source_key_chunks(
            retriever=retriever,
            query="Yeni 9903 sayılı karar mı uygulanır?",
            source_keys=["9903"],
            source_family_by_key={"9903": "cb_karar"},
            top_k=8,
        )

        assert len(chunks) == 1
        assert chunks[0].metadata["belge_turu"] == "cb_karar"
        assert chunks[0].metadata["belge_no"] == "9903"
        metadata_filter = retriever.last_filters[-1]
        assert metadata_filter.law_no == "9903"
        assert metadata_filter.belge_turu == "cb_karar"

    def test_source_identity_reranker_promotes_metadata_first_match(self):
        wrong_chunk = RetrievedChunk(
            text="Arazi devrine ilişkin yönetmelik hükmü.",
            citation="20047114 m.0",
            source="20047114",
            score=0.99,
            metadata={
                "belge_turu": "yonetmelik",
                "belge_no": "20047114",
                "source_title": "HAZİNE ARAZİLERİNİN BEDELSİZ DEVRİNE İLİŞKİN YÖNETMELİK",
                "madde_no": "0",
            },
        )
        right_chunk = RetrievedChunk(
            text="Yatırım teşvik belgesi ve geçiş hükümleri.",
            citation="9903 m.1",
            source="9903",
            score=0.42,
            metadata={
                "belge_turu": "cb_karar",
                "belge_no": "9903",
                "source_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR (KARAR SAYISI: 9903)",
                "canonical_identifier": "9903",
                "madde_no": "1",
                "yururluk_baslangic": "2025-05-30",
                "yururluk_bitis": "9999-12-31",
            },
        )
        selector = {
            "candidates": [
                {
                    "source_key": "9903",
                    "canonical_identifier": "9903",
                    "canonical_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR (KARAR SAYISI: 9903)",
                }
            ]
        }

        reranked, trace = _rerank_chunks_by_source_identity(
            query="Yatırım teşvik belgesi için 9903 sayılı karar uygulanır mı?",
            chunks=[wrong_chunk, right_chunk],
            requested_source_families=["cb_karar"],
            metadata_first_selector=selector,
        )

        assert reranked[0].citation == "9903 m.1"
        assert trace["applied"] is True
        assert trace["top_scores"][0]["metadata_first_match"] is True
        assert trace["identifier_match_type"] == "exact_identifier"
        assert trace["document_identity_score"] == trace["top_scores"][0]["document_identity_score"]
        assert trace["identity_lock_strength"] == "strong"
        assert trace["identity_rerank_input_source"] == "metadata_lookup_selector"
        assert trace["identity_rerank_input_lane"] == "unknown"
        assert trace["replacement_guard_triggered"] is False
        assert trace["selected_document_rank_after_identity_rerank"] == 1
        assert trace["selected_document_original_rank"] == 2
        assert trace["top_scores"][0]["title_bias_applied"] > 0

    def test_source_identity_reranker_triggers_replacement_guard_for_metadata_only_weak_match(self):
        weak_chunk = RetrievedChunk(
            text="İthalata ilişkin tebliğ hükmü.",
            citation="42854 m.0",
            source="42854",
            score=0.91,
            metadata={
                "belge_turu": "teblig",
                "belge_no": "42854",
                "source_title": "KULLANILMIŞ VEYA YENİLEŞTİRİLMİŞ EŞYA İTHALATINA İLİŞKİN TEBLİĞ (İTHALAT: 2026/9)",
                "madde_no": "0",
            },
        )
        _annotate_recall_lane_chunks([weak_chunk], lane="metadata_guided_recall")

        reranked, trace = _rerank_chunks_by_source_identity(
            query="İthalat rejimi kararı hangisidir?",
            chunks=[weak_chunk],
            requested_source_families=["cb_karar"],
            metadata_first_selector={"candidates": []},
        )

        assert reranked[0].citation == "42854 m.0"
        assert trace["identity_rerank_input_lane"] == "metadata_guided_recall"
        assert trace["replacement_guard_triggered"] is True
        assert trace["top_scores"][0]["replacement_guard_triggered"] is True

    def test_source_identity_reranker_prefers_strong_title_match_over_generic_family(self):
        generic_chunk = RetrievedChunk(
            text="Genel yönetmelik hükmü.",
            citation="1000 m.1",
            source="1000",
            score=0.99,
            metadata={
                "belge_turu": "yonetmelik",
                "belge_no": "1000",
                "source_title": "GENEL YÖNETMELİK",
                "madde_no": "1",
            },
        )
        titled_chunk = RetrievedChunk(
            text="Hazine arazilerinin bedelsiz devrine ilişkin usul.",
            citation="20047114 m.1",
            source="20047114",
            score=0.25,
            metadata={
                "belge_turu": "yonetmelik",
                "belge_no": "20047114",
                "source_title": "HAZİNE ARAZİLERİNİN BEDELSİZ DEVRİNE İLİŞKİN YÖNETMELİK",
                "madde_no": "1",
            },
        )

        reranked, trace = _rerank_chunks_by_source_identity(
            query="Hazine arazilerinin bedelsiz devrine ilişkin yönetmelikte devir usulü nedir?",
            chunks=[generic_chunk, titled_chunk],
            requested_source_families=["yonetmelik"],
            metadata_first_selector=None,
        )

        assert reranked[0].citation == "20047114 m.1"
        assert trace["title_match_type"] in {"exact_phrase", "strong_overlap"}
        assert "title_" in trace["document_rerank_reason"]

    def test_source_identity_reranker_demotes_repealed_chunk_for_current_query(self):
        repealed_chunk = RetrievedChunk(
            text="Eski yürürlükten kalkmış metin.",
            citation="6763 m.20",
            source="6763",
            score=0.99,
            metadata={
                "belge_turu": "mulga_kanun",
                "belge_no": "6763",
                "source_title": "MÜLGA KANUN",
                "madde_no": "20",
                "yururluk_bitis": "1900-01-01",
                "mulga": True,
            },
        )
        active_chunk = RetrievedChunk(
            text="Güncel yürürlükteki metin.",
            citation="9903 m.1",
            source="9903",
            score=0.5,
            metadata={
                "belge_turu": "cb_karar",
                "belge_no": "9903",
                "source_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR",
                "madde_no": "1",
                "yururluk_baslangic": "2025-05-30",
                "yururluk_bitis": "9999-12-31",
                "mulga": False,
            },
        )

        reranked, trace = _rerank_chunks_by_source_identity(
            query="Bu düzenleme halen yürürlükte mi, güncel metin hangisi?",
            chunks=[repealed_chunk, active_chunk],
            requested_source_families=[],
            metadata_first_selector=None,
        )

        assert reranked[0].citation == "9903 m.1"
        assert trace["top_scores"][0]["active_rank"] == 0

    def test_source_identity_reranker_does_not_reward_single_token_weak_title(self):
        generic_chunk = RetrievedChunk(
            text="Genel karar metni.",
            citation="100 m.1",
            source="100",
            score=0.9,
            metadata={
                "belge_turu": "cb_karar",
                "belge_no": "100",
                "source_title": "GENEL KARAR",
                "madde_no": "1",
            },
        )
        specific_chunk = RetrievedChunk(
            text="Yatırımlarda devlet yardımları hükmü.",
            citation="9903 m.1",
            source="9903",
            score=0.2,
            metadata={
                "belge_turu": "cb_karar",
                "belge_no": "9903",
                "source_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR",
                "madde_no": "1",
            },
        )

        reranked, trace = _rerank_chunks_by_source_identity(
            query="Yatırımlarda devlet yardımları hakkında karar ne düzenler?",
            chunks=[generic_chunk, specific_chunk],
            requested_source_families=["cb_karar"],
            metadata_first_selector=None,
        )

        assert reranked[0].citation == "9903 m.1"
        generic_trace = next(item for item in trace["top_scores"] if item["citation"] == "100 m.1")
        assert generic_trace["title_match_type"] == "none"

    def test_source_identity_reranker_demotes_university_regulation_without_academic_intent(self):
        university_chunk = RetrievedChunk(
            text="Üniversite yerel yönetmelik hükmü.",
            citation="3000 m.1",
            source="3000",
            score=0.95,
            metadata={
                "belge_turu": "uy",
                "belge_no": "3000",
                "source_title": "AMASYA ÜNİVERSİTESİ ÖNLİSANS VE LİSANS EĞİTİM-ÖĞRETİM VE SINAV YÖNETMELİĞİ",
                "madde_no": "1",
            },
        )
        regulator_chunk = RetrievedChunk(
            text="Uzaktan kimlik tespiti ve sözleşme kuruluşuna ilişkin kurum yönetmeliği.",
            citation="BANKA-UZAKTAN m.1",
            source="BANKA-UZAKTAN",
            score=0.2,
            metadata={
                "belge_turu": "kky",
                "belge_no": "BANKA-UZAKTAN",
                "source_title": "BANKALARCA KULLANILACAK UZAKTAN KİMLİK TESPİTİ YÖNTEMLERİNE VE ELEKTRONİK ORTAMDA SÖZLEŞME İLİŞKİSİNİN KURULMASINA İLİŞKİN YÖNETMELİK",
                "madde_no": "1",
            },
        )
        _annotate_recall_lane_chunks([university_chunk], lane="metadata_guided_recall")
        _annotate_recall_lane_chunks([regulator_chunk], lane="dense")

        reranked, trace = _rerank_chunks_by_source_identity(
            query="Bir banka müşterisini uzaktan kimlik tespiti yaparak ve elektronik ortamda sözleşme ilişkisi kurarak edinmek istiyor. Hangi kurum yönetmeliği ana uygulama metnidir?",
            chunks=[university_chunk, regulator_chunk],
            requested_source_families=["uy"],
            metadata_first_selector=None,
        )

        assert reranked[0].citation == "BANKA-UZAKTAN m.1"
        university_trace = next(item for item in trace["top_scores"] if item["citation"] == "3000 m.1")
        assert "uy_without_academic_query_penalty" in university_trace["document_rerank_reason"]
        assert university_trace["replacement_guard_triggered"] is True

    def test_apply_relation_query_metadata_focus_prefers_cb_karar_over_genelge(self):
        selector = {
            "candidates": [
                {
                    "source_key": "15",
                    "canonical_identifier": "15",
                    "canonical_title": "2026-2028 Dönemi Yatırım Programı Hazırlıkları ile İlgili",
                    "source_family": "cb_genelge",
                },
                {
                    "source_key": "10868",
                    "canonical_identifier": "10868",
                    "canonical_title": "2026 Yılı Kamu Yatırım Programının Kabulü ve Uygulanmasına Dair Karar (Karar Sayısı: 10868)",
                    "source_family": "cb_karar",
                },
            ]
        }

        focused = _apply_relation_query_metadata_focus(
            selector,
            query="2026 Yılı Kamu Yatırım Programında yer almayan bir proje için ihale yapılabilir mi? Soruyu hangi karar üzerinden cevaplayıp hangi uygulama genelgesine bakarsın?",
            source_family_resolution=None,
        )

        assert focused is not None
        assert focused["candidates"][0]["source_family"] == "cb_karar"
        assert focused["final_primary_source_reason"] == "cb_karar_cb_genelge_relation_primary"

    def test_source_identity_reranker_prefers_khk_over_cbk_for_transition_relation_query(self):
        cbk_chunk = RetrievedChunk(
            text="Cumhurbaşkanlığı kararnamesi hükmü.",
            citation="34 m.1",
            source="34",
            score=0.98,
            metadata={
                "belge_turu": "cb_kararname",
                "belge_no": "34",
                "source_title": "TÜRKİYE ADALET AKADEMİSİ HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 34)",
                "kararname_number": "34",
                "madde_no": "1",
            },
        )
        khk_chunk = RetrievedChunk(
            text="Eski teşkilat atfı ve geçiş hükmü.",
            citation="703 m.1",
            source="703",
            score=0.25,
            metadata={
                "belge_turu": "khk",
                "belge_no": "703",
                "source_title": "703 SAYILI KANUN HÜKMÜNDE KARARNAME",
                "kanun_no": "703",
                "madde_no": "1",
            },
        )
        _annotate_recall_lane_chunks([khk_chunk], lane="dense")

        reranked, trace = _rerank_chunks_by_source_identity(
            query="Mevzuat hâlâ Bakanlar Kurulu veya eski teşkilat isimlerine atıf yapıyorsa, Cumhurbaşkanlığı Hükümet Sistemine geçiş bakımından hangi KHK ve hangi CBK bağlantısı kontrol edilmelidir?",
            chunks=[cbk_chunk, khk_chunk],
            requested_source_families=["cb_kararname"],
            metadata_first_selector=None,
        )

        assert reranked[0].citation == "703 m.1"
        cbk_trace = next(item for item in trace["top_scores"] if item["citation"] == "34 m.1")
        assert "strict_khk_query_penalty" in cbk_trace["document_rerank_reason"]
        assert "relation_supporting_source_penalty" in cbk_trace["document_rerank_reason"]

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
            selected_source_keys={"ik"},
        )

        assert prioritized[0].citation == "IK m.21/f.0"

    def test_focus_chunks_on_metadata_selected_source_before_same_family_dense_hits(self):
        chunks = [
            RetrievedChunk(
                text="Bursa yatırımı için proje bazlı destek.",
                citation="4924 m.9/f.0",
                source="4924",
                score=0.99,
                metadata={
                    "source_title": "BURSA İLİNDE YAPILACAK OLAN BATARYA HÜCRESİ VE MODÜL ÜRETİM TESİSİ YATIRIMINA PROJE BAZLI DEVLET YARDIMI VERİLMESİNE İLİŞKİN KARAR (KARAR SAYISI: 4924)",
                    "belge_turu": "cb_karar",
                    "decision_number": "4924",
                    "madde_no": "9",
                },
            ),
            RetrievedChunk(
                text="Yatırım teşvik belgesi ve geçiş hükümleri.",
                citation="9903 m.1/f.0",
                source="9903",
                score=0.42,
                metadata={
                    "source_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR (KARAR SAYISI: 9903)",
                    "belge_turu": "cb_karar",
                    "decision_number": "9903",
                    "madde_no": "1",
                },
            ),
            RetrievedChunk(
                text="Yatırım teşvik kararının genel çerçevesi.",
                citation="9903 m.0/f.0",
                source="9903",
                score=0.40,
                metadata={
                    "source_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR (KARAR SAYISI: 9903)",
                    "belge_turu": "cb_karar",
                    "decision_number": "9903",
                    "madde_no": "0",
                },
            ),
            RetrievedChunk(
                text="Başka bir proje bazlı karar.",
                citation="1593 m.2/f.0",
                source="1593",
                score=0.95,
                metadata={
                    "source_title": "YATIRIMLARA PROJE BAZLI DEVLET YARDIMI VERİLMESİNE İLİŞKİN KARARDA DEĞİŞİKLİK YAPILMASINA DAİR KARAR (KARAR SAYISI: 1593)",
                    "belge_turu": "cb_karar",
                    "decision_number": "1593",
                    "madde_no": "2",
                },
            ),
        ]

        prioritized = _prioritize_chunks_for_source_families(
            query="Yeni 9903 sayılı karar mı uygulanır?",
            chunks=chunks,
            source_families=["cb_karar"],
            selected_source_keys={"9903"},
        )
        focused = _focus_chunks_on_selected_sources(
            chunks=prioritized,
            selected_source_keys={"9903"},
        )

        assert focused[0].citation == "9903 m.1/f.0"
        assert focused[1].citation == "9903 m.0/f.0"

    def test_focus_chunks_matches_document_key_when_source_key_is_article_scoped(self):
        chunks = [
            RetrievedChunk(
                text="Başka kararın yüksek skorlu hükmü.",
                citation="4924 m.9/f.0",
                source="4924",
                score=0.99,
                metadata={
                    "source_title": "BAŞKA KARAR (KARAR SAYISI: 4924)",
                    "belge_turu": "cb_karar",
                    "decision_number": "4924",
                    "canonical_identifier_display": "4924 m.9",
                    "madde_no": "9",
                },
            ),
            RetrievedChunk(
                text="9903 sayılı kararın geçiş hükmü.",
                citation="9903 m.1/f.0",
                source="9903",
                score=0.40,
                metadata={
                    "source_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR (KARAR SAYISI: 9903)",
                    "belge_turu": "cb_karar",
                    "decision_number": "9903",
                    "canonical_identifier_display": "9903 m.1",
                    "madde_no": "1",
                },
            ),
        ]

        prioritized = _prioritize_chunks_for_source_families(
            query="Yeni 9903 sayılı karar mı uygulanır?",
            chunks=chunks,
            source_families=["cb_karar"],
            selected_source_keys={"9903"},
        )
        focused = _focus_chunks_on_selected_sources(
            chunks=prioritized,
            selected_source_keys={"9903"},
        )

        assert focused[0].citation == "9903 m.1/f.0"

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

    def test_article_span_selector_builds_source_local_adjacent_window_metrics(self):
        chunks = [
            RetrievedChunk(
                text="Başka kaynakta madde 12 benzer konuyu düzenler.",
                citation="2547 m.12/f.0",
                source="2547",
                score=0.99,
                metadata={"source_title": "YÜKSEKÖĞRETİM KANUNU", "belge_turu": "kanun", "madde_no": "12"},
            ),
            RetrievedChunk(
                text="Tez danışmanı atanması madde 12 kapsamında düzenlenir.",
                citation="40969 m.12/f.0",
                source="40969",
                score=0.80,
                metadata={
                    "source_title": "KIRKLARELİ ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ",
                    "belge_turu": "uy",
                    "law_no": "40969",
                    "madde_no": "12",
                    "effective_state": "active",
                },
            ),
            RetrievedChunk(
                text="Tez izleme ve danışmanlık desteği madde 13 kapsamında devam eder.",
                citation="40969 m.13/f.0",
                source="40969",
                score=0.70,
                metadata={
                    "source_title": "KIRKLARELİ ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ",
                    "belge_turu": "uy",
                    "law_no": "40969",
                    "madde_no": "13",
                    "effective_state": "active",
                },
            ),
        ]

        selected, selector = _select_article_span_evidence(
            query="40969 sayılı üniversite yönetmeliğinin 12. maddesinde tez danışmanı nasıl düzenlenir?",
            chunks=chunks,
            requested_source_families=["uy", "yonetmelik"],
            explicit_article_refs=[],
            selected_source_keys={"40969"},
        )

        assert selected[0].citation == "40969 m.12/f.0"
        assert selected[1].citation == "40969 m.13/f.0"
        assert selector["selector_exact_article_hit"] is True
        assert selector["selector_article_rank"] == 1
        assert selector["selector_support_span_count"] >= 2
        assert selector["support_span_count"] >= 2
        assert selector["support_span_diversity"] >= 2
        assert selector["support_contains_article_number"] is True
        assert selector["selected_document_id"]
        assert selector["selected_article"] == "12"
        assert selector["article_match_type"] == "exact"
        assert selector["selector_article_lock_type"] == "explicit_exact"
        assert selector["query_article_alignment"] == "exact"
        assert selector["selector_reason"] == "selected_source_lock"
        assert selector["selector_evidence_sufficiency"] == "exact_enough"
        assert selector["metadata_identity_strength"] == "strong"
        assert selector["temporal_state_resolved"] is True
        assert selector["manual_review_trigger_reason"] == ""

    def test_article_span_selector_demotes_title_only_article_zero_for_article_query(self):
        chunks = [
            RetrievedChunk(
                text="Yönetmeliğin başlık ve genel tanıtım metni.",
                citation="40969 m.0/f.0",
                source="40969",
                score=0.99,
                metadata={
                    "source_title": "KIRKLARELİ ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ",
                    "belge_turu": "uy",
                    "law_no": "40969",
                    "madde_no": "0",
                },
            ),
            RetrievedChunk(
                text="Tez danışmanı atanması madde 12 kapsamında düzenlenir.",
                citation="40969 m.12/f.0",
                source="40969",
                score=0.70,
                metadata={
                    "source_title": "KIRKLARELİ ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ",
                    "belge_turu": "uy",
                    "law_no": "40969",
                    "madde_no": "12",
                },
            ),
        ]

        selected, selector = _select_article_span_evidence(
            query="40969 sayılı yönetmeliğin 12. maddesine göre tez danışmanı nasıl atanır?",
            chunks=chunks,
            requested_source_families=["uy", "yonetmelik"],
            explicit_article_refs=[],
        )

        assert selected[0].citation == "40969 m.12/f.0"
        assert selector["article_match_type"] == "exact"
        assert selector["selector_article_lock_type"] == "explicit_exact"
        assert selector["query_article_alignment"] == "exact"
        assert selector["selected_article"] == "12"

    def test_article_span_selector_demotes_title_only_inside_locked_document_without_article_query(self):
        chunks = [
            RetrievedChunk(
                text="9903 sayılı yatırım teşvik kararının başlık ve genel tanıtım metni.",
                citation="9903 m.0/f.0",
                source="9903",
                score=0.99,
                metadata={
                    "source_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR (KARAR SAYISI: 9903)",
                    "belge_turu": "cb_karar",
                    "decision_number": "9903",
                    "madde_no": "0",
                },
            ),
            RetrievedChunk(
                text="Faiz desteği ve yatırım teşvik şartları bu maddede düzenlenir.",
                citation="9903 m.8/f.0",
                source="9903",
                score=0.70,
                metadata={
                    "source_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR (KARAR SAYISI: 9903)",
                    "belge_turu": "cb_karar",
                    "decision_number": "9903",
                    "madde_no": "8",
                },
            ),
        ]

        selected, selector = _select_article_span_evidence(
            query="9903 sayılı yatırım teşvik kararında faiz desteği şartı nedir?",
            chunks=chunks,
            requested_source_families=["cb_karar"],
            explicit_article_refs=[],
            selected_source_keys={"9903"},
        )

        assert selected[0].citation == "9903 m.8/f.0"
        assert selector["selected_main_span_id"] == "9903 m.8/f.0"
        assert selector["selected_main_article"] == "8"
        assert selector["main_span_match_type"] == "same_heading_or_section"
        assert selector["article_precision_guard_triggered"] is True

    def test_article_span_selector_suppresses_cross_document_noise_after_exact_lock(self):
        chunks = [
            RetrievedChunk(
                text="Başka kararın aynı maddesi yatırım programına ilişkindir.",
                citation="1593 m.8/f.0",
                source="1593",
                score=0.99,
                metadata={
                    "source_title": "PROJE BAZLI DEVLET YARDIMI KARARI (KARAR SAYISI: 1593)",
                    "belge_turu": "cb_karar",
                    "decision_number": "1593",
                    "madde_no": "8",
                },
            ),
            RetrievedChunk(
                text="9903 sayılı kararda faiz desteği şartları madde 8 altında düzenlenir.",
                citation="9903 m.8/f.0",
                source="9903",
                score=0.74,
                metadata={
                    "source_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR (KARAR SAYISI: 9903)",
                    "belge_turu": "cb_karar",
                    "decision_number": "9903",
                    "madde_no": "8",
                },
            ),
            RetrievedChunk(
                text="9903 sayılı kararın yürürlük hükmü ve istisnaları saklıdır.",
                citation="9903 m.30/f.0",
                source="9903",
                score=0.60,
                metadata={
                    "source_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR (KARAR SAYISI: 9903)",
                    "belge_turu": "cb_karar",
                    "decision_number": "9903",
                    "madde_no": "30",
                },
            ),
        ]

        selected, selector = _select_article_span_evidence(
            query="9903 sayılı kararın 8. maddesine göre faiz desteği şartı nedir?",
            chunks=chunks,
            requested_source_families=["cb_karar"],
            explicit_article_refs=[],
            selected_source_keys={"9903"},
        )

        assert selected[0].citation == "9903 m.8/f.0"
        assert selected[1].citation == "9903 m.30/f.0"
        assert selector["selected_document_key"] == "9903"
        assert selector["selected_supporting_span_ids"] == ["9903 m.30/f.0"]
        assert selector["supporting_span_match_types"] == ["same_heading_or_section"]
        assert selector["span_cluster_noise_suppressed"] is True

    def test_article_span_selector_matches_selected_source_by_document_key_not_article_display(self):
        chunks = [
            RetrievedChunk(
                text="Tez danışmanı öğrencinin programına göre atanır.",
                citation="40969 m.12/f.0",
                source="40969",
                score=0.72,
                metadata={
                    "source_title": "KIRKLARELİ ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ",
                    "belge_turu": "uy",
                    "law_no": "40969",
                    "canonical_identifier_display": "40969 m.12",
                    "madde_no": "12",
                },
            )
        ]

        selected, selector = _select_article_span_evidence(
            query="40969 sayılı yönetmeliğe göre tez danışmanı nasıl atanır?",
            chunks=chunks,
            requested_source_families=["uy"],
            explicit_article_refs=[],
            selected_source_keys={"40969"},
        )

        assert selected[0].citation == "40969 m.12/f.0"
        assert selector["selected_document_key"] == "40969"
        assert selector["top_scores"][0]["selected_source_match"] is True
        assert selector["metadata_identity_strength"] == "strong"

    def test_selected_document_only_bundle_filters_generation_chunks_after_strong_lock(self):
        chunks = [
            RetrievedChunk(
                text="9903 sayılı kararda faiz desteği şartları madde 8 altında düzenlenir.",
                citation="9903 m.8/f.0",
                source="9903",
                score=0.74,
                metadata={
                    "source_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR (KARAR SAYISI: 9903)",
                    "belge_turu": "cb_karar",
                    "decision_number": "9903",
                    "madde_no": "8",
                },
            ),
            RetrievedChunk(
                text="Başka kararın yatırım programı hükmü.",
                citation="1593 m.8/f.0",
                source="1593",
                score=0.99,
                metadata={
                    "source_title": "PROJE BAZLI DEVLET YARDIMI KARARI (KARAR SAYISI: 1593)",
                    "belge_turu": "cb_karar",
                    "decision_number": "1593",
                    "madde_no": "8",
                },
            ),
        ]
        selector = {
            "selected_document_key": "9903",
            "selector_evidence_sufficiency": "exact_enough",
            "metadata_identity_strength": "strong",
            "selector_reason": "selected_source_lock",
            "identifier_tokens": ["9903"],
            "span_cluster_noise_suppressed_count": 0,
        }

        filtered = _apply_selected_document_only_bundle(
            chunks=chunks,
            article_span_selector=selector,
        )

        assert [chunk.citation for chunk in filtered] == ["9903 m.8/f.0"]
        assert selector["selected_document_only_bundle"] is True
        assert selector["selected_document_bundle_suppressed_count"] == 1
        assert selector["span_cluster_noise_suppressed"] is True

    def test_selected_document_only_bundle_skips_relation_queries(self):
        chunks = [
            RetrievedChunk(
                text="Kanun hükmü.",
                citation="7201 m.7/a/f.0",
                source="7201",
                score=0.80,
                metadata={"belge_turu": "kanun", "belge_no": "7201", "madde_no": "7/a"},
            ),
            RetrievedChunk(
                text="Yönetmelik destek hükmü.",
                citation="20631 m.11/f.0",
                source="20631",
                score=0.70,
                metadata={"belge_turu": "yonetmelik", "belge_no": "20631", "madde_no": "11"},
            ),
        ]
        selector = {
            "selected_document_key": "7201",
            "selector_evidence_sufficiency": "exact_enough",
            "metadata_identity_strength": "strong",
            "selector_reason": "selected_source_lock",
            "relation_query_detected": True,
        }

        filtered = _apply_selected_document_only_bundle(
            chunks=chunks,
            article_span_selector=selector,
        )

        assert filtered == chunks
        assert selector["selected_document_only_bundle"] is False
        assert selector["selected_document_bundle_skip_reason"] == "relation_query_requires_supporting_sources"

    def test_canonical_span_materialization_marks_title_only_collision_as_corpus_blocker(self):
        chunks = [
            RetrievedChunk(
                text="9903 m.0/f.0\n" + ("\x00" * 96),
                citation="9903 m.0/f.0",
                source="9903",
                score=0.99,
                metadata={
                    "belge_turu": "cb_karar",
                    "belge_no": "9903",
                    "source_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR",
                    "madde_no": "0",
                },
            )
        ]
        selector = {
            "selected_document_key": "9903",
            "selected_main_span_id": "9903 m.0/f.0",
            "selected_article": "0",
            "main_span_match_type": "title_only",
            "support_span_count": 1,
        }

        _annotate_canonical_span_materialization(
            chunks=chunks,
            article_span_selector=selector,
            family_routing_policy={
                "source_key_collision_detected": True,
                "source_key_collision_keys": ["9903"],
                "source_key_collision_pair": "9903=cb_karar:yatirim|teblig:garanti",
            },
        )

        assert selector["canonical_span_materialized"] is False
        assert selector["canonical_span_materialization_reason"] == "source_key_collision_without_family_body_span"
        assert selector["title_only_fallback_used"] is True
        assert selector["body_text_available"] is False
        assert selector["corpus_materialization_required"] is True
        assert selector["source_key_collision_detected"] is True
        assert selector["selected_document_has_body_span"] is False
        assert selector["selected_document_has_non_title_span"] is False
        assert selector["title_only_answer_degraded"] is True
        assert selector["insufficient_canonical_span_evidence"] is True

    def test_canonical_span_materialization_accepts_non_title_body_span(self):
        chunks = [
            RetrievedChunk(
                text=(
                    "9903 m.8/f.0\n"
                    "Faiz desteği, yatırım teşvik belgesi kapsamındaki yatırımlar için "
                    "kararda belirtilen koşullar gerçekleştiğinde uygulanır."
                ),
                citation="9903 m.8/f.0",
                source="9903",
                score=0.99,
                metadata={
                    "belge_turu": "cb_karar",
                    "belge_no": "9903",
                    "source_title": "YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR",
                    "madde_no": "8",
                },
            )
        ]
        selector = {
            "selected_document_key": "9903",
            "selected_main_span_id": "9903 m.8/f.0",
            "selected_article": "8",
            "main_span_match_type": "same_heading_or_section",
            "support_span_count": 1,
        }

        _annotate_canonical_span_materialization(
            chunks=chunks,
            article_span_selector=selector,
            family_routing_policy={},
        )

        assert selector["canonical_span_materialized"] is True
        assert selector["canonical_span_materialization_reason"] == "non_title_body_span_available"
        assert selector["title_only_fallback_used"] is False
        assert selector["body_text_available"] is True
        assert selector["corpus_materialization_required"] is False
        assert selector["candidate_completeness_score"] >= 0.75
        assert selector["selected_document_has_non_title_span"] is True
        assert selector["insufficient_canonical_span_evidence"] is False

    def test_canonical_span_materialization_accepts_readable_body_with_low_control_ratio(self):
        readable = (
            "MADDE 2 - Bu Karar ekinde yer alan yatırım programındaki projelerin "
            "parametre değişikliği, programa proje alınması veya çıkarılması ve "
            "ödenek tahsisi işlemleri yetkili kurumlarca yürütülür. "
        ) * 12
        chunks = [
            RetrievedChunk(
                text="767 m.2/f.0\n" + readable + ("\x00" * 90),
                citation="767 m.2/f.0",
                source="767",
                score=0.99,
                metadata={
                    "belge_turu": "cb_karar",
                    "belge_no": "767",
                    "source_title": "2019 YILI YATIRIM PROGRAMININ KABULÜ VE UYGULANMASINA DAİR KARAR",
                    "madde_no": "2",
                },
            )
        ]
        selector = {
            "selected_document_key": "767",
            "selected_main_span_id": "767 m.2/f.0",
            "selected_article": "2",
            "main_span_match_type": "same_heading_or_section",
            "support_span_count": 1,
        }

        _annotate_canonical_span_materialization(
            chunks=chunks,
            article_span_selector=selector,
            family_routing_policy={},
        )

        assert selector["body_text_available"] is True
        assert selector["canonical_span_materialized"] is True
        assert selector["corpus_materialization_required"] is False
        assert selector["insufficient_canonical_span_evidence"] is False

    def test_article_span_selector_uses_document_lock_before_cross_document_article_hit(self):
        chunks = [
            RetrievedChunk(
                text="Başka bir kanunda madde 12 yer alır.",
                citation="2547 m.12/f.0",
                source="2547",
                score=0.99,
                metadata={"source_title": "YÜKSEKÖĞRETİM KANUNU", "belge_turu": "kanun", "madde_no": "12"},
            ),
            RetrievedChunk(
                text="Üniversite yönetmeliğinde tez danışmanı madde 27 altında düzenlenir.",
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
            query="Üniversite yönetmeliğine göre tez danışmanı hangi maddede düzenlenir?",
            chunks=chunks,
            requested_source_families=["uy", "yonetmelik"],
            explicit_article_refs=[],
        )

        assert selected[0].citation == "40969 m.27/f.0"
        assert "kirklareli" in selector["selected_document_id"].replace("İ", "i").replace("I", "i").lower()
        assert selector["selector_reason"] == "preferred_family_lock"
        assert selector["article_match_type"] == "source_local_support"
        assert selector["selector_article_lock_type"] == "semantic_exact"
        assert selector["selector_exact_article_hit"] is True
        assert selector["query_article_alignment"] == "unknown"

    def test_article_span_selector_prefers_specific_family_inside_broad_yonetmelik_alias(self):
        chunks = [
            RetrievedChunk(
                text="Genel yönetmelikte tez danışmanı için farklı bir kurul usulü anlatılır.",
                citation="GENEL-YON m.27/f.0",
                source="GENEL-YON",
                score=0.99,
                metadata={
                    "source_title": "GENEL BİR YÖNETMELİK",
                    "belge_turu": "yonetmelik",
                    "madde_no": "27",
                },
            ),
            RetrievedChunk(
                text="Üniversite lisansüstü yönetmeliğinde tez danışmanı öğrencinin çalışmasına göre atanır.",
                citation="40969 m.12/f.0",
                source="40969",
                score=0.50,
                metadata={
                    "source_title": "KIRKLARELİ ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ",
                    "belge_turu": "uy",
                    "madde_no": "12",
                },
            ),
        ]

        selected, selector = _select_article_span_evidence(
            query="Üniversite yüksek lisans yönetmeliğine göre tez danışmanı nasıl atanır?",
            chunks=chunks,
            requested_source_families=["yonetmelik"],
            explicit_article_refs=[],
        )

        assert selected[0].citation == "40969 m.12/f.0"
        assert selector["preferred_source_families"] == ["uy"]
        assert selector["selector_preferred_family_hit"] is True
        assert selector["selector_reason"] == "preferred_family_lock"
        assert selector["top_scores"][0]["source_family"] == "uy"

    def test_article_span_selector_marks_semantic_exact_when_question_has_no_article_number(self):
        chunks = [
            RetrievedChunk(
                text="Tez danışmanı, öğrencinin programı ve çalışmanın niteliği dikkate alınarak atanır.",
                citation="40969 m.12/f.0",
                source="40969",
                score=0.88,
                metadata={
                    "source_title": "KIRKLARELİ ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ",
                    "belge_turu": "uy",
                    "law_no": "40969",
                    "madde_no": "12",
                    "effective_state": "active",
                },
            ),
            RetrievedChunk(
                text="Tez danışmanlığına ilişkin ek kurul usulleri aynı yönetmelikte düzenlenir.",
                citation="40969 m.13/f.0",
                source="40969",
                score=0.74,
                metadata={
                    "source_title": "KIRKLARELİ ÜNİVERSİTESİ LİSANSÜSTÜ EĞİTİM VE ÖĞRETİM YÖNETMELİĞİ",
                    "belge_turu": "uy",
                    "law_no": "40969",
                    "madde_no": "13",
                    "effective_state": "active",
                },
            ),
        ]

        selected, selector = _select_article_span_evidence(
            query="Kırklareli Üniversitesi lisansüstü yönetmeliğine göre tez danışmanı nasıl atanır?",
            chunks=chunks,
            requested_source_families=["uy", "yonetmelik"],
            explicit_article_refs=[],
            selected_source_keys={"40969"},
        )

        assert selected[0].citation == "40969 m.12/f.0"
        assert selector["selected_article"] == "12"
        assert selector["query_article_alignment"] == "unknown"
        assert selector["selector_article_lock_type"] == "semantic_exact"
        assert selector["selector_exact_article_hit"] is True
        assert selector["support_contains_article_number"] is True
        assert selector["support_span_diversity"] >= 1
        assert selector["selector_evidence_sufficiency"] == "exact_enough"

    def test_article_span_selector_prioritizes_scope_article_for_applicability_query(self):
        chunks = [
            RetrievedChunk(
                text="Yetki belgesi sahiplerinin bildirim yükümlülükleri ve belge yenileme usulü açıklanır.",
                citation="32695 m.5/f.0",
                source="32695",
                score=0.99,
                metadata={
                    "source_title": "ELEKTRONİK HABERLEŞME SEKTÖRÜNE İLİŞKİN YETKİLENDİRME YÖNETMELİĞİ",
                    "belge_turu": "kky",
                    "belge_no": "32695",
                    "madde_no": "5",
                    "heading": "Yetki belgesi",
                    "effective_state": "active",
                },
            ),
            RetrievedChunk(
                text="Kapsam MADDE 2 - Bu Yönetmelik yetki belgesi sahipleri hakkında uygulanır ve ilgili faaliyetleri kapsar.",
                citation="32695 m.2/f.0",
                source="32695",
                score=0.45,
                metadata={
                    "source_title": "ELEKTRONİK HABERLEŞME SEKTÖRÜNE İLİŞKİN YETKİLENDİRME YÖNETMELİĞİ",
                    "belge_turu": "kky",
                    "belge_no": "32695",
                    "madde_no": "2",
                    "heading": "Kapsam",
                    "effective_state": "active",
                },
            ),
        ]

        selected, selector = _select_article_span_evidence(
            query="İnternet yayın lisansı ve iletim yetkisi bakımından hangi RTÜK yönetmeliği aranmalıdır?",
            chunks=chunks,
            requested_source_families=["kky", "yonetmelik"],
            explicit_article_refs=[],
            selected_source_keys={"32695"},
        )

        assert selected[0].citation == "32695 m.2/f.0"
        assert selector["selected_main_article"] == "2"
        assert selector["main_span_match_type"] == "scope_or_applicability"
        assert selector["article_match_type"] == "scope_or_applicability"
        assert selector["top_scores"][0]["scope_match"] is True

    def test_article_span_selector_surfaces_temporal_and_exception_support_metrics(self):
        chunks = [
            RetrievedChunk(
                text="Bu yönetmelik yürürlüğe girer; istisna hükümleri ve başvuru süresi ayrıca saklıdır.",
                citation="12345 m.5/f.0",
                source="12345",
                score=0.80,
                metadata={
                    "source_title": "ÖRNEK YÖNETMELİK",
                    "belge_turu": "yonetmelik",
                    "law_no": "12345",
                    "madde_no": "5",
                    "effective_state": "active",
                },
            )
        ]

        _selected, selector = _select_article_span_evidence(
            query="Örnek yönetmelikte yürürlük ve istisna hükümleri nasıl düzenlenir?",
            chunks=chunks,
            requested_source_families=["yonetmelik"],
            explicit_article_refs=[],
        )

        assert selector["support_contains_temporal_clause"] is True
        assert selector["support_contains_exception_signal"] is True

    def test_article_span_selector_surfaces_insufficient_support_metrics(self):
        chunks = [
            RetrievedChunk(
                text="Genel kanun hükmü.",
                citation="2547 m.12/f.0",
                source="2547",
                score=0.90,
                metadata={"source_title": "YÜKSEKÖĞRETİM KANUNU", "belge_turu": "kanun", "madde_no": "12"},
            ),
        ]

        selected, selector = _select_article_span_evidence(
            query="Üniversite yönetmeliğine göre tez danışmanı hangi maddede düzenlenir?",
            chunks=chunks,
            requested_source_families=["uy"],
            explicit_article_refs=[],
        )

        assert selected[0].citation == "2547 m.12/f.0"
        assert selector["selector_evidence_sufficiency"] == "insufficient_support"
        assert selector["metadata_identity_strength"] == "weak"
        assert selector["selector_article_lock_type"] == "none"
        assert selector["selector_exact_article_hit"] is False
        assert selector["manual_review_trigger_reason"] == "insufficient_selector_support"

    def test_article_span_selector_demotes_repealed_candidate_when_active_kanun_exists(self):
        query = "İşveren performans gerekçesiyle işçiyi işten çıkarırsa işe iade davası açılabilir mi?"
        chunks = [
            RetrievedChunk(
                text="İşe iade başvurusu eski düzenlemede farklı sonuçlara bağlanır.",
                citation="1475 m.98/f.0",
                source="1475",
                score=0.98,
                metadata={
                    "source_title": "İŞ KANUNUNUN YÜRÜRLÜKTEN KALDIRILMIŞ HÜKÜMLERİ",
                    "belge_turu": "mulga_kanun",
                    "belge_no": "1475",
                    "madde_no": "98",
                    "effective_state": "repealed",
                    "mulga": True,
                    "yururluk_bitis": "2003-06-10",
                },
            ),
            RetrievedChunk(
                text="Geçersiz nedenle yapılan fesihte işçi işe iade talep edebilir.",
                citation="4857 m.21/f.0",
                source="4857",
                score=0.74,
                metadata={
                    "source_title": "İŞ KANUNU",
                    "belge_turu": "kanun",
                    "belge_no": "4857",
                    "madde_no": "21",
                    "effective_state": "active",
                    "mulga": False,
                    "yururluk_baslangic": "2003-06-10",
                    "yururluk_bitis": "9999-12-31",
                },
            ),
        ]

        selected, selector = _select_article_span_evidence(
            query=query,
            chunks=chunks,
            requested_source_families=["kanun"],
            explicit_article_refs=[],
            selected_source_keys={"1475"},
            source_family_resolution=_resolve_source_family_prior(query),
        )

        assert selected[0].citation == "4857 m.21/f.0"
        assert "kanunu" in str(selector["selected_document_id"]).lower()
        assert selector["selector_reason"] == "current_law_temporal_guard"
        assert selector["scenario_current_law_question"] is True
        assert selector["active_candidate_available"] is True
        assert selector["repealed_candidate_demoted"] is True
        assert selector["temporal_family_guard_triggered"] is True

    def test_article_span_selector_prefers_primary_kanun_for_relation_query(self):
        query = (
            "Elektronik tebligat muhatabın elektronik adresine ulaştığı anda mı, "
            "yoksa daha sonraki bir tarihte mi tebliğ edilmiş sayılır? "
            "Kanun ve yönetmelik ilişkisini de göster."
        )
        chunks = [
            RetrievedChunk(
                text="Elektronik tebligat yönetmeliğinde iletim kayıtları ayrıca düzenlenir.",
                citation="20631 m.11/f.0",
                source="20631",
                score=0.97,
                metadata={
                    "source_title": "ELEKTRONİK TEBLİGAT YÖNETMELİĞİ",
                    "belge_turu": "yonetmelik",
                    "belge_no": "20631",
                    "madde_no": "11",
                    "effective_state": "active",
                },
            ),
            RetrievedChunk(
                text="Elektronik tebligatın tebliğ edilmiş sayılması Tebligat Kanununda düzenlenir.",
                citation="7201 m.7/a/f.0",
                source="7201",
                score=0.78,
                metadata={
                    "source_title": "TEBLİGAT KANUNU",
                    "belge_turu": "kanun",
                    "belge_no": "7201",
                    "madde_no": "7/a",
                    "effective_state": "active",
                },
            ),
        ]

        selected, selector = _select_article_span_evidence(
            query=query,
            chunks=chunks,
            requested_source_families=["kanun", "yonetmelik"],
            explicit_article_refs=[],
            source_family_resolution=_resolve_source_family_prior(query),
        )

        assert selected[0].citation == "7201 m.7/a/f.0"
        assert selector["relation_query_detected"] is True
        assert "kanunu" in selector["primary_source_candidate"].replace("i̇", "i").lower()
        assert "YÖNETMELİĞİ" in selector["supporting_source_candidate"]

    def test_article_span_selector_prefers_legacy_khk_inside_locked_family(self):
        query = "Eski KHK'larla 2026'da doğrudan hüküm kurmak neden risklidir?"
        chunks = [
            RetrievedChunk(
                text="Bu Kanun Hükmünde Kararname nükleer düzenleme kurumuna ilişkindir.",
                citation="702 m.1/f.0",
                source="702",
                score=0.95,
                metadata={
                    "source_title": "NÜKLEER DÜZENLEME KURUMUNUN TEŞKİLAT VE GÖREVLERİ HAKKINDA KANUN HÜKMÜNDE KARARNAME",
                    "belge_turu": "kanun",
                    "belge_no": "702",
                    "madde_no": "1",
                    "effective_state": "active",
                    "yururluk_baslangic": "2018-07-09",
                    "yururluk_bitis": "9999-12-31",
                },
            ),
            RetrievedChunk(
                text="Patent haklarının korunmasına ilişkin eski KHK hükmüdür.",
                citation="551 m.1/f.0",
                source="551",
                score=0.71,
                metadata={
                    "source_title": "PATENT HAKLARININ KORUNMASI HAKKINDA KANUN HÜKMÜNDE KARARNAME",
                    "belge_turu": "kanun",
                    "belge_no": "551",
                    "madde_no": "1",
                    "effective_state": "active",
                    "yururluk_baslangic": "1995-06-27",
                    "yururluk_bitis": "9999-12-31",
                },
            ),
        ]

        selected, selector = _select_article_span_evidence(
            query=query,
            chunks=chunks,
            requested_source_families=["khk"],
            explicit_article_refs=[],
            source_family_resolution=_resolve_source_family_prior(query),
        )

        assert selected[0].citation == "551 m.1/f.0"
        assert selector["legacy_intent_binding_active"] is True
        assert selector["legacy_candidate_preferred"] is True
        assert selector["internal_document_state_rank"] == 0
        assert "patent haklarinin korunmasi hakkinda kanun hükmünde kararname" in selector[
            "selected_document_id"
        ].replace("i̇", "i").lower()

    def test_article_span_selector_prefers_703_for_constitutional_transition_khk_query(self):
        query = (
            "Mevzuat hâlâ Bakanlar Kurulu veya eski teşkilat isimlerine atıf yapıyorsa, "
            "Cumhurbaşkanlığı Hükümet Sistemine geçiş bakımından hangi KHK ve hangi CBK bağlantısı kontrol edilmelidir?"
        )
        chunks = [
            RetrievedChunk(
                text="Kamu gözetimi kurumunun teşkilat hükümleri düzenlenir.",
                citation="660 m.14/f.0",
                source="660",
                score=0.95,
                metadata={
                    "source_title": "KAMU GÖZETİMİ, MUHASEBE VE DENETİM STANDARTLARI KURUMUNUN TEŞKİLAT VE GÖREVLERİ HAKKINDA KANUN HÜKMÜNDE KARARNAME",
                    "belge_turu": "khk",
                    "kanun_no": "660",
                    "madde_no": "14",
                    "effective_state": "active",
                },
            ),
            RetrievedChunk(
                text="Bakanlar Kurulu ve eski teşkilat atıflarının Cumhurbaşkanlığı sistemine uyarlanmasına ilişkin geçiş hükümleri yer alır.",
                citation="703 m.216/f.0",
                source="703",
                score=0.40,
                metadata={
                    "source_title": "ANAYASADA YAPILAN DEĞİŞİKLİKLERE UYUM SAĞLANMASI AMACIYLA BAZI KANUN VE KANUN HÜKMÜNDE KARARNAMELERDE DEĞİŞİKLİK YAPILMASI HAKKINDA KANUN HÜKMÜNDE KARARNAME",
                    "belge_turu": "khk",
                    "kanun_no": "703",
                    "madde_no": "216",
                    "effective_state": "active",
                },
            ),
        ]

        selected, selector = _select_article_span_evidence(
            query=query,
            chunks=chunks,
            requested_source_families=["khk"],
            explicit_article_refs=[],
            source_family_resolution=_resolve_source_family_prior(query),
        )

        assert selected[0].citation == "703 m.216/f.0"
        assert selector["legacy_candidate_preferred"] is True
        assert "constitutional_transition_khk_703_anchor" in selector["top_scores"][0]["document_state_binding_reason"]

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
