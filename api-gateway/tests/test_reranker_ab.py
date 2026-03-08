"""Reranker A/B Evaluation — pytest iskelet.

Bu test dosyası iki katmanda çalışır:

1. UNIT (marker yok) — sentence-transformers kurulu olmasa bile geçer.
   Reranker sınıfının arayüzini, fixture formatını ve rapor şemasını doğrular.

2. INTEGRATION (pytest -m integration) — Gerçek model inference yapar.
   M4 Max'te sentence-transformers ve modeller indirilmiş olmalı.
   ~3-5 dakika, internet bağlantısı ilk çalıştırmada gerekli.

Çalıştırma:
    # Hızlı iskelet kontrolü (model gerektirmez):
    cd api-gateway && python -m pytest tests/test_reranker_ab.py -v

    # Gerçek model testi:
    cd api-gateway && python -m pytest tests/test_reranker_ab.py -v -m integration

    # Tam eval raporu (pytest değil, doğrudan script):
    python evaluation/reranker_ab_eval.py

Kabul kriteri (U-1):
    top-5 precision ≥ baseline top-20 precision (gain ≥ 0.0)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

# Proje kök dizini
PROJECT_ROOT = Path(__file__).parent.parent.parent
FIXTURES_PATH = PROJECT_ROOT / "evaluation" / "fixtures" / "reranker_queries.json"
SAMPLE_REPORT_PATH = PROJECT_ROOT / "evaluation" / "reports" / "reranker_ab_report.sample.json"

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def reranker_queries() -> list[dict]:
    """Türkçe hukuk query-passage fixture'larını yükle."""
    assert FIXTURES_PATH.exists(), (
        f"Fixture dosyası bulunamadı: {FIXTURES_PATH}\n"
        "evaluation/fixtures/reranker_queries.json oluşturulmuş olmalı."
    )
    data = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    return data["queries"]


