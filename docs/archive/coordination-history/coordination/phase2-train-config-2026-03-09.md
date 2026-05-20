# Phase 2 Training Config Wiring — Recovery Report (2026-03-09)

**Branch:** `feat/phase2-train-config`
**Commit Hash:** `8b29710`
**Status:** ✅ COMMITTED & PUSHED (new branch on GitHub)

---

## 1. What Was Recovered

The previous subagent run left three untracked files without committing:

| File | Description |
|------|-------------|
| `configs/training/sft_config.yaml` | Primary Unsloth LoRA training config |
| `configs/training/sft_llamafactory.yaml` | LLaMA-Factory alternative config |
| `scripts/build_training_dataset.py` | Dataset assembly + quality gate script |

All three were coherent and production-ready. Recovery also ran the build script to produce `data/finetune/sft/final_train.jsonl`, then committed all four files.

---

## 2. Expected Input Datasets

### Primary (lawyer-reviewed, committed)
| Path | Count | Notes |
|------|-------|-------|
| `data/review_sheets/phase2_first_batch_20260308/reconciled_20260308/batch1_first100_reconciled_master.jsonl` | 100 rows | Batch 1 reconciled by two lawyers; all 100 included in training |

### Supplementary (scaffolding only — real data pending)
| Path | Status |
|------|--------|
| `data/finetune/sft/legal_qa.jsonl` | SCAFFOLDING (1 dummy line) |
| `data/finetune/sft/petition_examples.jsonl` | SCAFFOLDING (1 dummy line) |
| `data/finetune/sft/rag_corrected.jsonl` | SCAFFOLDING (1 dummy line) |
| `data/finetune/sft/refusal_examples.jsonl` | SCAFFOLDING (1 dummy line) |

### Held-Out Eval
| Path | Status |
|------|--------|
| `data/finetune/eval/held_out_test.jsonl` | SCAFFOLDING (1 dummy line) |

---

## 3. Dataset Build Results (`build_training_dataset.py`)

```
Reconciled: 100 loaded  (approved=53, revised=47)
Deduplication: removed 8 duplicates
Training examples written: 92
Output: data/finetune/sft/final_train.jsonl
```

**Quality Gate:**
- ✅ Gate 1: 92 examples ≥ 80 (min threshold)
- ✅ Gate 2: 0.0% empty outputs
- ⚠️  Gate 3: 42.4% outputs missing `[Kaynak:]` citation tag (soft warning, threshold 30%)

---

## 4. Held-Out / Base-vs-Finetuned Wiring

### Held-out separation
- `build_training_dataset.py` reads `data/finetune/eval/held_out_test.jsonl` and filters any training example whose question appears in the eval set.
- **Currently**: held-out file is scaffolding only → no contamination filtering applied yet.
- **When real held-out set is populated**: wiring is in place and will activate automatically.

### Base vs. Finetuned model paths
| Phase | Model | Host | Path |
|-------|-------|------|------|
| Base (current prod) | `Qwen/Qwen3.5-35B-A3B-FP8` | dgxnode1 | HF default / vLLM |
| Finetuned (post-SFT) | `hukuk-ai-sft-v1` (LoRA merged, FP8) | dgxnode2 → deploy to dgxnode1 | `/home/btankut/models/hukuk-ai-sft-v1` |
| Rollback | Base model | dgxnode1 | Revert `MODEL_PATH` in `start-tp1.sh` |

Training is targeting **dgxnode2** (128GB VRAM DGX Spark, not dgxnode1 which is production inference).

Export pipeline: `merge_and_save → quantize_to_fp8 → gguf_export (q8_0)`.

---

## 5. Remaining Blockers

| Blocker | Severity | Notes |
|---------|----------|-------|
| Supplementary SFT files are scaffolding | P1 | `legal_qa.jsonl`, `petition_examples.jsonl`, `rag_corrected.jsonl`, `refusal_examples.jsonl` need real data from Phase 1 log extraction pipeline |
| Held-out test set is scaffolding | P1 | `held_out_test.jsonl` must be populated before eval numbers are meaningful; requires carving ~100 items from approved pool |
| Citation gap (42.4% missing `[Kaynak:]`) | P2 | Soft warning now; should be addressed in revised answers before training launch. Affects citation-following fine-tuning signal quality. |
| 92 examples is at quality gate floor | P2 | `min_training_examples=80`; 92 passes but is low. Next review batch should push to 200+ before real training run. |
| Unsloth + Qwen3.5-35B-A3B compatibility not validated on dgxnode2 | P2 | `sft_llamafactory.yaml` exists as fallback; PyTorch cu130 env setup not yet executed. |
| W&B / metrics tracking disabled | P3 | `report_to: none` in both configs. Enable before production training run. |
| PR not yet opened | — | Branch pushed; PR creation is a manual step for coordinator. |

---

## 6. Files Changed

| File | Action |
|------|--------|
| `configs/training/sft_config.yaml` | NEW — Unsloth primary config |
| `configs/training/sft_llamafactory.yaml` | NEW — LLaMA-Factory alternative |
| `scripts/build_training_dataset.py` | NEW — dataset assembly + quality gate |
| `data/finetune/sft/final_train.jsonl` | NEW — 92-example first-pass training set |

---

## 7. Next Steps

1. **Populate held-out test set** — carve ~100 items from batch1 approved pool into `held_out_test.jsonl`.
2. **Fill supplementary SFT files** — run `extract_qa_from_logs.py` on Phase 1 production logs.
3. **Fix citation gap** — review/revise the 39 examples missing `[Kaynak:]` tags before training.
4. **Validate dgxnode2 environment** — test Unsloth install; if issues, fall back to LLaMA-Factory.
5. **Open PR** — `feat/phase2-train-config` → `main`.
6. **Launch training** — only after held-out set and supplementary files are real.
