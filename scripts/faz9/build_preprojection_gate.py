#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz9_lib import load_json, stage_map, write_json


WATCHED_STAGE_KEYS = {
    "normalized_request_hash_mismatch_count": "normalized_request",
    "model_request_payload_hash_mismatch_count": "model_request_payload",
    "generation_contract_hash_mismatch_count": "generation_contract",
    "raw_answer_hash_mismatch_count": "raw_answer_object",
}


def _runtime_error(question_id: str, notes: str) -> dict[str, Any]:
    return {
        "question_id": question_id,
        "occurrence_index": None,
        "kind": "parity_runtime_error",
        "stage": None,
        "reference_hash": None,
        "candidate_hash": None,
        "reference_preprojection_hash": None,
        "candidate_preprojection_hash": None,
        "notes": notes,
    }


def _question_occurrences(report: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
    occurrences: dict[str, int] = {}
    indexed: dict[tuple[str, int], dict[str, Any]] = {}
    for item in report.get("per_question", []):
        if not isinstance(item, dict) or not item.get("question_id"):
            continue
        question_id = str(item["question_id"])
        occurrence_index = occurrences.get(question_id, 0) + 1
        occurrences[question_id] = occurrence_index
        indexed[(question_id, occurrence_index)] = item
    return indexed


def build_gate(reference_report: dict[str, Any], candidate_report: dict[str, Any]) -> dict[str, Any]:
    reference_questions = _question_occurrences(reference_report)
    candidate_questions = _question_occurrences(candidate_report)
    summary = {
        "eval_family": reference_report.get("report_meta", {}).get("eval_family"),
        "reference_checkpoint_ref": reference_report.get("report_meta", {}).get("checkpoint_ref"),
        "candidate_checkpoint_ref": candidate_report.get("report_meta", {}).get("checkpoint_ref"),
        "question_count": len(set(reference_questions) | set(candidate_questions)),
        "compared_question_count": 0,
        "normalized_request_hash_mismatch_count": 0,
        "model_request_payload_hash_mismatch_count": 0,
        "generation_contract_hash_mismatch_count": 0,
        "preprojection_hash_mismatch_count": 0,
        "raw_answer_hash_mismatch_count": 0,
        "parity_runtime_error_count": 0,
        "mismatches": [],
    }

    for key in sorted(set(reference_questions) | set(candidate_questions), key=lambda item: (item[0], item[1])):
        question_id, occurrence_index = key
        reference_question = reference_questions.get(key)
        candidate_question = candidate_questions.get(key)
        if reference_question is None or candidate_question is None:
            summary["parity_runtime_error_count"] += 1
            row = _runtime_error(question_id, "question missing in reference or candidate report")
            row["occurrence_index"] = occurrence_index
            summary["mismatches"].append(row)
            continue

        reference_trace = (reference_question.get("trace") or {}).get("parity_trace") or {}
        candidate_trace = (candidate_question.get("trace") or {}).get("parity_trace") or {}
        if not reference_trace or not candidate_trace:
            summary["parity_runtime_error_count"] += 1
            row = _runtime_error(question_id, "parity trace missing in reference or candidate report")
            row["occurrence_index"] = occurrence_index
            summary["mismatches"].append(row)
            continue

        reference_stages = stage_map(reference_question)
        candidate_stages = stage_map(candidate_question)
        runtime_error = False
        for counter_key, stage_name in WATCHED_STAGE_KEYS.items():
            reference_stage = reference_stages.get(stage_name) or {}
            candidate_stage = candidate_stages.get(stage_name) or {}
            reference_hash = reference_stage.get("hash")
            candidate_hash = candidate_stage.get("hash")
            if not isinstance(reference_hash, str) or not isinstance(candidate_hash, str):
                runtime_error = True
                break
            if reference_hash != candidate_hash:
                summary[counter_key] += 1
                summary["mismatches"].append(
                    {
                        "question_id": question_id,
                        "occurrence_index": occurrence_index,
                        "kind": counter_key.removesuffix("_count"),
                        "stage": stage_name,
                        "reference_hash": reference_hash,
                        "candidate_hash": candidate_hash,
                        "reference_preprojection_hash": None,
                        "candidate_preprojection_hash": None,
                        "notes": None,
                    }
                )

        reference_preprojection_hash = reference_trace.get("preprojection_hash")
        candidate_preprojection_hash = candidate_trace.get("preprojection_hash")
        if not isinstance(reference_preprojection_hash, str) or not isinstance(candidate_preprojection_hash, str):
            runtime_error = True
        elif reference_preprojection_hash != candidate_preprojection_hash:
            summary["preprojection_hash_mismatch_count"] += 1
            summary["mismatches"].append(
                {
                    "question_id": question_id,
                    "occurrence_index": occurrence_index,
                    "kind": "preprojection_hash_mismatch",
                    "stage": "raw_answer_object",
                    "reference_hash": reference_stages.get("raw_answer_object", {}).get("hash"),
                    "candidate_hash": candidate_stages.get("raw_answer_object", {}).get("hash"),
                    "reference_preprojection_hash": reference_preprojection_hash,
                    "candidate_preprojection_hash": candidate_preprojection_hash,
                    "notes": None,
                }
            )

        if runtime_error:
            summary["parity_runtime_error_count"] += 1
            row = _runtime_error(question_id, "missing watched stage hash or preprojection hash")
            row["occurrence_index"] = occurrence_index
            summary["mismatches"].append(row)
            continue

        summary["compared_question_count"] += 1

    return summary


def render_markdown(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- eval_family = `{summary['eval_family']}`",
        f"- reference_checkpoint_ref = `{summary['reference_checkpoint_ref']}`",
        f"- candidate_checkpoint_ref = `{summary['candidate_checkpoint_ref']}`",
        f"- question_count = `{summary['question_count']}`",
        f"- compared_question_count = `{summary['compared_question_count']}`",
        f"- normalized_request_hash_mismatch_count = `{summary['normalized_request_hash_mismatch_count']}`",
        f"- model_request_payload_hash_mismatch_count = `{summary['model_request_payload_hash_mismatch_count']}`",
        f"- generation_contract_hash_mismatch_count = `{summary['generation_contract_hash_mismatch_count']}`",
        f"- preprojection_hash_mismatch_count = `{summary['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{summary['raw_answer_hash_mismatch_count']}`",
        f"- parity_runtime_error_count = `{summary['parity_runtime_error_count']}`",
        "",
        "## Mismatch Sample",
        "",
    ]
    if not summary["mismatches"]:
        lines.append("- mismatch yok")
    else:
        for item in summary["mismatches"][:20]:
            note = f" ({item['notes']})" if item.get("notes") else ""
            lines.append(f"- `{item['question_id']}` `{item['kind']}` `{item.get('stage')}`{note}")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ9 preprojection gate summary.")
    parser.add_argument("--reference-report", type=Path, required=True)
    parser.add_argument("--candidate-report", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--title", default="FAZ9 RC-J Preprojection Gate")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = build_gate(load_json(args.reference_report), load_json(args.candidate_report))
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(summary, title=args.title), encoding="utf-8")
    if args.output_json:
        write_json(args.output_json, summary)
    counts = [
        summary["normalized_request_hash_mismatch_count"],
        summary["model_request_payload_hash_mismatch_count"],
        summary["generation_contract_hash_mismatch_count"],
        summary["preprojection_hash_mismatch_count"],
        summary["raw_answer_hash_mismatch_count"],
        summary["parity_runtime_error_count"],
    ]
    return 0 if sum(counts) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
