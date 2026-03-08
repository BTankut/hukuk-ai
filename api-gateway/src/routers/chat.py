"""Chat Router — Backlog #7: Chat API + SSE + Multi-turn.

Endpoint'ler:
    POST /v1/chat/completions   — OpenAI-uyumlu chat endpoint (streaming + non-streaming)
    GET  /v1/sessions/{id}      — Oturum geçmişini döndür
    DEL  /v1/sessions/{id}      — Oturumu sil
    GET  /v1/sessions           — Aktif oturum sayısı

Özellikler:
    - OpenAI chat completions formatı (uyumluluk: Open WebUI, diğer OpenAI clientları)
    - SSE (Server-Sent Events) streaming
    - Multi-turn konuşma geçmişi (session bazlı, in-memory)
    - RAG Orchestrator tam entegrasyonu (retrieval + LLM + guardrails + verification)
    - MetadataFilter desteği (kanun filtresi: TBK, TMK, TCK, ...)
    - Verification Engine entegrasyonu (hallüsinasyon önleyici)
    - Conversation context injection (önceki turlar LLM'e iletilir)

SSE Streaming Stratejisi (Faz 1):
    - Orchestrator tam yanıtı üretir (RAG + guardrails + verification)
    - Yanıt kelime grupları hâlinde SSE chunk olarak gönderilir
    - Son chunk'ta citations + verification metadata eklenir
    - Gerçek LLM streaming Faz 2'ye bırakıldı (guardrails mid-stream çatışmasından kaçınmak için)

Multi-turn Yönetimi:
    OpenAI standardı: client geçmişi messages dizisinde taşır.
    Ek özellik: session_id ile server-side history (client geçmişi göndermezse kullanılır).
    History, orchestrator çağrısından önce sorguya enjekte edilir.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from collections import OrderedDict
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from rag.orchestrator import RAGOrchestrator, RetrievedChunk

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


# ---------------------------------------------------------------------------
# Request / Response Modelleri
# ---------------------------------------------------------------------------


class ConversationMessage(BaseModel):
    """Tekil konuşma mesajı (OpenAI formatı)."""

    role: str  # "user" | "assistant" | "system"
    content: str


class ChatCompletionRequest(BaseModel):
    """OpenAI-uyumlu chat completions request.

    Ek alanlar (hukuk-ai özel):
        session_id:       Konuşma oturumu (None → yeni oturum oluşturulur)
        law_filter:       Metadata filtresi (kanun kısaltması: "TBK", "TMK", ...)
        use_verification: Verification Engine etkinleştir/pasifleştir (default: True)
        top_k:            Retrieval hit sayısı (default: 10)
    """

    model: str = "hukuk-ai-poc"
    messages: list[ConversationMessage]
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None

    # Hukuk AI özel alanlar
    session_id: str | None = None
    law_filter: str | None = None
    use_verification: bool = True
    top_k: int = Field(default=10, ge=1, le=50)


class ChatChoice(BaseModel):
    index: int
    message: ConversationMessage
    finish_reason: str = "stop"


class ChatUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """OpenAI-uyumlu chat completions response (hukuk-ai meta eklentisiyle)."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatChoice]
    usage: ChatUsage

    # Hukuk AI ek metadata
    session_id: str | None = None
    citations: list[str] = Field(default_factory=list)
    blocked: bool = False
    guardrails_reasons: list[str] = Field(default_factory=list)
    verification: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# In-memory Conversation Store
# ---------------------------------------------------------------------------


