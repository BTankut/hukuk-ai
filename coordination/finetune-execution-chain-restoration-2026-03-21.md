# Fine-Tune Execution Chain Restoration

Date: 2026-03-21
Scope: restore missing training/bootstrap assets and align them with the frozen canonical package
Decision: historical finetune bootstrap/config files are restored as first-class repo assets, but only after being rewired to the current 807-row package and evidence contract

## Problem

The repo had reached a state where:

- training readiness and evidence gates were hardened
- raw eval identity metadata was embedded into reports
- but the historical fine-tune bootstrap/config chain referenced in earlier reports was absent from the current worktree

Concretely, the following files were referenced by historical reports but missing from `main`:

- `configs/finetune/unsloth_sft_qwen35_35b_a3b.json`
- `configs/training/sft_config.yaml`
- `configs/training/sft_llamafactory.yaml`
- `scripts/finetune/bootstrap_dgxnode2_unsloth.sh`
- `scripts/finetune/validate_dgxnode2_env.sh`
- `scripts/finetune/check_finetune_config.py`
- `scripts/finetune/handoff_config.py`
- `scripts/finetune/plan_posttrain_eval.py`
- `docs/finetune/dgxnode2-lora-bootstrap.md`

That meant the promotion contract existed, but the official training entry path was still fragmented.

## Restored Assets

The missing chain is now restored and aligned to the current repo truth:

- active train package: `data/finetune/sft/final_train.jsonl`
  - rows: `807`
  - sha256: `1139008106af2bc655246b878d2dbc78bc6bad6a2e732fdb0caabd2f2fece3b0`
- active held-out package: `data/finetune/eval/held_out_test.jsonl`
  - rows: `22`
- baseline evidence manifest:
  - `evaluation/reports/evidence_baseline_faz1_50_20260308.json`
- expected eval family:
  - `faz1-50`

## What Changed

### 1) Official finetune config package restored

- `configs/finetune/unsloth_sft_qwen35_35b_a3b.json`
  - now points to the frozen 807-row train package
  - records expected train SHA and held-out row count
  - records baseline evidence manifest and expected eval family

### 2) Training framework configs restored

- `configs/training/sft_config.yaml`
  - primary Unsloth path
- `configs/training/sft_llamafactory.yaml`
  - fallback path only

Both now describe the current canonical package rather than the obsolete early training state.

### 3) Fine-tune preflight now hard-checks the frozen package

- `scripts/finetune/check_finetune_config.py`
- `scripts/finetune/handoff_config.py`

This handoff layer now verifies:

- train file exists
- held-out file exists
- eval question set exists
- baseline evidence manifest exists
- train SHA matches the frozen package
- held-out row count matches the frozen package
- placeholder marker scan passes
- baseline manifest role / eval family stay aligned
- `scripts/check_training_readiness.py --mode preflight` passes through the same policy already used elsewhere in the repo

So the training entrypoint now consumes the same hard gate the rest of the repo already trusts, instead of reintroducing a side policy.

### 4) Post-train command chain is now generated from the same config

- `scripts/finetune/plan_posttrain_eval.py`

This script builds the first official shell/JSON plan for:

- preflight
- direct post-train eval
- post-train evidence manifest
- promotion gate
### 5) DGX bootstrap runbook restored

- `docs/finetune/dgxnode2-lora-bootstrap.md`

This now documents:

- bootstrap
- node preflight
- active package gate
- primary vs fallback config choice
- mandatory post-train manifest + promotion steps

## Outcome

The repo now has a coherent official path for:

1. environment bootstrap
2. node preflight
3. package / readiness validation
4. framework config selection
5. post-train evidence preparation

## Remaining Blocker

This milestone restores the execution chain inside the repo. It does not create a real trained checkpoint by itself.

The next milestone remains:

- generate the first real post-train raw eval report against a newly trained checkpoint
- freeze the corresponding post-train evidence manifest
- run the promotion gate with baseline vs post-train manifests
