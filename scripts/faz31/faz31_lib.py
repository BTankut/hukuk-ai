#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-03-29"
RESULT_REPORT_NAME = (
    "FAZ31-RC-O-REPAIR-TRUTH-RECONCILIATION-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-29.md"
)

PASS_DECISION = "PASS - RC-O Repair Truth Reconciled Under Canonical Current Authority"
FAIL_DECISION = "NO-GO - RC-O Repair Truth Reconciliation Incomplete"

PASS_NEXT_WORK = "rc-o discard archival closure under canonical current authority"
FAIL_NEXT_WORK = "rc-o repair truth reconciliation rerun under canonical current authority"

RECONCILIATION_STAGES = [
    "R0 = reference_pack_integrity",
    "R1 = canonical_current_authority_binding",
    "R2 = rc_o_repair_truth_contrast",
    "R3 = current_forensic_truth_adoption",
    "R4 = historical_repair_archive_reclassification",
    "R5 = downstream_repair_truth_consumer_binding",
]

ROOT_CAUSE_CLASSES = [
    "current_forensic_truth_adopted_and_historical_repair_truths_reclassified",
    "canonical_current_authority_repair_truth_contract_breach",
    "unexplained_rc_o_repair_truth_divergence",
]

REFERENCE_DOCS = {
    "faz21": ROOT / "docs" / "FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
    "faz24": ROOT / "docs" / "FAZ24-RC-M-DISCARD-ARCHIVAL-CLOSURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md",
    "faz25": ROOT / "docs" / "FAZ25-POST-RC-M-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md",
    "faz27": ROOT / "docs" / "FAZ27-RC-N-RELEASE-CONTROLS-BOUNDARY-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-28.md",
    "faz28": ROOT / "docs" / "FAZ28-RC-O-RELEASE-CONTROLS-BOUNDARY-REPAIR-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-28.md",
    "faz29": ROOT / "docs" / "FAZ29-RC-O-RELEASE-CONTROLS-BOUNDARY-REPAIR-RECAPTURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-29.md",
    "faz30": ROOT / "docs" / "FAZ30-RC-O-REPAIR-TRUTH-INSTABILITY-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-29.md",
}

REFERENCE_MARKERS = {
    "faz21": [
        "PASS - Current Authority Canonicalized",
        "current_canonical_authority_adopted = true",
        "downstream_consumer_binding_pass = true",
    ],
    "faz24": [
        "PASS - RC-M Discard Archived Under Canonical Current Authority",
        "candidate_status = `discard_archived`",
        "archive_status = `closed`",
    ],
    "faz25": [
        "PASS - Post-RC-M Steering Re-Entered Under Canonical Current Authority",
        "active_quality_reference = `RC-G`",
        "active_control_pair = `RC-G vs RC-J`",
    ],
    "faz27": [
        "PASS - RC-N Boundary Root Cause Localized",
        "reference_pack_integrity_pass = `true`",
        "frontier_total = `166`",
    ],
    "faz28": [
        "NO-GO - RC-O Boundary Repair Failed",
        "preprojection_hash_mismatch_count = `152`",
        "response_envelope_hash_mismatch_count = `92`",
    ],
    "faz29": [
        "NO-GO - RC-O Recapture Inconclusive",
        "runtime_error_count = `166`",
        "runtime_error_count = `24`",
    ],
    "faz30": [
        "PASS - RC-O Repair Truth Instability Localized",
        "matches_neither_new_stable_truth = `true`",
        "dominant_interaction_class = `boundary_pack_orchestration_runtime_mutation`",
    ],
}

FAZ21_CANONICALIZATION_JSON = (
    ROOT / "coordination" / "faz21-current-authority-canonicalization-reconciliation-2026-03-27.json"
)
FAZ21_CANONICAL_REFERENCE_JSON = (
    ROOT / "coordination" / "faz21-current-authority-canonical-reference-pack-2026-03-27.json"
)
FAZ27_REFERENCE_JSON = ROOT / "coordination" / "faz27-reference-pack-2026-03-28.json"
FAZ28_PHASE_PACKAGE_JSON = ROOT / "coordination" / "faz28-phase-package-2026-03-28.json"
FAZ29_PHASE_PACKAGE_JSON = ROOT / "coordination" / "faz29-phase-package-2026-03-29.json"
FAZ30_PHASE_PACKAGE_JSON = ROOT / "coordination" / "faz30-phase-package-2026-03-29.json"

MATERIALIZED_REFERENCE_JSON = ROOT / "coordination" / f"faz31-reference-pack-{DATE}.json"
PHASE_PACKAGE_JSON = ROOT / "coordination" / f"faz31-phase-package-{DATE}.json"


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def markdown_table(columns: list[tuple[str, str]], rows: list[dict[str, Any]]) -> list[str]:
    header = "| " + " | ".join(label for label, _ in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, sep]
    for row in rows:
        cells: list[str] = []
        for _, key in columns:
            value = row.get(key, "")
            if isinstance(value, bool):
                cells.append(bool_text(value))
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return lines
