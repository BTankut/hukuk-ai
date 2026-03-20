# Training Readiness

This document defines the minimum gate that must pass before any new SFT or LoRA run is treated as valid.

The goal is simple: do not start or promote training unless the data, config, and evaluation evidence are all traceable.

## Execution Package

Before any new training run is treated as valid, freeze the active pre-train package.

The official active build chain is:

- `python3 scripts/build_training_dataset.py --dry-run`
- `python3 scripts/build_training_dataset.py`
- `python3 scripts/check_training_readiness.py --mode preflight --baseline-evidence-path evaluation/reports/<baseline_report>.json`

The builder now applies the official duplicate canonicalization package by default, so the active `final_train.jsonl` is reproducible from source reconciled masters plus the frozen canonicalization manifest.

Reference package:

- `coordination/pretrain-execution-package-2026-03-21.md`
- `coordination/promotion-evidence-contract-2026-03-21.md`
- `coordination/finetune-execution-chain-restoration-2026-03-21.md`

The fine-tune bootstrap / preflight entrypoints are:

- `bash scripts/finetune/bootstrap_dgxnode2_unsloth.sh ~/.venvs/hukuk-ai-ft`
- `bash scripts/finetune/validate_dgxnode2_env.sh ~/.venvs/hukuk-ai-ft`
- `python3 scripts/finetune/check_finetune_config.py --config configs/finetune/unsloth_sft_qwen35_35b_a3b.json`

## Hard Gates

### 1. Provenance

The active training dataset must be the lawyer-reviewed final set:

- `data/finetune/sft/final_train.jsonl`

The dataset must be traceable to reconciled lawyer review outputs. Pending-review material may exist in the repo, but it must not be consumed directly by the active training workflow.

The old invalid v1 dataset is forbidden in the active workflow:

- `data/finetune/sft_training_v1.jsonl`

If any active script, config, or runbook still points to that path, the run fails the gate.

### 2. Held-Out Leakage

The held-out evaluation set must exist and must not overlap with training questions:

- `data/finetune/eval/held_out_test.jsonl`

The readiness check compares held-out questions with training questions and fails if an exact overlap is found.

### 3. Approved vs Pending Data

The final training set must contain approved or lawyer-corrected records only.

Pending-review files are allowed only as intermediate review inputs. They are not valid training inputs unless they have been reconciled and written into the final train set.

### 4. Question Duplicate Gate

The final training set must not contain duplicate question rows beyond the allowed threshold.

The readiness check scans extracted question text inside `final_train.jsonl` and fails if duplicate excess rows exceed the configured limit.

Default rule:

- `--max-question-duplicate-excess 0`

This keeps training blocked until repeated questions are either merged, removed, or explicitly waived.

### 5. Config Validation

All JSONL inputs used by the training pipeline must pass schema validation with:

- `python scripts/validate_ft_data.py --file <path> --type sft`
- `python scripts/validate_ft_data.py --file <path> --type dpo`

The readiness script also checks active workflow files for forbidden references to the invalid v1 dataset path.

### 6. Baseline Evidence

Before training starts, there must be at least one frozen baseline evaluation artifact for the model state you are comparing against.

Provide the evidence manifest paths to the readiness script with `--baseline-evidence-path`.

The evidence should correspond to the same evaluation family that you plan to use for comparison after training.

If the raw report already embeds `eval_family`, `model_ref`, `checkpoint_ref`, and `git_commit` inside `report_meta`, `scripts/build_eval_evidence_manifest.py` can reuse them automatically.

### 7. Post-Train Evidence

Before any model is promoted, there must be at least one post-train evaluation artifact showing the new run was evaluated on the intended benchmark.

Provide the evidence manifest paths to the readiness script with `--post-train-evidence-path`.

The post-train manifest must be distinct from the baseline manifest and must reference the trained checkpoint or output directory.

## Readiness CLI

Run the gate from the repo root.

Pre-training preflight:

```bash
python scripts/build_eval_evidence_manifest.py \
  --report-path evaluation/reports/eval_live_20260308_080601.json \
  --role baseline \
  --eval-family faz1-50 \
  --model-ref Qwen/Qwen3.5-35B-A3B-FP8 \
  --checkpoint-ref base-acceptance-runtime-20260308 \
  --git-commit 420cd08 \
  --output evaluation/reports/evidence_baseline_faz1_50_20260308.json

python scripts/check_training_readiness.py \
  --mode preflight \
  --expected-eval-family faz1-50 \
  --max-question-duplicate-excess 0 \
  --baseline-evidence-path evaluation/reports/evidence_baseline_faz1_50_20260308.json
```

Promotion check after training:

```bash
python3 scripts/finetune/plan_posttrain_eval.py \
  --config configs/finetune/unsloth_sft_qwen35_35b_a3b.json \
  --checkpoint-ref <trained_checkpoint_ref> \
  --api-url <candidate_runtime_url> \
  --model <candidate_runtime_model> \
  --git-commit <git_commit>

python scripts/check_training_readiness.py \
  --mode promotion \
  --expected-eval-family faz1-50 \
  --max-question-duplicate-excess 0 \
  --baseline-evidence-path evaluation/reports/<baseline_manifest>.json \
  --post-train-evidence-path evaluation/reports/<post_train_manifest>.json
```

Optional workflow files can be checked for forbidden references with `--workflow-file`.

Examples:

```bash
python scripts/check_training_readiness.py \
  --mode preflight \
  --workflow-file scripts/build_training_dataset.py \
  --expected-eval-family faz1-50 \
  --max-question-duplicate-excess 0 \
  --baseline-evidence-path evaluation/reports/evidence_baseline_faz1_50_20260308.json
```

## Pass Rule

The readiness gate passes only if all of the following are true:

- `final_train.jsonl` exists and validates as SFT JSONL.
- `held_out_test.jsonl` exists and does not overlap with the train set.
- The train set does not exceed the allowed duplicate question threshold.
- The active train file comes from the frozen execution package / official builder path.
- Baseline and post-train evidence are manifest-backed and SHA-verified.
- Baseline and post-train evidence must come from the same eval runner family.
- The forbidden v1 dataset path is absent from active workflow files.
- Baseline evidence is provided.
- In `promotion` mode, post-train evidence is provided.

If any hard gate fails, training is not ready.
