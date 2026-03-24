#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from rc_g_offline_lib import load_question_map, load_report_rows, question_result_to_row, replay_rc_g_row


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify FAZ3 blocker invariance on RC-G.")
    parser.add_argument("--blocker-pack-jsonl", required=True, type=Path)
    parser.add_argument("--faz1-questions", required=True, type=Path)
    parser.add_argument("--v2-questions", required=True, type=Path)
    parser.add_argument("--v3-questions", required=True, type=Path)
    parser.add_argument("--faz1-rc-a", required=True, type=Path)
    parser.add_argument("--v2-rc-a", required=True, type=Path)
    parser.add_argument("--v3-rc-a", required=True, type=Path)
    parser.add_argument("--faz1-rc-d", required=True, type=Path)
    parser.add_argument("--v2-rc-d", required=True, type=Path)
    parser.add_argument("--v3-rc-d", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def render_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# FAZ 6 RC-G Blocker Invariance Rerun",
        "",
        f"- false_refusal_after_guardrail: `{summary['false_refusal_after_guardrail']}`",
        f"- true_guardrail_block: `{summary['true_guardrail_block']}`",
        f"- whitelist_violation_leak_count: `{summary['whitelist_violation_leak_count']}`",
        f"- temporal_answer_leak_count: `{summary['temporal_answer_leak_count']}`",
        f"- law_scope_answer_leak_count: `{summary['law_scope_answer_leak_count']}`",
        f"- claim_binding_answer_leak_count: `{summary['claim_binding_answer_leak_count']}`",
        f"- trace_coverage_rate: `{summary['trace_coverage_rate'] * 100:.1f}%`",
        f"- schema_validation_pass_rate: `{summary['schema_validation_pass_rate'] * 100:.1f}%`",
        f"- overall_pass: `{str(summary['overall_pass']).lower()}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    blocker_rows = load_jsonl(args.blocker_pack_jsonl)
    question_maps = {
        "faz1-50": load_question_map(args.faz1_questions),
        "v2-95": load_question_map(args.v2_questions),
        "v3-170": load_question_map(args.v3_questions),
    }
    rc_a_reports = {
        "faz1-50": load_report_rows(args.faz1_rc_a),
        "v2-95": load_report_rows(args.v2_rc_a),
        "v3-170": load_report_rows(args.v3_rc_a),
    }
    rc_d_reports = {
        "faz1-50": load_report_rows(args.faz1_rc_d),
        "v2-95": load_report_rows(args.v2_rc_d),
        "v3-170": load_report_rows(args.v3_rc_d),
    }

    false_refusal_after_guardrail = 0
    true_guardrail_block = 0
    whitelist_violation_leak_count = 0
    temporal_answer_leak_count = 0
    law_scope_answer_leak_count = 0
    claim_binding_answer_leak_count = 0
    trace_present = 0
    schema_pass = 0

    for blocker_row in blocker_rows:
        family = str(blocker_row["family"])
        question_id = str(blocker_row["question_id"])
        row = question_result_to_row(
            replay_rc_g_row(
                question=question_maps[family][question_id],
                rc_a_row=rc_a_reports[family][question_id],
                rc_d_row=rc_d_reports[family][question_id],
            )
        )
        expected_mode = str(blocker_row["expected_mode"])
        final_mode = str(row.get("final_mode"))
        cited_sources = row.get("cited_sources") or []
        correct_source_rate = float(row.get("correct_source_rate") or 0.0)
        if expected_mode == "answer" and final_mode == "refusal":
            false_refusal_after_guardrail += 1
        elif expected_mode == "answer":
            if correct_source_rate < 1.0 or not cited_sources:
                true_guardrail_block += 1

        trace = row.get("trace") or {}
        if trace:
            trace_present += 1
        if (trace.get("final_reason") or "") != "schema_validation_failed":
            schema_pass += 1
        final_reason = trace.get("final_reason")
        scope_class = ((trace.get("law_scope_signal") or {}).get("scope_class"))
        if final_reason == "citation_out_of_whitelist" and final_mode in {"answer", "partial"}:
            whitelist_violation_leak_count += 1
        if final_reason in {"temporal_mismatch", "source_validity_unknown"} and final_mode in {"answer", "partial"}:
            temporal_answer_leak_count += 1
        if final_reason == "law_scope_mismatch" and final_mode in {"answer", "partial"} and scope_class == "single_law_high_conf":
            law_scope_answer_leak_count += 1
        if final_reason == "claim_support_missing" and final_mode in {"answer", "partial"}:
            claim_binding_answer_leak_count += 1

    total = len(blocker_rows)
    payload = {
        "false_refusal_after_guardrail": false_refusal_after_guardrail,
        "true_guardrail_block": true_guardrail_block,
        "whitelist_violation_leak_count": whitelist_violation_leak_count,
        "temporal_answer_leak_count": temporal_answer_leak_count,
        "law_scope_answer_leak_count": law_scope_answer_leak_count,
        "claim_binding_answer_leak_count": claim_binding_answer_leak_count,
        "trace_coverage_rate": trace_present / total,
        "schema_validation_pass_rate": schema_pass / total,
    }
    payload["overall_pass"] = (
        payload["false_refusal_after_guardrail"] <= 4
        and payload["true_guardrail_block"] <= 12
        and payload["whitelist_violation_leak_count"] == 0
        and payload["temporal_answer_leak_count"] == 0
        and payload["law_scope_answer_leak_count"] == 0
        and payload["claim_binding_answer_leak_count"] == 0
        and payload["trace_coverage_rate"] == 1.0
        and payload["schema_validation_pass_rate"] == 1.0
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    args.output_md.write_text(render_markdown(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
