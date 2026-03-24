#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz8_lib import load_json, question_index, stage_map, write_json


def build_gate(reference_report: dict[str, Any], candidate_report: dict[str, Any]) -> dict[str, Any]:
    reference_questions = question_index(reference_report)
    candidate_questions = question_index(candidate_report)

    mismatches: list[dict[str, Any]] = []
    for question_id in sorted(set(reference_questions) | set(candidate_questions)):
        reference_question = reference_questions.get(question_id)
        candidate_question = candidate_questions.get(question_id)
        if reference_question is None or candidate_question is None:
            mismatches.append(
                {
                    "question_id": question_id,
                    "kind": "missing_question",
                    "reference_present": reference_question is not None,
                    "candidate_present": candidate_question is not None,
                }
            )
            continue
        reference_hash = (stage_map(reference_question).get("raw_answer_object") or {}).get("hash")
        candidate_hash = (stage_map(candidate_question).get("raw_answer_object") or {}).get("hash")
        if reference_hash != candidate_hash:
            mismatches.append(
                {
                    "question_id": question_id,
                    "kind": "raw_answer_hash_mismatch",
                    "reference_hash": reference_hash,
                    "candidate_hash": candidate_hash,
                }
            )

    return {
        "eval_family": reference_report.get("report_meta", {}).get("eval_family"),
        "question_count": len(reference_questions),
        "preprojection_hash_mismatch_count": len(mismatches),
        "raw_answer_hash_mismatch": len(mismatches),
        "mismatches": mismatches,
    }


def render_markdown(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- eval_family = `{summary['eval_family']}`",
        f"- question_count = `{summary['question_count']}`",
        f"- preprojection_hash_mismatch_count = `{summary['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch = `{summary['raw_answer_hash_mismatch']}`",
        "",
        "## Mismatch Sample",
        "",
    ]
    if not summary["mismatches"]:
        lines.append("- mismatch yok")
    else:
        for item in summary["mismatches"][:20]:
            lines.append(f"- `{item['question_id']}` `{item['kind']}`")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ8 preprojection hash gate.")
    parser.add_argument("--reference-report", type=Path, required=True)
    parser.add_argument("--candidate-report", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--title", default="FAZ8 RC-I Preprojection Hash Gate")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = build_gate(load_json(args.reference_report), load_json(args.candidate_report))
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(summary, title=args.title), encoding="utf-8")
    if args.output_json:
        write_json(args.output_json, summary)
    return 0 if summary["preprojection_hash_mismatch_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
