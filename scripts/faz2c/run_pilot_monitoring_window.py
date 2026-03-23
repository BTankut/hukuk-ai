#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _build_window_report(*, summary: dict[str, Any], latest_cycle_manifest: dict[str, Any] | None) -> str:
    lines = ["# FAZ 2C Pilot Monitoring Window Report", ""]
    lines.extend(
        [
            "## Executive Read",
            f"- final_status: `{summary['final_status']}`",
            f"- all_green: `{summary['all_green']}`",
            f"- latest_final_read: `{summary['latest_final_read']}`",
            f"- cycle_count_recorded: `{summary['cycle_count_recorded']}`",
            "",
        ]
    )
    lines.append("## Window Summary")
    lines.extend(
        [
            f"- clean_cycle_count: `{summary['clean_cycle_count']}`",
            f"- review_cycle_count: `{summary['review_cycle_count']}`",
            f"- latest_cycle_dir: `{summary['latest_cycle_dir']}`",
            f"- latest_rollup_status: `{summary['latest_rollup_status']}`",
            f"- latest_snapshot_rollback_recommended: `{summary['latest_snapshot_rollback_recommended']}`",
            "",
        ]
    )
    lines.append("## Latest Cycle")
    if latest_cycle_manifest is None:
        lines.append("- latest cycle manifest: unavailable")
    else:
        lines.extend(
            [
                f"- cycle_dir: `{latest_cycle_manifest.get('cycle_dir')}`",
                f"- watch_job_dir: `{latest_cycle_manifest.get('watch_job_dir')}`",
                f"- final_read: `{latest_cycle_manifest.get('final_read')}`",
                f"- latest_rollup_status: `{latest_cycle_manifest.get('latest_rollup_status')}`",
                f"- latest_snapshot_rollback_recommended: `{latest_cycle_manifest.get('latest_snapshot_rollback_recommended')}`",
            ]
        )
    lines.append("")
    lines.append("## Operator Action")
    if summary["all_green"]:
        lines.append("- stay on promoted lane")
        lines.append("- continue periodic archived monitoring windows")
    else:
        lines.append("- inspect latest cycle bundle and canonical pilot surfaces")
        lines.append("- consider `bash scripts/faz2c/run_controlled_rollback.sh` if the next window stays red")
    return "\n".join(lines) + "\n"


