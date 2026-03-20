# Training Readiness

This document defines the minimum gate that must pass before any new SFT or LoRA run is treated as valid.

The goal is simple: do not start or promote training unless the data, config, and evaluation evidence are all traceable.

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

Provide the evidence paths to the readiness script with `--baseline-evidence-path`.

The evidence should correspond to the same evaluation family that you plan to use for comparison after training.

### 7. Post-Train Evidence

Before any model is promoted, there must be at least one post-train evaluation artifact showing the new run was evaluated on the intended benchmark.

Provide the evidence paths to the readiness script with `--post-train-evidence-path`.

The post-train artifact must be distinct from the baseline artifact and must reference the trained checkpoint or output directory.

## Readiness CLI

Run the gate from the repo root.

Pre-training preflight:

```bash
python scripts/check_training_readiness.py \
  --mode preflight \
  --baseline-evidence-path evaluation/reports/<baseline_report>.json
```

Promotion check after training:

```bash
python scripts/check_training_readiness.py \
  --mode promotion \
  --baseline-evidence-path evaluation/reports/<baseline_report>.json \
  --post-train-evidence-path evaluation/reports/<post_train_report>.json
```

Optional workflow files can be checked for forbidden references with `--workflow-file`.

Examples:

```bash
python scripts/check_training_readiness.py \
  --mode preflight \
  --workflow-file scripts/build_training_dataset.py \
  --baseline-evidence-path evaluation/reports/eval_live_20260308_080601.json
```

## Pass Rule

The readiness gate passes only if all of the following are true:

- `final_train.jsonl` exists and validates as SFT JSONL.
- `held_out_test.jsonl` exists and does not overlap with the train set.
- The train set does not exceed the allowed duplicate question threshold.
- The forbidden v1 dataset path is absent from active workflow files.
- Baseline evidence is provided.
- In `promotion` mode, post-train evidence is provided.

If any hard gate fails, training is not ready.
