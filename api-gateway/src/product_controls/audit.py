from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


REQUIRED_AUDIT_FIELDS = (
    "request_id",
    "timestamp",
    "actor_role",
    "endpoint",
    "model_id",
    "collection_id",
    "retrieved_source_keys",
    "selected_source_keys",
    "guardrail_result",
    "verification_result",
    "privacy_result",
    "manual_review_flag",
    "latency",
    "error_state",
)


@dataclass(slots=True)
class ProductAuditPreview:
    enabled: bool
    audit_event_created: bool
    event: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "audit_event_created": self.audit_event_created,
            "event": self.event,
        }


def build_audit_event_preview(
    *,
    enabled: bool = False,
    request_id: str,
    actor_role: str,
    endpoint: str,
    model_id: str,
    collection_id: str,
    retrieved_source_keys: list[str] | None = None,
    selected_source_keys: list[str] | None = None,
    guardrail_result: str = "disabled",
    verification_result: str = "disabled",
    privacy_result: str = "disabled",
    manual_review_flag: bool = False,
    latency: float = 0.0,
    error_state: str | None = None,
    extra: dict[str, Any] | None = None,
) -> ProductAuditPreview:
    """Build a minimized audit event preview without persisting anything."""

    if not enabled:
        return ProductAuditPreview(enabled=False, audit_event_created=False)

    event = {
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "actor_role": actor_role,
        "endpoint": endpoint,
        "model_id": model_id,
        "collection_id": collection_id,
        "retrieved_source_keys": retrieved_source_keys or [],
        "selected_source_keys": selected_source_keys or [],
        "guardrail_result": guardrail_result,
        "verification_result": verification_result,
        "privacy_result": privacy_result,
        "manual_review_flag": manual_review_flag,
        "latency": latency,
        "error_state": error_state,
    }

    for key, value in (extra or {}).items():
        if key in {"raw_query", "raw_answer", "prompt", "messages", "retrieved_chunks"}:
            if isinstance(value, str):
                event[f"{key}_chars"] = len(value)
            elif isinstance(value, list):
                event[f"{key}_count"] = len(value)
            else:
                event[f"{key}_present"] = True

    return ProductAuditPreview(enabled=True, audit_event_created=True, event=event)
