"""OpenAI API Smoke Testleri — Güncellenmiş.

/v1/chat/completions artık routers/chat.py tarafından yönetiliyor.
Bu testler main.py entegrasyonunu ve OpenAI formatı uyumluluğunu doğrular.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from observability import get_metrics_registry
from rag.orchestrator import OrchestratorResponse


def _mock_orch_response(answer: str = "Hukuki bilgi yanıtı.") -> OrchestratorResponse:
    return OrchestratorResponse(
        answer=answer,
        citations=["TBK m.1"],
        blocked=False,
        guardrails_reasons=[],
        verification=None,
    )


@pytest.fixture
def main_client():
    """main.py app'ini mock orchestrator ile başlat."""
    from main import app
    from routers.chat import get_conversation_store, ConversationStore

    # Mock orchestrator: gerçek LLM/DGX bağlantısı gerekmez
    mock_orch = MagicMock()
    mock_orch.use_verification = False
    mock_orch.answer = AsyncMock(return_value=_mock_orch_response())

    app.state.orchestrator = mock_orch
    get_metrics_registry().reset()

    # Temiz store
    new_store = ConversationStore()
    app.dependency_overrides[get_conversation_store] = lambda: new_store

    with TestClient(app) as c:
        yield c, mock_orch

    app.dependency_overrides.clear()


def test_models_endpoint(main_client):
    client, _ = main_client
    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert len(data["data"]) > 0
    assert data["data"][0]["id"] == "hukuk-ai-poc"


def test_single_model_endpoint(main_client):
    client, _ = main_client
    response = client.get("/v1/models/hukuk-ai-poc")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "hukuk-ai-poc"
    assert data["object"] == "model"
    assert data["owned_by"] == "hukuk-ai"


def test_single_model_endpoint_returns_404_for_unknown_model(main_client):
    client, _ = main_client
    response = client.get("/v1/models/does-not-exist")
    assert response.status_code == 404
    assert response.json()["detail"] == "Model not found"


def test_models_endpoint_requires_auth_when_enabled(main_client, monkeypatch):
    client, _ = main_client
    monkeypatch.setenv("API_AUTH_ENABLED", "true")
    monkeypatch.setenv("API_AUTH_KEYS", "secret-key")

    denied = client.get("/v1/models")
    assert denied.status_code == 401

    allowed = client.get("/v1/models", headers={"X-API-Key": "secret-key"})
    assert allowed.status_code == 200

    denied_single = client.get("/v1/models/hukuk-ai-poc")
    assert denied_single.status_code == 401

    allowed_single = client.get("/v1/models/hukuk-ai-poc", headers={"X-API-Key": "secret-key"})
    assert allowed_single.status_code == 200


def test_metrics_endpoint_reports_request_counters(main_client):
    client, _ = main_client
    client.get("/v1/health")
    metrics = client.get("/v1/metrics")
    assert metrics.status_code == 200
    body = metrics.text
    assert 'hukuk_ai_http_requests_total{path="/v1/health",method="GET",status="200"}' in body
    assert "hukuk_ai_http_request_latency_ms_sum" in body


def test_metrics_endpoint_requires_auth_when_enabled(main_client, monkeypatch):
    client, _ = main_client
    monkeypatch.setenv("API_AUTH_ENABLED", "true")
    monkeypatch.setenv("API_AUTH_KEYS", "secret-key")

    denied = client.get("/v1/metrics")
    assert denied.status_code == 401

    allowed = client.get("/v1/metrics", headers={"X-API-Key": "secret-key"})
    assert allowed.status_code == 200


def test_chat_completions_non_streaming(main_client):
    client, mock_orch = main_client
    mock_orch.answer = AsyncMock(return_value=_mock_orch_response("TBK m.49 haksız fiili düzenler."))

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "hukuk-ai-poc",
            "messages": [{"role": "user", "content": "Haksız fiil nedir?"}],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "chat.completion"
    assert len(data["choices"]) > 0
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert len(data["choices"][0]["message"]["content"]) > 0
    assert "session_id" in data
    assert "citations" in data


def test_chat_completions_streaming(main_client):
    client, mock_orch = main_client
    mock_orch.answer = AsyncMock(
        return_value=_mock_orch_response("Bu bir streaming test yanıtıdır.")
    )

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "hukuk-ai-poc",
            "messages": [{"role": "user", "content": "Test stream sorusu"}],
            "stream": True,
        },
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    chunks = []
    for line in response.iter_lines():
        if line:
            line_str = line if isinstance(line, str) else line.decode("utf-8")
            if line_str.startswith("data: ") and "[DONE]" not in line_str:
                data = json.loads(line_str[6:])
                chunks.append(data)

    assert len(chunks) > 0

    # İlk chunk role "assistant" içermeli
    role_chunks = [
        c for c in chunks
        if c.get("object") == "chat.completion.chunk"
        and c.get("choices", [{}])[0].get("delta", {}).get("role") == "assistant"
    ]
    assert len(role_chunks) >= 1

    # Content chunk'ları olmali
    content_chunks = [
        c for c in chunks
        if c.get("object") == "chat.completion.chunk"
        and c.get("choices", [{}])[0].get("delta", {}).get("content")
    ]
    assert len(content_chunks) > 0

    # Son completion chunk'ında finish_reason="stop" olmalı
    finish_chunks = [
        c for c in chunks
        if c.get("object") == "chat.completion.chunk"
        and c.get("choices", [{}])[0].get("finish_reason") == "stop"
    ]
    assert len(finish_chunks) >= 1

    # OpenAI uyumluluğu için standard dışı metadata chunk gönderilmemeli
    meta_chunks = [c for c in chunks if c.get("object") == "chat.completion.metadata"]
    assert meta_chunks == []
