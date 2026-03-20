from __future__ import annotations

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
