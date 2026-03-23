#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path


def read_pid(pid_path: Path | None) -> int | None:
    if pid_path is None or not pid_path.exists():
        return None
    try:
        return int(pid_path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def pid_running(pid: int | None) -> bool:
    if pid is None or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def http_ok(url: str | None, *, api_key: str | None = None, timeout: float = 5.0) -> bool:
    if not url:
        return True
    request = urllib.request.Request(url)
    if api_key:
        request.add_header("X-API-Key", api_key)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError, ValueError):
        return False


@dataclass
class LaneStatus:
    gateway_pid: int | None
    gateway_pid_running: bool
    tunnel_pid: int | None
    tunnel_pid_running: bool
    health_ok: bool
    metrics_ok: bool
    audit_log_exists: bool
    healthy: bool
    restart_requested: bool = False
    restart_executed: bool = False
    errors: list[str] = field(default_factory=list)


def check_lane_status(
    *,
    gateway_pid_path: Path,
    health_url: str,
    tunnel_pid_path: Path | None = None,
    metrics_url: str | None = None,
    audit_log_path: Path | None = None,
    api_key: str | None = None,
) -> LaneStatus:
    gateway_pid = read_pid(gateway_pid_path)
    tunnel_pid = read_pid(tunnel_pid_path)
    gateway_pid_alive = pid_running(gateway_pid)
    tunnel_pid_alive = pid_running(tunnel_pid) if tunnel_pid_path else True
    health_ok = http_ok(health_url, timeout=5.0)
    metrics_ok = http_ok(metrics_url, api_key=api_key, timeout=5.0)
    audit_log_exists = True if audit_log_path is None else audit_log_path.exists()

    errors: list[str] = []
    if not gateway_pid_alive:
        errors.append("gateway_pid_not_running")
    if tunnel_pid_path and not tunnel_pid_alive:
        errors.append("tunnel_pid_not_running")
    if not health_ok:
        errors.append("health_failed")
    if not metrics_ok:
        errors.append("metrics_failed")
    if audit_log_path is not None and not audit_log_exists:
        errors.append("audit_log_missing")

    return LaneStatus(
        gateway_pid=gateway_pid,
        gateway_pid_running=gateway_pid_alive,
        tunnel_pid=tunnel_pid,
        tunnel_pid_running=tunnel_pid_alive,
        health_ok=health_ok,
        metrics_ok=metrics_ok,
        audit_log_exists=audit_log_exists,
        healthy=not errors,
        errors=errors,
    )


def ensure_lane(
    *,
    launch_script: Path,
    gateway_pid_path: Path,
    health_url: str,
    tunnel_pid_path: Path | None = None,
    metrics_url: str | None = None,
    audit_log_path: Path | None = None,
    api_key: str | None = None,
    restart: bool = False,
    dry_run: bool = False,
) -> LaneStatus:
    status = check_lane_status(
        gateway_pid_path=gateway_pid_path,
        tunnel_pid_path=tunnel_pid_path,
        health_url=health_url,
        metrics_url=metrics_url,
        audit_log_path=audit_log_path,
        api_key=api_key,
    )
    if status.healthy or not restart:
        return status

    status.restart_requested = True
    if dry_run:
        return status

    completed = subprocess.run(
        [str(launch_script)],
        check=False,
        capture_output=True,
        text=True,
    )
    status.restart_executed = completed.returncode == 0
    if completed.returncode != 0:
        status.errors.append("restart_failed")
    return status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check or restart a release lane.")
    parser.add_argument("--launch-script", type=Path, required=True)
    parser.add_argument("--gateway-pid-path", type=Path, required=True)
    parser.add_argument("--health-url", required=True)
    parser.add_argument("--tunnel-pid-path", type=Path)
    parser.add_argument("--metrics-url")
    parser.add_argument("--audit-log-path", type=Path)
    parser.add_argument("--api-key")
    parser.add_argument("--restart", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    status = ensure_lane(
        launch_script=args.launch_script,
        gateway_pid_path=args.gateway_pid_path,
        health_url=args.health_url,
        tunnel_pid_path=args.tunnel_pid_path,
        metrics_url=args.metrics_url,
        audit_log_path=args.audit_log_path,
        api_key=args.api_key,
        restart=args.restart,
        dry_run=args.dry_run,
    )
    print(json.dumps(asdict(status), ensure_ascii=False, indent=2))
    return 0 if status.healthy or status.restart_requested else 1


if __name__ == "__main__":
    raise SystemExit(main())
