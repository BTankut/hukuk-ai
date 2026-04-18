from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path


def read_pid(pid_path: Path) -> int | None:
    if not pid_path.exists():
        return None
    raw = pid_path.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def extract_env_value(ps_output: str, key: str) -> str | None:
    prefix = f"{key}="
    for token in ps_output.split():
        if token.startswith(prefix):
            return token[len(prefix) :]
    return None


def process_env_value(pid: int, key: str) -> str | None:
    result = subprocess.run(
        ["ps", "eww", "-p", str(pid)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return extract_env_value(result.stdout, key)


def listener_pids(port: int) -> list[int]:
    result = subprocess.run(
        ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 and not result.stdout.strip():
        return []
    pids: list[int] = []
    for raw in result.stdout.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            pids.append(int(raw))
        except ValueError:
            continue
    return sorted(set(pids))


def pid_owns_listener(pid: int | None, port: int) -> bool:
    if pid is None:
        return False
    return pid in listener_pids(port)


def terminate_pid(pid: int, *, timeout: float = 10.0) -> None:
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.2)

    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        return


def stop_pid_file(pid_path: Path) -> None:
    pid = read_pid(pid_path)
    if pid is None:
        return
    terminate_pid(pid)


def stop_listener_port(port: int) -> list[int]:
    pids = listener_pids(port)
    for pid in pids:
        terminate_pid(pid)
    return pids


def wait_for_port_closed(port: int, *, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not listener_pids(port):
            return True
        time.sleep(0.2)
    return False


def stop_pid_and_listener(pid_path: Path, port: int) -> dict[str, object]:
    before_pid = read_pid(pid_path)
    before_listeners = listener_pids(port)
    if before_pid is not None:
        terminate_pid(before_pid)
    remaining = [pid for pid in listener_pids(port) if pid != before_pid]
    for pid in remaining:
        terminate_pid(pid)
    port_closed = wait_for_port_closed(port)
    return {
        "pidfile_pid_before": before_pid,
        "listener_pids_before": before_listeners,
        "listener_pids_after": listener_pids(port),
        "port_closed": port_closed,
    }


def wait_for_pidfile_listener_match(pid_path: Path, port: int, *, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        pid = read_pid(pid_path)
        if pid_owns_listener(pid, port):
            return True
        time.sleep(0.2)
    return False
