#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "api-gateway" / "src"))

from faz2a_hardening import (  # noqa: E402
    StructuredAnswerContract,
    TracePack,
    canonicalize_source_id,
    is_narrow_question_type,
)

REQUIRED_TRACE_KEYS = {
    "request_id",
    "timestamp",
    "question_raw",
    "question_normalized",
    "parsed_query",
    "law_scope_signal",
    "question_type",
    "target_date",
    "retrieval_top_k",
    "rerank_list",
    "assembled_evidence",
    "allowed_source_whitelist",
    "answer_contract",
    "model_cited_source_ids",
    "verifier_verdict",
    "final_mode",
    "final_reason",
}
LEGACY_TRACE_KEYS = {
    "query_signals",
    "retrieval",
    "context_assembly",
    "generation_outcome",
}
ALLOWED_TRACE_KEYS = REQUIRED_TRACE_KEYS | LEGACY_TRACE_KEYS


@dataclass(slots=True)
class ReportContext:
    path: Path
    label: str
    payload: dict[str, Any]


def _load_report(path: Path) -> ReportContext:
    payload = json.loads(path.read_text(encoding="utf-8"))
    meta = payload.get("report_meta", {})
    label = str(meta.get("eval_family") or path.stem)
    return ReportContext(path=path, label=label, payload=payload)


