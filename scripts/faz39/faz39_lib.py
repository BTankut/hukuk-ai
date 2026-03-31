#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-03-31"
RESULT_REPORT_NAME = (
    "FAZ39-RC-Q-REPAIR-TRUTH-RECONCILIATION-UNDER-"
    f"CANONICAL-CURRENT-AUTHORITY-RAPORU-{DATE}.md"
)

PASS_DECISION = "PASS - RC-Q Repair Truth Reconciled Under Canonical Current Authority"
FAIL_DECISION = "NO-GO - RC-Q Repair Truth Reconciliation Incomplete"

PASS_NEXT_WORK = "rc-q discard archival closure under canonical current authority"
FAIL_NEXT_WORK = "rc-q repair truth reconciliation rerun under canonical current authority"

RECONCILIATION_STAGES = [
    "R0 = reference_pack_integrity",
    "R1 = canonical_current_authority_binding",
    "R2 = current_perimeter_truth_preservation",
    "R3 = rc_q_repair_truth_contrast",
    "R4 = current_instability_truth_adoption",
    "R5 = historical_repair_archive_reclassification",
    "R6 = downstream_repair_truth_consumer_binding",
]

ROOT_CAUSE_CLASSES = [
    "current_instability_truth_adopted_and_historical_repair_truths_reclassified_with_current_perimeter_truth_preserved",
    "canonical_current_authority_repair_truth_contract_breach",
    "unexplained_rc_q_repair_truth_divergence",
]

REFERENCE_DOCS = {
    "faz21": ROOT / "docs" / "FAZ21-CURRENT-AUTHORITY-CANONICALIZATION-GATE-RAPORU-2026-03-27.md",
    "faz33": ROOT / "docs" / "FAZ33-POST-RC-O-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
    "faz35": ROOT / "docs" / "FAZ35-RC-P-RELEASE-CONTROLS-PERIMETER-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
    "faz36": ROOT / "docs" / "FAZ36-RC-Q-RELEASE-CONTROLS-PERIMETER-REPAIR-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md",
    "faz37": ROOT / "docs" / "FAZ37-RC-Q-RELEASE-CONTROLS-PERIMETER-REPAIR-RECAPTURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
    "faz38": ROOT / "docs" / "FAZ38-RC-Q-REPAIR-TRUTH-INSTABILITY-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-31.md",
}

REFERENCE_MARKERS = {
    "faz21": [
        "PASS - Current Authority Canonicalized",
        "current_canonical_authority_adopted = true",
        "downstream_consumer_binding_pass = true",
    ],
    "faz33": [
        "PASS - Post-RC-O Steering Re-Entered Under Canonical Current Authority",
        "active_quality_reference = `RC-G`",
        "active_control_pair = `RC-G vs RC-J`",
        "active_forensic_reference = `RC-N`",
    ],
    "faz35": [
        "PASS - RC-P Perimeter Root Cause Localized",
        "frontier_record_count = `174`",
        "response_envelope_subfrontier_record_count = `109`",
        "dominant_stage = `P11`",
    ],
    "faz36": [
        "NO-GO - RC-Q Frontier Repair Failed",
        "frontier_record_count = `174`",
        "preprojection_hash_mismatch_count = `151`",
        "response_envelope_hash_mismatch_count = `92`",
    ],
    "faz37": [
        "NO-GO - RC-Q Recapture Inconclusive",
        "frontier_record_count = `174`",
        "capture_a_vs_capture_b_mismatch_count = `6`",
        "capture_a_vs_capture_b_mismatch_count = `3`",
    ],
    "faz38": [
        "PASS - RC-Q Repair Truth Instability Localized",
        "union_instability_rowset_count = `6`",
        "primary_reason = `frontier_membership_delta`",
        "root_cause_class = `frontier_membership_instability`",
    ],
}

