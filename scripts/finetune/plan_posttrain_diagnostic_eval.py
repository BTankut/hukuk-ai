#!/usr/bin/env python3
"""Build the diagnostic direct-eval chain for a local merged checkpoint."""

from __future__ import annotations

import argparse
import json
import re
import shlex
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from handoff_config import file_sha256, load_handoff_config
from check_finetune_config import build_readiness_command


@dataclass(frozen=True)
class DiagnosticPlan:
    config_path: Path
    eval_family: str
    report_path: Path
    manifest_path: Path
    train_package_sha: str
    baseline_manifest: Path
    preflight_command: list[str]
    eval_command: list[str]
    manifest_command: list[str]
    promotion_compatible: bool


def _slugify(value: str) -> str:
    lowered = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "_", lowered)
    return slug.strip("_") or "candidate"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan post-train diagnostic direct-eval commands.")
    parser.add_argument(
        "--config",
        default="configs/finetune/unsloth_sft_qwen35_35b_a3b.json",
        help="Path to fine-tune config JSON.",
    )
    parser.add_argument("--checkpoint-ref", required=True, help="Stable identifier for the trained checkpoint.")
    parser.add_argument("--model-path", required=True, help="Local merged checkpoint path for transformers eval.")
    parser.add_argument("--model", required=True, help="Logical model label to embed in the raw report.")
    parser.add_argument("--model-ref", default=None, help="Logical model identifier embedded in the raw report.")
    parser.add_argument("--git-commit", default="unknown", help="Git commit embedded in the raw report metadata.")
    parser.add_argument("--report-path", default=None, help="Optional explicit raw report output path.")
    parser.add_argument("--manifest-path", default=None, help="Optional explicit evidence manifest output path.")
    parser.add_argument("--stamp", default=None, help="Optional local-date stamp override, format YYYYMMDD.")
    parser.add_argument("--max-new-tokens", type=int, default=512, help="Generation max_new_tokens.")
    parser.add_argument("--limit", type=int, default=None, help="Optional question limit for diagnostics.")
    parser.add_argument("--category", default=None, help="Optional category filter.")
    parser.add_argument(
        "--format",
        choices=("shell", "json"),
        default="shell",
        help="Render as executable shell lines or JSON payload.",
    )
    return parser


def build_plan(
    *,
    config_path: Path,
    checkpoint_ref: str,
    model_path: str,
    model: str,
    model_ref: str | None,
    git_commit: str,
    report_path: Path | None,
    manifest_path: Path | None,
    stamp: str | None,
    max_new_tokens: int,
    limit: int | None,
    category: str | None,
) -> DiagnosticPlan:
    cfg = load_handoff_config(config_path)
    if not cfg.train_file.exists():
        raise SystemExit(f"train file not found: {cfg.train_file}")
    if not cfg.baseline_manifest.exists():
        raise SystemExit(f"baseline manifest not found: {cfg.baseline_manifest}")
    if not cfg.questions_path.exists():
        raise SystemExit(f"questions path not found: {cfg.questions_path}")

    safe_checkpoint = _slugify(checkpoint_ref)
    date_stamp = stamp or datetime.now().astimezone().strftime("%Y%m%d")
    resolved_report = report_path or (
        cfg.report_dir / f"eval_diagnostic_post_train_{cfg.eval_family}_{safe_checkpoint}_{date_stamp}.json"
    )
    resolved_manifest = manifest_path or (
        cfg.report_dir / f"evidence_diagnostic_post_train_{cfg.eval_family}_{safe_checkpoint}_{date_stamp}.json"
    )

    preflight_command = build_readiness_command(config_path)
    eval_command = [
        "python3",
        "evaluation/eval_transformers_direct.py",
        "--model-path",
        model_path,
        "--model",
        model,
        "--questions",
        str(cfg.questions_path.relative_to(cfg.repo_root)),
        "--output",
        str(resolved_report.relative_to(cfg.repo_root)),
        "--max-new-tokens",
        str(max_new_tokens),
        "--eval-family",
        cfg.eval_family,
        "--model-ref",
        model_ref or model,
        "--checkpoint-ref",
        checkpoint_ref,
        "--git-commit",
        git_commit,
        "--report-role",
        "diagnostic_post_train",
        "--trust-remote-code",
    ]
    if limit is not None:
        eval_command.extend(["--limit", str(limit)])
    if category:
        eval_command.extend(["--category", category])

    manifest_command = [
        "python3",
        "scripts/build_eval_evidence_manifest.py",
        "--report-path",
        str(resolved_report.relative_to(cfg.repo_root)),
        "--role",
        "post_train",
        "--train-package-sha",
        file_sha256(cfg.train_file),
        "--output",
        str(resolved_manifest.relative_to(cfg.repo_root)),
    ]

    return DiagnosticPlan(
        config_path=config_path.resolve(),
        eval_family=cfg.eval_family,
        report_path=resolved_report.resolve(),
        manifest_path=resolved_manifest.resolve(),
        train_package_sha=file_sha256(cfg.train_file),
        baseline_manifest=cfg.baseline_manifest.resolve(),
        preflight_command=preflight_command,
        eval_command=eval_command,
        manifest_command=manifest_command,
        promotion_compatible=False,
    )


def _render_shell(plan: DiagnosticPlan) -> str:
    sections = [
        ("1. Confirm frozen preflight gate", plan.preflight_command),
        ("2. Run direct diagnostic eval", plan.eval_command),
        ("3. Freeze diagnostic post-train manifest", plan.manifest_command),
    ]
    lines = [
        f"# config: {plan.config_path}",
        f"# eval_family: {plan.eval_family}",
        f"# train_package_sha256: {plan.train_package_sha}",
        f"# raw_report: {plan.report_path}",
        f"# manifest: {plan.manifest_path}",
        "# promotion_compatible: false",
        "# note: current accepted baseline uses runner=eval_runner; this direct path is diagnostic only unless a matched baseline is produced.",
        "",
    ]
    for title, command in sections:
        lines.append(f"# {title}")
        lines.append(" ".join(shlex.quote(part) for part in command))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_json(plan: DiagnosticPlan) -> str:
    payload = {
        "config_path": str(plan.config_path),
        "eval_family": plan.eval_family,
        "train_package_sha256": plan.train_package_sha,
        "report_path": str(plan.report_path),
        "manifest_path": str(plan.manifest_path),
        "baseline_manifest": str(plan.baseline_manifest),
        "promotion_compatible": plan.promotion_compatible,
        "commands": {
            "preflight": plan.preflight_command,
            "eval": plan.eval_command,
            "manifest": plan.manifest_command,
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    args = build_parser().parse_args()
    plan = build_plan(
        config_path=Path(args.config),
        checkpoint_ref=args.checkpoint_ref,
        model_path=args.model_path,
        model=args.model,
        model_ref=args.model_ref,
        git_commit=args.git_commit,
        report_path=Path(args.report_path) if args.report_path else None,
        manifest_path=Path(args.manifest_path) if args.manifest_path else None,
        stamp=args.stamp,
        max_new_tokens=args.max_new_tokens,
        limit=args.limit,
        category=args.category,
    )
    if args.format == "json":
        print(_render_json(plan), end="")
    else:
        print(_render_shell(plan), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
