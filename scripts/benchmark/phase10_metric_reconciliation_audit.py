#!/usr/bin/env python3
"""Build Phase 10 metric reconciliation artifacts for a benchmark run."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.benchmark.hukuk_ai_100_metric_registry import (
    aggregate_scored_metrics,
    read_csv,
    scored_row_metric_values,
    validate_metric_consistency,
    write_metric_registry_doc,
    write_validation_json,
)


DEFAULT_RUN_DIR = REPO_ROOT / "reports/benchmark/runs/20260422T153521Z_phase9_full"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_10_metric_reconciliation_audit.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_10_metric_reconciliation_audit.md"
DEFAULT_REGISTRY_MD = REPO_ROOT / "reports/benchmark/phase_10_metric_registry.md"
DEFAULT_VALIDATION_JSON = REPO_ROOT / "reports/benchmark/phase_10_metric_registry_validation.json"


AUDIT_FIELDS = [
    "qid",
    "score_0_10_proxy",
    "pass_fail_proxy",
    "expected_family",
    "claimed_family",
    "family_match_score",
    "document_match_score",
    "article_match_score",
    "trace_mechanism",
    "coverage_status",
    "right_document_wrong_article_or_span",
    "missing_required_content_signal",
    "partial_grounding_only",
    "required_fact_coverage_score",
    "minimum_answer_facts_present",
    "selected_article_equals_claimed_article",
    "rubric_completeness_class",
    "failure_classes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--coverage-csv", type=Path)
    parser.add_argument("--trace-csv", type=Path)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--registry-md", type=Path, default=DEFAULT_REGISTRY_MD)
    parser.add_argument("--validation-json", type=Path, default=DEFAULT_VALIDATION_JSON)
    parser.add_argument("--audit-limit", type=int, default=25)
    return parser.parse_args()


def _index(rows: list[dict[str, str]], key: str = "qid") -> dict[str, dict[str, str]]:
    return {row.get(key, ""): row for row in rows if row.get(key)}


def _read_optional(path: Path | None) -> list[dict[str, str]] | None:
    if path is None or not path.exists():
        return None
    return read_csv(path)


def build_audit_rows(
    *,
    scored_rows: list[dict[str, str]],
    coverage_rows: list[dict[str, str]] | None,
    trace_rows: list[dict[str, str]] | None,
    limit: int,
) -> list[dict[str, Any]]:
    coverage_by_qid = _index(coverage_rows or [])
    trace_by_qid = _index(trace_rows or [])
    enriched: list[dict[str, Any]] = []
    for row in scored_rows:
        qid = row.get("qid", "")
        metrics = scored_row_metric_values(row)
        enriched.append(
            {
                "qid": qid,
                "score_0_10_proxy": row.get("score_0_10_proxy", ""),
                "pass_fail_proxy": row.get("pass_fail_proxy", ""),
                "expected_family": row.get("expected_source_family_canonical", ""),
                "claimed_family": row.get("source_family_canonical", ""),
                "family_match_score": row.get("family_match_score", ""),
                "document_match_score": row.get("document_match_score", ""),
                "article_match_score": row.get("article_match_score", ""),
                "trace_mechanism": trace_by_qid.get(qid, {}).get("mechanism", ""),
                "coverage_status": coverage_by_qid.get(qid, {}).get("coverage_status", ""),
                "right_document_wrong_article_or_span": str(
                    metrics["right_document_wrong_article_or_span"]
                ).lower(),
                "missing_required_content_signal": str(metrics["missing_required_content_signal"]).lower(),
                "partial_grounding_only": str(metrics["partial_grounding_only"]).lower(),
                "required_fact_coverage_score": metrics["required_fact_coverage_score"],
                "minimum_answer_facts_present": str(metrics["minimum_answer_facts_present"]).lower(),
                "selected_article_equals_claimed_article": str(
                    metrics["selected_article_equals_claimed_article"]
                ).lower(),
                "rubric_completeness_class": metrics["rubric_completeness_class"],
                "failure_classes": row.get("failure_classes", ""),
            }
        )

    def sort_key(item: dict[str, Any]) -> tuple[int, float, str]:
        has_reconciled_metric = 0 if item["right_document_wrong_article_or_span"] == "true" else 1
        try:
            score = float(item.get("score_0_10_proxy") or 0)
        except ValueError:
            score = 0.0
        return has_reconciled_metric, score, item["qid"]

    return sorted(enriched, key=sort_key)[:limit]


def write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=AUDIT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(
    path: Path,
    *,
    run_dir: Path,
    summary: dict[str, Any],
    validation: dict[str, Any],
    audit_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# Phase 10 Metric Reconciliation Audit",
        "",
        f"- source_run_dir: `{run_dir}`",
        f"- validation_valid: {str(validation['valid']).lower()}",
        f"- mismatches: {len(validation['mismatches'])}",
        "",
        "## Canonical Metrics",
    ]
    for key, value in summary.items():
        if key == "rubric_completeness_class_counts":
            continue
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Rubric Completeness Classes"])
    for key, value in summary.get("rubric_completeness_class_counts", {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Artifact Consistency"])
    if validation["mismatches"]:
        for mismatch in validation["mismatches"]:
            lines.append(
                f"- {mismatch['artifact']} {mismatch['metric']}: expected={mismatch['expected']} actual={mismatch['actual']}"
            )
    else:
        lines.append("- all checked artifacts match canonical metric counts")
    lines.extend(["", "## 25-QID Row-Level Audit"])
    for row in audit_rows:
        lines.append(
            "- "
            f"{row['qid']}: score={row['score_0_10_proxy']}, pass={row['pass_fail_proxy']}, "
            f"coverage={row['coverage_status'] or 'n/a'}, trace={row['trace_mechanism'] or 'n/a'}, "
            f"right_doc_wrong_span={row['right_document_wrong_article_or_span']}, "
            f"completeness={row['rubric_completeness_class']}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    scored_rows = read_csv(args.run_dir / "scored.csv")
    coverage_rows = _read_optional(args.coverage_csv)
    trace_rows = _read_optional(args.trace_csv)
    validation = validate_metric_consistency(
        scored_rows=scored_rows,
        coverage_rows=coverage_rows,
        trace_rows=trace_rows,
    )
    summary = aggregate_scored_metrics(scored_rows)
    audit_rows = build_audit_rows(
        scored_rows=scored_rows,
        coverage_rows=coverage_rows,
        trace_rows=trace_rows,
        limit=args.audit_limit,
    )
    write_metric_registry_doc(args.registry_md)
    write_validation_json(args.validation_json, validation)
    write_csv_rows(args.out_csv, audit_rows)
    write_markdown(
        args.out_md,
        run_dir=args.run_dir,
        summary=summary,
        validation=validation,
        audit_rows=audit_rows,
    )
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")
    print(f"Wrote {args.registry_md}")
    print(f"Wrote {args.validation_json}")
    if not validation["valid"]:
        print(json.dumps(validation["mismatches"], ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
