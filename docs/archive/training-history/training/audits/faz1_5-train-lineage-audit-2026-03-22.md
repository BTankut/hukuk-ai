# FAZ 1.5 Train Lineage Audit

**Date:** 2026-03-22  
**Scope:** canonical SFT train package lineage, reduction rationale, and separation proof for the active frozen train set

## Executive Summary

The active canonical train package is the result of a controlled reduction from a historical `1076`-row snapshot to the frozen `807`-row package currently used by `scripts/build_training_dataset.py`.

The reduction is fully explained by three documented filters:

1. `26` exact duplicate rows removed by the builder.
2. `127` held-out contamination rows removed by the builder.
3. `116` duplicate-excess rows removed during final cluster canonicalization.

These deltas add up exactly:

- `1076 - 26 - 127 - 116 = 807`

The final package is reproducible, ready, and separated from held-out data:

- `final_train.jsonl` rows: `807`
- `held_out_test.jsonl` rows: `22`
- exact train/held-out overlap: `0`
- training readiness: `READY`

## Evidence Chain

### Current frozen package

- Train file: [`data/finetune/sft/final_train.jsonl`](/Users/btmacstudio/Projects/hukuk-ai/data/finetune/sft/final_train.jsonl)
- Held-out file: [`data/finetune/eval/held_out_test.jsonl`](/Users/btmacstudio/Projects/hukuk-ai/data/finetune/eval/held_out_test.jsonl)
- Builder: [`scripts/build_training_dataset.py`](/Users/btmacstudio/Projects/hukuk-ai/scripts/build_training_dataset.py)
- Preflight gate: [`scripts/check_training_readiness.py`](/Users/btmacstudio/Projects/hukuk-ai/scripts/check_training_readiness.py)

### Lineage references

- Pre-train execution package: [`coordination/pretrain-execution-package-2026-03-21.md`](/Users/btmacstudio/Projects/hukuk-ai/coordination/pretrain-execution-package-2026-03-21.md)
- Duplicate inventory: [`coordination/training-duplicate-inventory-2026-03-20.md`](/Users/btmacstudio/Projects/hukuk-ai/coordination/training-duplicate-inventory-2026-03-20.md)
- Duplicate cleanup complete: [`coordination/training-duplicate-cleanup-complete-2026-03-20.md`](/Users/btmacstudio/Projects/hukuk-ai/coordination/training-duplicate-cleanup-complete-2026-03-20.md)
- Final canonicalization manifest: [`coordination/training-duplicate-final-canonicalization-2026-03-20.json`](/Users/btmacstudio/Projects/hukuk-ai/coordination/training-duplicate-final-canonicalization-2026-03-20.json)
- Review packet: [`coordination/training-duplicate-review-packet-final-2026-03-20.md`](/Users/btmacstudio/Projects/hukuk-ai/coordination/training-duplicate-review-packet-final-2026-03-20.md)

## 1076 -> 807 Reduction

The historical `1076`-row snapshot came from the active reconciled master sources that were eligible for training at the time. The current builder reproduces the frozen package from those reconciled masters plus the official canonicalization manifest.

The dry-run output on 2026-03-21 reported the exact reduction path:

- `12` reconciled source files discovered
- `0` supplementary active rows
- `26` duplicate rows removed
- `127` held-out contamination rows removed
- `24/24` canonical clusters applied
- `923 -> 807` after canonicalization
- `116 -> 0` duplicate excess rows remaining

The same numbers explain the full historical shrink:

- `1076` historical snapshot
- minus `26` exact duplicate rows
- minus `127` held-out contamination rows
- minus `116` canonical duplicate-excess rows
- equals `807` final canonical package

## Source Provenance

The active package is sourced from reconciled lawyer-reviewed masters only.

### Active reconciled masters

| File | Rows | Notes |
| --- | ---: | --- |
| `data/review_sheets/phase2_first_batch_20260308/reconciled_20260308/batch1_first100_reconciled_master.jsonl` | 100 | active |
| `data/review_sheets/phase2_second_batch_20260309/reconciled_20260309/batch2_second100_reconciled_master.jsonl` | 100 | active |
| `data/review_sheets/phase2_third_batch_20260309/reconciled_20260309/batch3_remaining76_reconciled_master.jsonl` | 76 | active |
| `data/review_sheets/phase2_batch4_20260309/reconciled_20260309/batch4_reconciled_master.jsonl` | 100 | active |
| `data/review_sheets/phase2_batch5_20260309/reconciled_20260309/batch5_reconciled_master.jsonl` | 100 | active |
| `data/review_sheets/phase2_batch6_20260309/reconciled_20260309/batch6_reconciled_master.jsonl` | 100 | active |
| `data/review_sheets/phase2_batch7_20260309/reconciled_20260309/batch7_reconciled_master.jsonl` | 100 | active |
| `data/review_sheets/phase2_batch8_20260309/reconciled_20260309/batch8_reconciled_master.jsonl` | 100 | active |
| `data/review_sheets/phase2_batch9_20260309/reconciled_20260309/batch9_reconciled_master.jsonl` | 100 | active |
| `data/review_sheets/phase2_batch10_20260309/reconciled_20260309/batch10_reconciled_master.jsonl` | 100 | active |
| `data/review_sheets/phase2_batch11_20260309/reconciled_20260309/batch11_reconciled_master.jsonl` | 100 | active |

