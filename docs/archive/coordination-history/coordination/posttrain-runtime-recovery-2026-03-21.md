# Post-Train Runtime Recovery

Date: 2026-03-21
Scope: verify whether the historical fine-tuned merged checkpoint can be brought back into a runnable post-train eval path
Decision: the historical merged checkpoint still exists on dgxnode2, but the first recovery attempt is blocked by runtime/image compatibility rather than missing model files

## Verified Facts

### 1) Historical merged checkpoint still exists

Verified directly on `dgxnode2 (192.168.12.236)`:

- path: `/home/btankut/hukuk-ai-finetune/outputs/hukuk-ai-lora-v2/merged`
- size: ~`65G`
- files include:
  - `config.json`
  - `tokenizer.json`
  - `model-00001-of-00008.safetensors`
  - `...`
  - `model-00008-of-00008.safetensors`

So the current blocker is **not** “checkpoint lost”.

### 2) No active FT serving container was present

`docker ps` on dgxnode2 returned no running containers at the time of inspection.

### 3) Historical FT eval endpoint was down

Direct probe failed:

- `http://192.168.12.236:30002/v1/models`

This confirms the historical FT eval runtime was not already serving.

## Recovery Attempts

### Attempt 1 — direct `docker run ... vllm serve /model ...`

The image `hellohal2064/vllm-qwen3.5-gb10:latest` was present locally on dgxnode2.

However, the container entrypoint ignored the intended model path/port and fell back to its own defaults:

- model: `/models/Qwen3-Next-80B-A3B-Thinking-FP8`
- port: `8000`

Root cause:

- the image uses `/app/entrypoint.sh`
- model/port are controlled primarily by environment variables such as:
  - `MODEL_PATH`
  - `HOST`
  - `PORT`

### Attempt 2 — env-driven relaunch

Container relaunched as:

- name: `hukuk-ft-eval`
- port: `30002`
- model mount: `/model`
- `MODEL_PATH=/model`
- `ENABLE_THINKING=false`

This time the container bootstrapped correctly toward the intended path and port.

## Actual Runtime Blocker

The relaunch still failed during vLLM model initialization:

- checkpoint model type: `qwen3_5_moe`
- runtime error: current `Transformers` in the image does not recognize that architecture

Therefore the blocking issue is now explicitly:

- **runtime compatibility mismatch**
- not missing checkpoint
- not missing image
- not missing GPU availability

## Outcome

The post-train path has been narrowed to a concrete blocker:

1. checkpoint exists
2. isolated FT eval port can be reserved
3. current image cannot load `qwen3_5_moe`

## Next Options

### Option A — update/replace serving image

Bring up a vLLM image whose `Transformers` stack supports `qwen3_5_moe`.

This is the cleanest path if the target remains:

- OpenAI-compatible endpoint
- `evaluation/eval_vllm_direct.py`
- manifest + promotion chain

### Option B — direct merged-model eval fallback

Use the historical direct evaluator discovered in backup:

- `/Users/btmacstudio/openclaw-backup-20260320/workspace/projects/hukuk-ai/data/finetune/eval_merged_model.py`

This avoids vLLM serving and evaluates the merged model directly with `transformers`.

If restored into the repo, it can become the temporary post-train evidence path while the serving image is modernized.
