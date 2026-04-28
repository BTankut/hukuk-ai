from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from observability import get_metrics_registry
from rag.orchestrator import OrchestratorResponse
from routers.chat import ConversationStore, get_conversation_store


def _mock_orch_response(answer: str = "TBK m.49 haksiz fiil sorumlulugunu duzenler.") -> OrchestratorResponse:
    return OrchestratorResponse(
        answer=answer,
        citations=["TBK m.49"],
        blocked=False,
        guardrails_reasons=[],
        verification=None,
        usage={"prompt_tokens": 10, "completion_tokens": 12, "total_tokens": 22},
    )


@pytest.fixture
def endpoint_client(monkeypatch: pytest.MonkeyPatch):
    from main import app

    monkeypatch.setenv("API_AUTH_ENABLED", "false")
    monkeypatch.setenv("PARITY_TRACE_ENABLED", "true")

    mock_orch = MagicMock()
    mock_orch.use_verification = False
    mock_orch.answer = AsyncMock(return_value=_mock_orch_response())
    app.state.orchestrator = mock_orch
    if hasattr(app.state, "retriever"):
        delattr(app.state, "retriever")

    get_metrics_registry().reset()
    store = ConversationStore()
    app.dependency_overrides[get_conversation_store] = lambda: store
    with TestClient(app) as client:
        yield client, mock_orch
    app.dependency_overrides.clear()


def test_chat_endpoint_non_streaming_schema_and_contract(endpoint_client) -> None:
    client, mock_orch = endpoint_client
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "hukuk-ai-poc",
            "messages": [{"role": "user", "content": "TBK m.49 nedir?"}],
            "stream": False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "chat.completion"
    assert data["model"] == "hukuk-ai-poc"
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert data["choices"][0]["message"]["content"]
    assert data["answer_contract"]["contract_validation"]["contract_valid"] is True
    assert isinstance(data["final_mode"], str)
    mock_orch.answer.assert_awaited_once()


def test_chat_endpoint_include_trace_returns_trace(endpoint_client) -> None:
    client, _ = endpoint_client
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "hukuk-ai-poc",
            "messages": [{"role": "user", "content": "TBK m.49 nedir?"}],
            "include_trace": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["trace"], dict)
    assert data["trace"]["question_raw"] == "TBK m.49 nedir?"
    assert "generation_outcome" in data["trace"]


def test_chat_endpoint_empty_messages_error_shape(endpoint_client) -> None:
    client, _ = endpoint_client
    response = client.post(
        "/v1/chat/completions",
        json={"model": "hukuk-ai-poc", "messages": []},
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("messages listesi")
