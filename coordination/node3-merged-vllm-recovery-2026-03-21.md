# Node3 Merged vLLM Recovery

Date: 2026-03-21
Scope: recover a faster production-style serving path for the current merged `807` post-train candidate on `dgxnode3`
Decision: the merged checkpoint itself is valid; the active blocker narrowed from merge correctness to serving-runtime compatibility and unified-memory sizing

## Verified

- Current merged checkpoint exists and is a real full model:
  - `/home/btankut/dgx-spark-unsloth-qwen3.5-training/outputs/hukuk_ai_active_807_run/merged_model`
  - includes `model-00001-of-00002.safetensors`, `model-00002-of-00002.safetensors`, `model.safetensors.index.json`
  - total size: ~`66G`

- The first official Unsloth `merged_16bit` path was not reliable on its own for this artifact:
  - log emitted `Model is not a PeftModel (no Lora adapters detected). Skipping Merge.`
  - repo merge helper was hardened to validate the output and fall back to `merge_and_unload()`

- The fallback merge path succeeded and produced the usable merged checkpoint above.

## Serving Findings

### 1) `cu130-nightly` tokenizer path failed

Image:

- `vllm/vllm-openai:cu130-nightly`

Outcome:

- startup failed during tokenizer initialization
- root error:
  - `ValueError: Tokenizer class TokenizersBackend does not exist or is not currently imported.`

Adding:

- `--trust-remote-code`
- `--tokenizer unsloth/Qwen3.5-35B-A3B`

did not fix this path in practice for the local merged checkpoint.

### 2) `vllm-node-tf5` matched the Faz 1 runtime family and passed tokenizer init

Image:

- `vllm-node-tf5:latest`

This image successfully moved past the tokenizer crash and started real weight loading for:

- architecture: `Qwen3_5MoeForConditionalGeneration`
- model path: `/model`

So the blocker is not “merged checkpoint unreadable”.

### 3) Unified-memory cache cleanup is required before launch

Before cleanup:

- node memory looked effectively crowded for vLLM startup

After:

```bash
sync
echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null
```

available memory recovered from roughly the mid-30 GiB range to roughly:

- `117Gi` available

This matches the already documented DGX recovery pattern for post-crash relaunches.

### 4) `gpu_memory_utilization=0.50` was too low

At `0.50`:

- full weight loading completed
- weight load time: `671.59s`
- model load memory: `65.53 GiB`
- then vLLM failed with:
  - `Available KV cache memory: -8.93 GiB`
  - `ValueError: No available memory for the cache blocks`

This means:

- low utilization avoided early startup rejection
- but starved KV cache allocation after the model finished loading

## Repo Changes

- `scripts/finetune/launch_dgxnode3_merged_vllm.sh`
  - default image switched to `vllm-node-tf5:latest`
  - launch path switched to the direct `python3 -m vllm.entrypoints.openai.api_server` form used by the Faz 1 runtime family
  - host networking adopted
  - pre-launch cache drop support added
  - default `gpu_memory_utilization` raised from the temporary `0.50` test value to `0.70`

## Current State

- repo-native launcher has already relaunched the runtime with:
  - `image=vllm-node-tf5:latest`
  - `max_model_len=8192`
  - `gpu_memory_utilization=0.70`
  - `enforce_eager=true`
- this relaunch is the current active attempt

## Next Step

1. wait for the `0.70` relaunch to finish loading
2. verify `http://127.0.0.1:30003/v1/models`
3. open the local tunnel + candidate gateway on `8003`
4. run a cited smoke and compare latency against the previous adapter/proxy path
