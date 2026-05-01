#!/usr/bin/env python3
"""Guard Phase 22M-R2 intake until filled legal-review CSVs are present."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable, NamedTuple


class RequiredFile(NamedTuple):
    filename: str
    column_sets: tuple[set[str], ...]


REQUIRED_FILES = {
    "P0": RequiredFile(
        "filled_phase_22M_P0_manual_legal_review_packet.csv",
        (
            {
                "qid",
                "legal_reviewer_decision",
                "legal_reviewer_notes",
                "confirmed_expected_source",
                "confirmed_article_or_clause",
                "official_source_url",
                "effective_state_decision",
                "current_law_relation",
                "backfill_required",
            },
        ),
    ),
    "P1": RequiredFile(
        "filled_phase_22M_P1_manual_taxonomy_review_packet.csv",
        (
            {
                "qid",
                "legal_reviewer_decision",
                "legal_reviewer_notes",
                "expected_source_if_any",
                "taxonomy_decision",
                "runtime_relabel_allowed",
                "backfill_required",
            },
            {
                "qid",
                "legal_reviewer_decision",
                "legal_reviewer_notes",
                "confirmed_expected_source",
                "taxonomy_effective_action",
                "runtime_relabel_safe",
                "backfill_required",
            },
        ),
    ),
    "official_source": RequiredFile(
        "filled_phase_22M_official_source_acquisition_checklist.csv",
        (
            {
                "source_title",
                "official_url",
                "downloaded",
                "raw_file_path",
                "sha256",
                "parser_ready",
                "article_boundaries_detectable",
            },
        ),
    ),
}

BLOCKED_MESSAGE = "Phase 22F blocked: filled legal review CSVs missing"
PASS_MESSAGE = "Phase 22M-R2 intake may proceed"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def return_dir(root: Path) -> Path:
    return root / "reports" / "benchmark" / "legal_review_returns"


def missing_files(base_dir: Path) -> list[Path]:
    return [
        base_dir / required_file.filename
        for required_file in REQUIRED_FILES.values()
        if not (base_dir / required_file.filename).is_file()
    ]


def read_header(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return set()
    return {column.strip() for column in header if column.strip()}


def missing_columns(base_dir: Path) -> dict[str, list[str]]:
    failures: dict[str, list[str]] = {}
    for label, required_file in REQUIRED_FILES.items():
        path = base_dir / required_file.filename
        actual_columns = read_header(path)
        missing_by_schema = [
            sorted(required_columns - actual_columns)
            for required_columns in required_file.column_sets
        ]
        if any(not missing for missing in missing_by_schema):
            continue
        failures[label] = min(missing_by_schema, key=len)
    return failures


def format_missing(paths: Iterable[Path]) -> str:
    return "\n".join(f"- {path}" for path in paths)


def format_column_failures(failures: dict[str, list[str]]) -> str:
    lines: list[str] = ["Phase 22M return CSVs invalid: missing required columns"]
    for label, columns in failures.items():
        lines.append(f"- {label}: {', '.join(columns)}")
    return "\n".join(lines)


def check(root: Path) -> tuple[int, str]:
    base_dir = return_dir(root)
    missing = missing_files(base_dir)
    if missing:
        details = format_missing(missing)
        return 2, f"{BLOCKED_MESSAGE}\n{details}"

    column_failures = missing_columns(base_dir)
    if column_failures:
        return 3, format_column_failures(column_failures)

    return 0, PASS_MESSAGE


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check whether Phase 22M legal-review return CSVs are present and schema-valid."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=repo_root(),
        help="Repository root. Defaults to the root containing this script.",
    )
    args = parser.parse_args(argv)

    code, message = check(args.repo_root.resolve())
    print(message)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
