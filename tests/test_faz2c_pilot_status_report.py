from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "faz2c"))

import build_pilot_status_report as report_builder  # noqa: E402


def test_build_report_clean_state() -> None:
    snapshot = {
        "captured_at": "2026-03-23T08:45:52Z",
        "rollback_recommended": False,
        "health": {"status": "ok"},
        "smoke": {"ok": True, "latency_ms": 10357.38},
        "metrics_delta": {
            "audit_events_delta": 1,
            "upstream_usage_delta": 1,
            "successful_chat_delta": 1,
            "refusal_delta": 0,
        },
        "rollback_reasons": [],
    }
    rollup = {
        "latest_status": "clean",
        "job_count": 1,
        "clean_job_count": 1,
        "rollback_job_count": 0,
        "latest_job_dir": "runtime_logs/faz2c_watch_jobs/x",
        "avg_latency_ms": 9389.92,
        "max_latency_ms": 9389.92,
    }
    latest_job_summary = {
        "final_status": "clean",
        "sample_count": 2,
        "clean_sample_count": 2,
        "rollback_sample_count": 0,
        "avg_latency_ms": 9389.92,
        "max_latency_ms": 9472.84,
    }

    report = report_builder.build_report(
        snapshot=snapshot,
        rollup=rollup,
        latest_job_summary=latest_job_summary,
    )

    assert "stay on promoted lane" in report
    assert "`clean`" in report
    assert "`False`" in report


def test_main_writes_markdown_report(tmp_path: Path, monkeypatch: object) -> None:
    snapshot_path = tmp_path / "snapshot.json"
    rollup_path = tmp_path / "rollup.json"
    latest_summary_path = tmp_path / "latest_summary.json"
    output_path = tmp_path / "report.md"

    snapshot_path.write_text(
        json.dumps(
            {
                "captured_at": "2026-03-23T08:45:52Z",
                "rollback_recommended": False,
                "health": {"status": "ok"},
                "smoke": {"ok": True, "latency_ms": 10357.38},
                "metrics_delta": {},
                "rollback_reasons": [],
            }
        ),
        encoding="utf-8",
    )
    latest_summary_path.write_text(
        json.dumps(
            {
                "final_status": "clean",
                "sample_count": 2,
                "clean_sample_count": 2,
                "rollback_sample_count": 0,
                "avg_latency_ms": 9389.92,
                "max_latency_ms": 9472.84,
            }
        ),
        encoding="utf-8",
    )
    rollup_path.write_text(
        json.dumps(
            {
                "latest_status": "clean",
                "job_count": 1,
                "clean_job_count": 1,
                "rollback_job_count": 0,
                "latest_job_dir": "runtime_logs/faz2c_watch_jobs/x",
                "latest_summary_path": str(latest_summary_path),
                "avg_latency_ms": 9389.92,
                "max_latency_ms": 9389.92,
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_pilot_status_report.py",
            "--snapshot-path",
            str(snapshot_path),
            "--rollup-path",
            str(rollup_path),
            "--output-path",
            str(output_path),
        ],
    )

    result = report_builder.main()

    assert result == 0
    text = output_path.read_text(encoding="utf-8")
    assert "FAZ 2C Pilot Status Report" in text
    assert "stay on promoted lane" in text
