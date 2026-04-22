#!/usr/bin/env python3
"""Build Phase 5 coverage backlog with primary owner classes."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import phase4_coverage_backlog as phase4


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN_DIR = REPO_ROOT / "reports/benchmark/runs/20260422T050311Z_phase5_corpus_identity_final"
DEFAULT_ANSWER_KEY = REPO_ROOT / "evaluation/private/hukuk_ai_100_answer_key_private.csv"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_05_coverage_backlog.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_05_coverage_backlog.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--answer-key", type=Path, default=DEFAULT_ANSWER_KEY)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def owner_for(row: dict[str, Any]) -> str:
    status = str(row.get("coverage_status") or "")
    needs_corpus = str(row.get("needs_corpus_acquisition") or "").lower() == "true"
    needs_metadata = str(row.get("needs_metadata_enrichment") or "").lower() == "true"
    if status == "not_backlog":
        return "not_backlog"
    if needs_corpus or status in {"not_retrieved_or_not_indexed", "gold_document_not_retrieved", "runtime_trace_gap"}:
        return "needs_corpus_acquisition"
    if needs_metadata or status in {"candidate_collision_or_metadata", "temporal_state_gap"}:
        return "needs_metadata_backfill"
    return "needs_selector_logic"


def build_rows(args: argparse.Namespace) -> list[dict[str, Any]]:
    rows = phase4.build_rows(SimpleNamespace(run_dir=args.run_dir, answer_key=args.answer_key))
    for row in rows:
        row["primary_owner"] = owner_for(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "qid",
        "primary_owner",
        "expected_family",
        "expected_source",
        "coverage_status",
        "resolver_blocker",
        "needs_corpus_acquisition",
        "needs_metadata_enrichment",
        "claimed_family",
        "claimed_source",
        "score_0_10_proxy",
        "pass_fail_proxy",
        "failure_classes",
        "pre_family_counts",
        "post_family_counts",
        "pre_top_sources",
        "post_top_sources",
        "gold_seen_pre",
        "gold_seen_post",
        "retrieval_trace_id",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, Any]], run_dir: Path) -> None:
    owner_counts = Counter(row["primary_owner"] for row in rows)
    status_counts = Counter(row["coverage_status"] for row in rows)
    failing_rows = [row for row in rows if row["failure_classes"]]
    lines = [
        "# Phase 5 Coverage Owner Backlog",
        "",
        f"- source_run_dir: `{run_dir}`",
        f"- rows_analyzed: {len(rows)}",
        f"- failing_rows: {len(failing_rows)}",
        "",
        "## Primary Owner Counts",
    ]
    for owner, count in owner_counts.most_common():
        lines.append(f"- {owner}: {count}")
    lines.extend(["", "## Coverage Status Counts"])
    for status, count in status_counts.most_common():
        lines.append(f"- {status}: {count}")

    for owner in ("needs_corpus_acquisition", "needs_metadata_backfill", "needs_selector_logic"):
        lines.extend(["", f"## {owner}"])
        owner_rows = [row for row in rows if row["primary_owner"] == owner]
        if not owner_rows:
            lines.append("- none")
            continue
        for row in owner_rows[:30]:
            post_top = str(row["post_top_sources"])[:160].rstrip()
            lines.append(
                f"- {row['qid']}: expected={row['expected_family']}; "
                f"status={row['coverage_status']}; blocker={row['resolver_blocker']}; "
                f"post_top={post_top}"
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "- `needs_corpus_acquisition` means expected family/document was not visible in retrieved candidates.",
            "- `needs_metadata_backfill` means source identity, issuer, year, or temporal fields are too weak for deterministic selection.",
            "- `needs_selector_logic` means the corpus is present enough, but document/article/span selection still needs logic hardening.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    rows = build_rows(args)
    write_csv(args.out_csv, rows)
    write_markdown(args.out_md, rows, args.run_dir)
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
