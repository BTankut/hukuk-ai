# Phase 2 P1 — Raw Candidate Extraction Report

## Status
Raw extraction completed. These files are **NOT lawyer-approved** and are only for pending review.

## Split Method (Reproducible)
- Method: `sha256(normalized_question) % 10`
- Held-out buckets: `[0]`
- Split unit: normalized question text (same question always goes to same split).

## Counts
- Raw candidates (pre-dedupe): **310**
- Exact QA duplicates removed: **6**
- Total candidates (post-dedupe): **304**
- Train pending-review: **276**
- Held-out pending-review: **28**

## Source files
- `evaluation/reports/eval_live_20260308_042436.json` → 20 candidate(s)
- `evaluation/reports/eval_live_20260308_045101.json` → 20 candidate(s)
- `evaluation/reports/eval_live_20260308_080601.json` → 50 candidate(s)
- `evaluation/reports/eval_live_20260308_131021.json` → 50 candidate(s)
- `evaluation/reports/eval_live_20260308_edgecase_recovery_final.json` → 44 candidate(s)
- `evaluation/reports/eval_live_20260308_reindex.json` → 20 candidate(s)
- `evaluation/reports/eval_live_reranker_recovery_baseline_20260308.json` → 50 candidate(s)
- `evaluation/reports/eval_reranker_disabled_8010_20260308.json` → 50 candidate(s)

## Outputs
- `data/finetune/raw/pending_review/phase1_eval_reports_20260308/sft_train_pending_review.jsonl`
- `data/finetune/raw/pending_review/phase1_eval_reports_20260308/sft_heldout_pending_review.jsonl`
- `data/finetune/raw/pending_review/phase1_eval_reports_20260308/sft_all_pending_review.jsonl`
- `data/finetune/raw/pending_review/phase1_eval_reports_20260308/candidate_metadata.jsonl`
- `data/finetune/raw/pending_review/phase1_eval_reports_20260308/extraction_manifest.json`

## Reminder
No record in this output is lawyer-reviewed or approved.
