#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FamilyInput:
    family: str
    rc_d_path: Path
    rc_g_path: Path


def load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def detect_error_count(per_question: list[dict[str, Any]]) -> int:
    return sum(1 for row in per_question if row.get("error"))


def leak_count(
    per_question: list[dict[str, Any]],
    *,
    reason_set: set[str],
    mode_set: set[str] = {"answer", "partial"},
    require_single_law: bool = False,
) -> int:
    total = 0
    for row in per_question:
        trace = row.get("trace") or {}
        final_mode = row.get("final_mode") or trace.get("final_mode")
        final_reason = trace.get("final_reason")
        if final_reason not in reason_set or final_mode not in mode_set:
            continue
        if require_single_law:
            scope_class = ((trace.get("law_scope_signal") or {}).get("scope_class"))
            if scope_class != "single_law_high_conf":
                continue
        total += 1
    return total


def build_family_summary(family: str, rc_d_report: dict[str, Any], rc_g_report: dict[str, Any]) -> dict[str, Any]:
    rc_d_summary = rc_d_report["summary"]
    rc_g_summary = rc_g_report["summary"]
    per_question = rc_g_report["per_question"]
    rc_d_error_count = detect_error_count(rc_d_report["per_question"])
    rc_g_error_count = detect_error_count(per_question)
    trace_coverage = sum(1 for row in per_question if row.get("trace")) / len(per_question)
    schema_fail_count = sum(
        1 for row in per_question if ((row.get("trace") or {}).get("final_reason") == "schema_validation_failed")
    )
    acceptance = {
        "whitelist_violation_leak_count": leak_count(per_question, reason_set={"citation_out_of_whitelist"}),
        "trace_coverage_rate": trace_coverage,
        "schema_validation_pass_rate": 1.0 - (schema_fail_count / len(per_question)),
        "temporal_answer_leak_count": leak_count(per_question, reason_set={"temporal_mismatch", "source_validity_unknown"}),
        "law_scope_answer_leak_count": leak_count(
            per_question,
            reason_set={"law_scope_mismatch"},
            require_single_law=True,
        ),
        "claim_binding_answer_leak_count": leak_count(per_question, reason_set={"claim_support_missing"}),
    }
    metric_results = {
        "citation_rate": rc_g_summary["citation_rate"] >= rc_d_summary["citation_rate"],
        "correct_source_rate": rc_g_summary["correct_source_rate"] >= rc_d_summary["correct_source_rate"],
        "hallucination_rate": rc_g_summary["hallucination_rate"] <= rc_d_summary["hallucination_rate"],
        "refusal_accuracy": rc_g_summary["refusal_accuracy"] >= rc_d_summary["refusal_accuracy"],
        "error_count": rc_g_error_count <= rc_d_error_count,
    }
    acceptance_results = {
        "whitelist_violation_leak_count": acceptance["whitelist_violation_leak_count"] == 0,
        "trace_coverage_rate": acceptance["trace_coverage_rate"] == 1.0,
        "schema_validation_pass_rate": acceptance["schema_validation_pass_rate"] == 1.0,
        "temporal_answer_leak_count": acceptance["temporal_answer_leak_count"] == 0,
        "law_scope_answer_leak_count": acceptance["law_scope_answer_leak_count"] == 0,
        "claim_binding_answer_leak_count": acceptance["claim_binding_answer_leak_count"] == 0,
    }
    return {
        "family": family,
        "rc_d_summary": rc_d_summary,
        "rc_g_summary": rc_g_summary,
        "rc_d_error_count": rc_d_error_count,
        "rc_g_error_count": rc_g_error_count,
        "metric_results": metric_results,
        "acceptance": acceptance,
        "acceptance_results": acceptance_results,
        "passes": all(metric_results.values()) and all(acceptance_results.values()),
    }


def render_markdown(families: list[dict[str, Any]]) -> str:
    overall_pass = all(item["passes"] for item in families)
    lines = [
        "# FAZ 6 RC-G Family Eval",
        "",
        f"- overall_pass: `{str(overall_pass).lower()}`",
        "",
    ]
    for item in families:
        rc_d_summary = item["rc_d_summary"]
        rc_g_summary = item["rc_g_summary"]
        acceptance = item["acceptance"]
        lines.extend(
            [
                f"## {item['family']}",
                "",
                f"- pass: `{str(item['passes']).lower()}`",
                f"- citation: `RC-D {rc_d_summary['citation_rate'] * 100:.1f}% -> RC-G {rc_g_summary['citation_rate'] * 100:.1f}%`",
                f"- correct_source: `RC-D {rc_d_summary['correct_source_rate'] * 100:.1f}% -> RC-G {rc_g_summary['correct_source_rate'] * 100:.1f}%`",
                f"- hallucination: `RC-D {rc_d_summary['hallucination_rate'] * 100:.1f}% -> RC-G {rc_g_summary['hallucination_rate'] * 100:.1f}%`",
                f"- refusal: `RC-D {rc_d_summary['refusal_accuracy'] * 100:.1f}% -> RC-G {rc_g_summary['refusal_accuracy'] * 100:.1f}%`",
                f"- error_count: `RC-D {item['rc_d_error_count']} -> RC-G {item['rc_g_error_count']}`",
                f"- whitelist_violation_leak_count: `{acceptance['whitelist_violation_leak_count']}`",
                f"- trace_coverage_rate: `{acceptance['trace_coverage_rate'] * 100:.1f}%`",
                f"- schema_validation_pass_rate: `{acceptance['schema_validation_pass_rate'] * 100:.1f}%`",
                f"- temporal_answer_leak_count: `{acceptance['temporal_answer_leak_count']}`",
                f"- law_scope_answer_leak_count: `{acceptance['law_scope_answer_leak_count']}`",
                f"- claim_binding_answer_leak_count: `{acceptance['claim_binding_answer_leak_count']}`",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--faz1-50-rc-d", dest="faz1_50_rc_d", type=Path, required=True)
    parser.add_argument("--v2-95-rc-d", dest="v2_95_rc_d", type=Path, required=True)
    parser.add_argument("--v3-170-rc-d", dest="v3_170_rc_d", type=Path, required=True)
    parser.add_argument("--faz1-50-rc-g", dest="faz1_50_rc_g", type=Path, required=True)
    parser.add_argument("--v2-95-rc-g", dest="v2_95_rc_g", type=Path, required=True)
    parser.add_argument("--v3-170-rc-g", dest="v3_170_rc_g", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    families = [
        FamilyInput("faz1-50", args.faz1_50_rc_d, args.faz1_50_rc_g),
        FamilyInput("v2-95", args.v2_95_rc_d, args.v2_95_rc_g),
        FamilyInput("v3-170", args.v3_170_rc_d, args.v3_170_rc_g),
    ]
    results = [
        build_family_summary(item.family, load_report(item.rc_d_path), load_report(item.rc_g_path))
        for item in families
    ]
    payload = {"overall_pass": all(item["passes"] for item in results), "families": results}
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    args.output_md.write_text(render_markdown(results), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
