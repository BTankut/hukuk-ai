#!/usr/bin/env python3
"""Build Phase 10 rubric-aligned completeness calibration artifacts."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.benchmark.hukuk_ai_100_metric_registry import (
    read_csv,
    scored_row_metric_values,
    split_flags,
)


DEFAULT_RUN_DIR = REPO_ROOT / "reports/benchmark/runs/20260422T153521Z_phase9_full"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_10b_completeness_calibration.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_10b_completeness_calibration.md"


TASK_TYPE_MUST_HAVE_SLOTS: dict[str, tuple[str, ...]] = {
    "precise_retrieval": ("governing_source", "exact_source_identity", "article_or_span"),
    "temporal_validity": ("governing_source", "exact_source_identity", "temporal_validity"),
    "scenario_applicability": (
        "governing_source",
        "exact_source_identity",
        "scenario_applicability",
        "procedure_or_consequence",
    ),
    "hierarchy_conflict": (
        "governing_source",
        "exact_source_identity",
        "hierarchy_or_conflict_rule",
        "scenario_applicability",
    ),
    "document_selection": ("governing_source", "exact_source_identity", "document_selection_reason"),
    "compliance_checklist": (
        "governing_source",
        "article_or_span",
        "procedure_or_consequence",
        "exception_or_limitation",
    ),
    "exception_analysis": (
        "governing_source",
        "article_or_span",
        "exception_or_limitation",
        "scenario_applicability",
    ),
    "current_update": ("governing_source", "exact_source_identity", "temporal_validity"),
}


OUTPUT_FIELDS = [
    "qid",
    "task_type",
    "score_0_10_proxy",
    "pass_fail_proxy",
    "rubric_completeness_class",
    "must_have_fact_slots",
    "missing_required_content_signal",
    "partial_grounding_only",
    "required_fact_coverage_score",
    "minimum_answer_facts_present",
    "completeness_degrade_reason",
    "failure_classes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def must_have_slots(task_type: str) -> tuple[str, ...]:
    normalized = (task_type or "").strip()
    return TASK_TYPE_MUST_HAVE_SLOTS.get(
        normalized,
        ("governing_source", "exact_source_identity", "result_or_holding"),
    )


def build_rows(scored_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in scored_rows:
        metrics = scored_row_metric_values(row)
        rows.append(
            {
                "qid": row.get("qid", ""),
                "task_type": row.get("task_type", ""),
                "score_0_10_proxy": row.get("score_0_10_proxy", ""),
                "pass_fail_proxy": row.get("pass_fail_proxy", ""),
                "rubric_completeness_class": metrics["rubric_completeness_class"],
                "must_have_fact_slots": " | ".join(must_have_slots(row.get("task_type", ""))),
                "missing_required_content_signal": str(
                    metrics["missing_required_content_signal"]
                ).lower(),
                "partial_grounding_only": str(metrics["partial_grounding_only"]).lower(),
                "required_fact_coverage_score": metrics["required_fact_coverage_score"],
                "minimum_answer_facts_present": str(metrics["minimum_answer_facts_present"]).lower(),
                "completeness_degrade_reason": row.get("completeness_degrade_reason", ""),
                "failure_classes": row.get("failure_classes", ""),
            }
        )
    return rows


def write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, Any]], run_dir: Path) -> None:
    class_counts = Counter(row["rubric_completeness_class"] for row in rows)
    task_counts: dict[str, Counter[str]] = defaultdict(Counter)
    failure_counts: Counter[str] = Counter()
    for row in rows:
        task_counts[row["task_type"] or "UNKNOWN"][row["rubric_completeness_class"]] += 1
        failure_counts.update(split_flags(row.get("failure_classes", "")))

    lines = [
        "# Phase 10B Completeness Calibration",
        "",
        f"- source_run_dir: `{run_dir}`",
        f"- rows_analyzed: {len(rows)}",
        "",
        "## Task-Type Must-Have Fact Slots",
    ]
    for task_type, slots in sorted(TASK_TYPE_MUST_HAVE_SLOTS.items()):
        lines.append(f"- {task_type}: {' | '.join(slots)}")
    lines.extend(["", "## Rubric-Aligned Completeness Classes"])
    for key, count in class_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Private-Rubric Failure Signals"])
    for key in ("missing_required_content_signal", "partial_grounding_only"):
        lines.append(f"- {key}: {failure_counts.get(key, 0)}")
    lines.extend(["", "## Completeness Class by Task Type"])
    for task_type, counts in sorted(task_counts.items()):
        rendered = ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
        lines.append(f"- {task_type}: {rendered}")
    lines.extend(["", "## Calibration Interpretation"])
    lines.append(
        "- `structurally_full_but_legally_misaligned` means runtime structural completeness passed, "
        "but private-rubric required content or grounding still failed."
    )
    lines.append(
        "- `rubric_sufficient` is the only class that should map to `complete_enough` after runtime gating."
    )
    lines.append(
        "- The calibration is generic by task type and fact slot; it does not encode any benchmark QID-specific rule."
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    rows = build_rows(read_csv(args.run_dir / "scored.csv"))
    write_csv_rows(args.out_csv, rows)
    write_markdown(args.out_md, rows, args.run_dir)
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
