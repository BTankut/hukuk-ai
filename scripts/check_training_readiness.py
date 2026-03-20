#!/usr/bin/env python3
"""Training readiness gate for lawyer-reviewed fine-tuning runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
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


@dataclass(slots=True)
class EvidenceManifest:
    path: Path
    role: str
    eval_family: str
    model_ref: str
    checkpoint_ref: str
    git_commit: str
    report_path: Path
    report_sha256: str


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


def _check_question_duplicates(train_file: Path, max_duplicate_excess: int) -> CheckItem:
    train_records = _load_jsonl_records(train_file)
    questions = [_extract_question(record) for record in train_records]
    questions = [question for question in questions if question]

    counts = Counter(questions)
    duplicate_groups = [(question, count) for question, count in counts.items() if count > 1]
    duplicate_groups.sort(key=lambda item: (-item[1], item[0]))

    duplicate_excess = sum(count - 1 for _, count in duplicate_groups)
    if duplicate_excess > max_duplicate_excess:
        sample = [f"{question} (x{count})" for question, count in duplicate_groups[:3]]
        return CheckItem(
            name="Question duplicate check",
            ok=False,
            detail=(
                f"{len(duplicate_groups)} duplicate question groups, "
                f"{duplicate_excess} excess rows, threshold={max_duplicate_excess}, "
                f"sample={sample}"
            ),
        )

    return CheckItem(
        name="Question duplicate check",
        ok=True,
        detail=(
            f"{len(counts)} unique questions, "
            f"{duplicate_excess} excess duplicate rows (threshold={max_duplicate_excess})"
        ),
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


def _resolve_repo_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve()


def _parse_evidence_manifest(path: Path) -> tuple[EvidenceManifest | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"unreadable JSON ({exc})"

    if not isinstance(payload, dict):
        return None, "manifest must be a JSON object"

    required_fields = [
        "manifest_version",
        "role",
        "eval_family",
        "model_ref",
        "checkpoint_ref",
        "git_commit",
        "report_path",
        "report_sha256",
    ]
    missing = [field for field in required_fields if not payload.get(field)]
    if missing:
        return None, f"missing required fields: {', '.join(missing)}"

    role = str(payload["role"]).strip()
    if role not in {"baseline", "post_train"}:
        return None, f"invalid role={role!r}"

    report_path = _resolve_repo_path(str(payload["report_path"]))
    if not report_path.exists():
        return None, f"report path missing: {report_path}"

    actual_sha256 = hashlib.sha256(report_path.read_bytes()).hexdigest()
    expected_sha256 = str(payload["report_sha256"]).strip()
    if actual_sha256 != expected_sha256:
        return None, (
            "report sha256 mismatch: "
            f"expected={expected_sha256} actual={actual_sha256}"
        )

    return (
        EvidenceManifest(
            path=path,
            role=role,
            eval_family=str(payload["eval_family"]).strip(),
            model_ref=str(payload["model_ref"]).strip(),
            checkpoint_ref=str(payload["checkpoint_ref"]).strip(),
            git_commit=str(payload["git_commit"]).strip(),
            report_path=report_path,
            report_sha256=expected_sha256,
        ),
        None,
    )


def _check_evidence_manifests(
    paths: list[Path],
    *,
    label: str,
    allowed_roles: set[str],
    expected_eval_family: str | None = None,
) -> tuple[CheckItem, list[EvidenceManifest]]:
    if not paths:
        return CheckItem(name=label, ok=False, detail="no paths provided"), []

    manifests: list[EvidenceManifest] = []
    errors: list[str] = []
    for path in paths:
        if not path.exists():
            errors.append(f"{path}: missing manifest file")
            continue

        manifest, error = _parse_evidence_manifest(path)
        if error:
            errors.append(f"{path}: {error}")
            continue
        if manifest.role not in allowed_roles:
            errors.append(
                f"{path}: role {manifest.role!r} not allowed (expected one of {sorted(allowed_roles)})"
            )
            continue
        if expected_eval_family and manifest.eval_family != expected_eval_family:
            errors.append(
                f"{path}: eval_family={manifest.eval_family!r} != expected {expected_eval_family!r}"
            )
            continue
        manifests.append(manifest)

    if errors:
        return CheckItem(name=label, ok=False, detail="; ".join(errors)), []

    families = sorted({manifest.eval_family for manifest in manifests})
    checkpoints = sorted({manifest.checkpoint_ref for manifest in manifests})
    return (
        CheckItem(
            name=label,
            ok=True,
            detail=(
                f"{len(manifests)} manifest(s), eval_family={families}, "
                f"checkpoint_ref={checkpoints}"
            ),
        ),
        manifests,
    )


def _check_promotion_evidence_contract(
    baseline_manifests: list[EvidenceManifest],
    post_train_manifests: list[EvidenceManifest],
    expected_eval_family: str | None = None,
) -> CheckItem:
    baseline_families = {manifest.eval_family for manifest in baseline_manifests}
    post_train_families = {manifest.eval_family for manifest in post_train_manifests}
    if baseline_families != post_train_families:
        return CheckItem(
            name="Promotion evidence contract",
            ok=False,
            detail=(
                f"baseline eval families {sorted(baseline_families)} do not match "
                f"post-train eval families {sorted(post_train_families)}"
            ),
        )

    if expected_eval_family and baseline_families != {expected_eval_family}:
        return CheckItem(
            name="Promotion evidence contract",
            ok=False,
            detail=(
                f"eval family mismatch: expected {expected_eval_family!r}, "
                f"got {sorted(baseline_families)}"
            ),
        )

    baseline_checkpoints = {manifest.checkpoint_ref for manifest in baseline_manifests}
    post_train_checkpoints = {manifest.checkpoint_ref for manifest in post_train_manifests}
    if len(baseline_checkpoints) != 1:
        return CheckItem(
            name="Promotion evidence contract",
            ok=False,
            detail=f"baseline evidence has multiple checkpoint refs: {sorted(baseline_checkpoints)}",
        )
    if len(post_train_checkpoints) != 1:
        return CheckItem(
            name="Promotion evidence contract",
            ok=False,
            detail=f"post-train evidence has multiple checkpoint refs: {sorted(post_train_checkpoints)}",
        )
    if baseline_checkpoints == post_train_checkpoints:
        return CheckItem(
            name="Promotion evidence contract",
            ok=False,
            detail=f"baseline and post-train checkpoint_ref are identical: {sorted(baseline_checkpoints)}",
        )

    return CheckItem(
        name="Promotion evidence contract",
        ok=True,
        detail=(
            f"eval_family={sorted(baseline_families)} | "
            f"baseline_checkpoint={sorted(baseline_checkpoints)} | "
            f"post_train_checkpoint={sorted(post_train_checkpoints)}"
        ),
    )


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
    parser.add_argument(
        "--max-question-duplicate-excess",
        type=int,
        default=0,
        help="Maximum allowed duplicate question excess rows inside the train set.",
    )
    parser.add_argument(
        "--expected-eval-family",
        help="Expected evaluation family label shared by baseline and post-train evidence manifests (example: faz1-50).",
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

    if train_file.exists():
        try:
            checks.append(
                _check_question_duplicates(
                    train_file,
                    max_duplicate_excess=args.max_question_duplicate_excess,
                )
            )
        except (json.JSONDecodeError, OSError) as exc:
            checks.append(
                CheckItem(
                    name="Question duplicate check",
                    ok=False,
                    detail=f"unable to scan train JSONL duplicates: {exc}",
                )
            )

    checks.append(_scan_forbidden_refs(workflow_files, args.forbidden_ref))

    baseline_item, baseline_manifests = _check_evidence_manifests(
        baseline_paths,
        label="Baseline evidence manifest",
        allowed_roles={"baseline"},
        expected_eval_family=args.expected_eval_family,
    )
    checks.append(baseline_item)

    if args.mode == "promotion":
        post_train_item, post_train_manifests = _check_evidence_manifests(
            post_train_paths,
            label="Post-train evidence manifest",
            allowed_roles={"post_train"},
            expected_eval_family=args.expected_eval_family,
        )
        checks.append(post_train_item)
        if baseline_item.ok and post_train_item.ok:
            checks.append(
                _check_promotion_evidence_contract(
                    baseline_manifests,
                    post_train_manifests,
                    expected_eval_family=args.expected_eval_family,
                )
            )
    elif post_train_paths:
        optional_item, _ = _check_evidence_manifests(
            post_train_paths,
            label="Optional post-train evidence manifest",
            allowed_roles={"post_train"},
            expected_eval_family=args.expected_eval_family,
        )
        checks.append(optional_item)

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
