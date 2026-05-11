#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REQUIRED_COMMITS = ("f0e50b06", "2124942b", "28732f04")
LOCK_TAG = "mevzuat-engine-closed-20260511"
ROOT = Path(__file__).resolve().parents[2]
MEVZUAT_LOCK_ARTIFACT = ROOT / "evaluation/reports/mevzuat_engine_closure_20260511.json"
JUDICIAL_PREP_ARTIFACT = ROOT / "evaluation/reports/judicial_corpus_prep_20260511.json"


def _fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _commit_exists(commit: str) -> bool:
    return subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def _load_json(path: Path) -> dict:
    if not path.exists():
        _fail(f"missing required artifact: {path.relative_to(ROOT)}")
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        _fail(f"artifact is not a JSON object: {path.relative_to(ROOT)}")
    return payload


def _check_mevzuat_closed() -> None:
    missing = [commit for commit in REQUIRED_COMMITS if not _commit_exists(commit)]
    if missing:
        _fail(f"missing required mevzuat closure commits: {missing}")

    try:
        tag_target = _git("rev-list", "-n", "1", LOCK_TAG)
    except subprocess.CalledProcessError as exc:
        _fail(f"missing lock tag {LOCK_TAG}: {exc}")

    required_target = _git("rev-parse", "28732f04")
    if tag_target != required_target:
        _fail(f"lock tag {LOCK_TAG} points to {tag_target}, expected {required_target}")

    artifact = _load_json(MEVZUAT_LOCK_ARTIFACT)
    if not str(artifact.get("acceptance_status") or "").startswith("PASS"):
        _fail("mevzuat closure artifact is not passing")

    lock = artifact.get("acceptance_lock")
    if not isinstance(lock, dict):
        _fail("mevzuat closure artifact missing acceptance_lock block")

    state = lock.get("canonical_state") or {}
    if state.get("MEVZUAT_ENGINE_STATUS") != "production-candidate closed":
        _fail("MEVZUAT_ENGINE_STATUS is not locked closed")
    if state.get("JUDICIAL_CORPUS_STATUS") != "pending corpus/download completion":
        _fail("JUDICIAL_CORPUS_STATUS is not pending corpus/download completion")


def _check_judicial_runtime_disabled() -> None:
    enabled_value = os.getenv("JUDICIAL_RUNTIME_ENABLED", "false").strip().lower()
    if enabled_value in {"1", "true", "yes", "on"}:
        _fail("JUDICIAL_RUNTIME_ENABLED must remain false before judicial corpus closure")

    artifact = _load_json(JUDICIAL_PREP_ARTIFACT)
    if artifact.get("acceptance_status") != "PASS_LOCAL_ONLY":
        _fail("judicial prep artifact must be PASS_LOCAL_ONLY")

    runtime = artifact.get("runtime_disabled_confirmation") or {}
    if runtime.get("pass") is not True or runtime.get("runtime_enabled") is not False:
        _fail("judicial prep artifact does not confirm runtime-disabled state")

    lane = artifact.get("judicial_retrieval_lane_status") or {}
    if lane.get("status") != "prepared_offline_disabled_runtime":
        _fail("judicial retrieval lane is not marked offline-only/runtime-disabled")

    gate = artifact.get("judicial_gate_skeleton_status") or {}
    if gate.get("active") is not False:
        _fail("judicial gate must remain inactive until corpus download/indexing completes")


def main() -> int:
    _check_mevzuat_closed()
    _check_judicial_runtime_disabled()
    print("closed runtime state gates passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
