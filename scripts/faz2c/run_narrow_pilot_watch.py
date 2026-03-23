#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

from capture_narrow_pilot_snapshot import capture_snapshot


def build_summary(samples: list[dict[str, Any]]) -> dict[str, Any]:
    rollback_indices = [
        index
        for index, sample in enumerate(samples, start=1)
        if sample.get("rollback_recommended")
    ]
    reason_counter: Counter[str] = Counter()
    latencies: list[float] = []

    for sample in samples:
        for reason in sample.get("rollback_reasons", []):
            reason_counter[reason] += 1
        latency_ms = sample.get("smoke", {}).get("latency_ms")
        if isinstance(latency_ms, (int, float)):
            latencies.append(float(latency_ms))

    return {
        "sample_count": len(samples),
        "clean_sample_count": sum(1 for sample in samples if not sample.get("rollback_recommended")),
        "rollback_sample_count": len(rollback_indices),
        "final_status": "rollback_recommended" if rollback_indices else "clean",
        "first_rollback_sample": rollback_indices[0] if rollback_indices else None,
        "rollback_reason_counts": dict(sorted(reason_counter.items())),
        "max_latency_ms": max(latencies) if latencies else None,
        "avg_latency_ms": (sum(latencies) / len(latencies)) if latencies else None,
        "last_captured_at": samples[-1]["captured_at"] if samples else None,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(row, ensure_ascii=False) for row in rows]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a bounded narrow-pilot watch loop.")
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
    parser.add_argument(
        "--jsonl-path",
        type=Path,
        default=Path("runtime_logs/faz2c_narrow_pilot_watch.jsonl"),
    )
    parser.add_argument(
        "--summary-path",
        type=Path,
        default=Path("runtime_logs/faz2c_narrow_pilot_watch_summary.json"),
    )
    parser.add_argument("--stop-on-rollback", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    samples: list[dict[str, Any]] = []

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
            time.sleep(args.sleep_seconds)

    write_jsonl(args.jsonl_path, samples)
    summary = build_summary(samples)
    summary["jsonl_path"] = str(args.jsonl_path)
    summary["summary_path"] = str(args.summary_path)
    write_json(args.summary_path, summary)
    print(str(args.summary_path))
    return 0 if summary["rollback_sample_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
