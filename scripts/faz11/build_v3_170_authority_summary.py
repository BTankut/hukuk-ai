#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz11_lib import (
    load_json,
    parity_trace,
    preprojection_hash,
    question_bank_index,
    question_index,
    runtime_error_row,
    stage_hash,
    stage_payload,
)


def build_authority_summary(
    *,
    rc_g_report: dict[str, Any],
    rc_j_report: dict[str, Any],
    questions_path: Path,
    rc_g_gateway_pid: str | None,
    rc_j_gateway_pid: str | None,
    run_id: str,
    family_id: str,
    rc_g_rerun_report: dict[str, Any] | None = None,
    rc_j_rerun_report: dict[str, Any] | None = None,
    rc_g_rerun_gateway_pid: str | None = None,
    rc_j_rerun_gateway_pid: str | None = None,
) -> dict[str, Any]:
    bank_index = question_bank_index(questions_path)
    rc_g_questions = question_index(rc_g_report)
    rc_j_questions = question_index(rc_j_report)
    rc_g_rerun_questions = question_index(rc_g_rerun_report or {})
    rc_j_rerun_questions = question_index(rc_j_rerun_report or {})

    authoritative_rows: list[dict[str, Any]] = []
    mismatch_rows: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()

    for question_id, bank_row in bank_index.items():
        ordinal_index = int(bank_row["ordinal_index"])
        rc_g_question = rc_g_questions.get(question_id)
        rc_j_question = rc_j_questions.get(question_id)

        if rc_g_question is None or rc_j_question is None:
            counts["parity_runtime_error_count"] += 1
            counts["authoritative_mismatch_count"] += 1
            mismatch_rows.append(
                {
                    "question_id": question_id,
                    "ordinal_index": ordinal_index,
                    "runtime_error": 1,
                    "error_type": "question_missing_in_authority_reports",
                    "normalized_request_hash_mismatch": None,
                    "model_request_payload_hash_mismatch": None,
                    "generation_contract_hash_mismatch": None,
                    "preprojection_hash_mismatch": None,
                    "raw_answer_hash_mismatch": None,
                }
            )
            continue

        rc_g_runtime_error, rc_g_error_type = runtime_error_row(rc_g_question)
        rc_j_runtime_error, rc_j_error_type = runtime_error_row(rc_j_question)

        effective_rc_g_question = rc_g_question
        effective_rc_j_question = rc_j_question
        effective_rc_g_process_id = rc_g_gateway_pid
        effective_rc_j_process_id = rc_j_gateway_pid
        effective_first_run_authoritative = True

        if rc_g_runtime_error and question_id in rc_g_rerun_questions:
            effective_rc_g_question = rc_g_rerun_questions[question_id]
            effective_rc_g_process_id = rc_g_rerun_gateway_pid
            effective_first_run_authoritative = False
        if rc_j_runtime_error and question_id in rc_j_rerun_questions:
            effective_rc_j_question = rc_j_rerun_questions[question_id]
            effective_rc_j_process_id = rc_j_rerun_gateway_pid
            effective_first_run_authoritative = False

        effective_rc_g_runtime_error, effective_rc_g_error_type = runtime_error_row(effective_rc_g_question)
        effective_rc_j_runtime_error, effective_rc_j_error_type = runtime_error_row(effective_rc_j_question)
        runtime_error = int(effective_rc_g_runtime_error or effective_rc_j_runtime_error)
        if runtime_error:
            counts["parity_runtime_error_count"] += 1

        normalized_request_hash_mismatch = int(
            stage_hash(effective_rc_g_question, "normalized_request")
            != stage_hash(effective_rc_j_question, "normalized_request")
        )
        model_request_payload_hash_mismatch = int(
            stage_hash(effective_rc_g_question, "model_request_payload")
            != stage_hash(effective_rc_j_question, "model_request_payload")
        )
        generation_contract_hash_mismatch = int(
            stage_hash(effective_rc_g_question, "generation_contract")
            != stage_hash(effective_rc_j_question, "generation_contract")
        )
        preprojection_hash_mismatch = int(
            preprojection_hash(effective_rc_g_question) != preprojection_hash(effective_rc_j_question)
        )
        raw_answer_hash_mismatch = int(
            stage_hash(effective_rc_g_question, "raw_answer_object")
            != stage_hash(effective_rc_j_question, "raw_answer_object")
        )

        counts["normalized_request_hash_mismatch_count"] += normalized_request_hash_mismatch
        counts["model_request_payload_hash_mismatch_count"] += model_request_payload_hash_mismatch
        counts["generation_contract_hash_mismatch_count"] += generation_contract_hash_mismatch
        counts["preprojection_hash_mismatch_count"] += preprojection_hash_mismatch
        counts["raw_answer_hash_mismatch_count"] += raw_answer_hash_mismatch

        worker_id = stage_payload(effective_rc_j_question, "worker_assignment_tuple").get("pinned_worker_id")
        session_namespace = stage_payload(
            effective_rc_j_question,
            "session_namespace_after_payload_freeze",
        ).get("namespace")
        error_type = effective_rc_g_error_type or effective_rc_j_error_type

        authority_row = {
            "run_id": run_id,
            "family_id": family_id,
            "question_id": question_id,
            "ordinal_index": ordinal_index,
            "worker_id": worker_id if isinstance(worker_id, str) else None,
            "process_id": effective_rc_j_process_id,
            "session_namespace": session_namespace if isinstance(session_namespace, str) else None,
            "normalized_request_hash": stage_hash(effective_rc_j_question, "normalized_request"),
            "model_request_payload_hash": stage_hash(effective_rc_j_question, "model_request_payload"),
            "generation_contract_hash": stage_hash(effective_rc_j_question, "generation_contract"),
            "preprojection_hash": preprojection_hash(effective_rc_j_question),
            "raw_answer_hash": stage_hash(effective_rc_j_question, "raw_answer_object"),
            "runtime_error": runtime_error,
            "error_type": error_type,
            "error_retry_used": 0,
            "first_run_authoritative": effective_first_run_authoritative,
            "reference_process_id": effective_rc_g_process_id,
            "reference_session_namespace": stage_payload(
                effective_rc_g_question,
                "session_namespace_after_payload_freeze",
            ).get("namespace"),
            "reference_worker_id": stage_payload(
                effective_rc_g_question,
                "worker_assignment_tuple",
            ).get("pinned_worker_id"),
        }
        authoritative_rows.append(authority_row)

        mismatch_present = any(
            [
                runtime_error,
                normalized_request_hash_mismatch,
                model_request_payload_hash_mismatch,
                generation_contract_hash_mismatch,
                preprojection_hash_mismatch,
                raw_answer_hash_mismatch,
            ]
        )
        if mismatch_present:
            counts["authoritative_mismatch_count"] += 1
            mismatch_rows.append(
                {
                    "question_id": question_id,
                    "ordinal_index": ordinal_index,
                    "runtime_error": runtime_error,
                    "error_type": error_type,
                    "normalized_request_hash_mismatch": normalized_request_hash_mismatch,
                    "model_request_payload_hash_mismatch": model_request_payload_hash_mismatch,
                    "generation_contract_hash_mismatch": generation_contract_hash_mismatch,
                    "preprojection_hash_mismatch": preprojection_hash_mismatch,
                    "raw_answer_hash_mismatch": raw_answer_hash_mismatch,
                }
            )

    first_mismatch_ordinal = mismatch_rows[0]["ordinal_index"] if mismatch_rows else None
    last_mismatch_ordinal = mismatch_rows[-1]["ordinal_index"] if mismatch_rows else None

    return {
        "run_id": run_id,
        "family_id": family_id,
        "question_count": len(bank_index),
        "normalized_request_hash_mismatch_count": counts["normalized_request_hash_mismatch_count"],
        "model_request_payload_hash_mismatch_count": counts["model_request_payload_hash_mismatch_count"],
        "generation_contract_hash_mismatch_count": counts["generation_contract_hash_mismatch_count"],
        "preprojection_hash_mismatch_count": counts["preprojection_hash_mismatch_count"],
        "raw_answer_hash_mismatch_count": counts["raw_answer_hash_mismatch_count"],
        "parity_runtime_error_count": counts["parity_runtime_error_count"],
        "authoritative_mismatch_count": counts["authoritative_mismatch_count"],
        "first_mismatch_ordinal": first_mismatch_ordinal,
        "last_mismatch_ordinal": last_mismatch_ordinal,
        "reference_first_run_runtime_error_count": sum(
            1 for row in rc_g_questions.values() if runtime_error_row(row)[0]
        ),
        "candidate_first_run_runtime_error_count": sum(
            1 for row in rc_j_questions.values() if runtime_error_row(row)[0]
        ),
        "reference_error_rerun_row_count": len(rc_g_rerun_questions),
        "candidate_error_rerun_row_count": len(rc_j_rerun_questions),
        "authoritative_rows": authoritative_rows,
        "mismatch_rows": mismatch_rows,
        "reference_report_meta": rc_g_report.get("report_meta", {}),
        "candidate_report_meta": rc_j_report.get("report_meta", {}),
    }


