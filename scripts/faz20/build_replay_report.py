#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz20_lib import (  # type: ignore
    FAMILY_SEQUENCE,
    build_reference_match_row,
    first_truth_divergence,
    load_json,
    markdown_table,
    normalize_reason_for_stage,
    replay_family_row,
    stable_hash,
    write_json,
)


def build_replay_payload(
    *,
    replay_name: str,
    reference_pack: dict[str, Any],
    lineage_matrix: dict[str, Any],
    family_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    replay_families = [replay_family_row(report) for report in family_reports]
    replay_families.sort(key=lambda row: FAMILY_SEQUENCE.index(row["family_name"]))
    reference_by_family = {row["family_name"]: row for row in reference_pack["families"]}
    lineage_row = next(row for row in lineage_matrix["rows"] if row["reference_name"] == replay_name)
    comparison_rows = []
    for family_row in replay_families:
        reference_row = reference_by_family[family_row["family_name"]]
        comparison_rows.append(
            build_reference_match_row(
                family_row,
                reference_row,
                h10_match=family_row["per_ordinal_fingerprint_set_hash"] == stable_hash(
                    {
                        "reference_name": reference_pack["reference_name"],
                        "family_name": reference_row["family_name"],
                        "mismatch_question_ids": reference_row["mismatch_question_ids"],
                        "mismatch_ordinals": reference_row["mismatch_ordinals"],
                        "mismatch_stage_histogram": reference_row["mismatch_stage_histogram"],
                        "reason_histogram": reference_row["reason_histogram"],
                    }
                ),
                h11_match=family_row["authoritative_summary_hash"] == reference_row["authoritative_summary_hash"],
            )
        )

    reference_match = all(row["match"] for row in comparison_rows)
    reference_mismatch_count = sum(0 if row["match"] else 1 for row in comparison_rows)
    breach_in_h10_h11 = sorted({stage for row in comparison_rows for stage in row["breach_in_h10_h11"]})
    first_divergence_stage = first_truth_divergence(
        breach_in_h0_h9=list(lineage_row["surface_breach_stage_set"]),
        breach_in_h10_h11=breach_in_h10_h11,
        reference_match=reference_match,
    )
    primary_reason = (
        "stable_current_truth_canonical"
        if reference_match
        else normalize_reason_for_stage(first_divergence_stage)
    )
    payload = {
        "replay_name": replay_name,
        "reference_name": reference_pack["reference_name"],
        "families": replay_families,
        "runtime_error_count": sum(row["runtime_error_count"] for row in replay_families),
        "family_metric_delta_zero": all(row["family_metric_delta_zero"] for row in replay_families),
        "breach_in_h0_h9": bool(lineage_row["surface_breach_stage_set"]),
        "breach_in_h0_h9_stage_set": list(lineage_row["surface_breach_stage_set"]),
        "breach_in_h10_h11": bool(breach_in_h10_h11),
        "breach_in_h10_h11_stage_set": breach_in_h10_h11,
        "reference_match": reference_match,
        "reference_mismatch_count": reference_mismatch_count,
        "first_divergence_stage": first_divergence_stage,
        "primary_reason": primary_reason,
        "unexplained_count": 0 if primary_reason != "unexplained_authority_history_conflict" else reference_mismatch_count,
        "comparison_rows": comparison_rows,
    }
    payload["authoritative_summary_hash"] = stable_hash(
        {
            "replay_name": replay_name,
            "families": [
                {
                    key: value
                    for key, value in row.items()
                    if key != "per_ordinal_fingerprint_set_hash"
                }
                for row in replay_families
            ],
        }
    )
    payload["report_hash"] = stable_hash(payload)
    return payload


def render_markdown(payload: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- replay_name = `{payload['replay_name']}`",
        f"- reference_name = `{payload['reference_name']}`",
        f"- runtime_error_count = `{payload['runtime_error_count']}`",
        f"- family_metric_delta_zero = `{str(payload['family_metric_delta_zero']).lower()}`",
        f"- breach_in_h0_h9 = `{str(payload['breach_in_h0_h9']).lower()}`",
        f"- breach_in_h10_h11 = `{str(payload['breach_in_h10_h11']).lower()}`",
        f"- reference_match = `{str(payload['reference_match']).lower()}`",
        f"- reference_mismatch_count = `{payload['reference_mismatch_count']}`",
        f"- first_divergence_stage = `{payload['first_divergence_stage']}`",
        f"- primary_reason = `{payload['primary_reason']}`",
        f"- unexplained_count = `{payload['unexplained_count']}`",
        "",
        "## Family Summary",
        "",
    ]
    lines.extend(
        markdown_table(
            [
                ("family_name", "family"),
                ("mismatch_count", "mismatch_count"),
                ("runtime_error_count", "runtime_error_count"),
                ("family_metric_delta_zero", "family_metric_delta_zero"),
                ("mismatch_stage_histogram", "mismatch_stage_histogram"),
                ("mismatch_question_ids", "mismatch_question_ids"),
            ],
            payload["families"],
        )
    )
    lines.extend(["", "## Reference Contrast", ""])
    lines.extend(
        markdown_table(
            [
                ("family_name", "family"),
                ("match", "match"),
                ("mismatched_fields", "mismatched_fields"),
                ("breach_in_h10_h11", "breach_in_h10_h11"),
            ],
            payload["comparison_rows"],
        )
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ20 contract-conditioned replay report.")
    parser.add_argument("--replay-name", choices=["faz13", "faz18", "faz19"], required=True)
    parser.add_argument("--reference-json", type=Path, required=True)
    parser.add_argument("--lineage-json", type=Path, required=True)
    parser.add_argument("--family-report-json", type=Path, action="append", required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    payload = build_replay_payload(
        replay_name=args.replay_name,
        reference_pack=load_json(args.reference_json),
        lineage_matrix=load_json(args.lineage_json),
        family_reports=[load_json(path) for path in args.family_report_json],
    )
    write_json(args.output_json, payload)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(
        render_markdown(payload, title=f"FAZ20 Contract Conditioned Replay {args.replay_name.upper()}"),
        encoding="utf-8",
    )
    return 0 if payload["runtime_error_count"] == 0 and payload["family_metric_delta_zero"] and not payload["breach_in_h0_h9"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
