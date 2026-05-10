from __future__ import annotations

from config import Settings
from product_controls.privacy import preview_privacy_controls


def test_privacy_default_off() -> None:
    settings = Settings()

    assert settings.enable_product_privacy_pii is False
    result = preview_privacy_controls(
        query="test@example.com",
        enabled=settings.enable_product_privacy_pii,
    )

    assert result.enabled is False
    assert result.privacy_decision == "disabled"


def test_email_redaction_preview() -> None:
    result = preview_privacy_controls(query="Müvekkil test@example.com", enabled=True)

    assert result.pii_detected is True
    assert "EMAIL_ADDRESS" in result.pii_entity_types
    assert "test@example.com" not in result.query_redacted
    assert "[EMAIL_REDACTED]" in result.query_redacted


def test_phone_redaction_preview() -> None:
    result = preview_privacy_controls(query="Telefon 5551234567", enabled=True)

    assert "PHONE_NUMBER" in result.pii_entity_types
    assert "5551234567" not in result.query_redacted
    assert "[PHONE_REDACTED]" in result.query_redacted


def test_identity_number_redaction_preview() -> None:
    result = preview_privacy_controls(query="TC 12345678901", enabled=True)

    assert "TR_ID_NUMBER" in result.pii_entity_types
    assert "12345678901" not in result.query_redacted
    assert "[TR_ID_REDACTED]" in result.query_redacted


def test_trace_redaction_preserves_source_keys() -> None:
    result = preview_privacy_controls(
        query="TC 12345678901",
        trace_payload={
            "question_raw": "TC 12345678901",
            "selected_source_keys": ["TBK:49"],
        },
        enabled=True,
    )

    assert result.trace_redacted["selected_source_keys"] == ["TBK:49"]
    assert "12345678901" not in result.trace_redacted["question_raw"]


def test_audit_minimization_removes_raw_query_when_enabled() -> None:
    result = preview_privacy_controls(
        query="Müvekkil test@example.com",
        audit_payload={
            "request_id": "req-1",
            "raw_query": "Müvekkil test@example.com",
            "selected_source_keys": ["TBK:49"],
        },
        enabled=True,
    )

    assert "raw_query" not in result.audit_minimized
    assert result.audit_minimized["raw_query_chars"] == len("Müvekkil test@example.com")
    assert result.audit_minimized["selected_source_keys"] == ["TBK:49"]