FAZ21_RECONCILIATION_MD = (
    ROOT / "coordination" / "faz21-current-authority-canonicalization-reconciliation-2026-03-27.md"
)
FAZ35_PHASE_PACKAGE_JSON = ROOT / "coordination" / "faz35-phase-package-2026-03-30.json"
FAZ34_RC_P_FULL_FAMILY_MD = (
    ROOT / "evaluation" / "reports" / "faz34-rc-g-vs-rc-p-model-visible-surface-parity-2026-03-30.md"
)
FAZ36_REPORT_MD = REFERENCE_DOCS["faz36"]
FAZ37_REPORT_MD = REFERENCE_DOCS["faz37"]
FAZ38_REPORT_MD = REFERENCE_DOCS["faz38"]
FAZ38_ROWSET_OVERLAP_MD = ROOT / "coordination" / f"faz38-rc-q-rowset-overlap-matrix-{DATE}.md"
FAZ38_ROOT_CAUSE_MD = ROOT / "evaluation" / "reports" / f"faz38-rc-q-instability-root-cause-summary-{DATE}.md"
FAZ38_TARGETED_MD = ROOT / "evaluation" / "reports" / f"faz38-rc-q-targeted-acceptance-stability-check-{DATE}.md"
FAZ38_RETENTION_MD = ROOT / "evaluation" / "reports" / f"faz38-rc-q-retention-stability-check-{DATE}.md"
FAZ38_LINEAGE_MD = ROOT / "coordination" / f"faz38-rc-q-truth-lineage-matrix-{DATE}.md"


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def markdown_table(columns: list[tuple[str, str]], rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(label for _, label in columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        rendered: list[str] = []
        for key, _ in columns:
            value = row.get(key, "")
            if isinstance(value, bool):
                rendered.append(bool_text(value))
            elif isinstance(value, list):
                rendered.append(", ".join(str(item) for item in value))
            elif isinstance(value, dict):
                rendered.append(json.dumps(value, ensure_ascii=False, sort_keys=True))
            else:
                rendered.append(str(value))
        lines.append("| " + " | ".join(rendered) + " |")
    return lines


def parse_markdown_kv_text(text: str) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("- "):
            continue
        rest = line[2:]
        pair = rest
        if rest.startswith("`"):
            closing = rest.find("`", 1)
            if closing == -1:
                continue
            pair = rest[1:closing]
        if " = " not in pair:
            continue
        key_part, value_part = pair.split(" = ", 1)
        key = key_part.strip().strip("`")
        raw_value = value_part.strip().strip("`")
        if raw_value == "true":
            payload[key] = True
        elif raw_value == "false":
            payload[key] = False
        elif re.fullmatch(r"-?\d+", raw_value):
            payload[key] = int(raw_value)
        elif re.fullmatch(r"-?\d+\.\d+", raw_value):
            payload[key] = float(raw_value)
        else:
            payload[key] = raw_value
    return payload


def parse_markdown_kv(path: Path) -> dict[str, Any]:
    return parse_markdown_kv_text(load_text(path))


def extract_section(path: Path, heading: str) -> str:
    text = load_text(path)
    marker = f"## {heading}"
    start = text.find(marker)
    if start == -1:
        raise RuntimeError(f"section not found: {heading}")
    rest = text[start + len(marker):]
    next_heading = rest.find("\n## ")
    body = rest[:next_heading] if next_heading != -1 else rest
    return body.strip()


def parse_section_kv(path: Path, heading: str) -> dict[str, Any]:
    return parse_markdown_kv_text(extract_section(path, heading))


def parse_markdown_table(path: Path, title: str) -> list[dict[str, str]]:
    text = load_text(path)
    marker = f"# {title}"
    start = text.find(marker)
    if start == -1:
        raise RuntimeError(f"table title not found: {title}")
    lines = [line.strip() for line in text[start:].splitlines()]
    table_lines = [line for line in lines if line.startswith("|")]
    if len(table_lines) < 3:
        return []
    headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for raw in table_lines[2:]:
        cells = [cell.strip() for cell in raw.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        rows.append(dict(zip(headers, cells)))
    return rows
