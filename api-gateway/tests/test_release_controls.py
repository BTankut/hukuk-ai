from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import Request

import release_controls as controls


def _make_request(path: str = "/v1/chat/completions", headers: dict[str, str] | None = None) -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": path,
        "headers": [
            (key.lower().encode("utf-8"), value.encode("utf-8"))
            for key, value in (headers or {}).items()
        ],
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
        "server": ("testserver", 80),
    }
    request = Request(scope)
    request.state.request_started_at = 0.0
    request.state.request_wall_started_at = 0.0
    return request


def test_require_api_auth_allows_internal_smoke_when_enabled(monkeypatch: object) -> None:
    monkeypatch.setenv("RELEASE_CONTROLS_STRICT", "true")
    monkeypatch.setenv("ALLOW_ANONYMOUS_INTERNAL_SMOKE", "true")
    monkeypatch.setenv("API_AUTH_KEYS", "secret")

    subject = controls.require_api_auth(_make_request())

    assert subject == "internal-smoke"


def test_append_audit_event_redacts_pii_and_writes_hash_chain(
    monkeypatch: object,
    tmp_path: Path,
) -> None:
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setenv("AUDIT_LOG_ENABLED", "true")
    monkeypatch.setenv("AUDIT_LOG_PATH", str(audit_path))

    request = _make_request(headers={"X-Request-ID": "req-1"})
    request.state.auth_subject = "key-123"

    event = controls.append_audit_event(
        event_type="chat_completion",
        request=request,
        request_id="req-1",
        trace_id="trace-1",
        response_id="resp-1",
        session_id="sess-1",
        model="hukuk-lora",
        stream=False,
        blocked=False,
        citations=["TBK m.49"],
        guardrails_reasons=[],
        usage={"prompt_tokens": 12, "completion_tokens": 5, "total_tokens": 17},
        usage_source="tokenizer",
        message_count=1,
        user_message_chars=42,
        selected_lane="rc_h",
        final_mode="answer",
        refusal_reason=None,
        source_ids=["TBK m.49"],
        latency_ms=123.0,
        token_accounting={"usage": {"prompt_tokens": 12, "completion_tokens": 5, "total_tokens": 17}},
        decision_timestamps={"decision_completed_at": "2026-03-24T00:00:00Z"},
        persisted_request_snapshot={
            "messages": [
                {
                    "role": "user",
                    "content": "Muvekkil 12345678901 test@example.com 5551234567",
                }
            ]
        },
        persisted_raw_answer_snapshot={"answer_text": "TBK m.49"},
        persisted_response_envelope_snapshot={"response_id": "resp-1"},
    )

    assert event is not None
    line = audit_path.read_text(encoding="utf-8").strip()
    payload = json.loads(line)
    assert payload["event_sha256"]
    assert payload["selected_lane"] == "rc_h"
    assert payload["request_id"] == "req-1"
    assert payload["auth_principal"] == "key-123"
    assert payload["citation_list"] == ["TBK m.49"]
    assert payload["latency"] == 123.0
    assert payload["decision_timestamps"]["decision_completed_at"] == "2026-03-24T00:00:00Z"
    assert "12345678901" not in line
    assert "test@example.com" not in line
    assert "5551234567" not in line
    assert "[TR_ID_REDACTED]" in line
    assert "[EMAIL_REDACTED]" in line
    assert "[PHONE_REDACTED]" in line


def test_redact_persisted_payload_preserves_internal_ids_hashes_and_timestamps() -> None:
    payload = controls.redact_persisted_payload(
        {
            "request_id": "req-1234567890abcdef1234",
            "trace_id": "trace-abcdef1234567890abcd",
            "response_id": "chatcmpl-1234abcd5678",
            "event_sha256": "a" * 64,
            "prev_event_sha256": "b" * 64,
            "auth_subject": "key-123456abcdef",
            "decision_timestamps": {
                "request_started_at": "2026-03-24T09:25:00.123456+00:00",
                "decision_completed_at": "2026-03-24T09:25:01.654321+00:00",
            },
            "session_id": "5551234567",
            "question_raw": "Müvekkil 12345678901 ve test@example.com için 5551234567",
        }
    )

    assert payload["request_id"] == "req-1234567890abcdef1234"
    assert payload["trace_id"] == "trace-abcdef1234567890abcd"
    assert payload["response_id"] == "chatcmpl-1234abcd5678"
    assert payload["event_sha256"] == "a" * 64
    assert payload["prev_event_sha256"] == "b" * 64
    assert payload["auth_subject"] == "key-123456abcdef"
    assert payload["decision_timestamps"]["request_started_at"] == "2026-03-24T09:25:00.123456+00:00"
    assert payload["decision_timestamps"]["decision_completed_at"] == "2026-03-24T09:25:01.654321+00:00"
    assert payload["session_id"] == "[PHONE_REDACTED]"
    assert "[TR_ID_REDACTED]" in payload["question_raw"]
    assert "[EMAIL_REDACTED]" in payload["question_raw"]
    assert "[PHONE_REDACTED]" in payload["question_raw"]


def test_export_trace_pack_redacts_persisted_payload(monkeypatch: object, tmp_path: Path) -> None:
    monkeypatch.setenv("TRACE_LOG_DIR", str(tmp_path))

    trace_path = controls.export_trace_pack(
        request_id="trace-1",
        payload={
            "question_raw": "Müvekkil 12345678901 ve test@example.com hakkında",
            "answer_text": "Telefon 5551234567 [Kaynak: TBK m.49]",
        },
    )

    body = trace_path.read_text(encoding="utf-8")
    assert "12345678901" not in body
    assert "test@example.com" not in body
    assert "5551234567" not in body
    assert "[TR_ID_REDACTED]" in body


def test_version_headers_include_lane_and_api_version(monkeypatch: object) -> None:
    monkeypatch.setenv("RELEASE_LANE_ID", "rc_h")
    monkeypatch.setenv("API_VERSION_LABEL", "2026-03-24-rc-h")
    headers = controls.version_headers(request=_make_request())

    assert headers["X-Hukuk-AI-Lane"] == "rc_h"
    assert headers["X-Hukuk-AI-API-Version"] == "2026-03-24-rc-h"
    assert headers["X-Request-ID"].startswith("req-")