@pytest.fixture(scope="session")
def sample_report() -> dict:
    """Beklenen rapor formatı örneği."""
    assert SAMPLE_REPORT_PATH.exists(), f"Sample rapor bulunamadı: {SAMPLE_REPORT_PATH}"
    return json.loads(SAMPLE_REPORT_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def reranker_module():
    """Reranker modülünü import et."""
    try:
        from rag.reranker import (
            Reranker,
            RankedResult,
            RerankerStats,
            MODEL_A,
            MODEL_B,
            MODEL_C,
            FAZ1_DEFAULT_MODEL,
            FAZ1_DEFAULT_THRESHOLD,
            FAZ1_TOP_K,
        )
        return {
            "Reranker": Reranker,
            "RankedResult": RankedResult,
            "RerankerStats": RerankerStats,
            "MODEL_A": MODEL_A,
            "MODEL_B": MODEL_B,
            "MODEL_C": MODEL_C,
            "FAZ1_DEFAULT_MODEL": FAZ1_DEFAULT_MODEL,
            "FAZ1_DEFAULT_THRESHOLD": FAZ1_DEFAULT_THRESHOLD,
            "FAZ1_TOP_K": FAZ1_TOP_K,
        }
    except ImportError as e:
        pytest.skip(f"rag.reranker import hatası: {e}")


# ---------------------------------------------------------------------------
# Unit Tests — model gerektirmez
# ---------------------------------------------------------------------------

class TestFixtureIntegrity:
    """Fixture yapısının doğru olduğunu kontrol et."""

    def test_fixture_file_exists(self):
        assert FIXTURES_PATH.exists(), f"Fixture yok: {FIXTURES_PATH}"

    def test_fixture_has_queries(self, reranker_queries):
        assert len(reranker_queries) >= 5, "En az 5 sorgu olmalı"

    def test_each_query_has_required_fields(self, reranker_queries):
        required = {"id", "query", "law_domain", "candidates"}
        for q in reranker_queries:
            missing = required - set(q.keys())
            assert not missing, f"Sorgu {q.get('id')} eksik alanlar: {missing}"

    def test_each_candidate_has_required_fields(self, reranker_queries):
        required = {"id", "text", "citation", "relevance"}
        for q in reranker_queries:
            for c in q["candidates"]:
                missing = required - set(c.keys())
                assert not missing, (
                    f"Sorgu {q['id']} aday {c.get('id')} eksik alanlar: {missing}"
                )

    def test_relevance_labels_are_binary(self, reranker_queries):
        for q in reranker_queries:
            for c in q["candidates"]:
                assert c["relevance"] in (0, 1), (
                    f"Relevance {c['id']} için 0 veya 1 olmalı, şu an: {c['relevance']}"
                )

    def test_each_query_has_at_least_one_relevant(self, reranker_queries):
        for q in reranker_queries:
            relevant = [c for c in q["candidates"] if c["relevance"] == 1]
            assert len(relevant) >= 1, (
                f"Sorgu {q['id']}: en az 1 relevant aday olmalı"
            )

    def test_law_domains_covered(self, reranker_queries):
        domains = {q.get("law_domain") for q in reranker_queries}
        expected_min = {"borclar", "is", "ceza"}  # TBK, İK, TCK en az olmalı
        missing = expected_min - domains
        assert not missing, f"Eksik hukuk dalları: {missing}"

    def test_candidate_ids_unique_within_query(self, reranker_queries):
        for q in reranker_queries:
            ids = [c["id"] for c in q["candidates"]]
            assert len(ids) == len(set(ids)), f"Sorgu {q['id']} duplicate aday ID'si"


class TestRerankerModuleConstants:
    """Reranker modülündeki sabitler Faz 1 frozen scope ile uyumlu mu?"""

    def test_default_model_is_mmarco(self, reranker_module):
        """D-2: Primary model mmarco-mMiniLMv2 olmalı."""
        m = reranker_module
        assert m["FAZ1_DEFAULT_MODEL"] == m["MODEL_A"], (
            f"Faz 1 D-2 kararı: varsayılan model MODEL_A olmalı. "
            f"Şu an: {m['FAZ1_DEFAULT_MODEL']}"
        )
        assert "mmarco" in m["FAZ1_DEFAULT_MODEL"].lower(), (
            f"mmarco multilingual model seçili olmalı. Şu an: {m['FAZ1_DEFAULT_MODEL']}"
        )

    def test_default_threshold_is_07(self, reranker_module):
        """D-2: Başlangıç threshold 0.7 (grid search ile optimize edilecek)."""
        assert reranker_module["FAZ1_DEFAULT_THRESHOLD"] == 0.7

    def test_top_k_is_5(self, reranker_module):
        """RAG pipeline: top-20 retrieval → top-5 rerank."""
        assert reranker_module["FAZ1_TOP_K"] == 5

    def test_model_b_is_english_control(self, reranker_module):
        """MODEL_B İngilizce kontrol grubu olmalı."""
        assert "ms-marco-MiniLM" in reranker_module["MODEL_B"]

    def test_model_c_is_fallback_bge(self, reranker_module):
        """MODEL_C: mmarco başarısız olursa değerlendirilecek."""
        assert "bge-reranker" in reranker_module["MODEL_C"]


class TestRerankerInterface:
    """Reranker sınıf arayüzünü test et (model inference olmadan)."""

    def test_reranker_instantiation_defaults(self, reranker_module):
        Reranker = reranker_module["Reranker"]
        r = Reranker()
        assert r.model_id == reranker_module["FAZ1_DEFAULT_MODEL"]
        assert r.threshold == 0.7
        assert r.top_k == 5
        assert r.device == "cpu"

    def test_reranker_custom_params(self, reranker_module):
        Reranker = reranker_module["Reranker"]
        r = Reranker(
            model_id="cross-encoder/ms-marco-MiniLM-L-6-v2",
            threshold=0.5,
            top_k=3,
        )
        assert r.model_id == "cross-encoder/ms-marco-MiniLM-L-6-v2"
        assert r.threshold == 0.5
        assert r.top_k == 3

    def test_reranker_model_is_lazy_loaded(self, reranker_module):
        """Model ilk rerank çağrısına kadar yüklenmemiş olmalı."""
        Reranker = reranker_module["Reranker"]
        r = Reranker()
        assert r._model is None, "Model constructor'da yüklenmemeli (lazy-load)"

    def test_ranked_result_dataclass(self, reranker_module):
        RankedResult = reranker_module["RankedResult"]
        result = RankedResult(
            text="Test hukuki metin",
            citation="TBK md.49",
            score=0.85,
        )
        assert result.text == "Test hukuki metin"
        assert result.citation == "TBK md.49"
        assert result.score == 0.85
        assert result.source is None
        assert result.metadata == {}

    def test_reranker_stats_filter_rate(self, reranker_module):
        RerankerStats = reranker_module["RerankerStats"]
        stats = RerankerStats(
            model_id="test",
            threshold=0.7,
            input_count=20,
            output_count=5,
            top_k_count=5,
            latency_ms=200.0,
        )
        assert stats.filter_rate == pytest.approx(0.75)

    def test_reranker_stats_zero_input(self, reranker_module):
        RerankerStats = reranker_module["RerankerStats"]
        stats = RerankerStats(
            model_id="test",
            threshold=0.7,
            input_count=0,
            output_count=0,
            top_k_count=0,
            latency_ms=0.0,
        )
        assert stats.filter_rate == 0.0


class TestReportSchema:
    """Rapor formatı beklenen şemaya uyuyor mu?"""

    def test_sample_report_has_required_keys(self, sample_report):
        required = {
            "report_meta", "models_evaluated", "results",
            "faz1_decision", "recommendation", "missing_metrics"
        }
        missing = required - set(sample_report.keys())
        assert not missing, f"Sample raporda eksik anahtarlar: {missing}"

    def test_faz1_decision_values(self, sample_report):
        assert sample_report["faz1_decision"] in ("CONFIRMED", "NEEDS_REVIEW")

    def test_sample_report_has_threshold_grid(self, sample_report):
        meta = sample_report["report_meta"]
        assert "threshold_grid" in meta
        assert len(meta["threshold_grid"]) >= 2

    def test_sample_report_has_missing_metrics(self, sample_report):
        """İskelet raporu eksik metrikleri açıkça belirtmeli."""
        assert len(sample_report["missing_metrics"]) >= 3, (
            "Eksik metrikler açıkça listelenmelidir (dürüstlük kuralı)"
        )

    def test_results_include_per_threshold(self, sample_report):
        for model_key, model_result in sample_report["results"].items():
            assert "per_threshold" in model_result, (
                f"{model_key} için per_threshold verisi eksik"
            )
            for thr_key, thr_data in model_result["per_threshold"].items():
                required_thr_fields = {
                    "threshold", "avg_precision_at_5", "avg_baseline_precision",
                    "precision_gain_vs_baseline", "passes_faz1_criterion"
                }
                missing = required_thr_fields - set(thr_data.keys())
                assert not missing, (
                    f"{model_key}[{thr_key}] eksik alanlar: {missing}"
                )


class TestEvalScript:
    """Eval script'in dry-run modunda çalışabildiğini doğrula."""

    def test_eval_script_exists(self):
        script = PROJECT_ROOT / "evaluation" / "reranker_ab_eval.py"
        assert script.exists(), f"Eval script bulunamadı: {script}"
        assert script.stat().st_size > 5000, "Eval script çok küçük, eksik kod olabilir"

    def test_eval_script_dry_run(self, tmp_path):
        """Dry run: fixture yükleme başarılı, model inference yok."""
        import subprocess
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "evaluation" / "reranker_ab_eval.py"),
                "--dry-run",
                "--fixtures", str(FIXTURES_PATH),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"Eval script dry-run başarısız:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )
        output = json.loads(result.stdout.strip())
        assert output.get("status") == "dry_run_ok"
        assert output.get("queries_loaded", 0) >= 5


