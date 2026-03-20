#!/usr/bin/env python3
"""Training readiness gate for lawyer-reviewed fine-tuning runs."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TRAIN_FILE = PROJECT_ROOT / "data/finetune/sft/final_train.jsonl"
DEFAULT_HELDOUT_FILE = PROJECT_ROOT / "data/finetune/eval/held_out_test.jsonl"
DEFAULT_FORBIDDEN_REF = "data/finetune/sft_training_v1.jsonl"
DEFAULT_WORKFLOW_FILE = PROJECT_ROOT / "scripts/build_training_dataset.py"

from validate_ft_data import validate_sft_file  # noqa: E402


@dataclass(slots=True)
class CheckItem:
    name: str
    ok: bool
    detail: str


def _print_check(item: CheckItem) -> None:
    status = "PASS" if item.ok else "FAIL"
    print(f"[{status}] {item.name}: {item.detail}")


def _load_jsonl_records(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def _extract_question(record: dict) -> str:
    raw = record.get("input") or record.get("question") or ""
    if not isinstance(raw, str):
        return ""
    if "\n\nSORU:" in raw:
        return raw.split("\n\nSORU:", 1)[1].strip()
    if "SORU:" in raw:
        return raw.split("SORU:", 1)[1].strip()
    return raw.strip()


def _scan_forbidden_refs(paths: Iterable[Path], forbidden_ref: str) -> CheckItem:
    offenders: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            offenders.append(f"{path}: unreadable ({exc})")
            continue
        if forbidden_ref in content:
            offenders.append(str(path))

    if offenders:
        return CheckItem(
            name="Forbidden v1 reference scan",
            ok=False,
            detail=f"found '{forbidden_ref}' in: {', '.join(offenders)}",
        )

    return CheckItem(
        name="Forbidden v1 reference scan",
        ok=True,
        detail=f"no active workflow file references '{forbidden_ref}'",
    )


def _check_schema(path: Path, dataset_type: str) -> CheckItem:
    ok = validate_sft_file(str(path))
    return CheckItem(
        name=f"Schema validation ({dataset_type})",
        ok=ok,
        detail=f"{path}",
    )


def _check_existence(path: Path, label: str) -> CheckItem:
    ok = path.exists()
    return CheckItem(
        name=label,
        ok=ok,
        detail=str(path) if ok else f"missing: {path}",
    )


def _check_leakage(train_file: Path, heldout_file: Path) -> CheckItem:
    train_records = _load_jsonl_records(train_file)
    heldout_records = _load_jsonl_records(heldout_file)

    train_questions = {_extract_question(record) for record in train_records}
    train_questions.discard("")
    heldout_questions = {_extract_question(record) for record in heldout_records}
    heldout_questions.discard("")

    overlap = sorted(train_questions.intersection(heldout_questions))
    if overlap:
        sample = overlap[:3]
        return CheckItem(
            name="Held-out leakage check",
            ok=False,
            detail=f"{len(overlap)} overlapping questions, sample={sample}",
        )

    return CheckItem(
        name="Held-out leakage check",
        ok=True,
        detail=f"{len(train_questions)} train questions vs {len(heldout_questions)} held-out questions",
    )


def _check_required_paths(paths: list[Path], label: str) -> CheckItem:
    if not paths:
        return CheckItem(name=label, ok=False, detail="no paths provided")
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        return CheckItem(
            name=label,
            ok=False,
            detail=f"missing: {', '.join(missing)}",
        )
    return CheckItem(name=label, ok=True, detail=f"{len(paths)} paths present")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check fine-tuning readiness gates.")
    parser.add_argument(
        "--mode",
        choices=("preflight", "promotion"),
        default="preflight",
        help="preflight checks training prerequisites, promotion also requires post-train evidence.",
    )
    parser.add_argument(
        "--train-file",
        default=str(DEFAULT_TRAIN_FILE),
        help="Final lawyer-reviewed SFT dataset path.",
    )
    parser.add_argument(
        "--heldout-file",
        default=str(DEFAULT_HELDOUT_FILE),
        help="Held-out SFT evaluation set path.",
    )
    parser.add_argument(
        "--workflow-file",
        action="append",
        default=[str(DEFAULT_WORKFLOW_FILE)],
        help="Active workflow file to scan for forbidden v1 references. May be repeated.",
    )
    parser.add_argument(
        "--baseline-evidence-path",
        action="append",
        default=[],
        help="Baseline evaluation artifact path. May be repeated.",
    )
    parser.add_argument(
        "--post-train-evidence-path",
        action="append",
        default=[],
        help="Post-train evaluation artifact path. May be repeated.",
    )
    parser.add_argument(
        "--forbidden-ref",
        default=DEFAULT_FORBIDDEN_REF,
        help="Forbidden dataset path string to scan for in workflow files.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    train_file = Path(args.train_file)
    heldout_file = Path(args.heldout_file)
    workflow_files = [Path(path) for path in args.workflow_file]
    baseline_paths = [Path(path) for path in args.baseline_evidence_path]
    post_train_paths = [Path(path) for path in args.post_train_evidence_path]

    checks: list[CheckItem] = []

    checks.append(_check_existence(train_file, "Train file exists"))
    checks.append(_check_existence(heldout_file, "Held-out file exists"))

    if train_file.exists():
        checks.append(_check_schema(train_file, "sft"))
    if heldout_file.exists():
        checks.append(_check_schema(heldout_file, "sft"))

    if train_file.exists() and heldout_file.exists():
        try:
            checks.append(_check_leakage(train_file, heldout_file))
        except (json.JSONDecodeError, OSError) as exc:
            checks.append(
                CheckItem(
                    name="Held-out leakage check",
                    ok=False,
                    detail=f"unable to compare train and held-out JSONL: {exc}",
                )
            )

    checks.append(_scan_forbidden_refs(workflow_files, args.forbidden_ref))
    checks.append(_check_required_paths(baseline_paths, "Baseline evidence"))

    if args.mode == "promotion":
        checks.append(_check_required_paths(post_train_paths, "Post-train evidence"))
    elif post_train_paths:
        checks.append(_check_required_paths(post_train_paths, "Optional post-train evidence"))

    print("Training readiness report")
    print("=" * 24)

    all_ok = True
    for item in checks:
        _print_check(item)
        all_ok = all_ok and item.ok

    print("=" * 24)
    print("READY" if all_ok else "NOT READY")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
