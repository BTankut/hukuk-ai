#!/usr/bin/env python3
"""Build the Phase 7A corpus acquisition tracker.

The tracker is deliberately source/query agnostic: it normalizes the Phase 6
coverage targets into an owner/action/resolution table that later visibility
probes can update. It must not contain question-specific routing fixes.
"""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = REPO_ROOT / "reports/benchmark/phase_06_corpus_acquisition_targets.csv"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_07_acquisition_tracker.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_07_acquisition_tracker.md"

FIELDNAMES = [
    "qid",
    "priority",
    "blocker_type",
    "expected_family",
    "expected_source_title",
    "expected_identifier",
    "expected_identifier_type",
    "expected_related_identifiers",
    "expected_related_sources",
    "availability_status",
    "owner",
    "action_type",
    "resolution_status",
    "next_action",
    "expected_source",
    "previous_resolution_status",
    "current_owner",
    "current_coverage_status",
    "current_top_retrieved_source",
    "retrieval_trace_id",
]

TR_ASCII_TRANS = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "â": "a",
        "î": "i",
        "û": "u",
    }
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_text(value: Any) -> str:
    text = clean(value).casefold().translate(TR_ASCII_TRANS)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def split_expected_source(value: str) -> tuple[str, list[str]]:
    parts = [clean(part) for part in str(value or "").split("|") if clean(part)]
    if not parts:
        return "", []
    return parts[0], parts[1:]


IDENTIFIER_PATTERNS: tuple[tuple[str, str], ...] = (
    ("karar_sayisi", r"karar\s+say[ıi]s[ıi]\s*:?\s*([0-9]+)"),
    ("karar_sayisi", r"\b([0-9]{1,5})\s+say[ıi]l[ıi]\s+karar"),
    ("kararname_no", r"kararname\s+numaras[ıi]\s*:?\s*([0-9]+)"),
    ("teblig_no", r"tebli[ğg]\s+no\s*:?\s*([0-9][0-9A-Za-z/\-.]*)"),
    ("teblig_no", r"tebli[ğg]\s*\(\s*([0-9]{4}-[0-9]+/[0-9]+)\s*\)"),
    ("genelge_no", r"\b([0-9]{4}/[0-9]+)\s+say[ıi]l[ıi].*genelge"),
    ("kanun_no", r"\b([0-9]{3,5})\s+say[ıi]l[ıi]"),
)


def extract_identifiers(value: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for identifier_type, pattern in IDENTIFIER_PATTERNS:
        for match in re.finditer(pattern, value or "", flags=re.IGNORECASE):
            identifier = clean(match.group(1))
            key = (identifier_type, identifier)
            if identifier and key not in seen:
                seen.add(key)
                found.append(key)

    if not found:
        for match in re.finditer(r"\b([0-9]{3,8})\b", value or ""):
            identifier = clean(match.group(1))
            key = ("source_no", identifier)
            if key not in seen:
                seen.add(key)
                found.append(key)
                break
    return found


def action_next_step(action_type: str) -> str:
    if action_type == "index_visibility_or_metadata_filter_repair":
        return "run_visibility_probe_then_repair_metadata_filter_or_selector"
    if action_type == "source_acquisition_or_reindex":
        return "run_visibility_probe_then_acquire_or_reindex_if_absent"
    return "run_visibility_probe_then_assign_owner"


def initial_resolution_status(row: dict[str, str]) -> str:
    status = clean(row.get("resolution_status"))
    if status in {"", "open", "pending_acquisition_or_reindex"}:
        return "pending_visibility_probe"
    return status


def build_tracker_row(row: dict[str, str]) -> dict[str, str]:
    expected_source = clean(row.get("expected_source"))
    title, related_sources = split_expected_source(expected_source)
    primary_identifiers = extract_identifiers(title)
    related_identifier_pairs: list[tuple[str, str]] = []
    for related_source in related_sources:
        related_identifier_pairs.extend(extract_identifiers(related_source))
    identifiers = primary_identifiers or extract_identifiers(expected_source)
    primary_type, primary_identifier = identifiers[0] if identifiers else ("", "")
    related_identifiers = [
        f"{identifier_type}:{identifier}"
        for identifier_type, identifier in related_identifier_pairs
        if (identifier_type, identifier) != (primary_type, primary_identifier)
    ]
    owner = clean(row.get("owner")) or clean(row.get("current_owner")) or "needs_corpus_acquisition"
    action_type = clean(row.get("action_type")) or "source_acquisition_or_reindex"
    return {
        "qid": clean(row.get("qid")),
        "priority": clean(row.get("priority")),
        "blocker_type": clean(row.get("blocker_type")),
        "expected_family": clean(row.get("expected_family")),
        "expected_source_title": title,
        "expected_identifier": primary_identifier,
        "expected_identifier_type": primary_type,
        "expected_related_identifiers": " | ".join(related_identifiers),
        "expected_related_sources": " | ".join(related_sources),
        "availability_status": "pending_visibility_probe",
        "owner": owner,
        "action_type": action_type,
        "resolution_status": initial_resolution_status(row),
        "next_action": action_next_step(action_type),
        "expected_source": expected_source,
        "previous_resolution_status": clean(row.get("resolution_status")),
        "current_owner": clean(row.get("current_owner")),
        "current_coverage_status": clean(row.get("current_coverage_status")),
        "current_top_retrieved_source": clean(row.get("current_top_retrieved_source")),
        "retrieval_trace_id": clean(row.get("retrieval_trace_id")),
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, str]], *, input_path: Path) -> None:
    family_counts = Counter(row["expected_family"] or "unknown" for row in rows)
    action_counts = Counter(row["action_type"] or "unknown" for row in rows)
    status_counts = Counter(row["resolution_status"] or "unknown" for row in rows)
    missing_owner = [row["qid"] for row in rows if not row.get("owner")]
    missing_action = [row["qid"] for row in rows if not row.get("action_type")]
    lines = [
        "# Phase 7A Acquisition Tracker",
        "",
        f"- input: `{input_path}`",
        f"- tracker_rows: {len(rows)}",
        f"- missing_owner_rows: {len(missing_owner)}",
        f"- missing_action_rows: {len(missing_action)}",
        "",
        "## Family Counts",
    ]
    for family, count in family_counts.most_common():
        lines.append(f"- {family}: {count}")
    lines.extend(["", "## Action Counts"])
    for action, count in action_counts.most_common():
        lines.append(f"- {action}: {count}")
    lines.extend(["", "## Initial Resolution Status"])
    for status, count in status_counts.most_common():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Tracker Rows"])
    for row in rows:
        identifier = row["expected_identifier"] or "none"
        lines.append(
            f"- {row['qid']}: family={row['expected_family']}; identifier={identifier}; "
            f"action={row['action_type']}; status={row['resolution_status']}; "
            f"title={row['expected_source_title'][:120]}"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "- This file is a control table only; live Milvus/index visibility is measured by the Phase 7A probe artifact.",
            "- `pending_visibility_probe` means the item has not yet been proven available, absent, or retrieval-visible in the current serving collection.",
            "- Every open row must keep a non-empty owner, action type, and next action before Phase 7B work starts.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_tracker(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    tracker_rows = [build_tracker_row(row) for row in rows]
    return sorted(tracker_rows, key=lambda item: (int(item["priority"] or "99"), item["qid"]))


def main() -> int:
    args = parse_args()
    rows = build_tracker(read_csv(args.input))
    write_csv(args.out_csv, rows)
    write_markdown(args.out_md, rows, input_path=args.input)
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
