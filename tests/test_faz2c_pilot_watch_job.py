from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "faz2c"))

import run_narrow_pilot_watch_job as watch_job  # noqa: E402


def test_main_writes_timestamped_job_bundle(tmp_path: Path, monkeypatch: object) -> None:
    sample_iter = iter(
        [
            {
                "captured_at": "2026-03-23T08:45:00Z",
                "rollback_recommended": False,
                "rollback_reasons": [],
                "smoke": {"latency_ms": 1000.0},
            },
            {
                "captured_at": "2026-03-23T08:46:00Z",
                "rollback_recommended": False,
                "rollback_reasons": [],
                "smoke": {"latency_ms": 1100.0},
            },
        ]
    )
    monkeypatch.setattr(watch_job, "capture_snapshot", lambda **kwargs: next(sample_iter))
    monkeypatch.setattr(watch_job, "_utc_stamp", lambda: "20260323T090000Z")

    output_dir = tmp_path / "jobs"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_narrow_pilot_watch_job.py",
            "--samples",
            "2",
            "--sleep-seconds",
            "0",
            "--label",
            "pilot",
            "--output-dir",
            str(output_dir),
        ],
    )

    result = watch_job.main()

    assert result == 0
    job_dir = output_dir / "pilot_20260323T090000Z"
    manifest = json.loads((job_dir / "manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((job_dir / "summary.json").read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in (job_dir / "watch.jsonl").read_text(encoding="utf-8").splitlines()
    ]

    assert manifest["final_status"] == "clean"
    assert manifest["sample_count_recorded"] == 2
    assert summary["sample_count"] == 2
    assert len(rows) == 2
    assert rows[0]["_watch_index"] == 1
    assert rows[1]["_watch_index"] == 2


def test_main_stops_early_when_requested(tmp_path: Path, monkeypatch: object) -> None:
    sample_iter = iter(
        [
            {
                "captured_at": "2026-03-23T08:45:00Z",
                "rollback_recommended": True,
                "rollback_reasons": ["health_not_ok"],
                "smoke": {"latency_ms": 1000.0},
            },
            {
                "captured_at": "2026-03-23T08:46:00Z",
                "rollback_recommended": False,
                "rollback_reasons": [],
                "smoke": {"latency_ms": 1100.0},
            },
        ]
    )
    monkeypatch.setattr(watch_job, "capture_snapshot", lambda **kwargs: next(sample_iter))
    monkeypatch.setattr(watch_job, "_utc_stamp", lambda: "20260323T090500Z")

    output_dir = tmp_path / "jobs"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_narrow_pilot_watch_job.py",
            "--samples",
            "3",
            "--sleep-seconds",
            "0",
            "--stop-on-rollback",
            "--output-dir",
            str(output_dir),
        ],
    )

    result = watch_job.main()

    assert result == 1
    job_dir = output_dir / "narrow_pilot_watch_20260323T090500Z"
    manifest = json.loads((job_dir / "manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((job_dir / "summary.json").read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in (job_dir / "watch.jsonl").read_text(encoding="utf-8").splitlines()
    ]

    assert manifest["sample_count_recorded"] == 1
    assert summary["rollback_sample_count"] == 1
    assert len(rows) == 1
