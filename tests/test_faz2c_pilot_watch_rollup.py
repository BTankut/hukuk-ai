from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "faz2c"))

import build_pilot_watch_rollup as rollup  # noqa: E402


def test_build_rollup_empty() -> None:
    data = rollup.build_rollup([])

    assert data["job_count"] == 0
    assert data["latest_status"] is None
    assert data["recent_jobs"] == []


def test_build_rollup_with_jobs() -> None:
    summaries = [
        {
            "_summary_path": "a/summary.json",
            "_job_dir": "a",
            "final_status": "clean",
            "sample_count": 2,
            "avg_latency_ms": 9000.0,
        },
        {
            "_summary_path": "b/summary.json",
            "_job_dir": "b",
            "final_status": "rollback_recommended",
            "sample_count": 1,
            "avg_latency_ms": 31000.0,
        },
    ]

    data = rollup.build_rollup(summaries)

    assert data["job_count"] == 2
    assert data["clean_job_count"] == 1
    assert data["rollback_job_count"] == 1
    assert data["latest_status"] == "rollback_recommended"
    assert data["latest_summary_path"] == "b/summary.json"
    assert data["latest_job_dir"] == "b"
    assert data["max_latency_ms"] == 31000.0
    assert data["avg_latency_ms"] == 20000.0
    assert len(data["recent_jobs"]) == 2


def test_main_writes_rollup(tmp_path: Path, monkeypatch: object) -> None:
    watch_root = tmp_path / "jobs"
    job_dir = watch_root / "narrow_pilot_watch_20260323T091116Z"
    job_dir.mkdir(parents=True)
    (job_dir / "summary.json").write_text(
        json.dumps(
            {
                "final_status": "clean",
                "sample_count": 2,
                "avg_latency_ms": 9389.92,
            }
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "rollup.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_pilot_watch_rollup.py",
            "--watch-root",
            str(watch_root),
            "--output-path",
            str(output_path),
        ],
    )

    result = rollup.main()

    assert result == 0
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["job_count"] == 1
    assert data["latest_status"] == "clean"
    assert data["latest_job_dir"] == str(job_dir)
