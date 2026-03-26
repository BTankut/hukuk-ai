from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_module(relative_path: str, module_name: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_capture_report_builds_from_faz16_control_reports():
    capture_module = _load_module("scripts/faz19/build_capture_report.py", "faz19_build_capture_report")
    lib = _load_module("scripts/faz19/faz19_lib.py", "faz19_lib")
    reports = [
        (
            REPO_ROOT / "evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-faz1-50-20260325.json",
            lib.load_json(REPO_ROOT / "evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-faz1-50-20260325.json"),
        ),
        (
            REPO_ROOT / "evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-v2-95-20260325.json",
            lib.load_json(REPO_ROOT / "evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-v2-95-20260325.json"),
        ),
        (
            REPO_ROOT / "evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-v3-170-20260325.json",
            lib.load_json(REPO_ROOT / "evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-v3-170-20260325.json"),
        ),
    ]
    payload = capture_module.build_capture_report("capture_a", reports)
    assert payload["family_count"] == 3
    assert len(payload["candidate_fingerprints"]) == 6
    assert payload["families"][0]["family_id"] == "faz1-50"
    assert any(row["candidate_kind"] == "rc_g" for row in payload["candidate_fingerprints"])


def test_phase_outputs_detect_snapshot_confirmation_for_identical_captures():
    capture_module = _load_module("scripts/faz19/build_capture_report.py", "faz19_build_capture_report_two")
    phase_module = _load_module("scripts/faz19/build_phase_package.py", "faz19_build_phase_package")
    lib = _load_module("scripts/faz19/faz19_lib.py", "faz19_lib_two")

    reports = [
        (
            REPO_ROOT / "evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-faz1-50-20260325.json",
            lib.load_json(REPO_ROOT / "evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-faz1-50-20260325.json"),
        ),
        (
            REPO_ROOT / "evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-v2-95-20260325.json",
            lib.load_json(REPO_ROOT / "evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-v2-95-20260325.json"),
        ),
        (
            REPO_ROOT / "evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-v3-170-20260325.json",
            lib.load_json(REPO_ROOT / "evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-v3-170-20260325.json"),
        ),
    ]
    capture_a = capture_module.build_capture_report("capture_a", reports)
    capture_b = capture_module.build_capture_report("capture_b", reports)
    historical = phase_module._reference_payload(
        "historical_authority",
        [
            REPO_ROOT / "evaluation/reports/faz13-rc-j-output-parity-authoritative-faz1-50-2026-03-25.json",
            REPO_ROOT / "evaluation/reports/faz13-rc-j-output-parity-authoritative-v2-95-2026-03-25.json",
            REPO_ROOT / "evaluation/reports/faz13-rc-j-output-parity-authoritative-v3-170-2026-03-25.json",
        ],
    )
    snapshot = phase_module._reference_payload(
        "current_instability_snapshot",
        [
            REPO_ROOT / "evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-faz1-50-20260325.json",
            REPO_ROOT / "evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-v2-95-20260325.json",
            REPO_ROOT / "evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-v3-170-20260325.json",
        ],
    )
    outputs = phase_module.build_phase_outputs(
        capture_a_payload=capture_a,
        capture_b_payload=capture_b,
        historical_payload=historical,
        snapshot_payload=snapshot,
    )
    summary = outputs["current_summary"]
    reconciliation = outputs["reconciliation"]
    assert summary["capture_stability_match"] is True
    assert summary["historical_authority_restored"] is False
    assert summary["current_instability_snapshot_confirmed"] is True
    assert reconciliation["official_decision"] == "PASS - Stable Current Authority Re-Captured"
