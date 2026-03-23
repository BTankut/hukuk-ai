#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from rc_d_offline_lib import load_question_map, load_report_rows, replay_rc_d_row

BLOCKER_CLASSES = {"false_refusal_after_guardrail", "true_guardrail_block"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RC-D offline replay on the 77-row FAZ3 blocker pack.")
    parser.add_argument("--blocker-pack-jsonl", required=True, type=Path)
    parser.add_argument("--faz1-questions", required=True, type=Path)
    parser.add_argument("--v2-questions", required=True, type=Path)
    parser.add_argument("--v3-questions", required=True, type=Path)
    parser.add_argument("--faz1-rc-a", required=True, type=Path)
    parser.add_argument("--faz1-rc-c", required=True, type=Path)
    parser.add_argument("--v2-rc-a", required=True, type=Path)
    parser.add_argument("--v2-rc-c", required=True, type=Path)
    parser.add_argument("--v3-rc-a", required=True, type=Path)
    parser.add_argument("--v3-rc-c", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    return parser.parse_args()


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _question_maps(args: argparse.Namespace) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        "faz1-50": load_question_map(args.faz1_questions),
        "v2-95": load_question_map(args.v2_questions),
        "v3-170": load_question_map(args.v3_questions),
    }


def _report_maps(args: argparse.Namespace) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        "faz1-50": {
            "rc_a": load_report_rows(args.faz1_rc_a),
            "rc_c": load_report_rows(args.faz1_rc_c),
        },
        "v2-95": {
            "rc_a": load_report_rows(args.v2_rc_a),
            "rc_c": load_report_rows(args.v2_rc_c),
        },
        "v3-170": {
            "rc_a": load_report_rows(args.v3_rc_a),
            "rc_c": load_report_rows(args.v3_rc_c),
        },
    }


def _classify_residual(row: dict[str, Any], result_row: dict[str, Any]) -> str | None:
    expected_mode = row["expected_mode"]
    final_mode = result_row.get("final_mode")
    if expected_mode == "answer" and final_mode == "refusal":
        return "false_refusal_after_guardrail"

    if expected_mode == "answer":
        if float(result_row.get("correct_source_rate", 0.0)) < 1.0:
            return "true_guardrail_block"
        if not bool(result_row.get("cited_sources")):
            return "true_guardrail_block"
    return None


def main() -> int:
    args = parse_args()
    blocker_pack = _load_jsonl(args.blocker_pack_jsonl)
    if len(blocker_pack) != 77:
        raise RuntimeError(f"Expected 77 blocker rows, found {len(blocker_pack)}")

    question_maps = _question_maps(args)
    report_maps = _report_maps(args)

    rows: list[dict[str, Any]] = []
    residual_by_class = Counter()
    answer_count = 0
    partial_count = 0
    refusal_count = 0
    whitelist_violation_leak_count = 0
    temporal_answer_leak_count = 0
    law_scope_answer_leak_count = 0
    claim_binding_answer_leak_count = 0

    for blocker_row in blocker_pack:
        family = blocker_row["family"]
        question_id = blocker_row["question_id"]
        result = replay_rc_d_row(
            question=question_maps[family][question_id],
            rc_a_row=report_maps[family]["rc_a"][question_id],
            rc_c_row=report_maps[family]["rc_c"][question_id],
        )
        result_row = {
            "question_id": result.question_id,
            "family": family,
            "final_mode": result.final_mode,
            "final_reason": result.final_reason,
            "cited_sources": result.cited_sources,
            "correct_source_rate": result.correct_source_rate,
        }
        residual_class = _classify_residual(blocker_row, result_row)
        if residual_class:
            residual_by_class[residual_class] += 1

        if result.final_mode == "answer":
            answer_count += 1
        elif result.final_mode == "partial":
            partial_count += 1
        else:
            refusal_count += 1

        trace = result.trace or {}
        final_mode = result.final_mode
        final_reason = result.final_reason
        scope_class = ((trace.get("law_scope_signal") or {}).get("scope_class"))
        if final_reason == "citation_out_of_whitelist" and final_mode in {"answer", "partial"}:
            whitelist_violation_leak_count += 1
        if final_reason in {"temporal_mismatch", "source_validity_unknown"} and final_mode in {"answer", "partial"}:
            temporal_answer_leak_count += 1
        if final_reason == "law_scope_mismatch" and final_mode in {"answer", "partial"} and scope_class == "single_law_high_conf":
            law_scope_answer_leak_count += 1
        if final_reason == "claim_support_missing" and final_mode in {"answer", "partial"}:
            claim_binding_answer_leak_count += 1

        rows.append(
            {
                "question_id": question_id,
                "family": family,
                "expected_mode": blocker_row["expected_mode"],
                "blocker_class_before": blocker_row["blocker_class"],
                "rc_d_final_mode": result.final_mode,
                "rc_d_final_reason": result.final_reason,
                "correct_source_rate": result.correct_source_rate,
                "cited_sources": result.cited_sources,
                "residual_blocker_class": residual_class,
            }
        )

    summary = {
        "total_questions": len(rows),
        "false_refusal_after_guardrail": residual_by_class.get("false_refusal_after_guardrail", 0),
        "true_guardrail_block": residual_by_class.get("true_guardrail_block", 0),
        "answer_count": answer_count,
        "partial_count": partial_count,
        "refusal_count": refusal_count,
        "whitelist_violation_leak_count": whitelist_violation_leak_count,
        "temporal_answer_leak_count": temporal_answer_leak_count,
        "law_scope_answer_leak_count": law_scope_answer_leak_count,
        "claim_binding_answer_leak_count": claim_binding_answer_leak_count,
        "passes": {
            "false_refusal_after_guardrail": residual_by_class.get("false_refusal_after_guardrail", 0) <= 6,
            "true_guardrail_block": residual_by_class.get("true_guardrail_block", 0) <= 30,
            "whitelist_violation_leak_count": whitelist_violation_leak_count == 0,
            "temporal_answer_leak_count": temporal_answer_leak_count == 0,
            "law_scope_answer_leak_count": law_scope_answer_leak_count == 0,
            "claim_binding_answer_leak_count": claim_binding_answer_leak_count == 0,
        },
        "rows": rows,
    }
    summary["overall_pass"] = all(summary["passes"].values())

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    markdown = [
        "# FAZ 3 Guardrail Blocker Rerun",
        "",
        f"- total_questions: `{summary['total_questions']}`",
        f"- false_refusal_after_guardrail: `{summary['false_refusal_after_guardrail']}`",
        f"- true_guardrail_block: `{summary['true_guardrail_block']}`",
        f"- answer_count: `{summary['answer_count']}`",
        f"- partial_count: `{summary['partial_count']}`",
        f"- refusal_count: `{summary['refusal_count']}`",
        f"- whitelist_violation_leak_count: `{summary['whitelist_violation_leak_count']}`",
        f"- temporal_answer_leak_count: `{summary['temporal_answer_leak_count']}`",
        f"- law_scope_answer_leak_count: `{summary['law_scope_answer_leak_count']}`",
        f"- claim_binding_answer_leak_count: `{summary['claim_binding_answer_leak_count']}`",
        f"- overall_pass: `{str(summary['overall_pass']).lower()}`",
        "",
        "## Sample Rows",
        "",
        "| family | question_id | before | rc_d_mode | rc_d_reason | residual |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows[:25]:
        markdown.append(
            f"| {row['family']} | {row['question_id']} | {row['blocker_class_before']} | {row['rc_d_final_mode']} | {row['rc_d_final_reason']} | {row['residual_blocker_class']} |"
        )
    args.output_md.write_text("\n".join(markdown) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
