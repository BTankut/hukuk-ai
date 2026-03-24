#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "faz8"))

from faz8_lib import load_json, load_question_bank


FAMILY_ORDER = ["faz1-50", "v2-95", "v3-170"]


def build_selection(
    *,
    frontier: dict[str, Any],
    faz1_bank: dict[str, dict[str, Any]],
    v2_bank: dict[str, dict[str, Any]],
    v3_bank: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    banks = {
        "faz1-50": faz1_bank,
        "v2-95": v2_bank,
        "v3-170": v3_bank,
    }
    selected_ids_by_family: dict[str, list[str]] = {}
    selected_questions: list[dict[str, Any]] = []
    seen_output_ids: set[str] = set()

    rows = sorted(
        [row for row in frontier.get("rows", []) if isinstance(row, dict)],
        key=lambda row: (str(row.get("family") or ""), str(row.get("question_id") or "")),
    )

    for family in FAMILY_ORDER:
        family_rows = [row for row in rows if row.get("family") == family][:4]
        question_ids = [str(row["question_id"]) for row in family_rows if row.get("question_id")]
        if family == "faz1-50" and "TBK-005" not in question_ids:
            if len(question_ids) >= 4:
                question_ids[-1] = "TBK-005"
            else:
                question_ids.append("TBK-005")
        selected_ids_by_family[family] = question_ids
        bank = banks[family]
        for question_id in question_ids:
            question = bank.get(question_id)
            if question is None:
                raise KeyError(f"question_id={question_id} missing in {family} bank")
            materialized = dict(question)
            output_id = str(materialized["id"])
            if output_id in seen_output_ids:
                materialized["source_question_id"] = output_id
                materialized["id"] = f"{family}::{output_id}"
            seen_output_ids.add(str(materialized["id"]))
            selected_questions.append(materialized)

    return {
        "family_order": FAMILY_ORDER,
        "selected_ids_by_family": selected_ids_by_family,
        "question_count": len(selected_questions),
        "questions": selected_questions,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# FAZ9 Sentinel-12 Pack",
        "",
        f"- question_count = `{summary['question_count']}`",
        "",
    ]
    for family in FAMILY_ORDER:
        joined = ", ".join(f"`{item}`" for item in summary["selected_ids_by_family"].get(family, []))
        lines.append(f"- {family}: {joined}")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ9 Sentinel-12 question pack.")
    parser.add_argument("--frontier-json", type=Path, required=True)
    parser.add_argument("--faz1-questions", type=Path, required=True)
    parser.add_argument("--v2-questions", type=Path, required=True)
    parser.add_argument("--v3-questions", type=Path, required=True)
    parser.add_argument("--output-pack", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = build_selection(
        frontier=load_json(args.frontier_json),
        faz1_bank=load_question_bank(args.faz1_questions),
        v2_bank=load_question_bank(args.v2_questions),
        v3_bank=load_question_bank(args.v3_questions),
    )
    args.output_pack.parent.mkdir(parents=True, exist_ok=True)
    args.output_pack.write_text(
        json.dumps(summary["questions"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(summary), encoding="utf-8")
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(
                {
                    "family_order": summary["family_order"],
                    "selected_ids_by_family": summary["selected_ids_by_family"],
                    "question_count": summary["question_count"],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
