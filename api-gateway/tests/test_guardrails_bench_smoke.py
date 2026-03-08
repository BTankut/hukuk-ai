"""
Guardrails Benchmark — pytest smoke wrapper.

Benchmark scriptini test paketi içinden çalıştırmak için.
DGX gerektirmez; mock LLM ile citation-check pipeline'ını ölçer.

Çalıştırma:
    cd api-gateway
    .venv/bin/python -m pytest tests/test_guardrails_bench_smoke.py -v
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

# benchmarks/ dizini sys.path'e ekleniyor
_BENCH_DIR = Path(__file__).resolve().parents[1] / "benchmarks"
sys.path.insert(0, str(_BENCH_DIR))

from guardrails_latency_bench import BENCHMARK_CASES, BenchmarkRow, _measure_case
from config import Settings
from guardrails.pipeline import GuardrailsPipeline


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def pipeline_on() -> GuardrailsPipeline:
    """Guardrails enabled (NeMo atlanmış, citation-check aktif)."""
    return GuardrailsPipeline(
        settings=Settings(guardrails_enabled=False, guardrails_strict_mode=True)
    )


@pytest.fixture(scope="module")
def pipeline_off() -> GuardrailsPipeline:
    """Guardrails tamamen kapalı, strict mode devrede (baseline)."""
    return GuardrailsPipeline(
        settings=Settings(guardrails_enabled=False, guardrails_strict_mode=False)
    )


# ---------------------------------------------------------------------------
# Metrik doğruluğu testleri
# ---------------------------------------------------------------------------


class TestBenchmarkMetrics:
    """Benchmark metriklerinin doğru toplanıp toplanmadığını kontrol eder."""

    def test_valid_case_not_blocked(self, pipeline_on):
        """Geçerli kaynaklı sorgu bloke edilmemeli."""
        case = next(c for c in BENCHMARK_CASES if c["id"] == "tbk-49-valid")
        row: BenchmarkRow = asyncio.run(
            _measure_case(pipeline_on, case, mode="mock", guardrails_on=True)
        )
        assert row.error == "", f"Pipeline hatası: {row.error}"
        assert not row.refusal_triggered, "Geçerli sorgu bloke edildi"
        assert row.citation_present, "Geçerli yanıtta kaynak referansı bulunamadı"
        assert row.outcome_correct

    def test_fake_citation_blocked(self, pipeline_on):
        """Uydurma kaynak içeren yanıt bloke edilmeli."""
        case = next(c for c in BENCHMARK_CASES if c["id"] == "fake-citation")
        row: BenchmarkRow = asyncio.run(
            _measure_case(pipeline_on, case, mode="mock", guardrails_on=True)
        )
        assert row.error == "", f"Pipeline hatası: {row.error}"
        assert row.hallucination_blocked, "Uydurma kaynak bloke edilmedi"
        assert row.outcome_correct

    def test_no_citation_blocked_in_strict_mode(self, pipeline_on):
        """Citation olmayan yanıt strict modda bloke edilmeli."""
        case = next(c for c in BENCHMARK_CASES if c["id"] == "no-citation")
        row: BenchmarkRow = asyncio.run(
            _measure_case(pipeline_on, case, mode="mock", guardrails_on=True)
        )
        assert row.error == "", f"Pipeline hatası: {row.error}"
        assert row.hallucination_blocked, "Citation'sız yanıt strict modda bloke edilmedi"

    def test_no_citation_passes_in_non_strict_mode(self, pipeline_off):
        """Citation olmayan yanıt strict mode kapalıyken geçebilmeli."""
        case = next(c for c in BENCHMARK_CASES if c["id"] == "no-citation")
        row: BenchmarkRow = asyncio.run(
            _measure_case(pipeline_off, case, mode="mock", guardrails_on=False)
        )
        assert row.error == "", f"Pipeline hatası: {row.error}"
        assert not row.refusal_triggered

    def test_latency_recorded(self, pipeline_on):
        """Latency sıfırdan büyük olmalı."""
        case = BENCHMARK_CASES[0]
        row: BenchmarkRow = asyncio.run(
            _measure_case(pipeline_on, case, mode="mock", guardrails_on=True)
        )
        assert row.total_latency_s > 0.0

    def test_all_cases_complete_without_error(self, pipeline_on):
        """Tüm benchmark vakaları hatasız tamamlanmalı."""
        for case in BENCHMARK_CASES:
            row: BenchmarkRow = asyncio.run(
                _measure_case(pipeline_on, case, mode="mock", guardrails_on=True)
            )
            assert row.error == "", (
                f"Case '{case['id']}' pipeline hatası verdi: {row.error}"
            )


# ---------------------------------------------------------------------------
# Overhead ölçümü (smoke seviyesi)
# ---------------------------------------------------------------------------


class TestGuardrailsOverhead:
    """ON vs OFF latency farkını smoke seviyede ölçer.

    Mock modda bu fark yalnızca citation-check CPU overhead'ini yansıtır.
    Gerçek NeMo overhead'i (ek LLM çağrıları) DGX modunda görülür.
    """

    def test_guardrails_on_latency_within_mock_budget(self, pipeline_on):
        """Mock modda her vaka ≤5s içinde tamamlanmalı (NeMo LLM yok)."""
        for case in BENCHMARK_CASES:
            row: BenchmarkRow = asyncio.run(
                _measure_case(pipeline_on, case, mode="mock", guardrails_on=True)
            )
            assert row.total_latency_s < 5.0, (
                f"Mock modda {case['id']} {row.total_latency_s:.2f}s sürdü (beklenen <5s)"
            )

    def test_row_fields_complete(self, pipeline_on):
        """BenchmarkRow tüm alanları içermeli."""
        case = BENCHMARK_CASES[0]
        row: BenchmarkRow = asyncio.run(
            _measure_case(pipeline_on, case, mode="mock", guardrails_on=True)
        )
        d = row.to_dict()
        required_fields = [
            "run_id", "timestamp", "mode", "guardrails_on", "case_id",
            "total_latency_s", "citation_present", "refusal_triggered",
            "hallucination_blocked", "outcome_correct",
        ]
        for f in required_fields:
            assert f in d, f"BenchmarkRow alanı eksik: {f}"
