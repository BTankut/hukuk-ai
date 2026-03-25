#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz12_lib import load_json, write_json  # noqa: E402


def build_frontier_pack(per_family_reports: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    expected_count = 0
    unexplained_count = 0
    for report in per_family_reports:
        expected_count += int(report.get("parity_frontier_count", 0))
        for row in report.get("parity_rows", []):
            if not isinstance(row, dict):
                continue
            pack_row = {
                "family_id": row["family_id"],
                "question_id": row["question_id"],
                "ordinal_index": int(row["ordinal_index"]),
                "first_failing_surface": row.get("first_failing_surface"),
                "first_divergence_stage": row.get("first_divergence_stage"),
                "primary_reason": row.get("primary_reason"),
                "reference_runtime_error": int(row.get("reference_runtime_error", 0)),
                "candidate_runtime_error": int(row.get("candidate_runtime_error", 0)),
                "effective_view_used": int(row.get("effective_view_used", 0)),
            }
            if not pack_row["primary_reason"]:
                unexplained_count += 1
            rows.append(pack_row)
    rows.sort(key=lambda item: (item["family_id"], item["ordinal_index"]))
    return {
        "frontier_count": len(rows),
        "expected_frontier_count": expected_count,
        "unexplained_frontier_count": unexplained_count,
        "frontier_count_matches_summary": len(rows) == expected_count,
        "rows": rows,
    }


def render_markdown(pack: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- frontier_count = `{pack['frontier_count']}`",
        f"- expected_frontier_count = `{pack['expected_frontier_count']}`",
        f"- frontier_count_matches_summary = `{str(pack['frontier_count_matches_summary']).lower()}`",
        f"- unexplained_frontier_count = `{pack['unexplained_frontier_count']}`",
        "",
        "## Sample",
        "",
    ]
    if not pack["rows"]:
        lines.append("- frontier yok")
    else:
        for row in pack["rows"][:25]:
            lines.append(
                f"- `{row['family_id']}` `{row['question_id']}` stage `{row['first_divergence_stage']}` reason `{row['primary_reason']}`"
            )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ12 output parity frontier pack.")
    parser.add_argument("--parity-json", type=Path, action="append", required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--title", default="FAZ12 Output Parity Frontier Pack")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    pack = build_frontier_pack([load_json(path) for path in args.parity_json])
    write_json(args.output_json, pack)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(pack, title=args.title), encoding="utf-8")
    return 0 if pack["frontier_count_matches_summary"] and pack["unexplained_frontier_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
