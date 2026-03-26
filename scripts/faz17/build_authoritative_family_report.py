#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz17_lib import load_json, stable_hash, write_json


COUNT_KEYS = (
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
    "answer_body_hash_mismatch_count",
    "citation_body_hash_mismatch_count",
    "refusal_body_hash_mismatch_count",
)


def _body_counts(authoritative_rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "answer_body_hash_mismatch_count": sum(
            int(row.get("answer_body_hash") != row.get("reference_answer_body_hash")) for row in authoritative_rows
        ),
        "citation_body_hash_mismatch_count": sum(
            int(row.get("citation_body_hash") != row.get("reference_citation_body_hash")) for row in authoritative_rows
        ),
        "refusal_body_hash_mismatch_count": sum(
            int(row.get("refusal_body_hash") != row.get("reference_refusal_body_hash")) for row in authoritative_rows
        ),
    }


def build_report(source_report: dict[str, Any]) -> dict[str, Any]:
    authoritative_rows = list(source_report.get("authoritative_rows") or [])
    body_counts = _body_counts(authoritative_rows)
    runtime_error_count = int(source_report.get("reference_runtime_error_count", 0)) + int(
        source_report.get("candidate_runtime_error_count", 0)
    )
    mismatch_rows = []
    authoritative_by_question = {str(row.get("question_id")): row for row in authoritative_rows}
    for row in source_report.get("mismatch_rows") or []:
        enriched = dict(row)
        authoritative_row = authoritative_by_question.get(str(row.get("question_id")), {})
        enriched["answer_body_hash_mismatch"] = int(
            authoritative_row.get("answer_body_hash") != authoritative_row.get("reference_answer_body_hash")
        )
        enriched["citation_body_hash_mismatch"] = int(
            authoritative_row.get("citation_body_hash") != authoritative_row.get("reference_citation_body_hash")
        )
        enriched["refusal_body_hash_mismatch"] = int(
            authoritative_row.get("refusal_body_hash") != authoritative_row.get("reference_refusal_body_hash")
        )
        mismatch_rows.append(enriched)

    report = {
        "run_id": str(source_report.get("run_id")),
        "family_id": str(source_report.get("family_id")),
        "question_count": int(source_report.get("question_count", 0)),
        "runtime_error_count": runtime_error_count,
        "mismatch_count": int(source_report.get("mismatch_count", 0)),
        "family_metric_delta_zero": bool(source_report.get("family_metric_delta_zero")),
        "metric_delta": dict(source_report.get("metric_delta") or {}),
        "reference_checkpoint_ref": source_report.get("reference_checkpoint_ref"),
        "candidate_checkpoint_ref": source_report.get("candidate_checkpoint_ref"),
        "reference_eval_family": source_report.get("reference_eval_family"),
        "candidate_eval_family": source_report.get("candidate_eval_family"),
        "reference_run_label": source_report.get("reference_run_label"),
        "candidate_run_label": source_report.get("candidate_run_label"),
        "mismatch_rows": mismatch_rows,
        "authoritative_rows": authoritative_rows,
    }
    for key in COUNT_KEYS:
        if key in body_counts:
            report[key] = body_counts[key]
        else:
            report[key] = int(source_report.get(key, 0))

    report["gate_pass"] = (
        report["runtime_error_count"] == 0
        and report["mismatch_count"] == 0
        and report["family_metric_delta_zero"] is True
        and all(int(report[key]) == 0 for key in COUNT_KEYS)
    )
    report["report_hash"] = stable_hash(
        {key: value for key, value in report.items() if key not in {"mismatch_rows", "authoritative_rows"}}
    )
    return report


def render_markdown(report: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- family_id = `{report['family_id']}`",
        f"- question_count = `{report['question_count']}`",
        f"- runtime_error_count = `{report['runtime_error_count']}`",
        f"- mismatch_count = `{report['mismatch_count']}`",
        f"- family_metric_delta_zero = `{str(report['family_metric_delta_zero']).lower()}`",
        f"- gate_pass = `{str(report['gate_pass']).lower()}`",
        "",
    ]
    for key in COUNT_KEYS:
        lines.append(f"- `{key}` = `{report[key]}`")
    lines.extend(["", "## Metric Delta", ""])
    for key, value in sorted((report.get("metric_delta") or {}).items()):
        lines.append(f"- `{key}` = `{value}`")
    lines.extend(["", "## Frontier Sample", ""])
    if not report["mismatch_rows"]:
        lines.append("- mismatch yok")
    else:
        for row in report["mismatch_rows"][:15]:
            lines.append(
                f"- `{row['question_id']}` stage `{row.get('first_divergence_stage')}` "
                f"reason `{row.get('primary_reason')}`"
            )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ17 authoritative family report from frozen pair evidence.")
    parser.add_argument("--source-report-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--title", required=True)
    args = parser.parse_args()

    report = build_report(load_json(args.source_report_json))
    write_json(args.output_json, report)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(report, title=args.title), encoding="utf-8")
    return 0 if report["gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
