#!/usr/bin/env python3
"""Safe-activation runner for reranker baseline vs threshold sweeps.

This runner does not try to restart the API gateway automatically.
It makes the required server env blocks explicit and then runs the
canonical eval sets against the live API when requested.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVAL_RUNNER = PROJECT_ROOT / "evaluation" / "eval_runner.py"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "evaluation" / "reports"
DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_SETS = ["faz1-50", "v2-95", "v3-170"]
DEFAULT_THRESHOLDS = [0.1, 0.2, 0.3, 0.4, 0.5]
DEFAULT_MODEL = os.getenv(
    "RERANKER_MODEL",
    "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
)
DEFAULT_EVAL_MODEL_REF = os.getenv("EVAL_MODEL_REF", "gateway-api")
DEFAULT_EVAL_CHECKPOINT_REF = os.getenv("EVAL_CHECKPOINT_REF", "gateway-live")
DEFAULT_GIT_COMMIT = os.getenv("GIT_COMMIT", "unknown")
DEFAULT_BASELINE_THRESHOLD = 0.7
DEFAULT_RETRIEVE_TOP_K = 20
SET_PATHS = {
    "faz1-50": PROJECT_ROOT / "configs" / "evaluation" / "test_questions.json",
    "v2-95": PROJECT_ROOT / "configs" / "evaluation" / "test_questions_v2_95.json",
    "v3-170": PROJECT_ROOT / "configs" / "evaluation" / "test_questions_v3_170.json",
}
SET_ALIASES = {
    "phase3-95": "v2-95",
    "faz2-170": "v3-170",
}


@dataclass(slots=True)
class Variant:
    name: str
    enabled: bool
    threshold: float
    model_id: str
    retrieve_top_k: int
    env: dict[str, str]
    manual_restart_note: str


@dataclass(slots=True)
class RunSpec:
    variant: str
    set_key: str
    questions_path: str
    report_path: str
    command: list[str]
    env: dict[str, str]
    executed: bool = False
    returncode: int | None = None
    elapsed_ms: float | None = None


def _bool_flag(value: bool) -> str:
    return "true" if value else "false"


def _format_threshold(value: float) -> str:
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text.replace(".", "p")


def _normalize_sets(raw_sets: list[str]) -> list[str]:
    expanded: list[str] = []
    seen: set[str] = set()
    for item in raw_sets:
        for token in item.split(","):
            set_key = token.strip()
            if not set_key:
                continue
            if set_key == "all":
                candidates = DEFAULT_SETS
            else:
                candidates = [SET_ALIASES.get(set_key, set_key)]
            for candidate in candidates:
                if candidate not in SET_PATHS:
                    raise ValueError(
                        f"unknown set '{candidate}'. Expected one of: {', '.join(SET_PATHS)} or all"
                    )
                if candidate not in seen:
                    expanded.append(candidate)
                    seen.add(candidate)
    if not expanded:
        raise ValueError("no eval sets selected")
    return expanded


def _load_question_count(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        questions = data.get("questions", [])
    elif isinstance(data, list):
        questions = data
    else:
        raise ValueError(f"unexpected question file format: {type(data).__name__}")
    return len(questions)


def _build_variants(thresholds: list[float], model_id: str) -> list[Variant]:
    baseline_env = {
        "RERANKER_ENABLED": _bool_flag(False),
        "RERANKER_MODEL": model_id,
        "RERANKER_THRESHOLD": str(DEFAULT_BASELINE_THRESHOLD),
        "RERANKER_RETRIEVE_TOP_K": str(DEFAULT_RETRIEVE_TOP_K),
    }
    variants = [
        Variant(
            name="baseline-off",
            enabled=False,
            threshold=DEFAULT_BASELINE_THRESHOLD,
            model_id=model_id,
            retrieve_top_k=DEFAULT_RETRIEVE_TOP_K,
            env=baseline_env,
            manual_restart_note=(
                "Restart the API gateway with reranker disabled before running the evals."
            ),
        )
    ]

    for threshold in thresholds:
        env = {
            "RERANKER_ENABLED": _bool_flag(True),
            "RERANKER_MODEL": model_id,
            "RERANKER_THRESHOLD": str(threshold),
            "RERANKER_RETRIEVE_TOP_K": str(DEFAULT_RETRIEVE_TOP_K),
        }
        variants.append(
            Variant(
                name=f"reranker-on-thr-{_format_threshold(threshold)}",
                enabled=True,
                threshold=threshold,
                model_id=model_id,
                retrieve_top_k=DEFAULT_RETRIEVE_TOP_K,
                env=env,
                manual_restart_note=(
                    "Restart the API gateway with reranker enabled and this threshold "
                    "before running the evals."
                ),
            )
        )

    return variants


def _build_eval_command(
    questions_path: Path,
    report_path: Path,
    api_url: str,
    *,
    set_key: str,
    model_ref: str,
    checkpoint_ref: str,
    git_commit: str,
) -> list[str]:
    return [
        sys.executable,
        str(EVAL_RUNNER),
        "--questions",
        str(questions_path),
        "--output",
        str(report_path),
        "--api-url",
        api_url,
        "--eval-family",
        set_key,
        "--model-ref",
        model_ref,
        "--checkpoint-ref",
        checkpoint_ref,
        "--git-commit",
        git_commit,
        "--report-role",
        "ab_variant",
    ]


def _build_plan(
    sets: list[str],
    variants: list[Variant],
    api_url: str,
    output_dir: Path,
    *,
    model_ref: str,
    checkpoint_ref: str,
    git_commit: str,
) -> tuple[list[RunSpec], dict[str, Any]]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = output_dir / f"reranker_safe_activation_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    runs: list[RunSpec] = []
    set_meta: list[dict[str, Any]] = []

    for set_key in sets:
        questions_path = SET_PATHS[set_key]
        set_meta.append(
            {
                "set_key": set_key,
                "questions_path": str(questions_path),
                "question_count": _load_question_count(questions_path),
            }
        )
        for variant in variants:
            report_path = run_dir / f"{variant.name}__{set_key}.json"
            command = _build_eval_command(
                questions_path,
                report_path,
                api_url,
                set_key=set_key,
                model_ref=model_ref,
                checkpoint_ref=checkpoint_ref,
                git_commit=git_commit,
            )
            runs.append(
                RunSpec(
                    variant=variant.name,
                    set_key=set_key,
                    questions_path=str(questions_path),
                    report_path=str(report_path),
                    command=command,
                    env=variant.env,
                )
            )

    summary = {
        "run_id": run_id,
        "mode": "dry-run",
        "api_url": api_url,
        "output_dir": str(output_dir),
        "run_dir": str(run_dir),
        "manual_restart_required": True,
        "model_id": variants[0].model_id if variants else DEFAULT_MODEL,
        "thresholds": [variant.threshold for variant in variants if variant.enabled],
        "sets": set_meta,
        "variants": [asdict(variant) for variant in variants],
        "runs": [asdict(run) for run in runs],
    }
    return runs, summary


def _print_plan(summary: dict[str, Any]) -> None:
    print("Reranker safe-activation plan")
    print("=" * 32)
    print(f"run_id: {summary['run_id']}")
    print(f"api_url: {summary['api_url']}")
    print(f"output_dir: {summary['output_dir']}")
    print(f"run_dir: {summary['run_dir']}")
    print(f"manual_restart_required: {summary['manual_restart_required']}")
    print()
    print("Variant env blocks")
    for variant in summary["variants"]:
        print(f"- {variant['name']}")
        for key, value in variant["env"].items():
            print(f"  {key}={value}")
        print(f"  note: {variant['manual_restart_note']}")
    print()
    print("Eval matrix")
    for run in summary["runs"]:
        print(f"- {run['variant']} / {run['set_key']}")
        print(f"  questions: {run['questions_path']}")
        print(f"  report:    {run['report_path']}")
        print(f"  command:   {shlex.join(run['command'])}")
    print()


def _probe_api(api_url: str) -> None:
    health_url = api_url.rstrip("/") + "/v1/health"
    try:
        with urlopen(health_url, timeout=10) as resp:
            if resp.status >= 400:
                raise RuntimeError(f"health check failed: HTTP {resp.status}")
    except URLError as exc:
        raise RuntimeError(f"API health check failed for {health_url}: {exc}") from exc


def _execute_runs(runs: list[RunSpec], variants: list[Variant]) -> int:
    variant_map = {variant.name: variant for variant in variants}
    current_variant: str | None = None
    hard_failures = 0

    if not sys.stdin.isatty():
        raise SystemExit(
            "Live mode requires an interactive terminal because the API gateway "
            "must be restarted and confirmed for each reranker variant."
        )

    for run in runs:
        if run.variant != current_variant:
            current_variant = run.variant
            variant = variant_map[current_variant]
            print()
            print(f"Prepare variant: {variant.name}")
            for key, value in variant.env.items():
                print(f"  {key}={value}")
            print(f"  note: {variant.manual_restart_note}")
            input("Restart the API gateway for this variant, then press Enter to continue...")

        print(f"== {run.variant} / {run.set_key} ==")
        print(shlex.join(run.command))
        start = datetime.now(timezone.utc)
        proc = subprocess.run(run.command, check=False)
        elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        run.executed = True
        run.returncode = proc.returncode
        run.elapsed_ms = round(elapsed, 1)
        if proc.returncode != 0:
            if proc.returncode == 1:
                print(
                    "NOTE: Eval returned 1 for this variant. "
                    "Recording the failed Faz 1 gate and continuing the matrix."
                )
            else:
                hard_failures += 1
                print(
                    f"ERROR: Eval command failed with return code {proc.returncode}. "
                    "Continuing to record the rest of the matrix."
                )

    return hard_failures


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safe-activation runner for reranker baseline vs threshold sweeps",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned env matrix and eval commands without executing them.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Execute the eval commands against the live API.",
    )
    parser.add_argument(
        "--sets",
        nargs="+",
        default=DEFAULT_SETS,
        help="Canonical eval sets to run: faz1-50, v2-95, v3-170, or all. Legacy aliases remain accepted.",
    )
    parser.add_argument(
        "--thresholds",
        nargs="+",
        type=float,
        default=DEFAULT_THRESHOLDS,
        help="Threshold sweep for reranker-on variants.",
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help="Live chat API base URL.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for summary and eval report artifacts.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Reranker model id to advertise in the env matrix.",
    )
    parser.add_argument(
        "--eval-model-ref",
        default=DEFAULT_EVAL_MODEL_REF,
        help="Logical model identifier to embed in raw eval report metadata.",
    )
    parser.add_argument(
        "--eval-checkpoint-ref",
        default=DEFAULT_EVAL_CHECKPOINT_REF,
        help="Checkpoint/runtime identifier to embed in raw eval report metadata.",
    )
    parser.add_argument(
        "--git-commit",
        default=DEFAULT_GIT_COMMIT,
        help="Git commit to embed in raw eval report metadata.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    plan_only = args.dry_run or not args.live

    try:
        sets = _normalize_sets(args.sets)
        thresholds = sorted({float(value) for value in args.thresholds})
        variants = _build_variants(thresholds, args.model)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    runs, summary = _build_plan(
        sets,
        variants,
        args.api_url,
        args.output_dir,
        model_ref=args.eval_model_ref,
        checkpoint_ref=args.eval_checkpoint_ref,
        git_commit=args.git_commit,
    )
    summary["mode"] = "dry-run" if plan_only else "live"
    summary["thresholds"] = thresholds

    summary_path = Path(summary["run_dir"]).parent / f"{Path(summary['run_dir']).name}.json"
    summary["summary_path"] = str(summary_path)

    if plan_only:
        _print_plan(summary)
        with summary_path.open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, ensure_ascii=False, indent=2)
        print(f"summary: {summary_path}")
        return 0

    try:
        _probe_api(args.api_url)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    _print_plan(summary)
    print("Live mode: API health check passed. Make sure the gateway was restarted with the correct reranker env block before each variant.")
    try:
        hard_failures = _execute_runs(runs, variants)
    finally:
        summary["runs"] = [asdict(run) for run in runs]
        with summary_path.open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, ensure_ascii=False, indent=2)
    print(f"summary: {summary_path}")
    return 0 if hard_failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
