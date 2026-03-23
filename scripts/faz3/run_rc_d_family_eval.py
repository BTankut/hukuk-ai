#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from rc_d_offline_lib import build_rc_d_report, load_question_map, load_report_rows, replay_rc_d_row


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run offline RC-D family eval from RC-A answers + RC-C trace/context.")
    parser.add_argument("--questions", required=True, type=Path)
    parser.add_argument("--rc-a-report", required=True, type=Path)
    parser.add_argument("--rc-c-report", required=True, type=Path)
    parser.add_argument("--eval-family", required=True)
    parser.add_argument("--checkpoint-ref", required=True)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    question_map = load_question_map(args.questions)
    rc_a_rows = load_report_rows(args.rc_a_report)
    rc_c_rows = load_report_rows(args.rc_c_report)

    results = []
    for question_id, question in question_map.items():
        if question_id not in rc_a_rows or question_id not in rc_c_rows:
            raise RuntimeError(f"Missing row for {question_id} in RC-A or RC-C report")
        result = replay_rc_d_row(
            question=question,
            rc_a_row=rc_a_rows[question_id],
            rc_c_row=rc_c_rows[question_id],
        )
        results.append(result)

    git_commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    report = build_rc_d_report(
        results=results,
        questions_path=args.questions,
        eval_family=args.eval_family,
        checkpoint_ref=args.checkpoint_ref,
        git_commit=git_commit,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
