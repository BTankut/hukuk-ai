#!/usr/bin/env python3
"""Validate a completed hukuk-ai 100 benchmark run artifact."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_QUESTIONS = REPO_ROOT / "configs/evaluation/hukuk_ai_100_public_questions.csv"
REQUIRED_ANSWER_COLUMNS = [
    "qid",
    "answer",
    "citations",
    "source_titles",
    "source_ids",
    "doc_types",
    "confidence_0_100",
    "final_reason",
    "retrieval_trace_id",
]
PHASE2_CONTRACT_COLUMNS = [
    "answer_mode",
    "grounding_status",
    "source_family_claimed",
    "source_title_claimed",
    "source_identifier_claimed",
    "article_or_section_claimed",
    "effective_state_claimed",
    "temporal_qualification",
    "needs_manual_review",
    "contract_valid",
    "claimed_source_parse_success",
    "confidence_policy_ok",
    "uncertainty_disclosed",
    "manual_review_flag",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    parser.add_argument("--strict-contract", action="store_true")
    parser.add_argument(
        "--require-provenance",
        action="store_true",
        help="Fail the validation when runtime_provenance.json is absent.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


def read_trace_qids(path: Path) -> list[str]:
    qids: list[str] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            qids.append(str(record.get("qid", "")))
    return qids


def write_md(path: Path, summary: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# hukuk-ai 100 run validation",
        "",
        f"- status: `{summary['status']}`",
        f"- run_dir: `{summary['run_dir']}`",
        f"- answer_rows: {summary['answer_rows']}",
        f"- trace_rows: {summary['trace_rows']}",
        f"- missing_answer_columns: {summary['missing_answer_columns']}",
        f"- missing_phase2_contract_columns: {summary['missing_phase2_contract_columns']}",
        f"- missing_qids: {summary['missing_qids']}",
        f"- extra_qids: {summary['extra_qids']}",
        f"- duplicate_answer_qids: {summary['duplicate_answer_qids']}",
        f"- missing_retrieval_trace_id: {summary['missing_retrieval_trace_id']}",
        f"- error_rows: {summary['error_rows']}",
        f"- refused_or_empty_rows: {summary['refused_or_empty_rows']}",
        f"- missing_confidence_0_100: {summary['missing_confidence_0_100']}",
        f"- missing_final_reason: {summary['missing_final_reason']}",
        f"- missing_phase2_contract_fields: {summary['missing_phase2_contract_fields']}",
        f"- invalid_contract_rows: {summary['invalid_contract_rows']}",
        f"- runtime_provenance_present: {summary['runtime_provenance_present']}",
        f"- require_provenance: {summary['require_provenance']}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    answers_path = args.run_dir / "candidate_answers.csv"
    trace_path = args.run_dir / "trace.jsonl"
    provenance_path = args.run_dir / "runtime_provenance.json"
    question_columns, questions = read_csv(args.questions)
    answer_columns, answers = read_csv(answers_path)
    trace_qids = read_trace_qids(trace_path)

    expected_qids = [row.get("q_id", "").strip() for row in questions]
    answer_qids = [row.get("qid", "").strip() for row in answers]
    duplicate_answer_qids = sorted(qid for qid, count in Counter(answer_qids).items() if qid and count > 1)
    missing_qids = sorted(set(expected_qids) - set(answer_qids))
    extra_qids = sorted(set(answer_qids) - set(expected_qids))
    missing_answer_columns = [column for column in REQUIRED_ANSWER_COLUMNS if column not in answer_columns]
    missing_phase2_contract_columns = [
        column for column in PHASE2_CONTRACT_COLUMNS if column not in answer_columns
    ]
    missing_trace_qids = sorted(set(answer_qids) - set(trace_qids))
    extra_trace_qids = sorted(set(trace_qids) - set(answer_qids))
    missing_confidence = sum(1 for row in answers if not row.get("confidence_0_100", "").strip())
    missing_final_reason = sum(1 for row in answers if not row.get("final_reason", "").strip())
    missing_phase2_contract_fields = sum(
        1
        for row in answers
        if any(not row.get(column, "").strip() for column in PHASE2_CONTRACT_COLUMNS)
    )
    invalid_contract_rows = sum(1 for row in answers if row.get("contract_valid", "").strip() == "False")

    summary = {
        "run_dir": str(args.run_dir),
        "question_columns": question_columns,
        "answer_rows": len(answers),
        "trace_rows": len(trace_qids),
        "expected_question_rows": len(questions),
        "missing_answer_columns": missing_answer_columns,
        "missing_phase2_contract_columns": missing_phase2_contract_columns,
        "missing_qids": missing_qids,
        "extra_qids": extra_qids,
        "duplicate_answer_qids": duplicate_answer_qids,
        "missing_trace_qids": missing_trace_qids,
        "extra_trace_qids": extra_trace_qids,
        "missing_retrieval_trace_id": sum(1 for row in answers if not row.get("retrieval_trace_id", "").strip()),
        "error_rows": sum(1 for row in answers if row.get("error", "").strip()),
        "refused_or_empty_rows": sum(1 for row in answers if row.get("answer", "").startswith("REFUSED_OR_EMPTY:")),
        "missing_confidence_0_100": missing_confidence,
        "missing_final_reason": missing_final_reason,
        "missing_phase2_contract_fields": missing_phase2_contract_fields,
        "invalid_contract_rows": invalid_contract_rows,
        "strict_contract": args.strict_contract,
        "runtime_provenance_path": str(provenance_path),
        "runtime_provenance_present": provenance_path.exists(),
        "require_provenance": args.require_provenance,
    }
    hard_fail = (
        len(answers) != len(questions)
        or len(trace_qids) != len(answers)
        or bool(missing_answer_columns)
        or bool(missing_qids)
        or bool(extra_qids)
        or bool(duplicate_answer_qids)
        or bool(missing_trace_qids)
        or bool(extra_trace_qids)
        or summary["missing_retrieval_trace_id"] != 0
        or summary["error_rows"] != 0
        or summary["refused_or_empty_rows"] != 0
    )
    contract_fail = args.strict_contract and (
        missing_confidence > 0
        or missing_final_reason > 0
        or bool(missing_phase2_contract_columns)
        or missing_phase2_contract_fields > 0
        or invalid_contract_rows > 0
    )
    provenance_fail = args.require_provenance and not provenance_path.exists()
    summary["status"] = "fail" if hard_fail or contract_fail or provenance_fail else "pass"

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    if args.md_out:
        write_md(args.md_out, summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
