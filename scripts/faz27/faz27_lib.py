#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-03-28"
COMPACT_DATE = "20260328"

PASS_DECISION = "PASS - RC-N Boundary Root Cause Localized"
FAIL_BOUNDARY_TRUTH_DRIFT = "NO-GO - Boundary Truth Drift"
FAIL_UPSTREAM_CONTRACT = "NO-GO - Upstream Boundary Contract Breach"
FAIL_INCONCLUSIVE = "NO-GO - Boundary Forensics Inconclusive"

DECISION_TO_NEXT_WORK = {
    PASS_DECISION: "rc-o release-controls boundary repair gate under canonical current authority",
    FAIL_BOUNDARY_TRUTH_DRIFT: "rc-n release-controls boundary forensics recapture under canonical current authority",
    FAIL_UPSTREAM_CONTRACT: "rc-n upstream boundary contract recapture under canonical current authority",
    FAIL_INCONCLUSIVE: "rc-n release-controls boundary forensics recapture under canonical current authority",
}

REFERENCE_FILES = {
    "faz21": ROOT / "docs" / "FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
    "faz24": ROOT / "docs" / "FAZ24-RC-M-DISCARD-ARCHIVAL-CLOSURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md",
    "faz25": ROOT / "docs" / "FAZ25-POST-RC-M-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md",
    "faz26": ROOT / "docs" / "FAZ26-RC-N-RELEASE-CONTROLS-CLOSURE-REOPEN-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-28.md",
}

REFERENCE_MARKERS = {
    "faz21": [
        "PASS - Current Authority Canonicalized",
        "`current_canonical_authority_adopted = true`",
    ],
    "faz24": [
        "PASS - RC-M Discard Archived Under Canonical Current Authority",
        "archive_status = `closed`",
    ],
    "faz25": [
        "PASS - Post-RC-M Steering Re-Entered Under Canonical Current Authority",
        "candidate_status = `discard_archived`",
    ],
    "faz26": [
        "NO-GO - Release Controls",
        "preprojection_hash_mismatch_count = `166`",
        "raw_answer_hash_mismatch_count = `166`",
    ],
}

FAMILY_BANKS = {
    "faz1-50": ROOT / "configs" / "evaluation" / "test_questions.json",
    "v2-95": ROOT / "configs" / "evaluation" / "test_questions_v2_95.json",
    "v3-170": ROOT / "configs" / "evaluation" / "test_questions_v3_170.json",
}

FAZ26_ARTEFACTS = {
    "current_authority": ROOT / "evaluation" / "reports" / "faz26-rc-g-vs-rc-j-current-authority-check-2026-03-28.json",
    "model_visible_summary": ROOT / "evaluation" / "reports" / "faz26-rc-g-vs-rc-n-model-visible-surface-summary-2026-03-28.json",
    "output_parity_summary": ROOT / "evaluation" / "reports" / "faz26-rc-g-vs-rc-n-output-parity-summary-2026-03-28.json",
    "retention_gate": ROOT / "evaluation" / "reports" / "faz26-rc-n-release-controls-retention-gate-2026-03-28.json",
    "pii_probe": ROOT / "evaluation" / "reports" / "faz26-pii-redaction-probe-2026-03-28.json",
    "release_smoke_after_family_eval": ROOT / "runtime_logs" / "faz26_rc_n_release_smoke_after_family_eval.json",
    "metrics": ROOT / "runtime_logs" / "faz26_rc_n_metrics.txt",
    "alerts": ROOT / "runtime_logs" / "faz26_rc_n_alerts.json",
    "models_headers": ROOT / "runtime_logs" / "faz26_rc_n_models_headers.txt",
    "backup_manifest": ROOT / "coordination" / "faz26_backups" / "faz26_rc_n_20260328T053810Z" / "manifest.json",
    "restore_summary": ROOT / "coordination" / "faz26_restore" / "restore_summary.json",
    "supervision": ROOT / "coordination" / "faz26_rc_n_supervision.json",
    "restart_supervision": ROOT / "coordination" / "faz26_rc_n_restart_supervision.json",
    "restore_supervision": ROOT / "coordination" / "faz26_rc_n_restore_supervision.json",
}

