#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "api-gateway" / "src"))

from faz2a_hardening import canonicalize_source_id  # noqa: E402


def _load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _summary_metrics(report: dict[str, Any]) -> dict[str, float]:
    summary = report.get("summary", {})
    return {
        "citation_rate": float(summary.get("citation_rate", 0.0)),
        "correct_source_rate": float(summary.get("correct_source_rate", 0.0)),
        "hallucination_rate": float(summary.get("hallucination_rate", 0.0)),
        "refusal_accuracy": float(summary.get("refusal_accuracy", 0.0)),
    }


def _answer_contract(question: dict[str, Any]) -> dict[str, Any]:
    contract = question.get("answer_contract")
    return contract if isinstance(contract, dict) else {}


def _trace(question: dict[str, Any]) -> dict[str, Any]:
    trace = question.get("trace")
    return trace if isinstance(trace, dict) else {}


def normalize_question(question: dict[str, Any]) -> dict[str, Any]:
    answer_contract = _answer_contract(question)
    trace = _trace(question)
    final_mode = question.get("final_mode") or answer_contract.get("final_mode")
    answer_text = question.get("answer_text") or ""

    source_ids: list[str] = []
    primary = answer_contract.get("primary_source_id")
    if isinstance(primary, str) and primary.strip():
        source_ids.append(primary.strip())
    secondary = answer_contract.get("secondary_source_ids")
    if isinstance(secondary, list):
        source_ids.extend(item.strip() for item in secondary if isinstance(item, str) and item.strip())
    if not source_ids:
        source_ids = [item for item in question.get("cited_sources", []) if isinstance(item, str) and item.strip()]

    projection = (
        trace.get("hardening_diagnostics", {})
        .get("visible_citation_projection", {})
        .get("final_citations")
    )
    if not isinstance(projection, list):
        projection = question.get("cited_sources", [])

    refusal_reason = (
        answer_contract.get("unsupported_reason")
        or trace.get("final_reason")
        or question.get("final_reason")
    )

    return {
        "question_id": question.get("question_id"),
        "final_mode": final_mode,
        "answer_body": answer_text if final_mode != "refusal" else "",
        "refusal_body": answer_text if final_mode == "refusal" else "",
        "refusal_reason": refusal_reason,
        "ordered_citation_list": list(question.get("cited_sources", [])),
        "ordered_source_id_list": source_ids,
        "ordered_canonical_norm_keys": [
            canonicalize_source_id(item) or item for item in source_ids
        ],
        "visible_citation_projection": list(projection),
    }


def compare_reports(reference_report: dict[str, Any], candidate_report: dict[str, Any]) -> dict[str, Any]:
    ref_questions = {
        item["question_id"]: normalize_question(item)
        for item in reference_report.get("per_question", [])
        if isinstance(item, dict) and item.get("question_id")
    }
    cand_questions = {
        item["question_id"]: normalize_question(item)
        for item in candidate_report.get("per_question", [])
        if isinstance(item, dict) and item.get("question_id")
    }

    mismatches: list[dict[str, Any]] = []
    for question_id in sorted(set(ref_questions) | set(cand_questions)):
        reference = ref_questions.get(question_id)
        candidate = cand_questions.get(question_id)
        if reference is None or candidate is None:
            mismatches.append(
                {
                    "question_id": question_id,
                    "kind": "missing_question",
                    "reference_present": reference is not None,
                    "candidate_present": candidate is not None,
                }
            )
            continue

        differing_fields = [
            field_name
            for field_name in (
                "final_mode",
                "answer_body",
                "refusal_body",
                "refusal_reason",
                "ordered_citation_list",
                "ordered_source_id_list",
                "ordered_canonical_norm_keys",
                "visible_citation_projection",
            )
            if reference.get(field_name) != candidate.get(field_name)
        ]
        if differing_fields:
            mismatches.append(
                {
                    "question_id": question_id,
                    "kind": "normalized_output_mismatch",
                    "fields": differing_fields,
                    "reference": reference,
                    "candidate": candidate,
                }
            )

    reference_metrics = _summary_metrics(reference_report)
    candidate_metrics = _summary_metrics(candidate_report)
    metric_delta = {
        name: round(candidate_metrics[name] - reference_metrics[name], 10)
        for name in reference_metrics
    }

    return {
        "reference_eval_family": reference_report.get("report_meta", {}).get("eval_family"),
        "candidate_eval_family": candidate_report.get("report_meta", {}).get("eval_family"),
        "question_count": len(ref_questions),
        "mismatch_count": len(mismatches),
        "metric_delta": metric_delta,
        "family_metric_delta_zero": all(delta == 0 for delta in metric_delta.values()),
        "mismatches": mismatches,
    }


def render_markdown(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- mismatch_count = `{summary['mismatch_count']}`",
        f"- family_metric_delta_zero = `{str(summary['family_metric_delta_zero']).lower()}`",
        f"- question_count = `{summary['question_count']}`",
        "",
        "## Metric Delta",
        "",
    ]
    for metric_name, delta in summary["metric_delta"].items():
        lines.append(f"- `{metric_name}` = `{delta}`")

    lines.extend(["", "## Mismatch Sample", ""])
    if not summary["mismatches"]:
        lines.append("- mismatch yok")
    else:
        for mismatch in summary["mismatches"][:10]:
            lines.append(f"- `{mismatch['question_id']}` `{mismatch['kind']}`")
            if mismatch["kind"] == "normalized_output_mismatch":
                fields = ", ".join(mismatch["fields"])
                lines.append(f"  alanlar: {fields}")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ7 RC-H output parity report.")
    parser.add_argument("--reference-report", type=Path, required=True)
    parser.add_argument("--candidate-report", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--title", default="FAZ7 RC-H Output Parity Report")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    reference_report = _load_report(args.reference_report)
    candidate_report = _load_report(args.candidate_report)
    summary = compare_reports(reference_report, candidate_report)

    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(
        render_markdown(summary, title=args.title),
        encoding="utf-8",
    )
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return 0 if summary["mismatch_count"] == 0 and summary["family_metric_delta_zero"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
