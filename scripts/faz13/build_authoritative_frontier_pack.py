#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz13_lib import load_json, write_json  # noqa: E402


def build_frontier_pack(per_family_reports: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    family_breakdown: dict[str, int] = {}
    stage_histogram: Counter[str] = Counter()
    reason_histogram: Counter[str] = Counter()
    unexplained_count = 0

    for report in per_family_reports:
        family_id = str(report["family_id"])
        family_rows = []
        for row in report.get("mismatch_rows", []):
            if not isinstance(row, dict):
                continue
            pack_row = {
                "family_id": family_id,
                "question_id": row["question_id"],
                "ordinal_index": int(row["ordinal_index"]),
                "first_divergence_stage": row.get("first_divergence_stage"),
                "primary_reason": row.get("primary_reason"),
                "reference_runtime_error": int(row.get("reference_runtime_error", 0)),
                "candidate_runtime_error": int(row.get("candidate_runtime_error", 0)),
                "reference_error_rerun_used": int(row.get("reference_error_rerun_used", 0)),
                "candidate_error_rerun_used": int(row.get("candidate_error_rerun_used", 0)),
                "effective_view_member": int(row.get("effective_view_member", 0)),
            }
            family_rows.append(pack_row)
            if isinstance(pack_row["first_divergence_stage"], str) and pack_row["first_divergence_stage"]:
                stage_histogram[pack_row["first_divergence_stage"]] += 1
            if isinstance(pack_row["primary_reason"], str) and pack_row["primary_reason"]:
                reason_histogram[pack_row["primary_reason"]] += 1
            else:
                unexplained_count += 1
            rows.append(pack_row)
        family_breakdown[family_id] = len(family_rows)

    rows.sort(key=lambda item: (item["family_id"], item["ordinal_index"]))
    authoritative_mismatch_ordinals = [int(row["ordinal_index"]) for row in rows]
    authoritative_mismatch_question_ids = [str(row["question_id"]) for row in rows]
    first_divergence_assigned_count = sum(stage_histogram.values())
    primary_reason_assigned_count = sum(reason_histogram.values())
    for row in rows:
        if not row.get("first_divergence_stage"):
            unexplained_count += 1
        elif not row.get("primary_reason"):
            pass

    return {
        "frontier_count": len(rows),
        "authoritative_mismatch_ordinals": authoritative_mismatch_ordinals,
        "authoritative_mismatch_question_ids": authoritative_mismatch_question_ids,
        "family_breakdown": family_breakdown,
        "first_divergence_assigned_count": first_divergence_assigned_count,
        "primary_reason_assigned_count": primary_reason_assigned_count,
        "unexplained_count": unexplained_count,
        "stage_histogram": dict(stage_histogram),
        "reason_histogram": dict(reason_histogram),
        "rows": rows,
    }


def render_markdown(pack: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- frontier_count = `{pack['frontier_count']}`",
        f"- first_divergence_assigned_count = `{pack['first_divergence_assigned_count']}`",
        f"- primary_reason_assigned_count = `{pack['primary_reason_assigned_count']}`",
        f"- unexplained_count = `{pack['unexplained_count']}`",
        "",
        "## Family Breakdown",
        "",
    ]
    for family_id, count in sorted(pack["family_breakdown"].items()):
        lines.append(f"- `{family_id}` = `{count}`")
    lines.extend(["", "## Sample", ""])
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
    parser = argparse.ArgumentParser(description="Build FAZ13 authoritative output parity frontier pack.")
    parser.add_argument("--parity-json", type=Path, action="append", required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--title", default="FAZ13 Output Parity Authoritative Frontier Pack")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    pack = build_frontier_pack([load_json(path) for path in args.parity_json])
    write_json(args.output_json, pack)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(pack, title=args.title), encoding="utf-8")
    return 0 if pack["unexplained_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
