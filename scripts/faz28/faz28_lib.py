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

PASS_DECISION = "PASS - RC-O Boundary Repair Gate Cleared"
FAIL_UPSTREAM_EQUALITY = "NO-GO - Upstream Equality Breach"
FAIL_BOUNDARY_REPAIR = "NO-GO - RC-O Boundary Repair Failed"
FAIL_SPILLOVER = "NO-GO - RC-O Spillover Introduced"
FAIL_ACCEPTANCE = "NO-GO - RC-O Release Controls Acceptance Failed"
FAIL_INCONCLUSIVE = "NO-GO - RC-O Repair Gate Inconclusive"

DECISION_TO_NEXT_WORK = {
    PASS_DECISION: "rc-o release-controls closure reopen under canonical current authority",
    FAIL_UPSTREAM_EQUALITY: "rc-o upstream equality recapture under canonical current authority",
    FAIL_BOUNDARY_REPAIR: "rc-o release-controls boundary repair recapture under canonical current authority",
    FAIL_SPILLOVER: "rc-o release-controls boundary repair recapture under canonical current authority",
    FAIL_ACCEPTANCE: "rc-o release-controls boundary repair recapture under canonical current authority",
    FAIL_INCONCLUSIVE: "rc-o release-controls boundary repair recapture under canonical current authority",
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

REFERENCE_FILES = {
    "faz21": ROOT / "docs" / "FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
    "faz24": ROOT / "docs" / "FAZ24-RC-M-DISCARD-ARCHIVAL-CLOSURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md",
    "faz25": ROOT / "docs" / "FAZ25-POST-RC-M-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md",
    "faz26": ROOT / "docs" / "FAZ26-RC-N-RELEASE-CONTROLS-CLOSURE-REOPEN-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-28.md",
    "faz27": ROOT / "docs" / "FAZ27-RC-N-RELEASE-CONTROLS-BOUNDARY-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-28.md",
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
        "next_candidate_id = `RC-N`",
    ],
    "faz26": [
        "NO-GO - Release Controls",
        "preprojection_hash_mismatch_count = `166`",
        "raw_answer_hash_mismatch_count = `166`",
    ],
    "faz27": [
        "PASS - RC-N Boundary Root Cause Localized",
        "first_break_control = `mandatory auth`",
        "frontier_total = `166`",
    ],
}

FAZ21_CANONICAL_REFERENCE_JSON = (
    ROOT / "coordination" / "faz21-current-authority-canonical-reference-pack-2026-03-27.json"
)
FAZ21_CANONICAL_GATE_JSON = (
    ROOT / "evaluation" / "reports" / "faz21-current-authority-canonicalization-gate-2026-03-27.json"
)
FAZ27_REFERENCE_PACK_JSON = ROOT / "coordination" / "faz27-reference-pack-2026-03-28.json"

FAMILY_BANKS = {
    "faz1-50": ROOT / "configs" / "evaluation" / "test_questions.json",
    "v2-95": ROOT / "configs" / "evaluation" / "test_questions_v2_95.json",
    "v3-170": ROOT / "configs" / "evaluation" / "test_questions_v3_170.json",
}

FAZ26_RC_G_EVALS = {
    "faz1-50": ROOT / "evaluation" / "reports" / "eval_faz26_rc_g_faz1_50_20260328.json",
    "v2-95": ROOT / "evaluation" / "reports" / "eval_faz26_rc_g_v2_95_20260328.json",
    "v3-170": ROOT / "evaluation" / "reports" / "eval_faz26_rc_g_v3_170_20260328.json",
}

BOUNDARY_FRONTIER_PACK_PATH = (
    ROOT / "configs" / "evaluation" / f"test_questions_faz28_boundary_frontier_166_{COMPACT_DATE}.json"
)
SPILLOVER_GUARD_PACK_PATH = (
    ROOT / "configs" / "evaluation" / f"test_questions_faz28_spillover_guard_24_{COMPACT_DATE}.json"
)
MATERIALIZED_REFERENCE_JSON = ROOT / "coordination" / f"faz28-reference-pack-{DATE}.json"

