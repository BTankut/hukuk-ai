#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "faz5"))

from build_source_attribution_divergence_pack import (  # noqa: E402
    _build_supported_projection,
    _parser_target,
    _resolve_best_canonical_key_for_source_id,
    classify_failure,
    load_eval_rows,
    load_question_maps,
    normalize_sources,
    quality_loss_reasons,
)
from canonical_norm_lib import canonical_norm_key  # noqa: E402
from faz2a_hardening import canonicalize_source_id, extract_law_code_from_source_id  # noqa: E402

THRESHOLDS = {
    "canonical_alias_mismatch": lambda baseline, current: current == 0,
    "target_law_or_article_priority_miss": lambda baseline, current: baseline == 0 or current * 2 <= baseline,
    "citation_projection_gap": lambda baseline, current: baseline == 0 or current * 5 <= baseline * 3,
    "mode_drop_on_supported_canonical_source": lambda baseline, current: (baseline == 0 or current * 2 <= baseline) and current <= 2,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build FAZ5 source-attribution divergence rerun summary.")
    parser.add_argument("--baseline-jsonl", required=True, type=Path)
    parser.add_argument("--faz1-questions", required=True, type=Path)
    parser.add_argument("--v2-questions", required=True, type=Path)
    parser.add_argument("--v3-questions", required=True, type=Path)
    parser.add_argument("--faz1-rc-f", required=True, type=Path)
    parser.add_argument("--v2-rc-f", required=True, type=Path)
    parser.add_argument("--v3-rc-f", required=True, type=Path)
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


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# FAZ 5 Source Attribution Divergence Rerun",
        "",
        f"- overall_pass: `{str(payload['overall_pass']).lower()}`",
        f"- fixed_count: `{payload['fixed_count']}`",
        "",
        "| failure_class | baseline_count | rc_f_count | passes |",
        "| --- | --- | --- | --- |",
    ]
    for item in payload["classes"]:
        lines.append(
            f"| {item['failure_class']} | {item['baseline_count']} | {item['rc_f_count']} | {str(item['passes']).lower()} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    baseline_rows = load_jsonl(args.baseline_jsonl)
    tracked_ids = {(str(row["family"]), str(row["question_id"])) for row in baseline_rows}
    baseline_counts = Counter(str(row["failure_class"]) for row in baseline_rows)

    question_maps = load_question_maps([args.faz1_questions, args.v2_questions, args.v3_questions])
    rc_f_reports = load_eval_rows([args.faz1_rc_f, args.v2_rc_f, args.v3_rc_f])

    current_rows: list[dict[str, object]] = []
    current_counts = Counter()
    fixed_count = 0
    for family, question_map in question_maps.items():
        for question_id, question in question_map.items():
            if (family, question_id) not in tracked_ids:
                continue
            rc_f_row = rc_f_reports[family][question_id].payload
            expected_mode = "refusal" if question.get("refusal_expected") else "answer"
            reasons = quality_loss_reasons(expected_mode=expected_mode, row=rc_f_row)
            if not reasons:
                fixed_count += 1
                continue

            trace = rc_f_row.get("trace") or {}
            parsed_query = trace.get("parsed_query") or {}
            question_raw = str(trace.get("question_raw") or rc_f_row.get("question_text") or question.get("question") or "")
            assembled_evidence = list(
                trace.get("assembled_evidence")
                or ((trace.get("context_assembly") or {}).get("assembled_evidence"))
                or []
            )
            allowed_source_whitelist = list(
                trace.get("allowed_source_whitelist")
                or ((trace.get("context_assembly") or {}).get("allowed_source_whitelist"))
                or []
            )
            projection = _build_supported_projection(
                answer_text=str(rc_f_row.get("answer_text") or ""),
                question_raw=question_raw,
                assembled_evidence=assembled_evidence,
                allowed_source_whitelist=allowed_source_whitelist,
                law_scope_signal=trace.get("law_scope_signal") or {},
            )
            expected_citation_source_ids = normalize_sources(question.get("expected_sources"))
            expected_citation_keys = [
                canonical_norm_key(source_id=source_id, law_short_name=extract_law_code_from_source_id(source_id))
                for source_id in expected_citation_source_ids
            ]
            expected_primary_key = expected_citation_keys[0] if expected_citation_keys else None
            rc_f_primary_source_id = canonicalize_source_id(
                ((rc_f_row.get("answer_contract") or {}).get("primary_source_id"))
                or (rc_f_row.get("cited_sources") or [None])[0]
            )
            rc_f_primary_key = _resolve_best_canonical_key_for_source_id(
                rc_f_primary_source_id,
                assembled_evidence=assembled_evidence,
            )
            rc_f_emitted_source_ids = normalize_sources(rc_f_row.get("cited_sources"))
            rc_f_emitted_keys = [
                key
                for key in (
                    _resolve_best_canonical_key_for_source_id(source_id, assembled_evidence=assembled_evidence)
                    for source_id in rc_f_emitted_source_ids
                )
                if key
            ]
            parser_target_law_no, parser_target_article_no, parser_target_paragraph_no, _ = _parser_target(parsed_query)
            failure_class = classify_failure(
                expected_mode=expected_mode,
                rc_d_final_mode=rc_f_row.get("final_mode"),
                expected_primary_key=expected_primary_key,
                rc_d_primary_key=rc_f_primary_key,
                rc_d_emitted_source_ids=rc_f_emitted_source_ids,
                expected_citation_source_ids=expected_citation_source_ids,
                expected_citation_keys=expected_citation_keys,
                supported_canonical_norm_keys=projection["supported_canonical_norm_keys"],
                emitted_canonical_norm_keys=rc_f_emitted_keys,
                parser_target_law_no=parser_target_law_no,
                parser_target_article_no=parser_target_article_no,
                parser_target_paragraph_no=parser_target_paragraph_no,
                kept_claim_units=projection["kept_claim_units"],
            )
            current_rows.append(
                {
                    "family": family,
                    "question_id": question_id,
                    "failure_class": failure_class,
                    "quality_loss_reasons": reasons,
                }
            )
            current_counts[failure_class] += 1

    classes: list[dict[str, object]] = []
    overall_pass = True
    for failure_class, predicate in THRESHOLDS.items():
        baseline_count = int(baseline_counts.get(failure_class, 0))
        current_count = int(current_counts.get(failure_class, 0))
        passes = predicate(baseline_count, current_count)
        overall_pass = overall_pass and passes
        classes.append(
            {
                "failure_class": failure_class,
                "baseline_count": baseline_count,
                "rc_f_count": current_count,
                "passes": passes,
            }
        )

    payload = {
        "overall_pass": overall_pass,
        "fixed_count": fixed_count,
        "current_row_count": len(current_rows),
        "classes": classes,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    args.output_md.write_text(render_markdown(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
