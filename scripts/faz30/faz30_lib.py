#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-03-29"
COMPACT_DATE = "20260329"

sys.path.insert(0, str(ROOT / "scripts" / "faz29"))
sys.path.insert(0, str(ROOT / "scripts" / "faz27"))

from faz29_lib import (  # type: ignore
    bool_text,
    build_frontier_records as _build_boundary_frontier_records,
    build_repair_delta_records,
    build_spillover_guard_records as _build_spillover_guard_records,
    compare_question_maps,
    load_json,
    load_question_bank,
    load_text,
    markdown_table,
    merge_eval_question_maps,
    render_pair_report_markdown,
    stable_hash,
    summarize_pack_report,
    write_json,
    write_question_pack,
    write_text,
)
from faz27_lib import BIND_ORDER_ROWS, CONTROL_ROWS  # type: ignore


PASS_RESTORED = "PASS - RC-O Repair Truth Restored To FAZ28 Under Canonical Current Authority"
PASS_LOCALIZED = "PASS - RC-O Repair Truth Instability Localized"
FAIL_UNLOCALIZED = "NO-GO - RC-O Repair Truth Instability Unlocalized"

DECISION_TO_NEXT_WORK = {
    PASS_RESTORED: "rc-o repair truth reconciliation under canonical current authority",
    PASS_LOCALIZED: "rc-o repair truth reconciliation under canonical current authority",
    FAIL_UNLOCALIZED: "rc-o repair truth authority recapture under canonical current authority",
}

REFERENCE_FILES = {
    "faz21": ROOT / "docs" / "FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
    "faz24": ROOT / "docs" / "FAZ24-RC-M-DISCARD-ARCHIVAL-CLOSURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md",
    "faz25": ROOT / "docs" / "FAZ25-POST-RC-M-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md",
    "faz26": ROOT / "docs" / "FAZ26-RC-N-RELEASE-CONTROLS-CLOSURE-REOPEN-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-28.md",
    "faz27": ROOT / "docs" / "FAZ27-RC-N-RELEASE-CONTROLS-BOUNDARY-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-28.md",
    "faz28": ROOT / "docs" / "FAZ28-RC-O-RELEASE-CONTROLS-BOUNDARY-REPAIR-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-28.md",
    "faz29": ROOT / "docs" / "FAZ29-RC-O-RELEASE-CONTROLS-BOUNDARY-REPAIR-RECAPTURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-29.md",
}

REFERENCE_MARKERS = {
    "faz21": [
        "PASS - Current Authority Canonicalized",
        "`current_canonical_authority_adopted = true`",
    ],
    "faz24": [
        "PASS - RC-M Discard Archived Under Canonical Current Authority",
        "archive_status = `closed`",
    ],
    "faz25": [
        "PASS - Post-RC-M Steering Re-Entered Under Canonical Current Authority",
        "next_candidate_id = `RC-N`",
    ],
    "faz26": [
        "NO-GO - Release Controls",
        "preprojection_hash_mismatch_count = `166`",
        "raw_answer_hash_mismatch_count = `166`",
    ],
    "faz27": [
        "PASS - RC-N Boundary Root Cause Localized",
        "frontier_total = `166`",
    ],
    "faz28": [
        "NO-GO - RC-O Boundary Repair Failed",
        "faz1_50_mismatch_count = `14`",
        "tokenizer_backed_accounting_pass = `false`",
    ],
    "faz29": [
        "NO-GO - RC-O Recapture Inconclusive",
        "runtime_error_count = `166`",
        "runtime_error_count = `24`",
    ],
}

FAZ21_CANONICAL_REFERENCE_JSON = ROOT / "coordination" / "faz21-current-authority-canonical-reference-pack-2026-03-27.json"
FAZ21_CANONICAL_GATE_JSON = ROOT / "evaluation" / "reports" / "faz21-current-authority-canonicalization-gate-2026-03-27.json"
FAZ27_REFERENCE_PACK_JSON = ROOT / "coordination" / "faz27-reference-pack-2026-03-28.json"
FAZ28_PHASE_PACKAGE_JSON = ROOT / "coordination" / "faz28-phase-package-2026-03-28.json"
FAZ29_PHASE_PACKAGE_JSON = ROOT / "coordination" / "faz29-phase-package-2026-03-29.json"

FAZ26_RC_G_EVALS = {
    "faz1-50": ROOT / "evaluation" / "reports" / "eval_faz26_rc_g_faz1_50_20260328.json",
    "v2-95": ROOT / "evaluation" / "reports" / "eval_faz26_rc_g_v2_95_20260328.json",
    "v3-170": ROOT / "evaluation" / "reports" / "eval_faz26_rc_g_v3_170_20260328.json",
}

FAMILY_BANKS = {
    "faz1-50": ROOT / "configs" / "evaluation" / "test_questions.json",
    "v2-95": ROOT / "configs" / "evaluation" / "test_questions_v2_95.json",
    "v3-170": ROOT / "configs" / "evaluation" / "test_questions_v3_170.json",
}

