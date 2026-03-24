#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_latencies(payload: dict[str, Any]) -> list[float]:
    if isinstance(payload.get("latencies_ms"), list):
        return [float(item) for item in payload["latencies_ms"] if isinstance(item, (int, float))]
    smoke = payload.get("smoke")
    if isinstance(smoke, dict) and isinstance(smoke.get("latency_ms"), (int, float)):
        return [float(smoke["latency_ms"])]
    if isinstance(payload.get("avg_latency_ms"), (int, float)):
        return [float(payload["avg_latency_ms"])]
    return []


def _extract_recovery(payload: dict[str, Any]) -> dict[str, Any]:
    recovery = payload.get("recovery")
    if isinstance(recovery, dict):
        return recovery
    return {}


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = max(0.0, min(1.0, percentile)) * (len(ordered) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def build_gate(reference_payload: dict[str, Any], candidate_payload: dict[str, Any]) -> dict[str, Any]:
    reference_latencies = _extract_latencies(reference_payload)
    candidate_latencies = _extract_latencies(candidate_payload)
    reference_p95 = _percentile(reference_latencies, 0.95)
    candidate_p95 = _percentile(candidate_latencies, 0.95)

    if reference_p95 <= 0:
        regression_ratio = 0.0 if candidate_p95 <= 0 else float("inf")
    else:
        regression_ratio = (candidate_p95 - reference_p95) / reference_p95

    recovery = _extract_recovery(candidate_payload)
    healthy_after_restart = bool(recovery.get("healthy_after_restart", False))

    return {
        "reference_p95_latency_ms": round(reference_p95, 3),
        "candidate_p95_latency_ms": round(candidate_p95, 3),
        "p95_latency_regression_ratio": round(regression_ratio, 6),
        "p95_latency_regression_percent": round(regression_ratio * 100.0, 3),
        "latency_budget_pass": regression_ratio <= 0.20,
        "healthy_after_restart": healthy_after_restart,
        "auto_recovery_pass": healthy_after_restart,
        "reference_sample_count": len(reference_latencies),
        "candidate_sample_count": len(candidate_latencies),
    }


def render_markdown(summary: dict[str, Any], *, title: str) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            f"- reference_p95_latency_ms = `{summary['reference_p95_latency_ms']}`",
            f"- candidate_p95_latency_ms = `{summary['candidate_p95_latency_ms']}`",
            f"- p95_latency_regression_percent = `{summary['p95_latency_regression_percent']}`",
            f"- latency_budget_pass = `{str(summary['latency_budget_pass']).lower()}`",
            f"- healthy_after_restart = `{str(summary['healthy_after_restart']).lower()}`",
            f"- auto_recovery_pass = `{str(summary['auto_recovery_pass']).lower()}`",
            "",
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ7 operational regression gate summary.")
    parser.add_argument("--reference-json", type=Path, required=True)
    parser.add_argument("--candidate-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--title", default="FAZ7 Operational Regression Gate")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    reference_payload = _load_json(args.reference_json)
    candidate_payload = _load_json(args.candidate_json)
    summary = build_gate(reference_payload, candidate_payload)

    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(summary, title=args.title), encoding="utf-8")
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return 0 if summary["latency_budget_pass"] and summary["auto_recovery_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
