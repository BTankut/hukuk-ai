#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from rc_f_offline_lib import (
    build_rc_f_report,
    current_git_commit,
    load_question_map,
    load_report_rows,
    replay_rc_f_row,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run offline RC-F family eval from RC-A answers + RC-D trace/context.")
    parser.add_argument("--questions", required=True, type=Path)
    parser.add_argument("--rc-a-report", required=True, type=Path)
    parser.add_argument("--rc-d-report", required=True, type=Path)
    parser.add_argument("--eval-family", required=True)
    parser.add_argument("--checkpoint-ref", required=True)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    question_map = load_question_map(args.questions)
    rc_a_rows = load_report_rows(args.rc_a_report)
    rc_d_rows = load_report_rows(args.rc_d_report)

    results = []
    for question_id, question in question_map.items():
        if question_id not in rc_a_rows or question_id not in rc_d_rows:
            raise RuntimeError(f"Missing row for {question_id} in RC-A or RC-D report")
        results.append(
            replay_rc_f_row(
                question=question,
                rc_a_row=rc_a_rows[question_id],
                rc_d_row=rc_d_rows[question_id],
            )
        )

    report = build_rc_f_report(
        results=results,
        questions_path=args.questions,
        eval_family=args.eval_family,
        checkpoint_ref=args.checkpoint_ref,
        git_commit=current_git_commit(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
