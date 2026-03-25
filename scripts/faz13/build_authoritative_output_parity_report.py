#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz13_lib import (  # noqa: E402
    candidate_identity,
    first_divergence,
    lane_identity,
    load_json,
    metric_delta,
    parity_fields,
    primary_reason,
    question_bank_index,
    question_index,
    runtime_error_row,
    stable_hash,
    write_json,
)


MISMATCH_COUNTER_KEYS = (
    "normalized_request_hash_mismatch_count",
    "model_request_payload_hash_mismatch_count",
    "generation_contract_hash_mismatch_count",
    "preprojection_anchor_mismatch_count",
    "cited_projection_hash_mismatch_count",
    "citation_set_projection_hash_mismatch_count",
    "final_mode_mapping_hash_mismatch_count",
    "blocked_reason_set_mismatch_count",
    "final_answer_payload_hash_mismatch_count",
    "response_envelope_hash_mismatch_count",
    "serialized_output_hash_mismatch_count",
)


def _effective_question(
    *,
    first_run: dict[str, Any] | None,
    rerun_index: dict[str, dict[str, Any]],
    question_id: str,
) -> tuple[dict[str, Any] | None, bool, bool, str | None]:
    runtime_error, error_type = runtime_error_row(first_run)
    rerun_used = runtime_error and question_id in rerun_index
    effective_question = rerun_index.get(question_id) if rerun_used else first_run
    effective_runtime_error, effective_error_type = runtime_error_row(effective_question)
    return effective_question, bool(rerun_used), bool(effective_runtime_error), effective_error_type or error_type


