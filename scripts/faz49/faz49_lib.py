#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-04-01"
RESULT_REPORT_NAME = (
    "FAZ49-RC-R-KONTROLLU-GERCEK-DUNYA-DOGRULAMA-GATE-UNDER-CANONICAL-"
    f"CURRENT-AUTHORITY-RAPORU-{DATE}.md"
)

PASS_DECISION = "PASS - RC-R Controlled Real-World Validation Passed Under Canonical Current Authority"
FAIL_DECISION = "NO-GO - RC-R Controlled Real-World Validation Failed"

PASS_NEXT_WORK = "rc-s coverage readiness forensics under canonical current authority"
FAIL_NEXT_WORK = "rc-r real-world defect localization under canonical current authority"

REFERENCE_DOCS = {
    "faz21": ROOT / "docs" / "FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
    "faz45": ROOT / "reports" / "FAZ45-RC-R-NARROW-INTERNAL-PILOT-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md",
    "faz46": ROOT / "reports" / "FAZ46-RC-R-NARROW-INTERNAL-PILOT-EXECUTION-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md",
    "faz47": ROOT / "reports" / "FAZ47-POST-RC-R-NARROW-INTERNAL-PILOT-CLOSURE-VE-NEXT-TRACK-STEERING-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md",
    "faz48": ROOT / "reports" / "FAZ48-RC-S-COVERAGE-DATABASE-EXPANSION-READINESS-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md",
}

REFERENCE_MARKERS = {
    "faz21": [
        "PASS - Current Authority Canonicalized",
        "- `current_canonical_authority_adopted = true`",
        "- `downstream_consumer_binding_pass = true`",
        "- `surface_breach_stage_set = []`",
    ],
    "faz45": [
        "PASS - RC-R Narrow Internal Pilot Gate Opened Under Canonical Current Authority",
        "- pilot_candidate_id = `RC-R`",
        "- control_pair_authority_match = `true`",
        "- must_close_release_controls_pass = `true`",
        "- retained_after_restore = `true`",
    ],
    "faz46": [
        "PASS - RC-R Narrow Internal Pilot Executed Under Canonical Current Authority",
        "- selected_operator_count = `3`",
        "- planned_session_count = `9`",
        "- completed_session_count = `9`",
        "- session_success_count = `9`",
        "- incident_count = `0`",
    ],
    "faz47": [
        "PASS - Post-RC-R Narrow Internal Pilot Closed And Next Track Re-Entered Under Canonical Current Authority",
        "- active_quality_reference = `RC-G`",
        "- active_internal_pilot_base_candidate = `RC-R`",
        "- next_candidate_id = `RC-S`",
    ],
    "faz48": [
        "NO-GO - RC-S Coverage Readiness",
        "- accepted_release_controls_base_candidate = `RC-R`",
        "- missing_primary_source_manifest_count = `6`",
        "- missing_primary_raw_storage_location_count = `6`",
        "- next_official_work = `rc-s coverage readiness forensics under canonical current authority`",
    ],
}

BT_DIRECT_CLASS = "in_scope_supported_direct_citation"
BT_HEAVY_CLASS = "in_scope_supported_citation_heavy"
REFUSAL_CLASS = "refusal_expected_out_of_scope_or_unsupported"


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def bool_text(value: bool) -> str:
    return "true" if value else "false"
