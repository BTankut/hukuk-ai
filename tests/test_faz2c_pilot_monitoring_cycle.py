from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "faz2c"))

import run_pilot_monitoring_cycle as cycle  # noqa: E402


def test_cycle_main_writes_full_bundle(tmp_path: Path, monkeypatch: object) -> None:
    sample_iter = iter(
        [
            {
                "captured_at": "2026-03-23T08:45:00Z",
                "rollback_recommended": False,
                "rollback_reasons": [],
                "health": {"status": "ok"},
                "smoke": {"ok": True, "latency_ms": 1000.0},
                "metrics_delta": {
                    "audit_events_delta": 1,
                    "upstream_usage_delta": 1,
                    "successful_chat_delta": 1,
                    "refusal_delta": 0,
                },
            },
            {
                "captured_at": "2026-03-23T08:46:00Z",
                "rollback_recommended": False,
                "rollback_reasons": [],
                "health": {"status": "ok"},
                "smoke": {"ok": True, "latency_ms": 1100.0},
                "metrics_delta": {
                    "audit_events_delta": 1,
                    "upstream_usage_delta": 1,
                    "successful_chat_delta": 1,
                    "refusal_delta": 0,
                },
            },
        ]
    )
    monkeypatch.setattr(cycle, "capture_snapshot", lambda **kwargs: next(sample_iter))
    monkeypatch.setattr(cycle, "_utc_stamp", lambda: "20260323T091500Z")

    output_dir = tmp_path / "cycles"
    watch_root = tmp_path / "watch_jobs"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_pilot_monitoring_cycle.py",
            "--samples",
            "2",
            "--sleep-seconds",
            "0",
            "--watch-root",
            str(watch_root),
            "--output-dir",
            str(output_dir),
            "--snapshot-path",
            str(tmp_path / "faz2c_narrow_pilot_snapshot.json"),
            "--canonical-rollup-path",
            str(tmp_path / "faz2c_watch_rollup.json"),
            "--canonical-status-report-path",
            str(tmp_path / "faz2c_pilot_status_report.md"),
        ],
    )

    result = cycle.main()

    assert result == 0
    cycle_dir = output_dir / "pilot_monitoring_cycle_20260323T091500Z"
    manifest = json.loads((cycle_dir / "cycle_manifest.json").read_text(encoding="utf-8"))
    rollup = json.loads((cycle_dir / "rollup.json").read_text(encoding="utf-8"))
    report = (cycle_dir / "pilot_status_report.md").read_text(encoding="utf-8")
    canonical_snapshot = json.loads((tmp_path / "faz2c_narrow_pilot_snapshot.json").read_text(encoding="utf-8"))
    canonical_rollup = json.loads((tmp_path / "faz2c_watch_rollup.json").read_text(encoding="utf-8"))
    canonical_report = (tmp_path / "faz2c_pilot_status_report.md").read_text(encoding="utf-8")
    latest_manifest = json.loads((output_dir / "latest_cycle_manifest.json").read_text(encoding="utf-8"))
    latest_rollup = json.loads((output_dir / "latest_rollup.json").read_text(encoding="utf-8"))
    latest_index = json.loads((output_dir / "latest_cycle_index.json").read_text(encoding="utf-8"))
    latest_report = (output_dir / "latest_pilot_status_report.md").read_text(encoding="utf-8")
    watch_job_dir = watch_root / "narrow_pilot_watch_20260323T091500Z"

    assert manifest["final_read"] == "stay_on_promoted_lane"
    assert manifest["snapshot_path"] == str(tmp_path / "faz2c_narrow_pilot_snapshot.json")
    assert manifest["canonical_rollup_path"] == str(tmp_path / "faz2c_watch_rollup.json")
    assert manifest["latest_cycle_manifest_path"] == str(output_dir / "latest_cycle_manifest.json")
    assert rollup["job_count"] == 1
    assert canonical_snapshot["captured_at"] == "2026-03-23T08:46:00Z"
    assert canonical_rollup["latest_status"] == "clean"
    assert canonical_report == report
    assert latest_manifest["cycle_dir"] == str(cycle_dir)
    assert latest_rollup["latest_status"] == "clean"
    assert latest_index["final_read"] == "stay_on_promoted_lane"
    assert latest_index["cycle_manifest_path"] == str(cycle_dir / "cycle_manifest.json")
    assert watch_job_dir.exists()
    assert "stay on promoted lane" in report
    assert latest_report == report


def test_cycle_main_returns_1_when_snapshot_turns_red(tmp_path: Path, monkeypatch: object) -> None:
    sample_iter = iter(
        [
            {
                "captured_at": "2026-03-23T08:45:00Z",
                "rollback_recommended": True,
                "rollback_reasons": ["health_not_ok"],
                "health": {"status": "down"},
                "smoke": {"ok": False, "latency_ms": 50000.0},
                "metrics_delta": {
                    "audit_events_delta": 0,
                    "upstream_usage_delta": 0,
                    "successful_chat_delta": 0,
                    "refusal_delta": 1,
                },
            }
        ]
    )
    monkeypatch.setattr(cycle, "capture_snapshot", lambda **kwargs: next(sample_iter))
    monkeypatch.setattr(cycle, "_utc_stamp", lambda: "20260323T091700Z")

    output_dir = tmp_path / "cycles"
    watch_root = tmp_path / "watch_jobs"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_pilot_monitoring_cycle.py",
            "--samples",
            "1",
            "--watch-root",
            str(watch_root),
            "--output-dir",
            str(output_dir),
            "--snapshot-path",
            str(tmp_path / "faz2c_narrow_pilot_snapshot.json"),
            "--canonical-rollup-path",
            str(tmp_path / "faz2c_watch_rollup.json"),
            "--canonical-status-report-path",
            str(tmp_path / "faz2c_pilot_status_report.md"),
        ],
    )

    result = cycle.main()

    assert result == 1
    cycle_dir = output_dir / "pilot_monitoring_cycle_20260323T091700Z"
    manifest = json.loads((cycle_dir / "cycle_manifest.json").read_text(encoding="utf-8"))
    latest_index = json.loads((output_dir / "latest_cycle_index.json").read_text(encoding="utf-8"))
    canonical_rollup = json.loads((tmp_path / "faz2c_watch_rollup.json").read_text(encoding="utf-8"))
    assert manifest["final_read"] == "review_or_rollback_candidate"
    assert latest_index["final_read"] == "review_or_rollback_candidate"
    assert canonical_rollup["rollback_job_count"] == 1
