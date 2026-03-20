from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "finetune"))

import plan_posttrain_eval as planner


def test_build_plan_embeds_eval_manifest_and_promotion_chain(tmp_path: Path) -> None:
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
    baseline_manifest.write_text(json.dumps({"role": "baseline", "eval_family": "faz1-50"}) + "\n", encoding="utf-8")

    config_path = tmp_path / "configs/finetune/config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "data": {
                    "train_file": "data/finetune/sft/final_train.jsonl",
                    "held_out_file": "data/finetune/eval/held_out_test.jsonl",
                    "expected_train_sha256": "unused",
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
        api_url="http://127.0.0.1:8080",
        model="hukuk-ai-sft-v3",
        model_ref=None,
        git_commit="abc1234",
        report_path=None,
        manifest_path=None,
        stamp="20260321",
    )

    assert plan.eval_family == "faz1-50"
    assert "evaluation/eval_vllm_direct.py" in plan.eval_command
    assert "--checkpoint-ref" in plan.eval_command
    assert "hukuk-ai-sft-v3" in plan.eval_command
    assert "--post-train-evidence-path" in plan.promotion_command
    assert plan.report_path.name.startswith("eval_post_train_faz1-50_hukuk_ai_sft_v3_20260321")
    assert plan.manifest_path.name.startswith("evidence_post_train_faz1-50_hukuk_ai_sft_v3_20260321")
