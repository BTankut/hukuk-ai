#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


AUTHORIZED_RECORD_IDS = (
    "TBK-051",
    "TBK-054",
    "TBK-055",
    "TBK-057",
    "TBK-058",
    "TBK-061",
)

FAMILY_ORDER = {
    "faz1-50": 0,
    "v2-95": 1,
    "v3-170": 2,
}

UPSTREAM_MISMATCH_FIELDS = (
    "normalized_request_hash_mismatch",
    "model_request_payload_hash_mismatch",
    "generation_contract_hash_mismatch",
    "preprojection_anchor_mismatch",
    "cited_projection_hash_mismatch",
    "citation_set_projection_hash_mismatch",
)

LOCALIZED_ALLOWED_FIRST_STAGES = {
    "final_mode_mapping_hash",
    "blocked_reason_set_hash",
    "response_envelope_hash",
    "serialized_output_hash",
}

DECISION_TO_NEXT_WORK = {
    "PASS - RC-M Authoritative Output Parity Closed": "rc-m release-controls retention reopen",
    "NO-GO - RC-M Authority Run Unstable": "rc-m authoritative output parity repeatability recapture",
    "NO-GO - RC-M Authoritative Output Parity Drift Localized": "rc-m authoritative output parity repair gate",
    "NO-GO - RC-M Output Parity Surface Breach": "rc-m discard and output-parity surface forensics",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def family_sort_key(family_id: str) -> tuple[int, str]:
    return (FAMILY_ORDER.get(family_id, 999), family_id)


def row_sort_key(row: dict[str, Any]) -> tuple[int, int, str]:
    return (
        FAMILY_ORDER.get(str(row.get("family_id")), 999),
        int(row.get("ordinal_index", 999999)),
        str(row.get("question_id", "")),
    )
