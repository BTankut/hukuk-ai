from __future__ import annotations

from config import Settings
from product_controls.access_control import evaluate_access_control
from product_controls.audit import REQUIRED_AUDIT_FIELDS, build_audit_event_preview


def _audit_preview(enabled: bool):
    return build_audit_event_preview(
        enabled=enabled,
        request_id="req-1",
        actor_role="developer_operator",
        endpoint="/internal/product-controls/smoke",
        model_id="hukuk-ai-poc",
        collection_id="mevzuat-shadow",
        retrieved_source_keys=["TBK:49"],
        selected_source_keys=["TBK:49"],
        guardrail_result="allow",
        verification_result="pass",
        privacy_result="pass_redacted",
        manual_review_flag=False,
        latency=1.2,
        error_state=None,
        extra={"raw_query": "Müvekkil test@example.com"},
    )


def test_audit_logging_default_off() -> None:
    settings = Settings()

    assert settings.enable_product_audit_logging is False
    result = _audit_preview(enabled=settings.enable_product_audit_logging)

    assert result.enabled is False
    assert result.audit_event_created is False
    assert result.event == {}


def test_audit_event_minimized_shape_valid() -> None:
    result = _audit_preview(enabled=True)

    assert result.audit_event_created is True
    assert set(REQUIRED_AUDIT_FIELDS).issubset(result.event)
    assert "raw_query" not in result.event
    assert result.event["raw_query_chars"] == len("Müvekkil test@example.com")
    assert result.event["selected_source_keys"] == ["TBK:49"]


def test_access_control_default_off() -> None:
    settings = Settings()

    assert settings.enable_product_access_control is False
    result = evaluate_access_control(
        actor_role="external_user",
        action="trace_access",
        enabled=settings.enable_product_access_control,
    )

    assert result.enabled is False
    assert result.allowed is True
    assert result.decision == "disabled"


def test_external_user_denied_trace_access_when_enabled() -> None:
    result = evaluate_access_control(actor_role="external_user", action="trace_access", enabled=True)

    assert result.allowed is False
    assert result.decision == "deny_route_not_allowed"


def test_legal_reviewer_allowed_review_queue_when_enabled() -> None:
    result = evaluate_access_control(actor_role="legal_reviewer", action="review_queue", enabled=True)

    assert result.allowed is True
    assert result.decision == "allow"


def test_developer_operator_denied_pii_export_when_enabled() -> None:
    result = evaluate_access_control(actor_role="developer_operator", action="pii_export", enabled=True)

    assert result.allowed is False
    assert result.decision == "deny_route_not_allowed"
