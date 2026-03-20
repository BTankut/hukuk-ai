#!/usr/bin/env python3
"""Shared helpers for the fine-tune handoff package."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HandoffConfig:
    config_path: Path
    repo_root: Path
    payload: dict[str, Any]
    train_file: Path
    held_out_file: Path
    questions_path: Path
    baseline_manifest: Path
    output_dir: Path
    eval_family: str
    min_clean_examples: int
    placeholder_markers: list[str]
    report_dir: Path
    expected_train_sha256: str
    expected_heldout_rows: int
    max_question_duplicate_excess: int
    max_tokens: int
    delay_seconds: float
    timeout_seconds: float
    workflow_files: list[Path]


def _discover_repo_root(config_path: Path) -> Path:
    resolved = config_path.resolve()
    for parent in resolved.parents:
        if parent.name == "configs":
            return parent.parent
    return resolved.parent


def resolve_repo_path(repo_root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return repo_root / path


def load_handoff_config(config_path: Path) -> HandoffConfig:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    repo_root = _discover_repo_root(config_path)

    data_cfg = payload.get("data", {})
    eval_cfg = payload.get("evaluation", {})
    output_cfg = payload.get("output", {})

    return HandoffConfig(
        config_path=config_path.resolve(),
        repo_root=repo_root.resolve(),
        payload=payload,
        train_file=resolve_repo_path(repo_root, str(data_cfg.get("train_file", ""))),
        held_out_file=resolve_repo_path(repo_root, str(data_cfg.get("held_out_file", ""))),
        questions_path=resolve_repo_path(repo_root, str(eval_cfg.get("questions_path", ""))),
        baseline_manifest=resolve_repo_path(repo_root, str(eval_cfg.get("baseline_manifest", ""))),
        output_dir=resolve_repo_path(repo_root, str(output_cfg.get("dir", ""))),
        eval_family=str(eval_cfg.get("eval_family", "")).strip(),
        min_clean_examples=int(data_cfg.get("min_clean_examples", 0)),
        placeholder_markers=[str(item) for item in data_cfg.get("placeholder_markers", [])],
        report_dir=resolve_repo_path(repo_root, str(eval_cfg.get("report_dir", "evaluation/reports"))),
        expected_train_sha256=str(data_cfg.get("expected_train_sha256", "")).strip(),
        expected_heldout_rows=int(data_cfg.get("expected_heldout_rows", 0)),
        max_question_duplicate_excess=int(eval_cfg.get("max_question_duplicate_excess", 0)),
        max_tokens=int(eval_cfg.get("max_tokens", 3000)),
        delay_seconds=float(eval_cfg.get("delay_seconds", 1.0)),
        timeout_seconds=float(eval_cfg.get("timeout_seconds", 300.0)),
        workflow_files=[
            resolve_repo_path(repo_root, str(item))
            for item in eval_cfg.get("workflow_files", [])
        ],
    )


def count_clean_examples(data_file: Path, placeholder_markers: list[str]) -> tuple[int, int, int]:
    total = 0
    clean = 0
    flagged = 0

    for line_no, line in enumerate(data_file.read_text(encoding="utf-8").splitlines(), start=1):
        row_text = line.strip()
        if not row_text:
            continue
        total += 1
        try:
            row = json.loads(row_text)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"[FAIL] JSON parse error @ line {line_no}: {exc}") from exc

        content = " ".join(str(row.get(key, "")) for key in ("instruction", "input", "output"))
        if any(marker in content for marker in placeholder_markers):
            flagged += 1
            continue
        clean += 1

    return total, clean, flagged


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
