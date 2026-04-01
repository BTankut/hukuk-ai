#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-03-31"
RESULT_REPORT_NAME = (
    "FAZ42-RC-R-RELEASE-CONTROLS-PROCESS-ISOLATED-PERIMETER-ISOLATION-GATE-UNDER-"
    f"CANONICAL-CURRENT-AUTHORITY-RAPORU-{DATE}.md"
)

PASS_DECISION = "PASS - RC-R Process-Isolated Perimeter Isolated"
FAIL_AUTH_DECISION = "NO-GO - Authority Or Upstream Equality Breach"
FAIL_PERIMETER_DECISION = "NO-GO - Release Controls Process-Isolated Perimeter"

PASS_NEXT_WORK = "cutover-readiness closure reopen under canonical current authority"
FAIL_NEXT_WORK = "rc-r release-controls process-isolated perimeter forensics under canonical current authority"

REFERENCE_DOCS = {
    "faz21": ROOT / "docs" / "FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
    "faz35": ROOT / "docs" / "FAZ35-RC-P-RELEASE-CONTROLS-PERIMETER-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
    "faz36": ROOT / "docs" / "FAZ36-RC-Q-RELEASE-CONTROLS-PERIMETER-REPAIR-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
    "faz37": ROOT / "docs" / "FAZ37-RC-Q-RELEASE-CONTROLS-PERIMETER-REPAIR-RECAPTURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
    "faz38": ROOT / "docs" / "FAZ38-RC-Q-REPAIR-TRUTH-INSTABILITY-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
    "faz39": ROOT / "docs" / "FAZ39-RC-Q-REPAIR-TRUTH-RECONCILIATION-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
    "faz40": ROOT / "docs" / "FAZ40-RC-Q-DISCARD-ARCHIVAL-CLOSURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
    "faz41": ROOT / "reports" / "FAZ41-POST-RC-Q-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
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
        "- must_close_release_controls_count = `10`",
        "- persisted_pii_redaction_pass = `false`",
        "- tokenizer_backed_accounting_pass = `false`",
        "- next_official_work = `rc-q release-controls perimeter repair gate under canonical current authority`",
    ],
    "faz36": [
        "NO-GO - RC-Q Frontier Repair Failed",
        "- candidate_id = `RC-Q`",
        "- current_perimeter_truth_reference = `RC-P`",
        "- must_close_release_controls_count = `10`",
        "- tokenizer_usage_total = `1.0`",
        "- retained_after_family_eval = `false`",
    ],
    "faz37": [
        "NO-GO - RC-Q Recapture Inconclusive",
        "- capture_a_vs_capture_b_mismatch_count = `6`",
        "- capture_a_vs_capture_b_mismatch_count = `3`",
        "- must_close_release_controls_count = `10`",
    ],
    "faz38": [
        "PASS - RC-Q Repair Truth Instability Localized",
        "- union_instability_rowset_count = `6`",
        "- active_quality_reference = `RC-G`",
        "- active_control_pair = `RC-G vs RC-J`",
        "- active_forensic_reference = `RC-N`",
        "- current_perimeter_truth_reference = `RC-P`",
        "- must_close_release_controls_count = `10`",
        "- tokenizer_usage_total = `1.0`",
    ],
    "faz39": [
        "PASS - RC-Q Repair Truth Reconciled Under Canonical Current Authority",
        "- current_perimeter_truth_reference_preserved = `true`",
        "- current_instability_truth_adopted = `true`",
        "- historical_failed_repair_truth_reclassified = `true`",
        "- historical_inconclusive_recapture_truth_reclassified = `true`",
    ],
    "faz40": [
        "PASS - RC-Q Discard Archived Under Canonical Current Authority",
        "- candidate_id = `RC-Q`",
        "- candidate_status = `discard_archived`",
        "- archive_status = `closed`",
        "- tombstone_status = `active`",
        "- next_official_work = `post-rc-q steering re-entry under canonical current authority`",
    ],
    "faz41": [
        "PASS - Post-RC-Q Steering Re-Entered Under Canonical Current Authority",
        "- active_quality_reference = `RC-G`",
        "- active_control_pair = `RC-G vs RC-J`",
        "- active_forensic_reference = `RC-N`",
        "- current_perimeter_truth_reference = `RC-P`",
        "- archived_candidate_set = `[RC-M, RC-O, RC-Q]`",
        "- next_candidate_id = `RC-R`",
        "- next_candidate_status = `reserved_not_built`",
        "- must_close_release_controls_count = `10`",
        "- next_official_work = `rc-r release-controls process-isolated perimeter isolation gate under canonical current authority`",
    ],
}


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def bool_text(value: bool) -> str:
    return "true" if value else "false"
