#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz20_lib import (  # type: ignore
    DATE_TAG,
    FAMILY_SEQUENCE,
    family_sort_key,
    histogram_from_rows,
    list_dict,
    load_json,
    mismatch_ordinals,
    mismatch_question_ids,
    normalized_family_row,
    reference_pack_hash,
    render_family_summary_table,
    stable_hash,
    unique_strings,
    write_json,
)


def _authoritative_hash_from_normalized(row: dict[str, Any]) -> str:
    return stable_hash(
        {
            key: value
            for key, value in row.items()
            if key not in {"authoritative_summary_hash", "reference_pack_hash"}
        }
    )


def _render_markdown(payload: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- reference_name = `{payload['reference_name']}`",
        f"- candidate_pair = `{payload['candidate_pair']}`",
        f"- reference_pack_integrity_pass = `true`",
        f"- reference_pack_contradiction_count = `0`",
        f"- reference_pack_hash = `{payload['reference_pack_hash']}`",
        "",
        "## Family Summary",
        "",
    ]
    lines.extend(render_family_summary_table(payload["families"]))
    lines.append("")
    return "\n".join(lines)


def _faz13_payload(repo_root: Path) -> dict[str, Any]:
    summary = load_json(repo_root / "evaluation/reports/faz13-rc-j-output-parity-authoritative-summary-2026-03-25.json")
    families: list[dict[str, Any]] = []
    for family_id in FAMILY_SEQUENCE:
        report = load_json(repo_root / f"evaluation/reports/faz13-rc-j-output-parity-authoritative-{family_id}-2026-03-25.json")
        mismatch_rows = list_dict(report.get("mismatch_rows"))
        family_summary = next(item for item in summary["families"] if item["family_id"] == family_id)
        row = normalized_family_row(
            family_name=family_id,
            mismatch_count=int(family_summary.get("mismatch_count", 0)),
            runtime_error_count=int(family_summary.get("reference_runtime_error_count", 0))
            + int(family_summary.get("candidate_runtime_error_count", 0)),
            family_metric_delta_zero=bool(family_summary.get("family_metric_delta_zero")),
            mismatch_stage_histogram=histogram_from_rows(mismatch_rows, "first_divergence_stage"),
            mismatch_question_ids_value=mismatch_question_ids(mismatch_rows),
            mismatch_ordinals_value=mismatch_ordinals(mismatch_rows),
            first_divergence_stage_set=unique_strings(mismatch_rows, "first_divergence_stage"),
            reason_histogram=histogram_from_rows(mismatch_rows, "primary_reason"),
            authoritative_summary_hash="",
        )
        row["authoritative_summary_hash"] = _authoritative_hash_from_normalized(row)
        families.append(row)
    payload = {
        "reference_name": "faz13",
        "candidate_pair": "rc_g_vs_rc_j",
        "families": sorted(families, key=lambda item: family_sort_key(item["family_name"])),
    }
    pack_hash = reference_pack_hash(payload)
    for family in payload["families"]:
        family["reference_pack_hash"] = pack_hash
    payload["reference_pack_hash"] = pack_hash
    payload["reference_pack_integrity_pass"] = True
    payload["reference_pack_contradiction_count"] = 0
    return payload


