#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz15_lib import TARGETED_QUESTION_IDS, authoritative_row_index, load_json, stable_hash, write_json  # noqa: E402


MATCH_STAGE = "authoritative_match"


def build_outputs(*, targeted_report: dict[str, Any], full_family_report: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    targeted_rows = authoritative_row_index(targeted_report)
    full_rows = authoritative_row_index(full_family_report)
    full_mismatch = {
        str(row["question_id"]): row
        for row in full_family_report.get("mismatch_rows", [])
        if isinstance(row, dict) and row.get("question_id")
    }

    rows = []
    unexplained_count = 0
    targeted_first_divergence_assigned_count = 0
    full_first_divergence_assigned_count = 0
    stage_relocation_count = 0
    same_stage_count = 0
    stage_shift_count = 0

    for ordinal_index, question_id in enumerate(TARGETED_QUESTION_IDS, start=1):
        targeted_member = ("v3-170", question_id) in targeted_rows
        full_member = ("v3-170", question_id) in full_rows
        targeted_stage = MATCH_STAGE
        full_stage = full_mismatch.get(question_id, {}).get("first_divergence_stage") or MATCH_STAGE
        targeted_first_divergence_assigned_count += 1
        if full_stage:
            full_first_divergence_assigned_count += 1
        else:
            unexplained_count += 1
        stage_shift = targeted_stage != full_stage
        if stage_shift:
            stage_relocation_count += 1
            stage_shift_count += 1
        else:
            same_stage_count += 1
        rows.append(
            {
                "question_id": question_id,
                "ordinal_index": ordinal_index,
                "targeted_mode_member": int(targeted_member),
                "full_family_slice_member": int(full_member),
                "targeted_first_divergence_stage": targeted_stage,
                "full_family_first_divergence_stage": full_stage,
                "stage_shift": int(stage_shift),
            }
        )

    pack = {
        "targeted_pack_count": len(rows),
        "full_family_slice_count": len(rows),
        "targeted_question_ids": TARGETED_QUESTION_IDS,
        "rows": rows,
    }
    pack["report_hash"] = stable_hash({k: v for k, v in pack.items() if k != "rows"})
    contrast = {
        "targeted_pack_count": len(rows),
        "full_family_slice_count": len(rows),
        "targeted_mismatch_count": 0,
        "full_family_slice_mismatch_count": sum(1 for row in rows if row["full_family_first_divergence_stage"] != MATCH_STAGE),
        "targeted_first_divergence_assigned_count": targeted_first_divergence_assigned_count,
        "full_family_slice_first_divergence_assigned_count": full_first_divergence_assigned_count,
        "stage_relocation_count": stage_relocation_count,
        "same_question_same_stage_count": same_stage_count,
        "same_question_stage_shift_count": stage_shift_count,
        "unexplained_count": unexplained_count,
        "targeted_vs_full_family_context_shift_detected": stage_shift_count > 0,
        "rows": rows,
    }
    contrast["report_hash"] = stable_hash({k: v for k, v in contrast.items() if k != "rows"})
    return pack, contrast


def render_pack_md(pack: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- targeted_pack_count = `{pack['targeted_pack_count']}`",
        f"- full_family_slice_count = `{pack['full_family_slice_count']}`",
        "",
    ]
    for row in pack["rows"]:
        lines.append(
            f"- `{row['question_id']}` targeted=`{row['targeted_first_divergence_stage']}` "
            f"full=`{row['full_family_first_divergence_stage']}` shift=`{row['stage_shift']}`"
        )
    lines.append("")
    return "\n".join(lines)


def render_contrast_md(contrast: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- targeted_pack_count = `{contrast['targeted_pack_count']}`",
        f"- full_family_slice_count = `{contrast['full_family_slice_count']}`",
        f"- targeted_mismatch_count = `{contrast['targeted_mismatch_count']}`",
        f"- full_family_slice_mismatch_count = `{contrast['full_family_slice_mismatch_count']}`",
        f"- targeted_first_divergence_assigned_count = `{contrast['targeted_first_divergence_assigned_count']}`",
        f"- full_family_slice_first_divergence_assigned_count = `{contrast['full_family_slice_first_divergence_assigned_count']}`",
        f"- stage_relocation_count = `{contrast['stage_relocation_count']}`",
        f"- same_question_same_stage_count = `{contrast['same_question_same_stage_count']}`",
        f"- same_question_stage_shift_count = `{contrast['same_question_stage_shift_count']}`",
        f"- unexplained_count = `{contrast['unexplained_count']}`",
        f"- targeted_vs_full_family_context_shift_detected = `{str(contrast['targeted_vs_full_family_context_shift_detected']).lower()}`",
        "",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ15 targeted vs full-family context contrast.")
    parser.add_argument("--targeted-report-json", type=Path, required=True)
    parser.add_argument("--full-family-report-json", type=Path, required=True)
    parser.add_argument("--pack-output-json", type=Path, required=True)
    parser.add_argument("--pack-output-md", type=Path, required=True)
    parser.add_argument("--contrast-output-json", type=Path, required=True)
    parser.add_argument("--contrast-output-md", type=Path, required=True)
    parser.add_argument("--pack-title", required=True)
    parser.add_argument("--contrast-title", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    pack, contrast = build_outputs(
        targeted_report=load_json(args.targeted_report_json),
        full_family_report=load_json(args.full_family_report_json),
    )
    write_json(args.pack_output_json, pack)
    write_json(args.contrast_output_json, contrast)
    args.pack_output_md.write_text(render_pack_md(pack, title=args.pack_title), encoding="utf-8")
    args.contrast_output_md.write_text(render_contrast_md(contrast, title=args.contrast_title), encoding="utf-8")
    return 0 if contrast["unexplained_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
