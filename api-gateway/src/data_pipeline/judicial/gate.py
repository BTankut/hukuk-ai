from __future__ import annotations

import os
from typing import Any


JUDICIAL_GATE_ENABLED_ENV = "JUDICIAL_CORPUS_GATE_ENABLED"

JUDICIAL_GATE_METRICS = (
    "judicial_retrieval_hit_at_20",
    "decision_citation_validity_rate",
    "court_metadata_accuracy",
    "esas_karar_number_accuracy",
    "decision_date_accuracy",
    "selected_judicial_evidence_recall",
    "unsupported_judicial_claim_rate",
    "mevzuat_judicial_confusion_rate",
)

JUDICIAL_GATE_FAILURE_MODES = (
    "invalid decision citation",
    "wrong court/chamber",
    "wrong date",
    "wrong case/decision number",
    "unsupported case-law claim",
    "treating judicial interpretation as legislation",
    "treating legislation as judicial precedent",
    "answering case-law questions without retrieved judicial evidence",
)

JUDICIAL_OFFLINE_GATE_CHECKS = (
    "raw_jsonl_validity",
    "manifest_required_fields_validity",
    "quarantine_reason_coverage",
    "duplicate_status_coverage",
    "citation_key_determinism",
    "canonical_decision_id_uniqueness",
    "chunk_key_uniqueness",
    "chunk_metadata_validity",
    "chunk_hash_validity",
    "exact_lookup_success_rate",
    "judicial_retrieval_hit_at_20",
    "decision_citation_validity_rate",
    "court_metadata_accuracy",
    "esas_karar_number_accuracy",
    "decision_date_accuracy",
    "selected_judicial_evidence_recall",
    "unsupported_judicial_claim_rate",
    "mevzuat_judicial_confusion_rate",
    "runtime_disabled",
)


def build_judicial_gate_skeleton() -> dict[str, Any]:
    active = os.getenv(JUDICIAL_GATE_ENABLED_ENV, "false").lower() in {"1", "true", "yes", "on"}
    return {
        "gate_name": "judicial_corpus_closure",
        "active": active,
        "enabled_env_var": JUDICIAL_GATE_ENABLED_ENV,
        "required_current_state": "inactive until corpus download and indexing are complete",
        "metrics": list(JUDICIAL_GATE_METRICS),
        "offline_checks": list(JUDICIAL_OFFLINE_GATE_CHECKS),
        "failure_modes": list(JUDICIAL_GATE_FAILURE_MODES),
        "activation_scope": "offline_validation_only",
        "runtime_path_requirement": (
            "Gate must call the same judicial retrieval and evidence path that runtime will use "
            "after judicial closure; no eval-only quality path."
        ),
    }


def evaluate_offline_judicial_gate_state(checks: dict[str, Any]) -> dict[str, Any]:
    active = os.getenv(JUDICIAL_GATE_ENABLED_ENV, "false").lower() in {"1", "true", "yes", "on"}
    missing = [check for check in JUDICIAL_OFFLINE_GATE_CHECKS if check not in checks]
    failing = [check for check, value in checks.items() if check in JUDICIAL_OFFLINE_GATE_CHECKS and not bool(value)]
    runtime_enabled = bool(checks.get("runtime_enabled", False))
    if runtime_enabled and "runtime_disabled" not in failing:
        failing.append("runtime_disabled")
    return {
        "gate_name": "judicial_corpus_closure",
        "active": active,
        "activation_scope": "offline_validation_only",
        "pass": not active and not missing and not failing and not runtime_enabled,
        "missing_checks": missing,
        "failing_checks": sorted(set(failing)),
        "runtime_enabled": runtime_enabled,
        "required_checks": list(JUDICIAL_OFFLINE_GATE_CHECKS),
    }
