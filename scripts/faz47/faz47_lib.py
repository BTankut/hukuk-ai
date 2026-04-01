#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-04-01"
RESULT_REPORT_NAME = (
    "FAZ47-POST-RC-R-NARROW-INTERNAL-PILOT-CLOSURE-VE-NEXT-TRACK-STEERING-"
    f"UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-{DATE}.md"
)

PASS_DECISION = "PASS - Post-RC-R Narrow Internal Pilot Closed And Next Track Re-Entered Under Canonical Current Authority"
FAIL_DECISION = "NO-GO - Steering Integrity"

PASS_NEXT_WORK = "rc-s coverage-database-expansion-readiness-gate under canonical current authority"
FAIL_NEXT_WORK = "post-rc-r steering integrity repair under canonical current authority"

REFERENCE_DOCS = {
    "faz42": ROOT / "reports" / "FAZ42-RC-R-RELEASE-CONTROLS-PROCESS-ISOLATED-PERIMETER-ISOLATION-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
    "faz43": ROOT / "reports" / "FAZ43-RC-R-CUTOVER-READINESS-CLOSURE-REOPEN-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md",
    "faz44": ROOT / "reports" / "FAZ44-RC-R-NARROW-INTERNAL-PILOT-STEERING-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md",
    "faz45": ROOT / "reports" / "FAZ45-RC-R-NARROW-INTERNAL-PILOT-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md",
    "faz46": ROOT / "reports" / "FAZ46-RC-R-NARROW-INTERNAL-PILOT-EXECUTION-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md",
    "faz1": ROOT / "docs" / "FAZ1-FINAL-RAPOR.md",
    "faz1_5": ROOT / "coordination" / "faz1_5-closure-matrix-2026-03-22.md",
}

REFERENCE_MARKERS = {
    "faz42": [
        "PASS - RC-R Process-Isolated Perimeter Isolated",
        "- faz1_50_mismatch_count = `0`",
        "- v2_95_mismatch_count = `0`",
        "- v3_170_mismatch_count = `0`",
        "- must_close_release_controls_count = `10`",
    ],
    "faz43": [
        "PASS - Cutover Readiness Closed Under Canonical Current Authority",
        "- active_cutover_readiness_candidate = `RC-R`",
        "- comparison_order = `current_canonical -> historical_archive`",
        "- preprojection_hash_mismatch_count = `0`",
        "- response_envelope_hash_mismatch_count = `0`",
    ],
    "faz44": [
        "PASS - Narrow Internal Pilot Steering Re-Entered Under Canonical Current Authority",
        "- pilot_candidate_id = `RC-R`",
        "- pilot_scope = `narrow_internal_non_customer_controlled_observation_only`",
        "- pilot_user_class = `internal_named_allowlist_only`",
        "- rollback_target = `RC-G canonical answer lane`",
    ],
    "faz45": [
        "PASS - RC-R Narrow Internal Pilot Gate Opened Under Canonical Current Authority",
        "- control_pair_authority_match = `true`",
        "- must_close_release_controls_pass = `true`",
        "- retained_after_restore = `true`",
        "- next_official_work = `rc-r narrow internal pilot execution under canonical current authority`",
    ],
    "faz46": [
        "PASS - RC-R Narrow Internal Pilot Executed Under Canonical Current Authority",
        "- admitted_operator_count = `3`",
        "- selected_operator_count = `3`",
        "- planned_session_count = `9`",
        "- completed_session_count = `9`",
        "- session_success_count = `9`",
        "- session_fail_count = `0`",
        "- authority_breach_count = `0`",
        "- model_visible_delta_count = `0`",
        "- runtime_error_count = `0`",
        "- incident_count = `0`",
    ],
    "faz1": [
        "FAZ 1 KABUL EDİLDİ",
        "Mevzuat-only baseline",
        "Dense-only + metadata filter",
    ],
    "faz1_5": [
        "Gate 4 - Steering Decision Gate | Closed",
        "WP-8 Final Decision Package | Closed",
        "Criterion | Status | Source Of Record | Open Item |",
    ],
}


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def bool_text(value: bool) -> str:
    return "true" if value else "false"
