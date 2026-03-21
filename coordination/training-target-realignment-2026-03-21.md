# Training Target Realignment

Date: 2026-03-21
Scope: import proven external FINAL_SETTINGS and update the fine-tune execution direction
Decision: the primary fine-tune target is now `dgxnode3` on the Qwen3.5 Unsloth path; `dgxnode2` is kept for inference/recovery, and `dgxnode4` GPT-OSS remains an alternative experimental track

## Verified External Inputs

### 1) Qwen3.5 proven path

Found on:

- host: `dgxnode3`
- file: `/home/btankut/dgx-spark-unsloth-qwen3.5-training/FINAL_SETTINGS.md`

Key facts imported:

- base model: `unsloth/Qwen3.5-35B-A3B`
- single-device training
- `load_in_16bit=True`
- `load_in_4bit=False`
- `gpu_memory_utilization=0.95`
- dedicated `run_train.sh` + `train.py` path
- proven Docker image already exists on host:
  - `dgx-spark-qwen3.5:latest`

Important compatibility fact:

- the proven node3 trainer consumes ShareGPT `conversations` JSONL
- it calls `standardize_sharegpt(...)`

So the current repo's Alpaca-style active package is not a drop-in input for that trainer.

### 2) GPT-OSS proven path

Found on:

- host: `dgxnode4`
- file: `/home/btankut/dgx-spark-gpt-oss-120b/FINAL_SETTINGS.md`

Key facts imported:

- base/train target: `unsloth/gpt-oss-120b`
- QLoRA 4-bit
- `device_map single`
- effective batch size `4`
- final train loss `1.084`
- peak reserved memory `61.447 GB`

This is useful as a proven alternative track, but it does not match the repo's current frozen Qwen-first promotion chain.

## Repo Impact

### 1) Primary node decision

The repo should now treat:

- `dgxnode3` as primary Qwen fine-tune target
- `dgxnode2` as inference / runtime recovery target
- `dgxnode4` as alternative experimental training target

### 2) Missing bridge identified

Current active train package:

- `data/finetune/sft/final_train.jsonl`

Current format:

- Alpaca-style `instruction` + `input` + `output`

Node3 proven trainer expects:

- ShareGPT `conversations`

Therefore the missing bridge is not data quality; it is transport format compatibility.

### 3) Canonical truth-source drift still mattered

The repo had config drift between:

- `configs/finetune/unsloth_sft_qwen35_35b_a3b.json`
- `configs/training/sft_config.yaml`

Since the active smoke-validated entrypoint reads the JSON config, the YAML side should align to that truth instead of diverging.

## Implemented Direction

This milestone introduces the cleanest low-risk bridge first:

- add a repo-native ShareGPT exporter for the active frozen package
- keep the active canonical package unchanged
- keep GPT-OSS outside the primary promotion chain
- point the next execution step to node3 preflight/export/smoke instead of more training work on node2

## Next Step

1. Export the active 807-row package into ShareGPT format.
2. Sync the repo to `dgxnode3`.
3. Run node3 preflight against the frozen package.
4. Run a bounded node3 smoke using the Qwen proven path.
5. Only after that, consider whether GPT-OSS deserves a first-class repo track.
