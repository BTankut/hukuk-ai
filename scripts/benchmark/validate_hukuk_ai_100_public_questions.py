#!/usr/bin/env python3
"""Validate the public hukuk-ai 100 question file without private answers."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_QUESTIONS = REPO_ROOT / "configs/evaluation/hukuk_ai_100_public_questions.csv"
REQUIRED_COLUMNS = [
    "q_id",
    "difficulty",
    "primary_type",
    "secondary_types",
    "task_type",
    "reference_date",
    "question",
    "expected_deliverable",
    "source_hint_urls",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--expected-count", type=int, default=100)
    parser.add_argument("--json-out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with args.questions.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        columns = reader.fieldnames or []
    qids = [row.get("q_id", "").strip() for row in rows]
    duplicate_qids = sorted(qid for qid, count in Counter(qids).items() if qid and count > 1)
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in columns]
    empty_qids = sum(1 for qid in qids if not qid)
    empty_questions = sum(1 for row in rows if not row.get("question", "").strip())
    summary = {
        "questions": str(args.questions),
        "expected_count": args.expected_count,
        "row_count": len(rows),
        "missing_columns": missing_columns,
        "duplicate_qids": duplicate_qids,
        "empty_qids": empty_qids,
        "empty_questions": empty_questions,
    }
    summary["status"] = (
        "pass"
        if len(rows) == args.expected_count
        and not missing_columns
        and not duplicate_qids
        and empty_qids == 0
        and empty_questions == 0
        else "fail"
    )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
