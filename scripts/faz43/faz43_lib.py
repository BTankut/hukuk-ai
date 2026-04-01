#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-04-01"
RESULT_REPORT_NAME = (
    "FAZ43-RC-R-CUTOVER-READINESS-CLOSURE-REOPEN-UNDER-CANONICAL-CURRENT-"
    f"AUTHORITY-RAPORU-{DATE}.md"
)

PASS_DECISION = "PASS - Cutover Readiness Closed Under Canonical Current Authority"
FAIL_DECISION = "NO-GO - Cutover Readiness"

PASS_NEXT_WORK = "narrow internal pilot steering under canonical current authority"
FAIL_NEXT_WORK = "rc-r cutover-readiness forensics under canonical current authority"

REFERENCE_DOCS = {
    "faz21": ROOT / "docs" / "FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
    "faz35": ROOT / "docs" / "FAZ35-RC-P-RELEASE-CONTROLS-PERIMETER-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
    "faz36": ROOT / "docs" / "FAZ36-RC-Q-RELEASE-CONTROLS-PERIMETER-REPAIR-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
    "faz37": ROOT / "docs" / "FAZ37-RC-Q-RELEASE-CONTROLS-PERIMETER-REPAIR-RECAPTURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
    "faz38": ROOT / "docs" / "FAZ38-RC-Q-REPAIR-TRUTH-INSTABILITY-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
    "faz39": ROOT / "docs" / "FAZ39-RC-Q-REPAIR-TRUTH-RECONCILIATION-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
    "faz40": ROOT / "docs" / "FAZ40-RC-Q-DISCARD-ARCHIVAL-CLOSURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
    "faz41": ROOT / "reports" / "FAZ41-POST-RC-Q-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
    "faz42": ROOT / "reports" / "FAZ42-RC-R-RELEASE-CONTROLS-PROCESS-ISOLATED-PERIMETER-ISOLATION-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
}

REFERENCE_MARKERS = {
    "faz21": [
        "PASS - Current Authority Canonicalized",
        "- `current_canonical_authority_adopted = true`",
        "- `surface_breach_from_history_reintroduced = false`",
    ],
    "faz35": [
        "PASS - RC-P Perimeter Root Cause Localized",
        "- preprojection_hash_mismatch_count = `174`",
        "- raw_answer_hash_mismatch_count = `174`",
        "- response_envelope_hash_mismatch_count = `109`",
    ],
    "faz36": [
        "NO-GO - RC-Q Frontier Repair Failed",
        "- must_close_release_controls_count = `10`",
        "- one_command_release_smoke_pass = `true`",
    ],
    "faz37": [
        "NO-GO - RC-Q Recapture Inconclusive",
        "- capture_a_vs_capture_b_mismatch_count = `6`",
        "- capture_a_vs_capture_b_mismatch_count = `3`",
    ],
    "faz38": [
        "PASS - RC-Q Repair Truth Instability Localized",
        "- union_instability_rowset_count = `6`",
        "- current_perimeter_truth_reference = `RC-P`",
    ],
    "faz39": [
        "PASS - RC-Q Repair Truth Reconciled Under Canonical Current Authority",
        "- current_instability_truth_adopted = `true`",
        "- historical_failed_repair_truth_reclassified = `true`",
        "- historical_inconclusive_recapture_truth_reclassified = `true`",
    ],
    "faz40": [
        "PASS - RC-Q Discard Archived Under Canonical Current Authority",
        "- archive_status = `closed`",
        "- tombstone_status = `active`",
    ],
    "faz41": [
        "PASS - Post-RC-Q Steering Re-Entered Under Canonical Current Authority",
        "- active_quality_reference = `RC-G`",
        "- active_control_pair = `RC-G vs RC-J`",
        "- active_forensic_reference = `RC-N`",
        "- current_perimeter_truth_reference = `RC-P`",
        "- next_candidate_id = `RC-R`",
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
        "- tokenizer_usage_total = `1.0`",
        "- retained_after_family_eval = `true`",
        "- retained_after_restart = `true`",
        "- retained_after_restore = `true`",
        "- next_official_work = `cutover-readiness closure reopen under canonical current authority`",
    ],
}


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def bool_text(value: bool) -> str:
    return "true" if value else "false"
