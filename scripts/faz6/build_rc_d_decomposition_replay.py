#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from faz6_lib import (
    FAMILY_ORDER,
    QUESTION_PATHS,
    RC_A_REPORT_PATHS,
    RC_C_REPORT_PATHS,
    RC_D_REPORT_PATHS,
    build_attribution_trace_row,
    classify_attribution_loss,
    current_git_commit,
    family_sort_key,
    parse_tracked_key,
    question_maps_by_family,
)
from rc_d_offline_lib import load_report_rows, replay_rc_d_row, question_result_to_row


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay FAZ6 tracked pack on RC-D and build attribution decomposition.")
    parser.add_argument("--tracked-pack-json", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    return parser.parse_args()


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# FAZ 6 RC-D Decomposition Replay",
        "",
        f"- tracked_count: `{payload['tracked_count']}`",
        f"- parity_mismatch_count: `{payload['parity_mismatch_count']}`",
        f"- trace_complete_count: `{payload['trace_complete_count']}`",
        "",
        "## Reason Histogram",
        "",
    ]
    for reason, count in payload["reason_histogram"].items():
        lines.append(f"- `{reason}`: `{count}`")
    lines.extend(["", "## Stage-First-Loss", ""])
    for stage, count in payload["stage_first_loss_histogram"].items():
        lines.append(f"- `{stage}`: `{count}`")
    lines.extend(
        [
            "",
            "## Family Breakdown",
            "",
            "| family | count |",
            "| --- | --- |",
        ]
    )
    for family in FAMILY_ORDER:
        lines.append(f"| {family} | {payload['family_breakdown'].get(family, 0)} |")
    lines.extend(
        [
            "",
            "## Rows",
            "",
            "| family | question_id | primary_reason | secondary_reason | first_loss_stage | parity_match |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            f"| {row['family']} | {row['question_id']} | {row['primary_reason']} | "
            f"{row.get('secondary_reason') or '-'} | {row['first_loss_stage']} | {str(row['parity_match']).lower()} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    tracked_pack = json.loads(args.tracked_pack_json.read_text(encoding="utf-8"))
    question_maps = question_maps_by_family()
    rc_a_rows = {family: load_report_rows(path) for family, path in RC_A_REPORT_PATHS.items()}
    rc_c_rows = {family: load_report_rows(path) for family, path in RC_C_REPORT_PATHS.items()}
    rc_d_rows = {family: load_report_rows(path) for family, path in RC_D_REPORT_PATHS.items()}

    rows: list[dict[str, object]] = []
    reason_histogram: Counter[str] = Counter()
    stage_histogram: Counter[str] = Counter()
    family_breakdown: Counter[str] = Counter()
    parity_mismatch_count = 0
    trace_complete_count = 0

    for tracked_row in sorted(
        tracked_pack["rows"],
        key=lambda item: (family_sort_key(item["family"]), item["tracked_key"]),
    ):
        family, question_id = parse_tracked_key(tracked_row["tracked_key"])
        question = question_maps[family][question_id]
        replay_result = replay_rc_d_row(
            question=question,
            rc_a_row=rc_a_rows[family][question_id],
            rc_c_row=rc_c_rows[family][question_id],
        )
        replay_row = question_result_to_row(replay_result)
        stored_row = rc_d_rows[family][question_id]
        parity_match = all(
            [
                replay_row.get("final_mode") == stored_row.get("final_mode"),
                list(replay_row.get("cited_sources") or []) == list(stored_row.get("cited_sources") or []),
                str(replay_row.get("answer_text") or "") == str(stored_row.get("answer_text") or ""),
            ]
        )
        if not parity_match:
            parity_mismatch_count += 1

        attribution_trace = build_attribution_trace_row(
            tracked_row=tracked_row,
            question=question,
            rc_a_row=rc_a_rows[family][question_id],
            replay_row=replay_row,
        )
        attribution_trace["expected_mode"] = tracked_row["expected_mode"]
        loss = classify_attribution_loss(attribution_trace)
        if attribution_trace["trace_complete"]:
            trace_complete_count += 1

        row = {
            **attribution_trace,
            **loss,
            "tracked_key": tracked_row["tracked_key"],
            "expected_primary_source_id": tracked_row.get("expected_primary_source_id"),
            "parity_match": parity_match,
        }
        rows.append(row)
        reason_histogram[row["primary_reason"]] += 1
        stage_histogram[row["first_loss_stage"]] += 1
        family_breakdown[family] += 1

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": current_git_commit(),
        "question_paths": {family: str(path.relative_to(Path.cwd())) for family, path in QUESTION_PATHS.items()},
        "tracked_count": len(rows),
        "parity_mismatch_count": parity_mismatch_count,
        "trace_complete_count": trace_complete_count,
        "trace_complete_rate": (trace_complete_count / len(rows)) if rows else 0.0,
        "reason_histogram": dict(sorted(reason_histogram.items())),
        "stage_first_loss_histogram": dict(sorted(stage_histogram.items())),
        "family_breakdown": dict(sorted(family_breakdown.items())),
        "rows": rows,
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    args.output_md.write_text(render_markdown(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
