# DGXNode3 Qwen Full Run Success

Date: 2026-03-21
Scope: record the successful completion of the first detached full Qwen3.5 fine-tune run on the user-provided proven node3 training path using the active frozen 807-row package
Decision: the training milestone is closed successfully; the next valid step is post-train evaluation and evidence production, not another training launch

## Run Identity

- host: `dgxnode3`
- trainer path: `/home/btankut/dgx-spark-unsloth-qwen3.5-training`
- launch wrapper: `scripts/finetune/launch_dgxnode3_qwen_external.sh full`
- dataset bridge: ShareGPT export of `data/finetune/sft/final_train.jsonl`
- exported rows: `807`

## Completion Evidence

The detached run completed cleanly and wrote the final trainer footer:

- epochs: `3`
- global steps: `606`
- train runtime: `1.007e+04` seconds
- train samples per second: `0.24`
- train steps per second: `0.06`
- final logged train loss: `0.5051`

The same output tree also contains:

- final checkpoint: `/home/btankut/dgx-spark-unsloth-qwen3.5-training/outputs/hukuk_ai_active_807_run/checkpoint-606`
- final adapter: `/home/btankut/dgx-spark-unsloth-qwen3.5-training/outputs/hukuk_ai_active_807_run/lora_adapter`
- adapter weights file: `adapter_model.safetensors`
- adapter size: `3724487160` bytes

## Artefact Inventory

Verified output directories:

- `checkpoint-100`
- `checkpoint-200`
- `checkpoint-300`
- `checkpoint-400`
- `checkpoint-500`
- `checkpoint-600`
- `checkpoint-606`
- `lora_adapter`

## Acceptance

This closes the training execution milestone because:

1. the frozen active package reached full completion on the proven node3 path
2. the final adapter exists at a stable remote path
3. the run produced resumable checkpoints plus a final adapter export

## Next Step

1. bind this adapter to the repo's post-train eval identity chain
2. run matched post-train evaluation and build its evidence manifest
3. compare the resulting manifest against the frozen baseline manifest before any promotion decision