def _iter_questions(reports: list[ReportContext]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for report in reports:
        for item in report.payload.get("per_question", []):
            rows.append(
                {
                    "report_label": report.label,
                    "report_path": str(report.path),
                    **item,
                }
            )
    return rows


def _safe_pct(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _coverage_pct(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 1.0


def _trace_file_path(trace_dir: Path, request_id: str | None) -> Path | None:
    if not request_id:
        return None
    return trace_dir / f"{request_id}.json"


def _trace_validation(trace: dict[str, Any] | None) -> tuple[bool, list[str]]:
    if not isinstance(trace, dict):
        return False, ["missing_trace_object"]
    errors: list[str] = []
    missing = sorted(REQUIRED_TRACE_KEYS - set(trace))
    if missing:
        errors.append(f"missing_required_keys:{','.join(missing)}")
    extras = sorted(set(trace) - ALLOWED_TRACE_KEYS)
    if extras:
        errors.append(f"unexpected_keys:{','.join(extras)}")
    try:
        TracePack.model_validate(trace)
    except Exception as exc:  # pragma: no cover - pydantic exact text not stable
        errors.append(f"schema:{exc.__class__.__name__}")
    return not errors, errors


def _schema_validation(answer_contract: dict[str, Any] | None) -> tuple[bool, str | None]:
    if answer_contract is None:
        return False, "missing_answer_contract"
    try:
        StructuredAnswerContract.model_validate(answer_contract)
    except Exception as exc:  # pragma: no cover - pydantic exact text not stable
        return False, exc.__class__.__name__
    return True, None


def _normalize_list(values: list[str] | None) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        canonical = canonicalize_source_id(value)
        if not canonical or canonical in seen:
            continue
        normalized.append(canonical)
        seen.add(canonical)
    return normalized


def build_trace_index(rows: list[dict[str, Any]], trace_dir: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    matched_total = 0
    matched_traced = 0
    diagnostic_total = 0
    diagnostic_traced = 0
    unexpected_key_free = 0

    for row in rows:
        matched_total += 1
        trace = row.get("trace")
        trace_ok, trace_errors = _trace_validation(trace)
        request_id = (trace or {}).get("request_id") if isinstance(trace, dict) else None
        trace_path = _trace_file_path(trace_dir, request_id)
        trace_file_exists = bool(trace_path and trace_path.exists())
        has_trace = trace_ok and trace_file_exists
        if has_trace:
            matched_traced += 1
        if isinstance(trace, dict) and not (set(trace) - ALLOWED_TRACE_KEYS):
            unexpected_key_free += 1

        answer_contract = row.get("answer_contract") or {}
        verifier_status = answer_contract.get("verifier_status")
        final_mode = row.get("final_mode")
        final_reason = row.get("final_reason")
        is_diagnostic = (
            final_mode in {"blocked", "refusal"}
            or final_reason is not None
            or row.get("error") is not None
            or verifier_status in {"warn", "fail"}
        )
        if is_diagnostic:
            diagnostic_total += 1
            if has_trace:
                diagnostic_traced += 1

        entries.append(
            {
                "eval_family": row["report_label"],
                "question_id": row.get("question_id"),
                "request_id": request_id,
                "trace_present": has_trace,
                "trace_file": str(trace_path) if trace_path else None,
                "trace_errors": trace_errors,
                "final_mode": final_mode,
                "final_reason": final_reason,
                "error": row.get("error"),
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "trace_dir": str(trace_dir),
        "matched_eval": {
            "total": matched_total,
            "traced": matched_traced,
            "coverage_rate": _coverage_pct(matched_traced, matched_total),
            "unexpected_key_free_count": unexpected_key_free,
        },
        "diagnostic_subset": {
            "total": diagnostic_total,
            "traced": diagnostic_traced,
            "coverage_rate": _coverage_pct(diagnostic_traced, diagnostic_total),
        },
        "entries": entries,
    }


def _per_family_summary(report: ReportContext) -> dict[str, Any]:
    meta = report.payload.get("report_meta", {})
    summary = report.payload.get("summary", {})
    per_question = report.payload.get("per_question", [])
    return {
        "label": report.label,
        "question_count": len(per_question),
        "error_count": int(meta.get("error_count", 0)),
        "citation_rate": float(summary.get("citation_rate", 0.0)),
        "correct_source_rate": float(summary.get("correct_source_rate", 0.0)),
        "hallucination_rate": float(summary.get("hallucination_rate", 0.0)),
        "refusal_accuracy": float(summary.get("refusal_accuracy", 0.0)),
        "avg_response_time_ms": float(summary.get("avg_response_time_ms", 0.0)),
    }


def _external_whitelist_violation(row: dict[str, Any]) -> bool:
    trace = row.get("trace") or {}
    whitelist = set(_normalize_list(trace.get("allowed_source_whitelist")))
    cited = _normalize_list(row.get("cited_sources"))
    return any(source not in whitelist for source in cited)


def _claim_binding_violation(row: dict[str, Any]) -> bool:
    trace = row.get("trace") or {}
    if not is_narrow_question_type(str(trace.get("question_type") or "")):
        return False
    if row.get("final_mode") != "answer":
        return False
    answer_contract = row.get("answer_contract") or {}
    claim_units = answer_contract.get("claim_units") or []
    whitelist = set(_normalize_list(trace.get("allowed_source_whitelist")))
    if not claim_units:
        return True
    for claim in claim_units:
        source_id = canonicalize_source_id(claim.get("source_id"))
        excerpt = str(claim.get("source_excerpt") or "").strip()
        if not source_id or source_id not in whitelist or not excerpt:
            return True
    return False


def build_smoke_payload(reports: list[ReportContext], trace_index: dict[str, Any]) -> dict[str, Any]:
    rows = _iter_questions(reports)
    total = len(rows)

    schema_pass = 0
    schema_fail_entries: list[str] = []
    law_scope_answer_leaks = 0
    temporal_answer_leaks = 0
    whitelist_answer_leaks = 0
    narrow_claim_answer_leaks = 0
    narrow_question_total = 0
    narrow_question_with_claims = 0
    external_whitelist_violations = 0

    law_scope_counts: dict[str, int] = {}
    temporal_counts: dict[str, int] = {}
    citation_gate_counts: dict[str, int] = {}
    narrow_claim_counts: dict[str, int] = {}

    for row in rows:
        answer_contract = row.get("answer_contract")
        schema_ok, schema_error = _schema_validation(answer_contract)
        if schema_ok:
            schema_pass += 1
        else:
            schema_fail_entries.append(f"{row['report_label']}:{row.get('question_id')}:{schema_error}")

        final_mode = row.get("final_mode")
        final_reason = row.get("final_reason")
        if final_reason == "law_scope_mismatch":
            law_scope_counts[row["report_label"]] = law_scope_counts.get(row["report_label"], 0) + 1
            if final_mode == "answer":
                law_scope_answer_leaks += 1
        if final_reason in {"temporal_mismatch", "source_validity_unknown"}:
            temporal_counts[row["report_label"]] = temporal_counts.get(row["report_label"], 0) + 1
            if final_mode == "answer":
                temporal_answer_leaks += 1
        if final_reason == "citation_out_of_whitelist":
            citation_gate_counts[row["report_label"]] = citation_gate_counts.get(row["report_label"], 0) + 1
            if final_mode == "answer":
                whitelist_answer_leaks += 1
        if final_reason == "claim_support_missing":
            narrow_claim_counts[row["report_label"]] = narrow_claim_counts.get(row["report_label"], 0) + 1
            if final_mode == "answer":
                narrow_claim_answer_leaks += 1

        if _external_whitelist_violation(row):
            external_whitelist_violations += 1

        trace = row.get("trace") or {}
        if is_narrow_question_type(str(trace.get("question_type") or "")):
            narrow_question_total += 1
            claim_units = ((answer_contract or {}).get("claim_units") or [])
            if claim_units:
                narrow_question_with_claims += 1
        if _claim_binding_violation(row):
            narrow_claim_answer_leaks += 1

    family_rows = [_per_family_summary(report) for report in reports]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_questions": total,
        "trace_coverage_rate": trace_index["matched_eval"]["coverage_rate"],
        "diagnostic_trace_coverage_rate": trace_index["diagnostic_subset"]["coverage_rate"],
        "schema_validation_pass_rate": _safe_pct(schema_pass, total),
        "schema_fail_entries": schema_fail_entries,
        "external_whitelist_violation_rate": _safe_pct(external_whitelist_violations, total),
        "law_scope_answer_leaks": law_scope_answer_leaks,
        "temporal_answer_leaks": temporal_answer_leaks,
        "whitelist_answer_leaks": whitelist_answer_leaks,
        "narrow_claim_answer_leaks": narrow_claim_answer_leaks,
        "narrow_question_total": narrow_question_total,
        "narrow_question_with_claims": narrow_question_with_claims,
        "law_scope_counts": law_scope_counts,
        "temporal_counts": temporal_counts,
        "citation_gate_counts": citation_gate_counts,
        "narrow_claim_counts": narrow_claim_counts,
        "families": family_rows,
    }


def render_trace_pack_smoke(trace_index: dict[str, Any]) -> str:
    matched = trace_index["matched_eval"]
    diagnostic = trace_index["diagnostic_subset"]
    return "\n".join(
        [
            "# FAZ 2A Ek Sertleştirme — Trace Pack Smoke",
            "",
            f"- generated_at: `{trace_index['generated_at']}`",
            f"- matched_eval_total: `{matched['total']}`",
            f"- matched_eval_trace_coverage: `{matched['coverage_rate']:.1%}`",
            f"- diagnostic_total: `{diagnostic['total']}`",
            f"- diagnostic_trace_coverage: `{diagnostic['coverage_rate']:.1%}`",
            f"- unexpected_key_free_count: `{matched['unexpected_key_free_count']}`",
            "",
            "## Acceptance",
            "",
            f"- matched_eval_trace_coverage == 100%: `{'PASS' if matched['coverage_rate'] == 1.0 else 'FAIL'}`",
            f"- diagnostic_trace_coverage == 100%: `{'PASS' if diagnostic['coverage_rate'] == 1.0 else 'FAIL'}`",
            "",
        ]
    )


def render_answer_schema_validation(smoke: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# FAZ 2A Ek Sertleştirme — Answer Schema Validation",
            "",
            f"- generated_at: `{smoke['generated_at']}`",
            f"- total_questions: `{smoke['total_questions']}`",
            f"- schema_validation_pass_rate: `{smoke['schema_validation_pass_rate']:.1%}`",
            f"- schema_fail_count: `{len(smoke['schema_fail_entries'])}`",
            "",
            "## Acceptance",
            "",
            f"- schema_validation_pass_rate == 100%: `{'PASS' if smoke['schema_validation_pass_rate'] == 1.0 else 'FAIL'}`",
            "",
            "## Failing Entries",
            "",
            *([f"- `{entry}`" for entry in smoke["schema_fail_entries"]] or ["- none"]),
            "",
        ]
    )


def _render_reason_delta(title: str, rate_label: str, counts: dict[str, int], leak_count: int) -> str:
    total = sum(counts.values())
    lines = [
        f"# {title}",
        "",
        f"- total_trigger_count: `{total}`",
        f"- {rate_label}: `{leak_count}`",
        "",
        "## By Family",
        "",
    ]
    if counts:
        for family, count in sorted(counts.items()):
            lines.append(f"- `{family}`: `{count}`")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def render_smoke_summary(smoke: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# FAZ 2A Ek Sertleştirme — Smoke",
            "",
            f"- generated_at: `{smoke['generated_at']}`",
            f"- trace_coverage_rate: `{smoke['trace_coverage_rate']:.1%}`",
            f"- diagnostic_trace_coverage_rate: `{smoke['diagnostic_trace_coverage_rate']:.1%}`",
            f"- schema_validation_pass_rate: `{smoke['schema_validation_pass_rate']:.1%}`",
            f"- external_whitelist_violation_rate: `{smoke['external_whitelist_violation_rate']:.1%}`",
            f"- law_scope_answer_leaks: `{smoke['law_scope_answer_leaks']}`",
            f"- temporal_answer_leaks: `{smoke['temporal_answer_leaks']}`",
            f"- whitelist_answer_leaks: `{smoke['whitelist_answer_leaks']}`",
            f"- narrow_claim_answer_leaks: `{smoke['narrow_claim_answer_leaks']}`",
            f"- narrow_question_claim_coverage: `{_safe_pct(smoke['narrow_question_with_claims'], smoke['narrow_question_total']):.1%}`",
            "",
            "## Acceptance",
            "",
            f"- whitelist_violation_rate == 0: `{'PASS' if smoke['external_whitelist_violation_rate'] == 0.0 else 'FAIL'}`",
            f"- matched_eval_trace_coverage == 100%: `{'PASS' if smoke['trace_coverage_rate'] == 1.0 else 'FAIL'}`",
            f"- diagnostic_trace_coverage == 100%: `{'PASS' if smoke['diagnostic_trace_coverage_rate'] == 1.0 else 'FAIL'}`",
            f"- schema_validation_pass_rate == 100%: `{'PASS' if smoke['schema_validation_pass_rate'] == 1.0 else 'FAIL'}`",
            f"- law_scope answer leaks == 0: `{'PASS' if smoke['law_scope_answer_leaks'] == 0 else 'FAIL'}`",
            f"- temporal answer leaks == 0: `{'PASS' if smoke['temporal_answer_leaks'] == 0 else 'FAIL'}`",
            f"- narrow claim answer leaks == 0: `{'PASS' if smoke['narrow_claim_answer_leaks'] == 0 else 'FAIL'}`",
            "",
        ]
    )


def render_family_eval(reports: list[ReportContext], smoke: dict[str, Any], source_selection: dict[str, Any]) -> str:
    lines = [
        "# FAZ 2A Ek Sertleştirme — Family Eval",
        "",
        "| set | n | error | citation | correct_source | hallucination | refusal | avg_latency_ms |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for report in reports:
        family = _per_family_summary(report)
        lines.append(
            "| {label} | {question_count} | {error_count} | {citation_rate:.1%} | {correct_source_rate:.1%} | {hallucination_rate:.1%} | {refusal_accuracy:.1%} | {avg_response_time_ms:.0f} |".format(
                **family
            )
        )

    lines.extend(
        [
            "",
            "## Source Selection Breakdown",
            "",
            "| set | retrieved@k | assembled_present | model_selected | whitelist_violation | law_scope_mismatch | temporal_mismatch |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for report in source_selection.get("reports", []):
        lines.append(
            "| {label} | {retrieved_correct_source_at_k:.1%} | {assembled_correct_source_present:.1%} | {model_selected_correct_source:.1%} | {whitelist_violation_rate:.1%} | {law_scope_mismatch_rate:.1%} | {temporal_mismatch_rate:.1%} |".format(
                **report
            )
        )

    lines.extend(
        [
            "",
            "## Smoke Gate Snapshot",
            "",
            f"- trace_coverage_rate: `{smoke['trace_coverage_rate']:.1%}`",
            f"- schema_validation_pass_rate: `{smoke['schema_validation_pass_rate']:.1%}`",
            f"- external_whitelist_violation_rate: `{smoke['external_whitelist_violation_rate']:.1%}`",
            f"- law_scope_answer_leaks: `{smoke['law_scope_answer_leaks']}`",
            f"- temporal_answer_leaks: `{smoke['temporal_answer_leaks']}`",
            f"- narrow_claim_answer_leaks: `{smoke['narrow_claim_answer_leaks']}`",
            "",
        ]
    )
    return "\n".join(lines)


def render_final_report(reports: list[ReportContext], smoke: dict[str, Any], source_selection: dict[str, Any]) -> str:
    all_acceptance_pass = all(
        [
            smoke["external_whitelist_violation_rate"] == 0.0,
            smoke["trace_coverage_rate"] == 1.0,
            smoke["diagnostic_trace_coverage_rate"] == 1.0,
            smoke["schema_validation_pass_rate"] == 1.0,
            smoke["law_scope_answer_leaks"] == 0,
            smoke["temporal_answer_leaks"] == 0,
            smoke["narrow_claim_answer_leaks"] == 0,
        ]
    )
    lines = [
        "# FAZ 2A Ek Sertleştirme Sonuç Raporu",
        "",
        f"Tarih: {datetime.now(timezone.utc).date().isoformat()}",
        "",
        "## Sonuç",
        "",
        f"- karar: `{'PASS' if all_acceptance_pass else 'FAIL'}`",
        f"- ana yön değişmedi: `retrieval/source-precision/re-qualification hardening`",
        f"- yeni fine-tune / yeni promotion dalgası: `yapılmadı`",
        "",
        "## Kabul Kriterleri",
        "",
        f"- whitelist_violation_rate == 0: `{'PASS' if smoke['external_whitelist_violation_rate'] == 0.0 else 'FAIL'}`",
        f"- matched eval trace coverage == 100%: `{'PASS' if smoke['trace_coverage_rate'] == 1.0 else 'FAIL'}`",
        f"- warn/fail/blocked/refusal trace coverage == 100%: `{'PASS' if smoke['diagnostic_trace_coverage_rate'] == 1.0 else 'FAIL'}`",
        f"- schema validation pass rate == 100%: `{'PASS' if smoke['schema_validation_pass_rate'] == 1.0 else 'FAIL'}`",
        f"- law-scope mismatch answer leak == 0: `{'PASS' if smoke['law_scope_answer_leaks'] == 0 else 'FAIL'}`",
        f"- temporal mismatch/source_validity_unknown answer leak == 0: `{'PASS' if smoke['temporal_answer_leaks'] == 0 else 'FAIL'}`",
        f"- narrow-claim unsupported answer leak == 0: `{'PASS' if smoke['narrow_claim_answer_leaks'] == 0 else 'FAIL'}`",
        "",
        "## Family Sonuçları",
        "",
    ]
    for report in reports:
        family = _per_family_summary(report)
        lines.append(
            "- `{label}`: citation `{citation_rate:.1%}`, correct_source `{correct_source_rate:.1%}`, hallucination `{hallucination_rate:.1%}`, refusal `{refusal_accuracy:.1%}`, error `{error_count}`".format(
                **family
            )
        )

    overall = source_selection.get("overall", {})
    lines.extend(
        [
            "",
            "## Source-Selection Ayrıştırması",
            "",
            f"- retrieved_correct_source_at_k: `{overall.get('retrieved_correct_source_at_k', 0.0):.1%}`",
            f"- assembled_correct_source_present: `{overall.get('assembled_correct_source_present', 0.0):.1%}`",
            f"- model_selected_correct_source: `{overall.get('model_selected_correct_source', 0.0):.1%}`",
            f"- whitelist_violation_rate: `{overall.get('whitelist_violation_rate', 0.0):.1%}`",
            f"- law_scope_mismatch_rate: `{overall.get('law_scope_mismatch_rate', 0.0):.1%}`",
            f"- temporal_mismatch_rate: `{overall.get('temporal_mismatch_rate', 0.0):.1%}`",
            "",
            "## Kapanış",
            "",
            (
                "- FAZ 2A sonrası zorunlu ek sertleştirme paketi tamamlandı."
                if all_acceptance_pass
                else "- FAZ 2A sonrası zorunlu ek sertleştirme paketi acceptance gate'ini tam geçmedi."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ2A extra hardening report pack.")
    parser.add_argument("--report", action="append", required=True, type=Path)
    parser.add_argument("--trace-dir", type=Path, required=True)
    parser.add_argument("--source-selection-json", type=Path, required=True)
    parser.add_argument("--output-trace-index", type=Path, required=True)
    parser.add_argument("--output-trace-pack-smoke", type=Path, required=True)
    parser.add_argument("--output-answer-schema-validation", type=Path, required=True)
    parser.add_argument("--output-law-scope-delta", type=Path, required=True)
    parser.add_argument("--output-temporal-delta", type=Path, required=True)
    parser.add_argument("--output-citation-gate-delta", type=Path, required=True)
    parser.add_argument("--output-narrow-claim-delta", type=Path, required=True)
    parser.add_argument("--output-smoke", type=Path, required=True)
    parser.add_argument("--output-family-eval", type=Path, required=True)
    parser.add_argument("--output-final-report", type=Path, required=True)
    args = parser.parse_args()

    reports = [_load_report(path) for path in args.report]
    rows = _iter_questions(reports)
    trace_index = build_trace_index(rows, args.trace_dir)
    smoke = build_smoke_payload(reports, trace_index)
    source_selection = json.loads(args.source_selection_json.read_text(encoding="utf-8"))

    outputs: list[tuple[Path, str]] = [
        (args.output_trace_index, json.dumps(trace_index, ensure_ascii=False, indent=2) + "\n"),
        (args.output_trace_pack_smoke, render_trace_pack_smoke(trace_index)),
        (args.output_answer_schema_validation, render_answer_schema_validation(smoke)),
        (
            args.output_law_scope_delta,
            _render_reason_delta(
                "FAZ 2A Ek Sertleştirme — Law Scope Validator Delta",
                "answer_leak_count",
                smoke["law_scope_counts"],
                smoke["law_scope_answer_leaks"],
            ),
        ),
        (
            args.output_temporal_delta,
            _render_reason_delta(
                "FAZ 2A Ek Sertleştirme — Temporal Validity Delta",
                "answer_leak_count",
                smoke["temporal_counts"],
                smoke["temporal_answer_leaks"],
            ),
        ),
        (
            args.output_citation_gate_delta,
            _render_reason_delta(
                "FAZ 2A Ek Sertleştirme — Citation Gate Delta",
                "answer_leak_count",
                smoke["citation_gate_counts"],
                smoke["whitelist_answer_leaks"],
            ),
        ),
        (
            args.output_narrow_claim_delta,
            _render_reason_delta(
                "FAZ 2A Ek Sertleştirme — Narrow Claim Binding Delta",
                "answer_leak_count",
                smoke["narrow_claim_counts"],
                smoke["narrow_claim_answer_leaks"],
            ),
        ),
        (args.output_smoke, render_smoke_summary(smoke)),
        (args.output_family_eval, render_family_eval(reports, smoke, source_selection)),
        (args.output_final_report, render_final_report(reports, smoke, source_selection)),
    ]

    for path, content in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
