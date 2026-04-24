#!/usr/bin/env python3
"""Build Phase 17C evidence-to-answer required-slot audit artifacts."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_17c_evidence_slot_audit.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_17c_evidence_slot_audit.md"


def boolish(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "evet"}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def index_by_qid(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {str(row.get("qid") or row.get("q_id") or ""): row for row in rows}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    answers = read_csv(args.run_dir / "candidate_answers.csv")
    scored = index_by_qid(read_csv(args.run_dir / "scored.csv"))
    rows: list[dict[str, str]] = []
    for answer in answers:
        qid = str(answer.get("qid") or answer.get("q_id") or "")
        scored_row = scored.get(qid, {})
        rows.append(
            {
                "qid": qid,
                "primary_type": answer.get("primary_type", ""),
                "task_type": answer.get("task_type", ""),
                "minimum_answer_facts_present": answer.get("minimum_answer_facts_present", ""),
                "rubric_aligned_completeness_class": answer.get("rubric_aligned_completeness_class", ""),
                "completeness_degrade_reason": answer.get("completeness_degrade_reason", ""),
                "required_fact_coverage_score": answer.get("required_fact_coverage_score", ""),
                "answer_slot_coverage_score": answer.get("answer_slot_coverage_score", ""),
                "evidence_slot_reentry_applied": answer.get("evidence_slot_reentry_applied", ""),
                "evidence_required_slot_value_count": answer.get("evidence_required_slot_value_count", ""),
                "evidence_slot_synthesis_applied": answer.get("evidence_slot_synthesis_applied", ""),
                "evidence_slot_synthesis_slots": answer.get("evidence_slot_synthesis_slots", ""),
                "evidence_slot_synthesis_reason": answer.get("evidence_slot_synthesis_reason", ""),
                "missing_fact_slots": answer.get("missing_fact_slots", ""),
                "failure_classes": scored_row.get("failure_classes", ""),
                "must_include_hit_count": scored_row.get("must_include_hit_count", ""),
                "must_include_total": scored_row.get("must_include_total", ""),
                "grounding_score": scored_row.get("grounding_score", ""),
                "score_0_10_proxy": scored_row.get("score_0_10_proxy", ""),
            }
        )

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", newline="", encoding="utf-8") as f:
        fieldnames = list(rows[0].keys()) if rows else [
            "qid",
            "primary_type",
            "task_type",
            "minimum_answer_facts_present",
            "rubric_aligned_completeness_class",
            "evidence_slot_synthesis_applied",
            "failure_classes",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    failure_counts: Counter[str] = Counter()
    for row in rows:
        for failure in str(row.get("failure_classes") or "").split(" | "):
            if failure.strip():
                failure_counts[failure.strip()] += 1
    synthesis_reason_counts = Counter(row["evidence_slot_synthesis_reason"] or "unknown" for row in rows)
    runtime_counts = Counter(row["rubric_aligned_completeness_class"] or "unknown" for row in rows)
    value_counts: list[float] = []
    for row in rows:
        raw = str(row.get("evidence_required_slot_value_count") or "").strip()
        if not raw:
            continue
        try:
            value_counts.append(float(raw))
        except ValueError:
            pass

    lines = [
        "# Phase 17C Evidence-To-Answer Required Slot Audit",
        "",
        f"- source_run_dir: `{args.run_dir}`",
        f"- rows: {len(rows)}",
        f"- minimum_answer_facts_present_count: {sum(1 for row in rows if boolish(row['minimum_answer_facts_present']))}/{len(rows)}",
        f"- evidence_slot_synthesis_count: {sum(1 for row in rows if boolish(row['evidence_slot_synthesis_applied']))}/{len(rows)}",
        f"- avg_evidence_required_slot_value_count: {round(sum(value_counts) / len(value_counts), 3) if value_counts else 0.0}",
        "",
        "## Runtime Completeness",
    ]
    for key, count in runtime_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Synthesis Reasons"])
    for key, count in synthesis_reason_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Failure Classes"])
    for key, count in failure_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Rows"])
    for row in rows:
        lines.append(
            "- "
            f"{row['qid']}: min_facts={row['minimum_answer_facts_present']}, "
            f"synthesis={row['evidence_slot_synthesis_applied']}:{row['evidence_slot_synthesis_slots'] or '-'}, "
            f"slot_values={row['evidence_required_slot_value_count']}, "
            f"must={row['must_include_hit_count']}/{row['must_include_total']}, "
            f"score={row['score_0_10_proxy']}, "
            f"failures={row['failure_classes'] or '-'}"
        )
    args.out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