def render_summary_markdown(summary: dict[str, Any]) -> str:
    next_move = "RC-J output parity reopen" if summary["authoritative_mismatch_count"] == 0 and summary["parity_runtime_error_count"] == 0 else "WP-4 prefix ladder"
    decision = "PASS - V3-170 Preprojection Drift Cleared" if summary["authoritative_mismatch_count"] == 0 and summary["parity_runtime_error_count"] == 0 else (
        "NO-GO - Authority Contract Broken"
        if summary["parity_runtime_error_count"] > 0
        or summary["normalized_request_hash_mismatch_count"] > 0
        or summary["model_request_payload_hash_mismatch_count"] > 0
        or summary["generation_contract_hash_mismatch_count"] > 0
        or summary["raw_answer_hash_mismatch_count"] != summary["preprojection_hash_mismatch_count"]
        else "WP-3B - Drift Reproduced"
    )
    lines = [
        "# FAZ11 RC-J V3-170 Authoritative First Run",
        "",
        f"- run_id = `{summary['run_id']}`",
        f"- family_id = `{summary['family_id']}`",
        f"- question_count = `{summary['question_count']}`",
        f"- normalized_request_hash_mismatch_count = `{summary['normalized_request_hash_mismatch_count']}`",
        f"- model_request_payload_hash_mismatch_count = `{summary['model_request_payload_hash_mismatch_count']}`",
        f"- generation_contract_hash_mismatch_count = `{summary['generation_contract_hash_mismatch_count']}`",
        f"- preprojection_hash_mismatch_count = `{summary['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{summary['raw_answer_hash_mismatch_count']}`",
        f"- parity_runtime_error_count = `{summary['parity_runtime_error_count']}`",
        f"- authoritative_mismatch_count = `{summary['authoritative_mismatch_count']}`",
        f"- first_mismatch_ordinal = `{summary['first_mismatch_ordinal']}`",
        f"- last_mismatch_ordinal = `{summary['last_mismatch_ordinal']}`",
        f"- reference_first_run_runtime_error_count = `{summary['reference_first_run_runtime_error_count']}`",
        f"- candidate_first_run_runtime_error_count = `{summary['candidate_first_run_runtime_error_count']}`",
        f"- reference_error_rerun_row_count = `{summary['reference_error_rerun_row_count']}`",
        f"- candidate_error_rerun_row_count = `{summary['candidate_error_rerun_row_count']}`",
        "",
        f"- wp3_decision = `{decision}`",
        f"- next_official_move = `{next_move}`",
        "",
        "## Report Sources",
        "",
        f"- reference_checkpoint_ref = `{summary['reference_report_meta'].get('checkpoint_ref')}`",
        f"- candidate_checkpoint_ref = `{summary['candidate_report_meta'].get('checkpoint_ref')}`",
        f"- reference_api_url = `{summary['reference_report_meta'].get('api_url')}`",
        f"- candidate_api_url = `{summary['candidate_report_meta'].get('api_url')}`",
        "",
        "## Mismatch Sample",
        "",
    ]
    if not summary["mismatch_rows"]:
        lines.append("- mismatch yok")
    else:
        for row in summary["mismatch_rows"][:20]:
            bits = []
            for field in (
                "normalized_request_hash_mismatch",
                "model_request_payload_hash_mismatch",
                "generation_contract_hash_mismatch",
                "preprojection_hash_mismatch",
                "raw_answer_hash_mismatch",
            ):
                if row.get(field):
                    bits.append(field.removesuffix("_mismatch"))
            if row.get("runtime_error"):
                bits.append(f"runtime_error:{row.get('error_type') or 'unknown'}")
            joined = ", ".join(bits) if bits else "-"
            lines.append(f"- `{row['question_id']}` ordinal `{row['ordinal_index']}` -> {joined}")
    lines.append("")
    return "\n".join(lines)


