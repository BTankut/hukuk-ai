# DGXNode3 Qwen Smoke Success

Date: 2026-03-21
Scope: validate the newly added ShareGPT bridge against the proven external Qwen3.5 training path on `dgxnode3`
Decision: the node3 Qwen path is now operational with the active frozen 807-row package; `dgxnode3` can be treated as the primary fine-tune target

## Verified Facts

### 1) Repo-native preflight passed on node3

Remote repo copy:

- `/home/btankut/hukuk-ai-git`

Observed result:

- `READY`
- `[RESULT] READY_FOR_TRAINING_GATE`

This confirms the frozen active package, held-out set, duplicate gate, and baseline evidence contract remain valid on the node3 copy.

### 2) ShareGPT export passed on node3

Command result on node3:

- input: `/home/btankut/hukuk-ai-git/data/finetune/sft/final_train.jsonl`
- output: `/home/btankut/hukuk-ai-git/data/finetune/sft/final_train_sharegpt.jsonl`
- exported rows: `807`
- skipped rows: `0`

This is the compatibility bridge required by the proven node3 Qwen trainer.

### 3) Proven external Qwen repo consumed the exported active package

External proven training repo:

- `/home/btankut/dgx-spark-unsloth-qwen3.5-training`

Exported dataset copied to:

- `/home/btankut/dgx-spark-unsloth-qwen3.5-training/data/hukuk_ai_active_807_sharegpt.jsonl`

Observed trainer/runtime facts:

- Docker image: `dgx-spark-qwen3.5:latest`
- model load completed
- dataset standardized successfully
- trainer reached step `1/1`

### 4) One-step node3 smoke passed

Observed result from the external proven Qwen path:

- total steps: `1`
- total epochs configured for smoke: `1`
- train loss: `1.634`
- train runtime: `72.03s`
- adapter saved to:
  - `/home/btankut/dgx-spark-unsloth-qwen3.5-training/outputs/hukuk_ai_active_807_smoke/lora_adapter`

Observed output artefacts:

- `lora_adapter/adapter_model.safetensors`
- `checkpoint-1/adapter_model.safetensors`
- `checkpoint-1/trainer_state.json`
- `checkpoint-1/optimizer.pt`

## Outcome

The training target realignment is no longer theoretical:

1. node3 gate passed
2. node3 ShareGPT bridge passed
3. node3 proven Qwen trainer consumed the active package
4. node3 one-step smoke completed successfully

This is stronger evidence than the earlier node2 recovery smoke because it uses the historically proven external Qwen training path the user pointed to.

## Next Step

Immediate next action:

1. freeze a repo-native launcher/runbook for the node3 proven path
2. start the full node3 Qwen run against the active 807-row package
3. keep dgxnode2 reserved for inference/runtime work
