#!/usr/bin/env python3
"""Build Phase 20A rubric-aligned slot failure audit artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN_DIR = (
    REPO_ROOT / "reports/benchmark/runs/20260428T_phase19_R8G_full_benchmark_envparity"
)
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_20A_slot_failure_audit.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_20A_slot_failure_audit.md"

ROOT_CAUSES = {
    "slot_matrix_missing_required_slot",
    "slot_extractor_failed_to_fill_available_evidence",
    "slot_filled_but_not_synthesized",
    "synthesis_omitted_verified_slot",
    "evidence_missing_required_fact",
    "source_or_span_wrong",
    "rubric_requires_external_relation",
    "confidence_policy_too_strong",
    "scorer_proxy_mismatch",
    "unknown",
}

EXTERNAL_RELATION_SLOTS = {
    "hierarchy_or_conflict_rule",
    "transition_or_replacement_rule",
    "replacement_or_current_law_relation",
    "relation_to_law_if_question_asks",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def boolish(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "evet"}


def floatish(value: object, default: float = 0.0) -> float:
    try:
        return float(str(value or "").strip())
    except (TypeError, ValueError):
        return default


def intish(value: object, default: int = 0) -> int:
    try:
        return int(float(str(value or "").strip()))
    except (TypeError, ValueError):
        return default


def split_pipes(value: object) -> list[str]:
    return [part.strip() for part in re.split(r"\s*\|\s*", str(value or "")) if part.strip()]


def parse_answer_slots(value: str) -> list[dict[str, Any]]:
    if not value.strip():
        return []
    slots: list[dict[str, Any]] = []
    for part in re.split(r"(?<=\})\s+\|\s+(?=\{)", value):
        try:
            decoded = json.loads(part)
        except json.JSONDecodeError:
            continue
        if isinstance(decoded, dict):
            slots.append(decoded)
    return slots


def slot_names_by_status(row: dict[str, str], status: str) -> list[str]:
    out: list[str] = []
    for slot in parse_answer_slots(row.get("answer_slots", "")):
        if slot.get("fill_status") == status and slot.get("slot_name"):
            out.append(str(slot["slot_name"]))
    return sorted(set(out))


def has_external_relation_signal(row: dict[str, str]) -> bool:
    slot_fields = (
        "missing_fact_slots",
        "answer_slot_missing_reasons",
        "critical_answer_slots_missing",
        "evidence_slot_reentry_slots",
        "verified_answer_plan_missing_slots",
    )
    signals: set[str] = set()
    for field in slot_fields:
        raw = row.get(field, "")
        signals.update(split_pipes(raw))
        for part in split_pipes(raw):
            signals.add(part.split(":", 1)[0])
    if signals & EXTERNAL_RELATION_SLOTS:
        return True
    if boolish(row.get("relation_query_detected")):
        return True
    task = str(row.get("task_type") or row.get("required_slot_task_type") or "")
    return any(term in task for term in ("hierarchy", "conflict"))


def classify_root_cause(row: dict[str, str]) -> tuple[str, str]:
    flags = set(split_pipes(row.get("failure_classes", "")))
    missing_required = "missing_required_content_signal" in flags
    partial_grounding = "partial_grounding_only" in flags
    unsupported_confident = boolish(row.get("unsupported_confident_answer"))
    answer_slot_missing_count = intish(row.get("answer_slot_missing_count"))
    missing_fact_slots = split_pipes(row.get("missing_fact_slots", ""))
    answer_slot_missing_reasons = split_pipes(row.get("answer_slot_missing_reasons", ""))
    runtime_sufficient = row.get("rubric_aligned_completeness_class") == "rubric_sufficient"
    slot_coverage = floatish(row.get("answer_slot_coverage_score"))
    evidence_value_count = intish(row.get("evidence_required_slot_value_count"))
    source_wrong = bool(
        flags
        & {
            "wrong_family",
            "wrong_document",
            "wrong_article",
            "missing_gold_document_signal",
        }
    )
    source_wrong = source_wrong or floatish(row.get("family_match_score"), 1.0) <= 0.0
    source_wrong = source_wrong or floatish(row.get("document_match_score"), 1.0) <= 0.0
    source_wrong = source_wrong or boolish(row.get("article_lock_failed"))
    evidence_gap = bool(
        flags & {"insufficient_canonical_span_evidence"}
        or boolish(row.get("support_insufficient_for_specific_claim"))
        or not boolish(row.get("canonical_span_materialized"))
        or not boolish(row.get("selected_document_has_materialized_body_span"))
    )
    if unsupported_confident:
        return (
            "confidence_policy_too_strong",
            "unsupported confident answer flag is set",
        )
    if source_wrong:
        return (
            "source_or_span_wrong",
            "family/document/article alignment or article-lock signal failed",
        )
    if evidence_gap:
        return (
            "evidence_missing_required_fact",
            "selected evidence lacks canonical/materialized/supporting content",
        )
    if has_external_relation_signal(row) and (
        missing_required or partial_grounding or answer_slot_missing_count or missing_fact_slots
    ):
        return (
            "rubric_requires_external_relation",
            "relation/transition/hierarchy slot is implicated by runtime or scorer signals",
        )
    if any("evidence_span_not_mapped" in reason for reason in answer_slot_missing_reasons):
        return (
            "slot_extractor_failed_to_fill_available_evidence",
            "slot missing reason shows evidence span was not mapped into a required slot",
        )
    if evidence_value_count > 0 and (missing_fact_slots or answer_slot_missing_count):
        return (
            "slot_filled_but_not_synthesized",
            "evidence slot values exist but required runtime slots remain missing",
        )
    if (missing_required or partial_grounding) and runtime_sufficient and answer_slot_missing_count == 0:
        return (
            "slot_matrix_missing_required_slot",
            "runtime matrix marked the answer sufficient while private rubric still sees content/grounding gaps",
        )
    if (
        boolish(row.get("verified_answer_slot_synthesis_applied"))
        and (missing_required or partial_grounding)
        and slot_coverage >= 0.8
    ):
        return (
            "synthesis_omitted_verified_slot",
            "verified slot synthesis ran but private grounding/content signals still remain",
        )
    if not missing_required and not partial_grounding:
        return (
            "scorer_proxy_mismatch",
            "control row: no missing_required_content_signal or partial_grounding_only failure",
        )
    return "unknown", "no deterministic audit rule matched"


def build_audit_rows(
    scored_rows: list[dict[str, str]],
    answer_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    answers_by_qid = {row.get("qid", ""): row for row in answer_rows}
    audit_rows: list[dict[str, str]] = []
    for row in scored_rows:
        qid = row.get("qid", "")
        answer = answers_by_qid.get(qid, {})
        flags = set(split_pipes(row.get("failure_classes", "")))
        root_cause, detail = classify_root_cause(row)
        if root_cause not in ROOT_CAUSES:
            root_cause = "unknown"
        filled_slots = slot_names_by_status(row, "filled")
        missing_slots = sorted(
            set(
                split_pipes(row.get("missing_fact_slots", ""))
                + split_pipes(row.get("critical_answer_slots_missing", ""))
                + slot_names_by_status(row, "missing")
                + slot_names_by_status(row, "unsupported")
            )
        )
        audit_rows.append(
            {
                "qid": qid,
                "family": (
                    row.get("expected_family_prior")
                    or row.get("expected_source_family_canonical")
                    or row.get("source_family_canonical", "")
                ).lower(),
                "score": row.get("score_0_10_proxy", ""),
                "pass_fail": row.get("pass_fail_proxy", ""),
                "answer_mode": answer.get("answer_mode", ""),
                "confidence_0_100": answer.get("confidence_0_100", ""),
                "selected_source_family": answer.get("source_family_claimed")
                or row.get("source_family_canonical", ""),
                "selected_document_id": row.get("selected_document_id", ""),
                "selected_main_span_id": row.get("selected_main_span_id", ""),
                "required_slots": row.get("required_slot_runtime_slots")
                or row.get("must_have_fact_slots", ""),
                "filled_slots": " | ".join(filled_slots) if filled_slots else row.get("satisfied_fact_slots", ""),
                "missing_slots": " | ".join(missing_slots),
                "slot_missing_reasons": row.get("answer_slot_missing_reasons", ""),
                "answer_slot_coverage_score": row.get("answer_slot_coverage_score", ""),
                "minimum_answer_facts_present": row.get("minimum_answer_facts_present", ""),
                "runtime_rubric_sufficient": str(
                    row.get("rubric_aligned_completeness_class") == "rubric_sufficient"
                ),
                "missing_required_content_signal": str("missing_required_content_signal" in flags),
                "partial_grounding_only": str("partial_grounding_only" in flags),
                "unsupported_confident_claim": row.get("unsupported_confident_answer", ""),
                "root_cause": root_cause,
                "root_cause_detail": detail,
                "failure_classes": row.get("failure_classes", ""),
            }
        )
    return audit_rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(run_dir: Path, rows: list[dict[str, str]]) -> str:
    total = len(rows)
    root_counts = Counter(row["root_cause"] for row in rows)
    failure_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    root_by_family: Counter[tuple[str, str]] = Counter()
    for row in rows:
        family_counts[row["family"] or "unknown"] += 1
        root_by_family[(row["root_cause"], row["family"] or "unknown")] += 1
        for failure in split_pipes(row.get("failure_classes", "")):
            failure_counts[failure] += 1
    top_roots = root_counts.most_common(3)
    intervention = top_roots[0][0] if top_roots else "unknown"
    lines = [
        "# Phase 20A Slot Failure Audit",
        "",
        f"- source_run_dir: `{run_dir}`",
        f"- rows: {total}",
        f"- rows_with_root_cause: {sum(1 for row in rows if row['root_cause'])}/{total}",
        f"- missing_required_content_signal: {sum(1 for row in rows if row['missing_required_content_signal'] == 'True')}/{total}",
        f"- partial_grounding_only: {sum(1 for row in rows if row['partial_grounding_only'] == 'True')}/{total}",
        f"- unsupported_confident_claim: {sum(1 for row in rows if boolish(row['unsupported_confident_claim']))}/{total}",
        f"- runtime_rubric_sufficient: {sum(1 for row in rows if row['runtime_rubric_sufficient'] == 'True')}/{total}",
        "",
        "## Root Cause Distribution",
        "",
        "| Root cause | Count |",
        "|---|---:|",
    ]
    for key, count in root_counts.most_common():
        lines.append(f"| `{key}` | {count} |")
    lines.extend(
        [
            "",
            "## Top 3 Root Causes",
            "",
            "| Rank | Root cause | Count | First intervention implication |",
            "|---:|---|---:|---|",
        ]
    )
    implications = {
        "slot_matrix_missing_required_slot": (
            "Calibrate required slot matrix before changing answer text."
        ),
        "source_or_span_wrong": (
            "Out of Phase 20 scope unless a separate source/span mini-brief opens."
        ),
        "synthesis_omitted_verified_slot": (
            "Inspect verified slot synthesis visibility after slot matrix calibration."
        ),
        "slot_extractor_failed_to_fill_available_evidence": (
            "Improve evidence-to-slot filling while preserving evidence binding."
        ),
        "rubric_requires_external_relation": (
            "Add general relation/transition slots only where evidence supports them."
        ),
        "evidence_missing_required_fact": (
            "Do not synthesize unsupported facts; needs evidence/materialization work."
        ),
        "scorer_proxy_mismatch": (
            "Control/no-failure rows; no immediate runtime change from this audit."
        ),
        "slot_filled_but_not_synthesized": (
            "Reintegrate verified filled slots into final answer surface."
        ),
        "confidence_policy_too_strong": (
            "Tighten confidence policy, but only if unsupported confident appears."
        ),
        "unknown": "Manual inspection required before implementation.",
    }
    for idx, (key, count) in enumerate(top_roots, start=1):
        lines.append(f"| {idx} | `{key}` | {count} | {implications.get(key, '')} |")
    lines.extend(
        [
            "",
            "## Failure Classes",
            "",
            "| Failure class | Count |",
            "|---|---:|",
        ]
    )
    for key, count in failure_counts.most_common():
        lines.append(f"| `{key}` | {count} |")
    lines.extend(
        [
            "",
            "## Family Counts",
            "",
            "| Family | Count |",
            "|---|---:|",
        ]
    )
    for key, count in family_counts.most_common():
        lines.append(f"| `{key}` | {count} |")
    lines.extend(
        [
            "",
            "## Root Cause By Family",
            "",
            "| Root cause | Family | Count |",
            "|---|---|---:|",
        ]
    )
    for (root, family), count in root_by_family.most_common():
        lines.append(f"| `{root}` | `{family}` | {count} |")
    lines.extend(
        [
            "",
            "## First Intervention Area",
            "",
            f"Data-selected first intervention area: `{intervention}`.",
            "",
            "Rationale:",
        ]
    )
    if intervention == "slot_matrix_missing_required_slot":
        lines.extend(
            [
                "",
                "- The runtime slot matrix marks many rows structurally complete while the private/proxy scorer still flags missing required content and partial grounding.",
                "- Phase 20B should therefore calibrate required slots by task/family before changing evidence extraction or final answer synthesis.",
                "- This is still systemic: no QID-specific mapping is needed or allowed.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                f"- `{intervention}` is the highest-volume deterministic audit bucket.",
                "- Phase 20B/C should address it only through general task/family slot behavior.",
            ]
        )
    lines.extend(
        [
            "",
            "## Acceptance Check",
            "",
            "| Check | Result |",
            "|---|---:|",
            f"| 100 rows classified | {total == 100} |",
            f"| unknown root cause count | {root_counts.get('unknown', 0)} |",
            "| runtime behavior changed | False |",
            "| QID-specific rule used | False |",
            "",
            "## Row-Level Audit",
            "",
        ]
    )
    for row in rows:
        lines.append(
            "- "
            f"{row['qid']}: family={row['family']}, score={row['score']}, "
            f"pass={row['pass_fail']}, root_cause={row['root_cause']}, "
            f"missing_required={row['missing_required_content_signal']}, "
            f"partial_grounding={row['partial_grounding_only']}, "
            f"missing_slots={row['missing_slots'] or '-'}"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    scored_rows = read_csv(args.run_dir / "scored.csv")
    answer_rows = read_csv(args.run_dir / "candidate_answers.csv")
    audit_rows = build_audit_rows(scored_rows, answer_rows)
    write_csv(args.out_csv, audit_rows)
    args.out_md.write_text(build_markdown(args.run_dir, audit_rows), encoding="utf-8")
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