class ConversationStore:
    """Session bazlı konuşma geçmişi yönetimi (in-memory).

    Faz 1: Basit OrderedDict + kapasite limiti.
    Faz 2: Redis veya persistent storage ile değiştirilebilir.

    Thread-safety notu:
        asyncio single-thread modelde thread-safe.
        multi-worker (uvicorn --workers N) için process-shared store gerekir (Redis).
    """

    MAX_SESSIONS: int = 500               # Maksimum aktif oturum sayısı
    MAX_MESSAGES_PER_SESSION: int = 40    # Maksimum mesaj sayısı (user+assistant turlar)

    def __init__(self) -> None:
        # key: session_id, value: list of {"role": ..., "content": ...}
        self._sessions: OrderedDict[str, list[dict[str, str]]] = OrderedDict()

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        """Oturum geçmişini döndür. Oturum yoksa boş liste."""
        return list(self._sessions.get(session_id, []))

    def add_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
    ) -> None:
        """Oturuma kullanıcı + asistan turu ekle."""
        if session_id not in self._sessions:
            # Kapasite aşılmışsa en eski oturumu sil
            if len(self._sessions) >= self.MAX_SESSIONS:
                self._sessions.popitem(last=False)
            self._sessions[session_id] = []

        history = self._sessions[session_id]
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": assistant_message})

        # Maksimum mesaj limitini uygula (ilk turları at, başlangıç context gider)
        if len(history) > self.MAX_MESSAGES_PER_SESSION:
            self._sessions[session_id] = history[-self.MAX_MESSAGES_PER_SESSION :]

        # Bu oturumu "en yeni" konuma taşı
        self._sessions.move_to_end(session_id)

    def clear_session(self, session_id: str) -> bool:
        """Oturumu sil. Var idiyse True döndür."""
        return self._sessions.pop(session_id, None) is not None

    def session_count(self) -> int:
        """Aktif oturum sayısı."""
        return len(self._sessions)


# Global singleton
_conversation_store = ConversationStore()


def get_conversation_store() -> ConversationStore:
    """FastAPI Depends için ConversationStore factory."""
    return _conversation_store


# ---------------------------------------------------------------------------
# Multi-turn Context Builder
# ---------------------------------------------------------------------------


def _build_multiturn_query(
    *,
    last_user_message: str,
    conversation_history: list[dict[str, str]],
    max_history_chars: int = 2000,
) -> str:
    """Konuşma geçmişini son sorguya dahil et.

    Format:
        [Önceki Konuşma]\n
        Kullanıcı: ...
        Asistan: ...
        ...
        [Mevcut Soru]: <last_user_message>

    Çok uzun geçmiş → son N karakteri kısalt.
    Geçmiş yoksa → sadece son soruyu döndür.
    """
    if not conversation_history:
        return last_user_message

    # Geçmişi metin satırlarına dönüştür
    history_lines: list[str] = []
    for msg in conversation_history:
        role_label = "Kullanıcı" if msg["role"] == "user" else "Asistan"
        history_lines.append(f"{role_label}: {msg['content']}")

    history_text = "\n".join(history_lines)

    # Uzunluk limiti
    if len(history_text) > max_history_chars:
        history_text = "..." + history_text[-max_history_chars:]

    return (
        f"[Önceki Konuşma Bağlamı]\n{history_text}\n\n"
        f"[Mevcut Soru]: {last_user_message}"
    )


# ---------------------------------------------------------------------------
# SSE Generator
# ---------------------------------------------------------------------------


async def _stream_sse_response(
    *,
    answer: str,
    session_id: str,
    model: str,
    citations: list[str],
    blocked: bool,
    guardrails_reasons: list[str],
    verification: dict[str, Any] | None,
    words_per_chunk: int = 5,
    delay_between_chunks: float = 0.02,
) -> AsyncGenerator[str, None]:
    """RAG yanıtını OpenAI SSE formatında stream et.

    Akış:
        1. Role chunk (delta: {role: "assistant"})
        2. Content chunks (delta: {content: <kelime grubu>})
        3. Finish chunk (delta: {}, finish_reason: "stop")
        4. Metadata chunk (hukuk-ai özel: citations, verification)
        5. [DONE]
    """
    chunk_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created = int(time.time())

    def _make_delta_chunk(delta: dict[str, Any], finish_reason: str | None = None) -> str:
        payload = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": delta,
                    "finish_reason": finish_reason,
                }
            ],
        }
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    # 1. Role chunk
    yield _make_delta_chunk({"role": "assistant"})
    await asyncio.sleep(0)

    # 2. Content chunks
    words = answer.split()
    for i in range(0, len(words), words_per_chunk):
        group = words[i : i + words_per_chunk]
        # İlk chunk'ta boşluk yok, sonrakilerde boşluk ekle
        content = (" " if i > 0 else "") + " ".join(group)
        yield _make_delta_chunk({"content": content})
        await asyncio.sleep(delay_between_chunks)

    # 3. Finish chunk
    yield _make_delta_chunk({}, finish_reason="stop")
    await asyncio.sleep(0)

    # 4. Hukuk-AI özel metadata chunk
    meta_payload: dict[str, Any] = {
        "id": chunk_id,
        "object": "chat.completion.metadata",
        "session_id": session_id,
        "citations": citations,
        "blocked": blocked,
        "guardrails_reasons": guardrails_reasons,
        "verification": verification,
    }
    yield f"data: {json.dumps(meta_payload, ensure_ascii=False)}\n\n"

    # 5. Done sentinel
    yield "data: [DONE]\n\n"


