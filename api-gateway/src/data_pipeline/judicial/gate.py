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


def build_judicial_gate_skeleton() -> dict[str, Any]:
    active = os.getenv(JUDICIAL_GATE_ENABLED_ENV, "false").lower() in {"1", "true", "yes", "on"}
    return {
        "gate_name": "judicial_corpus_closure",
        "active": active,
        "enabled_env_var": JUDICIAL_GATE_ENABLED_ENV,
        "required_current_state": "inactive until corpus download and indexing are complete",
        "metrics": list(JUDICIAL_GATE_METRICS),
        "failure_modes": list(JUDICIAL_GATE_FAILURE_MODES),
        "runtime_path_requirement": (
            "Gate must call the same judicial retrieval and evidence path that runtime will use "
            "after judicial closure; no eval-only quality path."
        ),
    }
