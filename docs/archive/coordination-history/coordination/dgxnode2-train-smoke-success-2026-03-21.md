# DGXNode2 Train Smoke Success

Date: 2026-03-21
Scope: detached dgxnode2 training-chain recovery after SSH returned
Decision: the official text-only PEFT execution chain is now restored on `dgxnode2`; live `8080` inference remains a separate runtime blocker

## Verified Facts

### 1) Live `8080` runtime is still absent

- `curl http://192.168.12.236:8080/v1/models` returned connection failure.
- `ss -ltnp` on `dgxnode2` did not show a listener on `8080`.
- The only obvious long-lived app listener was:
  - `0.0.0.0:8000` → `unsloth studio`

This means the current blocker is not local gateway or retrieval anymore; it is the upstream live model runtime.

### 2) Historical node2 runtime traces still exist, but they are not active

- `/home/btankut/sglang_qwen3_node2.log`
- `/home/btankut/sglang_qwen3_node2.pid`
- `/home/btankut/qwen3_fp8_node2_autostart.sh`

Observed from the historical log:

- the old node2 serving path was `sglang`
- it booted on `31000`
- it loaded weights successfully once
- it then hit scheduler/warmup exceptions and no active listener remained

So the node2 serving problem is a runtime/serving issue, not a missing-host issue.

### 3) Detached dry-run passed

Remote command path:

- repo: `/home/btankut/hukuk-ai-git`
- script: `scripts/finetune/train_qwen35_textonly_peft.py`
- log: `/home/btankut/hukuk-ai-git/runtime_logs/train_dryrun_latest.log`

Observed result:

- `DRY_RUN_OK`
- `loaded_model_class=Qwen3_5MoeForCausalLM`
- `load_time_s=281.49`
- `peak_mem_allocated_gb=64.59`
- `peak_mem_reserved_gb=64.64`

This confirms the restored repo-native training entrypoint can load the target base model on dgxnode2.

### 4) One-step real training smoke passed

Detached smoke command wrote to:

- log: `/home/btankut/hukuk-ai-git/runtime_logs/train_smoke_step1_latest.log`
- output dir: `/home/btankut/hukuk-ai-git/artifacts/finetune/unsloth-sft-qwen35-35b-a3b/smoke-step1-20260321`

Observed result:

- `TRAIN_OK`
- `adapter_dir=artifacts/finetune/unsloth-sft-qwen35-35b-a3b/smoke-step1-20260321/adapter`
- `train_global_steps=1`
- `train_runtime=35.82`
- `train_loss=0.5954`
- `step_time_s=33.607`
- `peak_mem_allocated_gb=66.23`
- `peak_mem_reserved_gb=66.79`

Produced artefacts include:

- `adapter/adapter_model.safetensors`
- `adapter/adapter_config.json`
- `checkpoint-1/adapter_model.safetensors`
- `checkpoint-1/trainer_state.json`
- `checkpoint-1/optimizer.pt`

This is the first confirmed bounded real training step on the restored official text-only chain against the frozen 807-row package.

### 5) Historical merged checkpoint remains available

Verified again on `dgxnode2`:

- path: `/home/btankut/hukuk-ai-finetune/outputs/hukuk-ai-lora-v2/merged`
- size: `65G`

This keeps the direct diagnostic fallback path open for immediate post-train signal recovery.

## Outcome

The repo-native dgxnode2 training chain is no longer theoretical:

1. dry-run passed
2. one-step smoke passed
3. adapter and checkpoint artefacts were written

The live inference blocker is now cleanly isolated:

1. `8080` runtime is down
2. no active listener exists on host
3. this does not block detached diagnostic eval on the historical merged checkpoint

## Next Step

Immediate next action:

- run detached historical merged direct diagnostic eval with:
  - `evaluation/eval_transformers_direct.py`
  - report role `diagnostic_post_train`
  - matching evidence manifest

Separate follow-up work:

- restore or replace the `192.168.12.236:8080` serving path
- keep that work out of the promotion chain until runner parity is re-established
