#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "faz4"))

from build_citation_family_failure_pack import build_failure_pack, load_eval_rows, load_question_maps  # noqa: E402

THRESHOLDS = {
    "citation_under_emission": 18,
    "wrong_primary_source_with_supported_answer": 20,
    "residual_false_refusal": 4,
    "residual_unsupported_answer": 1,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build FAZ5 legacy failure-pack rerun summary.")
    parser.add_argument("--baseline-json", required=True, type=Path)
    parser.add_argument("--faz1-questions", required=True, type=Path)
    parser.add_argument("--v2-questions", required=True, type=Path)
    parser.add_argument("--v3-questions", required=True, type=Path)
    parser.add_argument("--faz1-rc-a", required=True, type=Path)
    parser.add_argument("--v2-rc-a", required=True, type=Path)
    parser.add_argument("--v3-rc-a", required=True, type=Path)
    parser.add_argument("--faz1-rc-f", required=True, type=Path)
    parser.add_argument("--v2-rc-f", required=True, type=Path)
    parser.add_argument("--v3-rc-f", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    return parser.parse_args()


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# FAZ 5 Legacy Failure Pack Rerun",
        "",
        f"- overall_pass: `{str(payload['overall_pass']).lower()}`",
        "",
        "| failure_class | baseline_count | rc_f_count | gate | passes |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in payload["classes"]:
        lines.append(
            f"| {item['failure_class']} | {item['baseline_count']} | {item['rc_f_count']} | <= {item['threshold']} | {str(item['passes']).lower()} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    baseline = json.loads(args.baseline_json.read_text(encoding="utf-8"))
    baseline_counts = {item["failure_class"]: int(item["rc_e_count"]) for item in baseline["classes"]}

    question_maps = load_question_maps([args.faz1_questions, args.v2_questions, args.v3_questions])
    rc_a_reports = load_eval_rows([args.faz1_rc_a, args.v2_rc_a, args.v3_rc_a])
    rc_f_reports = load_eval_rows([args.faz1_rc_f, args.v2_rc_f, args.v3_rc_f])

    rc_f_rows, _ = build_failure_pack(
        question_maps=question_maps,
        rc_a_reports=rc_a_reports,
        rc_d_reports=rc_f_reports,
    )
    rc_f_counts = Counter(str(row["failure_class"]) for row in rc_f_rows)

    classes: list[dict[str, object]] = []
    overall_pass = True
    for failure_class, threshold in THRESHOLDS.items():
        rc_f_count = int(rc_f_counts.get(failure_class, 0))
        passes = rc_f_count <= threshold
        overall_pass = overall_pass and passes
        classes.append(
            {
                "failure_class": failure_class,
                "baseline_count": int(baseline_counts.get(failure_class, 0)),
                "rc_f_count": rc_f_count,
                "threshold": threshold,
                "passes": passes,
            }
        )

    payload = {"overall_pass": overall_pass, "classes": classes}
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    args.output_md.write_text(render_markdown(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