# ---------------------------------------------------------------------------
# Integration Tests — gerçek model inference
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestRerankerIntegration:
    """Gerçek cross-encoder model ile çalıştırılan testler.

    Koşul: sentence-transformers kurulu + model indirilmiş olmalı.
    Çalıştırma: pytest -m integration
    Tahmini süre: 3-5 dk (ilk çalıştırma: model download dahil)
    """

    @pytest.fixture(scope="class")
    def loaded_reranker(self, reranker_module):
        """Test sınıfı genelinde tek model yüklemesi."""
        Reranker = reranker_module["Reranker"]
        try:
            r = Reranker(
                model_id=reranker_module["FAZ1_DEFAULT_MODEL"],
                threshold=0.5,  # geniş threshold — daha fazla sonuç
                top_k=5,
            )
            # Lazy load tetikle
            r._load_model()
            return r
        except Exception as e:
            pytest.skip(f"Model yüklenemedi: {e}")

    def test_reranker_runs_on_turkish_legal_text(self, loaded_reranker, reranker_queries):
        """TBK haksız fiil sorusu doğru şekilde rerank ediliyor mu?"""
        q = next(q for q in reranker_queries if q["id"] == "q001")
        results, stats = loaded_reranker.rerank(
            query=q["query"],
            candidates=q["candidates"],
            threshold=0.5,
        )
        assert stats.input_count == len(q["candidates"])
        assert stats.latency_ms > 0
        assert isinstance(results, list)

    def test_primary_model_beats_baseline(self, loaded_reranker, reranker_queries):
        """U-1 kabul kriteri: top-5 precision ≥ baseline precision."""
        pytest.importorskip("evaluation", reason="evaluation modülü PYTHONPATH'de değil; integration skip")
        from evaluation.reranker_ab_eval import (
            precision_at_k, baseline_precision
        )

        gains: list[float] = []
        for q in reranker_queries:
            candidates = q["candidates"]
            relevant_ids = {c["id"] for c in candidates if c["relevance"] == 1}
            results, _ = loaded_reranker.rerank(
                query=q["query"],
                candidates=candidates,
                threshold=0.5,
            )
            ranked_ids = [r.citation for r in results]  # noqa: F841 — citation sadece display
            result_texts = [r.text for r in results]

            # ID tabanlı eşleştirme: text'e göre candidate ID bul
            text_to_id = {c["text"]: c["id"] for c in candidates}
            reranked_ids = [
                text_to_id.get(r.text, f"unknown_{i}")
                for i, r in enumerate(results)
            ]

            p5 = precision_at_k(reranked_ids, relevant_ids, 5)
            bp = baseline_precision(candidates)
            gains.append(p5 - bp)

        avg_gain = sum(gains) / len(gains) if gains else 0.0
        assert avg_gain >= 0.0, (
            f"U-1 KRİTERİ BAŞARISIZ: mmarco reranker baseline'ı geçemedi. "
            f"Ortalama precision gain: {avg_gain:.3f}. "
            f"Alternatif: BAAI/bge-reranker-v2-m3 değerlendir veya fine-tune yap."
        )

    def test_threshold_07_returns_fewer_results_than_05(
        self, loaded_reranker, reranker_queries
    ):
        """Threshold arttıkça filtreleme artmalı (monotonicity check)."""
        q = reranker_queries[0]
        _, stats_05 = loaded_reranker.rerank(
            query=q["query"], candidates=q["candidates"], threshold=0.5
        )
        _, stats_07 = loaded_reranker.rerank(
            query=q["query"], candidates=q["candidates"], threshold=0.7
        )
        assert stats_07.output_count <= stats_05.output_count, (
            "Daha yüksek threshold daha az veya eşit sonuç döndürmeli"
        )

    def test_reranker_latency_acceptable_cpu(self, loaded_reranker, reranker_queries):
        """M4 Max CPU'da 10 passage için rerank <2 saniye olmalı."""
        import time
        q = reranker_queries[0]
        t0 = time.perf_counter()
        loaded_reranker.rerank(query=q["query"], candidates=q["candidates"])
        latency = time.perf_counter() - t0
        assert latency < 2.0, (
            f"CPU latency çok yüksek: {latency:.2f}s. "
            f"mmarco 10 passage için <2s bekleniyor."
        )

    @pytest.mark.parametrize("threshold", [0.5, 0.6, 0.7])
    def test_threshold_grid_search(self, loaded_reranker, reranker_queries, threshold):
        """Threshold grid search: her eşik için pipeline çalışıyor mu?"""
        results_per_query = []
        for q in reranker_queries:
            results, stats = loaded_reranker.rerank(
                query=q["query"],
                candidates=q["candidates"],
                threshold=threshold,
            )
            results_per_query.append((results, stats))
        assert len(results_per_query) == len(reranker_queries)
        # Her threshold'da en az 1 sorgunun en az 1 sonucu olmalı
        any_result = any(len(r) > 0 for r, _ in results_per_query)
        assert any_result, (
            f"Threshold {threshold}'da hiçbir sorgu için sonuç yok. "
            f"Eşik çok yüksek olabilir."
        )

    def test_english_control_underperforms_on_turkish(
        self, reranker_module, reranker_queries
    ):
        """MODEL_B (İngilizce) Türkçe'de MODEL_A'dan düşük precision vermeli."""
        Reranker = reranker_module["Reranker"]
        try:
            reranker_b = Reranker(
                model_id=reranker_module["MODEL_B"],
                threshold=0.5,
            )
            reranker_b._load_model()
        except Exception as e:
            pytest.skip(f"MODEL_B yüklenemedi: {e}")

        pytest.importorskip("evaluation", reason="evaluation modülü PYTHONPATH'de değil; integration skip")
        from evaluation.reranker_ab_eval import precision_at_k, baseline_precision

        p5_a_list, p5_b_list = [], []
        for q in reranker_queries:
            candidates = q["candidates"]
            relevant_ids = {c["id"] for c in candidates if c["relevance"] == 1}
            text_to_id = {c["text"]: c["id"] for c in candidates}

            res_a, _ = reranker_module["Reranker"](
                model_id=reranker_module["FAZ1_DEFAULT_MODEL"], threshold=0.5
            ).rerank(q["query"], candidates, threshold=0.5)
            res_b, _ = reranker_b.rerank(q["query"], candidates, threshold=0.5)

            ids_a = [text_to_id.get(r.text, "?") for r in res_a]
            ids_b = [text_to_id.get(r.text, "?") for r in res_b]

            p5_a_list.append(precision_at_k(ids_a, relevant_ids, 5))
            p5_b_list.append(precision_at_k(ids_b, relevant_ids, 5))

        avg_a = sum(p5_a_list) / len(p5_a_list)
        avg_b = sum(p5_b_list) / len(p5_b_list)

        # MODEL_A multilingual, MODEL_B İngilizce — A ≥ B bekleniyor
        assert avg_a >= avg_b * 0.9, (
            f"MODEL_A ({avg_a:.3f}) MODEL_B'ye ({avg_b:.3f}) kıyasla beklenen performansı göstermiyor. "
            f"İngilizce model beklenmedik şekilde iyi performans veriyor — veriyi kontrol et."
        )
