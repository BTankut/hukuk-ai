from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


TARGETED_QUESTION_IDS = [
    "TBK-051",
    "TBK-054",
    "TBK-055",
    "TBK-057",
    "TBK-058",
    "TBK-061",
]

O_STAGE_ORDER = [
    "normalized_request_hash",
    "model_request_payload_hash",
    "generation_contract_hash",
    "preprojection_anchor_hash",
    "cited_projection_hash",
    "citation_set_projection_hash",
    "final_mode_mapping_hash",
    "blocked_reason_set_hash",
    "final_answer_payload_hash",
    "response_envelope_hash",
    "serialized_output_hash",
]

UPSTREAM_MISMATCH_KEYS = [
    "normalized_request_hash_mismatch_count",
    "model_request_payload_hash_mismatch_count",
    "generation_contract_hash_mismatch_count",
    "preprojection_anchor_mismatch_count",
]

FINAL_MODE_RESIDUAL_QUESTION_ID = "TBK-020"

NEXT_WORK_BY_ROOT_CAUSE = {
    "control_pair_authority_breach": "control-pair authority repair gate",
    "rc_l_build_surface_breach": "rc-l replacement build-surface isolation gate",
    "full_family_context_breach": "full-family context bind repair gate",
    "runtime_binding_breach": "runtime binding repair gate",
    "eval_contract_breach": "eval contract repair gate",
    "request_payload_authority_breach_from_rc_l": "request-payload authority repair gate",
    "localized_final_mode_residual": "targeted final-mode residual repair gate",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def question_bank_rows(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    rows: list[dict[str, Any]]
    if isinstance(payload, dict) and isinstance(payload.get("questions"), list):
        rows = payload["questions"]
    elif isinstance(payload, list):
        rows = payload
    else:
        raise ValueError(f"unsupported question bank format: {path}")
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        question_id = row.get("question_id") or row.get("id")
        if not question_id:
            continue
        normalized.append({"question_id": str(question_id), **row})
    return normalized


def question_bank_index(path: Path) -> dict[str, dict[str, Any]]:
    return {
        str(row["question_id"]): {"ordinal_index": idx, **row}
        for idx, row in enumerate(question_bank_rows(path), start=1)
    }


def question_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in report.get("per_question", [])
        if isinstance(row, dict) and row.get("question_id")
    ]


def question_index(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["question_id"]): row for row in question_rows(report)}


def mismatch_index(report: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    family_id = str(report["family_id"])
    return {
        (family_id, str(row["question_id"])): row
        for row in report.get("mismatch_rows", [])
        if isinstance(row, dict) and row.get("question_id")
    }


def authoritative_row_index(report: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    family_id = str(report["family_id"])
    return {
        (family_id, str(row["question_id"])): row
        for row in report.get("authoritative_rows", [])
        if isinstance(row, dict) and row.get("question_id")
    }


def o_stage_to_f_stage(o_stage: str | None) -> str | None:
    if not o_stage:
        return None
    return o_stage


def pick_dominant(histogram: dict[str, int]) -> str | None:
    if not histogram:
        return None
    return sorted(histogram.items(), key=lambda item: (-item[1], item[0]))[0][0]
