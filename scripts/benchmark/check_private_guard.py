#!/usr/bin/env python3
"""Fail if hukuk-ai benchmark private inputs can be committed accidentally."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PRIVATE_PATTERNS = (
    "evaluation/private/",
    "hukuk_ai_100_answer_key_private.csv",
    "hukuk_ai_benchmark_answer_key_private.csv",
    "hukuk_ai_100_master.csv",
    "hukuk_ai_benchmark_master.csv",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path)
    return parser.parse_args()


def run_git(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def tracked_private_files() -> list[str]:
    result = run_git(["ls-files", "-z"], check=True)
    files = [item for item in result.stdout.split("\0") if item]
    return [path for path in files if any(pattern in path for pattern in PRIVATE_PATTERNS)]


def check_ignored(path: Path) -> bool:
    result = run_git(["check-ignore", "-q", str(path)], check=False)
    return result.returncode == 0


def main() -> int:
    args = parse_args()
    local_private_key = Path("evaluation/private/hukuk_ai_100_answer_key_private.csv")
    violations = tracked_private_files()
    private_key_ignored = check_ignored(local_private_key)
    summary = {
        "private_key_path": str(local_private_key),
        "private_key_ignored": private_key_ignored,
        "tracked_private_file_count": len(violations),
        "tracked_private_files": violations,
        "status": "pass" if private_key_ignored and not violations else "fail",
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
