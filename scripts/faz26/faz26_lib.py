#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-03-28"
COMPACT_DATE = "20260328"

PASS_DECISION = "PASS - RC-N Release Controls Closed Under Canonical Current Authority"
FAIL_DECISION = "NO-GO - Release Controls"

PASS_NEXT_WORK = "rc-n cutover-readiness closure reopen under canonical current authority"
FAIL_NEXT_WORK = "rc-n release-controls boundary forensics under canonical current authority"

RELEASE_CONTROLS_EXACT_SET = [
    "mandatory auth",
    "immutable audit logging",
    "persisted PII redaction",
    "Redis session persistence",
    "tokenizer-backed accounting",
    "observability / alerting",
    "API versioning",
    "process supervision",
    "backup / restore",
    "one-command release smoke",
]

REFERENCE_FILES = {
    "faz6": ROOT / "docs" / "FAZ6-ATTRIBUTION-LOSS-DECOMPOSITION-VE-REPAIR-GATE-RAPORU-2026-03-23.md",
    "faz7": ROOT / "docs" / "FAZ7-RELEASE-CONTROLS-CLOSURE-VE-NARROW-PILOT-STEERING-RAPORU-2026-03-24.md",
    "faz21": ROOT / "docs" / "FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
    "faz24": ROOT / "docs" / "FAZ24-RC-M-DISCARD-ARCHIVAL-CLOSURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md",
    "faz25": ROOT / "docs" / "FAZ25-POST-RC-M-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md",
    "faz1_5": ROOT / "coordination" / "faz1_5-closure-matrix-2026-03-22.md",
}

REFERENCE_MARKERS = {
    "faz6": [
        "PASS - Repair Surface Localized and RC-G Accepted",
    ],
    "faz7": [
        "NO-GO - Release Controls",
    ],
    "faz21": [
        "PASS - Current Authority Canonicalized",
        "`current_canonical_authority_adopted = true`",
    ],
    "faz24": [
        "PASS - RC-M Discard Archived Under Canonical Current Authority",
        "archive_status = `closed`",
    ],
    "faz25": [
        "PASS - Post-RC-M Steering Re-Entered Under Canonical Current Authority",
        "next_candidate_id = `RC-N`",
    ],
    "faz1_5": [
        "must-close release controls remain open",
    ],
}

FAMILY_DEFS = [
    ("faz1-50", ROOT / "configs" / "evaluation" / "test_questions.json", "faz1_50"),
    ("v2-95", ROOT / "configs" / "evaluation" / "test_questions_v2_95.json", "v2_95"),
    ("v3-170", ROOT / "configs" / "evaluation" / "test_questions_v3_170.json", "v3_170"),
]

_METRIC_RE = re.compile(r'^([a-zA-Z0-9_:]+)(\{[^}]*\})?\s+([0-9.eE+-]+)$')


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def markdown_table(columns: list[tuple[str, str]], rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(label for _, label in columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        values: list[str] = []
        for key, _ in columns:
            value = row.get(key)
            if isinstance(value, bool):
                values.append(bool_text(value))
            elif isinstance(value, list):
                values.append(", ".join(str(item) for item in value))
            elif isinstance(value, dict):
                values.append(json.dumps(value, ensure_ascii=False, sort_keys=True))
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def question_count_from_bank(path: Path) -> int:
    payload = load_json(path)
    if isinstance(payload, dict):
        rows = payload.get("questions")
        if isinstance(rows, list):
            return len(rows)
    if isinstance(payload, list):
        return len(payload)
    raise ValueError(f"unsupported question bank: {path}")


def parse_headers_text(text: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for raw_line in text.splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    return headers


def parse_metrics_text(text: str) -> dict[tuple[str, str], float]:
    metrics: dict[tuple[str, str], float] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = _METRIC_RE.match(line)
        if not match:
            continue
        name, labels, value = match.groups()
        metrics[(name, labels or "")] = float(value)
    return metrics


def metric_value(metrics: dict[tuple[str, str], float], name: str, *, source: str | None = None) -> float:
    if source is None:
        return metrics.get((name, ""), 0.0)
    return metrics.get((name, f'{{source="{source}"}}'), 0.0)
