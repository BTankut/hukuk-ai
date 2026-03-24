#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from faz8_lib import load_json, load_question_bank


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ8 frontier question subset.")
    parser.add_argument("--frontier-json", type=Path, required=True)
    parser.add_argument("--questions", type=Path, action="append", required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--family", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    frontier = load_json(args.frontier_json)
    bank: dict[str, dict] = {}
    for path in args.questions:
        bank.update(load_question_bank(path))

    rows = [row for row in frontier.get("rows", []) if row.get("family") == args.family]
    question_ids = []
    seen: set[str] = set()
    for row in rows:
        qid = row["question_id"]
        if qid in seen or qid not in bank:
            continue
        seen.add(qid)
        question_ids.append(bank[qid])

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(json.dumps(question_ids, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
