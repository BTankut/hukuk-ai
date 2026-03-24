from __future__ import annotations

import json
from pathlib import Path
from typing import Any


TRACE_STAGE_ORDER = [
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
    "L0": "raw_generation_nondeterminism",
    "L2": "process_reinit_dependency",
    "L3": "shared_runner_state_bleed",
    "L4": "post_payload_release_control_bleed",
    "L5": "request_order_accumulation_drift",
    "L6": "worker_affinity_or_parallelism_drift",
    "L7": "generation_cache_namespace_drift",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def question_index(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item["question_id"]): item
        for item in report.get("per_question", [])
        if isinstance(item, dict) and item.get("question_id")
    }


def runtime_trace(question: dict[str, Any]) -> dict[str, Any]:
    trace = question.get("trace") or {}
    return trace.get("v3_runtime_parity_trace") or {}


def stage_map(question: dict[str, Any]) -> dict[str, dict[str, Any]]:
    stages = runtime_trace(question).get("stages") or []
    return {
        str(item.get("stage")): item
        for item in stages
        if isinstance(item, dict) and item.get("stage")
    }


def stage_hash(stage_payload: dict[str, Any] | None) -> str | None:
    if not isinstance(stage_payload, dict):
        return None
    value = stage_payload.get("hash")
    return value if isinstance(value, str) else None


def stage_payload(stage_payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(stage_payload, dict):
        return {}
    payload = stage_payload.get("payload")
    return payload if isinstance(payload, dict) else {}


def top_level_payload_diff(reference: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
    differing: list[str] = []
    for key in sorted(set(reference) | set(candidate)):
        if reference.get(key) != candidate.get(key):
            differing.append(key)
    return differing
