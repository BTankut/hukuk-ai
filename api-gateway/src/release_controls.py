from __future__ import annotations

import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import HTTPException, Request
from observability import get_metrics_registry

_TR_ID_RE = re.compile(r"\b\d{11}\b")
_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?90[\s-]*)?5\d{2}[\s-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}(?!\d)")
_IP_RE = re.compile(
    r"\b(?:\d{1,3}\.){3}\d{1,3}\b|(?<![:\w])::1(?![:\w])|(?<![:\w])(?:[A-F0-9]{1,4}:){3,7}[A-F0-9]{1,4}(?![:\w])",
    re.IGNORECASE,
)
_SAFE_ID_RE = re.compile(
    r"^(?:req|trace)-[0-9a-f]{20}$|^chatcmpl-[0-9a-f]{12}$|^key-[0-9a-f]{12}$|^[0-9a-f]{64}$",
    re.IGNORECASE,
)
_SAFE_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def release_lane_id() -> str:
    return (os.getenv("RELEASE_LANE_ID") or "current_serving_lane").strip() or "current_serving_lane"


def api_version_label() -> str:
    return (os.getenv("API_VERSION_LABEL") or "2026-03-24-rc-h").strip() or "2026-03-24-rc-h"


def release_controls_strict() -> bool:
    return _to_bool(os.getenv("RELEASE_CONTROLS_STRICT"), release_lane_id().lower() == "rc-h")


def auth_enabled() -> bool:
    return release_controls_strict() or _to_bool(os.getenv("API_AUTH_ENABLED"), False)


def audit_log_enabled() -> bool:
    return release_controls_strict() or _to_bool(os.getenv("AUDIT_LOG_ENABLED"), False)


def allow_anonymous_internal_smoke() -> bool:
    return _to_bool(os.getenv("ALLOW_ANONYMOUS_INTERNAL_SMOKE"), False)


def audit_log_path() -> Path:
    raw = os.getenv("AUDIT_LOG_PATH")
    if raw:
        return Path(raw)
    return _project_root() / "runtime_logs" / "api_audit.jsonl"


def trace_log_dir() -> Path:
    raw = os.getenv("TRACE_LOG_DIR")
    if raw:
        return Path(raw)
    return _project_root() / "logs" / "traces"


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


def _client_host(request: Request) -> str:
    return request.client.host if request.client and request.client.host else ""


def _is_loopback_request(request: Request) -> bool:
    host = _client_host(request)
    return host in {"127.0.0.1", "::1", "localhost"}


def ensure_request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    if isinstance(request_id, str) and request_id:
        return request_id
    header_request_id = request.headers.get("X-Request-ID")
    if header_request_id and header_request_id.strip():
        request_id = header_request_id.strip()
    else:
        request_id = f"req-{uuid.uuid4().hex[:20]}"
    request.state.request_id = request_id
    return request_id


def ensure_trace_id(request: Request) -> str:
    trace_id = getattr(request.state, "trace_id", None)
    if isinstance(trace_id, str) and trace_id:
        return trace_id
    trace_id = f"trace-{uuid.uuid4().hex[:20]}"
    request.state.trace_id = trace_id
    return trace_id


def version_headers(*, request: Request | None = None) -> dict[str, str]:
    headers = {
        "X-Hukuk-AI-API-Version": api_version_label(),
        "X-Hukuk-AI-Lane": release_lane_id(),
    }
    if request is not None:
        headers["X-Request-ID"] = ensure_request_id(request)
    return headers


def require_api_auth(request: Request) -> str:
    request_id = ensure_request_id(request)
    ensure_trace_id(request)
    if not auth_enabled():
        request.state.auth_subject = "anonymous"
        return "anonymous"

    configured = _configured_api_keys()
    if not configured:
        raise HTTPException(
            status_code=503,
            detail="API auth etkin ama API_AUTH_KEYS / API_AUTH_TOKEN tanımlı değil",
            headers=version_headers(request=request),
        )

    presented = _extract_presented_api_key(request)
    if presented is None and allow_anonymous_internal_smoke() and _is_loopback_request(request):
        subject = "internal-smoke"
        request.state.auth_subject = subject
        return subject

    if presented is None or presented not in configured:
        get_metrics_registry().record_auth_failure()
        raise HTTPException(
            status_code=401,
            detail="Yetkisiz istek",
            headers={"WWW-Authenticate": "Bearer", **version_headers(request=request)},
        )

    subject = _subject_for_key(presented)
    request.state.auth_subject = subject
    return subject


