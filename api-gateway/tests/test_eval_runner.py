"""Unit tests — Evaluation Runner + Metrics (Backlog #8).

Kapsanan alanlar:
    - metrics.py: normalize_source, sources_overlap, detect_hallucination,
                  detect_refusal, keyword_coverage, compute_metrics, aggregate_metrics
    - eval_runner.py: MockChatClient, run_evaluation (mock mod)

Çalıştırma:
    cd api-gateway && .venv/bin/pytest tests/test_eval_runner.py -v
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path
from types import SimpleNamespace

import pytest

# ── sys.path: evaluation/ ve api-gateway/src/ ──────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.parent
EVAL_DIR = PROJECT_ROOT / "evaluation"
sys.path.insert(0, str(EVAL_DIR))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from metrics import (
    normalize_source,
    sources_overlap,
    detect_hallucination,
    detect_refusal,
    keyword_coverage,
    phrase_hit,
    compute_metrics,
    aggregate_metrics,
    QuestionResult,
)
from eval_runner import MockChatClient, build_report, run_evaluation
from eval_runner import ChatAPIClient


# ===========================================================================
# Fixture: örnek soru dict'leri
# ===========================================================================

@pytest.fixture
def tbk_question() -> dict:
    return {
        "id": "TBK-001",
        "question": "Sözleşme nasıl kurulur?",
        "category": "tbk_genel",
        "difficulty": "easy",
        "expected_sources": ["TBK m.1", "TBK m.2"],
        "expected_keywords": ["icap", "kabul", "irade"],
        "expected_answer_contains": "icap ve kabul",
        "refusal_expected": False,
        "notes": "Test",
    }


@pytest.fixture
def out_of_scope_question() -> dict:
    return {
        "id": "TBK-018",
        "question": "Kıdem tazminatı nasıl hesaplanır?",
        "category": "out_of_scope",
        "difficulty": "medium",
        "expected_sources": [],
        "expected_keywords": ["kıdem tazminatı", "4857"],
        "expected_answer_contains": None,
        "refusal_expected": True,
        "notes": "Refusal bekleniyor",
    }


@pytest.fixture
def questions_file(tmp_path) -> Path:
    """Geçici test_questions.json oluştur."""
    data = {
        "_meta": {"version": "1.0.0"},
        "questions": [
            {
                "id": "TEST-001",
                "question": "TBK m.1 nedir?",
                "category": "tbk_genel",
                "difficulty": "easy",
                "expected_sources": ["TBK m.1"],
                "expected_keywords": ["icap", "kabul"],
                "expected_answer_contains": "icap",
                "refusal_expected": False,
                "notes": "",
            },
            {
                "id": "TEST-002",
                "question": "Anonim şirket sermayesi nedir?",
                "category": "out_of_scope",
                "difficulty": "easy",
                "expected_sources": [],
                "expected_keywords": [],
                "expected_answer_contains": None,
                "refusal_expected": True,
                "notes": "Kapsam dışı",
            },
        ],
    }
    p = tmp_path / "test_questions.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


# ===========================================================================
# normalize_source
# ===========================================================================

class TestNormalizeSource:
    def test_basic(self):
        assert normalize_source("TBK m.1") == "tbk m.1"

    def test_with_space(self):
        assert normalize_source("TBK m. 299") == "tbk m.299"

    def test_madde_keyword(self):
        assert "m." in normalize_source("TBK Madde 146")

    def test_dash_format(self):
        result = normalize_source("TBK-299")
        assert "299" in result
        assert "tbk" in result

    def test_lowercase_input(self):
        assert normalize_source("tbk m.1") == "tbk m.1"

    def test_strip_whitespace(self):
        assert normalize_source("  TBK m.1  ") == "tbk m.1"


# ===========================================================================
# sources_overlap
# ===========================================================================

class TestSourcesOverlap:
    def test_exact_match(self):
        overlap, total = sources_overlap(["TBK m.1"], ["TBK m.1"])
        assert overlap == 1
        assert total == 1

    def test_no_match(self):
        overlap, total = sources_overlap(["TBK m.5"], ["TBK m.1"])
        assert overlap == 0

    def test_partial_match(self):
        overlap, total = sources_overlap(["TBK m.1", "TBK m.5"], ["TBK m.1", "TBK m.2"])
        assert overlap == 1
        assert total == 2

    def test_empty_expected(self):
        overlap, total = sources_overlap(["TBK m.1"], [])
        assert total == 0

    def test_empty_cited(self):
        overlap, total = sources_overlap([], ["TBK m.1"])
        assert overlap == 0
        assert total == 1

    def test_case_insensitive(self):
        overlap, total = sources_overlap(["tbk m.1"], ["TBK m.1"])
        assert overlap == 1

    def test_soft_match_article_number(self):
        # "TBK m.299" vs "TBK Madde 299" → yumuşak eşleşme
        overlap, total = sources_overlap(["TBK m.299"], ["TBK m. 299"])
        assert overlap >= 1


# ===========================================================================
# detect_hallucination
# ===========================================================================

class TestDetectHallucination:
    def test_hallucination_when_wrong_source(self):
        # Beklenen: TBK m.1, Atıf yapılan: TBK m.99 (yanlış)
        result = detect_hallucination(["TBK m.99"], ["TBK m.1"], "TBK m.99 kapsamında...")
        assert result is True

    def test_no_hallucination_correct_source(self):
        result = detect_hallucination(["TBK m.1"], ["TBK m.1"], "TBK m.1 kapsamında...")
        assert result is False

    def test_no_hallucination_no_citation(self):
        # Atıf yoksa hallüsinasyon değil (citation rate düşer)
        result = detect_hallucination([], ["TBK m.1"], "Genel bir yanıt")
        assert result is False

    def test_no_hallucination_no_expected(self):
        # Beklenen yoksa hallüsinasyon kararı verilemez
        result = detect_hallucination(["TBK m.1"], [], "TBK m.1 kapsamında...")
        assert result is False


# ===========================================================================
# detect_refusal
# ===========================================================================

class TestDetectRefusal:
    def test_explicit_kapsam_disi(self):
        assert detect_refusal("Bu soru kapsam dışıdır.") is True

    def test_bilgim_yok(self):
        assert detect_refusal("Bu konuda bilgim bulunmamaktadır.") is True

    def test_cevap_veremiyorum(self):
        assert detect_refusal("Üzgünüm, bu konuya cevap veremiyorum.") is True

    def test_is_kanunu_reference(self):
        # Kıdem tazminatı sorusunda İş Kanunu'na yönlendirme → refusal
        assert detect_refusal("Bu konu İş Kanunu kapsamındadır.") is True

    def test_normal_answer_not_refusal(self):
        assert detect_refusal("TBK m.1 kapsamında sözleşme icap ve kabul ile kurulur.") is False

    def test_veri_tabaninda_yok(self):
        assert detect_refusal("Veri tabanımda bu konu mevcut değil.") is True

    def test_kaynak_bulunamadi(self):
        assert detect_refusal("İlgili kaynak bulunamadı.") is True


# ===========================================================================
# keyword_coverage
# ===========================================================================

class TestKeywordCoverage:
    def test_all_keywords_present(self):
        answer = "Bu sözleşme icap ve kabul beyanlarını içermektedir."
        assert keyword_coverage(answer, ["icap", "kabul", "beyan"]) == 1.0

    def test_no_keywords_present(self):
        answer = "Genel bir yanıt metni."
        assert keyword_coverage(answer, ["icap", "kabul"]) == 0.0

    def test_partial_coverage(self):
        answer = "Sözleşme icap içermektedir."
        cov = keyword_coverage(answer, ["icap", "kabul"])
        assert cov == 0.5

    def test_empty_keywords(self):
        assert keyword_coverage("herhangi bir yanıt", []) == 1.0

    def test_case_insensitive(self):
        answer = "TBK m.1 kapsamında İCAP ve KABUL gereklidir."
        assert keyword_coverage(answer, ["icap", "kabul"]) == 1.0


# ===========================================================================
# phrase_hit
# ===========================================================================

class TestPhraseHit:
    def test_phrase_present(self):
        assert phrase_hit("icap ve kabul gereklidir", "icap ve kabul") is True

    def test_phrase_absent(self):
        assert phrase_hit("Genel yanıt", "icap ve kabul") is False

    def test_none_phrase(self):
        assert phrase_hit("herhangi bir yanıt", None) is None

    def test_case_insensitive(self):
        assert phrase_hit("İCAP VE KABUL", "icap ve kabul") is True


# ===========================================================================
# compute_metrics
# ===========================================================================

class TestComputeMetrics:
    def test_full_correct(self, tbk_question):
        result = compute_metrics(
            question=tbk_question,
            answer_text="TBK m.1 ve TBK m.2 uyarınca sözleşme icap ve kabul ile kurulur. İrade beyanı gereklidir.",
            cited_sources=["TBK m.1", "TBK m.2"],
            response_time_ms=120.0,
        )
        assert result.has_citation is True
        assert result.correct_source_rate == 1.0
        assert result.is_hallucination is False
        assert result.kw_coverage > 0.5  # icap, kabul, irade
        assert result.phrase_hit_result is True
        assert result.error is None

    def test_no_citation(self, tbk_question):
        result = compute_metrics(
            question=tbk_question,
            answer_text="Sözleşme icap ve kabul ile kurulur.",
            cited_sources=[],
        )
        assert result.has_citation is False
        assert result.is_hallucination is False  # Atıf yoksa hal değil

    def test_hallucination(self, tbk_question):
        result = compute_metrics(
            question=tbk_question,
            answer_text="TBK m.999 uyarınca...",
            cited_sources=["TBK m.999"],  # Beklenen değil
        )
        assert result.is_hallucination is True

    def test_refusal_correct(self, out_of_scope_question):
        result = compute_metrics(
            question=out_of_scope_question,
            answer_text="Bu konu kapsam dışıdır. İş Kanunu'na başvurunuz.",
            cited_sources=[],
        )
        assert result.is_refusal is True
        assert result.refusal_correct is True  # Beklenen refusal → doğru

    def test_refusal_missed(self, out_of_scope_question):
        result = compute_metrics(
            question=out_of_scope_question,
            answer_text="Kıdem tazminatı 30 güne göre hesaplanır.",
            cited_sources=[],
        )
        assert result.is_refusal is False
        assert result.refusal_correct is False  # Refusal beklendi ama gelmedi

    def test_with_error(self, tbk_question):
        result = compute_metrics(
            question=tbk_question,
            answer_text="",
            cited_sources=[],
            error="Connection refused",
        )
        assert result.error == "Connection refused"

    def test_evidence_level_metrics_from_trace_and_contract(self, tbk_question):
        contract = {
            "selected_source_keys": ["TBK m.1", "TBK m.2"],
            "primary_source_id": "TBK m.1",
            "secondary_source_ids": ["TBK m.2"],
            "source_validity": "active",
            "claim_units": [
                {
                    "claim_text": "Sözleşme irade açıklamalarıyla kurulur.",
                    "source_id": "TBK m.1",
                    "selected_source_key": "TBK m.1",
                },
                {
                    "claim_text": "Taraflar esaslı noktaları kararlaştırmalıdır.",
                    "source_id": "TBK m.2",
                    "selected_source_key": "TBK m.2",
                },
            ],
        }
        trace = {
            "query_signals": {"forced_article_refs": [], "applied_expansions": []},
            "retrieval": {
                "pre_rerank_chunks": [
                    {"source_id": "TBK m.1"},
                    {"source_id": "TBK m.2"},
                    {"source_id": "TBK m.3"},
                ],
                "post_rerank_chunks": [
                    {"source_id": "TBK m.1"},
                    {"source_id": "TBK m.2"},
                ],
            },
            "context_assembly": {
                "assembled_evidence": [
                    {"source_id": "TBK m.1"},
                    {"source_id": "TBK m.2"},
                ]
            },
            "generation_outcome": {"decision_lane": "rag"},
        }

        result = compute_metrics(
            question={**tbk_question, "expected_evidence_sources": ["TBK m.1", "TBK m.2"], "expected_law_state": "current"},
            answer_text="TBK m.1 ve TBK m.2 uyarınca cevap. [Kaynak: TBK m.1] [Kaynak: TBK m.2]",
            cited_sources=["TBK m.1", "TBK m.2"],
            answer_contract=contract,
            final_mode="answer",
            trace=trace,
        )

        assert result.retrieval_hit_at_5 == 1.0
        assert result.retrieval_hit_at_20 == 1.0
        assert result.selected_evidence_precision == 1.0
        assert result.selected_evidence_recall == 1.0
        assert result.citation_exactness == 1.0
        assert result.claim_supported_rate == 1.0
        assert result.unsupported_claim_rate == 0.0
        assert result.current_law_state_error is False
        assert result.no_benchmark_specific_runtime_patch is True

    def test_benchmark_runtime_patch_trace_fails_static_metric(self, tbk_question):
        result = compute_metrics(
            question=tbk_question,
            answer_text="TBK m.1 yanıtı. [Kaynak: TBK m.1]",
            cited_sources=["TBK m.1"],
            trace={
                "query_signals": {
                    "forced_article_refs": [{"law": "TBK", "madde": "1"}],
                    "applied_expansions": [],
                },
                "generation_outcome": {"decision_lane": "precise_tbk_shortcut"},
            },
        )

        assert result.no_benchmark_specific_runtime_patch is False


# ===========================================================================
# aggregate_metrics
# ===========================================================================

class TestAggregateMetrics:
    def _make_result(self, **kwargs) -> QuestionResult:
        defaults = dict(
            question_id="TEST-001",
            question_text="Soru",
            category="tbk_genel",
            difficulty="easy",
            answer_text="Yanıt",
            cited_sources=[],
            expected_sources=["TBK m.1"],
            expected_keywords=["icap"],
            expected_answer_contains=None,
            refusal_expected=False,
            has_citation=True,
            correct_source_overlap=1,
            expected_source_count=1,
            correct_source_rate=1.0,
            is_hallucination=False,
            is_refusal=False,
            refusal_correct=True,
            kw_coverage=1.0,
            phrase_hit_result=None,
            response_time_ms=100.0,
            blocked=False,
            verification_verdict="pass",
            error=None,
        )
        defaults.update(kwargs)
        return QuestionResult(**defaults)

    def test_empty_results(self):
        agg = aggregate_metrics([])
        assert agg.total_questions == 0

    def test_perfect_score(self):
        results = [self._make_result() for _ in range(5)]
        agg = aggregate_metrics(results)
        assert agg.citation_rate == 1.0
        assert agg.correct_source_rate == 1.0
        assert agg.hallucination_rate == 0.0
        assert agg.refusal_accuracy == 1.0

    def test_faz1_criteria_pass(self):
        results = [self._make_result() for _ in range(10)]
        agg = aggregate_metrics(results)
        assert agg.faz1_criteria["overall"]["passes"] is True

    def test_faz1_criteria_fail_hallucination(self):
        # Hallüsinasyon rate > 0.10
        results = [
            self._make_result(is_hallucination=(i < 5))  # 50% hallüsinasyon
            for i in range(10)
        ]
        agg = aggregate_metrics(results)
        hal_data = agg.faz1_criteria["hallucination_rate"]
        assert hal_data["passes"] is False

    def test_error_count(self):
        results = [
            self._make_result(),
            self._make_result(error="Timeout"),
        ]
        agg = aggregate_metrics(results)
        assert agg.error_count == 1

    def test_by_category(self):
        results = [
            self._make_result(category="tbk_kira"),
            self._make_result(category="tbk_kira"),
            self._make_result(category="tbk_genel"),
        ]
        agg = aggregate_metrics(results)
        assert "tbk_kira" in agg.by_category
        assert agg.by_category["tbk_kira"]["count"] == 2

    def test_by_difficulty(self):
        results = [
            self._make_result(difficulty="easy"),
            self._make_result(difficulty="hard"),
        ]
        agg = aggregate_metrics(results)
        assert "easy" in agg.by_difficulty
        assert "hard" in agg.by_difficulty

    def test_closure_criteria_pass_for_evidence_metrics(self):
        results = [
            self._make_result(
                retrieval_hit_at_20=1.0,
                selected_evidence_recall=1.0,
                citation_exactness=1.0,
                claim_supported_rate=1.0,
                unsupported_claim_rate=0.0,
                current_law_state_error=False,
                refusal_correctness=1.0,
                no_benchmark_specific_runtime_patch=True,
            )
            for _ in range(3)
        ]

        agg = aggregate_metrics(results)

        assert agg.retrieval_hit_at_20 == 1.0
        assert agg.selected_evidence_recall == 1.0
        assert agg.closure_criteria["overall"]["passes"] is True

    def test_closure_criteria_fail_for_benchmark_patch_metric(self):
        results = [
            self._make_result(
                retrieval_hit_at_20=1.0,
                selected_evidence_recall=1.0,
                citation_exactness=1.0,
                claim_supported_rate=1.0,
                unsupported_claim_rate=0.0,
                current_law_state_error=False,
                refusal_correctness=1.0,
                no_benchmark_specific_runtime_patch=False,
            )
        ]

        agg = aggregate_metrics(results)

        assert agg.no_benchmark_specific_runtime_patch is False
        assert agg.closure_criteria["no_benchmark_specific_runtime_patch"]["passes"] is False
        assert agg.closure_criteria["overall"]["passes"] is False


# ===========================================================================
# MockChatClient
# ===========================================================================

class TestMockChatClient:
    def test_normal_question(self, tbk_question):
        client = MockChatClient()
        resp = client.chat(tbk_question["question"], _question_meta=tbk_question)
        assert isinstance(resp["answer_text"], str)
        assert len(resp["answer_text"]) > 10
        assert resp["error"] is None

    def test_out_of_scope_refusal(self, out_of_scope_question):
        client = MockChatClient()
        resp = client.chat(
            out_of_scope_question["question"],
            _question_meta=out_of_scope_question,
        )
        # Refusal bekleniyor → yanıtta kapsam dışı ifadesi olmalı
        answer = resp["answer_text"].lower()
        assert any(kw in answer for kw in [
            "kapsam dışı", "bilunmamaktadır", "yeterli", "iş kanunu", "kapsam"
        ])

    def test_mock_response_structure(self, tbk_question):
        client = MockChatClient()
        resp = client.chat(tbk_question["question"], _question_meta=tbk_question)
        required_keys = {"answer_text", "citations", "blocked", "verification", "response_time_ms", "error"}
        assert required_keys.issubset(resp.keys())


# ===========================================================================
# run_evaluation (mock mod)
# ===========================================================================

class TestRunEvaluation:
    def test_mock_run_all_questions(self, questions_file):
        """Mock mod ile tüm sorular değerlendirilebiliyor mu?"""
        with open(questions_file) as f:
            data = json.load(f)
        questions = data["questions"]

        client = MockChatClient()
        results = run_evaluation(
            questions=questions,
            client=client,
            delay_between_requests=0.0,
            mock_mode=True,
        )
        assert len(results) == len(questions)
        assert all(isinstance(r, QuestionResult) for r in results)

    def test_category_filter(self, questions_file):
        """Kategori filtresi doğru çalışıyor mu?"""
        with open(questions_file) as f:
            data = json.load(f)
        questions = data["questions"]

        client = MockChatClient()
        results = run_evaluation(
            questions=questions,
            client=client,
            category_filter="out_of_scope",
            delay_between_requests=0.0,
            mock_mode=True,
        )
        # Sadece out_of_scope kategorisi → 1 soru
        assert len(results) == 1
        assert results[0].category == "out_of_scope"

    def test_full_evaluation_integration(self):
        """Uçtan uca mock değerlendirme — gerçek questions JSON ile."""
        real_questions_path = PROJECT_ROOT / "configs" / "evaluation" / "test_questions.json"
        if not real_questions_path.exists():
            pytest.skip("Test soruları dosyası mevcut değil")

        with open(real_questions_path) as f:
            data = json.load(f)
        questions = data["questions"]

        client = MockChatClient()
        results = run_evaluation(
            questions=questions,
            client=client,
            delay_between_requests=0.0,
            mock_mode=True,
        )
        assert len(results) == len(questions)

        summary = aggregate_metrics(results)
        assert summary.total_questions == len(questions)
        # Mock client refusal doğru çalışmalı → refusal_accuracy > 0
        assert summary.refusal_accuracy > 0.0
        # Mock client kaynak üretiyor → citation_rate > 0
        assert summary.citation_rate > 0.0

    def test_aggregate_after_run(self, questions_file):
        """run_evaluation + aggregate_metrics zinciri çalışıyor mu?"""
        with open(questions_file) as f:
            data = json.load(f)
        questions = data["questions"]

        client = MockChatClient()
        results = run_evaluation(
            questions=questions,
            client=client,
            delay_between_requests=0.0,
            mock_mode=True,
        )
        summary = aggregate_metrics(results)
        assert summary.total_questions == 2
        assert "overall" in summary.faz1_criteria


# ===========================================================================
# questions JSON yapısı
# ===========================================================================

class TestQuestionsJSON:
    def test_real_questions_file_exists(self):
        path = PROJECT_ROOT / "configs" / "evaluation" / "test_questions.json"
        assert path.exists(), f"test_questions.json bulunamadı: {path}"

    def test_questions_have_required_fields(self):
        path = PROJECT_ROOT / "configs" / "evaluation" / "test_questions.json"
        if not path.exists():
            pytest.skip("Dosya mevcut değil")

        with open(path) as f:
            data = json.load(f)

        required = {"id", "question", "category", "difficulty",
                    "expected_sources", "expected_keywords", "refusal_expected"}
        for q in data["questions"]:
            missing = required - q.keys()
            assert not missing, f"Soru {q.get('id')} eksik alanlar: {missing}"

    def test_question_count(self):
        path = PROJECT_ROOT / "configs" / "evaluation" / "test_questions.json"
        if not path.exists():
            pytest.skip("Dosya mevcut değil")

        with open(path) as f:
            data = json.load(f)

        assert len(data["questions"]) >= 10, "En az 10 soru bekleniyor"

    def test_refusal_questions_exist(self):
        path = PROJECT_ROOT / "configs" / "evaluation" / "test_questions.json"
        if not path.exists():
            pytest.skip("Dosya mevcut değil")

        with open(path) as f:
            data = json.load(f)

        refusal_qs = [q for q in data["questions"] if q.get("refusal_expected")]
        assert len(refusal_qs) >= 1, "En az 1 refusal sorusu bekleniyor"

    def test_mevzuat_closure_eval_file_has_required_evidence_fields(self):
        path = PROJECT_ROOT / "configs" / "evaluation" / "mevzuat_closure_eval.json"
        assert path.exists(), f"mevzuat_closure_eval.json bulunamadı: {path}"

        with open(path) as f:
            data = json.load(f)

        assert data["_meta"]["eval_family"] == "mevzuat_closure_eval"
        assert len(data["questions"]) >= 10
        required = {"id", "question", "category", "expected_sources", "expected_evidence_sources", "refusal_expected"}
        for q in data["questions"]:
            missing = required - q.keys()
            assert not missing, f"Soru {q.get('id')} eksik alanlar: {missing}"


class TestReportMetadata:
    def test_build_report_embeds_identity_metadata(self):
        summary = SimpleNamespace(
            total_questions=1,
            error_count=0,
            citation_rate=1.0,
            correct_source_rate=1.0,
            hallucination_rate=0.0,
            refusal_accuracy=1.0,
            avg_keyword_coverage=1.0,
            phrase_hit_rate=1.0,
            avg_response_time_ms=120.0,
            blocked_rate=0.0,
            faz1_criteria={"overall": {"passes": True, "status": "PASS"}},
            by_category={},
            by_difficulty={},
        )

        report = build_report(
            results=[],
            summary=summary,
            questions_path=PROJECT_ROOT / "configs" / "evaluation" / "test_questions_v2_95.json",
            api_url="http://localhost:8000",
            mock_mode=False,
            model_ref="gateway-live:qwen35",
            checkpoint_ref="dgxnode2-runtime-20260321",
            git_commit="abc1234",
            report_role="baseline",
            config_fingerprint={"verification_enabled": True},
        )

        meta = report["report_meta"]
        assert meta["schema_version"] == 2
        assert meta["runner"] == "eval_runner"
        assert meta["report_role"] == "baseline"
        assert meta["eval_family"] == "v2-95"
        assert meta["model_ref"] == "gateway-live:qwen35"
        assert meta["checkpoint_ref"] == "dgxnode2-runtime-20260321"
        assert meta["git_commit"] == "abc1234"
        assert meta["config_fingerprint"] == {"verification_enabled": True}

    def test_build_report_includes_closure_metrics(self):
        summary = aggregate_metrics([
            QuestionResult(
                question_id="MEV-CLOSURE-001",
                question_text="TBK m.1 nedir?",
                category="explicit_law_article",
                difficulty="easy",
                answer_text="TBK m.1",
                cited_sources=["TBK m.1"],
                expected_sources=["TBK m.1"],
                expected_evidence_sources=["TBK m.1"],
                has_citation=True,
                correct_source_overlap=1,
                expected_source_count=1,
                correct_source_rate=1.0,
                refusal_correct=True,
                retrieval_hit_at_20=1.0,
                selected_evidence_recall=1.0,
                selected_evidence_precision=1.0,
                citation_exactness=1.0,
                claim_supported_rate=1.0,
                unsupported_claim_rate=0.0,
                refusal_correctness=1.0,
                no_benchmark_specific_runtime_patch=True,
            )
        ])

        report = build_report(
            results=[],
            summary=summary,
            questions_path=PROJECT_ROOT / "configs" / "evaluation" / "mevzuat_closure_eval.json",
            api_url="http://localhost:8000",
            mock_mode=False,
        )

        assert report["summary"]["retrieval_hit_at_20"] == 1.0
        assert report["summary"]["claim_supported_rate"] == 1.0
        assert report["closure_criteria"]["overall"]["passes"] is True

    def test_build_report_preserves_optional_trace(self):
        summary = SimpleNamespace(
            total_questions=1,
            error_count=0,
            citation_rate=1.0,
            correct_source_rate=1.0,
            hallucination_rate=0.0,
            refusal_accuracy=1.0,
            avg_keyword_coverage=1.0,
            phrase_hit_rate=1.0,
            avg_response_time_ms=120.0,
            blocked_rate=0.0,
            faz1_criteria={"overall": {"passes": True, "status": "PASS"}},
            by_category={},
            by_difficulty={},
        )
        result = QuestionResult(
            question_id="TBK-001",
            question_text="TBK m.1 nedir?",
            category="tbk_genel",
            difficulty="easy",
            answer_text="TBK m.1",
            cited_sources=["TBK m.1"],
            expected_sources=["TBK m.1"],
            expected_keywords=[],
            has_citation=True,
            correct_source_overlap=1,
            expected_source_count=1,
            correct_source_rate=1.0,
            kw_coverage=1.0,
            refusal_correct=True,
            final_mode="answer",
            final_reason=None,
            answer_contract={
                "answer_text": "TBK m.1",
                "primary_source_id": "TBK m.1",
                "secondary_source_ids": [],
                "law_scope": ["TBK"],
                "source_validity": "active",
                "unsupported_reason": None,
                "verifier_status": "pass",
                "final_mode": "answer",
                "claim_units": [],
            },
            trace={
                "query_signals": {"user_query": "TBK m.1 nedir?"},
                "retrieval": {"top_k_requested": 20},
            },
        )

        report = build_report(
            results=[result],
            summary=summary,
            questions_path=PROJECT_ROOT / "configs" / "evaluation" / "test_questions.json",
            api_url="http://localhost:8000",
            mock_mode=False,
        )

        assert report["per_question"][0]["trace"]["query_signals"]["user_query"] == "TBK m.1 nedir?"
        assert report["per_question"][0]["answer_contract"]["primary_source_id"] == "TBK m.1"


class TestChatApiClient:
    def test_chat_api_client_passes_include_trace_and_reads_trace(self, monkeypatch):
        captured: dict[str, object] = {}

        class _FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return json.dumps(
                    {
                        "choices": [{"message": {"content": "Yanıt"}}],
                        "citations": ["TBK m.1"],
                        "blocked": False,
                        "final_mode": "answer",
                        "final_reason": None,
                        "answer_contract": {"primary_source_id": "TBK m.1"},
                        "verification": {"verdict": "pass"},
                        "trace": {"query_signals": {"user_query": "TBK m.1 nedir?"}},
                    }
                ).encode("utf-8")

        def fake_urlopen(req, timeout):
            captured["payload"] = json.loads(req.data.decode("utf-8"))
            return _FakeResponse()

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        client = ChatAPIClient(
            base_url="http://localhost:8000",
            include_trace=True,
        )

        result = client.chat("TBK m.1 nedir?")

        assert captured["payload"]["include_trace"] is True
        assert result["trace"]["query_signals"]["user_query"] == "TBK m.1 nedir?"
        assert result["answer_contract"]["primary_source_id"] == "TBK m.1"
        assert result["final_mode"] == "answer"
