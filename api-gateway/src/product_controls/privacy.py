from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


_TR_ID_RE = re.compile(r"\b\d{11}\b")
_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?90[\s-]*)?5\d{2}[\s-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}(?!\d)")
_RAW_AUDIT_KEYS = {"raw_query", "raw_answer", "prompt", "messages", "retrieved_chunks"}
_SOURCE_KEY_NAMES = {"source_key", "source_keys", "selected_source_keys", "retrieved_source_keys", "citations"}


@dataclass(slots=True)
class ProductPrivacyPreview:
    enabled: bool
    privacy_decision: str
    pii_detected: bool = False
    pii_entity_types: list[str] = field(default_factory=list)
    query_redacted: str | None = None
    trace_redacted: dict[str, Any] = field(default_factory=dict)
    audit_minimized: dict[str, Any] = field(default_factory=dict)
    reviewer_payload: dict[str, Any] = field(default_factory=dict)
    pii_event_metrics: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "privacy_decision": self.privacy_decision,
            "pii_detected": self.pii_detected,
            "pii_entity_types": self.pii_entity_types,
            "query_redacted": self.query_redacted,
            "trace_redacted": self.trace_redacted,
            "audit_minimized": self.audit_minimized,
            "reviewer_payload": self.reviewer_payload,
            "pii_event_metrics": self.pii_event_metrics,
        }


def detect_pii(text: str) -> dict[str, int]:
    counts = {
        "TR_ID_NUMBER": len(_TR_ID_RE.findall(text or "")),
        "EMAIL_ADDRESS": len(_EMAIL_RE.findall(text or "")),
        "PHONE_NUMBER": len(_PHONE_RE.findall(text or "")),
    }
    return {key: value for key, value in counts.items() if value}


def redact_text(text: str) -> str:
    redacted = _TR_ID_RE.sub("[TR_ID_REDACTED]", text or "")
    redacted = _EMAIL_RE.sub("[EMAIL_REDACTED]", redacted)
    return _PHONE_RE.sub("[PHONE_REDACTED]", redacted)


def _redact_payload(value: Any, *, key_name: str | None = None) -> Any:
    if key_name in _SOURCE_KEY_NAMES:
        return value
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [_redact_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: _redact_payload(item, key_name=str(key)) for key, item in value.items()}
    return value


def _minimize_audit_payload(payload: dict[str, Any]) -> dict[str, Any]:
    minimized: dict[str, Any] = {}
    for key, value in payload.items():
        if key in _RAW_AUDIT_KEYS:
            if isinstance(value, str):
                minimized[f"{key}_chars"] = len(value)
            elif isinstance(value, list):
                minimized[f"{key}_count"] = len(value)
            else:
                minimized[f"{key}_present"] = True
            continue
        minimized[key] = _redact_payload(value, key_name=key)
    return minimized


def preview_privacy_controls(
    *,
    query: str,
    trace_payload: dict[str, Any] | None = None,
    audit_payload: dict[str, Any] | None = None,
    reviewer_payload: dict[str, Any] | None = None,
    enabled: bool = False,
) -> ProductPrivacyPreview:
    """Preview privacy controls without writing audit or trace artifacts."""

    if not enabled:
        return ProductPrivacyPreview(enabled=False, privacy_decision="disabled")

    trace = trace_payload or {}
    audit = audit_payload or {}
    reviewer = reviewer_payload or {}
    combined_text = " ".join(
        [
            query or "",
            str(trace),
            str(audit),
            str(reviewer),
        ]
    )
    metrics = detect_pii(combined_text)
    pii_types = sorted(metrics)
    pii_detected = bool(pii_types)

    return ProductPrivacyPreview(
        enabled=True,
        privacy_decision="pass_redacted" if pii_detected else "pass_no_pii",
        pii_detected=pii_detected,
        pii_entity_types=pii_types,
        query_redacted=redact_text(query),
        trace_redacted=_redact_payload(trace),
        audit_minimized=_minimize_audit_payload(audit),
        reviewer_payload=_redact_payload(reviewer),
        pii_event_metrics={f"pii_{key.lower()}_count": value for key, value in metrics.items()},
    )
