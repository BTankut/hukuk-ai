from __future__ import annotations

import json
from pathlib import Path
from typing import Any


STAGE_ORDER = [
    "raw_input_request",
    "normalized_request",
    "auth_enriched_request",
    "session_enriched_request",
    "retrieval_input_payload",
    "retrieved_source_id_ordered_list",
    "assembly_payload",
    "model_request_payload",
    "generation_contract",
    "raw_answer_object",
    "response_envelope",
    "eval_client_parsed_object",
    "normalized_parity_object",
]

PRIMARY_REASON_BY_STAGE = {
    "raw_input_request": "normalized_request_hash_drift",
    "normalized_request": "normalized_request_hash_drift",
    "auth_enriched_request": "auth_visibility_leak",
    "session_enriched_request": "session_visibility_leak",
    "retrieval_input_payload": "retrieval_input_hash_drift",
    "retrieved_source_id_ordered_list": "retrieved_source_order_drift",
    "assembly_payload": "assembly_payload_hash_drift",
    "model_request_payload": "model_request_payload_hash_drift",
    "generation_contract": "generation_contract_hash_drift",
    "raw_answer_object": "raw_answer_object_hash_drift",
    "response_envelope": "response_envelope_mapping_drift",
    "eval_client_parsed_object": "eval_client_parse_drift",
    "normalized_parity_object": "eval_client_parse_drift",
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


def stage_map(question: dict[str, Any]) -> dict[str, dict[str, Any]]:
    parity_trace = (question.get("trace") or {}).get("parity_trace") or {}
    stages = parity_trace.get("stages") or []
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
