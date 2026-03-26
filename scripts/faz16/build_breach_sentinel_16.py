#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz16_lib import QUESTIONS_PATH_BY_FAMILY, load_json, question_bank_rows, stable_hash, write_json


TAKE_BY_FAMILY = {
    "faz1-50": 4,
    "v2-95": 6,
    "v3-170": 6,
}


def build_pack(first_divergence_table: dict[str, Any]) -> dict[str, Any]:
    rows = [
        row
        for row in first_divergence_table.get("rows", [])
        if isinstance(row, dict) and row.get("family_id") in TAKE_BY_FAMILY and row.get("question_id")
    ]
    rows.sort(key=lambda item: (str(item["family_id"]), str(item["question_id"])))

    selected: list[dict[str, Any]] = []
    taken = {family_id: 0 for family_id in TAKE_BY_FAMILY}
    for row in rows:
        family_id = str(row["family_id"])
        if taken[family_id] >= TAKE_BY_FAMILY[family_id]:
            continue
        selected.append(
            {
                "family_id": family_id,
                "question_id": str(row["question_id"]),
                "ordinal_index": int(row["ordinal_index"]),
                "first_divergence_stage_f": row.get("first_divergence_stage_f"),
                "primary_reason": row.get("primary_reason"),
                "root_cause_class": row.get("root_cause_class"),
            }
        )
        taken[family_id] += 1

    pack = {
        "selection_rule": {
            "sort": ["family ASC", "record_id ASC"],
            "take": TAKE_BY_FAMILY,
        },
        "count": len(selected),
        "family_breakdown": {
            family_id: sum(1 for row in selected if row["family_id"] == family_id)
            for family_id in TAKE_BY_FAMILY
        },
        "rows": selected,
    }
    pack["report_hash"] = stable_hash({k: v for k, v in pack.items() if k != "rows"})
    return pack


def render_markdown(pack: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        "- source = `coordination/faz15-breach-first-divergence-table-2026-03-25.md`",
        "- sort = `family ASC, record_id ASC`",
        f"- count = `{pack['count']}`",
        "",
        "| family | question_id | ordinal | first_divergence_stage_f | primary_reason | root_cause_class |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for row in pack["rows"]:
        lines.append(
            f"| {row['family_id']} | {row['question_id']} | {row['ordinal_index']} | "
            f"{row.get('first_divergence_stage_f')} | {row.get('primary_reason')} | {row.get('root_cause_class')} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_subset_questions(pack: dict[str, Any], *, repo_root: Path) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for family_id, relative_path in QUESTIONS_PATH_BY_FAMILY.items():
        wanted = {row["question_id"] for row in pack["rows"] if row["family_id"] == family_id}
        if not wanted:
            out[family_id] = []
            continue
        question_rows = question_bank_rows(repo_root / relative_path)
        out[family_id] = [row for row in question_rows if str(row["question_id"]) in wanted]
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ16 breach sentinel-16 pack.")
    parser.add_argument("--first-divergence-table", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--subset-output-faz1", type=Path)
    parser.add_argument("--subset-output-v2", type=Path)
    parser.add_argument("--subset-output-v3", type=Path)
    parser.add_argument("--title", default="FAZ16 Breach Sentinel-16")
    args = parser.parse_args()

    pack = build_pack(load_json(args.first_divergence_table))
    write_json(args.output_json, pack)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(pack, title=args.title), encoding="utf-8")

    repo_root = Path(__file__).resolve().parents[2]
    subsets = build_subset_questions(pack, repo_root=repo_root)
    if args.subset_output_faz1:
        write_json(args.subset_output_faz1, subsets["faz1-50"])
    if args.subset_output_v2:
        write_json(args.subset_output_v2, subsets["v2-95"])
    if args.subset_output_v3:
        write_json(args.subset_output_v3, subsets["v3-170"])
    return 0 if pack["count"] == 16 else 1


if __name__ == "__main__":
    raise SystemExit(main())

