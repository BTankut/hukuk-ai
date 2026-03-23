#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_job_summaries(root: Path) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    if not root.exists():
        return summaries
    for summary_path in sorted(root.glob("*/summary.json")):
        data = json.loads(summary_path.read_text(encoding="utf-8"))
        data["_summary_path"] = str(summary_path)
        data["_job_dir"] = str(summary_path.parent)
        summaries.append(data)
    return summaries


def build_rollup(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    if not summaries:
        return {
            "job_count": 0,
            "clean_job_count": 0,
            "rollback_job_count": 0,
            "latest_status": None,
            "latest_summary_path": None,
            "latest_job_dir": None,
            "max_latency_ms": None,
            "avg_latency_ms": None,
            "recent_jobs": [],
        }

    clean_jobs = [summary for summary in summaries if summary.get("final_status") == "clean"]
    rollback_jobs = [summary for summary in summaries if summary.get("final_status") != "clean"]
    latencies = [
        float(summary["avg_latency_ms"])
        for summary in summaries
        if isinstance(summary.get("avg_latency_ms"), (int, float))
    ]
    latest = summaries[-1]

    return {
        "job_count": len(summaries),
        "clean_job_count": len(clean_jobs),
        "rollback_job_count": len(rollback_jobs),
        "latest_status": latest.get("final_status"),
        "latest_summary_path": latest.get("_summary_path"),
        "latest_job_dir": latest.get("_job_dir"),
        "max_latency_ms": max(latencies) if latencies else None,
        "avg_latency_ms": (sum(latencies) / len(latencies)) if latencies else None,
        "recent_jobs": [
            {
                "job_dir": summary.get("_job_dir"),
                "final_status": summary.get("final_status"),
                "sample_count": summary.get("sample_count"),
                "avg_latency_ms": summary.get("avg_latency_ms"),
            }
            for summary in summaries[-5:]
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a rollup across archived pilot watch jobs.")
    parser.add_argument(
        "--watch-root",
        type=Path,
        default=Path("runtime_logs/faz2c_watch_jobs"),
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("runtime_logs/faz2c_watch_rollup.json"),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summaries = load_job_summaries(args.watch_root)
    rollup = build_rollup(summaries)
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(json.dumps(rollup, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(args.output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
