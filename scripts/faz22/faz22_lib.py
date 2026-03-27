#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


FAMILY_ORDER = {
    "faz1-50": 0,
    "v2-95": 1,
    "v3-170": 2,
}

UPSTREAM_F0_F12_FIELDS = (
    "normalized_request_hash_mismatch_count",
    "model_request_payload_hash_mismatch_count",
    "generation_contract_hash_mismatch_count",
    "preprojection_anchor_mismatch_count",
    "cited_projection_hash_mismatch_count",
    "citation_set_projection_hash_mismatch_count",
)

AUTHORIZED_OUTPUT_SURFACE_STAGES = {
    "final_mode_mapping_hash",
    "blocked_reason_set_hash",
    "final_answer_payload_hash",
    "response_envelope_hash",
    "serialized_output_hash",
    "answer_body_hash",
    "citation_body_hash",
    "refusal_body_hash",
}

F_STAGE_CODE = {
    "candidate_manifest_hash": "F0",
    "effective_file_set_hash": "F1",
    "resolved_candidate_config_hash": "F2",
    "runtime_lane_binding_hash": "F3",
    "eval_run_contract_hash": "F4",
    "question_batch_context_hash": "F5",
    "per_question_request_input_hash": "F6",
    "normalized_request_hash": "F7",
    "model_request_payload_hash": "F8",
    "generation_contract_hash": "F9",
    "preprojection_anchor_hash": "F10",
    "cited_projection_hash": "F11",
    "citation_set_projection_hash": "F12",
    "final_mode_mapping_hash": "F13",
    "blocked_reason_set_hash": "F14",
    "final_answer_payload_hash": "F15",
    "response_envelope_hash": "F16",
    "serialized_output_hash": "F17",
    "answer_body_hash": "F18",
    "citation_body_hash": "F19",
    "refusal_body_hash": "F20",
}

F_TO_O_STAGE = {
    "normalized_request_hash": "O0",
    "model_request_payload_hash": "O1",
    "generation_contract_hash": "O2",
    "preprojection_anchor_hash": "O3",
    "cited_projection_hash": "O4",
    "citation_set_projection_hash": "O5",
    "final_mode_mapping_hash": "O6",
    "blocked_reason_set_hash": "O7",
    "final_answer_payload_hash": "O8",
    "response_envelope_hash": "O9",
    "serialized_output_hash": "O10",
}

DECISION_TO_NEXT_WORK = {
    "PASS - RC-M Output Parity Surface Breach Localized Under Canonical Current Authority": (
        "rc-m authoritative output-parity repair gate under canonical current authority"
    ),
    "NO-GO - Canonical Current Authority Contract Breach": "canonical current authority breach forensics",
    "NO-GO - RC-M Surface Breach Non-Reproducible Under Canonical Current Authority": (
        "rc-m authoritative summary truth reconciliation under canonical current authority"
    ),
    "NO-GO - Unexplained Output Parity Surface Breach Under Canonical Current Authority": (
        "rc-m unexplained output-parity surface forensics under canonical current authority"
    ),
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def bool_text(value: Any) -> str:
    return str(bool(value)).lower()


def family_sort_key(family_id: str) -> tuple[int, str]:
    return (FAMILY_ORDER.get(family_id, 999), family_id)


def markdown_table(columns: list[tuple[str, str]], rows: list[dict[str, Any]]) -> list[str]:
    header = "| " + " | ".join(label for _, label in columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        rendered = []
        for key, _ in columns:
            value = row.get(key)
            if isinstance(value, list):
                value = ", ".join(str(item) for item in value)
            elif isinstance(value, dict):
                value = json.dumps(value, ensure_ascii=False, sort_keys=True)
            rendered.append(str(value))
        body.append("| " + " | ".join(rendered) + " |")
    return [header, divider, *body]


def stage_label(stage_name: str | None, mapping: dict[str, str]) -> str | None:
    if not stage_name:
        return None
    code = mapping.get(stage_name)
    if code is None:
        return stage_name
    return f"{code}={stage_name}"
