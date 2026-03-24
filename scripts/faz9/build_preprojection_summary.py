#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz9_lib import load_json, write_json


COUNTER_KEYS = (
    "normalized_request_hash_mismatch_count",
    "model_request_payload_hash_mismatch_count",
    "generation_contract_hash_mismatch_count",
    "preprojection_hash_mismatch_count",
    "raw_answer_hash_mismatch_count",
    "parity_runtime_error_count",
)


def build_summary(per_family_gates: list[dict[str, Any]]) -> dict[str, Any]:
    families: list[dict[str, Any]] = []
    for gate in per_family_gates:
        family = {
            "family": gate.get("eval_family") or "unknown",
            "question_count": int(gate.get("question_count", 0)),
            "compared_question_count": int(gate.get("compared_question_count", 0)),
        }
        family.update({key: int(gate.get(key, 0)) for key in COUNTER_KEYS})
        family["pass"] = all(family[key] == 0 for key in COUNTER_KEYS)
        families.append(family)

    summary = {
        "family_count": len(families),
        "question_count": sum(item["question_count"] for item in families),
        "compared_question_count": sum(item["compared_question_count"] for item in families),
        "all_families_pass": all(item["pass"] for item in families),
        "families": families,
    }
    for key in COUNTER_KEYS:
        summary[key] = sum(item[key] for item in families)
    return summary


def render_markdown(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- family_count = `{summary['family_count']}`",
        f"- question_count = `{summary['question_count']}`",
        f"- compared_question_count = `{summary['compared_question_count']}`",
    ]
    for key in COUNTER_KEYS:
        lines.append(f"- {key} = `{summary[key]}`")
    lines.extend(
        [
            f"- all_families_pass = `{str(summary['all_families_pass']).lower()}`",
            "",
            "## Family Breakdown",
            "",
        ]
    )
    for item in summary["families"]:
        lines.append(
            f"- `{item['family']}` pass `{str(item['pass']).lower()}` q `{item['compared_question_count']}/{item['question_count']}`"
        )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ9 preprojection family summary.")
    parser.add_argument("--gate-json", type=Path, action="append", required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--title", default="FAZ9 RC-J Preprojection Summary")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = build_summary([load_json(path) for path in args.gate_json])
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(summary, title=args.title), encoding="utf-8")
    if args.output_json:
        write_json(args.output_json, summary)
    return 0 if summary["all_families_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
