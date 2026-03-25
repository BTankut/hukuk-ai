from __future__ import annotations

import json
from pathlib import Path
from typing import Any


V3_TRACE_STAGE_ORDER = [
    "normalized_request",
    "model_request_payload",
    "generation_contract",
    "worker_assignment_tuple",
    "session_namespace_after_payload_freeze",
    "cache_namespace_or_cache_key",
    "generation_start_ordinal",
    "first_token_id_hash",
    "raw_token_stream_hash",
    "raw_answer_object",
    "response_envelope",
    "eval_client_parsed_object",
    "normalized_parity_object",
]

PRIMARY_REASONS = {
    "C1": "process_reuse_state_leak",
    "C2": "request_reset_missing",
    "C3": "session_namespace_leak",
    "C4": "cache_namespace_bleed",
    "C5": "post_payload_context_shadow",
    "C6": "release_control_bind_effect",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def question_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in report.get("per_question", [])
        if isinstance(row, dict) and row.get("question_id")
    ]


def question_index(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row["question_id"]): row
        for row in question_rows(report)
    }


def parity_trace(question: dict[str, Any]) -> dict[str, Any]:
    trace = question.get("trace") or {}
    v3_trace = trace.get("v3_runtime_parity_trace") or {}
    if v3_trace:
        return v3_trace
    return trace.get("parity_trace") or {}


def stage_map(question: dict[str, Any]) -> dict[str, dict[str, Any]]:
    stages = parity_trace(question).get("stages") or []
    return {
        str(stage.get("stage")): stage
        for stage in stages
        if isinstance(stage, dict) and stage.get("stage")
    }


def stage_hash(question: dict[str, Any], stage_name: str) -> str | None:
    stage = stage_map(question).get(stage_name) or {}
    value = stage.get("hash")
    return value if isinstance(value, str) else None


def stage_payload(question: dict[str, Any], stage_name: str) -> dict[str, Any]:
    stage = stage_map(question).get(stage_name) or {}
    payload = stage.get("payload")
    return payload if isinstance(payload, dict) else {}


def preprojection_hash(question: dict[str, Any]) -> str | None:
    value = parity_trace(question).get("preprojection_hash")
    return value if isinstance(value, str) else None


def runtime_error_row(question: dict[str, Any]) -> tuple[bool, str | None]:
    error_value = question.get("error")
    if isinstance(error_value, str) and error_value.strip():
        return True, error_value.strip()
    return False, None


def question_bank_rows(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    def normalize_row(row: dict[str, Any]) -> dict[str, Any] | None:
        if not isinstance(row, dict):
            return None
        question_id = row.get("question_id") or row.get("id")
        if not question_id:
            return None
        if row.get("question_id"):
            return row
        return {"question_id": str(question_id), **row}

    if isinstance(payload, dict):
        rows = payload.get("questions")
        if isinstance(rows, list):
            return [normalized for row in rows if (normalized := normalize_row(row)) is not None]
    if isinstance(payload, list):
        return [normalized for row in payload if (normalized := normalize_row(row)) is not None]
    raise ValueError(f"unsupported question bank format: {path}")


def question_bank_index(path: Path) -> dict[str, dict[str, Any]]:
    rows = question_bank_rows(path)
    return {
        str(row["question_id"]): {"ordinal_index": idx, **row}
        for idx, row in enumerate(rows, start=1)
    }
