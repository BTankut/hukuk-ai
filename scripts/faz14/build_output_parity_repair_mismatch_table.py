#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz14_lib import load_json, write_json  # noqa: E402


def build_table(per_family_reports: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    family_breakdown: dict[str, int] = {}
    for report in per_family_reports:
        family_id = str(report["family_id"])
        report_rows = []
        for row in report.get("mismatch_rows", []):
            if not isinstance(row, dict):
                continue
            item = {
                "family_id": family_id,
                "question_id": row["question_id"],
                "ordinal_index": int(row["ordinal_index"]),
                "first_divergence_stage": row.get("first_divergence_stage"),
                "primary_reason": row.get("primary_reason"),
            }
            report_rows.append(item)
            rows.append(item)
        family_breakdown[family_id] = len(report_rows)
    rows.sort(key=lambda item: (item["family_id"], item["ordinal_index"]))
    return {
        "mismatch_count": len(rows),
        "family_breakdown": family_breakdown,
        "rows": rows,
    }


def render_markdown(table: dict[str, Any], *, title: str) -> str:
    lines = [f"# {title}", "", f"- mismatch_count = `{table['mismatch_count']}`", "", "## Family Breakdown", ""]
    for family, count in sorted(table["family_breakdown"].items()):
        lines.append(f"- `{family}` = `{count}`")
    lines.extend(["", "| family | ordinal | question_id | first_divergence_stage | primary_reason |", "| --- | ---: | --- | --- | --- |"])
    for row in table["rows"]:
        lines.append(
            f"| {row['family_id']} | {row['ordinal_index']} | {row['question_id']} | "
            f"{row.get('first_divergence_stage')} | {row.get('primary_reason')} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ14 output parity repair mismatch table.")
    parser.add_argument("--report-json", type=Path, action="append", required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--title", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    table = build_table([load_json(path) for path in args.report_json])
    write_json(args.output_json, table)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(table, title=args.title), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