def invoke_cycle(args: argparse.Namespace) -> tuple[int, Path]:
    cycle_script = Path(__file__).with_name("run_pilot_monitoring_cycle.py")
    command = [
        sys.executable,
        str(cycle_script),
        "--base-url",
        args.base_url,
        "--model",
        args.model,
        "--smoke-query",
        args.smoke_query,
        "--expected-ref",
        args.expected_ref,
        "--max-tokens",
        str(args.max_tokens),
        "--timeout",
        str(args.timeout),
        "--latency-budget-ms",
        str(args.latency_budget_ms),
        "--samples",
        str(args.cycle_samples),
        "--sleep-seconds",
        str(args.cycle_sample_sleep_seconds),
        "--watch-root",
        str(args.watch_root),
        "--output-dir",
        str(args.cycle_output_dir),
        "--snapshot-path",
        str(args.snapshot_path),
        "--canonical-rollup-path",
        str(args.canonical_rollup_path),
        "--canonical-status-report-path",
        str(args.canonical_status_report_path),
    ]
    if args.api_key:
        command.extend(["--api-key", args.api_key])
    completed = subprocess.run(
        command,
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        check=False,
    )
    stdout_lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if not stdout_lines:
        raise RuntimeError(f"cycle runner did not emit a manifest path; stderr={completed.stderr.strip()}")
    return completed.returncode, Path(stdout_lines[-1])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run multiple archived FAZ 2C monitoring cycles as one operator window.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--api-key")
    parser.add_argument("--model", default="hukuk-lora")
    parser.add_argument(
        "--smoke-query",
        default="TBK m.49 uyarınca haksız fiilin genel şartları nelerdir? Kısa cevap ver.",
    )
    parser.add_argument("--expected-ref", default="TBK m.49")
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--latency-budget-ms", type=float, default=30000.0)
    parser.add_argument("--cycles", type=int, default=2)
    parser.add_argument("--sleep-seconds", type=float, default=30.0)
    parser.add_argument("--cycle-samples", type=int, default=2)
    parser.add_argument("--cycle-sample-sleep-seconds", type=float, default=2.0)
    parser.add_argument("--stop-on-red", action="store_true")
    parser.add_argument(
        "--watch-root",
        type=Path,
        default=Path("runtime_logs/faz2c_watch_jobs"),
    )
    parser.add_argument(
        "--cycle-output-dir",
        type=Path,
        default=Path("runtime_logs/faz2c_cycles"),
    )
    parser.add_argument(
        "--snapshot-path",
        type=Path,
        default=Path("runtime_logs/faz2c_narrow_pilot_snapshot.json"),
    )
    parser.add_argument(
        "--canonical-rollup-path",
        type=Path,
        default=Path("runtime_logs/faz2c_watch_rollup.json"),
    )
    parser.add_argument(
        "--canonical-status-report-path",
        type=Path,
        default=Path("runtime_logs/faz2c_pilot_status_report.md"),
    )
    parser.add_argument(
        "--window-output-dir",
        type=Path,
        default=Path("runtime_logs/faz2c_window_jobs"),
    )
    parser.add_argument("--label", default="pilot_monitoring_window")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    stamp = _utc_stamp()
    window_dir = args.window_output_dir / f"{args.label}_{stamp}"
    window_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    latest_cycle_manifest: dict[str, Any] | None = None

    for index in range(1, args.cycles + 1):
        return_code, cycle_manifest_path = invoke_cycle(args)
        latest_cycle_manifest = json.loads(cycle_manifest_path.read_text(encoding="utf-8"))
        row = {
            "index": index,
            "return_code": return_code,
            "cycle_manifest_path": str(cycle_manifest_path),
            "cycle_dir": latest_cycle_manifest.get("cycle_dir"),
            "final_read": latest_cycle_manifest.get("final_read"),
            "latest_rollup_status": latest_cycle_manifest.get("latest_rollup_status"),
            "latest_snapshot_rollback_recommended": latest_cycle_manifest.get(
                "latest_snapshot_rollback_recommended"
            ),
        }
        rows.append(row)
        if args.stop_on_red and row["final_read"] != "stay_on_promoted_lane":
            break
        if index < args.cycles:
            time.sleep(args.sleep_seconds)

    clean_rows = [row for row in rows if row["final_read"] == "stay_on_promoted_lane"]
    review_rows = [row for row in rows if row["final_read"] != "stay_on_promoted_lane"]
    summary = {
        "label": args.label,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "window_dir": str(window_dir),
        "cycle_count_requested": args.cycles,
        "cycle_count_recorded": len(rows),
        "clean_cycle_count": len(clean_rows),
        "review_cycle_count": len(review_rows),
        "all_green": len(rows) > 0 and len(review_rows) == 0,
        "final_status": "clean" if rows and len(review_rows) == 0 else "review_or_rollback_candidate",
        "latest_final_read": rows[-1]["final_read"] if rows else None,
        "latest_cycle_dir": rows[-1]["cycle_dir"] if rows else None,
        "latest_rollup_status": rows[-1]["latest_rollup_status"] if rows else None,
        "latest_snapshot_rollback_recommended": (
            rows[-1]["latest_snapshot_rollback_recommended"] if rows else None
        ),
    }

    rows_path = window_dir / "cycle_manifests.jsonl"
    summary_path = window_dir / "window_summary.json"
    report_path = window_dir / "window_report.md"
    manifest_path = window_dir / "window_manifest.json"
    latest_summary_path = args.window_output_dir / "latest_window_summary.json"
    latest_report_path = args.window_output_dir / "latest_window_report.md"
    latest_manifest_path = args.window_output_dir / "latest_window_manifest.json"

    _write_jsonl(rows_path, rows)
    _write_json(summary_path, summary)
    report = _build_window_report(summary=summary, latest_cycle_manifest=latest_cycle_manifest)
    report_path.write_text(report, encoding="utf-8")
    manifest = {
        "label": args.label,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "window_dir": str(window_dir),
        "rows_path": str(rows_path),
        "summary_path": str(summary_path),
        "report_path": str(report_path),
        "latest_window_summary_path": str(latest_summary_path),
        "latest_window_report_path": str(latest_report_path),
        "latest_window_manifest_path": str(latest_manifest_path),
        "cycle_count_recorded": summary["cycle_count_recorded"],
        "final_status": summary["final_status"],
        "latest_final_read": summary["latest_final_read"],
    }
    _write_json(manifest_path, manifest)
    _write_json(latest_summary_path, summary)
    latest_report_path.write_text(report, encoding="utf-8")
    _write_json(latest_manifest_path, manifest)

    print(str(manifest_path))
    return 0 if summary["final_status"] == "clean" else 1


if __name__ == "__main__":
    raise SystemExit(main())
