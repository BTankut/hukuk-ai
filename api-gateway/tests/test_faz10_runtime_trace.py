from __future__ import annotations

from fastapi import Request

from routers.chat import _session_namespace_stage_payload


def _make_request() -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/v1/chat/completions",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
        "server": ("testserver", 80),
    }
    request = Request(scope)
    request.state.request_id = "req-1234567890abcdef1234"
    return request


def test_session_namespace_stage_payload_redacts_request_local_suffix(monkeypatch) -> None:
    monkeypatch.setenv("SESSION_STORE_NAMESPACE", "hukuk-ai-topology-l0")
    monkeypatch.setenv("PARITY_SESSION_NAMESPACE_MODE", "fresh_per_request")

    payload = _session_namespace_stage_payload(request=_make_request(), session_id="sess-1")

    assert payload == {
        "mode": "fresh_per_request",
        "namespace": "hukuk-ai-topology-l0:<request-local>",
        "request_local_suffix": "request_id",
        "session_id_present": True,
    }


def test_session_namespace_stage_payload_keeps_canonical_namespace(monkeypatch) -> None:
    monkeypatch.setenv("SESSION_STORE_NAMESPACE", "hukuk-ai-topology-l1")
    monkeypatch.setenv("PARITY_SESSION_NAMESPACE_MODE", "canonical")

    payload = _session_namespace_stage_payload(request=_make_request(), session_id="sess-1")

    assert payload == {
        "mode": "canonical",
        "namespace": "hukuk-ai-topology-l1",
        "request_local_suffix": None,
        "session_id_present": True,
    }
