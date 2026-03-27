#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DECISION_TO_NEXT_WORK = {
    "PASS - RC-M Authoritative Summary Truth Reconciled Under Canonical Current Authority": (
        "rc-m discard archival closure under canonical current authority"
    ),
    "NO-GO - Canonical Current Authority Summary Contract Breach": (
        "canonical current authority summary breach forensics"
    ),
    "NO-GO - Unexplained RC-M Summary Truth Divergence Under Canonical Current Authority": (
        "rc-m summary truth divergence forensics under canonical current authority"
    ),
}

REFERENCE_DECISIONS = {
    "faz16": "PASS - Replacement Build Surface Isolated",
    "faz17": "NO-GO - RC-M Output Parity Surface Breach",
    "faz21": "PASS - Current Authority Canonicalized",
    "faz22": "NO-GO - RC-M Surface Breach Non-Reproducible Under Canonical Current Authority",
}

RECONCILIATION_STAGES = ("R0", "R1", "R2", "R3", "R4")

ROOT_CAUSE_CLASSES = (
    "historical_summary_truth_reclassified_to_archive",
    "canonical_current_authority_summary_contract_breach",
    "unexplained_rc_m_summary_truth_divergence",
)


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def markdown_table(columns: list[tuple[str, str]], rows: list[dict[str, Any]]) -> list[str]:
    headers = [label for _, label in columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        rendered = []
        for key, _ in columns:
            value = row.get(key)
            if isinstance(value, list):
                value = ", ".join(str(item) for item in value)
            elif isinstance(value, dict):
                value = json.dumps(value, ensure_ascii=False, sort_keys=True)
            rendered.append(str(value))
        lines.append("| " + " | ".join(rendered) + " |")
    return lines
