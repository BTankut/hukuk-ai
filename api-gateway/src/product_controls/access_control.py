from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ROLES = {
    "system_admin",
    "legal_reviewer",
    "product_reviewer",
    "developer_operator",
    "read_only_auditor",
    "external_user",
}

_ACTION_PERMISSIONS = {
    "trace_access": {"system_admin", "read_only_auditor"},
    "review_queue": {"system_admin", "legal_reviewer", "product_reviewer"},
    "pii_export": {"system_admin"},
    "audit_summary": {"system_admin", "developer_operator", "read_only_auditor"},
    "product_controls_dry_run": {"system_admin", "developer_operator"},
}


@dataclass(slots=True)
class ProductAccessDecision:
    enabled: bool
    actor_role: str
    action: str
    allowed: bool
    decision: str
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "actor_role": self.actor_role,
            "action": self.action,
            "allowed": self.allowed,
            "decision": self.decision,
            "reason": self.reason,
        }


def evaluate_access_control(
    *,
    actor_role: str,
    action: str,
    enabled: bool = False,
) -> ProductAccessDecision:
    """Preview role/action access decisions without enforcing live routes."""

    if not enabled:
        return ProductAccessDecision(
            enabled=False,
            actor_role=actor_role,
            action=action,
            allowed=True,
            decision="disabled",
        )

    if actor_role not in ROLES:
        return ProductAccessDecision(
            enabled=True,
            actor_role=actor_role,
            action=action,
            allowed=False,
            decision="deny_unknown_role",
            reason="unknown_role",
        )

    allowed_roles = _ACTION_PERMISSIONS.get(action)
    if allowed_roles is None:
        return ProductAccessDecision(
            enabled=True,
            actor_role=actor_role,
            action=action,
            allowed=False,
            decision="deny_unknown_action",
            reason="unknown_action",
        )

    allowed = actor_role in allowed_roles
    return ProductAccessDecision(
        enabled=True,
        actor_role=actor_role,
        action=action,
        allowed=allowed,
        decision="allow" if allowed else "deny_route_not_allowed",
        reason=None if allowed else "role_not_allowed_for_action",
    )
