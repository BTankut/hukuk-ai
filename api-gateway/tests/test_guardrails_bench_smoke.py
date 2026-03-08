"""
Guardrails Benchmark — pytest smoke wrapper.

Mock modda deterministic input moderation + Presidio maskeleme davranışını doğrular.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

_BENCH_DIR = Path(__file__).resolve().parents[1] / "benchmarks"
sys.path.insert(0, str(_BENCH_DIR))

from guardrails_latency_bench import BENCHMARK_CASES, BenchmarkRow, _measure_case
from config import Settings
from guardrails.pipeline import GuardrailsPipeline


@pytest.fixture(scope="module")
def pipeline_on() -> GuardrailsPipeline:
    return GuardrailsPipeline(
        settings=Settings(
            guardrails_enabled=False,
            guardrails_strict_mode=False,
            guardrails_input_moderation_enabled=True,
        )
    )


@pytest.fixture(scope="module")
def pipeline_off() -> GuardrailsPipeline:
    return GuardrailsPipeline(
        settings=Settings(
            guardrails_enabled=False,
            guardrails_strict_mode=False,
            guardrails_input_moderation_enabled=False,
        )
    )


class TestBenchmarkMetrics:
    def test_valid_case_not_blocked(self, pipeline_on):
        case = next(c for c in BENCHMARK_CASES if c["id"] == "tbk-49-valid")
        row: BenchmarkRow = asyncio.run(
            _measure_case(pipeline_on, case, mode="mock", guardrails_on=True)
        )
        assert row.error == ""
        assert not row.refusal_triggered
        assert row.outcome_correct

    def test_fake_citation_not_blocked_in_safe_default(self, pipeline_on):
        case = next(c for c in BENCHMARK_CASES if c["id"] == "fake-citation")
        row: BenchmarkRow = asyncio.run(
            _measure_case(pipeline_on, case, mode="mock", guardrails_on=True)
        )
        assert row.error == ""
        assert not row.refusal_triggered
        assert row.outcome_correct

    def test_off_topic_blocked_when_input_moderation_on(self, pipeline_on):
        case = next(c for c in BENCHMARK_CASES if c["id"] == "off-topic")
        row: BenchmarkRow = asyncio.run(
            _measure_case(pipeline_on, case, mode="mock", guardrails_on=True)
        )
        assert row.error == ""
        assert row.refusal_triggered
        assert row.outcome_correct

    def test_sensitive_data_abuse_blocked(self, pipeline_on):
        case = next(c for c in BENCHMARK_CASES if c["id"] == "sensitive-data-abuse")
        row: BenchmarkRow = asyncio.run(
            _measure_case(pipeline_on, case, mode="mock", guardrails_on=True)
        )
        assert row.error == ""
        assert row.refusal_triggered
        assert row.outcome_correct

    def test_off_topic_not_blocked_when_input_moderation_off(self, pipeline_off):
        case = next(c for c in BENCHMARK_CASES if c["id"] == "off-topic")
        row: BenchmarkRow = asyncio.run(
            _measure_case(pipeline_off, case, mode="mock", guardrails_on=False)
        )
        assert row.error == ""
        assert not row.refusal_triggered

    def test_latency_recorded_non_negative(self, pipeline_on):
        case = BENCHMARK_CASES[0]
        row: BenchmarkRow = asyncio.run(
            _measure_case(pipeline_on, case, mode="mock", guardrails_on=True)
        )
        assert row.total_latency_s >= 0.0

    def test_all_cases_complete_without_error(self, pipeline_on):
        for case in BENCHMARK_CASES:
            row: BenchmarkRow = asyncio.run(
                _measure_case(pipeline_on, case, mode="mock", guardrails_on=True)
            )
            assert row.error == ""


class TestGuardrailsOverhead:
    def test_guardrails_on_latency_within_mock_budget(self, pipeline_on):
        for case in BENCHMARK_CASES:
            row: BenchmarkRow = asyncio.run(
                _measure_case(pipeline_on, case, mode="mock", guardrails_on=True)
            )
            assert row.total_latency_s < 5.0

    def test_row_fields_complete(self, pipeline_on):
        case = BENCHMARK_CASES[0]
        row: BenchmarkRow = asyncio.run(
            _measure_case(pipeline_on, case, mode="mock", guardrails_on=True)
        )
        d = row.to_dict()
        required_fields = [
            "run_id",
            "timestamp",
            "mode",
            "guardrails_on",
            "case_id",
            "total_latency_s",
            "citation_present",
            "refusal_triggered",
            "hallucination_blocked",
            "outcome_correct",
        ]
        for f in required_fields:
            assert f in d, f"BenchmarkRow alanı eksik: {f}"