def build_report(
    *,
    run_id: str,
    family_id: str,
    questions_path: Path,
    reference_report: dict[str, Any],
    candidate_report: dict[str, Any],
    reference_run_label: str,
    candidate_run_label: str,
    reference_rerun_report: dict[str, Any] | None = None,
    candidate_rerun_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    bank_index = question_bank_index(questions_path)
    reference_first_run = question_index(reference_report)
    candidate_first_run = question_index(candidate_report)
    reference_rerun = question_index(reference_rerun_report or {})
    candidate_rerun = question_index(candidate_rerun_report or {})

    counts: Counter[str] = Counter()
    authoritative_rows: list[dict[str, Any]] = []
    mismatch_rows: list[dict[str, Any]] = []
    effective_reference_rows: list[dict[str, Any]] = []
    effective_candidate_rows: list[dict[str, Any]] = []

    reference_candidate_id = candidate_identity(reference_report, reference_run_label)
    candidate_candidate_id = candidate_identity(candidate_report, candidate_run_label)
    reference_lane_id = lane_identity(reference_report, reference_run_label)
    candidate_lane_id = lane_identity(candidate_report, candidate_run_label)

    for question_id, bank_row in bank_index.items():
        ordinal_index = int(bank_row["ordinal_index"])
        reference_question = reference_first_run.get(question_id)
        candidate_question = candidate_first_run.get(question_id)

        reference_runtime_error, reference_error_type = runtime_error_row(reference_question)
        candidate_runtime_error, candidate_error_type = runtime_error_row(candidate_question)

        effective_reference_question, reference_error_rerun_used, effective_reference_runtime_error, effective_reference_error_type = _effective_question(
            first_run=reference_question,
            rerun_index=reference_rerun,
            question_id=question_id,
        )
        effective_candidate_question, candidate_error_rerun_used, effective_candidate_runtime_error, effective_candidate_error_type = _effective_question(
            first_run=candidate_question,
            rerun_index=candidate_rerun,
            question_id=question_id,
        )

        counts["reference_runtime_error_count"] += int(effective_reference_runtime_error)
        counts["candidate_runtime_error_count"] += int(effective_candidate_runtime_error)
        counts["reference_error_rerun_row_count"] += int(reference_error_rerun_used)
        counts["candidate_error_rerun_row_count"] += int(candidate_error_rerun_used)

        reference_fields = parity_fields(effective_reference_question or {})
        candidate_fields = parity_fields(effective_candidate_question or {})
        effective_view_member = int(effective_reference_question is not None and effective_candidate_question is not None)

        authoritative_row = {
            "run_id": run_id,
            "family_id": family_id,
            "question_id": question_id,
            "ordinal_index": ordinal_index,
            "candidate_id": candidate_candidate_id,
            "lane_id": candidate_lane_id,
            "worker_id": candidate_fields.get("worker_id"),
            "process_id": candidate_fields.get("process_id"),
            "session_namespace": candidate_fields.get("session_namespace"),
            "cache_namespace": candidate_fields.get("cache_namespace"),
            "first_run_authoritative": True,
            "runtime_error": int(candidate_runtime_error),
            "error_type": candidate_error_type,
            "error_rerun_used": int(candidate_error_rerun_used),
            "effective_view_member": effective_view_member,
            "normalized_request_hash": candidate_fields.get("normalized_request_hash"),
            "model_request_payload_hash": candidate_fields.get("model_request_payload_hash"),
            "generation_contract_hash": candidate_fields.get("generation_contract_hash"),
            "preprojection_anchor_hash": candidate_fields.get("preprojection_anchor_hash"),
            "cited_projection_hash": candidate_fields.get("cited_projection_hash"),
            "citation_set_projection_hash": candidate_fields.get("citation_set_projection_hash"),
            "final_mode_mapping_hash": candidate_fields.get("final_mode_mapping_hash"),
            "blocked_reason_set_hash": candidate_fields.get("blocked_reason_set_hash"),
            "final_answer_payload_hash": candidate_fields.get("final_answer_payload_hash"),
            "response_envelope_hash": candidate_fields.get("response_envelope_hash"),
            "serialized_output_hash": candidate_fields.get("serialized_output_hash"),
            "refusal_mode": candidate_fields.get("refusal_mode"),
            "refusal_body_hash": candidate_fields.get("refusal_body_hash"),
            "answer_body_hash": candidate_fields.get("answer_body_hash"),
            "citation_body_hash": candidate_fields.get("citation_body_hash"),
            "effective_runtime_error": int(effective_candidate_runtime_error),
            "effective_error_type": effective_candidate_error_type,
            "reference_candidate_id": reference_candidate_id,
            "reference_lane_id": reference_lane_id,
            "reference_worker_id": reference_fields.get("worker_id"),
            "reference_process_id": reference_fields.get("process_id"),
            "reference_session_namespace": reference_fields.get("session_namespace"),
            "reference_cache_namespace": reference_fields.get("cache_namespace"),
            "reference_runtime_error": int(reference_runtime_error),
            "reference_error_type": reference_error_type,
            "reference_error_rerun_used": int(reference_error_rerun_used),
            "reference_effective_runtime_error": int(effective_reference_runtime_error),
            "reference_effective_error_type": effective_reference_error_type,
            "reference_normalized_request_hash": reference_fields.get("normalized_request_hash"),
            "reference_model_request_payload_hash": reference_fields.get("model_request_payload_hash"),
            "reference_generation_contract_hash": reference_fields.get("generation_contract_hash"),
            "reference_preprojection_anchor_hash": reference_fields.get("preprojection_anchor_hash"),
            "reference_cited_projection_hash": reference_fields.get("cited_projection_hash"),
            "reference_citation_set_projection_hash": reference_fields.get("citation_set_projection_hash"),
            "reference_final_mode_mapping_hash": reference_fields.get("final_mode_mapping_hash"),
            "reference_blocked_reason_set_hash": reference_fields.get("blocked_reason_set_hash"),
            "reference_final_answer_payload_hash": reference_fields.get("final_answer_payload_hash"),
            "reference_response_envelope_hash": reference_fields.get("response_envelope_hash"),
            "reference_serialized_output_hash": reference_fields.get("serialized_output_hash"),
            "reference_refusal_mode": reference_fields.get("refusal_mode"),
            "reference_refusal_body_hash": reference_fields.get("refusal_body_hash"),
            "reference_answer_body_hash": reference_fields.get("answer_body_hash"),
            "reference_citation_body_hash": reference_fields.get("citation_body_hash"),
        }
        authoritative_rows.append(authoritative_row)

        row = {
            "family_id": family_id,
            "question_id": question_id,
            "ordinal_index": ordinal_index,
            "reference_runtime_error": int(effective_reference_runtime_error),
            "candidate_runtime_error": int(effective_candidate_runtime_error),
            "reference_error_rerun_used": int(reference_error_rerun_used),
            "candidate_error_rerun_used": int(candidate_error_rerun_used),
            "effective_view_member": effective_view_member,
        }

        mismatch_bits = {
            "normalized_request_hash_mismatch": int(
                reference_fields.get("normalized_request_hash") != candidate_fields.get("normalized_request_hash")
            ),
            "model_request_payload_hash_mismatch": int(
                reference_fields.get("model_request_payload_hash") != candidate_fields.get("model_request_payload_hash")
            ),
            "generation_contract_hash_mismatch": int(
                reference_fields.get("generation_contract_hash") != candidate_fields.get("generation_contract_hash")
            ),
            "preprojection_anchor_mismatch": int(
                reference_fields.get("preprojection_anchor_hash") != candidate_fields.get("preprojection_anchor_hash")
            ),
            "cited_projection_hash_mismatch": int(
                reference_fields.get("cited_projection_hash") != candidate_fields.get("cited_projection_hash")
            ),
            "citation_set_projection_hash_mismatch": int(
                reference_fields.get("citation_set_projection_hash") != candidate_fields.get("citation_set_projection_hash")
            ),
            "final_mode_mapping_hash_mismatch": int(
                reference_fields.get("final_mode_mapping_hash") != candidate_fields.get("final_mode_mapping_hash")
            ),
            "blocked_reason_set_mismatch": int(
                reference_fields.get("blocked_reason_set_hash") != candidate_fields.get("blocked_reason_set_hash")
            ),
            "final_answer_payload_hash_mismatch": int(
                reference_fields.get("final_answer_payload_hash") != candidate_fields.get("final_answer_payload_hash")
            ),
            "response_envelope_hash_mismatch": int(
                reference_fields.get("response_envelope_hash") != candidate_fields.get("response_envelope_hash")
            ),
            "serialized_output_hash_mismatch": int(
                reference_fields.get("serialized_output_hash") != candidate_fields.get("serialized_output_hash")
            ),
        }
        row.update(mismatch_bits)

        for key, value in mismatch_bits.items():
            counts[f"{key}_count"] += int(value)

        row_mismatch = any(mismatch_bits.values()) or effective_reference_runtime_error or effective_candidate_runtime_error
        if row_mismatch:
            row["first_divergence_stage"] = first_divergence(reference_fields, candidate_fields)
            row["primary_reason"] = primary_reason(
                first_divergence_stage=row["first_divergence_stage"],
                reference_runtime_error=bool(effective_reference_runtime_error),
                candidate_runtime_error=bool(effective_candidate_runtime_error),
                reference_error_rerun_used=int(reference_error_rerun_used),
                candidate_error_rerun_used=int(candidate_error_rerun_used),
            )
            mismatch_rows.append(row)

        if isinstance(effective_reference_question, dict):
            effective_reference_rows.append(effective_reference_question)
        if isinstance(effective_candidate_question, dict):
            effective_candidate_rows.append(effective_candidate_question)

    metric_deltas = metric_delta(effective_reference_rows, effective_candidate_rows)
    family_metric_delta_zero = all(value == 0 for value in metric_deltas.values())
    mismatch_count = len(mismatch_rows)

    report = {
        "run_id": run_id,
        "family_id": family_id,
        "question_count": len(bank_index),
        "reference_runtime_error_count": counts["reference_runtime_error_count"],
        "candidate_runtime_error_count": counts["candidate_runtime_error_count"],
        "reference_error_rerun_row_count": counts["reference_error_rerun_row_count"],
        "candidate_error_rerun_row_count": counts["candidate_error_rerun_row_count"],
        "normalized_request_hash_mismatch_count": counts["normalized_request_hash_mismatch_count"],
        "model_request_payload_hash_mismatch_count": counts["model_request_payload_hash_mismatch_count"],
        "generation_contract_hash_mismatch_count": counts["generation_contract_hash_mismatch_count"],
        "preprojection_anchor_mismatch_count": counts["preprojection_anchor_mismatch_count"],
        "cited_projection_hash_mismatch_count": counts["cited_projection_hash_mismatch_count"],
        "citation_set_projection_hash_mismatch_count": counts["citation_set_projection_hash_mismatch_count"],
        "final_mode_mapping_hash_mismatch_count": counts["final_mode_mapping_hash_mismatch_count"],
        "blocked_reason_set_mismatch_count": counts["blocked_reason_set_mismatch_count"],
        "final_answer_payload_hash_mismatch_count": counts["final_answer_payload_hash_mismatch_count"],
        "response_envelope_hash_mismatch_count": counts["response_envelope_hash_mismatch_count"],
        "serialized_output_hash_mismatch_count": counts["serialized_output_hash_mismatch_count"],
        "mismatch_count": mismatch_count,
        "family_metric_delta_zero": family_metric_delta_zero,
        "metric_delta": metric_deltas,
        "reference_run_label": reference_run_label,
        "candidate_run_label": candidate_run_label,
        "reference_checkpoint_ref": reference_candidate_id,
        "candidate_checkpoint_ref": candidate_candidate_id,
        "reference_eval_family": reference_report.get("report_meta", {}).get("eval_family"),
        "candidate_eval_family": candidate_report.get("report_meta", {}).get("eval_family"),
        "authoritative_rows": authoritative_rows,
        "mismatch_rows": mismatch_rows,
        "output_parity_authority_cleared": mismatch_count == 0 and family_metric_delta_zero,
    }
    report["report_hash"] = stable_hash({key: report[key] for key in report if key not in {"authoritative_rows", "mismatch_rows"}})
    return report


def render_markdown(report: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- run_id = `{report['run_id']}`",
        f"- family_id = `{report['family_id']}`",
        f"- question_count = `{report['question_count']}`",
        f"- mismatch_count = `{report['mismatch_count']}`",
        f"- family_metric_delta_zero = `{str(report['family_metric_delta_zero']).lower()}`",
        f"- output_parity_authority_cleared = `{str(report['output_parity_authority_cleared']).lower()}`",
        "",
        "## Mismatch Counts",
        "",
    ]
    for key in MISMATCH_COUNTER_KEYS:
        lines.append(f"- `{key}` = `{report[key]}`")
    lines.extend(["", "## Metric Delta", ""])
    for key, value in report["metric_delta"].items():
        lines.append(f"- `{key}` = `{value}`")
    lines.extend(["", "## Frontier Sample", ""])
    if not report["mismatch_rows"]:
        lines.append("- mismatch yok")
    else:
        for row in report["mismatch_rows"][:15]:
            lines.append(
                f"- `{row['question_id']}` stage `{row.get('first_divergence_stage')}` reason `{row.get('primary_reason')}`"
            )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ13 authoritative output parity report.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--family-id", required=True)
    parser.add_argument("--questions-path", type=Path, required=True)
    parser.add_argument("--reference-report", type=Path, required=True)
    parser.add_argument("--candidate-report", type=Path, required=True)
    parser.add_argument("--reference-rerun-report", type=Path)
    parser.add_argument("--candidate-rerun-report", type=Path)
    parser.add_argument("--reference-run-label", default="rc_g")
    parser.add_argument("--candidate-run-label", default="rc_j")
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--title", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = build_report(
        run_id=args.run_id,
        family_id=args.family_id,
        questions_path=args.questions_path,
        reference_report=load_json(args.reference_report),
        candidate_report=load_json(args.candidate_report),
        reference_run_label=args.reference_run_label,
        candidate_run_label=args.candidate_run_label,
        reference_rerun_report=load_json(args.reference_rerun_report) if args.reference_rerun_report else None,
        candidate_rerun_report=load_json(args.candidate_rerun_report) if args.candidate_rerun_report else None,
    )
    write_json(args.output_json, report)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(report, title=args.title), encoding="utf-8")
    return 0 if report["output_parity_authority_cleared"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
