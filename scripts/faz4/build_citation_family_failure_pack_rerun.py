#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from build_citation_family_failure_pack import build_failure_pack, load_eval_rows, load_question_maps
from rc_e_offline_lib import question_result_to_row, replay_rc_e_row

FAILURE_CLASSES = [
    "citation_under_emission",
    "wrong_primary_source_with_supported_answer",
    "residual_false_refusal",
    "residual_unsupported_answer",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rerun the FAZ4 RC-D family failure pack on RC-E.")
    parser.add_argument("--rc-d-pack-jsonl", required=True, type=Path)
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
        "# FAZ 4 Citation Family Failure Pack Rerun",
        "",
        f"- overall_pass: `{str(summary['overall_pass']).lower()}`",
        "",
        "| failure_class | rc_d_count | rc_e_count | delta |",
        "| --- | --- | --- | --- |",
    ]
    for item in summary["classes"]:
        lines.append(
            f"| {item['failure_class']} | {item['rc_d_count']} | {item['rc_e_count']} | {item['delta']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    rc_d_pack_rows = load_jsonl(args.rc_d_pack_jsonl)
    tracked_ids = {(str(row["family"]), str(row["question_id"])) for row in rc_d_pack_rows}
    rc_d_counts = Counter(str(row["failure_class"]) for row in rc_d_pack_rows)

    question_maps = load_question_maps([args.faz1_questions, args.v2_questions, args.v3_questions])
    rc_a_reports = load_eval_rows([args.faz1_rc_a, args.v2_rc_a, args.v3_rc_a])
    rc_d_reports = load_eval_rows([args.faz1_rc_d, args.v2_rc_d, args.v3_rc_d])
    filtered_question_maps = {
        family: {
            question_id: question
            for question_id, question in questions.items()
            if (family, question_id) in tracked_ids
        }
        for family, questions in question_maps.items()
    }
    rc_e_reports: dict[str, dict[str, object]] = {"faz1-50": {}, "v2-95": {}, "v3-170": {}}
    for family, questions in filtered_question_maps.items():
        for question_id, question in questions.items():
            result = replay_rc_e_row(
                question=question,
                rc_a_row=rc_a_reports[family][question_id].payload,
                rc_d_row=rc_d_reports[family][question_id].payload,
            )
            rc_e_reports[family][question_id] = type(
                "EvalRowShim",
                (),
                {"family": family, "question_id": question_id, "payload": question_result_to_row(result)},
            )()
    rc_e_rows, _ = build_failure_pack(
        question_maps=filtered_question_maps,
        rc_a_reports=rc_a_reports,
        rc_d_reports=rc_e_reports,
    )
    rc_e_counts = Counter(
        row["failure_class"]
        for row in rc_e_rows
        if (row["family"], row["question_id"]) in tracked_ids
    )

    classes: list[dict[str, object]] = []
    overall_pass = True
    for failure_class in FAILURE_CLASSES:
        rc_d_count = rc_d_counts.get(failure_class, 0)
        rc_e_count = rc_e_counts.get(failure_class, 0)
        delta = rc_e_count - rc_d_count
        if failure_class in {"citation_under_emission", "wrong_primary_source_with_supported_answer"}:
            passes = rc_e_count < rc_d_count
        else:
            passes = rc_e_count <= rc_d_count
        overall_pass = overall_pass and passes
        classes.append(
            {
                "failure_class": failure_class,
                "rc_d_count": rc_d_count,
                "rc_e_count": rc_e_count,
                "delta": delta,
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
