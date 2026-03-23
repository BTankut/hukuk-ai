#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from build_pilot_status_report import build_report
from build_pilot_watch_rollup import build_rollup, load_job_summaries
from capture_narrow_pilot_snapshot import capture_snapshot
from run_narrow_pilot_watch import build_summary, write_json, write_jsonl


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the full FAZ 2C pilot monitoring cycle.")
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
    parser.add_argument("--samples", type=int, default=2)
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    parser.add_argument("--stop-on-rollback", action="store_true")
    parser.add_argument(
        "--watch-root",
        type=Path,
        default=Path("runtime_logs/faz2c_watch_jobs"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("runtime_logs/faz2c_cycles"),
    )
    parser.add_argument("--label", default="pilot_monitoring_cycle")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    from run_narrow_pilot_watch import time as watch_time

    stamp = _utc_stamp()
    cycle_dir = args.output_dir / f"{args.label}_{stamp}"
    cycle_dir.mkdir(parents=True, exist_ok=True)

    watch_job_dir = args.watch_root / f"narrow_pilot_watch_{stamp}"
    watch_job_dir.mkdir(parents=True, exist_ok=True)

    samples: list[dict] = []
    for index in range(1, args.samples + 1):
        sample = capture_snapshot(
            base_url=args.base_url,
            api_key=args.api_key,
            smoke_query=args.smoke_query,
            model=args.model,
            expected_ref=args.expected_ref,
            max_tokens=args.max_tokens,
            timeout=args.timeout,
            latency_budget_ms=args.latency_budget_ms,
        )
        sample["_watch_index"] = index
        samples.append(sample)
        if args.stop_on_rollback and sample.get("rollback_recommended"):
            break
        if index < args.samples:
            watch_time.sleep(args.sleep_seconds)

    watch_jsonl_path = watch_job_dir / "watch.jsonl"
    watch_summary_path = watch_job_dir / "summary.json"
    watch_manifest_path = watch_job_dir / "manifest.json"

    write_jsonl(watch_jsonl_path, samples)
    watch_summary = build_summary(samples)
    watch_summary["jsonl_path"] = str(watch_jsonl_path)
    watch_summary["summary_path"] = str(watch_summary_path)
    watch_summary["label"] = "narrow_pilot_watch"
    write_json(watch_summary_path, watch_summary)

    watch_manifest = {
        "label": "narrow_pilot_watch",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url,
        "job_dir": str(watch_job_dir),
        "sample_count_requested": args.samples,
        "sample_count_recorded": len(samples),
        "stop_on_rollback": args.stop_on_rollback,
        "summary_path": str(watch_summary_path),
        "jsonl_path": str(watch_jsonl_path),
        "final_status": watch_summary["final_status"],
    }
    write_json(watch_manifest_path, watch_manifest)

    summaries = load_job_summaries(args.watch_root)
    rollup = build_rollup(summaries)
    rollup_path = cycle_dir / "rollup.json"
    write_json(rollup_path, rollup)

    latest_job_summary = None
    if rollup.get("latest_summary_path"):
        latest_job_summary = json.loads(Path(rollup["latest_summary_path"]).read_text(encoding="utf-8"))

    latest_snapshot = samples[-1] if samples else None
    status_report = build_report(
        snapshot=latest_snapshot,
        rollup=rollup,
        latest_job_summary=latest_job_summary,
    )
    status_report_path = cycle_dir / "pilot_status_report.md"
    status_report_path.write_text(status_report, encoding="utf-8")

    cycle_manifest = {
        "label": args.label,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url,
        "cycle_dir": str(cycle_dir),
        "watch_job_dir": str(watch_job_dir),
        "watch_manifest_path": str(watch_manifest_path),
        "rollup_path": str(rollup_path),
        "status_report_path": str(status_report_path),
        "latest_snapshot_rollback_recommended": (
            latest_snapshot.get("rollback_recommended") if latest_snapshot else None
        ),
        "latest_rollup_status": rollup.get("latest_status"),
        "final_read": (
            "stay_on_promoted_lane"
            if latest_snapshot is not None
            and latest_snapshot.get("rollback_recommended") is False
            and rollup.get("latest_status") == "clean"
            else "review_or_rollback_candidate"
        ),
    }
    cycle_manifest_path = cycle_dir / "cycle_manifest.json"
    write_json(cycle_manifest_path, cycle_manifest)

    print(str(cycle_manifest_path))
    return 0 if cycle_manifest["final_read"] == "stay_on_promoted_lane" else 1


if __name__ == "__main__":
    raise SystemExit(main())
