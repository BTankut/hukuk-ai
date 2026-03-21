#!/usr/bin/env python3
"""Export the active Alpaca-style SFT package into ShareGPT conversations JSONL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = REPO_ROOT / "data/finetune/sft/final_train.jsonl"
DEFAULT_OUTPUT = REPO_ROOT / "data/finetune/sft/final_train_sharegpt.jsonl"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export Alpaca-style SFT JSONL into ShareGPT conversations JSONL.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Source Alpaca-style JSONL file.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Target ShareGPT JSONL file.")
    parser.add_argument("--dry-run", action="store_true", help="Parse and count only; do not write output.")
    return parser


def combine_human_prompt(record: dict) -> str:
    parts: list[str] = []
    instruction = str(record.get("instruction", "")).strip()
    user_input = str(record.get("input", "")).strip()
    if instruction:
        parts.append(instruction)
    if user_input:
        parts.append(user_input)
    return "\n\n".join(parts).strip()


def convert_record(record: dict) -> dict:
    human_turn = combine_human_prompt(record)
    assistant_turn = str(record.get("output", "")).strip()

    if not human_turn:
        raise ValueError("missing human turn")
    if not assistant_turn:
        raise ValueError("missing assistant turn")

    payload = {
        "conversations": [
            {"from": "human", "value": human_turn},
            {"from": "gpt", "value": assistant_turn},
        ]
    }

    if isinstance(record.get("_meta"), dict) and record["_meta"]:
        payload["_meta"] = record["_meta"]

    return payload


def load_records(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def export_records(input_path: Path, output_path: Path, *, dry_run: bool = False) -> tuple[int, int]:
    if not input_path.exists():
        raise SystemExit(f"[FAIL] Input file bulunamadi: {input_path}")

    records = load_records(input_path)
    converted: list[dict] = []
    skipped = 0

    for record in records:
        try:
            converted.append(convert_record(record))
        except ValueError:
            skipped += 1

    if not dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            for record in converted:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    return len(converted), skipped


def main() -> int:
    args = build_parser().parse_args()
    exported, skipped = export_records(args.input, args.output, dry_run=args.dry_run)

    print(f"[INFO] input={args.input}")
    if not args.dry_run:
        print(f"[INFO] output={args.output}")
    print(f"[INFO] exported_rows={exported}")
    print(f"[INFO] skipped_rows={skipped}")
    print("[RESULT] SHAREGPT_EXPORT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
