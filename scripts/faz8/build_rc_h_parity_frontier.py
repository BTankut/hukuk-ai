#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from faz8_lib import collect_error_rows, family_from_report, load_json, write_json


def _frontier_rows(parity_report: dict[str, Any], eval_report: dict[str, Any]) -> list[dict[str, Any]]:
    family = family_from_report(eval_report)
    rows: list[dict[str, Any]] = []
    for mismatch in parity_report.get("mismatches", []):
        if not isinstance(mismatch, dict) or not mismatch.get("question_id"):
            continue
        rows.append(
            {
                "family": family,
                "question_id": mismatch["question_id"],
                "kind": mismatch.get("kind", "normalized_output_mismatch"),
                "fields": mismatch.get("fields", []),
            }
        )
    rows.extend(collect_error_rows(eval_report))
    rows.sort(key=lambda item: (item["family"], item["question_id"], item["kind"]))
    return rows


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# FAZ8 RC-H Drift Frontier",
        "",
        f"- frontier_total = `{summary['frontier_total']}`",
        f"- mismatch_total = `{summary['mismatch_total']}`",
        f"- parity_runtime_error_total = `{summary['parity_runtime_error_total']}`",
        "",
        "## Family Breakdown",
        "",
    ]
    for item in summary["family_breakdown"]:
        lines.append(
            f"- `{item['family']}` frontier `{item['frontier_total']}` mismatch `{item['mismatch_total']}` error `{item['parity_runtime_error_total']}`"
        )
    lines.extend(["", "## Kind Breakdown", ""])
    for kind, count in summary["kind_breakdown"].items():
        lines.append(f"- `{kind}` = `{count}`")
    lines.extend(["", "## Frontier Sample", ""])
    for item in summary["rows"][:20]:
        detail = ", ".join(item.get("fields", [])) if item.get("fields") else item.get("error", "")
        lines.append(f"- `{item['family']}` `{item['question_id']}` `{item['kind']}` {detail}".rstrip())
    lines.append("")
    return "\n".join(lines)


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    kind_counter = Counter(row["kind"] for row in rows)
    family_counter: dict[str, Counter[str]] = {}
    for row in rows:
        family = row["family"]
        family_counter.setdefault(family, Counter())
        family_counter[family]["frontier_total"] += 1
        if row["kind"] == "parity_runtime_error":
            family_counter[family]["parity_runtime_error_total"] += 1
        else:
            family_counter[family]["mismatch_total"] += 1
    family_breakdown = [
        {
            "family": family,
            "frontier_total": counters["frontier_total"],
            "mismatch_total": counters["mismatch_total"],
            "parity_runtime_error_total": counters["parity_runtime_error_total"],
        }
        for family, counters in sorted(family_counter.items())
    ]
    return {
        "frontier_total": len(rows),
        "mismatch_total": sum(1 for row in rows if row["kind"] != "parity_runtime_error"),
        "parity_runtime_error_total": sum(1 for row in rows if row["kind"] == "parity_runtime_error"),
        "kind_breakdown": dict(sorted(kind_counter.items())),
        "family_breakdown": family_breakdown,
        "rows": rows,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ8 RC-H drift frontier.")
    parser.add_argument("--parity-report", type=Path, action="append", required=True)
    parser.add_argument("--eval-report", type=Path, action="append", required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if len(args.parity_report) != len(args.eval_report):
        raise SystemExit("parity report count must match eval report count")

    rows: list[dict[str, Any]] = []
    for parity_path, eval_path in zip(args.parity_report, args.eval_report, strict=True):
        rows.extend(_frontier_rows(load_json(parity_path), load_json(eval_path)))

    summary = build_summary(rows)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(summary), encoding="utf-8")
    if args.output_json:
        write_json(args.output_json, summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
