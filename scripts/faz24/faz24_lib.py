#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PASS_DECISION = "PASS - RC-M Discard Archived Under Canonical Current Authority"
FAIL_DECISION = "FAIL - RC-M Archival Closure Contract Not Materialized"

PASS_NEXT_WORK = "post-rc-m steering re-entry under canonical current authority"
FAIL_NEXT_WORK = "rc-m archival closure remediation"

REFERENCE_FILES = {
    "faz16": "docs/FAZ16-REPLACEMENT-BUILD-SURFACE-ISOLATION-GATE-RAPORU-2026-03-25.md",
    "faz17": "docs/FAZ17-RC-M-AUTHORITATIVE-OUTPUT-PARITY-REOPEN-RAPORU-2026-03-25.md",
    "faz21": "docs/FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
    "faz22": "docs/FAZ22-RC-M-DISCARD-VE-OUTPUT-PARITY-SURFACE-FORENSICS-REOPEN-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md",
    "faz23": "docs/FAZ23-RC-M-AUTHORITATIVE-SUMMARY-TRUTH-RECONCILIATION-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md",
}

REFERENCE_MARKERS = {
    "faz16": {
        "official_decision": "PASS - Replacement Build Surface Isolated",
        "runtime_error_count": "runtime_error_count = 0",
        "control_pair_breach_in_f0_f12": "control_pair_breach_in_f0_f12 = false",
    },
    "faz17": {
        "official_decision": "NO-GO - RC-M Output Parity Surface Breach",
        "runtime_error_count": "runtime_error_count = 0",
        "authoritative_summary_mismatch_count": "authoritative_summary_mismatch_count = 1",
        "output_parity_surface_breach_count": "output_parity_surface_breach_count = 1",
        "localized_authorized_downstream_drift_count": "localized_authorized_downstream_drift_count = 0",
    },
    "faz21": {
        "official_decision": "PASS - Current Authority Canonicalized",
        "current_canonical_authority_adopted": "current_canonical_authority_adopted = true",
        "historical_archive_reclassified": "historical_archive_reclassified = true",
        "downstream_consumer_binding_pass": "downstream_consumer_binding_pass = true",
        "comparison_order": "authoritative comparison order = `current_canonical -> historical_archive`",
        "historical_summary_channel": "historical archive kanali = `diagnostic_only`",
        "surface_breach_from_history_reintroduced": "surface_breach_from_history_reintroduced = false",
    },
    "faz22": {
        "official_decision": "NO-GO - RC-M Surface Breach Non-Reproducible Under Canonical Current Authority",
        "authoritative_summary_mismatch_count": "authoritative_summary_mismatch_count = 0",
        "output_parity_surface_breach_count": "output_parity_surface_breach_count = 0",
        "frontier_candidate_count": "frontier_candidate_count = 0",
    },
    "faz23": {
        "official_decision": "PASS - RC-M Authoritative Summary Truth Reconciled Under Canonical Current Authority",
        "historical_summary_mismatch_count": "historical_summary_mismatch_count = `1`",
        "current_summary_mismatch_count": "current_summary_mismatch_count = `0`",
        "historical_surface_breach_count": "historical_surface_breach_count = `1`",
        "current_surface_breach_count": "current_surface_breach_count = `0`",
        "historical_frontier_candidate_count": "historical_frontier_candidate_count = `1`",
        "current_frontier_candidate_count": "current_frontier_candidate_count = `0`",
        "primary_reason": "historical_summary_truth_reclassified_to_archive_after_canonical_current_authority_adoption",
        "root_cause_class": "historical_summary_truth_reclassified_to_archive",
    },
}


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def bool_text(value: bool) -> str:
    return "true" if value else "false"