FAZ26_FAMILY_MODEL_VISIBLE_REPORTS = {
    "faz1-50": ROOT / "evaluation" / "reports" / "faz26-rc-g-vs-rc-n-model-visible-surface-faz1_50-2026-03-28.json",
    "v2-95": ROOT / "evaluation" / "reports" / "faz26-rc-g-vs-rc-n-model-visible-surface-v2_95-2026-03-28.json",
    "v3-170": ROOT / "evaluation" / "reports" / "faz26-rc-g-vs-rc-n-model-visible-surface-v3_170-2026-03-28.json",
}

FAZ26_RC_G_EVALS = {
    "faz1-50": ROOT / "evaluation" / "reports" / "eval_faz26_rc_g_faz1_50_20260328.json",
    "v2-95": ROOT / "evaluation" / "reports" / "eval_faz26_rc_g_v2_95_20260328.json",
    "v3-170": ROOT / "evaluation" / "reports" / "eval_faz26_rc_g_v3_170_20260328.json",
}

FAZ26_RC_N_EVALS = {
    "faz1-50": ROOT / "evaluation" / "reports" / "eval_faz26_rc_n_faz1_50_20260328.json",
    "v2-95": ROOT / "evaluation" / "reports" / "eval_faz26_rc_n_v2_95_20260328.json",
    "v3-170": ROOT / "evaluation" / "reports" / "eval_faz26_rc_n_v3_170_20260328.json",
}

CONTROL_ROWS = [
    {
        "control_name": "mandatory auth",
        "control_class": "runtime-boundary",
        "bind_step": "B1",
        "has_distinct_runtime_handle": True,
        "should_touch_answer_path": True,
    },
    {
        "control_name": "immutable audit logging",
        "control_class": "runtime-boundary",
        "bind_step": "B2",
        "has_distinct_runtime_handle": True,
        "should_touch_answer_path": True,
    },
    {
        "control_name": "persisted PII redaction",
        "control_class": "runtime-boundary",
        "bind_step": "B3",
        "has_distinct_runtime_handle": False,
        "runtime_surface_delegate": "immutable audit logging",
        "should_touch_answer_path": True,
    },
    {
        "control_name": "Redis session persistence",
        "control_class": "runtime-boundary",
        "bind_step": "B4",
        "has_distinct_runtime_handle": True,
        "should_touch_answer_path": True,
    },
    {
        "control_name": "tokenizer-backed accounting",
        "control_class": "runtime-boundary",
        "bind_step": "B5",
        "has_distinct_runtime_handle": True,
        "should_touch_answer_path": True,
    },
    {
        "control_name": "observability / alerting",
        "control_class": "runtime-boundary",
        "bind_step": "B6",
        "has_distinct_runtime_handle": False,
        "runtime_surface_delegate": "tokenizer-backed accounting",
        "should_touch_answer_path": True,
    },
    {
        "control_name": "API versioning",
        "control_class": "runtime-boundary",
        "bind_step": "B7",
        "has_distinct_runtime_handle": False,
        "runtime_surface_delegate": "tokenizer-backed accounting",
        "should_touch_answer_path": True,
    },
    {
        "control_name": "process supervision",
        "control_class": "runtime-boundary",
        "bind_step": "B8",
        "has_distinct_runtime_handle": False,
        "runtime_surface_delegate": "tokenizer-backed accounting",
        "should_touch_answer_path": True,
    },
    {
        "control_name": "backup / restore",
        "control_class": "operational-only",
        "bind_step": None,
        "has_distinct_runtime_handle": False,
        "should_touch_answer_path": False,
    },
    {
        "control_name": "one-command release smoke",
        "control_class": "operational-only",
        "bind_step": None,
        "has_distinct_runtime_handle": False,
        "should_touch_answer_path": False,
    },
]

