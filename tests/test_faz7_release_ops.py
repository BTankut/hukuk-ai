from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "faz7"))

import build_operational_regression_gate as op_gate  # noqa: E402
import build_output_parity_report as parity  # noqa: E402
import build_rc_h_manifest as manifest_builder  # noqa: E402
import run_release_smoke_suite as smoke_suite  # noqa: E402


def test_compare_reports_detects_zero_mismatch_and_zero_metric_delta(tmp_path: Path) -> None:
    report = {
        "report_meta": {"eval_family": "faz1-50"},
        "summary": {
            "citation_rate": 0.86,
            "correct_source_rate": 0.83,
            "hallucination_rate": 0.04,
            "refusal_accuracy": 0.94,
        },
        "per_question": [
            {
                "question_id": "TBK-001",
                "answer_text": "TBK m.1 [Kaynak: TBK m.1]",
                "cited_sources": ["TBK m.1"],
                "final_mode": "answer",
                "answer_contract": {
                    "primary_source_id": "TBK m.1",
                    "secondary_source_ids": [],
                    "unsupported_reason": None,
                    "final_mode": "answer",
                },
                "trace": {
                    "hardening_diagnostics": {
                        "visible_citation_projection": {"final_citations": ["TBK m.1"]}
                    }
                },
            }
        ],
    }
    summary = parity.compare_reports(report, report)

    assert summary["mismatch_count"] == 0
    assert summary["family_metric_delta_zero"] is True


def test_compare_reports_detects_normalized_output_mismatch() -> None:
    reference = {
        "report_meta": {"eval_family": "faz1-50"},
        "summary": {
            "citation_rate": 0.86,
            "correct_source_rate": 0.83,
            "hallucination_rate": 0.04,
            "refusal_accuracy": 0.94,
        },
        "per_question": [
            {
                "question_id": "TBK-001",
                "answer_text": "A",
                "cited_sources": ["TBK m.1"],
                "final_mode": "answer",
                "answer_contract": {
                    "primary_source_id": "TBK m.1",
                    "secondary_source_ids": [],
                    "unsupported_reason": None,
                    "final_mode": "answer",
                },
                "trace": {},
            }
        ],
    }
    candidate = {
        "report_meta": {"eval_family": "faz1-50"},
        "summary": reference["summary"],
        "per_question": [
            {
                "question_id": "TBK-001",
                "answer_text": "B",
                "cited_sources": ["TBK m.1"],
                "final_mode": "answer",
                "answer_contract": {
                    "primary_source_id": "TBK m.1",
                    "secondary_source_ids": [],
                    "unsupported_reason": None,
                    "final_mode": "answer",
                },
                "trace": {},
            }
        ],
    }

    summary = parity.compare_reports(reference, candidate)

    assert summary["mismatch_count"] == 1
    assert summary["mismatches"][0]["question_id"] == "TBK-001"


def test_build_gate_passes_with_small_latency_regression() -> None:
    summary = op_gate.build_gate(
        {"latencies_ms": [1000.0, 1100.0, 1200.0]},
        {
            "latencies_ms": [1100.0, 1200.0, 1300.0],
            "recovery": {"healthy_after_restart": True},
        },
    )

    assert summary["latency_budget_pass"] is True
    assert summary["auto_recovery_pass"] is True


def test_run_release_smoke_suite_acceptance(monkeypatch: object) -> None:
    metric_calls = iter(
        [
            """
            hukuk_ai_audit_events_total 1
            hukuk_ai_auth_failure_total 0
            hukuk_ai_citation_total 1
            hukuk_ai_chat_refusal_total{path="/v1/chat/completions",model="hukuk-lora"} 0
            """,
            """
            hukuk_ai_audit_events_total 3
            hukuk_ai_auth_failure_total 1
            hukuk_ai_citation_total 3
            hukuk_ai_chat_refusal_total{path="/v1/chat/completions",model="hukuk-lora"} 1
            """,
        ]
    )

    def fake_fetch_json(url: str, *, api_key: str | None = None, timeout: float = 10.0):
        if url.endswith("/v1/health"):
            return 200, {"status": "ok"}
        if url.endswith("/v1/alerts"):
            return 200, {"lane_unhealthy": False}
        if "/v1/sessions/" in url:
            return 200, {"history": [1, 2, 3, 4]}
        raise AssertionError(url)

    def fake_fetch_text(url: str, *, api_key: str | None = None, timeout: float = 10.0):
        return 200, next(metric_calls)

    responses = iter(
        [
            (
                200,
                {
                    "choices": [{"message": {"content": "TBK m.49 [Kaynak: TBK m.49]"}}],
                    "citations": ["TBK m.49"],
                    "final_mode": "answer",
                    "blocked": False,
                },
            ),
            (
                200,
                {
                    "choices": [{"message": {"content": "Tek cümlelik özet."}}],
                    "citations": ["TBK m.49"],
                    "final_mode": "answer",
                    "blocked": False,
                },
            ),
            (
                200,
                {
                    "choices": [{"message": {"content": "Kapsam dışı."}}],
                    "citations": [],
                    "final_mode": "refusal",
                    "blocked": False,
                },
            ),
        ]
    )

    monkeypatch.setattr(smoke_suite, "_fetch_json", fake_fetch_json)
    monkeypatch.setattr(smoke_suite, "_fetch_text", fake_fetch_text)
    monkeypatch.setattr(smoke_suite, "_post_json", lambda *args, **kwargs: next(responses))
    monkeypatch.setattr(smoke_suite, "_delete_json", lambda *args, **kwargs: (200, {"deleted": True}))
    monkeypatch.setattr(smoke_suite, "_unauthorized_status", lambda *args, **kwargs: 401)

    result = smoke_suite.run_release_smoke_suite(
        base_url="http://127.0.0.1:8004",
        api_key="secret",
        model="hukuk-lora",
        cited_query="cited",
        continuity_query="followup",
        refusal_query="refusal",
        expected_ref="TBK m.49",
        session_id="sess-1",
        timeout=10.0,
    )

    assert result["acceptance"]["auth_enforced"] is True
    assert result["acceptance"]["cited_smoke_pass"] is True
    assert result["acceptance"]["refusal_smoke_pass"] is True
    assert result["acceptance"]["session_continuity_pass"] is True
    assert result["acceptance"]["audit_advancing"] is True
    assert len(result["latencies_ms"]) == 3
    assert result["avg_latency_ms"] >= 0


def test_build_rc_h_manifest_inherits_answer_path_identity(tmp_path: Path) -> None:
    reference_manifest = {
        "candidate_id": "rc-g",
        "base_model_id": "base",
        "adapter_id": "adapter",
        "claim_binding_version": "v3",
        "final_mode_mapping_version": "v3",
        "source_locking_version": "v1",
        "citation_normalization_version": "v1",
        "law_scope_gate_version": "v2",
        "trace_contract_version": "trace-v1",
        "schema_contract_version": "schema-v1",
        "family_reports": [{"family": "faz1-50"}],
    }
    output_path = tmp_path / "manifest.json"

    manifest = manifest_builder.build_manifest(
        reference_manifest=reference_manifest,
        candidate_id="rc-h",
        checkpoint_ref="rc-h-20260324",
        git_commit="deadbeef",
        output_path=output_path,
        allowed_diff_files=["api-gateway/src/release_controls.py"],
    )

    assert manifest["inherits_from"] == "rc-g"
    assert manifest["answer_path_delta"] == []
    assert manifest["allowed_diff_surface"] == ["api-gateway/src/release_controls.py"]