BOUNDARY_PACK_PATH = ROOT / "configs" / "evaluation" / f"test_questions_faz30_boundary_frontier_166_{COMPACT_DATE}.json"
SPILLOVER_PACK_PATH = ROOT / "configs" / "evaluation" / f"test_questions_faz30_spillover_guard_24_{COMPACT_DATE}.json"
COMBINED_PACK_PATH = ROOT / "configs" / "evaluation" / f"test_questions_faz30_boundary_spillover_190_{COMPACT_DATE}.json"
MATERIALIZED_REFERENCE_JSON = ROOT / "coordination" / f"faz30-reference-pack-{DATE}.json"

STABLE_REPAIR_TRUTH_REF = {
    "boundary_frontier_count": 166,
    "faz1_50_mismatch_count": 14,
    "v2_95_mismatch_count": 52,
    "v3_170_mismatch_count": 86,
    "preprojection_hash_mismatch_count": 152,
    "raw_answer_hash_mismatch_count": 152,
    "response_envelope_hash_mismatch_count": 92,
    "first_break_stage_assigned_count": 152,
    "primary_reason_assigned_count": 152,
    "unexplained_count": 0,
    "spillover_guard_record_count": 24,
    "spillover_mismatch_count": 5,
    "spillover_preprojection_hash_mismatch_count": 5,
    "spillover_raw_answer_hash_mismatch_count": 5,
    "spillover_response_envelope_hash_mismatch_count": 2,
    "spillover_runtime_error_count": 0,
    "persisted_pii_redaction_pass": False,
    "tokenizer_backed_accounting_pass": False,
    "one_command_release_smoke_pass": False,
    "retained_after_family_eval": False,
    "retained_after_restart": False,
    "retained_after_restore": True,
    "answer_path_delta_reintroduced": True,
}

INCONCLUSIVE_RECAPTURE_REF = {
    "boundary_frontier_count": 166,
    "faz1_50_mismatch_count": 16,
    "v2_95_mismatch_count": 56,
    "v3_170_mismatch_count": 94,
    "preprojection_hash_mismatch_count": 0,
    "raw_answer_hash_mismatch_count": 0,
    "response_envelope_hash_mismatch_count": 0,
    "runtime_error_count": 166,
    "first_break_stage_assigned_count": 0,
    "primary_reason_assigned_count": 0,
    "unexplained_count": 166,
    "spillover_guard_record_count": 24,
    "spillover_mismatch_count": 24,
    "spillover_runtime_error_count": 24,
    "spillover_preprojection_hash_mismatch_count": 0,
    "spillover_raw_answer_hash_mismatch_count": 0,
    "spillover_response_envelope_hash_mismatch_count": 0,
    "persisted_pii_redaction_pass": False,
    "tokenizer_backed_accounting_pass": True,
    "api_versioning_pass": False,
    "one_command_release_smoke_pass": False,
    "retained_after_family_eval": False,
    "retained_after_restart": False,
    "retained_after_restore": True,
    "answer_path_delta_reintroduced": True,
}

RUNTIME_STAGE_LADDER = [
    "R0_bootstrap",
    "R1_auth_context_bind",
    "R2_audit_logger_bind",
    "R3_pii_redaction_bind",
    "R4_redis_session_bind",
    "R5_tokenizer_accounting_bind",
    "R6_api_versioning_bind",
    "R7_release_smoke_bind",
    "R8_request_envelope_materialization",
    "R9_model_request_dispatch",
    "R10_stream_open",
    "R11_stream_finalize",
    "R12_evaluator_write",
    "R13_retention_write",
]

PRIMARY_REASON_SET = [
    "multi_control_interaction_runtime_mutation",
    "persisted_pii_redaction_runtime_mutation",
    "tokenizer_accounting_runtime_mutation",
    "api_versioning_runtime_mutation",
    "one_command_release_smoke_runtime_mutation",
    "boundary_pack_orchestration_runtime_mutation",
    "evaluator_boundary_materialization_runtime_mutation",
    "retention_side_effect_runtime_mutation",
]

