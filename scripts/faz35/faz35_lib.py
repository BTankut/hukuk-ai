#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-03-30"
RESULT_REPORT_NAME = (
    f"FAZ35-RC-P-RELEASE-CONTROLS-PERIMETER-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-{DATE}.md"
)

PASS_DECISION = "PASS - RC-P Perimeter Root Cause Localized"
FAIL_REFERENCE = "NO-GO - Reference Pack Contradiction"
FAIL_TOPOLOGY = "NO-GO - Topology Contract Breach"
FAIL_AUTHORITY = "NO-GO - Current Authority Breach"
FAIL_UPSTREAM = "NO-GO - RC-P Upstream Equality Breach"
FAIL_TRUTH = "NO-GO - RC-P Current Truth Drift"
FAIL_ACCEPTANCE = "NO-GO - RC-P Acceptance Truth Drift"
FAIL_RETENTION = "NO-GO - Retention Truth Drift"
FAIL_LADDER = "NO-GO - Stage Ladder Inconclusive"
FAIL_ISOLATION = "NO-GO - Control Isolation Inconclusive"

DECISION_TO_NEXT_WORK = {
    PASS_DECISION: "rc-q release-controls perimeter repair gate under canonical current authority",
    FAIL_REFERENCE: "reference pack reconciliation under canonical current authority",
    FAIL_TOPOLOGY: "topology normalization under canonical current authority",
    FAIL_AUTHORITY: "rc-g vs rc-j current authority recapture under canonical current authority",
    FAIL_UPSTREAM: "rc-p upstream equality recapture under canonical current authority",
    FAIL_TRUTH: "rc-p perimeter truth recapture under canonical current authority",
    FAIL_ACCEPTANCE: "rc-p targeted acceptance recapture under canonical current authority",
    FAIL_RETENTION: "rc-p retention truth recapture under canonical current authority",
    FAIL_LADDER: "rc-p perimeter truth recapture under canonical current authority",
    FAIL_ISOLATION: "rc-p perimeter truth recapture under canonical current authority",
}

REFERENCE_FILES = {
    "faz21": ROOT / "docs" / "FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
    "faz25": ROOT / "docs" / "FAZ25-POST-RC-M-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md",
    "faz26": ROOT / "docs" / "FAZ26-RC-N-RELEASE-CONTROLS-CLOSURE-REOPEN-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-28.md",
    "faz27": ROOT / "docs" / "FAZ27-RC-N-RELEASE-CONTROLS-BOUNDARY-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-28.md",
    "faz31": ROOT / "docs" / "FAZ31-RC-O-REPAIR-TRUTH-RECONCILIATION-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-29.md",
    "faz32": ROOT / "docs" / "FAZ32-RC-O-DISCARD-ARCHIVAL-CLOSURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
    "faz33": ROOT / "docs" / "FAZ33-POST-RC-O-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
    "faz34": ROOT / "docs" / "FAZ34-RC-P-RELEASE-CONTROLS-PERIMETER-ISOLATION-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
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
        "preprojection_hash_mismatch_count = `166`",
        "raw_answer_hash_mismatch_count = `166`",
    ],
    "faz27": [
        "PASS - RC-N Boundary Root Cause Localized",
        "first_break_control = `mandatory auth`",
        "root_cause_class = `multi_control_interaction_runtime_mutation`",
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
        "active_quality_reference = `RC-G`",
    ],
    "faz34": [
        "NO-GO - Release Controls Perimeter",
        "preprojection_hash_mismatch_count = `174`",
        "raw_answer_hash_mismatch_count = `174`",
        "response_envelope_hash_mismatch_count = `109`",
    ],
}

FAZ34_CURRENT_AUTHORITY_JSON = (
    ROOT / "evaluation" / "reports" / "faz34-rc-g-vs-rc-j-current-authority-check-2026-03-30.json"
)
FAZ34_TARGETED_ACCEPTANCE_MD = (
    ROOT / "evaluation" / "reports" / "faz34-rc-p-release-controls-targeted-acceptance-2026-03-30.md"
)
FAZ34_RETENTION_MD = (
    ROOT / "evaluation" / "reports" / "faz34-rc-p-release-controls-retention-matrix-2026-03-30.md"
)
FAZ34_RESTART_RETENTION_MD = (
    ROOT / "evaluation" / "reports" / "faz34-rc-p-post-restart-retention-check-2026-03-30.md"
)
FAZ34_RESTORE_RETENTION_MD = (
    ROOT / "evaluation" / "reports" / "faz34-rc-p-post-restore-retention-check-2026-03-30.md"
)
FAZ27_BOUNDARY_ROOT_CAUSE_MD = (
    ROOT / "evaluation" / "reports" / "faz27-rc-n-boundary-root-cause-summary-2026-03-28.md"
)
FAZ27_FULL_BOUNDARY_SUMMARY_MD = (
    ROOT / "evaluation" / "reports" / "faz27-rc-g-vs-rc-n-full-family-boundary-summary-2026-03-28.md"
)

