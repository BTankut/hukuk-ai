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
RESULT_REPORT_NAME = (
    f"FAZ36-RC-Q-RELEASE-CONTROLS-PERIMETER-REPAIR-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-{DATE}.md"
)

PASS_DECISION = "PASS - RC-Q Perimeter Repair Gate Cleared"
FAIL_REFERENCE = "NO-GO - Reference Pack Contradiction"
FAIL_TOPOLOGY = "NO-GO - Topology Contract Breach"
FAIL_CURRENT_AUTHORITY = "NO-GO - Current Authority Breach"
FAIL_UPSTREAM = "NO-GO - RC-Q Upstream Equality Breach"
FAIL_FRONTIER = "NO-GO - RC-Q Frontier Repair Failed"
FAIL_RESPONSE = "NO-GO - RC-Q Response Envelope Repair Failed"
FAIL_ACCEPTANCE = "NO-GO - RC-Q Release Controls Acceptance Failed"
FAIL_PARITY = "NO-GO - RC-Q Full-Family Parity Failed"
FAIL_RETENTION = "NO-GO - RC-Q Retention Failed"
FAIL_INCONCLUSIVE = "NO-GO - RC-Q Repair Gate Inconclusive"

DECISION_TO_NEXT_WORK = {
    PASS_DECISION: "rc-q release-controls closure reopen under canonical current authority",
    FAIL_REFERENCE: "reference pack reconciliation under canonical current authority",
    FAIL_TOPOLOGY: "post-rc-p steering normalization under canonical current authority",
    FAIL_CURRENT_AUTHORITY: "rc-g vs rc-j current authority recapture under canonical current authority",
    FAIL_UPSTREAM: "rc-q upstream equality recapture under canonical current authority",
    FAIL_FRONTIER: "rc-q release-controls perimeter repair recapture under canonical current authority",
    FAIL_RESPONSE: "rc-q response-envelope perimeter repair recapture under canonical current authority",
    FAIL_ACCEPTANCE: "rc-q release-controls acceptance forensics under canonical current authority",
    FAIL_PARITY: "rc-q perimeter spillover forensics under canonical current authority",
    FAIL_RETENTION: "rc-q release-controls retention forensics under canonical current authority",
    FAIL_INCONCLUSIVE: "rc-q repair truth reconciliation under canonical current authority",
}

EXPECTED_LANE = "rc_q"
EXPECTED_API_VERSION = "2026-03-30-rc-q"

REFERENCE_FILES = {
    "faz21": ROOT / "docs" / "FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
    "faz25": ROOT / "docs" / "FAZ25-POST-RC-M-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md",
    "faz26": ROOT / "docs" / "FAZ26-RC-N-RELEASE-CONTROLS-CLOSURE-REOPEN-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-28.md",
    "faz27": ROOT / "docs" / "FAZ27-RC-N-RELEASE-CONTROLS-BOUNDARY-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-28.md",
    "faz31": ROOT / "docs" / "FAZ31-RC-O-REPAIR-TRUTH-RECONCILIATION-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-29.md",
    "faz32": ROOT / "docs" / "FAZ32-RC-O-DISCARD-ARCHIVAL-CLOSURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
    "faz33": ROOT / "docs" / "FAZ33-POST-RC-O-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
    "faz34": ROOT / "docs" / "FAZ34-RC-P-RELEASE-CONTROLS-PERIMETER-ISOLATION-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
    "faz35": ROOT / "docs" / "FAZ35-RC-P-RELEASE-CONTROLS-PERIMETER-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
}

