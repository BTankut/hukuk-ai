#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz18_lib import bool_text, load_json, stable_hash, write_json  # noqa: E402


def build_payload(*, source_report: dict[str, Any], source_report_path: str, status: str, reason: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": status,
        "reason": reason,
        "source_report_path": source_report_path,
    }
    for key in [
        "family_id",
        "question_count",
        "runtime_error_count",
        "mismatch_count",
        "family_metric_delta_zero",
        "gate_pass",
        "family_count",
        "authoritative_summary_mismatch_count",
        "output_parity_surface_breach_count",
        "localized_authorized_downstream_drift_count",
        "frontier_candidate_count",
    ]:
        if key in source_report:
            payload[key] = source_report[key]
    payload["report_hash"] = stable_hash(payload)
    return payload


def render_markdown(payload: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- status = `{payload['status']}`",
        f"- reason = `{payload['reason']}`",
        f"- source_report_path = `{payload['source_report_path']}`",
    ]
    for key in [
        "family_id",
        "family_count",
        "question_count",
        "runtime_error_count",
        "mismatch_count",
        "family_metric_delta_zero",
        "gate_pass",
        "authoritative_summary_mismatch_count",
    ]:
        if key in payload:
            value = payload[key]
            if isinstance(value, bool):
                value = bool_text(value)
            lines.append(f"- {key} = `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ18 not-authorized authoritative adoption wrapper.")
    parser.add_argument("--source-report-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--reason", required=True)
    args = parser.parse_args()

    source_report = load_json(args.source_report_json)
    payload = build_payload(
        source_report=source_report,
        source_report_path=str(args.source_report_json),
        status=args.status,
        reason=args.reason,
    )
    write_json(args.output_json, payload)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(payload, title=args.title), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
