from __future__ import annotations

from fastapi import Request

from faz2a_hardening import validate_trace_payload
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
        trace_payload={
            "question_raw": "TBK m.49 nedir?",
            "retrieval": {
                "post_rerank_chunks": [
                    {"source_id": "TBK m.49"},
                    {"source_id": "TBK m.50"},
                ]
            },
            "context_assembly": {
                "assembled_context": "[Kaynak: TBK m.49]\nMetin",
                "allowed_source_whitelist": ["TBK m.49", "TBK m.50"],
                "assembled_evidence": [{"source_id": "TBK m.49"}],
            },
            "parsed_query": {"enriched_query": "TBK m.49 nedir?"},
        },
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
        llm_trace={
            "assembly_payload": {"query": "TBK m.49 nedir?", "context": "[Kaynak: TBK m.49]\nMetin"},
            "model_request_payload": {
                "model": "Qwen/Qwen3.5-35B-A3B-FP8",
                "messages": [{"role": "user", "content": "TBK m.49 nedir?"}],
                "temperature": 0.1,
                "max_tokens": 512,
                "extra_body": {"chat_template_kwargs": {"enable_thinking": False}},
            },
            "generation_contract": {
                "temperature": 0.1,
                "top_p": None,
                "top_k": None,
                "max_tokens": 512,
                "stop": None,
                "seed": None,
                "retry_count": 0,
                "timeout_seconds": 180.0,
                "streaming": False,
                "enable_thinking": False,
            },
            "raw_answer_object": {
                "role": "assistant",
                "content": "TBK m.49 [Kaynak: TBK m.49]",
                "extracted_text": "TBK m.49 [Kaynak: TBK m.49]",
                "finish_reason": "stop",
            },
        },
    )

    parity_trace = trace_payload["parity_trace"]
    assert parity_trace["preprojection_hash"]
    assert parity_trace["normalized_parity_hash"]
    assert [item["stage"] for item in parity_trace["stages"]] == [
        "raw_input_request",
        "normalized_request",
        "auth_enriched_request",
        "session_enriched_request",
        "retrieval_input_payload",
        "retrieved_source_id_ordered_list",
        "assembly_payload",
        "model_request_payload",
        "generation_contract",
        "raw_answer_object",
        "response_envelope",
        "eval_client_parsed_object",
        "normalized_parity_object",
    ]
    auth_stage = next(item for item in parity_trace["stages"] if item["stage"] == "auth_enriched_request")
    assert "auth_subject" not in auth_stage["payload"]
    raw_stage = next(item for item in parity_trace["stages"] if item["stage"] == "raw_answer_object")
    assert "ordered_source_id_list" not in raw_stage["payload"]
    assert "visible_citation_projection" not in raw_stage["payload"]


def test_validate_trace_payload_keeps_parity_trace() -> None:
    payload = validate_trace_payload(
        {
            "request_id": "req-123",
            "timestamp": "2026-03-24T17:30:00Z",
            "question_raw": "TBK m.49 nedir?",
            "question_normalized": "tbk m.49 nedir?",
            "parsed_query": {},
            "law_scope_signal": {},
            "question_type": "definition",
            "target_date": "2026-03-24",
            "retrieval_top_k": 20,
            "rerank_list": [],
            "assembled_evidence": [],
            "allowed_source_whitelist": [],
            "answer_contract": {},
            "model_cited_source_ids": [],
            "final_mode": "answer",
            "query_signals": {},
            "retrieval": {},
            "context_assembly": {},
            "generation_outcome": {},
            "parity_trace": {
                "stages": [{"stage": "raw_answer_object", "hash": "abc", "payload": {"content": "x"}}],
                "preprojection_hash": "abc",
                "normalized_parity_hash": "def",
            },
        }
    )
    assert payload["parity_trace"]["preprojection_hash"] == "abc"
