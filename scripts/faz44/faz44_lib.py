#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-04-01"
RESULT_REPORT_NAME = (
    "FAZ44-RC-R-NARROW-INTERNAL-PILOT-STEERING-UNDER-CANONICAL-CURRENT-"
    f"AUTHORITY-RAPORU-{DATE}.md"
)

PASS_DECISION = "PASS - Narrow Internal Pilot Steering Re-Entered Under Canonical Current Authority"
FAIL_DECISION = "NO-GO - Narrow Internal Pilot Steering Contract"

PASS_NEXT_WORK = "rc-r narrow internal pilot gate under canonical current authority"
FAIL_NEXT_WORK = "rc-r narrow internal pilot steering reconciliation under canonical current authority"

REFERENCE_DOCS = {
    "faz21": ROOT / "docs" / "FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
    "faz42": ROOT / "reports" / "FAZ42-RC-R-RELEASE-CONTROLS-PROCESS-ISOLATED-PERIMETER-ISOLATION-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
    "faz43": ROOT / "reports" / "FAZ43-RC-R-CUTOVER-READINESS-CLOSURE-REOPEN-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md",
}

REFERENCE_MARKERS = {
    "faz21": [
        "PASS - Current Authority Canonicalized",
        "- `current_canonical_authority_adopted = true`",
        "- `surface_breach_from_history_reintroduced = false`",
    ],
    "faz42": [
        "PASS - RC-R Process-Isolated Perimeter Isolated",
        "- faz1_50_mismatch_count = `0`",
        "- v2_95_mismatch_count = `0`",
        "- v3_170_mismatch_count = `0`",
        "- preprojection_hash_mismatch_count = `0`",
        "- raw_answer_hash_mismatch_count = `0`",
        "- response_envelope_hash_mismatch_count = `0`",
        "- must_close_release_controls_count = `10`",
        "- retained_after_restore = `true`",
        "- next_official_work = `cutover-readiness closure reopen under canonical current authority`",
    ],
    "faz43": [
        "PASS - Cutover Readiness Closed Under Canonical Current Authority",
        "- active_cutover_readiness_candidate = `RC-R`",
        "- comparison_order = `current_canonical -> historical_archive`",
        "- faz1_50_mismatch_count = `0`",
        "- v2_95_mismatch_count = `0`",
        "- v3_170_mismatch_count = `0`",
        "- preprojection_hash_mismatch_count = `0`",
        "- raw_answer_hash_mismatch_count = `0`",
        "- response_envelope_hash_mismatch_count = `0`",
        "- next_official_work = `narrow internal pilot steering under canonical current authority`",
    ],
}


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def bool_text(value: bool) -> str:
    return "true" if value else "false"
