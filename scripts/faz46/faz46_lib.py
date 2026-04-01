#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-04-01"
RESULT_REPORT_NAME = (
    "FAZ46-RC-R-NARROW-INTERNAL-PILOT-EXECUTION-UNDER-CANONICAL-CURRENT-"
    f"AUTHORITY-RAPORU-{DATE}.md"
)

PASS_DECISION = "PASS - RC-R Narrow Internal Pilot Executed Under Canonical Current Authority"
ADMISSION_FAIL_DECISION = "NO-GO - Pilot Admission Not Ready"
INCIDENT_FAIL_DECISION = "NO-GO - RC-R Narrow Internal Pilot Incident Or Breach"

PASS_NEXT_WORK = "post-rc-r narrow internal pilot closure and next-track steering under canonical current authority"
ADMISSION_FAIL_NEXT_WORK = "rc-r narrow internal pilot admission completion under canonical current authority"
INCIDENT_FAIL_NEXT_WORK = "rc-r narrow internal pilot incident forensics under canonical current authority"

REFERENCE_DOCS = {
    "faz45": ROOT / "reports" / "FAZ45-RC-R-NARROW-INTERNAL-PILOT-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md",
    "faz44": ROOT / "reports" / "FAZ44-RC-R-NARROW-INTERNAL-PILOT-STEERING-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md",
    "faz43": ROOT / "reports" / "FAZ43-RC-R-CUTOVER-READINESS-CLOSURE-REOPEN-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md",
    "faz21": ROOT / "docs" / "FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
}

REFERENCE_MARKERS = {
    "faz45": [
        "PASS - RC-R Narrow Internal Pilot Gate Opened Under Canonical Current Authority",
        "- control_pair_authority_match = `true`",
        "- faz1_50_mismatch_count = `0`",
        "- v2_95_mismatch_count = `0`",
        "- v3_170_mismatch_count = `0`",
        "- must_close_release_controls_pass = `true`",
        "- retained_after_restore = `true`",
        "- next_official_work = `rc-r narrow internal pilot execution under canonical current authority`",
    ],
    "faz44": [
        "PASS - Narrow Internal Pilot Steering Re-Entered Under Canonical Current Authority",
        "- pilot_candidate_id = `RC-R`",
        "- pilot_scope = `narrow_internal_non_customer_controlled_observation_only`",
        "- pilot_user_class = `internal_named_allowlist_only`",
        "- pilot_start_authorized_in_this_phase = `false`",
    ],
    "faz43": [
        "PASS - Cutover Readiness Closed Under Canonical Current Authority",
        "- faz1_50_mismatch_count = `0`",
        "- v2_95_mismatch_count = `0`",
        "- v3_170_mismatch_count = `0`",
        "- preprojection_hash_mismatch_count = `0`",
        "- raw_answer_hash_mismatch_count = `0`",
        "- response_envelope_hash_mismatch_count = `0`",
    ],
    "faz21": [
        "PASS - Current Authority Canonicalized",
        "- `current_canonical_authority_adopted = true`",
        "- `surface_breach_from_history_reintroduced = false`",
    ],
}

SESSION_CLASSES = [
    "in_scope_supported_direct_citation",
    "in_scope_supported_citation_heavy",
    "refusal_expected_out_of_scope_or_unsupported",
]

PSEUDONYMOUS_ALLOWLIST = [
    "internal_operator_001",
    "internal_operator_002",
    "internal_operator_003",
]


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def bool_text(value: bool) -> str:
    return "true" if value else "false"
