"""OpenAI Compat — Model Discovery.

Bu modül OpenAI-uyumlu model discovery endpoint'lerini sağlar.
/v1/chat/completions artık src/routers/chat.py tarafından yönetilmektedir.
"""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, Request

from release_controls import api_version_label, release_lane_id, require_api_auth, version_headers

router = APIRouter(tags=["openai-compat"])
_MODEL_ID = "hukuk-ai-poc"


def _build_model_descriptor() -> dict[str, object]:
    return {
        "id": _MODEL_ID,
        "object": "model",
        "created": int(time.time()),
        "owned_by": "hukuk-ai",
        "description": "AI Hukuk Asistanı — Türk Mevzuatı RAG Modeli",
        "api_version": api_version_label(),
        "lane": release_lane_id(),
    }


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
        "data": [_build_model_descriptor()],
    }


@router.get("/v1/models/{model_id}", summary="Belirli bir modeli getir")
async def get_model(
    model_id: str,
    _request: Request,
    _auth_subject: str = Depends(require_api_auth),
) -> dict[str, object]:
    """OpenAI-uyumlu tekil model discovery endpoint'i."""
    if model_id != _MODEL_ID:
        raise HTTPException(status_code=404, detail="Model not found")
    return _build_model_descriptor()