Total active reconciled-master rows: `1076`

### Explicitly excluded reconciled source

| File | Rows | Reason |
| --- | ---: | --- |
| `data/review_sheets/phase2_second_batch_20260309/reconciled_20260309/batch1_first100_reconciled_master.jsonl` | 100 | `include_in_training = 0`, historical mirror, `manual_escalation` |

### Explicitly excluded supplementary inputs

All supplementary SFT files were scanned and contributed `0` active rows in the dry-run:

- `data/finetune/sft/legal_qa.jsonl`
- `data/finetune/sft/petition_examples.jsonl`
- `data/finetune/sft/rag_corrected.jsonl`
- `data/finetune/sft/refusal_examples.jsonl`

## Category Breakdown

### Duplicate

Documented duplicate inventory:

- duplicate question groups: `24`
- duplicate excess rows: `116`
- `all_rows_unique_outputs`: `13`
- `mixed_repeat_and_variant_outputs`: `11`

Interpretation:

- there was no pure exact-answer-repeat cluster;
- cleanup required canonicalization, not blind row deletion;
- final canonicalization applied `24/24` clusters.

### Near-Duplicate

This bucket is not separately quantified in the source artefacts.

What exists instead is a cluster classification that distinguishes:

- `all_rows_unique_outputs`
- `mixed_repeat_and_variant_outputs`

The `11` mixed clusters are the closest evidence of near-duplicate / variant-heavy repetition, but there is no separate numeric near-duplicate counter in the current audit trail.

### Held-Out Leakage

Builder dry-run and readiness preflight both prove the held-out filter:

- builder removed `127` held-out contamination rows
- readiness preflight reported `807 train questions vs 22 held-out questions`
- exact overlap: `0`

### Out-Of-Scope

Excluded from active training:

- pending-review expansion packages
- synthetic-pending-review sources
- supplementary SFT files with no active rows
- historical mirror reconciled source with `include_in_training = 0`
- forbidden old dataset path `data/finetune/sft_training_v1.jsonl`

### Low-Quality / Malformed

This bucket is not separately counted in the current lineage artefacts.

What the builder does enforce:

- malformed JSON lines are skipped
- scaffolding rows are skipped
- rows with empty answers are skipped

Dry-run output did not report a non-zero malformed-row bucket, so there is no evidence-based count to assign here.

### Reviewer Rejection

This bucket is only partially evidenced.

The active audit trail shows:

- one reconciled mirror source explicitly marked `include_in_training = 0`
- the mirror source is labeled `manual_escalation`
- cluster review comments resolved `cluster-22` in favor of the canonical selection
- `cluster-11` was retained because the cited variant was sufficiently clear

There is no separate global numeric reviewer-rejection counter in the current artefacts.

### Merge / Canonicalization

Canonicalization is fully evidenced:

- canonicalization clusters applied: `24/24`
- cluster manifest: [`coordination/training-duplicate-final-canonicalization-2026-03-20.json`](/Users/btmacstudio/Projects/hukuk-ai/coordination/training-duplicate-final-canonicalization-2026-03-20.json)
- source packet: [`coordination/training-duplicate-review-packet-final-2026-03-20.md`](/Users/btmacstudio/Projects/hukuk-ai/coordination/training-duplicate-review-packet-final-2026-03-20.md)
- committed package reproduces byte-for-byte from the builder

## Train / Held-Out Separation Proof

Proof summary:

- train file exists and validates as SFT JSONL
- held-out file exists and validates as SFT JSONL
- exact overlap between train questions and held-out questions is `0`
- train size is `807`
- held-out size is `22`
- readiness gate reports `READY`

The builder also enforces the separation at generation time by filtering held-out questions before the final canonicalization stage.

## Evaluation Leakage Checklist

- `PASS` baseline evidence manifest exists and is SHA-verified
- `PASS` active workflow files no longer reference `data/finetune/sft_training_v1.jsonl`
- `PASS` held-out set is separate from the train set
- `PASS` canonical duplicate-excess threshold is `0`
- `PASS` canonicalization manifest is frozen and applied `24/24`
- `PASS` final train package is reproducible from the builder
- `PASS` preflight readiness returned `READY`
- `PASS` the evaluation family for promotion remains fixed to `faz1-50`

## Conclusion

The canonical train package lineage is auditable and reproducible. The `1076 -> 807` reduction is explained by exact duplicate removal, held-out contamination removal, and final duplicate canonicalization, with no unresolved leakage in the active train/held-out split.
