# DGXNode2 Overnight Launch Recovery

Date: 2026-03-21
Scope: make the restored post-train diagnostic and training chain observable under unstable SSH sessions
Decision: treat the current blocker as remote access stability, not model-class or dataset-gate failure, and switch overnight execution strategy to detached log-backed jobs

## Verified Progress Before SSH Instability

### 1) Remote training gate passes on dgxnode2

The restored repo copy on `dgxnode2` reached:

- `scripts/finetune/check_finetune_config.py`
- result: `READY_FOR_TRAINING_GATE`

This confirms the remote worktree had:

- active `807`-row canonical train package
- held-out file
- baseline evidence manifest
- preflight readiness contract passing on-node

### 2) Base model cache exists on dgxnode2

Verified Hugging Face cache contents included:

- `models--Qwen--Qwen3.5-35B-A3B`
- `models--unsloth--Qwen3.5-35B-A3B`

So the first practical blocker is no longer “model missing”.

### 3) Direct diagnostic fallback reaches real model load

`evaluation/eval_transformers_direct.py` against the historical merged checkpoint:

- loaded weights to `100%`
- entered question generation

This means the repo-native direct fallback bypasses the earlier `qwen3_5_moe` serving-image mismatch at least through model initialization.

### 4) Text-only PEFT dry-run reaches real shard loading

`scripts/finetune/train_qwen35_textonly_peft.py --dry-run --max-train-samples 2` on dgxnode2:

- passed config parse
- selected `cuda:0`
- began loading `Qwen/Qwen3.5-35B-A3B`
- reached deep into shard load progress before the SSH session dropped

This materially reduces uncertainty around:

- HF auth/cache
- early `Qwen3_5MoeForCausalLM` import
- immediate single-device load refusal

## Actual Current Blocker

During the overnight probe window, `ssh` access to `dgxnode2` degraded from working to unstable:

- connection reset by peer
- broken pipe during `rsync`
- later full timeout on port `22`
- fabric IP (`192.168.101.12`) also timed out on `ssh`

At this point the critical blocker is:

- **remote SSH stability**

Not yet proven as blockers:

- model-class incompatibility
- frozen dataset gate
- missing HF cache

## Recovery Change Added To Repo

To avoid losing progress when SSH drops mid-run, the repo now includes:

- `scripts/finetune/detach_logged_job.py`

Purpose:

- launch background jobs
- persist combined stdout/stderr to a log file
- persist child pid to a pid file
- allow overnight polling without holding open the launch SSH session

Local verification passed:

- `python3 -m py_compile scripts/finetune/detach_logged_job.py`
- `pytest tests/test_detach_logged_job.py`

## Next Action

When `ssh` access to dgxnode2 recovers:

1. sync the latest repo worktree (or at minimum the detached launcher)
2. relaunch:
   - text-only PEFT dry-run
   - direct diagnostic eval smoke
3. run both as detached, log-backed jobs
4. only after stable logs are available, start:
   - first bounded training smoke checkpoint
   - first bounded post-train diagnostic run

## Decision

The official overnight strategy is now:

- **do not rely on long interactive SSH sessions for heavy dgxnode2 jobs**
- use detached log-backed launch as the default operational path
