#!/usr/bin/env python3
"""Compare two evaluation reports and summarize key metric deltas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


METRIC_DIRECTIONS = {
    "citation_rate": "higher",
    "correct_source_rate": "higher",
    "hallucination_rate": "lower",
    "refusal_accuracy": "higher",
    "avg_keyword_coverage": "higher",
    "phrase_hit_rate": "higher",
    "avg_response_time_ms": "lower",
    "blocked_rate": "lower",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare two eval_runner JSON reports by summary metrics."
    )
    parser.add_argument("--baseline", required=True, help="Path to the baseline report JSON.")
    parser.add_argument("--candidate", required=True, help="Path to the candidate report JSON.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text table.",
    )
    return parser.parse_args()


def load_report(path: str) -> dict:
    report_path = Path(path)
    with report_path.open(encoding="utf-8") as f:
        return json.load(f)


def metric_status(metric: str, delta: float) -> str:
    if abs(delta) < 1e-9:
        return "same"
    direction = METRIC_DIRECTIONS[metric]
    if direction == "higher":
        return "better" if delta > 0 else "worse"
    return "better" if delta < 0 else "worse"


def build_comparison(baseline: dict, candidate: dict) -> dict:
    base_summary = baseline["summary"]
    cand_summary = candidate["summary"]
    metrics = {}
    for metric in METRIC_DIRECTIONS:
        baseline_value = float(base_summary[metric])
        candidate_value = float(cand_summary[metric])
        delta = candidate_value - baseline_value
        metrics[metric] = {
            "baseline": baseline_value,
            "candidate": candidate_value,
            "delta": delta,
            "status": metric_status(metric, delta),
        }

    return {
        "baseline": {
            "path": baseline.get("report_path"),
            "eval_family": baseline.get("metadata", {}).get("eval_family"),
            "model_ref": baseline.get("metadata", {}).get("model_ref"),
            "checkpoint_ref": baseline.get("metadata", {}).get("checkpoint_ref"),
        },
        "candidate": {
            "path": candidate.get("report_path"),
            "eval_family": candidate.get("metadata", {}).get("eval_family"),
            "model_ref": candidate.get("metadata", {}).get("model_ref"),
            "checkpoint_ref": candidate.get("metadata", {}).get("checkpoint_ref"),
        },
        "metrics": metrics,
    }


def print_text(comparison: dict) -> None:
    print("metric\tbaseline\tcandidate\tdelta\tstatus")
    for metric, values in comparison["metrics"].items():
        print(
            f"{metric}\t"
            f"{values['baseline']:.4f}\t"
            f"{values['candidate']:.4f}\t"
            f"{values['delta']:+.4f}\t"
            f"{values['status']}"
        )


def main() -> None:
    args = parse_args()
    comparison = build_comparison(
        load_report(args.baseline),
        load_report(args.candidate),
    )
    if args.json:
        print(json.dumps(comparison, ensure_ascii=False, indent=2))
        return
    print_text(comparison)


if __name__ == "__main__":
    main()
