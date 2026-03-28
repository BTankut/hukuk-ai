#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz26_lib import load_json, stable_hash, write_json


FIELD_SPECS = [
    ("retrieval_request_hash_mismatch_count", "retrieval_input_payload", "retrieval_request_hash"),
    ("assembled_context_hash_mismatch_count", "assembly_payload", "assembled_context_hash"),
    ("model_request_payload_hash_mismatch_count", "model_request_payload", "model_request_payload_hash"),
    ("preprojection_hash_mismatch_count", None, "preprojection_hash"),
    ("raw_answer_hash_mismatch_count", "raw_answer_object", "raw_answer_hash"),
]

FIRST_BREAK_PRIORITY = [
    ("retrieval_request_hash_mismatch_count", "retrieval_input_payload"),
    ("assembled_context_hash_mismatch_count", "assembly_payload"),
    ("model_request_payload_hash_mismatch_count", "model_request_payload"),
    ("preprojection_hash_mismatch_count", "preprojection_hash"),
    ("raw_answer_hash_mismatch_count", "raw_answer_object"),
]

PRIMARY_REASON_BY_STAGE = {
    "retrieval_input_payload": "retrieval_request_hash_drift",
    "assembly_payload": "assembled_context_hash_drift",
    "model_request_payload": "model_request_payload_hash_drift",
    "preprojection_hash": "preprojection_hash_drift",
    "raw_answer_object": "raw_answer_hash_drift",
}


def _question_index(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row["question_id"]): row
        for row in report.get("per_question", [])
        if isinstance(row, dict) and row.get("question_id")
    }


def _stage_map(question: dict[str, Any]) -> dict[str, dict[str, Any]]:
    parity_trace = ((question.get("trace") or {}).get("parity_trace") or {}) if isinstance(question, dict) else {}
    stages = parity_trace.get("stages") or []
    return {
        str(item.get("stage")): item
        for item in stages
        if isinstance(item, dict) and item.get("stage")
    }


def _stage_hash(question: dict[str, Any], stage_name: str) -> str | None:
    stage = _stage_map(question).get(stage_name) or {}
    value = stage.get("hash")
    if isinstance(value, str) and value:
        return value
    payload = stage.get("payload")
    if isinstance(payload, dict):
        return stable_hash(payload)
    return None


def _preprojection_hash(question: dict[str, Any]) -> str | None:
    parity_trace = ((question.get("trace") or {}).get("parity_trace") or {}) if isinstance(question, dict) else {}
    value = parity_trace.get("preprojection_hash")
    return value if isinstance(value, str) and value else None


