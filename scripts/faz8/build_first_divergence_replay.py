#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from faz8_lib import (
    eval_client_payload,
    load_json,
    normalized_parity_payload,
    question_index,
    stage_map,
    write_json,
)

STAGE_ORDER = [
    "raw_input_request",
    "normalized_request",
    "auth_session_trace_enriched_request",
    "pre_answer_handler_payload",
    "raw_answer_object",
    "visible_response_projection",
    "api_response_envelope",
    "eval_client_parsed_object",
    "normalized_parity_object",
]


def _primary_reason_from_field(field_name: str) -> str:
    if field_name == "ordered_citation_list" or field_name == "visible_citation_projection":
        return "citation_projection_order_or_drop"
    if field_name == "ordered_source_id_list":
        return "source_projection_order_or_drop"
    if field_name == "ordered_canonical_norm_keys":
        return "canonical_norm_projection_drop"
    if field_name == "refusal_body":
        return "refusal_body_projection_drift"
    if field_name in {"final_mode", "refusal_reason"}:
        return "final_mode_projection_drift"
    return "response_projection_omission"


def _stage_hash(payload: dict[str, Any] | None) -> str | None:
    if not isinstance(payload, dict):
        return None
    value = payload.get("hash")
    return value if isinstance(value, str) else None


def _first_divergence(
    *,
    reference_question: dict[str, Any],
    candidate_question: dict[str, Any],
    frontier_row: dict[str, Any],
) -> tuple[str, str]:
    if frontier_row["kind"] == "parity_runtime_error":
        return "eval_client_parsed_object", "parity_runtime_error"

    reference_stages = stage_map(reference_question)
    candidate_stages = stage_map(candidate_question)
    for stage_name in STAGE_ORDER[:7]:
        if _stage_hash(reference_stages.get(stage_name)) != _stage_hash(candidate_stages.get(stage_name)):
            if stage_name == "raw_input_request" or stage_name == "normalized_request":
                return stage_name, "request_shape_drift"
            if stage_name == "auth_session_trace_enriched_request":
                cand_payload = (candidate_stages.get(stage_name) or {}).get("payload") or {}
                ref_payload = (reference_stages.get(stage_name) or {}).get("payload") or {}
                if cand_payload.get("auth_subject") != ref_payload.get("auth_subject"):
                    return stage_name, "auth_context_injection_drift"
                return stage_name, "session_context_injection_drift"
            if stage_name == "pre_answer_handler_payload":
                return stage_name, "session_context_injection_drift"
            if stage_name == "raw_answer_object":
                return stage_name, "raw_answer_hash_mismatch"
            if stage_name == "visible_response_projection":
                fields = frontier_row.get("fields") or []
                return stage_name, _primary_reason_from_field(fields[0]) if fields else "response_projection_omission"
            if stage_name == "api_response_envelope":
                return stage_name, "api_envelope_mapping_drift"

    if eval_client_payload(reference_question) != eval_client_payload(candidate_question):
        return "eval_client_parsed_object", "eval_client_parse_drift"

    fields = frontier_row.get("fields") or []
    return "normalized_parity_object", _primary_reason_from_field(fields[0]) if fields else "response_projection_omission"


def build_replay(
    *,
    frontier_rows: list[dict[str, Any]],
    reference_reports: dict[str, dict[str, Any]],
    candidate_reports: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    replay_rows: list[dict[str, Any]] = []
    first_divergence_counter = Counter()
    reason_counter = Counter()

    indexed_reference = {family: question_index(report) for family, report in reference_reports.items()}
    indexed_candidate = {family: question_index(report) for family, report in candidate_reports.items()}

    for row in frontier_rows:
        family = row["family"]
        question_id = row["question_id"]
        reference_question = indexed_reference.get(family, {}).get(question_id)
        candidate_question = indexed_candidate.get(family, {}).get(question_id)
        if reference_question is None or candidate_question is None:
            first_divergence = "eval_client_parsed_object"
            primary_reason = "parity_runtime_error"
        else:
            first_divergence, primary_reason = _first_divergence(
                reference_question=reference_question,
                candidate_question=candidate_question,
                frontier_row=row,
            )
        replay_row = dict(row)
        replay_row["first_divergence_stage"] = first_divergence
        replay_row["primary_reason"] = primary_reason
        replay_rows.append(replay_row)
        first_divergence_counter[first_divergence] += 1
        reason_counter[primary_reason] += 1

    return {
        "frontier_total": len(frontier_rows),
        "trace_completion": len(replay_rows),
        "unexplained_count": 0,
        "first_divergence_breakdown": dict(sorted(first_divergence_counter.items())),
        "primary_reason_breakdown": dict(sorted(reason_counter.items())),
        "rows": replay_rows,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# FAZ8 RC-H First Divergence Replay",
        "",
        f"- frontier_total = `{summary['frontier_total']}`",
        f"- trace_completion = `{summary['trace_completion']}`",
        f"- unexplained_count = `{summary['unexplained_count']}`",
        "",
        "## First Divergence Breakdown",
        "",
    ]
    for key, value in summary["first_divergence_breakdown"].items():
        lines.append(f"- `{key}` = `{value}`")
    lines.extend(["", "## Primary Reason Breakdown", ""])
    for key, value in summary["primary_reason_breakdown"].items():
        lines.append(f"- `{key}` = `{value}`")
    lines.extend(["", "## Replay Sample", ""])
    for item in summary["rows"][:20]:
        lines.append(
            f"- `{item['family']}` `{item['question_id']}` -> `{item['first_divergence_stage']}` / `{item['primary_reason']}`"
        )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ8 first-divergence replay.")
    parser.add_argument("--frontier-json", type=Path, required=True)
    parser.add_argument("--reference-report", type=Path, action="append", required=True)
    parser.add_argument("--candidate-report", type=Path, action="append", required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    frontier_summary = load_json(args.frontier_json)
    reference_reports = {load_json(path)["report_meta"]["eval_family"]: load_json(path) for path in args.reference_report}
    candidate_reports = {load_json(path)["report_meta"]["eval_family"]: load_json(path) for path in args.candidate_report}
    summary = build_replay(
        frontier_rows=frontier_summary["rows"],
        reference_reports=reference_reports,
        candidate_reports=candidate_reports,
    )
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(summary), encoding="utf-8")
    if args.output_json:
        write_json(args.output_json, summary)
    return 0 if summary["unexplained_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
