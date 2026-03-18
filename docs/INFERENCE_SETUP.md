# INFERENCE SETUP — Qwen3.5 + Hukuk-AI Fine-Tuned Model

This document captures the **currently working** inference setup and the key operational pitfalls discovered during deployment tests.

## Working Runtime

- **Container image:** `vllm/vllm-openai:cu130-nightly`
- **Image build:** v0.17.2rc0 (CUDA 13.0)
- **Why this image:** Required for **Qwen3.5** support. Standard/stable vLLM images were not sufficient for this model stack during testing.
- **Reference implementation:** https://github.com/adadrag/qwen3.5-dgx-spark

---

## Recommended: Serve the MERGED Fine-Tuned Model

> Use merged weights for production serving. Direct LoRA adapter loading currently crashes in vLLM (details below).

```bash
docker run -d \
  --name qwen35-ft \
  --gpus all --ipc host --shm-size 64gb \
  -p 30000:30000 \
  -v /path/to/merged-model:/model \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:cu130-nightly \
  /model \
  --served-model-name hukuk-ai-ft \
  --port 30000 --host 0.0.0.0 \
  --gpu-memory-utilization 0.80 \
  --enforce-eager \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice --tool-call-parser qwen3_coder \
  --enable-prefix-caching --language-model-only
```

---

## ⚠️ Known Issues (Critical)

1. **LoRA adapter crashes vLLM**
   - Error: `IndexError: list index out of range`
   - Location: `column_parallel_linear.py` in `set_lora`
   - Root cause: LoRA adapter structure is incompatible with current vLLM layer expectations in this stack.
   - **Action:** Do **not** serve adapter directly. Use **merged model**.

2. **Merged model + torch.compile crash**
   - Error: `TorchRuntimeError: shape invalid`
   - **Action:** launch with `--enforce-eager` to bypass compile/graph path.

3. **Performance drop with enforce-eager**
   - GPU utilization drops from ~96% to ~50–60%
   - Throughput drops from ~31 tok/s to ~15 tok/s
   - This is expected under current workaround.

4. **Memory recovery after container crash**
   - After crash, memory cache must be cleaned before restart to avoid cascading OOM behavior.
   - Command:
     ```bash
     sync; echo 3 | sudo tee /proc/sys/vm/drop_caches
     ```

5. **Do not enable restart policy right now**
   - Avoid `--restart unless-stopped`
   - Reason: automatic restart without memory cleanup can trigger OOM crash loop.

---

## Base Model Serving (Comparison / Baseline)

```bash
docker run -d \
  --name qwen35-base \
  --gpus all --ipc host --shm-size 64gb \
  -p 30001:30001 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:cu130-nightly \
  Qwen/Qwen3.5-35B-A3B \
  --served-model-name qwen35-base \
  --port 30001 --host 0.0.0.0 \
  --gpu-memory-utilization 0.80 \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice --tool-call-parser qwen3_coder \
  --enable-prefix-caching --language-model-only
```

**Note:** Base model works **without** `--enforce-eager` (CUDA graphs + `torch.compile` path is functional there).

---

## Operational Notes

- Prefer manual lifecycle control (`docker stop/start`) until adapter/compile issues are resolved upstream.
- Keep HF cache mounted (`~/.cache/huggingface`) to avoid repeated cold downloads.
- For benchmarks, compare both quality and throughput because current workaround trades speed for stability.
