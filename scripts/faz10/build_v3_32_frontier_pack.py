#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz10_lib import load_json, write_json


def _question_id_sort_key(question_id: str) -> tuple[str, int]:
    prefix = "".join(ch for ch in question_id if not ch.isdigit())
    digits = "".join(ch for ch in question_id if ch.isdigit())
    return prefix, int(digits or "0")


def build_frontier_pack(
    *,
    gate_summary: dict[str, Any],
    question_bank: list[dict[str, Any]] | dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if isinstance(question_bank, dict):
        question_rows = question_bank.get("questions") or []
    else:
        question_rows = question_bank
    mismatch_question_ids = sorted(
        {
            str(item["question_id"])
            for item in gate_summary.get("mismatches", [])
            if isinstance(item, dict) and item.get("question_id")
        },
        key=_question_id_sort_key,
    )
    question_map = {
        str(item.get("id")): item
        for item in question_rows
        if isinstance(item, dict) and item.get("id")
    }
    frontier_questions = [question_map[qid] for qid in mismatch_question_ids if qid in question_map]
    summary = {
        "tracked_count": len(frontier_questions),
        "question_ids": mismatch_question_ids,
        "source_gate": {
            "reference_checkpoint_ref": gate_summary.get("reference_checkpoint_ref"),
            "candidate_checkpoint_ref": gate_summary.get("candidate_checkpoint_ref"),
            "preprojection_hash_mismatch_count": gate_summary.get("preprojection_hash_mismatch_count"),
            "raw_answer_hash_mismatch_count": gate_summary.get("raw_answer_hash_mismatch_count"),
            "parity_runtime_error_count": gate_summary.get("parity_runtime_error_count"),
        },
    }
    return frontier_questions, summary


def render_pack_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# FAZ10 V3-32 Frontier Pack",
        "",
        f"- tracked_count = `{summary['tracked_count']}`",
        f"- reference_checkpoint_ref = `{summary['source_gate']['reference_checkpoint_ref']}`",
        f"- candidate_checkpoint_ref = `{summary['source_gate']['candidate_checkpoint_ref']}`",
        f"- preprojection_hash_mismatch_count = `{summary['source_gate']['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{summary['source_gate']['raw_answer_hash_mismatch_count']}`",
        f"- parity_runtime_error_count = `{summary['source_gate']['parity_runtime_error_count']}`",
        "",
        "## Ordered Question IDs",
        "",
    ]
    for question_id in summary["question_ids"]:
        lines.append(f"- `{question_id}`")
    lines.append("")
    return "\n".join(lines)


def render_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# FAZ10 V3-32 Frontier Summary",
        "",
        f"- tracked_count = `{summary['tracked_count']}`",
        f"- ordered_question_count = `{len(summary['question_ids'])}`",
        f"- first_question_id = `{summary['question_ids'][0] if summary['question_ids'] else None}`",
        f"- last_question_id = `{summary['question_ids'][-1] if summary['question_ids'] else None}`",
        "",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ10 v3-32 frontier pack from FAZ9 v3-170 gate.")
    parser.add_argument("--gate-summary", type=Path, required=True)
    parser.add_argument("--question-bank", type=Path, required=True)
    parser.add_argument("--output-questions", type=Path, required=True)
    parser.add_argument("--output-pack-md", type=Path, required=True)
    parser.add_argument("--output-summary-md", type=Path, required=True)
    parser.add_argument("--output-summary-json", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    gate_summary = load_json(args.gate_summary)
    question_bank = json.loads(args.question_bank.read_text(encoding="utf-8"))
    frontier_questions, summary = build_frontier_pack(
        gate_summary=gate_summary,
        question_bank=question_bank,
    )
    args.output_questions.parent.mkdir(parents=True, exist_ok=True)
    args.output_questions.write_text(
        json.dumps(frontier_questions, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.output_pack_md.write_text(render_pack_markdown(summary), encoding="utf-8")
    args.output_summary_md.write_text(render_summary_markdown(summary), encoding="utf-8")
    if args.output_summary_json:
        write_json(args.output_summary_json, summary)
    return 0 if summary["tracked_count"] == 32 else 1


if __name__ == "__main__":
    raise SystemExit(main())
