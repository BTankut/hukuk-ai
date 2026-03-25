#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from faz11_lib import load_json, question_bank_rows, runtime_error_row


def build_subset(*, report_path: Path, questions_path: Path) -> list[dict]:
    report = load_json(report_path)
    report_questions = {
        str(row["question_id"]): row
        for row in report.get("per_question", [])
        if isinstance(row, dict) and row.get("question_id")
    }
    subset: list[dict] = []
    for row in question_bank_rows(questions_path):
        question_id = str(row["question_id"])
        report_row = report_questions.get(question_id)
        if report_row is None:
            continue
        runtime_error, _ = runtime_error_row(report_row)
        if runtime_error:
            subset.append(row)
    return subset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ11 error-only rerun subset.")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    subset = build_subset(report_path=args.report, questions_path=args.questions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    import json

    args.output.write_text(json.dumps(subset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
