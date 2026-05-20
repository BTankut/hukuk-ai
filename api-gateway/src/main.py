"""Hukuk AI API Gateway — FastAPI Ana Uygulama.

Başlatma sırası:
    1. Settings & logging
    2. LLMClient + GuardrailsPipeline oluştur
    3. RAGOrchestrator oluştur (verification flag'i env'den)
    4. Retriever oluştur (Milvus varsa MilvusRetriever, yoksa MockRetriever)
    5. app.state'e bileşenleri kaydet
    6. Router'ları include et

Router'lar:
    - /v1/health              → sağlık kontrolü (main.py)
    - /v1/chat/completions    → chat router (SSE + multi-turn + RAG)
    - /v1/sessions/*          → oturum yönetimi (chat router)
    - /v1/models              → OpenAI model listesi (api/openai.py)
    - /v1/chat [POST]         → legacy basit chat (main.py, backward-compat)
"""

from __future__ import annotations

import logging
import os
import time
import uuid

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

from config import get_settings
from guardrails.pipeline import GuardrailsPipeline
from llm.client import LLMClient
from observability import get_metrics_registry
from rag.legal_rag_orchestrator import LegalRagOrchestrator
from rag.orchestrator import RAGOrchestrator, RetrievedChunk
from api.openai import router as openai_router
from release_controls import (
    api_version_label,
    append_audit_event,
    ensure_request_id,
    ensure_trace_id,
    release_lane_id,
    require_api_auth,
    version_headers,
)
from routers.chat import router as chat_router

settings = get_settings()

# Logging
logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# ── Bileşen Fabrikaları ────────────────────────────────────────────────────────

llm_client = LLMClient(settings=settings)
guardrails_pipeline = GuardrailsPipeline(settings=settings)

# Verification Engine: USE_VERIFICATION=true ile etkinleştir (default: off)
_use_verification = os.getenv("USE_VERIFICATION", "false").lower() in {"1", "true", "yes"}
_verification_strict = os.getenv("VERIFICATION_STRICT", "true").lower() in {"1", "true", "yes"}

orchestrator = RAGOrchestrator(
    llm_client=llm_client,
    guardrails=guardrails_pipeline,
    use_verification=_use_verification,
    verification_strict=_verification_strict,
    verification_blocking=True,
)

logger.info(
    "RAGOrchestrator hazır: verification=%s strict=%s",
    _use_verification,
    _verification_strict,
)

# ── Retriever (opsiyonel) ──────────────────────────────────────────────────────

def _build_retriever() -> object | None:
    """Milvus varsa MilvusRetriever döndür, yoksa None.

    MILVUS_ENABLED=false → None (mock/offline mod)
    MILVUS_ENABLED=true  → MilvusRetriever.from_env()
    """
    if os.getenv("MILVUS_ENABLED", "false").lower() not in {"1", "true", "yes"}:
        logger.info("Retriever: MILVUS_ENABLED=false → retriever yok (direkt LLM modu)")
        return None

    try:
        from rag.retriever import MilvusRetriever

        retriever = MilvusRetriever.from_env()
        health = retriever.health_check()
        if health["status"] == "ok":
            logger.info(
                "Retriever: Milvus bağlandı, collection=%s entities=%d",
                health.get("collection"),
                health.get("num_entities", 0),
            )
            return retriever
        else:
            logger.warning("Milvus health check başarısız: %s — retriever yok", health.get("error"))
            return None
    except Exception as exc:
        logger.warning("MilvusRetriever oluşturulamadı: %s — retriever yok", exc)
        return None


# ── FastAPI App ────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    description="AI Hukuk Asistanı — Türk Hukuku RAG API Gateway",
    version="0.1.0",
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    request.state.request_started_at = time.perf_counter()
    request.state.request_wall_started_at = time.time()
    request.state.request_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:20]}"
    request.state.trace_id = f"trace-{uuid.uuid4().hex[:20]}"
    started = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers.update(version_headers(request=request))
        return response
    finally:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        get_metrics_registry().record_http_request(
            path=request.url.path,
            method=request.method,
            status_code=status_code,
            latency_ms=elapsed_ms,
        )

# app.state: bileşenleri request handler'larına inject et
app.state.orchestrator = orchestrator
app.state.retriever = _build_retriever()
app.state.legal_rag_orchestrator = LegalRagOrchestrator.from_settings(
    settings,
    mevzuat_retriever=app.state.retriever,
)
get_metrics_registry().set_lane_health_state(lane=release_lane_id(), healthy=True)

