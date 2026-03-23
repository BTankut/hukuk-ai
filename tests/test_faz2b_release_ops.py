from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "faz2b"))

import ensure_release_lane as lane_ops  # noqa: E402
from backup_release_state import create_backup_bundle  # noqa: E402
from ensure_release_lane import check_lane_status, ensure_lane  # noqa: E402
from restore_release_state import restore_backup_bundle  # noqa: E402


def test_check_lane_status_reports_healthy_lane(tmp_path: Path, monkeypatch: object) -> None:
    gateway_pid = tmp_path / "gateway.pid"
    tunnel_pid = tmp_path / "tunnel.pid"
    audit_log = tmp_path / "api_audit.jsonl"
    gateway_pid.write_text(f"{os.getpid()}\n", encoding="utf-8")
    tunnel_pid.write_text(f"{os.getpid()}\n", encoding="utf-8")
    audit_log.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(lane_ops, "http_ok", lambda *args, **kwargs: True)

    status = check_lane_status(
        gateway_pid_path=gateway_pid,
        tunnel_pid_path=tunnel_pid,
        health_url="http://release-lane/v1/health",
        metrics_url="http://release-lane/v1/metrics",
        audit_log_path=audit_log,
    )

    assert status.healthy is True
    assert status.gateway_pid_running is True
    assert status.tunnel_pid_running is True
    assert status.health_ok is True
    assert status.metrics_ok is True
    assert status.audit_log_exists is True
    assert status.errors == []


def test_ensure_lane_requests_restart_on_unhealthy_dry_run(tmp_path: Path) -> None:
    launch_script = tmp_path / "launch.sh"
    launch_script.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    launch_script.chmod(0o755)

    status = ensure_lane(
        launch_script=launch_script,
        gateway_pid_path=tmp_path / "missing.pid",
        tunnel_pid_path=tmp_path / "missing_tunnel.pid",
        health_url="http://127.0.0.1:9/v1/health",
        metrics_url="http://127.0.0.1:9/v1/metrics",
        audit_log_path=tmp_path / "missing.log",
        restart=True,
        dry_run=True,
    )

    assert status.healthy is False
    assert status.restart_requested is True
    assert status.restart_executed is False
    assert "gateway_pid_not_running" in status.errors
    assert "health_failed" in status.errors


def test_backup_restore_bundle_roundtrip(tmp_path: Path, monkeypatch: object) -> None:
    include_path = tmp_path / "lane.env"
    include_path.write_text("DGX_MODEL=example\n", encoding="utf-8")
    monkeypatch.setenv("API_AUTH_ENABLED", "true")
    monkeypatch.setenv("SESSION_STORE_BACKEND", "redis")

    manifest_path = create_backup_bundle(
        output_dir=tmp_path / "backups",
        label="release_lane",
        env_keys=["API_AUTH_ENABLED", "SESSION_STORE_BACKEND"],
        include_paths=[include_path],
    )
    summary_path = restore_backup_bundle(
        manifest_path=manifest_path,
        restore_dir=tmp_path / "restore",
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    restore_env = (tmp_path / "restore" / "restore.env.sh").read_text(encoding="utf-8")

    assert manifest["env"]["API_AUTH_ENABLED"] == "true"
    assert manifest["env"]["SESSION_STORE_BACKEND"] == "redis"
    assert manifest["files"][0]["source_path"] == str(include_path)
    assert summary["files"][0]["exists"] is True
    assert "export API_AUTH_ENABLED=true" in restore_env
    assert "export SESSION_STORE_BACKEND=redis" in restore_env
