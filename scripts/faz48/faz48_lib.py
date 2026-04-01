#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-04-01"
RESULT_REPORT_NAME = (
    "FAZ48-RC-S-COVERAGE-DATABASE-EXPANSION-READINESS-GATE-"
    f"UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-{DATE}.md"
)

PASS_DECISION = "PASS - RC-S Coverage Database Expansion Readiness Gate Passed Under Canonical Current Authority"
FAIL_DECISION = "NO-GO - RC-S Coverage Readiness"

PASS_NEXT_WORK = "rc-s narrow controlled primary-source expansion gate under canonical current authority"
FAIL_NEXT_WORK = "rc-s coverage readiness forensics under canonical current authority"

REFERENCE_DOCS = {
    "faz21": ROOT / "docs" / "FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
    "faz42": ROOT / "reports" / "FAZ42-RC-R-RELEASE-CONTROLS-PROCESS-ISOLATED-PERIMETER-ISOLATION-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
    "faz43": ROOT / "reports" / "FAZ43-RC-R-CUTOVER-READINESS-CLOSURE-REOPEN-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md",
    "faz44": ROOT / "reports" / "FAZ44-RC-R-NARROW-INTERNAL-PILOT-STEERING-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md",
    "faz45": ROOT / "reports" / "FAZ45-RC-R-NARROW-INTERNAL-PILOT-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md",
    "faz46": ROOT / "reports" / "FAZ46-RC-R-NARROW-INTERNAL-PILOT-EXECUTION-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md",
    "faz47": ROOT / "reports" / "FAZ47-POST-RC-R-NARROW-INTERNAL-PILOT-CLOSURE-VE-NEXT-TRACK-STEERING-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md",
    "faz1": ROOT / "docs" / "FAZ1-FINAL-RAPOR.md",
    "faz1_5": ROOT / "coordination" / "faz1_5-closure-matrix-2026-03-22.md",
}

REFERENCE_MARKERS = {
    "faz21": [
        "PASS - Current Authority Canonicalized",
        "- `current_canonical_authority_adopted = true`",
        "- `current_authority_contract_breach = false`",
        "- `surface_breach_stage_set = []`",
    ],
    "faz42": [
        "PASS - RC-R Process-Isolated Perimeter Isolated",
        "- control_pair_authority_match = `true`",
        "- faz1_50_mismatch_count = `0`",
        "- v2_95_mismatch_count = `0`",
        "- v3_170_mismatch_count = `0`",
        "- preprojection_hash_mismatch_count = `0`",
        "- raw_answer_hash_mismatch_count = `0`",
        "- response_envelope_hash_mismatch_count = `0`",
        "- must_close_release_controls_pass = `true`",
        "- retained_after_restore = `true`",
    ],
    "faz43": [
        "PASS - Cutover Readiness Closed Under Canonical Current Authority",
        "- active_cutover_readiness_candidate = `RC-R`",
        "- control_pair_authority_match = `true`",
        "- precutover_must_close_release_controls_pass = `true`",
        "- post_restore_retained_after_restore = `true`",
    ],
    "faz44": [
        "PASS - Narrow Internal Pilot Steering Re-Entered Under Canonical Current Authority",
        "- pilot_candidate_id = `RC-R`",
        "- active_cutover_readiness_candidate = `RC-R`",
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
        "- authority_breach_count = `0`",
        "- model_visible_delta_count = `0`",
        "- incident_count = `0`",
    ],
    "faz47": [
        "PASS - Post-RC-R Narrow Internal Pilot Closed And Next Track Re-Entered Under Canonical Current Authority",
        "- next_candidate_id = `RC-S`",
        "- next_candidate_status = `reserved_not_built`",
        "- next_phase_scope = `coverage_database_expansion_readiness_only_under_canonical_current_authority`",
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

PRIMARY_SOURCE_ROWS = [
    {"source_class": "TMK core corpus", "canonical_order": "1", "law_code": "TMK", "law_tokens": ["tmk"]},
    {"source_class": "TCK", "canonical_order": "2", "law_code": "TCK", "law_tokens": ["tck"]},
    {"source_class": "HMK", "canonical_order": "3", "law_code": "HMK", "law_tokens": ["hmk"]},
    {"source_class": "CMK", "canonical_order": "4", "law_code": "CMK", "law_tokens": ["cmk"]},
    {"source_class": "TTK", "canonical_order": "5", "law_code": "TTK", "law_tokens": ["ttk"]},
    {"source_class": "İK", "canonical_order": "6", "law_code": "İK", "law_tokens": ["ik", "iik", "ii̇k", "i̇i̇k"]},
]

EXCLUDED_SOURCE_ROWS = [
    {
        "source_class": "Yargıtay İçtihat Merkezi (YİM)",
        "canonical_order": "EXCLUDED",
        "inventory_manifest_present": False,
        "raw_storage_location_present": False,
        "canonical_source_locator_present": False,
        "usage_scope_allowed": False,
        "excluded": True,
        "notes": "excluded_source_class",
    },
    {
        "source_class": "customer/private documents",
        "canonical_order": "EXCLUDED",
        "inventory_manifest_present": False,
        "raw_storage_location_present": False,
        "canonical_source_locator_present": False,
        "usage_scope_allowed": False,
        "excluded": True,
        "notes": "excluded_source_class",
    },
    {
        "source_class": "external internet-derived ad hoc content",
        "canonical_order": "EXCLUDED",
        "inventory_manifest_present": False,
        "raw_storage_location_present": False,
        "canonical_source_locator_present": False,
        "usage_scope_allowed": False,
        "excluded": True,
        "notes": "excluded_source_class",
    },
]

MANDATORY_METADATA_FIELDS = [
    "kanun_no",
    "kanun_kisa_adi",
    "madde_no",
    "fikra_no",
    "source_id",
    "yururluk_baslangic",
    "yururluk_bitis",
    "mulga",
]

SCAN_ROOTS = [
    ROOT / "data",
    ROOT / "training",
    ROOT / "pilot",
    ROOT / "configs",
    ROOT / "api-gateway" / "src" / "data_pipeline",
]

LOCATOR_REFERENCE_FILES = [
    ROOT / "scripts" / "faz5" / "canonical_norm_lib.py",
    ROOT / "api-gateway" / "src" / "faz2a_hardening.py",
    ROOT / "api-gateway" / "src" / "routers" / "chat.py",
]


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def bool_text(value: bool) -> str:
    return "true" if value else "false"
