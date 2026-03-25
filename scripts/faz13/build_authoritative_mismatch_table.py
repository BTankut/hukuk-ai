#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz13_lib import load_json  # noqa: E402


def build_table(per_family_reports: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    family_breakdown: dict[str, int] = {}
    for report in per_family_reports:
        family_id = str(report["family_id"])
        mismatch_rows = []
        for row in report.get("mismatch_rows", []):
            if not isinstance(row, dict):
                continue
            normalized = {
                "family_id": family_id,
                "question_id": row["question_id"],
                "ordinal_index": int(row["ordinal_index"]),
                "normalized_request_hash_mismatch": int(row.get("normalized_request_hash_mismatch", 0)),
                "model_request_payload_hash_mismatch": int(row.get("model_request_payload_hash_mismatch", 0)),
                "generation_contract_hash_mismatch": int(row.get("generation_contract_hash_mismatch", 0)),
                "preprojection_anchor_mismatch": int(row.get("preprojection_anchor_mismatch", 0)),
                "cited_projection_hash_mismatch": int(row.get("cited_projection_hash_mismatch", 0)),
                "citation_set_projection_hash_mismatch": int(row.get("citation_set_projection_hash_mismatch", 0)),
                "final_mode_mapping_hash_mismatch": int(row.get("final_mode_mapping_hash_mismatch", 0)),
                "blocked_reason_set_mismatch": int(row.get("blocked_reason_set_mismatch", 0)),
                "final_answer_payload_hash_mismatch": int(row.get("final_answer_payload_hash_mismatch", 0)),
                "response_envelope_hash_mismatch": int(row.get("response_envelope_hash_mismatch", 0)),
                "serialized_output_hash_mismatch": int(row.get("serialized_output_hash_mismatch", 0)),
                "reference_runtime_error": int(row.get("reference_runtime_error", 0)),
                "candidate_runtime_error": int(row.get("candidate_runtime_error", 0)),
                "first_divergence_stage": row.get("first_divergence_stage"),
                "primary_reason": row.get("primary_reason"),
            }
            mismatch_rows.append(normalized)
            rows.append(normalized)
        family_breakdown[family_id] = len(mismatch_rows)
    rows.sort(key=lambda item: (item["family_id"], item["ordinal_index"]))
    return {
        "mismatch_count": len(rows),
        "family_breakdown": family_breakdown,
        "rows": rows,
    }


def render_markdown(table: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- mismatch_count = `{table['mismatch_count']}`",
        "",
        "## Family Breakdown",
        "",
    ]
    for family_id, count in sorted(table["family_breakdown"].items()):
        lines.append(f"- `{family_id}` = `{count}`")
    lines.extend(
        [
            "",
            "| family | ordinal | question_id | first_divergence_stage | primary_reason |",
            "| --- | ---: | --- | --- | --- |",
        ]
    )
    for row in table["rows"]:
        lines.append(
            f"| {row['family_id']} | {row['ordinal_index']} | {row['question_id']} | {row['first_divergence_stage']} | {row['primary_reason']} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ13 authoritative mismatch table.")
    parser.add_argument("--parity-json", type=Path, action="append", required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--title", default="FAZ13 Output Parity Authoritative Mismatch Table")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    table = build_table([load_json(path) for path in args.parity_json])
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(table, title=args.title), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
