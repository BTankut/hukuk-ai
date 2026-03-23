#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from run_narrow_pilot_watch import build_summary, write_json, write_jsonl
from capture_narrow_pilot_snapshot import capture_snapshot


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a timestamped narrow-pilot watch job.")
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
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--sleep-seconds", type=float, default=5.0)
    parser.add_argument("--label", default="narrow_pilot_watch")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("runtime_logs/faz2c_watch_jobs"),
    )
    parser.add_argument("--stop-on-rollback", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    from run_narrow_pilot_watch import time as watch_time

    stamp = _utc_stamp()
    job_dir = args.output_dir / f"{args.label}_{stamp}"
    job_dir.mkdir(parents=True, exist_ok=True)

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

    jsonl_path = job_dir / "watch.jsonl"
    summary_path = job_dir / "summary.json"
    manifest_path = job_dir / "manifest.json"

    write_jsonl(jsonl_path, samples)
    summary = build_summary(samples)
    summary["jsonl_path"] = str(jsonl_path)
    summary["summary_path"] = str(summary_path)
    summary["label"] = args.label
    write_json(summary_path, summary)

    manifest = {
        "label": args.label,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url,
        "job_dir": str(job_dir),
        "sample_count_requested": args.samples,
        "sample_count_recorded": len(samples),
        "stop_on_rollback": args.stop_on_rollback,
        "summary_path": str(summary_path),
        "jsonl_path": str(jsonl_path),
        "final_status": summary["final_status"],
    }
    write_json(manifest_path, manifest)

    print(str(manifest_path))
    return 0 if summary["rollback_sample_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
