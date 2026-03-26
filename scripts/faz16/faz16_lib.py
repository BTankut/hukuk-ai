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

ALLOWED_CHANGED_FIELDS = {
    "final_mode_mapping_hash",
    "blocked_reason_set_hash",
    "response_envelope_hash",
}

UPSTREAM_EQUALITY_FIELDS = {
    "normalized_request_hash",
    "model_request_payload_hash",
    "generation_contract_hash",
    "preprojection_anchor_hash",
    "cited_projection_hash",
    "citation_set_projection_hash",
}

UPSTREAM_MISMATCH_KEYS = {
    "normalized_request_hash_mismatch",
    "model_request_payload_hash_mismatch",
    "generation_contract_hash_mismatch",
    "preprojection_anchor_mismatch",
    "cited_projection_hash_mismatch",
    "citation_set_projection_hash_mismatch",
}

NEXT_WORK_BY_DECISION = {
    "PASS - Replacement Build Surface Isolated": "rc-m authoritative output parity reopen",
    "NO-GO - Control Authority Unstable": "rc-g-vs-rc-j current authority recapture repeatability forensics",
    "NO-GO - Build Surface Isolation Failed": "rc-m build-surface breach first-divergence forensics",
    "NO-GO - Replacement Repair Ineffective": "rc-m downstream repair authority redesign gate",
}

QUESTIONS_PATH_BY_FAMILY = {
    "faz1-50": "configs/evaluation/test_questions.json",
    "v2-95": "configs/evaluation/test_questions_v2_95.json",
    "v3-170": "configs/evaluation/test_questions_v3_170.json",
}


def load_json(path: Path) -> dict[str, Any] | list[Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def question_bank_rows(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
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


def family_slug(family_id: str) -> str:
    return family_id.replace("-", "_")

