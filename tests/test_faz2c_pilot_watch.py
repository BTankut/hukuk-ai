from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "faz2c"))

import run_narrow_pilot_watch as watch  # noqa: E402


def test_build_summary_with_clean_samples() -> None:
    samples = [
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
            "smoke": {"latency_ms": 2000.0},
        },
    ]

    summary = watch.build_summary(samples)

    assert summary["sample_count"] == 2
    assert summary["clean_sample_count"] == 2
    assert summary["rollback_sample_count"] == 0
    assert summary["final_status"] == "clean"
    assert summary["first_rollback_sample"] is None
    assert summary["max_latency_ms"] == 2000.0
    assert summary["avg_latency_ms"] == 1500.0


def test_build_summary_with_rollback_samples() -> None:
    samples = [
        {
            "captured_at": "2026-03-23T08:45:00Z",
            "rollback_recommended": False,
            "rollback_reasons": [],
            "smoke": {"latency_ms": 1000.0},
        },
        {
            "captured_at": "2026-03-23T08:46:00Z",
            "rollback_recommended": True,
            "rollback_reasons": ["health_not_ok", "latency_budget_exceeded"],
            "smoke": {"latency_ms": 32000.0},
        },
        {
            "captured_at": "2026-03-23T08:47:00Z",
            "rollback_recommended": True,
            "rollback_reasons": ["latency_budget_exceeded"],
            "smoke": {"latency_ms": 33000.0},
        },
    ]

    summary = watch.build_summary(samples)

    assert summary["rollback_sample_count"] == 2
    assert summary["first_rollback_sample"] == 2
    assert summary["final_status"] == "rollback_recommended"
    assert summary["rollback_reason_counts"] == {
        "health_not_ok": 1,
        "latency_budget_exceeded": 2,
    }


def test_main_writes_watch_outputs(tmp_path: Path, monkeypatch: object) -> None:
    samples_iter = iter(
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
                "smoke": {"latency_ms": 1200.0},
            },
        ]
    )
    monkeypatch.setattr(watch, "capture_snapshot", lambda **kwargs: next(samples_iter))
    monkeypatch.setattr(watch.time, "sleep", lambda *_args, **_kwargs: None)

    jsonl_path = tmp_path / "watch.jsonl"
    summary_path = tmp_path / "summary.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_narrow_pilot_watch.py",
            "--samples",
            "2",
            "--sleep-seconds",
            "0",
            "--jsonl-path",
            str(jsonl_path),
            "--summary-path",
            str(summary_path),
        ],
    )

    result = watch.main()

    assert result == 0
    rows = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines()]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert len(rows) == 2
    assert rows[0]["_watch_index"] == 1
    assert rows[1]["_watch_index"] == 2
    assert summary["sample_count"] == 2
    assert summary["rollback_sample_count"] == 0


def test_main_stops_early_on_rollback(tmp_path: Path, monkeypatch: object) -> None:
    samples_iter = iter(
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
                "smoke": {"latency_ms": 1200.0},
            },
        ]
    )
    monkeypatch.setattr(watch, "capture_snapshot", lambda **kwargs: next(samples_iter))
    monkeypatch.setattr(watch.time, "sleep", lambda *_args, **_kwargs: None)

    jsonl_path = tmp_path / "watch.jsonl"
    summary_path = tmp_path / "summary.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_narrow_pilot_watch.py",
            "--samples",
            "3",
            "--sleep-seconds",
            "0",
            "--stop-on-rollback",
            "--jsonl-path",
            str(jsonl_path),
            "--summary-path",
            str(summary_path),
        ],
    )

    result = watch.main()

    assert result == 1
    rows = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines()]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert len(rows) == 1
    assert summary["rollback_sample_count"] == 1
