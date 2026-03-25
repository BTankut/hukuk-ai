#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz14_lib import load_json  # noqa: E402


def build_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in report.get("authoritative_rows", []):
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "family_id": row["family_id"],
                "question_id": row["question_id"],
                "ordinal_index": int(row["ordinal_index"]),
                "changed_field_set": list(row.get("changed_field_set") or []),
                "changed_field_outside_contract": list(row.get("changed_field_outside_contract") or []),
            }
        )
    rows.sort(key=lambda item: (item["family_id"], item["ordinal_index"]))
    return rows


def render_markdown(rows: list[dict[str, Any]], *, title: str) -> str:
    lines = [f"# {title}", "", "| family | ordinal | question_id | changed_field_set | changed_field_outside_contract |", "| --- | ---: | --- | --- | --- |"]
    for row in rows:
        lines.append(
            f"| {row['family_id']} | {row['ordinal_index']} | {row['question_id']} | "
            f"{row['changed_field_set']} | {row['changed_field_outside_contract']} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ14 v3 final-mode repair table.")
    parser.add_argument("--report-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--title", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    rows = build_rows(load_json(args.report_json))
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(rows, title=args.title), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