MODEL_VISIBLE_REPORTS = {
    "faz1-50": ROOT / "evaluation" / "reports" / "faz34_rc_g_vs_rc_p_model_visible_faz1_50_20260330.json",
    "v2-95": ROOT / "evaluation" / "reports" / "faz34_rc_g_vs_rc_p_model_visible_v2_95_20260330.json",
    "v3-170": ROOT / "evaluation" / "reports" / "faz34_rc_g_vs_rc_p_model_visible_v3_170_20260330.json",
}
OUTPUT_PARITY_REPORTS = {
    "faz1-50": ROOT / "evaluation" / "reports" / "faz34_rc_g_vs_rc_p_output_parity_faz1_50_20260330.json",
    "v2-95": ROOT / "evaluation" / "reports" / "faz34_rc_g_vs_rc_p_output_parity_v2_95_20260330.json",
    "v3-170": ROOT / "evaluation" / "reports" / "faz34_rc_g_vs_rc_p_output_parity_v3_170_20260330.json",
}

CONTROL_SET_ROWS = [
    ("S0", "rc_g_baseline"),
    ("S1", "mandatory_auth + immutable_audit_logging + redis_session_persistence"),
    ("S2", "persisted_pii_redaction"),
    ("S3", "tokenizer_backed_accounting"),
    ("S4", "backup_restore"),
    ("S5", "one_command_release_smoke"),
    ("S6", "mandatory_auth + immutable_audit_logging + redis_session_persistence + persisted_pii_redaction"),
    ("S7", "mandatory_auth + immutable_audit_logging + redis_session_persistence + tokenizer_backed_accounting"),
    ("S8", "mandatory_auth + immutable_audit_logging + redis_session_persistence + backup_restore"),
    ("S9", "mandatory_auth + immutable_audit_logging + redis_session_persistence + one_command_release_smoke"),
    ("S10", "persisted_pii_redaction + tokenizer_backed_accounting + backup_restore + one_command_release_smoke"),
    ("S11", "full_rc_p_perimeter_surface"),
    ("S12", "full_rc_p_perimeter_surface_minus_persisted_pii_redaction"),
    ("S13", "full_rc_p_perimeter_surface_minus_tokenizer_backed_accounting"),
    ("S14", "full_rc_p_perimeter_surface_minus_backup_restore"),
    ("S15", "full_rc_p_perimeter_surface_minus_one_command_release_smoke"),
]

STAGE_LADDER = [
    ("P0", "transport_gateway_boundary"),
    ("P1", "auth_identity_token_boundary"),
    ("P2", "frozen_snapshot_async_outbox_boundary"),
    ("P3", "sidecar_session_state_boundary"),
    ("P4", "persistence_and_audit_view_boundary"),
    ("P5", "post_response_accounting_snapshot_boundary"),
    ("P6", "passive_observability_tap_boundary"),
    ("P7", "api_version_transport_boundary"),
    ("P8", "host_process_supervision_boundary"),
    ("P9", "offline_backup_restore_boundary"),
    ("P10", "non_serving_release_smoke_boundary"),
    ("P11", "preprojection_hash"),
    ("P12", "raw_answer_hash"),
    ("P13", "response_envelope_hash"),
]


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
            else:
                rendered.append(str(value))
        lines.append("| " + " | ".join(rendered) + " |")
    return lines


_KV_RE = re.compile(r"^- ([A-Za-z0-9_]+) = `?(.*?)`?$")


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


def build_frontier_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for family_id in ("faz1-50", "v2-95", "v3-170"):
        report = load_json(MODEL_VISIBLE_REPORTS[family_id])
        for row in report.get("mismatch_rows", []):
            records.append(
                {
                    "id": f"{family_id}::{row['question_id']}",
                    "family_id": family_id,
                    "question_id": row["question_id"],
                    "first_break_stage": row["first_break_stage"],
                    "primary_reason": row["primary_reason"],
                    "runtime_error": bool(row.get("runtime_error", False)),
                    "mismatch_keys": list(row.get("mismatch_keys") or []),
                }
            )
    return records


def build_response_envelope_records() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family_id in ("faz1-50", "v2-95", "v3-170"):
        report = load_json(OUTPUT_PARITY_REPORTS[family_id])
        for row in report.get("parity_rows", []):
            if not row.get("response_envelope_hash_mismatch"):
                continue
            rows.append(
                {
                    "id": f"{family_id}::{row['question_id']}",
                    "family_id": family_id,
                    "question_id": row["question_id"],
                    "first_divergence_stage": row["first_divergence_stage"],
                    "primary_reason": row["primary_reason"],
                    "preprojection_hash": row.get("preprojection_hash"),
                    "response_envelope_hash_mismatch": True,
                }
            )
    return rows


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    family_counts = {"faz1-50": 0, "v2-95": 0, "v3-170": 0}
    for row in records:
        family_counts[row["family_id"]] += 1
    return family_counts
