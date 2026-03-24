"""OpenAI Compat — Model Discovery.

Bu modül sadece /v1/models endpoint'ini sağlar.
/v1/chat/completions artık src/routers/chat.py tarafından yönetilmektedir.
"""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Request

from release_controls import api_version_label, release_lane_id, require_api_auth, version_headers

router = APIRouter(tags=["openai-compat"])


@router.get("/v1/models", summary="Kullanılabilir modelleri listele")
async def list_models(
    request: Request,
    _auth_subject: str = Depends(require_api_auth),
) -> dict:
    """OpenAI-uyumlu model listesi.

    Open WebUI ve diğer OpenAI clientları bu endpoint'i model keşfinde kullanır.
    """
    return {
        "object": "list",
        "api_version": api_version_label(),
        "lane": release_lane_id(),
        "headers": version_headers(request=request),
        "data": [
            {
                "id": "hukuk-ai-poc",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "hukuk-ai",
                "description": "AI Hukuk Asistanı — Türk Mevzuatı RAG Modeli",
                "api_version": api_version_label(),
                "lane": release_lane_id(),
            }
        ],
    }