def _redact_string(value: str) -> str:
    if _SAFE_ID_RE.fullmatch(value) or _SAFE_TIMESTAMP_RE.fullmatch(value):
        return value
    redacted = _TR_ID_RE.sub("[TR_ID_REDACTED]", value)
    redacted = _EMAIL_RE.sub("[EMAIL_REDACTED]", redacted)
    redacted = _PHONE_RE.sub("[PHONE_REDACTED]", redacted)
    return _IP_RE.sub("[IP_REDACTED]", redacted)


def redact_persisted_payload(payload: Any) -> Any:
    if isinstance(payload, str):
        return _redact_string(payload)
    if isinstance(payload, list):
        return [redact_persisted_payload(item) for item in payload]
    if isinstance(payload, tuple):
        return [redact_persisted_payload(item) for item in payload]
    if isinstance(payload, dict):
        return {key: redact_persisted_payload(value) for key, value in payload.items()}
    return payload


def _read_last_event_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    last_line = ""
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                last_line = line
    if not last_line:
        return None
    try:
        event = json.loads(last_line)
    except json.JSONDecodeError:
        return None
    event_hash = event.get("event_sha256")
    return event_hash if isinstance(event_hash, str) else None


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


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
    request_id: str | None = None,
    trace_id: str | None = None,
    selected_lane: str | None = None,
    final_mode: str | None = None,
    refusal_reason: str | None = None,
    source_ids: list[str] | None = None,
    latency_ms: float | None = None,
    token_accounting: dict[str, Any] | None = None,
    decision_timestamps: dict[str, str] | None = None,
    api_version: str | None = None,
) -> dict[str, Any] | None:
    if not audit_log_enabled():
        return None

    request_id = request_id or ensure_request_id(request)
    trace_id = trace_id or ensure_trace_id(request)
    lane = selected_lane or release_lane_id()
    path = audit_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "ts": int(time.time()),
        "event_type": event_type,
        "request_id": request_id,
        "trace_id": trace_id,
        "response_id": response_id,
        "session_id": session_id,
        "path": request.url.path,
        "method": request.method,
        "auth_subject": getattr(request.state, "auth_subject", "anonymous"),
        "selected_lane": lane,
        "api_version": api_version or api_version_label(),
        "model": model,
        "stream": stream,
        "blocked": blocked,
        "final_mode": final_mode,
        "refusal_reason": refusal_reason,
        "guardrails_reasons": guardrails_reasons,
        "citations": citations,
        "citations_count": len(citations),
        "source_ids": source_ids or [],
        "usage": usage,
        "usage_source": usage_source,
        "token_accounting": token_accounting or {"usage": usage, "source": usage_source},
        "latency_ms": latency_ms,
        "message_count": message_count,
        "user_message_chars": user_message_chars,
        "decision_timestamps": decision_timestamps or {},
    }

    prev_hash = _read_last_event_hash(path)
    event["prev_event_sha256"] = prev_hash
    canonical = _canonical_json(redact_persisted_payload(event))
    event["event_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    redacted_event = redact_persisted_payload(event)

    try:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(redacted_event, ensure_ascii=False) + "\n")
    except OSError:
        get_metrics_registry().record_audit_write_error()
        return None

    get_metrics_registry().record_audit_event()
    return redacted_event


def export_trace_pack(
    *,
    request_id: str,
    payload: dict[str, Any],
) -> Path:
    path = trace_log_dir() / f"{request_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    redacted_payload = redact_persisted_payload(payload)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(redacted_payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return path
