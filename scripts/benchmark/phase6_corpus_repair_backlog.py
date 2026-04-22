#!/usr/bin/env python3
"""Build Phase 6 owner-bound corpus repair and acquisition artifacts."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PHASE5_BACKLOG = REPO_ROOT / "reports/benchmark/phase_05_coverage_backlog.csv"
DEFAULT_OUT_OWNER_CSV = REPO_ROOT / "reports/benchmark/phase_06_owner_bound_backlog.csv"
DEFAULT_OUT_OWNER_MD = REPO_ROOT / "reports/benchmark/phase_06_owner_bound_backlog.md"
DEFAULT_OUT_ACQ_CSV = REPO_ROOT / "reports/benchmark/phase_06_corpus_acquisition_targets.csv"
DEFAULT_OUT_ACQ_MD = REPO_ROOT / "reports/benchmark/phase_06_corpus_acquisition_targets.md"


PRIORITY_ORDER = {
    "CB_KARAR": 1,
    "CB_YONETMELIK": 2,
    "KANUN": 3,
    "YONETMELIK": 4,
    "UY": 5,
    "TEBLIGLER": 6,
    "TUZUK": 7,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase5-backlog", type=Path, default=DEFAULT_PHASE5_BACKLOG)
    parser.add_argument(
        "--current-backlog",
        type=Path,
        help="Optional Phase 6 coverage backlog CSV. When present, resolution status is computed by qid.",
    )
    parser.add_argument("--out-owner-csv", type=Path, default=DEFAULT_OUT_OWNER_CSV)
    parser.add_argument("--out-owner-md", type=Path, default=DEFAULT_OUT_OWNER_MD)
    parser.add_argument("--out-acquisition-csv", type=Path, default=DEFAULT_OUT_ACQ_CSV)
    parser.add_argument("--out-acquisition-md", type=Path, default=DEFAULT_OUT_ACQ_MD)
    return parser.parse_args()


def read_csv(path: Path | None) -> list[dict[str, str]]:
    if path is None or not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def bool_text(value: Any) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes", "evet"}


def action_type(owner: str, status: str) -> str:
    if owner == "needs_corpus_acquisition":
        if status == "gold_document_not_retrieved":
            return "index_visibility_or_metadata_filter_repair"
        return "source_acquisition_or_reindex"
    if owner == "needs_metadata_backfill":
        return "structured_metadata_backfill"
    if owner == "needs_selector_logic":
        return "article_span_selector_hardening"
    return "no_action"


def priority_for(row: dict[str, str]) -> int:
    return PRIORITY_ORDER.get(str(row.get("expected_family") or ""), 99)


def resolution_status(previous: dict[str, str], current: dict[str, str] | None) -> str:
    owner = previous.get("primary_owner") or ""
    if not current:
        if owner == "needs_metadata_backfill":
            return "runtime_metadata_backfill_added_pending_rerun"
        if owner == "needs_selector_logic":
            return "selector_logic_updated_pending_rerun"
        if owner == "needs_corpus_acquisition":
            return "pending_acquisition_or_reindex"
        return "not_backlog"

    current_owner = current.get("primary_owner") or ""
    current_status = current.get("coverage_status") or ""
    if current_status == "not_backlog" or current_owner == "not_backlog":
        return "resolved"
    if owner == "needs_corpus_acquisition" and current_owner != "needs_corpus_acquisition":
        return "visibility_resolved_still_needs_downstream_work"
    if owner == "needs_metadata_backfill" and current_owner != "needs_metadata_backfill":
        return "metadata_owner_resolved_still_needs_downstream_work"
    if owner == "needs_selector_logic" and current_owner != "needs_selector_logic":
        return "selector_owner_changed"
    return "open"


def current_top_source(row: dict[str, str]) -> str:
    return (row.get("post_top_sources") or row.get("pre_top_sources") or "")[:240].rstrip()


def build_rows(phase5_rows: list[dict[str, str]], current_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    current_by_qid = {row.get("qid", ""): row for row in current_rows if row.get("qid")}
    rows: list[dict[str, str]] = []
    for row in phase5_rows:
        qid = row.get("qid", "")
        current = current_by_qid.get(qid)
        owner = row.get("primary_owner", "")
        status = row.get("coverage_status", "")
        rows.append(
            {
                "qid": qid,
                "owner": owner,
                "priority": str(priority_for(row)),
                "blocker_type": status,
                "expected_family": row.get("expected_family", ""),
                "expected_source": row.get("expected_source", ""),
                "current_top_retrieved_source": current_top_source(current or row),
                "phase5_top_retrieved_source": current_top_source(row),
                "action_type": action_type(owner, status),
                "phase5_resolution_status": row.get("pass_fail_proxy", ""),
                "resolution_status": resolution_status(row, current),
                "current_owner": (current or {}).get("primary_owner", ""),
                "current_coverage_status": (current or {}).get("coverage_status", ""),
                "current_score_0_10_proxy": (current or {}).get("score_0_10_proxy", ""),
                "current_pass_fail_proxy": (current or {}).get("pass_fail_proxy", ""),
                "resolver_blocker": row.get("resolver_blocker", ""),
                "retrieval_trace_id": (current or row).get("retrieval_trace_id", ""),
            }
        )
    return sorted(rows, key=lambda item: (int(item["priority"]), item["owner"], item["qid"]))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "qid",
        "owner",
        "priority",
        "blocker_type",
        "expected_family",
        "expected_source",
        "current_top_retrieved_source",
        "phase5_top_retrieved_source",
        "action_type",
        "phase5_resolution_status",
        "resolution_status",
        "current_owner",
        "current_coverage_status",
        "current_score_0_10_proxy",
        "current_pass_fail_proxy",
        "resolver_blocker",
        "retrieval_trace_id",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_owner_md(path: Path, rows: list[dict[str, str]], *, current_backlog: Path | None) -> None:
    owner_counts = Counter(row["owner"] for row in rows)
    status_counts = Counter(row["resolution_status"] for row in rows)
    action_counts = Counter(row["action_type"] for row in rows)
    lines = [
        "# Phase 6 Owner-Bound Backlog",
        "",
        f"- phase5_rows: {len(rows)}",
        f"- current_backlog: `{current_backlog}`" if current_backlog else "- current_backlog: `not_supplied`",
        "",
        "## Owner Counts",
    ]
    for owner, count in owner_counts.most_common():
        lines.append(f"- {owner}: {count}")
    lines.extend(["", "## Action Counts"])
    for action, count in action_counts.most_common():
        lines.append(f"- {action}: {count}")
    lines.extend(["", "## Resolution Status"])
    for status, count in status_counts.most_common():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Open Corpus Acquisition Items"])
    acq_rows = [row for row in rows if row["owner"] == "needs_corpus_acquisition"]
    for row in acq_rows[:30]:
        lines.append(
            f"- {row['qid']}: family={row['expected_family']}; action={row['action_type']}; "
            f"status={row['resolution_status']}; expected={row['expected_source'][:120]}"
        )
    if not acq_rows:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_acquisition_md(path: Path, rows: list[dict[str, str]]) -> None:
    acq_rows = [row for row in rows if row["owner"] == "needs_corpus_acquisition"]
    family_counts = Counter(row["expected_family"] for row in acq_rows)
    resolved_count = sum(1 for row in acq_rows if row["resolution_status"] in {"resolved", "visibility_resolved_still_needs_downstream_work"})
    lines = [
        "# Phase 6 Corpus Acquisition Targets",
        "",
        f"- acquisition_target_rows: {len(acq_rows)}",
        f"- acquisition_visibility_resolved_count: {resolved_count}",
        "",
        "## Family Counts",
    ]
    for family, count in family_counts.most_common():
        lines.append(f"- {family}: {count}")
    lines.extend(["", "## Targets"])
    for row in acq_rows:
        lines.append(
            f"- priority={row['priority']} qid={row['qid']} family={row['expected_family']} "
            f"status={row['resolution_status']} expected={row['expected_source'][:140]}"
        )
    if not acq_rows:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    phase5_rows = read_csv(args.phase5_backlog)
    current_rows = read_csv(args.current_backlog)
    rows = build_rows(phase5_rows, current_rows)
    acquisition_rows = [row for row in rows if row["owner"] == "needs_corpus_acquisition"]

    write_csv(args.out_owner_csv, rows)
    write_csv(args.out_acquisition_csv, acquisition_rows)
    write_owner_md(args.out_owner_md, rows, current_backlog=args.current_backlog)
    write_acquisition_md(args.out_acquisition_md, rows)
    print(f"Wrote {args.out_owner_csv}")
    print(f"Wrote {args.out_acquisition_csv}")
    print(f"Wrote {args.out_owner_md}")
    print(f"Wrote {args.out_acquisition_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