# ── Router'lar ─────────────────────────────────────────────────────────────────

# OpenAI-compat model listesi (/v1/models)
app.include_router(openai_router)

# Chat completions + session yönetimi (gerçek RAG + SSE + multi-turn)
app.include_router(chat_router)


# ── Legacy Endpoints ────────────────────────────────────────────────────────────


class RetrievedChunkPayload(BaseModel):
    text: str
    citation: str
    source: str | None = None
    score: float | None = None
    metadata: dict[str, str] | None = None


class ChatRequest(BaseModel):
    query: str = Field(min_length=2)
    retrieved_chunks: list[RetrievedChunkPayload] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    citations: list[str]
    blocked: bool
    guardrails_reasons: list[str]


@app.get("/v1/health")
async def health() -> dict[str, str]:
    """Servis sağlık kontrolü."""
    legal_runtime_health = app.state.legal_rag_orchestrator.health()
    return {
        "status": "ok",
        "service": settings.app_name,
        "lane": release_lane_id(),
        "api_version": api_version_label(),
        "guardrails": "enabled" if settings.guardrails_enabled else "disabled",
        "retriever": "milvus" if app.state.retriever is not None else "none",
        "verification": "enabled" if _use_verification else "disabled",
        "judicial_runtime_enabled": "enabled" if legal_runtime_health["judicial_runtime_enabled"] else "disabled",
        "judicial_indexes": "available" if legal_runtime_health["judicial_ready"] else "unavailable",
        "judicial_vector_index": str(legal_runtime_health["vector_index_status"]),
    }


@app.get("/v1/metrics", include_in_schema=False)
async def metrics(
    _request: Request,
    _auth_subject: str = Depends(require_api_auth),
) -> PlainTextResponse:
    return PlainTextResponse(get_metrics_registry().render_prometheus())


@app.get("/v1/alerts", include_in_schema=False)
async def alerts(
    request: Request,
    _auth_subject: str = Depends(require_api_auth),
) -> JSONResponse:
    payload = get_metrics_registry().alerts_snapshot()
    payload["lane"] = release_lane_id()
    payload["api_version"] = api_version_label()
    return JSONResponse(payload, headers=version_headers(request=request))


@app.post("/v1/chat", response_model=ChatResponse, deprecated=True)
async def chat_legacy(
    request_body: ChatRequest,
    request: Request,
    _auth_subject: str = Depends(require_api_auth),
) -> ChatResponse:
    """Legacy chat endpoint — chunk'ları dışarıdan alır.

    Yeni entegrasyonlar için /v1/chat/completions kullanın.
    """
    response = await orchestrator.answer(
        query=request_body.query,
        retrieved_chunks=[
            RetrievedChunk(
                text=item.text,
                citation=item.citation,
                source=item.source,
                score=item.score,
                metadata=item.metadata,
            )
            for item in request_body.retrieved_chunks
        ],
    )

    chat_response = ChatResponse(
        answer=response.answer,
        citations=response.citations,
        blocked=response.blocked,
        guardrails_reasons=response.guardrails_reasons,
    )
    append_audit_event(
        event_type="legacy_chat",
        request=request,
        request_id=ensure_request_id(request),
        trace_id=ensure_trace_id(request),
        response_id=f"legacy-{int(os.times().elapsed * 1000)}",
        session_id=None,
        model=settings.dgx_model,
        stream=False,
        blocked=response.blocked,
        citations=response.citations,
        guardrails_reasons=response.guardrails_reasons,
        usage=response.usage,
        usage_source="upstream" if response.usage else "none",
        message_count=1,
        user_message_chars=len(request_body.query),
        selected_lane=release_lane_id(),
        final_mode="blocked" if response.blocked else "answer",
        refusal_reason=response.guardrails_reasons[0] if response.guardrails_reasons else None,
        source_ids=response.citations,
        latency_ms=(time.perf_counter() - getattr(request.state, "request_started_at", time.perf_counter())) * 1000.0,
        decision_timestamps={
            "request_started_at": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ",
                time.gmtime(getattr(request.state, "request_wall_started_at", time.time())),
            ),
            "decision_completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
        api_version=api_version_label(),
    )
    return chat_response
