# Phase 2 Candidate Expansion Report (2026-03-09)

## Status
Yeni aday paket üretimi tamamlandı. Bu paketteki tüm kayıtlar **pending-review** durumundadır.

## Source Inventory (Repo Artifacts)
- Reconciled correction pairs: `data/review_sheets/phase2_first_batch_20260308/reconciled_20260308/batch1_first100_reconciled_master.jsonl`
- Mevzuat text fixture (TBK full HTML): `api-gateway/src/data_pipeline/fixtures/tbk_detail.html`

## Counts
- Raw candidates (pre-dedupe): **2651**
- Dedupe removed (existing pool): **0**
- Dedupe removed (within new): **8**
- Total new candidates: **2643**
- Train pending-review: **2383**
- Heldout pending-review: **260**
- Source-grounded count: **2643**
- Synthetic-pending-review count: **2604**
- Non-synthetic pending-review count: **39**

### By Origin
- `source_grounded_correction_pair_pending_revalidation`: **39**
- `synthetic_pending_review_source_grounded_tbk_fixture`: **2604**

## Blocker Impact Estimate
- Approved baseline: **100**
- Target: **1000**
- Gap before: **900**
- New pending candidates added: **2643**
- Potential gap after (if all approved later): **0**

## Schema Validation
- Validation file: `data/finetune/raw/pending_review/phase2_candidate_expansion_20260309/schema_validation.json`
- All passed: **True**

## Outputs
- `data/finetune/raw/pending_review/phase2_candidate_expansion_20260309/sft_train_pending_review.jsonl`
- `data/finetune/raw/pending_review/phase2_candidate_expansion_20260309/sft_heldout_pending_review.jsonl`
- `data/finetune/raw/pending_review/phase2_candidate_expansion_20260309/sft_all_pending_review.jsonl`
- `data/finetune/raw/pending_review/phase2_candidate_expansion_20260309/candidate_metadata.jsonl`
- `data/finetune/raw/pending_review/phase2_candidate_expansion_20260309/extraction_manifest.json`
- `data/finetune/raw/pending_review/phase2_candidate_expansion_20260309/schema_validation.json`

## Reminder
No record in this package is lawyer-approved by default.
