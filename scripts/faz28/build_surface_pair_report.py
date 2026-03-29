#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz28_lib import (  # type: ignore
    compare_question_maps,
    load_json,
    merge_eval_question_maps,
    render_pair_report_markdown,
    write_json,
    write_text,
)


def _load_reference_by_family(paths: list[Path]) -> dict[str, dict[str, dict]]:
    reference_by_family: dict[str, dict[str, dict]] = {}
    for path in paths:
        payload = load_json(path)
        report_meta = payload.get("report_meta") or {}
        family_id = str(report_meta.get("eval_family") or "")
        if not family_id:
            raise ValueError(f"reference report is missing eval_family: {path}")
        reference_by_family[family_id] = merge_eval_question_maps([path])
    return reference_by_family


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ28 surface pair report.")
    parser.add_argument("--family-id", required=True)
    parser.add_argument("--reference-report", type=Path, action="append", required=True)
    parser.add_argument("--candidate-report", type=Path, required=True)
    parser.add_argument("--question-pack", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--title", required=True)
    args = parser.parse_args()

    candidate_payload = load_json(args.candidate_report)
    candidate_questions = {
        str(row["question_id"]): row
        for row in candidate_payload.get("per_question", [])
        if isinstance(row, dict) and row.get("question_id")
    }

    question_ids = None
    reference_questions = merge_eval_question_maps(args.reference_report)
    if args.question_pack:
        reference_by_family = _load_reference_by_family(args.reference_report)
        pack = load_json(args.question_pack)
        rows = pack.get("questions") if isinstance(pack, dict) else pack
        if isinstance(rows, list):
            question_ids = []
            reference_questions = {}
            for row in rows:
                if not isinstance(row, dict) or not row.get("id"):
                    continue
                composite_id = str(row["id"])
                family_id = str(row.get("authority_family_id") or row.get("family_id") or "")
                source_question_id = str(row.get("source_question_id") or composite_id)
                if not family_id:
                    raise ValueError(f"question pack row is missing authority_family_id: {composite_id}")
                if family_id not in reference_by_family:
                    raise KeyError(f"missing reference family {family_id} for {composite_id}")
                reference_question = reference_by_family[family_id].get(source_question_id)
                if reference_question is None:
                    raise KeyError(f"missing reference question {family_id}::{source_question_id}")
                reference_questions[composite_id] = reference_question
                question_ids.append(composite_id)

    report = compare_question_maps(
        family_id=args.family_id,
        reference_questions=reference_questions,
        candidate_questions=candidate_questions,
        question_ids=question_ids,
    )
    write_json(args.output_json, report)
    write_text(args.output_md, render_pair_report_markdown(report, title=args.title))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
