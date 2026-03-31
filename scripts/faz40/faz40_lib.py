#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-03-31"
RESULT_REPORT_NAME = (
    "FAZ40-RC-Q-DISCARD-ARCHIVAL-CLOSURE-UNDER-CANONICAL-CURRENT-AUTHORITY-"
    f"RAPORU-{DATE}.md"
)

PASS_DECISION = "PASS - RC-Q Discard Archived Under Canonical Current Authority"
FAIL_DECISION = "FAIL - RC-Q Archival Closure Contract Not Materialized"

PASS_NEXT_WORK = "post-rc-q steering re-entry under canonical current authority"
FAIL_NEXT_WORK = "rc-q archival closure remediation"

REFERENCE_DOCS = {
    "faz21": ROOT / "docs" / "FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
    "faz33": ROOT / "docs" / "FAZ33-POST-RC-O-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
    "faz35": ROOT / "docs" / "FAZ35-RC-P-RELEASE-CONTROLS-PERIMETER-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
    "faz36": ROOT / "docs" / "FAZ36-RC-Q-RELEASE-CONTROLS-PERIMETER-REPAIR-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
    "faz37": ROOT / "docs" / "FAZ37-RC-Q-RELEASE-CONTROLS-PERIMETER-REPAIR-RECAPTURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
    "faz38": ROOT / "docs" / "FAZ38-RC-Q-REPAIR-TRUTH-INSTABILITY-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
    "faz39": ROOT / "docs" / "FAZ39-RC-Q-REPAIR-TRUTH-RECONCILIATION-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
}

REFERENCE_MARKERS = {
    "faz21": [
        "PASS - Current Authority Canonicalized",
        "`current_canonical_authority_adopted = true`",
        "`downstream_consumer_binding_pass = true`",
    ],
    "faz33": [
        "PASS - Post-RC-O Steering Re-Entered Under Canonical Current Authority",
        "active_quality_reference = `RC-G`",
        "active_control_pair = `RC-G vs RC-J`",
        "allowed_diff_surface = `non_model_visible_release_controls_perimeter_only`",
        "answer_path_delta_allowed = `false`",
        "database_expansion_allowed = `false`",
        "cutover_authorized_in_next_phase = `false`",
        "pilot_authorized_in_next_phase = `false`",
    ],
    "faz35": [
        "PASS - RC-P Perimeter Root Cause Localized",
        "frontier_record_count = `174`",
        "response_envelope_subfrontier_record_count = `109`",
        "dominant_stage = `P11`",
        "dominant_reason = `preprojection_hash_drift`",
        "minimal_failing_control_set = `S1 = mandatory_auth + immutable_audit_logging + redis_session_persistence`",
        "dominant_interaction_class = `multi_control_interaction_runtime_mutation`",
    ],
    "faz36": [
        "NO-GO - RC-Q Frontier Repair Failed",
        "candidate_id = `RC-Q`",
        "preprojection_hash_mismatch_count = `151`",
        "raw_answer_hash_mismatch_count = `151`",
        "response_envelope_hash_mismatch_count = `84`",
        "response_envelope_hash_mismatch_count = `100`",
    ],
    "faz37": [
        "NO-GO - RC-Q Recapture Inconclusive",
        "frontier_record_count = `174`",
        "capture_a_vs_capture_b_mismatch_count = `6`",
        "capture_a_vs_capture_b_mismatch_count = `3`",
    ],
    "faz38": [
        "PASS - RC-Q Repair Truth Instability Localized",
        "union_instability_rowset_count = `6`",
        "primary_reason = `frontier_membership_delta`",
        "root_cause_class = `frontier_membership_instability`",
        "runtime_error_count = `0`",
        "unexplained_count = `0`",
    ],
    "faz39": [
        "PASS - RC-Q Repair Truth Reconciled Under Canonical Current Authority",
        "current_perimeter_truth_reference_preserved = `true`",
        "current_instability_truth_adopted = `true`",
        "historical_failed_repair_truth_reclassified = `true`",
        "historical_inconclusive_recapture_truth_reclassified = `true`",
        "repair_truth_comparison_order = `current_perimeter_truth_reference -> current_repair_truth -> historical_repair_archive`",
        "surface_breach_from_history_reintroduced = `false`",
    ],
}


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def bool_text(value: bool) -> str:
    return "true" if value else "false"
