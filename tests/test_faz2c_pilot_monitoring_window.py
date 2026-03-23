from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "faz2c"))

import run_pilot_monitoring_window as window  # noqa: E402


def _write_cycle_manifest(path: Path, *, cycle_dir: str, final_read: str, latest_rollup_status: str, rollback: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "cycle_dir": cycle_dir,
                "watch_job_dir": f"{cycle_dir}/watch",
                "final_read": final_read,
                "latest_rollup_status": latest_rollup_status,
                "latest_snapshot_rollback_recommended": rollback,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_window_main_writes_clean_bundle(tmp_path: Path, monkeypatch: object) -> None:
    output_dir = tmp_path / "window_jobs"
    cycle_paths = [
        tmp_path / "cycles" / "cycle1.json",
        tmp_path / "cycles" / "cycle2.json",
    ]
    _write_cycle_manifest(
        cycle_paths[0],
        cycle_dir="runtime_logs/faz2c_cycles/pilot_monitoring_cycle_20260323T100000Z",
        final_read="stay_on_promoted_lane",
        latest_rollup_status="clean",
        rollback=False,
    )
    _write_cycle_manifest(
        cycle_paths[1],
        cycle_dir="runtime_logs/faz2c_cycles/pilot_monitoring_cycle_20260323T100500Z",
        final_read="stay_on_promoted_lane",
        latest_rollup_status="clean",
        rollback=False,
    )
    calls = iter([(0, cycle_paths[0]), (0, cycle_paths[1])])
    monkeypatch.setattr(window, "invoke_cycle", lambda args: next(calls))
    monkeypatch.setattr(window, "_utc_stamp", lambda: "20260323T101000Z")
    monkeypatch.setattr(window.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_pilot_monitoring_window.py",
            "--cycles",
            "2",
            "--sleep-seconds",
            "0",
            "--window-output-dir",
            str(output_dir),
        ],
    )

    result = window.main()

    assert result == 0
    window_dir = output_dir / "pilot_monitoring_window_20260323T101000Z"
    summary = json.loads((window_dir / "window_summary.json").read_text(encoding="utf-8"))
    manifest = json.loads((window_dir / "window_manifest.json").read_text(encoding="utf-8"))
    latest_summary = json.loads((output_dir / "latest_window_summary.json").read_text(encoding="utf-8"))
    latest_manifest = json.loads((output_dir / "latest_window_manifest.json").read_text(encoding="utf-8"))
    latest_report = (output_dir / "latest_window_report.md").read_text(encoding="utf-8")

    assert summary["final_status"] == "clean"
    assert summary["cycle_count_recorded"] == 2
    assert summary["latest_cycle_dir"] == "runtime_logs/faz2c_cycles/pilot_monitoring_cycle_20260323T100500Z"
    assert manifest["latest_final_read"] == "stay_on_promoted_lane"
    assert latest_summary["clean_cycle_count"] == 2
    assert latest_manifest["cycle_count_recorded"] == 2
    assert "stay on promoted lane" in latest_report


def test_window_main_stops_on_red(tmp_path: Path, monkeypatch: object) -> None:
    output_dir = tmp_path / "window_jobs"
    cycle_path = tmp_path / "cycles" / "cycle1.json"
    _write_cycle_manifest(
        cycle_path,
        cycle_dir="runtime_logs/faz2c_cycles/pilot_monitoring_cycle_20260323T100000Z",
        final_read="review_or_rollback_candidate",
        latest_rollup_status="red",
        rollback=True,
    )
    call_count = {"value": 0}

    def _invoke(args: object) -> tuple[int, Path]:
        call_count["value"] += 1
        return 1, cycle_path

    monkeypatch.setattr(window, "invoke_cycle", _invoke)
    monkeypatch.setattr(window, "_utc_stamp", lambda: "20260323T101500Z")
    monkeypatch.setattr(window.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_pilot_monitoring_window.py",
            "--cycles",
            "3",
            "--sleep-seconds",
            "0",
            "--stop-on-red",
            "--window-output-dir",
            str(output_dir),
        ],
    )

    result = window.main()

    assert result == 1
    assert call_count["value"] == 1
    window_dir = output_dir / "pilot_monitoring_window_20260323T101500Z"
    summary = json.loads((window_dir / "window_summary.json").read_text(encoding="utf-8"))
    latest_manifest = json.loads((output_dir / "latest_window_manifest.json").read_text(encoding="utf-8"))

    assert summary["final_status"] == "review_or_rollback_candidate"
    assert summary["cycle_count_recorded"] == 1
    assert latest_manifest["latest_final_read"] == "review_or_rollback_candidate"
