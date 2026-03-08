"""OpenAI Compat — Model Discovery.

Bu modül sadece /v1/models endpoint'ini sağlar.
/v1/chat/completions artık src/routers/chat.py tarafından yönetilmektedir.
"""

from __future__ import annotations

import time

from fastapi import APIRouter

router = APIRouter(tags=["openai-compat"])


@router.get("/v1/models", summary="Kullanılabilir modelleri listele")
async def list_models() -> dict:
    """OpenAI-uyumlu model listesi.

    Open WebUI ve diğer OpenAI clientları bu endpoint'i model keşfinde kullanır.
    """
    return {
        "object": "list",
        "data": [
            {
                "id": "hukuk-ai-poc",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "hukuk-ai",
                "description": "AI Hukuk Asistanı — Türk Mevzuatı RAG Modeli",
            }
        ],
    }
