#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz19_lib import (  # type: ignore
    CANDIDATE_SEQUENCE,
    bool_text,
    candidate_fingerprint_entry,
    family_report_row,
    family_sort_key,
    load_json,
    markdown_table,
    stable_hash,
    write_json,
)


def build_capture_report(capture_id: str, reports: list[tuple[Path, dict[str, Any]]]) -> dict[str, Any]:
    family_rows = [
        family_report_row(report, report_path=str(path))
        for path, report in sorted(reports, key=lambda item: family_sort_key(str(item[1]["family_id"])))
    ]
    fingerprint_rows = []
    for path, report in sorted(reports, key=lambda item: family_sort_key(str(item[1]["family_id"]))):
        for candidate_kind in CANDIDATE_SEQUENCE:
            fingerprint_rows.append(
                candidate_fingerprint_entry(
                    report,
                    report_path=str(path),
                    capture_id=capture_id,
                    candidate_kind=candidate_kind,
                )
            )

    payload = {
        "capture_id": capture_id,
        "family_count": len(family_rows),
        "control_pair_runtime_error_count": sum(row["runtime_error_count"] for row in family_rows),
        "control_pair_breach_in_o0_o5": any(row["breach_in_o0_o5"] for row in family_rows),
        "control_pair_breach_in_f0_f12": any(row["breach_in_f0_f12"] for row in family_rows),
        "family_metric_delta_zero": all(row["family_metric_delta_zero"] for row in family_rows),
        "families": family_rows,
        "candidate_fingerprints": fingerprint_rows,
    }
    payload["report_hash"] = stable_hash(payload)
    return payload


def render_markdown(payload: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- capture_id = `{payload['capture_id']}`",
        f"- family_count = `{payload['family_count']}`",
        f"- control_pair_runtime_error_count = `{payload['control_pair_runtime_error_count']}`",
        f"- control_pair_breach_in_o0_o5 = `{bool_text(payload['control_pair_breach_in_o0_o5'])}`",
        f"- control_pair_breach_in_f0_f12 = `{bool_text(payload['control_pair_breach_in_f0_f12'])}`",
        f"- family_metric_delta_zero = `{bool_text(payload['family_metric_delta_zero'])}`",
        "",
        "## Family Summary",
        "",
    ]
    lines.extend(
        markdown_table(
            [
                ("family_id", "family"),
                ("mismatch_count", "mismatch_count"),
                ("runtime_error_count", "runtime_error_count"),
                ("family_metric_delta_zero", "family_metric_delta_zero"),
                ("mismatch_stage_histogram", "mismatch_stage_histogram"),
                ("mismatch_question_ids", "mismatch_question_ids"),
            ],
            payload["families"],
        )
    )
    lines.extend(["", "## Candidate Fingerprints", ""])
    lines.extend(
        markdown_table(
            [
                ("family_id", "family"),
                ("candidate_kind", "candidate"),
                ("row_count", "row_count"),
                ("runtime_error_count", "runtime_error_count"),
                ("session_namespaces", "session_namespaces"),
                ("cache_namespaces", "cache_namespaces"),
                ("fingerprint_hash", "fingerprint_hash"),
            ],
            payload["candidate_fingerprints"],
        )
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ19 capture report.")
    parser.add_argument("--capture-id", required=True)
    parser.add_argument("--family-report-json", type=Path, action="append", required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--title", required=True)
    args = parser.parse_args()

    payload = build_capture_report(
        args.capture_id,
        [(path, load_json(path)) for path in args.family_report_json],
    )
    write_json(args.output_json, payload)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(payload, title=args.title), encoding="utf-8")
    return 0 if payload["control_pair_runtime_error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