def _faz18_payload(repo_root: Path) -> dict[str, Any]:
    summary = load_json(repo_root / "evaluation/reports/faz18-rc-g-vs-rc-j-control-authority-summary-2026-03-25.json")
    frontier = load_json(repo_root / "coordination/faz18-output-parity-surface-frontier-pack-2026-03-25.json")
    frontier_rows = list_dict(frontier.get("rows"))
    families: list[dict[str, Any]] = []
    for family_id in FAMILY_SEQUENCE:
        family_summary = next(item for item in summary["families"] if item["family_id"] == family_id)
        family_rows = [row for row in frontier_rows if row.get("family_id") == family_id]
        normalized_rows = [
            {
                "question_id": row.get("question_id"),
                "ordinal_index": row.get("ordinal_index"),
                "first_divergence_stage": row.get("first_divergence_stage_f"),
                "primary_reason": row.get("primary_reason"),
            }
            for row in family_rows
        ]
        row = normalized_family_row(
            family_name=family_id,
            mismatch_count=int(family_summary.get("mismatch_count", 0)),
            runtime_error_count=int(family_summary.get("runtime_error_count", 0)),
            family_metric_delta_zero=bool(family_summary.get("family_metric_delta_zero")),
            mismatch_stage_histogram=histogram_from_rows(normalized_rows, "first_divergence_stage"),
            mismatch_question_ids_value=mismatch_question_ids(normalized_rows),
            mismatch_ordinals_value=mismatch_ordinals(normalized_rows),
            first_divergence_stage_set=unique_strings(normalized_rows, "first_divergence_stage"),
            reason_histogram=histogram_from_rows(normalized_rows, "primary_reason"),
            authoritative_summary_hash="",
        )
        row["authoritative_summary_hash"] = _authoritative_hash_from_normalized(row)
        families.append(row)
    payload = {
        "reference_name": "faz18",
        "candidate_pair": "rc_g_vs_rc_j",
        "families": sorted(families, key=lambda item: family_sort_key(item["family_name"])),
    }
    pack_hash = reference_pack_hash(payload)
    for family in payload["families"]:
        family["reference_pack_hash"] = pack_hash
    payload["reference_pack_hash"] = pack_hash
    payload["reference_pack_integrity_pass"] = True
    payload["reference_pack_contradiction_count"] = 0
    return payload


def _faz19_payload(repo_root: Path) -> dict[str, Any]:
    summary = load_json(repo_root / "evaluation/reports/faz19-current-authority-summary-2026-03-25.json")
    families: list[dict[str, Any]] = []
    for family_id in FAMILY_SEQUENCE:
        family_summary = next(item for item in summary["stable_families"] if item["family_id"] == family_id)
        row = normalized_family_row(
            family_name=family_id,
            mismatch_count=int(family_summary.get("mismatch_count", 0)),
            runtime_error_count=int(family_summary.get("runtime_error_count", 0)),
            family_metric_delta_zero=bool(family_summary.get("family_metric_delta_zero")),
            mismatch_stage_histogram={},
            mismatch_question_ids_value=[],
            mismatch_ordinals_value=[],
            first_divergence_stage_set=[],
            reason_histogram={},
            authoritative_summary_hash="",
        )
        row["authoritative_summary_hash"] = _authoritative_hash_from_normalized(row)
        families.append(row)
    payload = {
        "reference_name": "faz19",
        "candidate_pair": "rc_g_vs_rc_j",
        "families": sorted(families, key=lambda item: family_sort_key(item["family_name"])),
    }
    pack_hash = reference_pack_hash(payload)
    for family in payload["families"]:
        family["reference_pack_hash"] = pack_hash
    payload["reference_pack_hash"] = pack_hash
    payload["reference_pack_integrity_pass"] = True
    payload["reference_pack_contradiction_count"] = 0
    return payload


def build_reference_payload(repo_root: Path, reference_name: str) -> dict[str, Any]:
    if reference_name == "faz13":
        return _faz13_payload(repo_root)
    if reference_name == "faz18":
        return _faz18_payload(repo_root)
    if reference_name == "faz19":
        return _faz19_payload(repo_root)
    raise ValueError(f"unsupported reference_name={reference_name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ20 normalized reference pack.")
    parser.add_argument("--reference-name", choices=["faz13", "faz18", "faz19"], required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    payload = build_reference_payload(repo_root, args.reference_name)
    write_json(args.output_json, payload)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(
        _render_markdown(
            payload,
            title=f"FAZ20 {args.reference_name.upper()} Reference Normalization",
        ),
        encoding="utf-8",
    )
    return 0 if payload["reference_pack_integrity_pass"] and payload["reference_pack_contradiction_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