BIND_ORDER_ROWS = [
    {"step_id": "B0", "bound_control_set": [], "label": "RC-G canonical baseline"},
    {"step_id": "B1", "bound_control_set": ["mandatory auth"], "label": "mandatory auth"},
    {"step_id": "B2", "bound_control_set": ["mandatory auth", "immutable audit logging"], "label": "immutable audit logging"},
    {"step_id": "B3", "bound_control_set": ["mandatory auth", "immutable audit logging", "persisted PII redaction"], "label": "persisted PII redaction"},
    {"step_id": "B4", "bound_control_set": ["mandatory auth", "immutable audit logging", "persisted PII redaction", "Redis session persistence"], "label": "Redis session persistence"},
    {"step_id": "B5", "bound_control_set": ["mandatory auth", "immutable audit logging", "persisted PII redaction", "Redis session persistence", "tokenizer-backed accounting"], "label": "tokenizer-backed accounting"},
    {"step_id": "B6", "bound_control_set": ["mandatory auth", "immutable audit logging", "persisted PII redaction", "Redis session persistence", "tokenizer-backed accounting", "observability / alerting"], "label": "observability / alerting"},
    {"step_id": "B7", "bound_control_set": ["mandatory auth", "immutable audit logging", "persisted PII redaction", "Redis session persistence", "tokenizer-backed accounting", "observability / alerting", "API versioning"], "label": "API versioning"},
    {"step_id": "B8", "bound_control_set": ["mandatory auth", "immutable audit logging", "persisted PII redaction", "Redis session persistence", "tokenizer-backed accounting", "observability / alerting", "API versioning", "process supervision"], "label": "process supervision"},
]

RUNTIME_CONTROL_NAMES = [row["control_name"] for row in CONTROL_ROWS if row["control_class"] == "runtime-boundary"]
OPERATIONAL_CONTROL_NAMES = [row["control_name"] for row in CONTROL_ROWS if row["control_class"] == "operational-only"]

FIELD_SPECS = [
    ("model_request_payload_hash_mismatch_count", "model_request_payload", "model_request_payload_hash"),
    ("retrieval_request_hash_mismatch_count", "retrieval_input_payload", "retrieval_request_hash"),
    ("assembled_context_hash_mismatch_count", "assembly_payload", "assembled_context_hash"),
    ("preprojection_hash_mismatch_count", "preprojection_hash", "preprojection_hash"),
    ("raw_answer_hash_mismatch_count", "raw_answer_object", "raw_answer_hash"),
    ("response_envelope_hash_mismatch_count", "response_envelope", "response_envelope_hash"),
]

FIRST_BREAK_PRIORITY = [
    ("retrieval_request_hash_mismatch_count", "retrieval_input_payload"),
    ("assembled_context_hash_mismatch_count", "assembly_payload"),
    ("model_request_payload_hash_mismatch_count", "model_request_payload"),
    ("preprojection_hash_mismatch_count", "preprojection_hash"),
    ("raw_answer_hash_mismatch_count", "raw_answer_object"),
    ("response_envelope_hash_mismatch_count", "response_envelope"),
]

PRIMARY_REASON_BY_STAGE = {
    "retrieval_input_payload": "retrieval_request_hash_drift",
    "assembly_payload": "assembled_context_hash_drift",
    "model_request_payload": "model_request_payload_hash_drift",
    "preprojection_hash": "preprojection_hash_drift",
    "raw_answer_object": "raw_answer_hash_drift",
    "response_envelope": "response_envelope_projection_delta",
}

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
        rendered = []
        for key, _ in columns:
            value = row.get(key)
            if isinstance(value, bool):
                rendered.append(bool_text(value))
            elif isinstance(value, list):
                rendered.append(", ".join(str(item) for item in value))
            elif value is None:
                rendered.append("")
            else:
                rendered.append(str(value))
        lines.append("| " + " | ".join(rendered) + " |")
    return lines


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


