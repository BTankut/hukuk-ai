from __future__ import annotations

from fastapi import Request

from routers.chat import (
    ChatCompletionRequest,
    ConversationMessage,
    _attach_parity_trace,
)


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
    request.state.trace_id = "trace-abcdef1234567890abcd"
    request.state.auth_subject = "internal-smoke"
    return request


def test_attach_parity_trace_adds_stage_chain(monkeypatch: object) -> None:
    monkeypatch.setenv("PARITY_TRACE_ENABLED", "true")
    request_body = ChatCompletionRequest(
        messages=[ConversationMessage(role="user", content="TBK m.49 nedir?")],
        include_trace=True,
    )

    trace_payload = _attach_parity_trace(
        trace_payload={"question_raw": "TBK m.49 nedir?"},
        request=_make_request(),
        request_body=request_body,
        session_id="sess-1",
        conversation_history=[],
        pre_answer_payload={"decision_lane": "rag", "user_message": "TBK m.49 nedir?"},
        answer_text="TBK m.49 [Kaynak: TBK m.49]",
        citations=["TBK m.49"],
        blocked=False,
        guardrails_reasons=[],
        verification=None,
        answer_contract={
            "primary_source_id": "TBK m.49",
            "secondary_source_ids": [],
            "final_mode": "answer",
        },
        final_mode="answer",
        final_reason=None,
    )

    parity_trace = trace_payload["parity_trace"]
    assert parity_trace["preprojection_hash"]
    assert [item["stage"] for item in parity_trace["stages"]] == [
        "raw_input_request",
        "normalized_request",
        "auth_session_trace_enriched_request",
        "pre_answer_handler_payload",
        "raw_answer_object",
        "visible_response_projection",
        "api_response_envelope",
    ]
