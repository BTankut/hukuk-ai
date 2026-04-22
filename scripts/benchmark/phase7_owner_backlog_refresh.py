#!/usr/bin/env python3
"""Refresh Phase 7 owner backlog with acquisition visibility probe results."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COVERAGE = REPO_ROOT / "reports/benchmark/phase_07_coverage_backlog.csv"
DEFAULT_VISIBILITY = REPO_ROOT / "reports/benchmark/phase_07_visibility_probe.csv"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_07_owner_backlog_refresh.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_07_owner_backlog_refresh.md"

OUTPUT_FIELDS = [
    "qid",
    "expected_family",
    "expected_source",
    "original_primary_owner",
    "phase7_primary_owner",
    "coverage_status",
    "phase7_visibility_status",
    "phase7_resolution_status",
    "phase7_next_action",
    "score_0_10_proxy",
    "pass_fail_proxy",
    "failure_classes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage-csv", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--visibility-csv", type=Path, default=DEFAULT_VISIBILITY)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def refreshed_owner(row: dict[str, str], visibility: dict[str, str] | None) -> tuple[str, str, str]:
    original_owner = row.get("primary_owner", "")
    if original_owner != "needs_corpus_acquisition" or not visibility:
        return original_owner, "", ""

    visibility_status = visibility.get("availability_status", "")
    resolution_status = visibility.get("resolution_status", "")
    if (
        visibility_status == "not_available_in_current_corpus"
        or resolution_status == "open_source_acquisition_required"
    ):
        return "needs_corpus_acquisition", resolution_status, visibility.get("next_action", "")

    if "catalog_backfill_required" in visibility_status or "catalog_backfill_required" in resolution_status:
        return "needs_metadata_backfill", resolution_status, "backfill_source_catalog_metadata_then_rerun"

    if visibility.get("phase7_blocker_type") == "visibility_resolved":
        return "needs_selector_logic", resolution_status, "query_visibility_or_selector_repair"

    return original_owner, resolution_status, visibility.get("next_action", "")


def build_refresh(
    coverage_rows: list[dict[str, str]],
    visibility_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    visibility_by_qid = {row.get("qid", ""): row for row in visibility_rows if row.get("qid")}
    refreshed: list[dict[str, str]] = []
    for row in coverage_rows:
        visibility = visibility_by_qid.get(row.get("qid", ""))
        owner, resolution, next_action = refreshed_owner(row, visibility)
        refreshed.append(
            {
                "qid": row.get("qid", ""),
                "expected_family": row.get("expected_family", ""),
                "expected_source": row.get("expected_source", ""),
                "original_primary_owner": row.get("primary_owner", ""),
                "phase7_primary_owner": owner,
                "coverage_status": row.get("coverage_status", ""),
                "phase7_visibility_status": visibility.get("availability_status", "") if visibility else "",
                "phase7_resolution_status": resolution,
                "phase7_next_action": next_action,
                "score_0_10_proxy": row.get("score_0_10_proxy", ""),
                "pass_fail_proxy": row.get("pass_fail_proxy", ""),
                "failure_classes": row.get("failure_classes", ""),
            }
        )
    return refreshed


def write_outputs(rows: list[dict[str, str]], out_csv: Path, out_md: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    owner_counts = Counter(row["phase7_primary_owner"] or "unknown" for row in rows)
    original_counts = Counter(row["original_primary_owner"] or "unknown" for row in rows)
    resolution_counts = Counter(row["phase7_resolution_status"] or "not_applicable" for row in rows)
    lines = [
        "# Phase 7 Owner Backlog Refresh",
        "",
        f"- rows: {len(rows)}",
        "",
        "## Refreshed Owner Counts",
    ]
    for owner, count in sorted(owner_counts.items()):
        lines.append(f"- {owner}: {count}")
    lines.extend(["", "## Original Owner Counts"])
    for owner, count in sorted(original_counts.items()):
        lines.append(f"- {owner}: {count}")
    lines.extend(["", "## Visibility Resolution Counts"])
    for status, count in sorted(resolution_counts.items()):
        lines.append(f"- {status}: {count}")
    open_rows = [row for row in rows if row["phase7_primary_owner"] == "needs_corpus_acquisition"]
    lines.extend(["", "## Open Corpus Acquisition Rows"])
    if not open_rows:
        lines.append("- none")
    for row in open_rows:
        lines.append(
            f"- {row['qid']}: status={row['phase7_resolution_status']}; "
            f"next={row['phase7_next_action']}; expected={row['expected_source']}"
        )
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    rows = build_refresh(read_csv(args.coverage_csv), read_csv(args.visibility_csv))
    write_outputs(rows, args.out_csv, args.out_md)
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
