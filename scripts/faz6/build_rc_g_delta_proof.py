#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from faz6_lib import (
    RC_A_REPORT_PATHS,
    RC_D_REPORT_PATHS,
    build_attribution_trace_row,
    classify_attribution_loss,
    parse_tracked_key,
    question_maps_by_family,
    row_changed_between,
)
from rc_g_offline_lib import load_report_rows, question_result_to_row, replay_rc_g_row


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build FAZ6 RC-G tracked delta proof.")
    parser.add_argument("--tracked-pack-json", required=True, type=Path)
    parser.add_argument("--rc-d-decomposition-json", required=True, type=Path)
    parser.add_argument("--faz1-50-rc-g", dest="faz1_50_rc_g", required=True, type=Path)
    parser.add_argument("--v2-95-rc-g", dest="v2_95_rc_g", required=True, type=Path)
    parser.add_argument("--v3-170-rc-g", dest="v3_170_rc_g", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    return parser.parse_args()


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# FAZ 6 RC-G Delta Proof",
        "",
        f"- tracked_record_count: `{payload['tracked_record_count']}`",
        f"- changed_output_count: `{payload['changed_output_count']}`",
        f"- beneficial_change_count: `{payload['beneficial_change_count']}`",
        f"- harmful_change_count: `{payload['harmful_change_count']}`",
        f"- citation_omission_baseline: `{payload['citation_omission_baseline']}`",
        f"- citation_omission_rc_g: `{payload['citation_omission_rc_g']}`",
        f"- citation_omission_reduction_rate: `{payload['citation_omission_reduction_rate'] * 100:.1f}%`",
        f"- post_generation_primary_flip_baseline: `{payload['post_generation_primary_flip_baseline']}`",
        f"- post_generation_primary_flip_rc_g: `{payload['post_generation_primary_flip_rc_g']}`",
        f"- overall_pass: `{str(payload['overall_pass']).lower()}`",
        "",
        "## Current Reason Histogram",
        "",
    ]
    for reason, count in payload["current_reason_histogram"].items():
        lines.append(f"- `{reason}`: `{count}`")
    lines.extend(["", "## Sample", ""])
    for item in payload["sample"]:
        lines.append(
            f"- {item['family']} {item['question_id']}: citation `{item['rc_d_citation']} -> {item['rc_g_citation']}`, "
            f"correct_source `{item['rc_d_correct_source']:.4f} -> {item['rc_g_correct_source']:.4f}`, "
            f"mode `{item['rc_d_mode']} -> {item['rc_g_mode']}`"
        )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    tracked_pack = json.loads(args.tracked_pack_json.read_text(encoding="utf-8"))
    rc_d_decomposition = json.loads(args.rc_d_decomposition_json.read_text(encoding="utf-8"))
    question_maps = question_maps_by_family()
    rc_a_rows = {family: load_report_rows(path) for family, path in RC_A_REPORT_PATHS.items()}
    rc_d_rows = {family: load_report_rows(path) for family, path in RC_D_REPORT_PATHS.items()}
    rc_g_reports = {
        "faz1-50": load_report_rows(args.faz1_50_rc_g),
        "v2-95": load_report_rows(args.v2_95_rc_g),
        "v3-170": load_report_rows(args.v3_170_rc_g),
    }

    current_reason_histogram: Counter[str] = Counter()
    changed_output_count = 0
    beneficial_change_count = 0
    harmful_change_count = 0
    sample: list[dict[str, object]] = []

    for tracked_row in tracked_pack["rows"]:
        family, question_id = parse_tracked_key(tracked_row["tracked_key"])
        question = question_maps[family][question_id]
        rc_d_row = rc_d_rows[family][question_id]
        rc_g_replayed = question_result_to_row(
            replay_rc_g_row(
                question=question,
                rc_a_row=rc_a_rows[family][question_id],
                rc_d_row=rc_d_row,
            )
        )
        if row_changed_between(rc_d_row, rc_g_replayed):
            changed_output_count += 1

        beneficial = any(
            [
                float(rc_g_replayed.get("correct_source_rate") or 0.0) > float(rc_d_row.get("correct_source_rate") or 0.0),
                bool(rc_g_replayed.get("has_citation")) and not bool(rc_d_row.get("has_citation")),
                bool(rc_g_replayed.get("refusal_correct")) and not bool(rc_d_row.get("refusal_correct")),
                rc_d_row.get("final_mode") in {"refusal", "partial"} and rc_g_replayed.get("final_mode") == "answer",
            ]
        )
        harmful = any(
            [
                float(rc_g_replayed.get("correct_source_rate") or 0.0) < float(rc_d_row.get("correct_source_rate") or 0.0),
                bool(rc_d_row.get("has_citation")) and not bool(rc_g_replayed.get("has_citation")),
                bool(rc_d_row.get("refusal_correct")) and not bool(rc_g_replayed.get("refusal_correct")),
                rc_d_row.get("final_mode") == "answer" and rc_g_replayed.get("final_mode") in {"partial", "refusal"},
                bool(rc_g_replayed.get("is_hallucination")) and not bool(rc_d_row.get("is_hallucination")),
            ]
        )
        beneficial_change_count += int(beneficial)
        harmful_change_count += int(harmful)

        attribution_trace = build_attribution_trace_row(
            tracked_row=tracked_row,
            question=question,
            rc_a_row=rc_a_rows[family][question_id],
            replay_row=rc_g_replayed,
        )
        attribution_trace["expected_mode"] = tracked_row["expected_mode"]
        loss = classify_attribution_loss(attribution_trace)
        current_reason_histogram[loss["primary_reason"]] += 1

        if len(sample) < 20 and row_changed_between(rc_d_row, rc_g_replayed):
            sample.append(
                {
                    "family": family,
                    "question_id": question_id,
                    "rc_d_mode": rc_d_row.get("final_mode"),
                    "rc_g_mode": rc_g_replayed.get("final_mode"),
                    "rc_d_citation": bool(rc_d_row.get("has_citation")),
                    "rc_g_citation": bool(rc_g_replayed.get("has_citation")),
                    "rc_d_correct_source": float(rc_d_row.get("correct_source_rate") or 0.0),
                    "rc_g_correct_source": float(rc_g_replayed.get("correct_source_rate") or 0.0),
                }
            )

    baseline_reason_histogram = rc_d_decomposition.get("reason_histogram") or {}
    baseline_citation_omission = int(baseline_reason_histogram.get("citation_omission_with_correct_primary_present", 0))
    current_citation_omission = int(current_reason_histogram.get("citation_omission_with_correct_primary_present", 0))
    baseline_primary_flip = int(baseline_reason_histogram.get("post_generation_primary_flip", 0))
    current_primary_flip = int(current_reason_histogram.get("post_generation_primary_flip", 0))

    citation_omission_reduction_rate = (
        (baseline_citation_omission - current_citation_omission) / baseline_citation_omission
        if baseline_citation_omission
        else 0.0
    )
    overall_pass = (
        citation_omission_reduction_rate >= 0.30
        and current_primary_flip <= baseline_primary_flip
        and beneficial_change_count > harmful_change_count
    )

    payload = {
        "tracked_record_count": tracked_pack["tracked_count"],
        "changed_output_count": changed_output_count,
        "beneficial_change_count": beneficial_change_count,
        "harmful_change_count": harmful_change_count,
        "citation_omission_baseline": baseline_citation_omission,
        "citation_omission_rc_g": current_citation_omission,
        "citation_omission_reduction_rate": citation_omission_reduction_rate,
        "post_generation_primary_flip_baseline": baseline_primary_flip,
        "post_generation_primary_flip_rc_g": current_primary_flip,
        "current_reason_histogram": dict(sorted(current_reason_histogram.items())),
        "overall_pass": overall_pass,
        "sample": sample,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    args.output_md.write_text(render_markdown(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