REFERENCE_MARKERS = {
    "faz21": [
        "PASS - Current Authority Canonicalized",
        "current_canonical_authority_adopted = true",
    ],
    "faz25": [
        "PASS - Post-RC-M Steering Re-Entered Under Canonical Current Authority",
        "active_quality_reference = `RC-G`",
    ],
    "faz26": [
        "NO-GO - Release Controls",
        "| persisted PII redaction | `FAIL` |",
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
        "archive_status = `closed`",
    ],
    "faz33": [
        "PASS - Post-RC-O Steering Re-Entered Under Canonical Current Authority",
        "next_candidate_id = `RC-P`",
    ],
    "faz34": [
        "NO-GO - Release Controls Perimeter",
        "preprojection_hash_mismatch_count = `174`",
        "response_envelope_hash_mismatch_count = `109`",
    ],
    "faz35": [
        "PASS - RC-P Perimeter Root Cause Localized",
        "dominant_stage = `P11`",
        "dominant_interaction_class = `multi_control_interaction_runtime_mutation`",
    ],
}

FAZ35_CURRENT_AUTHORITY_JSON = (
    ROOT / "evaluation" / "reports" / "faz35-rc-g-vs-rc-j-current-authority-check-2026-03-30.json"
)
FAZ35_TARGETED_ACCEPTANCE_MD = (
    ROOT / "evaluation" / "reports" / "faz34-rc-p-release-controls-targeted-acceptance-2026-03-30.md"
)
FAZ35_RETENTION_MD = (
    ROOT / "evaluation" / "reports" / "faz34-rc-p-release-controls-retention-matrix-2026-03-30.md"
)
FAZ34_MODEL_VISIBLE_REPORTS = {
    "faz1-50": ROOT / "evaluation" / "reports" / "faz34_rc_g_vs_rc_p_model_visible_faz1_50_20260330.json",
    "v2-95": ROOT / "evaluation" / "reports" / "faz34_rc_g_vs_rc_p_model_visible_v2_95_20260330.json",
    "v3-170": ROOT / "evaluation" / "reports" / "faz34_rc_g_vs_rc_p_model_visible_v3_170_20260330.json",
}
FAZ34_OUTPUT_PARITY_REPORTS = {
    "faz1-50": ROOT / "evaluation" / "reports" / "faz34_rc_g_vs_rc_p_output_parity_faz1_50_20260330.json",
    "v2-95": ROOT / "evaluation" / "reports" / "faz34_rc_g_vs_rc_p_output_parity_v2_95_20260330.json",
    "v3-170": ROOT / "evaluation" / "reports" / "faz34_rc_g_vs_rc_p_output_parity_v3_170_20260330.json",
}

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

BRIDGE_CONTRACT = {
    "deep_copy_barrier_before_P11": True,
    "live_object_reference_reuse_allowed": False,
    "perimeter_callback_into_model_request_allowed": False,
    "perimeter_callback_into_retrieval_request_allowed": False,
    "perimeter_callback_into_assembled_context_allowed": False,
    "perimeter_callback_into_preprojection_allowed": False,
    "perimeter_callback_into_raw_answer_allowed": False,
    "perimeter_callback_into_response_envelope_allowed": False,
    "shared_mutable_runtime_container_allowed": False,
    "frozen_snapshot_id_only_cross_boundary": True,
    "mandatory_auth_placement": "transport_gateway_only",
    "immutable_audit_logging_placement": "frozen_snapshot_async_outbox_only",
    "redis_session_persistence_placement": "sidecar_state_store_only",
    "persisted_pii_redaction_placement": "persistence_and_audit_views_only",
    "tokenizer_backed_accounting_placement": "post_response_frozen_snapshot_only",
    "backup_restore_placement": "offline_operational_boundary_only",
    "one_command_release_smoke_placement": "non_serving_harness_only",
    "pii_redaction_before_raw_answer_freeze_allowed": False,
    "tokenizer_feedback_into_runtime_allowed": False,
    "backup_restore_runtime_attachment_allowed": False,
    "one_command_release_smoke_runtime_attachment_allowed": False,
}

