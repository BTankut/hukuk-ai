from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


AUTHORIZED_REPAIR_RECORD_IDS = (
    "TBK-051",
    "TBK-054",
    "TBK-055",
    "TBK-057",
    "TBK-058",
    "TBK-061",
)

AUTHORIZED_OUTPUT_SURFACE_STAGES = (
    "final_mode_mapping_hash",
    "blocked_reason_set_hash",
    "response_envelope_hash",
    "serialized_output_hash",
)

FAMILY_ORDER = {
    "faz1-50": 0,
    "v2-95": 1,
    "v3-170": 2,
}

EXPECTED_CONTROL_BY_FAMILY = {
    "faz1-50": {
        "mismatch_count": 0,
        "family_metric_delta_zero": True,
        "normalized_request_hash_mismatch_count": 0,
        "model_request_payload_hash_mismatch_count": 0,
        "generation_contract_hash_mismatch_count": 0,
        "preprojection_anchor_mismatch_count": 0,
        "final_mode_mapping_hash_mismatch_count": 0,
        "blocked_reason_set_mismatch_count": 0,
        "response_envelope_hash_mismatch_count": 0,
    },
    "v2-95": {
        "mismatch_count": 0,
        "family_metric_delta_zero": True,
        "normalized_request_hash_mismatch_count": 0,
        "model_request_payload_hash_mismatch_count": 0,
        "generation_contract_hash_mismatch_count": 0,
        "preprojection_anchor_mismatch_count": 0,
        "final_mode_mapping_hash_mismatch_count": 0,
        "blocked_reason_set_mismatch_count": 0,
        "response_envelope_hash_mismatch_count": 0,
    },
    "v3-170": {
        "mismatch_count": 6,
        "family_metric_delta_zero": True,
        "normalized_request_hash_mismatch_count": 0,
        "model_request_payload_hash_mismatch_count": 0,
        "generation_contract_hash_mismatch_count": 0,
        "preprojection_anchor_mismatch_count": 0,
        "final_mode_mapping_hash_mismatch_count": 6,
        "blocked_reason_set_mismatch_count": 6,
        "response_envelope_hash_mismatch_count": 6,
    },
}

UPSTREAM_F0_F12_STAGES = (
    "candidate_manifest_hash",
    "effective_file_set_hash",
    "resolved_candidate_config_hash",
    "runtime_lane_binding_hash",
    "eval_run_contract_hash",
    "question_batch_context_hash",
    "per_question_request_input_hash",
    "normalized_request_hash",
    "model_request_payload_hash",
    "generation_contract_hash",
    "preprojection_anchor_hash",
    "cited_projection_hash",
    "citation_set_projection_hash",
)

F_STAGE_TO_O_STAGE = {
    "normalized_request_hash": "normalized_request_hash",
    "model_request_payload_hash": "model_request_payload_hash",
    "generation_contract_hash": "generation_contract_hash",
    "preprojection_anchor_hash": "preprojection_anchor_hash",
    "cited_projection_hash": "cited_projection_hash",
    "citation_set_projection_hash": "citation_set_projection_hash",
    "final_mode_mapping_hash": "final_mode_mapping_hash",
    "blocked_reason_set_hash": "blocked_reason_set_hash",
    "final_answer_payload_hash": "final_answer_payload_hash",
    "response_envelope_hash": "response_envelope_hash",
    "serialized_output_hash": "serialized_output_hash",
}

DECISION_TO_NEXT_WORK = {
    "PASS - RC-M Output Parity Surface Breach Localized": "rc-m replacement output-parity surface isolation gate",
    "NO-GO - Current Authority Unstable": "current authority recapture",
    "NO-GO - RC-M Surface Breach Non-Reproducible": "rc-m surface-breach repeatability recapture",
    "NO-GO - Unexplained Output Parity Surface Breach": "rc-m output-parity surface authority forensics recapture",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def family_sort_key(family_id: str) -> tuple[int, str]:
    return (FAMILY_ORDER.get(family_id, 999), family_id)


def bool_text(value: Any) -> str:
    return str(bool(value)).lower()


def markdown_table(columns: list[tuple[str, str]], rows: list[dict[str, Any]]) -> list[str]:
    header = "| " + " | ".join(label for _, label in columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(key, "")) for key, _ in columns) + " |")
    return [header, divider, *body]
