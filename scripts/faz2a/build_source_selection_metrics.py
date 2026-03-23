#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "api-gateway" / "src"))

from faz2a_hardening import canonicalize_source_id  # noqa: E402


@dataclass(slots=True)
class MetricBreakdown:
    question_count: int
    retrieved_correct_source_at_k: float
    assembled_correct_source_present: float
    model_selected_correct_source: float
    whitelist_violation_rate: float
    law_scope_mismatch_rate: float
    temporal_mismatch_rate: float


def _safe_rate(hits: int, total: int) -> float:
    return round((hits / total), 4) if total else 0.0


def _normalize_source_list(values: list[str] | None) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        canonical = canonicalize_source_id(value)
        if not canonical or canonical in seen:
            continue
        normalized.append(canonical)
        seen.add(canonical)
    return normalized


def _report_label(report: dict[str, Any], fallback_path: Path) -> str:
    meta = report.get("report_meta", {})
    return str(meta.get("eval_family") or fallback_path.stem)


def compute_metric_breakdown(report: dict[str, Any]) -> MetricBreakdown:
    per_question = report.get("per_question", [])
    total = len(per_question)

    retrieved_hits = 0
    assembled_hits = 0
    selected_hits = 0
    whitelist_violations = 0
    law_scope_mismatches = 0
    temporal_mismatches = 0

    for item in per_question:
        expected_sources = _normalize_source_list(item.get("expected_sources"))
        trace = item.get("trace") or {}
        answer_contract = item.get("answer_contract") or {}

        retrieved_sources = _normalize_source_list(
            [
                chunk.get("source_id") or chunk.get("citation")
                for chunk in (trace.get("retrieval") or {}).get("pre_rerank_chunks", [])
            ]
        )
        assembled_sources = _normalize_source_list(
            (trace.get("context_assembly") or {}).get("allowed_source_whitelist", [])
        )
        primary_source_id = canonicalize_source_id(answer_contract.get("primary_source_id"))
        final_reason = item.get("final_reason") or answer_contract.get("unsupported_reason")

        if expected_sources and any(source in retrieved_sources for source in expected_sources):
            retrieved_hits += 1
        if expected_sources and any(source in assembled_sources for source in expected_sources):
            assembled_hits += 1
        if expected_sources and primary_source_id in expected_sources:
            selected_hits += 1
        if final_reason == "citation_out_of_whitelist":
            whitelist_violations += 1
        if final_reason == "law_scope_mismatch":
            law_scope_mismatches += 1
        if final_reason == "temporal_mismatch":
            temporal_mismatches += 1

    return MetricBreakdown(
        question_count=total,
        retrieved_correct_source_at_k=_safe_rate(retrieved_hits, total),
        assembled_correct_source_present=_safe_rate(assembled_hits, total),
        model_selected_correct_source=_safe_rate(selected_hits, total),
        whitelist_violation_rate=_safe_rate(whitelist_violations, total),
        law_scope_mismatch_rate=_safe_rate(law_scope_mismatches, total),
        temporal_mismatch_rate=_safe_rate(temporal_mismatches, total),
    )


def build_payload(report_paths: list[Path]) -> dict[str, Any]:
    reports: list[dict[str, Any]] = []
    overall_accumulator = {
        "question_count": 0,
        "retrieved_correct_source_at_k": 0.0,
        "assembled_correct_source_present": 0.0,
        "model_selected_correct_source": 0.0,
        "whitelist_violation_rate": 0.0,
        "law_scope_mismatch_rate": 0.0,
        "temporal_mismatch_rate": 0.0,
    }

    for report_path in report_paths:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        breakdown = compute_metric_breakdown(report)
        label = _report_label(report, report_path)
        report_entry = {
            "label": label,
            "report_path": str(report_path),
            **asdict(breakdown),
        }
        reports.append(report_entry)

        overall_accumulator["question_count"] += breakdown.question_count
        for key in (
            "retrieved_correct_source_at_k",
            "assembled_correct_source_present",
            "model_selected_correct_source",
            "whitelist_violation_rate",
            "law_scope_mismatch_rate",
            "temporal_mismatch_rate",
        ):
            overall_accumulator[key] += getattr(breakdown, key) * breakdown.question_count

    total_questions = overall_accumulator["question_count"]
    overall = {"question_count": total_questions}
    for key in (
        "retrieved_correct_source_at_k",
        "assembled_correct_source_present",
        "model_selected_correct_source",
        "whitelist_violation_rate",
        "law_scope_mismatch_rate",
        "temporal_mismatch_rate",
    ):
        overall[key] = round(
            overall_accumulator[key] / total_questions,
            4,
        ) if total_questions else 0.0

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reports": reports,
        "overall": overall,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# FAZ 2A Source Selection Metrics",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        "",
        "| set | n | retrieved@k | assembled_present | model_selected | whitelist_violation | law_scope_mismatch | temporal_mismatch |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for report in payload["reports"]:
        lines.append(
            "| {label} | {question_count} | {retrieved_correct_source_at_k:.1%} | "
            "{assembled_correct_source_present:.1%} | {model_selected_correct_source:.1%} | "
            "{whitelist_violation_rate:.1%} | {law_scope_mismatch_rate:.1%} | {temporal_mismatch_rate:.1%} |".format(
                **report
            )
        )

    overall = payload["overall"]
    lines.extend(
        [
            "",
            "## Overall",
            "",
            f"- question_count: `{overall['question_count']}`",
            f"- retrieved_correct_source_at_k: `{overall['retrieved_correct_source_at_k']:.1%}`",
            f"- assembled_correct_source_present: `{overall['assembled_correct_source_present']:.1%}`",
            f"- model_selected_correct_source: `{overall['model_selected_correct_source']:.1%}`",
            f"- whitelist_violation_rate: `{overall['whitelist_violation_rate']:.1%}`",
            f"- law_scope_mismatch_rate: `{overall['law_scope_mismatch_rate']:.1%}`",
            f"- temporal_mismatch_rate: `{overall['temporal_mismatch_rate']:.1%}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ2A source-selection metric breakdown.")
    parser.add_argument("--report", action="append", required=True, type=Path, help="Raw eval report path.")
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    payload = build_payload(args.report)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