def load_question_bank(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    if isinstance(payload, dict):
        rows = payload.get("questions")
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    raise ValueError(f"unsupported question bank: {path}")


def load_question_bank_index(path: Path) -> dict[str, dict[str, Any]]:
    return {
        str(row["id"]): row
        for row in load_question_bank(path)
        if row.get("id")
    }


def build_frontier_records() -> list[dict[str, Any]]:
    question_maps = {family_id: load_question_bank_index(bank_path) for family_id, bank_path in FAMILY_BANKS.items()}
    rows: list[dict[str, Any]] = []
    for family_id in ("faz1-50", "v2-95", "v3-170"):
        report = load_json(FAZ26_FAMILY_MODEL_VISIBLE_REPORTS[family_id])
        for ordinal, row in enumerate(report.get("mismatch_rows", []), start=1):
            question_id = str(row.get("question_id"))
            source_question = question_maps[family_id][question_id]
            rows.append(
                {
                    "id": f"{family_id}::{question_id}",
                    "source_question_id": question_id,
                    "authority_family_id": family_id,
                    "question": source_question.get("question", ""),
                    "category": source_question.get("category"),
                    "difficulty": source_question.get("difficulty"),
                    "expected_sources": source_question.get("expected_sources", []),
                    "expected_keywords": source_question.get("expected_keywords", []),
                    "expected_answer_contains": source_question.get("expected_answer_contains", []),
                    "refusal_expected": bool(source_question.get("refusal_expected", False)),
                    "notes": source_question.get("notes"),
                    "family_ordinal": ordinal,
                    "authoritative_first_break_stage": row.get("first_break_stage"),
                    "authoritative_primary_reason": row.get("primary_reason"),
                    "authoritative_mismatch_keys": row.get("mismatch_keys", []),
                }
            )
    return rows


def merge_eval_question_maps(paths: list[Path]) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for path in paths:
        payload = load_json(path)
        for row in payload.get("per_question", []):
            if isinstance(row, dict) and row.get("question_id"):
                merged[str(row["question_id"])] = row
    return merged


def stage_map(question: dict[str, Any]) -> dict[str, dict[str, Any]]:
    parity_trace = ((question.get("trace") or {}).get("parity_trace") or {}) if isinstance(question, dict) else {}
    stages = parity_trace.get("stages") or []
    return {
        str(item.get("stage")): item
        for item in stages
        if isinstance(item, dict) and item.get("stage")
    }


def stage_hash(question: dict[str, Any], stage_name: str) -> str | None:
    stage = stage_map(question).get(stage_name) or {}
    value = stage.get("hash")
    if isinstance(value, str) and value:
        return value
    payload = stage.get("payload")
    if isinstance(payload, dict):
        return stable_hash(payload)
    return None


def preprojection_hash(question: dict[str, Any]) -> str | None:
    parity_trace = ((question.get("trace") or {}).get("parity_trace") or {}) if isinstance(question, dict) else {}
    value = parity_trace.get("preprojection_hash")
    return value if isinstance(value, str) and value else None


def compare_question_maps(
    *,
    family_id: str,
    reference_questions: dict[str, dict[str, Any]],
    candidate_questions: dict[str, dict[str, Any]],
    question_ids: list[str] | None = None,
) -> dict[str, Any]:
    selected_ids = question_ids or sorted(set(reference_questions) | set(candidate_questions))
    report: dict[str, Any] = {
        "family_id": family_id,
        "question_count": len(selected_ids),
        "compared_question_count": 0,
        "model_request_payload_hash_mismatch_count": 0,
        "retrieval_request_hash_mismatch_count": 0,
        "assembled_context_hash_mismatch_count": 0,
        "preprojection_hash_mismatch_count": 0,
        "raw_answer_hash_mismatch_count": 0,
        "response_envelope_hash_mismatch_count": 0,
        "runtime_error_count": 0,
        "first_break_stage_assigned_count": 0,
        "primary_reason_assigned_count": 0,
        "unexplained_count": 0,
        "mismatch_rows": [],
    }

    for question_id in selected_ids:
        reference_question = reference_questions.get(question_id)
        candidate_question = candidate_questions.get(question_id)
        if reference_question is None or candidate_question is None:
            report["runtime_error_count"] += 1
            report["unexplained_count"] += 1
            report["mismatch_rows"].append(
                {
                    "question_id": question_id,
                    "first_break_stage": None,
                    "primary_reason": None,
                    "runtime_error": True,
                    "mismatch_keys": [],
                    "notes": "question missing in reference or candidate map",
                }
            )
            continue

        mismatches: dict[str, dict[str, str | None]] = {}
        runtime_error = False
        for counter_key, stage_name, label in FIELD_SPECS:
            if stage_name == "preprojection_hash":
                reference_hash = preprojection_hash(reference_question)
                candidate_hash = preprojection_hash(candidate_question)
            else:
                reference_hash = stage_hash(reference_question, stage_name)
                candidate_hash = stage_hash(candidate_question, stage_name)
            if not isinstance(reference_hash, str) or not isinstance(candidate_hash, str):
                runtime_error = True
                mismatches[label] = {"reference_hash": reference_hash, "candidate_hash": candidate_hash}
                continue
            if reference_hash != candidate_hash:
                report[counter_key] += 1
                mismatches[label] = {"reference_hash": reference_hash, "candidate_hash": candidate_hash}

        if runtime_error:
            report["runtime_error_count"] += 1

        if not mismatches and not runtime_error:
            report["compared_question_count"] += 1
            continue

        first_break_stage = None
        primary_reason = None
        for counter_key, stage_name in FIRST_BREAK_PRIORITY:
            label = next(spec[2] for spec in FIELD_SPECS if spec[1] == stage_name)
            if label in mismatches:
                first_break_stage = stage_name
                primary_reason = PRIMARY_REASON_BY_STAGE[stage_name]
                break

        if first_break_stage is not None:
            report["first_break_stage_assigned_count"] += 1
        if primary_reason is not None:
            report["primary_reason_assigned_count"] += 1
        if first_break_stage is None or primary_reason is None:
            report["unexplained_count"] += 1

        report["mismatch_rows"].append(
            {
                "question_id": question_id,
                "first_break_stage": first_break_stage,
                "primary_reason": primary_reason,
                "runtime_error": runtime_error,
                "mismatch_keys": sorted(mismatches.keys()),
            }
        )
        report["compared_question_count"] += 1

    return report


def render_pair_report_markdown(report: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- family_id = `{report['family_id']}`",
        f"- question_count = `{report['question_count']}`",
        f"- compared_question_count = `{report['compared_question_count']}`",
        f"- model_request_payload_hash_mismatch_count = `{report['model_request_payload_hash_mismatch_count']}`",
        f"- retrieval_request_hash_mismatch_count = `{report['retrieval_request_hash_mismatch_count']}`",
        f"- assembled_context_hash_mismatch_count = `{report['assembled_context_hash_mismatch_count']}`",
        f"- preprojection_hash_mismatch_count = `{report['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{report['raw_answer_hash_mismatch_count']}`",
        f"- response_envelope_hash_mismatch_count = `{report['response_envelope_hash_mismatch_count']}`",
        f"- runtime_error_count = `{report['runtime_error_count']}`",
        f"- first_break_stage_assigned_count = `{report['first_break_stage_assigned_count']}`",
        f"- primary_reason_assigned_count = `{report['primary_reason_assigned_count']}`",
        f"- unexplained_count = `{report['unexplained_count']}`",
        "",
        "## Frontier Sample",
        "",
    ]
    if not report["mismatch_rows"]:
        lines.append("- mismatch yok")
    else:
        for row in report["mismatch_rows"][:20]:
            lines.append(
                f"- `{row['question_id']}` stage `{row['first_break_stage']}` reason `{row['primary_reason']}` mismatch_keys `{', '.join(row['mismatch_keys'])}`"
            )
    lines.append("")
    return "\n".join(lines)
