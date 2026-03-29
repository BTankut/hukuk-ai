#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-03-29"
COMPACT_DATE = "20260329"

PASS_DECISION = "PASS - RC-O Boundary Repair Truth Recaptured"
FAIL_UPSTREAM_EQUALITY = "NO-GO - Current Authority Or Upstream Equality Drift"
FAIL_UNSTABLE = "NO-GO - RC-O Repair Truth Unstable"
FAIL_INCONCLUSIVE = "NO-GO - RC-O Recapture Inconclusive"
FAIL_TRUTH_UNSTABLE = FAIL_UNSTABLE

DECISION_TO_NEXT_WORK = {
    PASS_DECISION: "rc-p release-controls boundary replacement gate under canonical current authority",
    FAIL_UPSTREAM_EQUALITY: "rc-o current authority or upstream equality recapture under canonical current authority",
    FAIL_UNSTABLE: "rc-o repair truth instability forensics under canonical current authority",
    FAIL_INCONCLUSIVE: "rc-o repair truth instability forensics under canonical current authority",
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

FAILING_CONTROL_TRIPLET = [
    "persisted PII redaction",
    "tokenizer-backed accounting",
    "one-command release smoke",
]

BOUNDARY_EXPECTED = {
    "input_pack_count": 166,
    "remaining_mismatch_count": 152,
    "repair_delta_record_count": 14,
    "faz1_50_mismatch_count": 14,
    "v2_95_mismatch_count": 52,
    "v3_170_mismatch_count": 86,
    "preprojection_hash_mismatch_count": 152,
    "raw_answer_hash_mismatch_count": 152,
    "response_envelope_hash_mismatch_count": 92,
    "first_break_stage_assigned_count": 152,
    "primary_reason_assigned_count": 152,
    "runtime_error_count": 0,
    "unexplained_count": 0,
}

SPILLOVER_EXPECTED = {
    "record_count": 24,
    "mismatch_count": 5,
    "preprojection_hash_mismatch_count": 5,
    "raw_answer_hash_mismatch_count": 5,
    "response_envelope_hash_mismatch_count": 2,
    "runtime_error_count": 0,
    "unexplained_count": 0,
}

ACCEPTANCE_EXPECTED = {
    "must_close_release_controls_count": 10,
    "mandatory_auth_pass": True,
    "immutable_audit_logging_pass": True,
    "persisted_pii_redaction_pass": False,
    "redis_session_persistence_pass": True,
    "tokenizer_backed_accounting_pass": False,
    "observability_alerting_pass": True,
    "api_versioning_pass": True,
    "process_supervision_pass": True,
    "backup_restore_pass": True,
    "one_command_release_smoke_pass": False,
    "auth_bypass_found": False,
    "audit_write_loss_found": False,
    "pii_leak_found": True,
    "redis_continuity_break_found": False,
    "token_accounting_fallback_found": True,
    "observability_gap_found": False,
    "api_versioning_gap_found": False,
    "supervision_gap_found": False,
    "backup_restore_gap_found": False,
    "release_smoke_gap_found": True,
    "runtime_error_count": 0,
    "unexplained_count": 0,
}

RETENTION_EXPECTED = {
    "retained_after_family_eval": False,
    "retained_after_restart": False,
    "retained_after_restore": True,
    "answer_path_delta_reintroduced": True,
    "runtime_error_count": 0,
    "unexplained_count": 0,
}

REFERENCE_FILES = {
    "faz21": ROOT / "docs" / "FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
    "faz24": ROOT / "docs" / "FAZ24-RC-M-DISCARD-ARCHIVAL-CLOSURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md",
    "faz25": ROOT / "docs" / "FAZ25-POST-RC-M-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md",
    "faz26": ROOT / "docs" / "FAZ26-RC-N-RELEASE-CONTROLS-CLOSURE-REOPEN-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-28.md",
    "faz27": ROOT / "docs" / "FAZ27-RC-N-RELEASE-CONTROLS-BOUNDARY-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-28.md",
    "faz28": ROOT / "docs" / "FAZ28-RC-O-RELEASE-CONTROLS-BOUNDARY-REPAIR-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-28.md",
}

REFERENCE_MARKERS = {
    "faz21": [
        "PASS - Current Authority Canonicalized",
        "current_canonical_authority_adopted = true",
    ],
    "faz24": [
        "PASS - RC-M Discard Archived Under Canonical Current Authority",
        "archive_status = `closed`",
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
    "faz28": [
        "NO-GO - RC-O Boundary Repair Failed",
        "preprojection_hash_mismatch_count = `152`",
        "response_envelope_hash_mismatch_count = `92`",
        "retained_after_restore = `true`",
    ],
}

FAZ21_CANONICAL_REFERENCE_JSON = ROOT / "coordination" / "faz21-current-authority-canonical-reference-pack-2026-03-27.json"
FAZ21_CANONICAL_GATE_JSON = ROOT / "evaluation" / "reports" / "faz21-current-authority-canonicalization-gate-2026-03-27.json"
FAZ27_REFERENCE_PACK_JSON = ROOT / "coordination" / "faz27-reference-pack-2026-03-28.json"
FAZ28_REFERENCE_PACK_JSON = ROOT / "coordination" / "faz28-reference-pack-2026-03-28.json"
FAZ28_PHASE_PACKAGE_JSON = ROOT / "coordination" / "faz28-phase-package-2026-03-28.json"

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

BOUNDARY_FRONTIER_PACK_PATH = ROOT / "configs" / "evaluation" / f"test_questions_faz29_boundary_frontier_166_{COMPACT_DATE}.json"
REPAIR_DELTA_PACK_PATH = ROOT / "configs" / "evaluation" / f"test_questions_faz29_repair_delta_14_{COMPACT_DATE}.json"
SPILLOVER_GUARD_PACK_PATH = ROOT / "configs" / "evaluation" / f"test_questions_faz29_spillover_guard_24_{COMPACT_DATE}.json"
MATERIALIZED_REFERENCE_JSON = ROOT / "coordination" / f"faz29-reference-pack-{DATE}.json"
PHASE_PACKAGE_JSON = ROOT / "coordination" / f"faz29-phase-package-{DATE}.json"
RESULT_REPORT_PATH = ROOT / "reports" / f"FAZ29-RC-O-RELEASE-CONTROLS-BOUNDARY-REPAIR-RECAPTURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-{DATE}.md"
DOC_RESULT_REPORT_PATH = ROOT / "docs" / RESULT_REPORT_PATH.name
FAZ28_BOUNDARY_PAIR_JSON = ROOT / "runtime_logs" / "faz28_boundary_frontier_pair.json"
FAZ28_SPILLOVER_PAIR_JSON = ROOT / "runtime_logs" / "faz28_spillover_pair.json"
SPILLOVER_GUARD_PACK_SOURCE_JSON = ROOT / "configs" / "evaluation" / "test_questions_faz28_spillover_guard_24_20260328.json"

TRUTH_FIELDS = {
    "wp2_current_authority": {
        "control_pair_authority_match": True,
        "current_authority_contract_breach": False,
        "surface_breach_from_history_reintroduced": False,
        "current_canonical_authority_adopted": True,
        "control_pair_runtime_error_count": 0,
    },
    "wp2_upstream_equality": {
        "model_request_payload_hash_mismatch_count": 0,
        "retrieval_request_hash_mismatch_count": 0,
        "assembled_context_hash_mismatch_count": 0,
        "runtime_error_count": 0,
    },
    "wp3_boundary": dict(BOUNDARY_EXPECTED),
    "wp4_spillover": dict(SPILLOVER_EXPECTED),
    "wp5_acceptance": dict(ACCEPTANCE_EXPECTED),
    "wp6_retention": dict(RETENTION_EXPECTED),
}

_METRIC_RE = re.compile(r"^([a-zA-Z0-9_:]+)(\{[^}]*\})?\s+([0-9.eE+-]+)$")

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


def build_repair_delta_records(frontier_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    phase_payload = load_json(FAZ28_PHASE_PACKAGE_JSON)
    remaining_ids = {
        str(row["question_id"])
        for row in (phase_payload.get("boundary_frontier_summary", {}).get("mismatch_rows") or [])
        if isinstance(row, dict) and row.get("question_id")
    }
    rows = [dict(row) for row in frontier_records if str(row.get("id") or "") not in remaining_ids]
    if len(rows) != BOUNDARY_EXPECTED["repair_delta_record_count"]:
        raise RuntimeError(
            f"repair delta set must be {BOUNDARY_EXPECTED['repair_delta_record_count']} rows, got {len(rows)}"
        )
    return rows


def build_spillover_guard_records() -> list[dict[str, Any]]:
    payload = load_json(SPILLOVER_GUARD_PACK_SOURCE_JSON)
    records = payload.get("questions") if isinstance(payload, dict) else payload
    rows = [dict(row) for row in records if isinstance(row, dict)]
    if len(rows) != SPILLOVER_EXPECTED["record_count"]:
        raise RuntimeError(f"spillover guard must be {SPILLOVER_EXPECTED['record_count']} rows, got {len(rows)}")
    return rows


def expected_boundary_summary_from_faz28() -> dict[str, Any]:
    return {
        "input_pack_count": 166,
        "remaining_mismatch_count": 152,
        "repair_delta_record_count": 14,
        **BOUNDARY_EXPECTED,
    }


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


def summarize_pack_report(*, report: dict[str, Any], pack_rows: list[dict[str, Any]]) -> dict[str, Any]:
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
