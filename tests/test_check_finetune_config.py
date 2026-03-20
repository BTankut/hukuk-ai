from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "finetune"))

import check_finetune_config as finetune


def test_count_clean_examples_flags_placeholders(tmp_path: Path) -> None:
    data_file = tmp_path / "train.jsonl"
    rows = [
        {"instruction": "i", "input": "x", "output": "good"},
        {"instruction": "i", "input": "TODO", "output": "bad"},
    ]
    data_file.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    total, clean, bad = finetune.count_clean_examples(data_file, ["TODO"])

    assert total == 2
    assert clean == 1
    assert bad == 1


def test_build_readiness_command_includes_gate_inputs(tmp_path: Path) -> None:
    config_path = tmp_path / "configs/finetune/active.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "data": {
                    "train_file": "data/finetune/sft/final_train.jsonl",
                    "held_out_file": "data/finetune/eval/held_out_test.jsonl",
                    "min_clean_examples": 2,
                    "placeholder_markers": ["TODO"],
                    "expected_train_sha256": "sha",
                    "expected_heldout_rows": 1,
                },
                "output": {
                    "dir": "artifacts/finetune/demo"
                },
                "evaluation": {
                    "eval_family": "faz1-50",
                    "questions_path": "configs/evaluation/test_questions.json",
                    "baseline_manifest": "evaluation/reports/base.json",
                    "report_dir": "evaluation/reports",
                    "max_question_duplicate_excess": 0,
                    "workflow_files": [
                        "scripts/build_training_dataset.py",
                        "configs/finetune/active.json"
                    ]
                },
            }
        ),
        encoding="utf-8",
    )

    command = finetune.build_readiness_command(config_path)

    assert command[0].endswith("python") or command[0].endswith("python3") or "python" in command[0]
    assert "--mode" in command
    assert "--expected-eval-family" in command
    assert str(tmp_path / "evaluation/reports/base.json") in command
    assert str(tmp_path / "scripts/build_training_dataset.py") in command
    assert str(tmp_path / "configs/finetune/active.json") in command


def test_main_passes_when_package_and_readiness_match(tmp_path: Path, monkeypatch, capsys) -> None:
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "check_training_readiness.py").write_text("print('stub')\n", encoding="utf-8")

    train_file = tmp_path / "data/finetune/sft/final_train.jsonl"
    train_file.parent.mkdir(parents=True)
    train_rows = [
        {"instruction": "i", "input": "q1", "output": "a1"},
        {"instruction": "i", "input": "q2", "output": "a2"},
    ]
    train_file.write_text("\n".join(json.dumps(row) for row in train_rows) + "\n", encoding="utf-8")

    heldout_file = tmp_path / "data/finetune/eval/held_out_test.jsonl"
    heldout_file.parent.mkdir(parents=True)
    heldout_rows = [{"question": "heldout-1"}]
    heldout_file.write_text("\n".join(json.dumps(row) for row in heldout_rows) + "\n", encoding="utf-8")

    baseline_manifest = tmp_path / "evaluation/reports/base.json"
    baseline_manifest.parent.mkdir(parents=True)
    baseline_manifest.write_text(
        json.dumps({"role": "baseline", "eval_family": "faz1-50"}) + "\n",
        encoding="utf-8",
    )

    config_path = tmp_path / "configs/finetune/config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "model": {"name": "Qwen/Qwen3.5-35B-A3B"},
                "data": {
                    "train_file": "data/finetune/sft/final_train.jsonl",
                    "held_out_file": "data/finetune/eval/held_out_test.jsonl",
                    "min_clean_examples": 2,
                    "placeholder_markers": ["TODO"],
                    "expected_train_sha256": finetune.file_sha256(train_file),
                    "expected_heldout_rows": 1
                },
                "output": {"dir": "artifacts/finetune/demo"},
                "evaluation": {
                    "eval_family": "faz1-50",
                    "questions_path": "configs/evaluation/test_questions.json",
                    "baseline_manifest": "evaluation/reports/base.json",
                    "report_dir": "evaluation/reports",
                    "max_tokens": 3000,
                    "max_question_duplicate_excess": 0,
                    "workflow_files": ["scripts/build_training_dataset.py"]
                },
            }
        ),
        encoding="utf-8",
    )

    def fake_run(command: list[str], cwd: Path, check: bool) -> object:
        assert command[1] == str(tmp_path / "scripts/check_training_readiness.py")
        assert cwd == tmp_path
        assert check is False
        return type("Result", (), {"returncode": 0})()

    monkeypatch.setattr(finetune.subprocess, "run", fake_run)
    monkeypatch.setattr("sys.argv", ["check_finetune_config.py", "--config", str(config_path)])

    questions_path = tmp_path / "configs/evaluation/test_questions.json"
    questions_path.parent.mkdir(parents=True)
    questions_path.write_text("[]\n", encoding="utf-8")

    exit_code = finetune.main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "READY_FOR_TRAINING_GATE" in captured.out
