#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-03-30"
RESULT_REPORT_NAME = (
    "FAZ32-RC-O-DISCARD-ARCHIVAL-CLOSURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md"
)

PASS_DECISION = "PASS - RC-O Discard Archived Under Canonical Current Authority"
FAIL_DECISION = "FAIL - RC-O Archival Closure Contract Not Materialized"

PASS_NEXT_WORK = "post-rc-o steering re-entry under canonical current authority"
FAIL_NEXT_WORK = "rc-o archival closure remediation"

REFERENCE_DOCS = {
    "faz21": ROOT / "docs" / "FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
    "faz25": ROOT
    / "docs"
    / "FAZ25-POST-RC-M-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md",
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
}

REFERENCE_MARKERS = {
    "faz21": [
        "PASS - Current Authority Canonicalized",
        "`current_canonical_authority_adopted = true`",
        "`downstream_consumer_binding_pass = true`",
    ],
    "faz25": [
        "PASS - Post-RC-M Steering Re-Entered Under Canonical Current Authority",
        "active_quality_reference = `RC-G`",
        "active_control_pair = `RC-G vs RC-J`",
    ],
    "faz27": [
        "PASS - RC-N Boundary Root Cause Localized",
        "preprojection_hash_mismatch_count = `166`",
        "raw_answer_hash_mismatch_count = `166`",
        "response_envelope_hash_mismatch_count = `99`",
        "unexplained_count = `0`",
    ],
    "faz28": [
        "NO-GO - RC-O Boundary Repair Failed",
        "preprojection_hash_mismatch_count = `152`",
        "raw_answer_hash_mismatch_count = `152`",
        "response_envelope_hash_mismatch_count = `92`",
        "unexplained_count = `0`",
    ],
    "faz29": [
        "NO-GO - RC-O Recapture Inconclusive",
        "preprojection_hash_mismatch_count = `0`",
        "raw_answer_hash_mismatch_count = `0`",
        "runtime_error_count = `166`",
        "unexplained_count = `166`",
    ],
    "faz30": [
        "PASS - RC-O Repair Truth Instability Localized",
        "current_forensic_truth = `record_count:166 mismatch_count:152 preprojection:152 raw:152 response_envelope:86 runtime_error:0 first_break:152 primary_reason:152 unexplained:0`",
        "dominant_interaction_class = `boundary_pack_orchestration_runtime_mutation`",
        "spillover_runtime_error_count = `0`",
    ],
    "faz31": [
        "PASS - RC-O Repair Truth Reconciled Under Canonical Current Authority",
        "current_forensic_truth_adopted = `true`",
        "historical_stable_repair_truth_reclassified = `true`",
        "historical_inconclusive_recapture_truth_reclassified = `true`",
        "repair_truth_comparison_order = `current_forensic_truth -> historical_repair_archive`",
        "surface_breach_from_history_reintroduced = `false`",
    ],
}

PHASE_PACKAGE_JSON = ROOT / "coordination" / f"faz32-phase-package-{DATE}.json"


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