PROHIBITED_RUNTIME_MUTATION_FLAGS = {
    "auth_principal_in_model_request_allowed": False,
    "user_id_in_model_request_allowed": False,
    "session_id_in_prompt_path_allowed": False,
    "trace_id_in_prompt_path_allowed": False,
    "request_id_in_prompt_path_allowed": False,
    "audit_id_in_prompt_path_allowed": False,
    "timestamp_feedback_into_answer_path_allowed": False,
    "token_count_feedback_into_answer_path_allowed": False,
    "estimated_token_count_feedback_into_answer_path_allowed": False,
    "health_debug_metadata_in_answer_path_allowed": False,
    "observability_metadata_in_answer_path_allowed": False,
    "backup_metadata_in_answer_path_allowed": False,
    "restore_metadata_in_answer_path_allowed": False,
    "supervision_metadata_in_answer_path_allowed": False,
    "alerting_metadata_in_answer_path_allowed": False,
    "smoke_metadata_in_answer_path_allowed": False,
    "version_negotiation_metadata_in_answer_path_allowed": False,
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

_KV_RE = re.compile(r"^- ([A-Za-z0-9_]+) = `?(.*?)`?$")
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
        for key, _ in columns:
            value = row.get(key, "")
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


def parse_markdown_kv(path: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for raw_line in load_text(path).splitlines():
        line = raw_line.strip()
        match = _KV_RE.match(line)
        if not match:
            continue
        key, raw_value = match.groups()
        payload[key] = _coerce_value(raw_value)
    return payload


def _coerce_value(raw: str) -> Any:
    if raw == "true":
        return True
    if raw == "false":
        return False
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    if re.fullmatch(r"-?\d+\.\d+", raw):
        return float(raw)
    return raw


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
        name, labels_text, value_text = match.groups()
        labels_key = ""
        if labels_text:
            labels_key = labels_text.strip("{}")
        metrics[(name, labels_key)] = float(value_text)
    return metrics


def metric_value(metrics: dict[tuple[str, str], float], name: str, **labels: str) -> float:
    if labels:
        label_key = ",".join(f'{key}="{value}"' for key, value in sorted(labels.items()))
        return metrics.get((name, label_key), 0.0)
    return metrics.get((name, ""), 0.0)


def _load_frontier_model_visible_reports() -> dict[str, dict[str, Any]]:
    return {family_id: load_json(path) for family_id, path in FAZ34_MODEL_VISIBLE_REPORTS.items()}


def _load_frontier_output_parity_reports() -> dict[str, dict[str, Any]]:
    return {family_id: load_json(path) for family_id, path in FAZ34_OUTPUT_PARITY_REPORTS.items()}


def build_frozen_frontier_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for family_id, report in _load_frontier_model_visible_reports().items():
        for row in report.get("mismatch_rows", []):
            records.append(
                {
                    "id": f"{family_id}::{row['question_id']}",
                    "family_id": family_id,
                    "question_id": row["question_id"],
                    "first_break_stage": row.get("first_break_stage"),
                    "primary_reason": row.get("primary_reason"),
                    "runtime_error": bool(row.get("runtime_error", False)),
                    "mismatch_keys": list(row.get("mismatch_keys") or []),
                }
            )
    return records


def build_frozen_response_envelope_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for family_id, report in _load_frontier_output_parity_reports().items():
        for row in report.get("parity_rows", []):
            if not row.get("response_envelope_hash_mismatch"):
                continue
            records.append(
                {
                    "id": f"{family_id}::{row['question_id']}",
                    "family_id": family_id,
                    "question_id": row["question_id"],
                    "first_divergence_stage": row.get("first_divergence_stage"),
                    "primary_reason": row.get("primary_reason"),
                    "runtime_error": bool(row.get("reference_runtime_error", 0))
                    or bool(row.get("candidate_runtime_error", 0)),
                }
            )
    return records


def summarize_record_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"faz1-50": 0, "v2-95": 0, "v3-170": 0}
    for row in records:
        counts[str(row["family_id"])] += 1
    return counts