def render_mismatch_table_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# FAZ11 V3-170 Authoritative Mismatch Table",
        "",
        "| ordinal_index | question_id | normalized_request | model_request_payload | generation_contract | preprojection | raw_answer | runtime_error | error_type |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    if not summary["mismatch_rows"]:
        lines.append("| - | - | - | - | - | - | - | - | no mismatch |")
    else:
        for row in summary["mismatch_rows"]:
            lines.append(
                f"| {row['ordinal_index']} | {row['question_id']} | {row['normalized_request_hash_mismatch']} | {row['model_request_payload_hash_mismatch']} | {row['generation_contract_hash_mismatch']} | {row['preprojection_hash_mismatch']} | {row['raw_answer_hash_mismatch']} | {row['runtime_error']} | {row.get('error_type') or '-'} |"
            )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ11 v3-170 authoritative first-run summary.")
    parser.add_argument("--reference-report", type=Path, required=True)
    parser.add_argument("--candidate-report", type=Path, required=True)
    parser.add_argument("--questions-path", type=Path, required=True)
    parser.add_argument("--reference-gateway-pid", default=None)
    parser.add_argument("--candidate-gateway-pid", default=None)
    parser.add_argument("--reference-rerun-report", type=Path)
    parser.add_argument("--candidate-rerun-report", type=Path)
    parser.add_argument("--reference-rerun-gateway-pid", default=None)
    parser.add_argument("--candidate-rerun-gateway-pid", default=None)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--family-id", default="v3-170")
    parser.add_argument("--output-summary-md", type=Path, required=True)
    parser.add_argument("--output-mismatch-md", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = build_authority_summary(
        rc_g_report=load_json(args.reference_report),
        rc_j_report=load_json(args.candidate_report),
        questions_path=args.questions_path,
        rc_g_gateway_pid=args.reference_gateway_pid,
        rc_j_gateway_pid=args.candidate_gateway_pid,
        run_id=args.run_id,
        family_id=args.family_id,
        rc_g_rerun_report=load_json(args.reference_rerun_report) if args.reference_rerun_report else None,
        rc_j_rerun_report=load_json(args.candidate_rerun_report) if args.candidate_rerun_report else None,
        rc_g_rerun_gateway_pid=args.reference_rerun_gateway_pid,
        rc_j_rerun_gateway_pid=args.candidate_rerun_gateway_pid,
    )
    args.output_summary_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_summary_md.write_text(render_summary_markdown(summary), encoding="utf-8")
    args.output_mismatch_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_mismatch_md.write_text(render_mismatch_table_markdown(summary), encoding="utf-8")
    if args.output_json:
        from faz11_lib import write_json

        write_json(args.output_json, summary)

    if (
        summary["normalized_request_hash_mismatch_count"] == 0
        and summary["model_request_payload_hash_mismatch_count"] == 0
        and summary["generation_contract_hash_mismatch_count"] == 0
        and summary["preprojection_hash_mismatch_count"] == 0
        and summary["raw_answer_hash_mismatch_count"] == 0
        and summary["parity_runtime_error_count"] == 0
    ):
        return 0
    if (
        summary["normalized_request_hash_mismatch_count"] == 0
        and summary["model_request_payload_hash_mismatch_count"] == 0
        and summary["generation_contract_hash_mismatch_count"] == 0
        and summary["preprojection_hash_mismatch_count"] > 0
        and summary["raw_answer_hash_mismatch_count"] == summary["preprojection_hash_mismatch_count"]
        and summary["parity_runtime_error_count"] == 0
    ):
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
