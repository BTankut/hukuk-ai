from __future__ import annotations

from typing import Any, Sequence


def build_generation_contract(
    settings: Any,
    *,
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    return {
        "temperature": temperature,
        "top_p": settings.dgx_top_p,
        "top_k": settings.dgx_top_k,
        "max_tokens": max_tokens,
        "stop": None,
        "seed": settings.dgx_seed,
        "retry_count": settings.dgx_retry_count,
        "timeout_seconds": settings.dgx_request_timeout_seconds,
        "streaming": False,
        "enable_thinking": settings.dgx_enable_thinking,
    }


def build_request_payload(
    settings: Any,
    *,
    messages: Sequence[Any],
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": settings.dgx_model,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "extra_body": {"chat_template_kwargs": {"enable_thinking": settings.dgx_enable_thinking}},
    }
    if settings.dgx_top_p is not None:
        payload["top_p"] = settings.dgx_top_p
    if settings.dgx_seed is not None:
        payload["seed"] = settings.dgx_seed
    if settings.dgx_top_k is not None:
        payload["extra_body"]["top_k"] = settings.dgx_top_k
    return payload
