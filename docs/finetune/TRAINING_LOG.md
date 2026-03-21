# TRAINING LOG — Faz-3 Fine-Tuning

> **Important:** The previous "complete" training run (v1) is invalid and has been discarded.  
> The current active train package is the canonicalized lawyer-reviewed set at `data/finetune/sft/final_train.jsonl`.
>
> **2026-03-21 package freeze:** `scripts/build_training_dataset.py` now reproduces the active package by default, including held-out filtering and final duplicate canonicalization. The committed `final_train.jsonl` now contains **807** training rows and **807** unique questions.
>
> **Promotion note:** historical v2 training on 2026-03-18 used the earlier **1076**-row snapshot that existed at the same path at that time. That run remains auditable, but it is **not promotion-eligible** against the current frozen package until re-run and re-evaluated.

## Snapshot

- **Current active train package:** `data/finetune/sft/final_train.jsonl`
- **Active package size:** `807`
- **Readiness status:** `READY` (2026-03-21 preflight)
- **Historical output under audit:** `outputs/hukuk-ai-lora-v2`

## Execution Recovery — 2026-03-21

- **Node:** `dgxnode2`
- **Chain:** official text-only PEFT entrypoint
- **Dry-run status:** `PASS`
- **One-step smoke status:** `PASS`

### Dry-run evidence

- `loaded_model_class=Qwen3_5MoeForCausalLM`
- `load_time_s=281.49`
- `peak_mem_reserved_gb=64.64`
- Result: `DRY_RUN_OK`

### One-step smoke evidence

- `max_train_samples=8`
- `max_steps=1`
- `train_runtime=35.82`
- `step_time_s=33.607`
- `train_loss=0.5954`
- `peak_mem_reserved_gb=66.79`
- Result: `TRAIN_OK`

### Artefacts

- remote adapter: `artifacts/finetune/unsloth-sft-qwen35-35b-a3b/smoke-step1-20260321/adapter`
- remote checkpoint: `artifacts/finetune/unsloth-sft-qwen35-35b-a3b/smoke-step1-20260321/checkpoint-1`

### Note

- This smoke restores confidence in the execution chain only.
- It does **not** replace the need for a fresh full run against the frozen package plus post-train evidence.

## Node3 Proven Path Smoke — 2026-03-21

- **Node:** `dgxnode3`
- **Trainer path:** external proven Qwen3.5 Unsloth repo
- **Input bridge:** exported ShareGPT view of the active 807-row package
- **Status:** `PASS`

### Evidence

- repo copy preflight: `READY_FOR_TRAINING_GATE`
- ShareGPT export: `807` rows, `0` skipped
- smoke steps: `1`
- train runtime: `72.03`
- train loss: `1.634`

### Artefacts

- external adapter: `/home/btankut/dgx-spark-unsloth-qwen3.5-training/outputs/hukuk_ai_active_807_smoke/lora_adapter`
- external checkpoint: `/home/btankut/dgx-spark-unsloth-qwen3.5-training/outputs/hukuk_ai_active_807_smoke/checkpoint-1`

### Note

- This is the first successful smoke using the user-provided proven Qwen3.5 training path with the repo's frozen active package.
- The next valid milestone is a full run plus post-train evidence, not promotion by smoke alone.

## Node3 Proven Path Full Run — 2026-03-21

- **Node:** `dgxnode3`
- **Trainer path:** external proven Qwen3.5 Unsloth repo
- **Input bridge:** exported ShareGPT view of the active 807-row package
- **Status:** `PASS`

### Evidence

- epochs: `3`
- global steps: `606`
- train runtime: `1.007e+04`
- train samples per second: `0.24`
- train steps per second: `0.06`
- final train loss: `0.5051`

### Artefacts

- external final adapter: `/home/btankut/dgx-spark-unsloth-qwen3.5-training/outputs/hukuk_ai_active_807_run/lora_adapter`
- external final checkpoint: `/home/btankut/dgx-spark-unsloth-qwen3.5-training/outputs/hukuk_ai_active_807_run/checkpoint-606`
- adapter weights size: `3724487160` bytes

