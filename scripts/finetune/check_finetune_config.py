#!/usr/bin/env python3
"""Validate the restored fine-tune handoff config against the frozen package."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from handoff_config import count_clean_examples, file_sha256, load_handoff_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate fine-tune handoff config + frozen package.")
    parser.add_argument(
        "--config",
        default="configs/finetune/unsloth_sft_qwen35_35b_a3b.json",
        help="Path to fine-tune config JSON.",
    )
    return parser


def count_jsonl_rows(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def build_readiness_command(config_path: Path) -> list[str]:
    cfg = load_handoff_config(config_path)
    command = [
        sys.executable,
        str(cfg.repo_root / "scripts/check_training_readiness.py"),
        "--mode",
        "preflight",
        "--expected-eval-family",
        cfg.eval_family,
        "--max-question-duplicate-excess",
        str(cfg.max_question_duplicate_excess),
        "--baseline-evidence-path",
        str(cfg.baseline_manifest),
    ]
    for workflow_file in cfg.workflow_files:
        command.extend(["--workflow-file", str(workflow_file)])
    return command


def main() -> int:
    args = build_parser().parse_args()
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"[FAIL] Config bulunamadi: {config_path}")
        return 1

    cfg = load_handoff_config(config_path)
    manifest_payload = {}

    if not cfg.train_file.exists():
        print(f"[FAIL] Train file bulunamadi: {cfg.train_file}")
        return 1
    if not cfg.held_out_file.exists():
        print(f"[FAIL] Held-out file bulunamadi: {cfg.held_out_file}")
        return 1
    if not cfg.questions_path.exists():
        print(f"[FAIL] Eval questions bulunamadi: {cfg.questions_path}")
        return 1
    if not cfg.baseline_manifest.exists():
        print(f"[FAIL] Baseline manifest bulunamadi: {cfg.baseline_manifest}")
        return 1

    try:
        manifest_payload = json.loads(cfg.baseline_manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[FAIL] Baseline manifest parse edilemedi: {exc}")
        return 1

    if manifest_payload.get("role") != "baseline":
        print(f"[FAIL] Baseline manifest role invalid: {manifest_payload.get('role')!r}")
        return 1
    if manifest_payload.get("eval_family") != cfg.eval_family:
        print(
            "[FAIL] Eval family mismatch: "
            f"config={cfg.eval_family!r} manifest={manifest_payload.get('eval_family')!r}"
        )
        return 1
    if cfg.max_tokens < 3000:
        print(f"[FAIL] evaluation.max_tokens must be >= 3000, got {cfg.max_tokens}")
        return 1

    try:
        cfg.output_dir.relative_to(cfg.repo_root / "artifacts" / "finetune")
    except ValueError:
        print(f"[FAIL] Output dir artifacts/finetune altinda olmali: {cfg.output_dir}")
        return 1

    total, clean, flagged = count_clean_examples(cfg.train_file, cfg.placeholder_markers)
    train_sha = file_sha256(cfg.train_file)
    heldout_rows = count_jsonl_rows(cfg.held_out_file)

    print(f"[PASS] Config: {cfg.config_path}")
    print(f"[PASS] Train file: {cfg.train_file}")
    print(f"[PASS] Held-out file: {cfg.held_out_file}")
    print(f"[PASS] Eval questions: {cfg.questions_path}")
    print(f"[PASS] Baseline manifest: {cfg.baseline_manifest}")
    print(f"[INFO] eval_family={cfg.eval_family}")
    print(f"[INFO] train_package_sha256={train_sha}")
    print(f"[INFO] heldout_rows={heldout_rows}")
    print(f"[INFO] total_examples={total}")
    print(f"[INFO] clean_examples={clean}")
    print(f"[INFO] flagged_examples={flagged}")
    print(f"[INFO] min_clean_examples={cfg.min_clean_examples}")
    print(f"[INFO] output_dir={cfg.output_dir}")

    if clean < cfg.min_clean_examples:
        print(
            "[FAIL] Data gate gecmedi: "
            f"clean_examples ({clean}) < min_clean_examples ({cfg.min_clean_examples})"
        )
        return 1

    if cfg.expected_train_sha256 and train_sha != cfg.expected_train_sha256:
        print(
            "[FAIL] Train package SHA uyusmuyor: "
            f"actual={train_sha} expected={cfg.expected_train_sha256}"
        )
        return 1

    if cfg.expected_heldout_rows and heldout_rows != cfg.expected_heldout_rows:
        print(
            "[FAIL] Held-out row count uyusmuyor: "
            f"actual={heldout_rows} expected={cfg.expected_heldout_rows}"
        )
        return 1

    readiness_command = build_readiness_command(cfg.config_path)
    print("[INFO] readiness_command=" + " ".join(str(part) for part in readiness_command))
    readiness = subprocess.run(readiness_command, cwd=cfg.repo_root, check=False)
    if readiness.returncode != 0:
        print("[FAIL] check_training_readiness.py preflight fail verdi")
        return readiness.returncode

    print("[RESULT] READY_FOR_TRAINING_GATE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
