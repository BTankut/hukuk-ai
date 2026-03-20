from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_training_readiness as readiness  # noqa: E402


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def test_question_duplicate_check_fails_on_excess_duplicates(tmp_path: Path) -> None:
    train_file = tmp_path / "train.jsonl"
    _write_jsonl(
        train_file,
        [
            {"instruction": "i", "input": "SORU: Aynı soru?", "output": "cevap 1"},
            {"instruction": "i", "input": "SORU: Aynı soru?", "output": "cevap 2"},
            {"instruction": "i", "input": "SORU: Farklı soru?", "output": "cevap 3"},
        ],
    )

    result = readiness._check_question_duplicates(train_file, max_duplicate_excess=0)

    assert result.ok is False
    assert result.name == "Question duplicate check"
    assert "1 duplicate question groups" in result.detail
    assert "1 excess rows" in result.detail


def test_question_duplicate_check_passes_when_threshold_allows(tmp_path: Path) -> None:
    train_file = tmp_path / "train.jsonl"
    _write_jsonl(
        train_file,
        [
            {"instruction": "i", "input": "SORU: Aynı soru?", "output": "cevap 1"},
            {"instruction": "i", "input": "SORU: Aynı soru?", "output": "cevap 2"},
        ],
    )

    result = readiness._check_question_duplicates(train_file, max_duplicate_excess=1)

    assert result.ok is True
    assert "threshold=1" in result.detail


def test_parse_evidence_manifest_validates_report_sha(tmp_path: Path) -> None:
    report_path = tmp_path / "baseline_report.json"
    report_path.write_text(
        json.dumps({"report_meta": {"questions_source": "configs/evaluation/test_questions.json"}}),
        encoding="utf-8",
    )
    manifest_path = tmp_path / "baseline_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "manifest_version": 1,
                "role": "baseline",
                "eval_family": "faz1-50",
                "model_ref": "base:qwen35",
                "checkpoint_ref": "base-runtime",
                "git_commit": "abc1234",
                "report_path": str(report_path),
                "report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
            }
        ),
        encoding="utf-8",
    )

    manifest, error = readiness._parse_evidence_manifest(manifest_path)

    assert error is None
    assert manifest is not None
    assert manifest.eval_family == "faz1-50"
    assert manifest.report_path == report_path


def test_check_evidence_manifests_rejects_raw_report_path(tmp_path: Path) -> None:
    raw_report = tmp_path / "raw_report.json"
    raw_report.write_text(json.dumps({"report_meta": {"generated_at": "2026-03-21T00:00:00+00:00"}}), encoding="utf-8")

    item, manifests = readiness._check_evidence_manifests(
        [raw_report],
        label="Baseline evidence manifest",
        allowed_roles={"baseline"},
    )

    assert item.ok is False
    assert manifests == []
    assert "missing required fields" in item.detail


def test_promotion_evidence_contract_requires_distinct_checkpoint_refs(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps({"report_meta": {}}), encoding="utf-8")
    report_sha = hashlib.sha256(report_path.read_bytes()).hexdigest()
    baseline_manifest = readiness.EvidenceManifest(
        path=tmp_path / "baseline.json",
        role="baseline",
        eval_family="faz1-50",
        model_ref="base:qwen35",
        checkpoint_ref="shared-ref",
        git_commit="base123",
        report_path=report_path,
        report_sha256=report_sha,
    )
    post_train_manifest = readiness.EvidenceManifest(
        path=tmp_path / "post.json",
        role="post_train",
        eval_family="faz1-50",
        model_ref="lora:qwen35",
        checkpoint_ref="shared-ref",
        git_commit="post123",
        report_path=report_path,
        report_sha256=report_sha,
    )

    item = readiness._check_promotion_evidence_contract(
        [baseline_manifest],
        [post_train_manifest],
        expected_eval_family="faz1-50",
    )

    assert item.ok is False
    assert "identical" in item.detail