CONTROL_SET_ROWS = [
    {"control_set_id": "C0", "controls": ["mandatory auth", "immutable audit logging", "Redis session persistence"]},
    {
        "control_set_id": "C1",
        "controls": ["mandatory auth", "immutable audit logging", "Redis session persistence", "persisted PII redaction"],
    },
    {
        "control_set_id": "C2",
        "controls": ["mandatory auth", "immutable audit logging", "Redis session persistence", "tokenizer-backed accounting"],
    },
    {
        "control_set_id": "C3",
        "controls": ["mandatory auth", "immutable audit logging", "Redis session persistence", "API versioning"],
    },
    {
        "control_set_id": "C4",
        "controls": ["mandatory auth", "immutable audit logging", "Redis session persistence", "one-command release smoke"],
    },
    {
        "control_set_id": "C5",
        "controls": [
            "mandatory auth",
            "immutable audit logging",
            "Redis session persistence",
            "persisted PII redaction",
            "tokenizer-backed accounting",
        ],
    },
    {
        "control_set_id": "C6",
        "controls": [
            "mandatory auth",
            "immutable audit logging",
            "Redis session persistence",
            "persisted PII redaction",
            "one-command release smoke",
        ],
    },
    {
        "control_set_id": "C7",
        "controls": [
            "mandatory auth",
            "immutable audit logging",
            "Redis session persistence",
            "API versioning",
            "one-command release smoke",
        ],
    },
    {
        "control_set_id": "C8",
        "controls": [
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
        ],
    },
]


def build_boundary_frontier_records() -> list[dict[str, Any]]:
    return _build_boundary_frontier_records()


def build_spillover_guard_records() -> list[dict[str, Any]]:
    return _build_spillover_guard_records()


def build_combined_records() -> list[dict[str, Any]]:
    return [*build_boundary_frontier_records(), *build_spillover_guard_records()]


def build_truth_class_rows(current_forensic_truth: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "truth_class": "boundary_root_cause_truth",
            "record_count": 166,
            "mismatch_count": 166,
            "preprojection_hash_mismatch_count": 166,
            "raw_answer_hash_mismatch_count": 166,
            "response_envelope_hash_mismatch_count": 99,
            "runtime_error_count": 0,
            "first_break_stage_assigned_count": 166,
            "primary_reason_assigned_count": 166,
            "unexplained_count": 0,
        },
        {
            "truth_class": "stable_repair_truth",
            "record_count": STABLE_REPAIR_TRUTH_REF["boundary_frontier_count"],
            "mismatch_count": STABLE_REPAIR_TRUTH_REF["boundary_frontier_count"] - 14,
            "preprojection_hash_mismatch_count": STABLE_REPAIR_TRUTH_REF["preprojection_hash_mismatch_count"],
            "raw_answer_hash_mismatch_count": STABLE_REPAIR_TRUTH_REF["raw_answer_hash_mismatch_count"],
            "response_envelope_hash_mismatch_count": STABLE_REPAIR_TRUTH_REF["response_envelope_hash_mismatch_count"],
            "runtime_error_count": 0,
            "first_break_stage_assigned_count": STABLE_REPAIR_TRUTH_REF["first_break_stage_assigned_count"],
            "primary_reason_assigned_count": STABLE_REPAIR_TRUTH_REF["primary_reason_assigned_count"],
            "unexplained_count": STABLE_REPAIR_TRUTH_REF["unexplained_count"],
        },
        {
            "truth_class": "inconclusive_recapture_truth",
            "record_count": INCONCLUSIVE_RECAPTURE_REF["boundary_frontier_count"],
            "mismatch_count": INCONCLUSIVE_RECAPTURE_REF["boundary_frontier_count"],
            "preprojection_hash_mismatch_count": INCONCLUSIVE_RECAPTURE_REF["preprojection_hash_mismatch_count"],
            "raw_answer_hash_mismatch_count": INCONCLUSIVE_RECAPTURE_REF["raw_answer_hash_mismatch_count"],
            "response_envelope_hash_mismatch_count": INCONCLUSIVE_RECAPTURE_REF["response_envelope_hash_mismatch_count"],
            "runtime_error_count": INCONCLUSIVE_RECAPTURE_REF["runtime_error_count"],
            "first_break_stage_assigned_count": INCONCLUSIVE_RECAPTURE_REF["first_break_stage_assigned_count"],
            "primary_reason_assigned_count": INCONCLUSIVE_RECAPTURE_REF["primary_reason_assigned_count"],
            "unexplained_count": INCONCLUSIVE_RECAPTURE_REF["unexplained_count"],
        },
        {
            "truth_class": "current_forensic_truth",
            "record_count": int(current_forensic_truth["boundary"]["record_count"]),
            "mismatch_count": int(current_forensic_truth["boundary"]["mismatch_count"]),
            "preprojection_hash_mismatch_count": int(current_forensic_truth["boundary"]["preprojection_hash_mismatch_count"]),
            "raw_answer_hash_mismatch_count": int(current_forensic_truth["boundary"]["raw_answer_hash_mismatch_count"]),
            "response_envelope_hash_mismatch_count": int(current_forensic_truth["boundary"]["response_envelope_hash_mismatch_count"]),
            "runtime_error_count": int(current_forensic_truth["boundary"]["runtime_error_count"]),
            "first_break_stage_assigned_count": int(current_forensic_truth["boundary"]["first_break_stage_assigned_count"]),
            "primary_reason_assigned_count": int(current_forensic_truth["boundary"]["primary_reason_assigned_count"]),
            "unexplained_count": int(current_forensic_truth["boundary"]["unexplained_count"]),
        },
    ]
