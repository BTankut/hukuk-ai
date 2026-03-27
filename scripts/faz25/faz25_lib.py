#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PASS_DECISION = "PASS - Post-RC-M Steering Re-Entered Under Canonical Current Authority"
FAIL_DECISION = "FAIL - Post-RC-M Steering Baseline Not Materialized"

PASS_NEXT_WORK = "rc-n release-controls closure reopen under canonical current authority"
FAIL_NEXT_WORK = "post-rc-m steering remediation"

REFERENCE_FILES = {
    "faz6": "docs/FAZ6-ATTRIBUTION-LOSS-DECOMPOSITION-VE-REPAIR-GATE-RAPORU-2026-03-23.md",
    "faz7": "docs/FAZ7-RELEASE-CONTROLS-CLOSURE-VE-NARROW-PILOT-STEERING-RAPORU-2026-03-24.md",
    "faz21": "docs/FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
    "faz24": "docs/FAZ24-RC-M-DISCARD-ARCHIVAL-CLOSURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md",
    "faz1_5": "coordination/faz1_5-closure-matrix-2026-03-22.md",
}

SOURCE_OF_RECORD_FILES = {
    "faz1_5_release_matrix": "coordination/faz1_5-production-readiness-matrix-2026-03-22.md",
    "faz7_release_matrix": "coordination/faz7-production-readiness-matrix-v2-2026-03-24.md",
}

REFERENCE_MARKERS = {
    "faz6": {
        "official_decision": "PASS - Repair Surface Localized and RC-G Accepted",
    },
    "faz7": {
        "official_decision": "NO-GO - Release Controls",
        "allowed_diff_surface": "allowed diff surface: release-controls / observability / session / auth / API versioning / eval client",
    },
    "faz21": {
        "official_decision": "PASS - Current Authority Canonicalized",
        "current_canonical_authority_adopted": "current_canonical_authority_adopted = true",
        "comparison_order": "authoritative comparison order = `current_canonical -> historical_archive`",
    },
    "faz24": {
        "official_decision": "PASS - RC-M Discard Archived Under Canonical Current Authority",
        "next_official_work": "post-rc-m steering re-entry under canonical current authority",
        "candidate_status": "candidate_status = `discard_archived`",
    },
    "faz1_5": {
        "release_gate_open": "must-close release controls remain open",
    },
}

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


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def bool_text(value: bool) -> str:
    return "true" if value else "false"
