#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz26_lib import load_json, write_json


SUMMARY_KEYS = (
    "model_request_payload_hash_mismatch_count",
    "retrieval_request_hash_mismatch_count",
    "assembled_context_hash_mismatch_count",
    "preprojection_hash_mismatch_count",
    "raw_answer_hash_mismatch_count",
    "runtime_error_count",
    "first_break_stage_assigned_count",
    "primary_reason_assigned_count",
    "unexplained_count",
)


def build_summary(reports: list[dict[str, Any]]) -> dict[str, Any]:
    families = []
    for report in reports:
        row = {"family_id": str(report["family_id"]), "question_count": int(report["question_count"])}
        row.update({key: int(report.get(key, 0)) for key in SUMMARY_KEYS})
        row["pass"] = all(row[key] == 0 for key in SUMMARY_KEYS if key not in {"first_break_stage_assigned_count", "primary_reason_assigned_count"})
        families.append(row)

    summary = {
        "family_count": len(families),
        "question_count": sum(item["question_count"] for item in families),
        "all_families_pass": all(item["pass"] for item in families),
        "families": families,
    }
    for key in SUMMARY_KEYS:
        summary[key] = sum(item[key] for item in families)
    return summary


def render_markdown(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- family_count = `{summary['family_count']}`",
        f"- question_count = `{summary['question_count']}`",
    ]
    for key in SUMMARY_KEYS:
        lines.append(f"- {key} = `{summary[key]}`")
    lines.extend(
        [
            f"- all_families_pass = `{'true' if summary['all_families_pass'] else 'false'}`",
            "",
            "| family | pass | model_request | retrieval_request | assembled_context | preprojection | raw_answer | runtime_error | unexplained |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in summary["families"]:
        lines.append(
            f"| {item['family_id']} | {'true' if item['pass'] else 'false'} | {item['model_request_payload_hash_mismatch_count']} | {item['retrieval_request_hash_mismatch_count']} | {item['assembled_context_hash_mismatch_count']} | {item['preprojection_hash_mismatch_count']} | {item['raw_answer_hash_mismatch_count']} | {item['runtime_error_count']} | {item['unexplained_count']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ26 model-visible surface summary.")
    parser.add_argument("--report-json", type=Path, action="append", required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--title", required=True)
    args = parser.parse_args()

    summary = build_summary([load_json(path) for path in args.report_json])
    write_json(args.output_json, summary)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(summary, title=args.title), encoding="utf-8")
    return 0 if summary["all_families_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
