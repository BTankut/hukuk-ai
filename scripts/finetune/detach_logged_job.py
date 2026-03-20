#!/usr/bin/env python3
"""Launch a background job with stdout/stderr redirected to a log file."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Detach a background job and record pid/log paths.")
    parser.add_argument("--workdir", default=".", help="Working directory for the child process.")
    parser.add_argument("--log-path", required=True, type=Path, help="Path to the combined stdout/stderr log file.")
    parser.add_argument("--pid-path", required=True, type=Path, help="Path to the pid file.")
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to the log file instead of truncating it before launch.",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to launch. Prefix with -- to separate launcher args from child args.",
    )
    return parser


def normalize_command(raw_command: list[str]) -> list[str]:
    if raw_command and raw_command[0] == "--":
        raw_command = raw_command[1:]
    if not raw_command:
        raise SystemExit("[FAIL] No child command provided.")
    return raw_command


def main() -> int:
    args = build_parser().parse_args()
    command = normalize_command(args.command)

    log_path = args.log_path.resolve()
    pid_path = args.pid_path.resolve()
    workdir = Path(args.workdir).resolve()
    if not workdir.exists():
        raise SystemExit(f"[FAIL] Workdir not found: {workdir}")

    log_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if args.append else "w"

    with open(log_path, mode, encoding="utf-8") as handle:
        process = subprocess.Popen(
            command,
            cwd=str(workdir),
            stdin=subprocess.DEVNULL,
            stdout=handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    pid_path.write_text(f"{process.pid}\n", encoding="utf-8")
    payload = {
        "pid": process.pid,
        "log_path": str(log_path),
        "pid_path": str(pid_path),
        "workdir": str(workdir),
        "command": command,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
