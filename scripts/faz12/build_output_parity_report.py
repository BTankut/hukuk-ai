#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz12_lib import (  # noqa: E402
    POST_PREPROJECTION_SURFACES,
    first_divergence,
    load_json,
    metric_delta,
    parity_fields,
    preprojection_hash,
    primary_reason,
    question_bank_index,
    question_index,
    runtime_error_row,
    stable_hash,
    write_json,
)


def build_report(
    *,
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
    mismatch_rows: list[dict[str, Any]] = []
    effective_reference_rows: list[dict[str, Any]] = []
    effective_candidate_rows: list[dict[str, Any]] = []

    for question_id, bank_row in bank_index.items():
        ordinal_index = int(bank_row["ordinal_index"])
        reference_question = reference_first_run.get(question_id)
        candidate_question = candidate_first_run.get(question_id)

        reference_runtime_error, reference_error_type = runtime_error_row(reference_question)
        candidate_runtime_error, candidate_error_type = runtime_error_row(candidate_question)

        effective_reference_question = (
            reference_rerun.get(question_id)
            if reference_runtime_error and question_id in reference_rerun
            else reference_question
        )
        effective_candidate_question = (
            candidate_rerun.get(question_id)
            if candidate_runtime_error and question_id in candidate_rerun
            else candidate_question
        )

        reference_error_rerun_used = int(reference_runtime_error and question_id in reference_rerun)
        candidate_error_rerun_used = int(candidate_runtime_error and question_id in candidate_rerun)
        effective_view_used = int(reference_error_rerun_used or candidate_error_rerun_used)

        effective_reference_runtime_error, effective_reference_error_type = runtime_error_row(effective_reference_question)
        effective_candidate_runtime_error, effective_candidate_error_type = runtime_error_row(effective_candidate_question)
        counts["reference_runtime_error_count"] += int(effective_reference_runtime_error)
        counts["candidate_runtime_error_count"] += int(effective_candidate_runtime_error)

        reference_fields = parity_fields(effective_reference_question or {})
        candidate_fields = parity_fields(effective_candidate_question or {})

        row = {
            "family_id": family_id,
            "question_id": question_id,
            "ordinal_index": ordinal_index,
            "reference_candidate_pair": [reference_run_label, candidate_run_label],
            "reference_first_run_authoritative": True,
            "candidate_first_run_authoritative": True,
            "reference_runtime_error": int(effective_reference_runtime_error),
            "candidate_runtime_error": int(effective_candidate_runtime_error),
            "reference_error_rerun_used": reference_error_rerun_used,
            "candidate_error_rerun_used": candidate_error_rerun_used,
            "effective_view_used": effective_view_used,
            "preprojection_hash": reference_fields.get("preprojection_hash"),
            "first_failing_surface": None,
            "first_divergence_stage": None,
            "primary_reason": None,
            "reference_error_type": effective_reference_error_type,
            "candidate_error_type": effective_candidate_error_type,
            "reference_fields": reference_fields,
            "candidate_fields": candidate_fields,
        }

        counts["reference_error_rerun_row_count"] += reference_error_rerun_used
        counts["candidate_error_rerun_row_count"] += candidate_error_rerun_used

        preprojection_anchor_mismatch = int(
            preprojection_hash(effective_reference_question or {}) != preprojection_hash(effective_candidate_question or {})
        )
        cited_projection_hash_mismatch = int(
            reference_fields["cited_projection_hash"] != candidate_fields["cited_projection_hash"]
        )
        citation_set_projection_hash_mismatch = int(
            reference_fields["citation_set_projection_hash"] != candidate_fields["citation_set_projection_hash"]
        )
        final_mode_mapping_hash_mismatch = int(
            reference_fields["final_mode_mapping_hash"] != candidate_fields["final_mode_mapping_hash"]
        )
        final_answer_payload_hash_mismatch = int(
            reference_fields["final_answer_payload_hash"] != candidate_fields["final_answer_payload_hash"]
        )
        response_envelope_hash_mismatch = int(
            reference_fields["response_envelope_hash"] != candidate_fields["response_envelope_hash"]
        )
        serialized_output_hash_mismatch = int(
            reference_fields["serialized_output_hash"] != candidate_fields["serialized_output_hash"]
        )
        answer_body_hash_mismatch = int(
            reference_fields["answer_body_hash"] != candidate_fields["answer_body_hash"]
        )
        citation_body_hash_mismatch = int(
            reference_fields["citation_body_hash"] != candidate_fields["citation_body_hash"]
        )
        refusal_body_hash_mismatch = int(
            reference_fields["refusal_body_hash"] != candidate_fields["refusal_body_hash"]
        )
        blocked_reason_set_mismatch = int(
            reference_fields["blocked_reason_set"] != candidate_fields["blocked_reason_set"]
        )

        row.update(
            {
                "preprojection_anchor_mismatch": preprojection_anchor_mismatch,
                "cited_projection_hash_mismatch": cited_projection_hash_mismatch,
                "citation_set_projection_hash_mismatch": citation_set_projection_hash_mismatch,
                "final_mode_mapping_hash_mismatch": final_mode_mapping_hash_mismatch,
                "final_answer_payload_hash_mismatch": final_answer_payload_hash_mismatch,
                "response_envelope_hash_mismatch": response_envelope_hash_mismatch,
                "serialized_output_hash_mismatch": serialized_output_hash_mismatch,
                "answer_body_hash_mismatch": answer_body_hash_mismatch,
                "citation_body_hash_mismatch": citation_body_hash_mismatch,
                "refusal_body_hash_mismatch": refusal_body_hash_mismatch,
                "blocked_reason_set_mismatch": blocked_reason_set_mismatch,
            }
        )

        for counter_name in (
            "preprojection_anchor_mismatch",
            "cited_projection_hash_mismatch",
            "citation_set_projection_hash_mismatch",
            "final_mode_mapping_hash_mismatch",
            "final_answer_payload_hash_mismatch",
            "response_envelope_hash_mismatch",
            "serialized_output_hash_mismatch",
            "answer_body_hash_mismatch",
            "citation_body_hash_mismatch",
            "refusal_body_hash_mismatch",
            "blocked_reason_set_mismatch",
        ):
            counts[f"{counter_name}_count"] += int(row[counter_name])

        row_mismatch = any(
            [
                preprojection_anchor_mismatch,
                cited_projection_hash_mismatch,
                citation_set_projection_hash_mismatch,
                final_mode_mapping_hash_mismatch,
                final_answer_payload_hash_mismatch,
                response_envelope_hash_mismatch,
                serialized_output_hash_mismatch,
                answer_body_hash_mismatch,
                citation_body_hash_mismatch,
                refusal_body_hash_mismatch,
                blocked_reason_set_mismatch,
                effective_candidate_runtime_error,
            ]
        )
        if row_mismatch:
            row["first_failing_surface"] = first_divergence(reference_fields, candidate_fields) or (
                "candidate_runtime_error" if effective_candidate_runtime_error else "reference_runtime_error"
            )
            row["first_divergence_stage"] = row["first_failing_surface"]
            row["primary_reason"] = (
                "unexplained_post_preprojection_drift"
                if effective_candidate_runtime_error or effective_reference_runtime_error
                else primary_reason(
                    reference_fields=reference_fields,
                    candidate_fields=candidate_fields,
                    first_divergence_stage=row["first_divergence_stage"],
                )
            )
            mismatch_rows.append(row)

        if isinstance(effective_reference_question, dict):
            effective_reference_rows.append(effective_reference_question)
        if isinstance(effective_candidate_question, dict):
            effective_candidate_rows.append(effective_candidate_question)

    deltas = metric_delta(effective_reference_rows, effective_candidate_rows)
    family_metric_delta_zero = all(delta == 0 for delta in deltas.values())

    report = {
        "family_id": family_id,
        "question_count": len(bank_index),
        "reference_runtime_error_count": counts["reference_runtime_error_count"],
        "candidate_runtime_error_count": counts["candidate_runtime_error_count"],
        "reference_error_rerun_row_count": counts["reference_error_rerun_row_count"],
        "candidate_error_rerun_row_count": counts["candidate_error_rerun_row_count"],
        "preprojection_anchor_mismatch_count": counts["preprojection_anchor_mismatch_count"],
        "cited_projection_hash_mismatch_count": counts["cited_projection_hash_mismatch_count"],
        "citation_set_projection_hash_mismatch_count": counts["citation_set_projection_hash_mismatch_count"],
        "final_mode_mapping_hash_mismatch_count": counts["final_mode_mapping_hash_mismatch_count"],
        "final_answer_payload_hash_mismatch_count": counts["final_answer_payload_hash_mismatch_count"],
        "response_envelope_hash_mismatch_count": counts["response_envelope_hash_mismatch_count"],
        "serialized_output_hash_mismatch_count": counts["serialized_output_hash_mismatch_count"],
        "answer_body_hash_mismatch_count": counts["answer_body_hash_mismatch_count"],
        "citation_body_hash_mismatch_count": counts["citation_body_hash_mismatch_count"],
        "refusal_body_hash_mismatch_count": counts["refusal_body_hash_mismatch_count"],
        "blocked_reason_set_mismatch_count": counts["blocked_reason_set_mismatch_count"],
        "family_metric_delta_zero": family_metric_delta_zero,
        "metric_delta": deltas,
        "reference_checkpoint_ref": reference_report.get("report_meta", {}).get("checkpoint_ref"),
        "candidate_checkpoint_ref": candidate_report.get("report_meta", {}).get("checkpoint_ref"),
        "reference_eval_family": reference_report.get("report_meta", {}).get("eval_family"),
        "candidate_eval_family": candidate_report.get("report_meta", {}).get("eval_family"),
        "reference_run_label": reference_run_label,
        "candidate_run_label": candidate_run_label,
        "parity_rows": mismatch_rows,
        "parity_frontier_count": len(mismatch_rows),
        "output_parity_reopened": (
            counts["preprojection_anchor_mismatch_count"] == 0
            and counts["cited_projection_hash_mismatch_count"] == 0
            and counts["citation_set_projection_hash_mismatch_count"] == 0
            and counts["final_mode_mapping_hash_mismatch_count"] == 0
            and counts["final_answer_payload_hash_mismatch_count"] == 0
            and counts["response_envelope_hash_mismatch_count"] == 0
            and counts["serialized_output_hash_mismatch_count"] == 0
            and counts["answer_body_hash_mismatch_count"] == 0
            and counts["citation_body_hash_mismatch_count"] == 0
            and counts["refusal_body_hash_mismatch_count"] == 0
            and counts["blocked_reason_set_mismatch_count"] == 0
            and family_metric_delta_zero
            and counts["candidate_runtime_error_count"] == 0
        ),
    }
    report["report_hash"] = stable_hash(
        {
            key: report[key]
            for key in report
            if key not in {"parity_rows"}
        }
    )
    return report


def render_markdown(report: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- family_id = `{report['family_id']}`",
        f"- question_count = `{report['question_count']}`",
        f"- reference_runtime_error_count = `{report['reference_runtime_error_count']}`",
        f"- candidate_runtime_error_count = `{report['candidate_runtime_error_count']}`",
        f"- reference_error_rerun_row_count = `{report['reference_error_rerun_row_count']}`",
        f"- candidate_error_rerun_row_count = `{report['candidate_error_rerun_row_count']}`",
        f"- family_metric_delta_zero = `{str(report['family_metric_delta_zero']).lower()}`",
        f"- output_parity_reopened = `{str(report['output_parity_reopened']).lower()}`",
        "",
        "## Mismatch Counts",
        "",
    ]
    for key in (
        "preprojection_anchor_mismatch_count",
        "cited_projection_hash_mismatch_count",
        "citation_set_projection_hash_mismatch_count",
        "final_mode_mapping_hash_mismatch_count",
        "final_answer_payload_hash_mismatch_count",
        "response_envelope_hash_mismatch_count",
        "serialized_output_hash_mismatch_count",
        "answer_body_hash_mismatch_count",
        "citation_body_hash_mismatch_count",
        "refusal_body_hash_mismatch_count",
        "blocked_reason_set_mismatch_count",
    ):
        lines.append(f"- `{key}` = `{report[key]}`")

    lines.extend(["", "## Metric Delta", ""])
    for key, value in report["metric_delta"].items():
        lines.append(f"- `{key}` = `{value}`")

    lines.extend(["", "## Frontier Sample", ""])
    if not report["parity_rows"]:
        lines.append("- parity mismatch yok")
    else:
        for row in report["parity_rows"][:15]:
            lines.append(
                f"- `{row['question_id']}` stage `{row['first_divergence_stage']}` reason `{row['primary_reason']}`"
            )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ12 per-family output parity report.")
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
    return 0 if report["output_parity_reopened"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
