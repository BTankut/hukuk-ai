#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-03-30"
COMPACT_DATE = "20260330"

PASS_DECISION = "PASS - RC-P Release Controls Perimeter Isolated"
FAIL_DECISION = "NO-GO - Release Controls Perimeter"

PASS_NEXT_WORK = "rc-p cutover-readiness closure reopen under canonical current authority"
FAIL_NEXT_WORK = "rc-p release-controls perimeter forensics under canonical current authority"

EXPECTED_LANE = "rc_p"
EXPECTED_API_VERSION = "2026-03-30-rc-p"

RELEASE_CONTROLS_EXACT_SET = [
    "mandatory auth",
    "immutable audit logging",
    "persisted PII redaction",
    "Redis session persistence",
    "tokenizer-backed accounting",
    "observability / alerting",
    "API versioning",
    "process supervision",
    "backup / restore",
    "one-command release smoke",
]

REFERENCE_FILES = {
    "faz21": ROOT / "docs" / "FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
    "faz25": ROOT / "docs" / "FAZ25-POST-RC-M-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md",
    "faz26": ROOT / "docs" / "FAZ26-RC-N-RELEASE-CONTROLS-CLOSURE-REOPEN-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-28.md",
    "faz27": ROOT / "docs" / "FAZ27-RC-N-RELEASE-CONTROLS-BOUNDARY-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-28.md",
    "faz31": ROOT / "docs" / "FAZ31-RC-O-REPAIR-TRUTH-RECONCILIATION-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-29.md",
    "faz32": ROOT / "docs" / "FAZ32-RC-O-DISCARD-ARCHIVAL-CLOSURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
    "faz33": ROOT / "docs" / "FAZ33-POST-RC-O-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
}

REFERENCE_MARKERS = {
    "faz21": [
        "PASS - Current Authority Canonicalized",
        "current_canonical_authority_adopted = true",
    ],
    "faz25": [
        "PASS - Post-RC-M Steering Re-Entered Under Canonical Current Authority",
        "active_control_pair = `RC-G vs RC-J`",
    ],
    "faz26": [
        "NO-GO - Release Controls",
        "preprojection_hash_mismatch_count = `166`",
    ],
    "faz27": [
        "PASS - RC-N Boundary Root Cause Localized",
        "effective_control_set = `mandatory auth, immutable audit logging, Redis session persistence`",
    ],
    "faz31": [
        "PASS - RC-O Repair Truth Reconciled Under Canonical Current Authority",
        "current_forensic_truth_adopted = `true`",
    ],
    "faz32": [
        "PASS - RC-O Discard Archived Under Canonical Current Authority",
        "next_official_work = `post-rc-o steering re-entry under canonical current authority`",
    ],
    "faz33": [
        "PASS - Post-RC-O Steering Re-Entered Under Canonical Current Authority",
        "next_candidate_id = `RC-P`",
    ],
}

FAMILY_DEFS = [
    ("faz1-50", ROOT / "configs" / "evaluation" / "test_questions.json", "faz1_50"),
    ("v2-95", ROOT / "configs" / "evaluation" / "test_questions_v2_95.json", "v2_95"),
    ("v3-170", ROOT / "configs" / "evaluation" / "test_questions_v3_170.json", "v3_170"),
]

