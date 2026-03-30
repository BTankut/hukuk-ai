#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-03-30"
RESULT_REPORT_NAME = (
    "FAZ33-POST-RC-O-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md"
)

PASS_DECISION = "PASS - Post-RC-O Steering Re-Entered Under Canonical Current Authority"
FAIL_DECISION = "FAIL - Post-RC-O Steering Baseline Not Materialized"

PASS_NEXT_WORK = "rc-p release-controls perimeter isolation gate under canonical current authority"
FAIL_NEXT_WORK = "post-rc-o steering remediation"

REFERENCE_DOCS = {
    "faz21": ROOT / "docs" / "FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
    "faz25": ROOT
    / "docs"
    / "FAZ25-POST-RC-M-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md",
    "faz26": ROOT
    / "docs"
    / "FAZ26-RC-N-RELEASE-CONTROLS-CLOSURE-REOPEN-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-28.md",
    "faz27": ROOT
    / "docs"
    / "FAZ27-RC-N-RELEASE-CONTROLS-BOUNDARY-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-28.md",
    "faz28": ROOT
    / "docs"
    / "FAZ28-RC-O-RELEASE-CONTROLS-BOUNDARY-REPAIR-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-28.md",
    "faz29": ROOT
    / "docs"
    / "FAZ29-RC-O-RELEASE-CONTROLS-BOUNDARY-REPAIR-RECAPTURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-29.md",
    "faz30": ROOT
    / "docs"
    / "FAZ30-RC-O-REPAIR-TRUTH-INSTABILITY-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-29.md",
    "faz31": ROOT
    / "docs"
    / "FAZ31-RC-O-REPAIR-TRUTH-RECONCILIATION-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-29.md",
    "faz32": ROOT
    / "docs"
    / "FAZ32-RC-O-DISCARD-ARCHIVAL-CLOSURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
}

REFERENCE_MARKERS = {
    "faz21": {
        "official_decision": "PASS - Current Authority Canonicalized",
        "current_canonical_authority_adopted": "`current_canonical_authority_adopted = true`",
        "surface_breach_history": "`surface_breach_from_history_reintroduced = false`",
    },
    "faz25": {
        "official_decision": "PASS - Post-RC-M Steering Re-Entered Under Canonical Current Authority",
        "active_quality_reference": "active_quality_reference = `RC-G`",
        "active_control_pair": "active_control_pair = `RC-G vs RC-J`",
        "next_official_work": "rc-n release-controls closure reopen under canonical current authority",
    },
    "faz26": {
        "official_decision": "NO-GO - Release Controls",
        "preprojection_mismatch": "preprojection_hash_mismatch_count = `166`",
        "raw_mismatch": "raw_answer_hash_mismatch_count = `166`",
        "surface_breach_history": "surface_breach_from_history_reintroduced = `false`",
    },
    "faz27": {
        "official_decision": "PASS - RC-N Boundary Root Cause Localized",
        "dominant_control": "dominant_control = `Redis session persistence`",
        "effective_control_set": "effective_control_set = `mandatory auth, immutable audit logging, Redis session persistence`",
        "root_cause_class": "root_cause_class = `multi_control_interaction_runtime_mutation`",
    },
    "faz28": {
        "official_decision": "NO-GO - RC-O Boundary Repair Failed",
        "preprojection_mismatch": "preprojection_hash_mismatch_count = `152`",
        "response_envelope_mismatch": "response_envelope_hash_mismatch_count = `92`",
        "runtime_error_zero": "runtime_error_count = `0`",
    },
    "faz29": {
        "official_decision": "NO-GO - RC-O Recapture Inconclusive",
        "runtime_error_count": "runtime_error_count = `166`",
        "unexplained_count": "unexplained_count = `166`",
    },
    "faz30": {
        "official_decision": "PASS - RC-O Repair Truth Instability Localized",
        "current_forensic_truth": "current_forensic_truth = `record_count:166 mismatch_count:152 preprojection:152 raw:152 response_envelope:86 runtime_error:0 first_break:152 primary_reason:152 unexplained:0`",
        "dominant_interaction_class": "dominant_interaction_class = `boundary_pack_orchestration_runtime_mutation`",
        "spillover_runtime_zero": "spillover_runtime_error_count = `0`",
    },
    "faz31": {
        "official_decision": "PASS - RC-O Repair Truth Reconciled Under Canonical Current Authority",
        "current_forensic_truth_adopted": "current_forensic_truth_adopted = `true`",
        "historical_stable_repair_truth_reclassified": "historical_stable_repair_truth_reclassified = `true`",
        "historical_inconclusive_recapture_truth_reclassified": "historical_inconclusive_recapture_truth_reclassified = `true`",
        "comparison_order": "repair_truth_comparison_order = `current_forensic_truth -> historical_repair_archive`",
    },
    "faz32": {
        "official_decision": "PASS - RC-O Discard Archived Under Canonical Current Authority",
        "candidate_status": "candidate_status = `discard_archived`",
        "archive_status": "archive_status = `closed`",
        "next_official_work": "post-rc-o steering re-entry under canonical current authority",
    },
}

PERIMETER_RULES = {
    "mandatory_auth_placement": "transport_gateway_only",
    "mandatory_auth_model_visible_mutation_allowed": False,
    "mandatory_auth_prompt_path_access_allowed": False,
    "mandatory_auth_session_object_injection_allowed": False,
    "mandatory_auth_only_immutable_identity_token_allowed": True,
    "immutable_audit_logging_placement": "frozen_snapshot_async_outbox_only",
    "immutable_audit_logging_in_prompt_path_allowed": False,
    "immutable_audit_logging_in_context_assembly_allowed": False,
    "immutable_audit_logging_raw_answer_mutation_allowed": False,
    "immutable_audit_logging_response_envelope_mutation_allowed": False,
    "redis_session_persistence_placement": "sidecar_state_store_only",
    "redis_live_read_write_in_model_path_allowed": False,
    "redis_only_immutable_session_id_visible_to_model_path": True,
    "redis_context_mutation_allowed": False,
    "persisted_pii_redaction_placement": "persistence_and_audit_views_only",
    "persisted_pii_redaction_before_raw_answer_freeze_allowed": False,
    "persisted_pii_redaction_prompt_mutation_allowed": False,
    "persisted_pii_redaction_context_mutation_allowed": False,
    "tokenizer_backed_accounting_placement": "post_response_frozen_snapshot_only",
    "tokenizer_backed_accounting_feedback_into_runtime_allowed": False,
    "tokenizer_backed_accounting_prompt_path_access_allowed": False,
    "observability_alerting_placement": "passive_tap_only",
    "observability_alerting_runtime_mutation_allowed": False,
    "api_versioning_placement": "transport_boundary_only",
    "api_versioning_answer_path_mutation_allowed": False,
    "process_supervision_placement": "host_or_process_boundary_only",
    "process_supervision_answer_path_mutation_allowed": False,
    "backup_restore_placement": "offline_operational_boundary_only",
    "backup_restore_answer_path_mutation_allowed": False,
    "one_command_release_smoke_placement": "non_serving_harness_only",
    "one_command_release_smoke_runtime_attachment_allowed": False,
}

MUST_CLOSE_RELEASE_CONTROLS = [
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
]


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
