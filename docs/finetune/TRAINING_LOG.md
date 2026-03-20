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