PERIMETER_RULES = {
    "mandatory_auth_placement": "transport_gateway_only",
    "mandatory_auth_model_visible_mutation_allowed": False,
    "mandatory_auth_prompt_path_access_allowed": False,
    "mandatory_auth_session_object_injection_allowed": False,
    "mandatory_auth_only_immutable_identity_token_allowed": True,
    "immutable_audit_logging_placement": "frozen_snapshot_async_outbox_only",
    "immutable_audit_logging_in_prompt_path_allowed": False,
    "immutable_audit_logging_in_context_assembly_allowed": False,
    "immutable_audit_logging_raw_answer_mutation_allowed": False,
    "immutable_audit_logging_response_envelope_mutation_allowed": False,
    "redis_session_persistence_placement": "sidecar_state_store_only",
    "redis_live_read_write_in_model_path_allowed": False,
    "redis_only_immutable_session_id_visible_to_model_path": True,
    "redis_context_mutation_allowed": False,
    "persisted_pii_redaction_placement": "persistence_and_audit_views_only",
    "persisted_pii_redaction_before_raw_answer_freeze_allowed": False,
    "persisted_pii_redaction_prompt_mutation_allowed": False,
    "persisted_pii_redaction_context_mutation_allowed": False,
    "tokenizer_backed_accounting_placement": "post_response_frozen_snapshot_only",
    "tokenizer_backed_accounting_feedback_into_runtime_allowed": False,
    "tokenizer_backed_accounting_prompt_path_access_allowed": False,
    "observability_alerting_placement": "passive_tap_only",
    "observability_alerting_runtime_mutation_allowed": False,
    "api_versioning_placement": "transport_boundary_only",
    "api_versioning_answer_path_mutation_allowed": False,
    "process_supervision_placement": "host_or_process_boundary_only",
    "process_supervision_answer_path_mutation_allowed": False,
    "backup_restore_placement": "offline_operational_boundary_only",
    "backup_restore_answer_path_mutation_allowed": False,
    "one_command_release_smoke_placement": "non_serving_harness_only",
    "one_command_release_smoke_runtime_attachment_allowed": False,
}

PROHIBITED_MUTATION_FLAGS = {
    "auth_principal_in_model_request_allowed": False,
    "user_id_in_model_request_allowed": False,
    "session_id_context_injection_allowed": False,
    "trace_id_in_prompt_path_allowed": False,
    "request_id_in_prompt_path_allowed": False,
    "audit_id_in_prompt_path_allowed": False,
    "timestamp_feedback_into_answer_path_allowed": False,
    "token_count_feedback_into_answer_path_allowed": False,
    "health_debug_metadata_in_answer_path_allowed": False,
    "observability_metadata_in_answer_path_allowed": False,
    "backup_metadata_in_answer_path_allowed": False,
    "supervision_metadata_in_answer_path_allowed": False,
    "alerting_metadata_in_answer_path_allowed": False,
    "version_negotiation_metadata_in_answer_path_allowed": False,
    "transport_boundary_headers_in_answer_path_allowed": False,
    "redis_runtime_state_in_answer_path_allowed": False,
    "async_outbox_identifier_in_answer_path_allowed": False,
}

BOUNDARY_IDENTITY_TOKEN_CONTRACT = {
    "allowed_model_path_identity_token": "session_id_only",
    "request_id_visible_to_model_path": False,
    "trace_id_visible_to_model_path": False,
    "auth_subject_visible_to_model_path": False,
    "audit_identifier_visible_to_model_path": False,
    "session_token_mutable_payload_allowed": False,
}

REQUIRED_ALERT_KEYS = [
    "lane_unhealthy",
    "audit_write_failure",
    "redis_unavailable",
    "token_accounting_failure",
    "backup_failure",
    "auth_failure_spike",
    "latency_regression_spike",
]

_METRIC_RE = re.compile(r'^([a-zA-Z0-9_:]+)(\{[^}]*\})?\s+([0-9.eE+-]+)$')


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def markdown_table(columns: list[tuple[str, str]], rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(label for _, label in columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        rendered: list[str] = []
        for key, _label in columns:
            value = row.get(key)
            if isinstance(value, bool):
                rendered.append(bool_text(value))
            elif isinstance(value, list):
                rendered.append(", ".join(str(item) for item in value))
            elif isinstance(value, dict):
                rendered.append(json.dumps(value, ensure_ascii=False, sort_keys=True))
            else:
                rendered.append(str(value))
        lines.append("| " + " | ".join(rendered) + " |")
    return lines


def parse_headers_text(text: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for raw_line in text.splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    return headers


def parse_metrics_text(text: str) -> dict[tuple[str, str], float]:
    metrics: dict[tuple[str, str], float] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = _METRIC_RE.match(line)
        if not match:
            continue
        name, labels, value = match.groups()
        metrics[(name, labels or "")] = float(value)
    return metrics


def metric_value(metrics: dict[tuple[str, str], float], name: str, *, source: str | None = None) -> float:
    if source is None:
        return metrics.get((name, ""), 0.0)
    return metrics.get((name, f'{{source="{source}"}}'), 0.0)