# ---------------------------------------------------------------------------
# Router Dependencies
# ---------------------------------------------------------------------------


def _get_orchestrator(request: Request) -> RAGOrchestrator:
    """FastAPI app.state'ten RAGOrchestrator al."""
    orchestrator: RAGOrchestrator | None = getattr(request.app.state, "orchestrator", None)
    if orchestrator is None:
        raise HTTPException(
            status_code=503,
            detail="RAG Orchestrator henüz başlatılmadı. Sunucu hazır değil.",
        )
    return orchestrator


def _get_retriever(request: Request) -> Any | None:
    """FastAPI app.state'ten retriever al (opsiyonel)."""
    return getattr(request.app.state, "retriever", None)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/v1/chat/completions",
    summary="OpenAI-uyumlu Chat Completions (RAG + SSE)",
    response_model=ChatCompletionResponse,
    response_model_exclude_none=True,
)
async def chat_completions(
    request_body: ChatCompletionRequest,
    request: Request,
    store: ConversationStore = Depends(get_conversation_store),
) -> Any:
    """OpenAI-uyumlu chat completions endpoint.

    RAG pipeline, SSE streaming ve multi-turn konuşma desteği.

    **Akış:**
    1. Son kullanıcı mesajı çıkarılır
    2. Konuşma geçmişi sorguya enjekte edilir (multi-turn bağlamı)
    3. Retriever ile ilgili mevzuat chunk'ları alınır
    4. RAGOrchestrator → LLM → Guardrails → Verification
    5. Yanıt SSE (stream=True) veya JSON (stream=False) olarak döndürülür

    **Session Yönetimi:**
    - `session_id` verilmezse yeni oturum oluşturulur
    - Yanıt sonrası bu tur session store'a kaydedilir

    **Law Filter:**
    - `law_filter: "TBK"` → sadece TBK maddelerinde arama yapılır
    """
    # ── Doğrulama ────────────────────────────────────────────────────────────
    if not request_body.messages:
        raise HTTPException(status_code=400, detail="messages listesi boş olamaz")

    # Son kullanıcı mesajını çıkar
    last_user_msg: str | None = None
    for msg in reversed(request_body.messages):
        if msg.role == "user":
            last_user_msg = msg.content
            break

    if last_user_msg is None:
        raise HTTPException(
            status_code=400,
            detail="messages içinde en az bir 'user' rol mesajı gerekli",
        )

    if not last_user_msg.strip():
        raise HTTPException(status_code=400, detail="Kullanıcı mesajı boş olamaz")

    # ── Session & Multi-turn ─────────────────────────────────────────────────
    session_id = request_body.session_id or f"sess-{uuid.uuid4().hex[:16]}"

    # Konuşma geçmişi: request'teki messages'ın son user mesajından öncekiler
    request_history: list[dict[str, str]] = []
    for msg in request_body.messages[:-1]:
        if msg.role in {"user", "assistant", "system"}:
            request_history.append({"role": msg.role, "content": msg.content})

    # Eğer client geçmiş mesaj göndermemişse → session store'u kullan
    conversation_history = request_history
    if not conversation_history:
        conversation_history = store.get_history(session_id)

    # Multi-turn sorgu oluştur
    enriched_query = _build_multiturn_query(
        last_user_message=last_user_msg,
        conversation_history=conversation_history,
    )

    # ── Retrieval ─────────────────────────────────────────────────────────────
    retrieved_chunks: list[RetrievedChunk] = []
    retriever = _get_retriever(request)

    if retriever is not None:
        try:
            # Metadata filter (kanun filtresi)
            metadata_filter = None
            if request_body.law_filter:
                from rag.retriever import MetadataFilter

                metadata_filter = MetadataFilter(law_short_name=request_body.law_filter)

            # Embedder varsa embed et, yoksa direkt query string ile dene
            if hasattr(retriever, "retrieve") and callable(retriever.retrieve):
                # MilvusRetriever: retrieve(query=str, top_k=int, metadata_filter=...)
                results, stats = retriever.retrieve(
                    query=last_user_msg,  # Orijinal sorgu (geçmiş eklenmemiş)
                    top_k=request_body.top_k,
                    metadata_filter=metadata_filter,
                )
                retrieved_chunks = [
                    RetrievedChunk(
                        text=r.text,
                        citation=r.citation,
                        source=r.law_short_name,
                        score=r.score,
                        metadata=r.metadata,
                    )
                    for r in results
                ]
                logger.info(
                    "Retrieval: session=%s hits=%d latency=%.0fms",
                    session_id,
                    stats.hit_count,
                    stats.latency_ms,
                )
        except Exception as exc:
            logger.warning(
                "Retrieval hatası (devam ediliyor, chunk yok): %s", exc, exc_info=True
            )

    # ── Orchestrator ─────────────────────────────────────────────────────────
    orchestrator = _get_orchestrator(request)

    # Verification Engine: request'teki tercih + orchestrator'ın mevcut ayarı
    # Not: orchestrator.use_verification request başına override edilemiyor (stateful).
    # Faz 1: orchestrator'da verification global açık/kapalı; request override Faz 2.
    if request_body.use_verification and not orchestrator.use_verification:
        logger.debug("Verification request'te istendi ama orchestrator'da kapalı; atlanıyor.")

    try:
        orch_response = await orchestrator.answer(
            query=enriched_query,
            retrieved_chunks=retrieved_chunks,
        )
    except Exception as exc:
        logger.error("Orchestrator hatası: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"RAG pipeline hatası: {exc}",
        ) from exc

    answer_text = orch_response.answer
    citations = orch_response.citations
    blocked = orch_response.blocked
    guardrails_reasons = orch_response.guardrails_reasons
    verification = orch_response.verification

    # ── Session kaydet ────────────────────────────────────────────────────────
    store.add_turn(session_id, last_user_msg, answer_text)

    model_name = request_body.model

    # ── SSE Streaming Yanıt ───────────────────────────────────────────────────
    if request_body.stream:
        return StreamingResponse(
            _stream_sse_response(
                answer=answer_text,
                session_id=session_id,
                model=model_name,
                citations=citations,
                blocked=blocked,
                guardrails_reasons=guardrails_reasons,
                verification=verification,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",  # Nginx proxy buffering'i devre dışı bırak
                "X-Session-Id": session_id,
            },
        )

    # ── Non-streaming JSON Yanıt ──────────────────────────────────────────────
    prompt_tokens = sum(len(m.content.split()) for m in request_body.messages)
    completion_tokens = len(answer_text.split())

    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
        created=int(time.time()),
        model=model_name,
        choices=[
            ChatChoice(
                index=0,
                message=ConversationMessage(role="assistant", content=answer_text),
                finish_reason="stop",
            )
        ],
        usage=ChatUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
        session_id=session_id,
        citations=citations,
        blocked=blocked,
        guardrails_reasons=guardrails_reasons,
        verification=verification,
    )


