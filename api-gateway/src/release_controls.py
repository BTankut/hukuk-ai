from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from fastapi import HTTPException, Request
from observability import get_metrics_registry


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def auth_enabled() -> bool:
    return _to_bool(os.getenv("API_AUTH_ENABLED"), False)


def audit_log_enabled() -> bool:
    return _to_bool(os.getenv("AUDIT_LOG_ENABLED"), False)


def audit_log_path() -> Path:
    raw = os.getenv("AUDIT_LOG_PATH")
    if raw:
        return Path(raw)
    return _project_root() / "runtime_logs" / "api_audit.jsonl"


def _configured_api_keys() -> set[str]:
    raw = os.getenv("API_AUTH_KEYS") or os.getenv("API_AUTH_TOKEN") or ""
    return {item.strip() for item in raw.split(",") if item.strip()}


def _extract_presented_api_key(request: Request) -> str | None:
    bearer = request.headers.get("Authorization")
    if bearer:
        scheme, _, token = bearer.partition(" ")
        if scheme.lower() == "bearer" and token.strip():
            return token.strip()

    api_key = request.headers.get("X-API-Key")
    if api_key and api_key.strip():
        return api_key.strip()
    return None


def _subject_for_key(api_key: str) -> str:
    digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:12]
    return f"key-{digest}"


def require_api_auth(request: Request) -> str:
    if not auth_enabled():
        request.state.auth_subject = "anonymous"
        return "anonymous"

    configured = _configured_api_keys()
    if not configured:
        raise HTTPException(
            status_code=503,
            detail="API auth etkin ama API_AUTH_KEYS / API_AUTH_TOKEN tanımlı değil",
        )

    presented = _extract_presented_api_key(request)
    if presented is None or presented not in configured:
        raise HTTPException(
            status_code=401,
            detail="Yetkisiz istek",
            headers={"WWW-Authenticate": "Bearer"},
        )

    subject = _subject_for_key(presented)
    request.state.auth_subject = subject
    return subject


def append_audit_event(
    *,
    event_type: str,
    request: Request,
    response_id: str,
    session_id: str | None,
    model: str,
    stream: bool,
    blocked: bool,
    citations: list[str],
    guardrails_reasons: list[str],
    usage: dict[str, int] | None,
    usage_source: str,
    message_count: int,
    user_message_chars: int,
) -> dict[str, Any] | None:
    if not audit_log_enabled():
        return None

    event = {
        "ts": int(time.time()),
        "event_type": event_type,
        "response_id": response_id,
        "session_id": session_id,
        "path": request.url.path,
        "method": request.method,
        "client_host": request.client.host if request.client else None,
        "auth_subject": getattr(request.state, "auth_subject", "anonymous"),
        "model": model,
        "stream": stream,
        "blocked": blocked,
        "guardrails_reasons": guardrails_reasons,
        "citations": citations,
        "citations_count": len(citations),
        "usage": usage,
        "usage_source": usage_source,
        "message_count": message_count,
        "user_message_chars": user_message_chars,
    }

    path = audit_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    get_metrics_registry().record_audit_event()
    return event
