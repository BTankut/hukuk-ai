from __future__ import annotations

from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers.chat import (
    ChatCompletionRequest,
    ConversationMessage,
    ConversationStore,
    _build_canonical_request_snapshot,
    get_conversation_store,
    router as chat_router,
)


def _make_app(store: ConversationStore) -> FastAPI:
    app = FastAPI()
    app.include_router(chat_router)
    app.dependency_overrides[get_conversation_store] = lambda: store
    return app


def test_build_canonical_request_snapshot_includes_session_id() -> None:
    request = ChatCompletionRequest(
        model="hukuk-lora",
        messages=[ConversationMessage(role="user", content="TBK m.49 nedir?")],
        session_id="sess-faz34",
        stream=False,
    )

    snapshot = _build_canonical_request_snapshot(
        request_body=request,
        conversation_history=[],
        last_user_message="TBK m.49 nedir?",
    )

    assert snapshot["session_id"] == "sess-faz34"
    assert snapshot["messages"] == [{"role": "user", "content": "TBK m.49 nedir?"}]


def test_boundary_proxy_perimeter_isolation_skips_local_store_history_and_write(monkeypatch) -> None:
    store = ConversationStore()
    store.add_turn("sess-faz34", "eski soru", "eski cevap")
    app = _make_app(store)

    monkeypatch.setenv("RELEASE_CONTROLS_BOUNDARY_PROXY_ENABLED", "true")
    monkeypatch.setenv("RELEASE_CONTROLS_PERIMETER_SESSION_ISOLATION", "true")
    monkeypatch.setenv("API_AUTH_ENABLED", "false")
    monkeypatch.setenv("AUDIT_LOG_ENABLED", "false")
    monkeypatch.setenv("TRACE_LOG_DIR", "/tmp/faz34-proxy-test-traces")

    captured: dict[str, object] = {}

    async def fake_proxy_canonical_answer_path(*, request_body, conversation_history, last_user_message):
        captured["conversation_history"] = conversation_history
        captured["session_id"] = request_body.session_id
        captured["last_user_message"] = last_user_message
        return (
            {
                "model": request_body.model,
                "messages": [{"role": "user", "content": last_user_message}],
                "session_id": request_body.session_id,
            },
            {
                "id": "chatcmpl-faz34",
                "created": 1,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "TBK m.49 genel hükmüdür."}}],
                "citations": ["TBK m.49"],
                "blocked": False,
                "guardrails_reasons": [],
                "verification": None,
                "answer_contract": {
                    "final_mode": "answer",
                    "primary_source_id": "TBK m.49",
                    "secondary_source_ids": [],
                },
                "final_mode": "answer",
                "final_reason": None,
                "trace": {},
            },
        )

    sidecar_calls: list[dict[str, str]] = []

    def fake_persist_sidecar_session_turn(*, session_id: str, user_message: str, assistant_message: str, max_messages_per_session: int):
        sidecar_calls.append(
            {
                "session_id": session_id,
                "user_message": user_message,
                "assistant_message": assistant_message,
            }
        )
        return {"persisted": True}

    with (
        patch("routers.chat._proxy_canonical_answer_path", side_effect=fake_proxy_canonical_answer_path),
        patch("routers.chat.persist_sidecar_session_turn", side_effect=fake_persist_sidecar_session_turn),
        TestClient(app) as client,
    ):
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "hukuk-lora",
                "messages": [{"role": "user", "content": "TBK m.49 nedir?"}],
                "session_id": "sess-faz34",
                "stream": False,
            },
        )

    assert response.status_code == 200
    assert captured["conversation_history"] == []
    assert captured["session_id"] == "sess-faz34"
    assert response.json()["choices"][0]["message"]["content"] == "TBK m.49 genel hükmüdür."
    assert len(store.get_history("sess-faz34")) == 2
    assert sidecar_calls == [
        {
            "session_id": "sess-faz34",
            "user_message": "TBK m.49 nedir?",
            "assistant_message": "TBK m.49 genel hükmüdür.",
        }
    ]