def build_report(
    *,
    family_id: str,
    reference_report: dict[str, Any],
    candidate_report: dict[str, Any],
) -> dict[str, Any]:
    reference_questions = _question_index(reference_report)
    candidate_questions = _question_index(candidate_report)
    report = {
        "family_id": family_id,
        "question_count": len(set(reference_questions) | set(candidate_questions)),
        "compared_question_count": 0,
        "model_request_payload_hash_mismatch_count": 0,
        "retrieval_request_hash_mismatch_count": 0,
        "assembled_context_hash_mismatch_count": 0,
        "preprojection_hash_mismatch_count": 0,
        "raw_answer_hash_mismatch_count": 0,
        "runtime_error_count": 0,
        "first_break_stage_assigned_count": 0,
        "primary_reason_assigned_count": 0,
        "unexplained_count": 0,
        "mismatch_rows": [],
    }

    for question_id in sorted(set(reference_questions) | set(candidate_questions)):
        reference_question = reference_questions.get(question_id)
        candidate_question = candidate_questions.get(question_id)
        if reference_question is None or candidate_question is None:
            report["runtime_error_count"] += 1
            report["unexplained_count"] += 1
            report["mismatch_rows"].append(
                {
                    "question_id": question_id,
                    "first_break_stage": None,
                    "primary_reason": None,
                    "notes": "question missing in reference or candidate report",
                }
            )
            continue

        mismatches: dict[str, dict[str, str | None]] = {}
        runtime_error = False
        for counter_key, stage_name, label in FIELD_SPECS:
            reference_hash = _preprojection_hash(reference_question) if stage_name is None else _stage_hash(reference_question, stage_name)
            candidate_hash = _preprojection_hash(candidate_question) if stage_name is None else _stage_hash(candidate_question, stage_name)
            if not isinstance(reference_hash, str) or not isinstance(candidate_hash, str):
                runtime_error = True
                mismatches[label] = {"reference_hash": reference_hash, "candidate_hash": candidate_hash}
                continue
            if reference_hash != candidate_hash:
                report[counter_key] += 1
                mismatches[label] = {"reference_hash": reference_hash, "candidate_hash": candidate_hash}

        if runtime_error:
            report["runtime_error_count"] += 1

        if not mismatches and not runtime_error:
            report["compared_question_count"] += 1
            continue

        first_break_stage = None
        primary_reason = None
        for counter_key, stage_name in FIRST_BREAK_PRIORITY:
            if stage_name == "preprojection_hash":
                hit = "preprojection_hash" in mismatches
            else:
                label = next(spec[2] for spec in FIELD_SPECS if spec[1] == stage_name)
                hit = label in mismatches
            if hit:
                first_break_stage = stage_name
                primary_reason = PRIMARY_REASON_BY_STAGE[stage_name]
                break

        if first_break_stage is not None:
            report["first_break_stage_assigned_count"] += 1
        if primary_reason is not None:
            report["primary_reason_assigned_count"] += 1
        if first_break_stage is None or primary_reason is None:
            report["unexplained_count"] += 1

        report["mismatch_rows"].append(
            {
                "question_id": question_id,
                "first_break_stage": first_break_stage,
                "primary_reason": primary_reason,
                "runtime_error": runtime_error,
                "mismatch_keys": sorted(mismatches.keys()),
            }
        )
        report["compared_question_count"] += 1

    return report


def render_markdown(report: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- family_id = `{report['family_id']}`",
        f"- question_count = `{report['question_count']}`",
        f"- compared_question_count = `{report['compared_question_count']}`",
        f"- model_request_payload_hash_mismatch_count = `{report['model_request_payload_hash_mismatch_count']}`",
        f"- retrieval_request_hash_mismatch_count = `{report['retrieval_request_hash_mismatch_count']}`",
        f"- assembled_context_hash_mismatch_count = `{report['assembled_context_hash_mismatch_count']}`",
        f"- preprojection_hash_mismatch_count = `{report['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{report['raw_answer_hash_mismatch_count']}`",
        f"- runtime_error_count = `{report['runtime_error_count']}`",
        f"- first_break_stage_assigned_count = `{report['first_break_stage_assigned_count']}`",
        f"- primary_reason_assigned_count = `{report['primary_reason_assigned_count']}`",
        f"- unexplained_count = `{report['unexplained_count']}`",
        "",
        "## Frontier Sample",
        "",
    ]
    if not report["mismatch_rows"]:
        lines.append("- mismatch yok")
    else:
        for row in report["mismatch_rows"][:20]:
            lines.append(
                f"- `{row['question_id']}` stage `{row['first_break_stage']}` reason `{row['primary_reason']}`"
            )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ26 model-visible surface report.")
    parser.add_argument("--family-id", required=True)
    parser.add_argument("--reference-report", type=Path, required=True)
    parser.add_argument("--candidate-report", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--title", required=True)
    args = parser.parse_args()

    report = build_report(
        family_id=args.family_id,
        reference_report=load_json(args.reference_report),
        candidate_report=load_json(args.candidate_report),
    )
    write_json(args.output_json, report)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(report, title=args.title), encoding="utf-8")
    counts = [
        report["model_request_payload_hash_mismatch_count"],
        report["retrieval_request_hash_mismatch_count"],
        report["assembled_context_hash_mismatch_count"],
        report["preprojection_hash_mismatch_count"],
        report["raw_answer_hash_mismatch_count"],
        report["runtime_error_count"],
        report["unexplained_count"],
    ]
    return 0 if sum(counts) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