@router.get(
    "/v1/sessions/{session_id}",
    summary="Oturum geçmişini döndür",
)
async def get_session(
    session_id: str,
    store: ConversationStore = Depends(get_conversation_store),
) -> dict[str, Any]:
    """Verilen session_id için konuşma geçmişini döndür."""
    history = store.get_history(session_id)
    return {
        "session_id": session_id,
        "message_count": len(history),
        "messages": history,
    }


@router.delete(
    "/v1/sessions/{session_id}",
    summary="Oturumu sil",
)
async def delete_session(
    session_id: str,
    store: ConversationStore = Depends(get_conversation_store),
) -> dict[str, Any]:
    """Verilen session_id için konuşma oturumunu ve geçmişini sil."""
    deleted = store.clear_session(session_id)
    return {
        "session_id": session_id,
        "deleted": deleted,
        "message": "Oturum silindi" if deleted else "Oturum bulunamadı",
    }


@router.get(
    "/v1/sessions",
    summary="Aktif oturum sayısı",
)
async def list_sessions(
    store: ConversationStore = Depends(get_conversation_store),
) -> dict[str, Any]:
    """Aktif oturum sayısını ve limiti döndür."""
    return {
        "active_sessions": store.session_count(),
        "max_sessions": ConversationStore.MAX_SESSIONS,
    }
