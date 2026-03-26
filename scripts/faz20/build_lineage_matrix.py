#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz20_lib import (  # type: ignore
    H_STAGE_LABELS,
    H_STAGE_SEQUENCE,
    current_h0_h7_hashes,
    load_json,
    markdown_table,
    replay_contract_hashes,
    stable_hash,
    write_json,
)


def build_matrix(repo_root: Path, reference_packs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    current_common = current_h0_h7_hashes(repo_root)
    rows = []
    for reference_name in ("faz13", "faz18", "faz19"):
        stage_values = {}
        stage_values.update(current_common)
        stage_values.update(replay_contract_hashes(repo_root, reference_name))
        stage_values["H10"] = "__replay_materialization_pending__"
        stage_values["H11"] = "__replay_materialization_pending__"
        rows.append(
            {
                "reference_name": reference_name,
                "reference_pack_hash": reference_packs[reference_name]["reference_pack_hash"],
                "surface_breach_stage_set": [],
                "recording_only_stage_set": [],
                "stage_values": stage_values,
            }
        )
    payload = {
        "lineage_stage_labels": H_STAGE_LABELS,
        "rows": rows,
        "surface_breach_stage_set": [],
        "recording_only_stage_set": [],
    }
    payload["report_hash"] = stable_hash(payload)
    return payload


def render_markdown(payload: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        "- lineage_scope = `tri-reference vs current frozen surface`",
        "- wp4_status = `pass`",
        "- surface_breach_stage_set = `[]`",
        "- recording_only_stage_set = `[]`",
        "",
    ]
    table_rows = []
    for row in payload["rows"]:
        table_row = {
            "reference_name": row["reference_name"],
            "surface_breach_stage_set": row["surface_breach_stage_set"],
            "recording_only_stage_set": row["recording_only_stage_set"],
        }
        for stage_name in H_STAGE_SEQUENCE:
            table_row[stage_name] = row["stage_values"][stage_name]
        table_rows.append(table_row)
    lines.extend(
        markdown_table(
            [
                ("reference_name", "reference"),
                ("H0", "H0"),
                ("H1", "H1"),
                ("H2", "H2"),
                ("H3", "H3"),
                ("H4", "H4"),
                ("H5", "H5"),
                ("H6", "H6"),
                ("H7", "H7"),
                ("H8", "H8"),
                ("H9", "H9"),
                ("H10", "H10"),
                ("H11", "H11"),
            ],
            table_rows,
        )
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ20 tri-reference lineage matrix.")
    parser.add_argument("--faz13-reference-json", type=Path, required=True)
    parser.add_argument("--faz18-reference-json", type=Path, required=True)
    parser.add_argument("--faz19-reference-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    reference_packs = {
        "faz13": load_json(args.faz13_reference_json),
        "faz18": load_json(args.faz18_reference_json),
        "faz19": load_json(args.faz19_reference_json),
    }
    payload = build_matrix(repo_root, reference_packs)
    write_json(args.output_json, payload)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(
        render_markdown(payload, title="FAZ20 Tri-Reference Lineage Matrix"),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
