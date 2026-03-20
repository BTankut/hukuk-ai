from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "finetune"))

import plan_posttrain_diagnostic_eval as planner  # noqa: E402


def test_build_plan_marks_diagnostic_only(tmp_path: Path) -> None:
    train_file = tmp_path / "data/finetune/sft/final_train.jsonl"
    train_file.parent.mkdir(parents=True)
    train_file.write_text(
        json.dumps({"instruction": "i", "input": "q", "output": "a"}) + "\n",
        encoding="utf-8",
    )

    heldout_file = tmp_path / "data/finetune/eval/held_out_test.jsonl"
    heldout_file.parent.mkdir(parents=True)
    heldout_file.write_text(json.dumps({"question": "heldout"}) + "\n", encoding="utf-8")

    questions_path = tmp_path / "configs/evaluation/test_questions.json"
    questions_path.parent.mkdir(parents=True)
    questions_path.write_text("[]\n", encoding="utf-8")

    baseline_manifest = tmp_path / "evaluation/reports/base.json"
    baseline_manifest.parent.mkdir(parents=True)
    baseline_manifest.write_text(
        json.dumps(
            {
                "manifest_version": 1,
                "role": "baseline",
                "eval_family": "faz1-50",
                "model_ref": "gateway-live:qwen35",
                "checkpoint_ref": "base-runtime",
                "git_commit": "abc1234",
                "runner": "eval_runner",
                "report_path": "evaluation/reports/base_raw.json",
                "report_sha256": "dummy",
            }
        ),
        encoding="utf-8",
    )

    config_path = tmp_path / "configs/finetune/config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "data": {
                    "train_file": "data/finetune/sft/final_train.jsonl",
                    "held_out_file": "data/finetune/eval/held_out_test.jsonl",
                    "expected_train_sha256": "",
                    "expected_heldout_rows": 1,
                    "min_clean_examples": 1,
                    "placeholder_markers": ["TODO"],
                },
                "output": {"dir": "artifacts/finetune/demo"},
                "evaluation": {
                    "eval_family": "faz1-50",
                    "questions_path": "configs/evaluation/test_questions.json",
                    "baseline_manifest": "evaluation/reports/base.json",
                    "report_dir": "evaluation/reports",
                    "max_question_duplicate_excess": 0,
                    "max_tokens": 3000,
                    "delay_seconds": 1.0,
                    "timeout_seconds": 300.0,
                    "workflow_files": ["scripts/build_training_dataset.py"],
                },
            }
        ),
        encoding="utf-8",
    )

    plan = planner.build_plan(
        config_path=config_path,
        checkpoint_ref="hukuk-ai-sft-v3",
        model_path="/models/hukuk-ai-sft-v3",
        model="hukuk-ai-sft-v3",
        model_ref=None,
        git_commit="abc1234",
        report_path=None,
        manifest_path=None,
        stamp="20260321",
        max_new_tokens=512,
        limit=10,
        category=None,
    )

    assert plan.promotion_compatible is False
    assert "evaluation/eval_transformers_direct.py" in plan.eval_command
    assert "diagnostic_post_train" in plan.eval_command
    assert "--limit" in plan.eval_command