_METRIC_RE = re.compile(r'^([a-zA-Z0-9_:]+)(\{[^}]*\})?\s+([0-9.eE+-]+)$')

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
            value = row.get(key)
            if isinstance(value, bool):
                rendered.append(bool_text(value))
            elif isinstance(value, list):
                rendered.append(", ".join(str(item) for item in value))
            elif isinstance(value, dict):
                rendered.append(json.dumps(value, ensure_ascii=False, sort_keys=True))
            elif value is None:
                rendered.append("")
            else:
                rendered.append(str(value))
        lines.append("| " + " | ".join(rendered) + " |")
    return lines


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


def family_sort_key(family_id: str) -> tuple[int, str]:
    order = {"faz1-50": 0, "v2-95": 1, "v3-170": 2}
    return (order.get(family_id, 99), family_id)


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


def parse_headers_text(text: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for raw_line in text.splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    return headers


def build_frontier_records() -> list[dict[str, Any]]:
    payload = load_json(FAZ27_REFERENCE_PACK_JSON)
    records = payload.get("frontier_freeze", {}).get("records") or []
    return [dict(row) for row in records if isinstance(row, dict)]


def build_spillover_guard_records(frontier_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frontier_ids = {str(row["id"]) for row in frontier_records if row.get("id")}
    selections = {"faz1-50": 4, "v2-95": 8, "v3-170": 12}
    rows: list[dict[str, Any]] = []
    for family_id, limit in selections.items():
        bank_rows = sorted(load_question_bank(FAMILY_BANKS[family_id]), key=lambda row: str(row.get("id") or ""))
        family_rows: list[dict[str, Any]] = []
        for ordinal, row in enumerate(bank_rows, start=1):
            source_question_id = str(row.get("id") or "")
            if not source_question_id:
                continue
            composite_id = f"{family_id}::{source_question_id}"
            if composite_id in frontier_ids:
                continue
            family_rows.append(
                {
                    "id": composite_id,
                    "source_question_id": source_question_id,
                    "authority_family_id": family_id,
                    "question": row.get("question", ""),
                    "category": row.get("category"),
                    "difficulty": row.get("difficulty"),
                    "expected_sources": row.get("expected_sources", []),
                    "expected_keywords": row.get("expected_keywords", []),
                    "expected_answer_contains": row.get("expected_answer_contains"),
                    "refusal_expected": bool(row.get("refusal_expected", False)),
                    "notes": row.get("notes"),
                    "family_ordinal": ordinal,
                }
            )
            if len(family_rows) == limit:
                break
        if len(family_rows) != limit:
            raise RuntimeError(f"spillover guard selection underfilled for {family_id}: {len(family_rows)} != {limit}")
        rows.extend(family_rows)
    return rows


def write_question_pack(path: Path, rows: list[dict[str, Any]]) -> None:
    write_json(path, {"questions": rows})


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
        for _counter_key, stage_name in FIRST_BREAK_PRIORITY:
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


def summarize_pack_report(
    *,
    report: dict[str, Any],
    pack_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    counts_by_family = {family_id: 0 for family_id in FAMILY_BANKS}
    row_index = {
        str(row["id"]): str(row.get("authority_family_id") or "")
        for row in pack_rows
        if row.get("id")
    }
    for row in report.get("mismatch_rows", []):
        family_id = row_index.get(str(row.get("question_id")))
        if family_id in counts_by_family:
            counts_by_family[family_id] += 1
    return {
        "record_count": len(pack_rows),
        "mismatch_count": len(report.get("mismatch_rows", [])),
        "faz1_50_mismatch_count": counts_by_family["faz1-50"],
        "v2_95_mismatch_count": counts_by_family["v2-95"],
        "v3_170_mismatch_count": counts_by_family["v3-170"],
        "preprojection_hash_mismatch_count": int(report.get("preprojection_hash_mismatch_count", 0)),
        "raw_answer_hash_mismatch_count": int(report.get("raw_answer_hash_mismatch_count", 0)),
        "response_envelope_hash_mismatch_count": int(report.get("response_envelope_hash_mismatch_count", 0)),
        "runtime_error_count": int(report.get("runtime_error_count", 0)),
        "first_break_stage_assigned_count": int(report.get("first_break_stage_assigned_count", 0)),
        "primary_reason_assigned_count": int(report.get("primary_reason_assigned_count", 0)),
        "unexplained_count": int(report.get("unexplained_count", 0)),
        "mismatch_rows": list(report.get("mismatch_rows", [])),
    }
