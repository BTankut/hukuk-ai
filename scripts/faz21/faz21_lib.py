#!/usr/bin/env python3
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any


DECISION_TO_NEXT_WORK = {
    "PASS - Current Authority Canonicalized": "rc-m discard and output-parity surface forensics reopen under canonical current authority",
    "NO-GO - Current Authority Canonicalization Breach": "current authority canonicalization breach forensics",
}

CONSUMER_ROWS = [
    {
        "consumer_name": "current_authority_gate",
        "consumer_scope": "official current authority gate",
        "primary_reference": "canonical_current_authority_ref",
        "primary_reference_source": "faz19 stable current truth",
        "secondary_reference": "historical_archive_ref",
        "secondary_reference_source": "faz13 historical authority + faz18 instability snapshot",
        "comparison_order": "current_canonical -> historical_archive",
        "current_channel": "authoritative",
        "history_channel": "diagnostic_only",
        "allowed_history_stage_set": ["H10", "H11"],
        "blocked_history_stage_set": ["H0-H9"],
        "canonical_current_truth_match_required": True,
        "surface_breach_from_history_reintroduced": False,
        "notes": "Current gate decisions are taken from canonical current authority first.",
    },
    {
        "consumer_name": "control_pair_authoritative_comparison",
        "consumer_scope": "rc_g_vs_rc_j authoritative comparison",
        "primary_reference": "canonical_current_authority_ref",
        "primary_reference_source": "faz19 stable current truth",
        "secondary_reference": "historical_archive_ref",
        "secondary_reference_source": "faz13 historical authority + faz18 instability snapshot",
        "comparison_order": "current_canonical -> historical_archive",
        "current_channel": "authoritative",
        "history_channel": "diagnostic_only",
        "allowed_history_stage_set": ["H10", "H11"],
        "blocked_history_stage_set": ["H0-H9"],
        "canonical_current_truth_match_required": True,
        "surface_breach_from_history_reintroduced": False,
        "notes": "Historical rows stay explanatory only and cannot replace the current reference.",
    },
    {
        "consumer_name": "frontier_localization",
        "consumer_scope": "frontier localization and replay interpretation",
        "primary_reference": "canonical_current_authority_ref",
        "primary_reference_source": "faz19 stable current truth",
        "secondary_reference": "historical_archive_ref",
        "secondary_reference_source": "faz13 historical authority + faz18 instability snapshot",
        "comparison_order": "current_canonical -> historical_archive",
        "current_channel": "authoritative",
        "history_channel": "diagnostic_only",
        "allowed_history_stage_set": ["H10", "H11"],
        "blocked_history_stage_set": ["H0-H9"],
        "canonical_current_truth_match_required": True,
        "surface_breach_from_history_reintroduced": False,
        "notes": "Historical archive remains available only to explain prior FAZ13/FAZ18 differences.",
    },
    {
        "consumer_name": "output_parity_reopen",
        "consumer_scope": "future output parity reopen under canonical current authority",
        "primary_reference": "canonical_current_authority_ref",
        "primary_reference_source": "faz19 stable current truth",
        "secondary_reference": "historical_archive_ref",
        "secondary_reference_source": "faz13 historical authority + faz18 instability snapshot",
        "comparison_order": "current_canonical -> historical_archive",
        "current_channel": "authoritative",
        "history_channel": "diagnostic_only",
        "allowed_history_stage_set": ["H10", "H11"],
        "blocked_history_stage_set": ["H0-H9"],
        "canonical_current_truth_match_required": True,
        "surface_breach_from_history_reintroduced": False,
        "notes": "Historical mismatch rows cannot be promoted back into current parity breach state.",
    },
]


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def markdown_table(columns: list[tuple[str, str]], rows: list[dict[str, Any]]) -> list[str]:
    headers = [label for _, label in columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        values = []
        for key, _ in columns:
            value = row.get(key)
            if isinstance(value, list):
                value = ", ".join(str(item) for item in value)
            elif isinstance(value, dict):
                value = json.dumps(value, ensure_ascii=False, sort_keys=True)
            values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def bool_text(value: bool) -> str:
    return "true" if value else "false"
