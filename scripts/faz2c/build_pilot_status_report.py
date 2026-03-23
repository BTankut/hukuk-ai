#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt_latency(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value):.2f}ms"
    return "n/a"


def build_report(
    *,
    snapshot: dict[str, Any] | None,
    rollup: dict[str, Any] | None,
    latest_job_summary: dict[str, Any] | None,
) -> str:
    lines: list[str] = ["# FAZ 2C Pilot Status Report", ""]

    latest_status = rollup.get("latest_status") if rollup else None
    rollback_recommended = snapshot.get("rollback_recommended") if snapshot else None

    lines.extend(
        [
            "## Executive Read",
            f"- latest rollup status: `{latest_status or 'unknown'}`",
            f"- latest snapshot rollback recommended: `{rollback_recommended}`",
            f"- current live read: `{'stay on promoted lane' if rollback_recommended is False else 'review / rollback candidate'}`",
            "",
        ]
    )

    lines.append("## Latest Snapshot")
    if snapshot is None:
        lines.append("- snapshot: unavailable")
    else:
        lines.extend(
            [
                f"- captured_at: `{snapshot.get('captured_at', 'unknown')}`",
                f"- health: `{snapshot.get('health', {}).get('status', 'unknown')}`",
                f"- smoke_ok: `{snapshot.get('smoke', {}).get('ok')}`",
                f"- smoke_latency: `{_fmt_latency(snapshot.get('smoke', {}).get('latency_ms'))}`",
                f"- audit_events_delta: `{snapshot.get('metrics_delta', {}).get('audit_events_delta')}`",
                f"- upstream_usage_delta: `{snapshot.get('metrics_delta', {}).get('upstream_usage_delta')}`",
                f"- successful_chat_delta: `{snapshot.get('metrics_delta', {}).get('successful_chat_delta')}`",
                f"- refusal_delta: `{snapshot.get('metrics_delta', {}).get('refusal_delta')}`",
                f"- rollback_reasons: `{snapshot.get('rollback_reasons', [])}`",
            ]
        )
    lines.append("")

    lines.append("## Archived Watch Rollup")
    if rollup is None:
        lines.append("- rollup: unavailable")
    else:
        lines.extend(
            [
                f"- job_count: `{rollup.get('job_count')}`",
                f"- clean_job_count: `{rollup.get('clean_job_count')}`",
                f"- rollback_job_count: `{rollup.get('rollback_job_count')}`",
                f"- latest_status: `{rollup.get('latest_status')}`",
                f"- latest_job_dir: `{rollup.get('latest_job_dir')}`",
                f"- avg_latency_ms: `{_fmt_latency(rollup.get('avg_latency_ms'))}`",
                f"- max_latency_ms: `{_fmt_latency(rollup.get('max_latency_ms'))}`",
            ]
        )
    lines.append("")

    lines.append("## Latest Archived Job")
    if latest_job_summary is None:
        lines.append("- latest archived job summary: unavailable")
    else:
        lines.extend(
            [
                f"- final_status: `{latest_job_summary.get('final_status')}`",
                f"- sample_count: `{latest_job_summary.get('sample_count')}`",
                f"- clean_sample_count: `{latest_job_summary.get('clean_sample_count')}`",
                f"- rollback_sample_count: `{latest_job_summary.get('rollback_sample_count')}`",
                f"- avg_latency_ms: `{_fmt_latency(latest_job_summary.get('avg_latency_ms'))}`",
                f"- max_latency_ms: `{_fmt_latency(latest_job_summary.get('max_latency_ms'))}`",
            ]
        )
    lines.append("")

    lines.append("## Operator Action")
    if rollback_recommended is False and latest_status == "clean":
        lines.append("- stay on promoted lane")
        lines.append("- continue periodic archived watch jobs")
    else:
        lines.append("- investigate current lane state")
        lines.append("- consider `bash scripts/faz2c/run_controlled_rollback.sh` if next snapshot stays red")

    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a markdown pilot status handoff report.")
    parser.add_argument(
        "--snapshot-path",
        type=Path,
        default=Path("runtime_logs/faz2c_narrow_pilot_snapshot.json"),
    )
    parser.add_argument(
        "--rollup-path",
        type=Path,
        default=Path("runtime_logs/faz2c_watch_rollup.json"),
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("runtime_logs/faz2c_pilot_status_report.md"),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    snapshot = load_json(args.snapshot_path)
    rollup = load_json(args.rollup_path)

    latest_job_summary = None
    if rollup and rollup.get("latest_summary_path"):
        latest_job_summary = load_json(Path(rollup["latest_summary_path"]))

    report = build_report(
        snapshot=snapshot,
        rollup=rollup,
        latest_job_summary=latest_job_summary,
    )
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(report, encoding="utf-8")
    print(str(args.output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