### Note

- This is the first completed full run on the frozen active package using the user-provided proven Qwen3.5 path.
- The next valid milestone is matched post-train evaluation plus evidence manifest production.

## Node3 Post-Train Evaluation — 2026-03-21

- **Node:** `dgxnode3`
- **Serving chain:** external adapter serve -> repo OpenAI proxy -> local SSH tunnel -> candidate gateway `127.0.0.1:8002`
- **Eval family:** `faz1-50`
- **Runner:** `eval_runner`
- **Promotion gate status:** `READY`

### Official artefacts

- raw report: `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_node3_20260321_t600.json`
- evidence manifest: `evaluation/reports/evidence_post_train_faz1_50_hukuk_ai_sft_qwen35_807_node3_20260321_t600.json`

### Summary

- citation rate: `0.9000`
- correct source rate: `0.7713`
- hallucination rate: `0.0200`
- refusal accuracy: `1.0000`
- avg response time: `120302.8 ms`
- error count: `0`

### Note

- This closes the repo's formal post-train evidence requirement for the frozen 807-row package.
- It does **not** mean the candidate has matched the original Faz 1 live latency picture; the current served path is still far slower than the desired live target.

---

## Training v1 — INVALID (Wrong Dataset)

- **Date:** 2026-03-17
- **Dataset used:** `sft_training_v1.jsonl`
- **Dataset size:** 388 pairs
- **Data type:** synthetic/eval-style pairs

### What went wrong

- The final, lawyer-reviewed training set was already available at:
  - `data/finetune/sft/final_train.jsonl` (1076 pairs)
- However, v1 was launched with `sft_training_v1.jsonl` (388 synthetic pairs) instead.
- Therefore, v1 does **not** represent the intended quality baseline for production.

### Config

- Framework: **Axolotl**
- Method: **LoRA**
- LoRA rank: **r=16**
- Target modules: **q_proj + v_proj**
- Epochs: **3**
- Learning rate: **2e-5**

### Run result (for record only)

- Total steps: **273**
- Final loss: **0.5535**
- Duration: **78 minutes**

### Status

- **DISCARDED**
- Old training artifact/data file removed from active workflow:
  - `data/finetune/sft_training_v1.jsonl` (deleted)

---

## Training v2 — HISTORICAL (Pre-Canonicalization Snapshot)

- **Date:** 2026-03-18
- **Dataset used:** `data/finetune/sft/final_train.jsonl`
- **Dataset size:** 1076 pairs
- **Data provenance:** lawyer-reviewed
  - **137** directly approved by lawyers
  - **939** rewritten/corrected by lawyers (highest quality subset)

### Config

- Framework: **Axolotl**
- Method: **LoRA**
- LoRA rank: **r=16**
- Target modules: **q_proj + v_proj**
- Epochs: **3**
- Learning rate: **2e-5**
- Warmup steps: **30**

### Runtime / hardware

- Node: **dgxnode2**
- GPU: **NVIDIA GB10**
- Memory: **128GB unified memory**

### Progress (live)

- Total planned steps: **405**
- Average speed: **~30 sec/step**
- Current state: **~70% complete**
- Observed loss: **~0.37** at epoch **2.1**

### Output

- Active output directory: `outputs/hukuk-ai-lora-v2`

### Status

- **HISTORICAL / NOT PROMOTION-ELIGIBLE**
- This run predates the held-out leakage fix and duplicate canonicalization freeze.

---

## Decision Record

1. v1 is retained in documentation only for auditability.
2. v1 metrics/loss should not be used in model selection decisions.
3. v2 is the first historical run launched on the lawyer-reviewed path, but it no longer matches the frozen active train package.
4. Subsequent evaluations and deployment decisions must be based on runs executed against the current canonicalized package plus post-train evidence.
