from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "faz2c"))

import capture_narrow_pilot_snapshot as monitoring  # noqa: E402


def test_parse_metrics_text_and_metric_value() -> None:
    metrics = monitoring.parse_metrics_text(
        """
        # HELP sample help
        hukuk_ai_http_requests_total{path="/v1/chat/completions",method="POST",status="200"} 3
        hukuk_ai_audit_events_total 5
        hukuk_ai_usage_source_total{source="upstream"} 4
        """
    )

    assert monitoring.metric_value(metrics, "hukuk_ai_audit_events_total") == 5
    assert monitoring.metric_value(
        metrics,
        "hukuk_ai_http_requests_total",
        labels={"path": "/v1/chat/completions", "method": "POST", "status": "200"},
    ) == 3
    assert monitoring.metric_value(
        metrics,
        "hukuk_ai_usage_source_total",
        labels={"source": "upstream"},
    ) == 4


def test_capture_snapshot_passes_when_metrics_and_smoke_advance(monkeypatch: object) -> None:
    metric_calls = iter(
        [
            """
            hukuk_ai_audit_events_total 1
            hukuk_ai_usage_source_total{source="upstream"} 10
            hukuk_ai_http_requests_total{path="/v1/chat/completions",method="POST",status="200"} 20
            hukuk_ai_chat_refusal_total{path="/v1/chat/completions",model="hukuk-lora"} 0
            """,
            """
            hukuk_ai_audit_events_total 2
            hukuk_ai_usage_source_total{source="upstream"} 11
            hukuk_ai_http_requests_total{path="/v1/chat/completions",method="POST",status="200"} 21
            hukuk_ai_chat_refusal_total{path="/v1/chat/completions",model="hukuk-lora"} 0
            """,
        ]
    )

    monkeypatch.setattr(
        monitoring,
        "fetch_json",
        lambda *args, **kwargs: {"status": "ok", "service": "hukuk-ai-api-gateway"},
    )
    monkeypatch.setattr(monitoring, "fetch_text", lambda *args, **kwargs: next(metric_calls))
    monkeypatch.setattr(
        monitoring,
        "run_smoke",
        lambda **kwargs: monitoring.SmokeResult(
            ok=True,
            latency_ms=1250.0,
            cited_ref_found=True,
            blocked=False,
            answer_preview="TBK m.49 ...",
        ),
    )

    snapshot = monitoring.capture_snapshot(
        base_url="http://127.0.0.1:8000",
        api_key=None,
        smoke_query="q",
        model="hukuk-lora",
        expected_ref="TBK m.49",
        max_tokens=128,
        timeout=60.0,
        latency_budget_ms=30_000.0,
    )

    assert snapshot["rollback_recommended"] is False
    assert snapshot["metrics_delta"]["audit_events_delta"] == 1
    assert snapshot["metrics_delta"]["upstream_usage_delta"] == 1
    assert snapshot["metrics_delta"]["successful_chat_delta"] == 1
    assert snapshot["rollback_reasons"] == []


def test_capture_snapshot_recommends_rollback_on_failures(monkeypatch: object) -> None:
    metric_calls = iter(
        [
            """
            hukuk_ai_audit_events_total 3
            hukuk_ai_usage_source_total{source="upstream"} 7
            hukuk_ai_http_requests_total{path="/v1/chat/completions",method="POST",status="200"} 15
            hukuk_ai_chat_refusal_total{path="/v1/chat/completions",model="hukuk-lora"} 0
            """,
            """
            hukuk_ai_audit_events_total 3
            hukuk_ai_usage_source_total{source="upstream"} 7
            hukuk_ai_http_requests_total{path="/v1/chat/completions",method="POST",status="200"} 15
            hukuk_ai_chat_refusal_total{path="/v1/chat/completions",model="hukuk-lora"} 1
            """,
        ]
    )

    monkeypatch.setattr(
        monitoring,
        "fetch_json",
        lambda *args, **kwargs: {"status": "ok", "service": "hukuk-ai-api-gateway"},
    )
    monkeypatch.setattr(monitoring, "fetch_text", lambda *args, **kwargs: next(metric_calls))
    monkeypatch.setattr(
        monitoring,
        "run_smoke",
        lambda **kwargs: monitoring.SmokeResult(
            ok=False,
            latency_ms=45_000.0,
            cited_ref_found=False,
            blocked=True,
            answer_preview="",
            error="failed",
        ),
    )

    snapshot = monitoring.capture_snapshot(
        base_url="http://127.0.0.1:8000",
        api_key=None,
        smoke_query="q",
        model="hukuk-lora",
        expected_ref="TBK m.49",
        max_tokens=128,
        timeout=60.0,
        latency_budget_ms=30_000.0,
    )

    assert snapshot["rollback_recommended"] is True
    assert set(snapshot["rollback_reasons"]) == {
        "cited_smoke_failed",
        "audit_not_advancing",
        "upstream_usage_not_advancing",
        "chat_request_counter_not_advancing",
        "unexpected_refusal_delta",
        "latency_budget_exceeded",
    }


def test_main_writes_output_file(tmp_path: Path, monkeypatch: object) -> None:
    snapshot = {
        "captured_at": "2026-03-23T08:11:00Z",
        "rollback_recommended": False,
        "rollback_reasons": [],
    }
    monkeypatch.setattr(monitoring, "capture_snapshot", lambda **kwargs: snapshot)
    output_path = tmp_path / "snapshot.json"

    exit_code = monitoring.main.__wrapped__ if hasattr(monitoring.main, "__wrapped__") else None
    assert exit_code is None

    argv = [
        "capture_narrow_pilot_snapshot.py",
        "--output-path",
        str(output_path),
    ]
    monkeypatch.setattr(sys, "argv", argv)

    result = monitoring.main()

    assert result == 0
    assert json.loads(output_path.read_text(encoding="utf-8")) == snapshot
