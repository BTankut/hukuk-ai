#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-03-31"
RESULT_REPORT_NAME = (
    "FAZ38-RC-Q-REPAIR-TRUTH-INSTABILITY-FORENSICS-UNDER-"
    f"CANONICAL-CURRENT-AUTHORITY-RAPORU-{DATE}.md"
)

PASS_DECISION = "PASS - RC-Q Repair Truth Instability Localized"
FAIL_AUTHORITY = "NO-GO - Authority Or Upstream Equality Breach"
FAIL_UNLOCALIZED = "NO-GO - RC-Q Instability Still Unlocalized"

DECISION_TO_NEXT_WORK = {
    PASS_DECISION: "rc-q repair truth reconciliation under canonical current authority",
    FAIL_AUTHORITY: "rc-q repair truth instability forensics reopen under canonical current authority",
    FAIL_UNLOCALIZED: "rc-q repair truth instability forensics reopen under canonical current authority",
}

FAMILY_IDS = ["faz1-50", "v2-95", "v3-170"]
FAMILY_ORDER = {family_id: idx for idx, family_id in enumerate(FAMILY_IDS)}

REFERENCE_FILES = {
    "faz21": ROOT
    / "docs"
    / "FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
    "faz33": ROOT
    / "docs"
    / "FAZ33-POST-RC-O-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
    "faz35": ROOT
    / "docs"
    / "FAZ35-RC-P-RELEASE-CONTROLS-PERIMETER-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
    "faz36": ROOT
    / "docs"
    / "FAZ36-RC-Q-RELEASE-CONTROLS-PERIMETER-REPAIR-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
    "faz37": ROOT
    / "docs"
    / "FAZ37-RC-Q-RELEASE-CONTROLS-PERIMETER-REPAIR-RECAPTURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
}

REFERENCE_MARKERS = {
    "faz21": [
        "PASS - Current Authority Canonicalized",
        "current_canonical_authority_adopted = true",
    ],
    "faz33": [
        "PASS - Post-RC-O Steering Re-Entered Under Canonical Current Authority",
        "active_quality_reference = `RC-G`",
    ],
    "faz35": [
        "PASS - RC-P Perimeter Root Cause Localized",
        "dominant_stage = `P11`",
        "dominant_interaction_class = `multi_control_interaction_runtime_mutation`",
    ],
    "faz36": [
        "NO-GO - RC-Q Frontier Repair Failed",
        "frontier_record_count = `174`",
        "preprojection_hash_mismatch_count = `151`",
        "response_envelope_hash_mismatch_count = `92`",
    ],
    "faz37": [
        "NO-GO - RC-Q Recapture Inconclusive",
        "capture_a_vs_capture_b_mismatch_count = `6`",
        "capture_a_vs_capture_b_mismatch_count = `3`",
        "matches_neither = `true`",
    ],
}

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

CURRENT_AUTHORITY_EXPECTED = {
    "control_pair_authority_match": True,
    "current_authority_contract_breach": False,
    "surface_breach_from_history_reintroduced": False,
    "model_request_payload_hash_mismatch_count": 0,
    "retrieval_request_hash_mismatch_count": 0,
    "assembled_context_hash_mismatch_count": 0,
    "runtime_error_count": 0,
}

FAZ35_FRONTIER_TRUTH = {
    "record_count": 174,
    "faz1_50_mismatch_count": 18,
    "v2_95_mismatch_count": 57,
    "v3_170_mismatch_count": 99,
    "preprojection_hash_mismatch_count": 174,
    "raw_answer_hash_mismatch_count": 174,
    "response_envelope_hash_mismatch_count": 109,
    "runtime_error_count": 0,
    "capture_stability_match": True,
    "capture_a_vs_capture_b_mismatch_count": 0,
    "unexplained_count": 0,
}

FAZ36_FAILED_REPAIR_TRUTH = {
    "record_count": 174,
    "faz1_50_mismatch_count": 18,
    "v2_95_mismatch_count": 49,
    "v3_170_mismatch_count": 84,
    "preprojection_hash_mismatch_count": 151,
    "raw_answer_hash_mismatch_count": 151,
    "response_envelope_hash_mismatch_count": 92,
    "runtime_error_count": 0,
    "capture_stability_match": True,
    "capture_a_vs_capture_b_mismatch_count": 0,
    "unexplained_count": 0,
}

STAGE_LADDER = [
    ("I0", "reference_pack_identity"),
    ("I1", "candidate_manifest_identity"),
    ("I2", "canonical_topology_identity"),
    ("I3", "eval_family_pack_identity"),
    ("I4", "frontier_membership_identity"),
    ("I5", "row_order_identity"),
    ("I6", "preprojection_hash_materialization"),
    ("I7", "raw_answer_hash_materialization"),
    ("I8", "response_envelope_hash_materialization"),
    ("I9", "family_aggregation_materialization"),
    ("I10", "targeted_acceptance_materialization"),
    ("I11", "retention_materialization"),
    ("I12", "final_truth_materialization"),
]

ALLOWED_PRIMARY_REASONS = [
    "reference_pack_identity_delta",
    "candidate_manifest_identity_delta",
    "canonical_topology_identity_delta",
    "eval_family_pack_identity_delta",
    "frontier_membership_delta",
    "row_order_delta",
    "preprojection_hash_materialization_delta",
    "raw_answer_hash_materialization_delta",
    "response_envelope_hash_materialization_delta",
    "family_aggregation_delta",
    "targeted_acceptance_materialization_delta",
    "retention_materialization_delta",
    "final_truth_materialization_delta",
]

ALLOWED_ROOT_CAUSE_CLASSES = [
    "reference_identity_instability",
    "manifest_identity_instability",
    "topology_identity_instability",
    "family_pack_instability",
    "frontier_membership_instability",
    "row_order_instability",
    "preprojection_materialization_instability",
    "raw_answer_materialization_instability",
    "response_envelope_materialization_instability",
    "aggregation_surface_instability",
    "retention_surface_instability",
    "truth_materialization_instability",
]

_KV_RE = re.compile(r"^- ([A-Za-z0-9_]+) = `?(.*?)`?$")


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
        if raw_value == "true":
            payload[key] = True
        elif raw_value == "false":
            payload[key] = False
        elif re.fullmatch(r"-?\d+", raw_value):
            payload[key] = int(raw_value)
        elif re.fullmatch(r"-?\d+\.\d+", raw_value):
            payload[key] = float(raw_value)
        else:
            payload[key] = raw_value
    return payload


def _load_faz34_model_visible_reports() -> dict[str, dict[str, Any]]:
    return {family_id: load_json(path) for family_id, path in FAZ34_MODEL_VISIBLE_REPORTS.items()}


def _load_faz34_output_parity_reports() -> dict[str, dict[str, Any]]:
    return {family_id: load_json(path) for family_id, path in FAZ34_OUTPUT_PARITY_REPORTS.items()}


def build_frozen_frontier_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for family_id, report in _load_faz34_model_visible_reports().items():
        for row in report.get("mismatch_rows", []):
            records.append(
                {
                    "id": f"{family_id}::{row['question_id']}",
                    "family_id": family_id,
                    "question_id": row["question_id"],
                }
            )
    return records


def build_frozen_response_envelope_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for family_id, report in _load_faz34_output_parity_reports().items():
        for row in report.get("parity_rows", []):
            if not row.get("response_envelope_hash_mismatch"):
                continue
            records.append(
                {
                    "id": f"{family_id}::{row['question_id']}",
                    "family_id": family_id,
                    "question_id": row["question_id"],
                }
            )
    return records
