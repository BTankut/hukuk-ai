#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-04-01"
RESULT_REPORT_NAME = (
    "FAZ45-RC-R-NARROW-INTERNAL-PILOT-GATE-UNDER-CANONICAL-CURRENT-"
    f"AUTHORITY-RAPORU-{DATE}.md"
)

PASS_DECISION = "PASS - RC-R Narrow Internal Pilot Gate Opened Under Canonical Current Authority"
FAIL_DECISION = "NO-GO - Narrow Internal Pilot Gate"

PASS_NEXT_WORK = "rc-r narrow internal pilot execution under canonical current authority"
FAIL_NEXT_WORK = "rc-r narrow internal pilot gate remediation under canonical current authority"

REFERENCE_DOCS = {
    "faz44": ROOT / "reports" / "FAZ44-RC-R-NARROW-INTERNAL-PILOT-STEERING-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md",
    "faz43": ROOT / "reports" / "FAZ43-RC-R-CUTOVER-READINESS-CLOSURE-REOPEN-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md",
    "faz42": ROOT / "reports" / "FAZ42-RC-R-RELEASE-CONTROLS-PROCESS-ISOLATED-PERIMETER-ISOLATION-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
    "faz41": ROOT / "reports" / "FAZ41-POST-RC-Q-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
    "faz21": ROOT / "docs" / "FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
}

REFERENCE_MARKERS = {
    "faz44": [
        "PASS - Narrow Internal Pilot Steering Re-Entered Under Canonical Current Authority",
        "- pilot_candidate_id = `RC-R`",
        "- pilot_scope = `narrow_internal_non_customer_controlled_observation_only`",
        "- pilot_user_class = `internal_named_allowlist_only`",
        "- pilot_start_authorized_in_this_phase = `false`",
        "- next_official_work = `rc-r narrow internal pilot gate under canonical current authority`",
    ],
    "faz43": [
        "PASS - Cutover Readiness Closed Under Canonical Current Authority",
        "- faz1_50_mismatch_count = `0`",
        "- v2_95_mismatch_count = `0`",
        "- v3_170_mismatch_count = `0`",
        "- preprojection_hash_mismatch_count = `0`",
        "- raw_answer_hash_mismatch_count = `0`",
        "- response_envelope_hash_mismatch_count = `0`",
        "- family_metric_delta_zero = `true`",
        "- next_official_work = `narrow internal pilot steering under canonical current authority`",
    ],
    "faz42": [
        "PASS - RC-R Process-Isolated Perimeter Isolated",
        "- must_close_release_controls_count = `10`",
        "- retained_after_family_eval = `true`",
        "- retained_after_restart = `true`",
        "- retained_after_restore = `true`",
        "- answer_path_delta_reintroduced = `false`",
    ],
    "faz41": [
        "PASS - Post-RC-Q Steering Re-Entered Under Canonical Current Authority",
        "- active_quality_reference = `RC-G`",
        "- active_control_pair = `RC-G vs RC-J`",
        "- active_forensic_reference = `RC-N`",
        "- current_perimeter_truth_reference = `RC-P`",
        "- next_candidate_id = `RC-R`",
    ],
    "faz21": [
        "PASS - Current Authority Canonicalized",
        "- `current_canonical_authority_adopted = true`",
        "- `surface_breach_from_history_reintroduced = false`",
    ],
}


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def bool_text(value: bool) -> str:
    return "true" if value else "false"
