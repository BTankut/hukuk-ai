from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_eval_evidence_manifest as evidence_builder  # noqa: E402


def test_builder_reuses_identity_fields_from_report_meta(tmp_path: Path, monkeypatch) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "report_meta": {
                    "eval_family": "faz1-50",
                    "model_ref": "gateway-live:qwen35",
                    "checkpoint_ref": "runtime-20260321",
                    "git_commit": "abc1234",
                }
            }
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "manifest.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_eval_evidence_manifest.py",
            "--report-path",
            str(report_path),
            "--role",
            "baseline",
            "--output",
            str(output_path),
        ],
    )

    result = evidence_builder.main()

    assert result == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["role"] == "baseline"
    assert payload["eval_family"] == "faz1-50"
    assert payload["model_ref"] == "gateway-live:qwen35"
    assert payload["checkpoint_ref"] == "runtime-20260321"
    assert payload["git_commit"] == "abc1234"
