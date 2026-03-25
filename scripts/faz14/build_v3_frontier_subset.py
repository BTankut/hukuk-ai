#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz14_lib import question_bank_rows  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ14 fixed v3 frontier subset.")
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--question-id", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    wanted = {item.strip() for item in args.question_id if item.strip()}
    subset = [row for row in question_bank_rows(args.questions) if str(row.get("question_id")) in wanted]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(subset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
