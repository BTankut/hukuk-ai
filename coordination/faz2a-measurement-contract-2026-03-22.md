# FAZ 2A Measurement Contract

**Date:** 2026-03-22  
**Scope:** freeze the eval family labels, source-of-record reports, trace contract, and exit bars for FAZ 2A

## Canonical Eval Families

The only canonical family labels for FAZ 2A are:

- `faz1-50`
- `v2-95`
- `v3-170`

Legacy labels such as `phase3-95` and `faz2-170` may exist in old scripts or reports, but they are not the canonical labels going forward.

## Source Of Record

Preserved baseline:

- `evaluation/reports/eval_baseline_faz1-50_matched_dgxnode2_base_thinkingoff_r2_20260322.json`
- `evaluation/reports/eval_baseline_v2-95_matched_dgxnode2_base_thinkingoff_r2_20260322.json`
- `evaluation/reports/eval_baseline_v3-170_matched_dgxnode2_base_thinkingoff_r2_20260322.json`

Promoted candidate snapshot used to open FAZ 2A:

- `evaluation/reports/eval_post_train_faz1-50_matched_dgx1_merged_post_promotion_cleanup_20260322.json`
- `evaluation/reports/eval_post_train_v2-95_matched_dgx1_merged_post_promotion_cleanup_20260322.json`
- `evaluation/reports/eval_post_train_v3-170_matched_dgx1_merged_post_promotion_cleanup_20260322.json`

## Runner Contract

- runner family: `eval_runner`
- report identity metadata must include:
  - `schema_version`
  - `runner`
  - `report_role`
  - `eval_family`
  - `model_ref`
  - `checkpoint_ref`
  - `git_commit`
  - `config_fingerprint`

## Trace Contract

Default live behavior remains unchanged.

Diagnostic runs may opt into trace capture with `include_trace=true`. When enabled, the response/report should persist:

- `query_signals`
  - `user_query`
  - `enriched_query`
  - `retrieval_query`
  - `law_filter`
  - `explicit_article_refs`
  - `applied_expansions`
- `retrieval`
  - `top_k_requested`
  - `top_k_effective`
  - `reranker_enabled`
  - `pre_rerank_chunks`
  - `post_rerank_chunks`
- `context_assembly`
  - `context_chunk_citations`
  - `assembled_context`
- `generation_outcome`
  - `decision_lane`
  - `blocked`
  - `guardrails_reasons`
  - `verification`

This contract exists so the next FAZ 2A reruns can distinguish retrieval miss, law/article parse miss, context contamination, and source-locking failure.

## Failure Freeze Contract

The first FAZ 2A failure freeze is report-derived, not trace-derived.

That means:

- answer-level failure labels are considered valid
- retrieval/context-stage attribution remains provisional until trace-backed reruns exist

## Focus Slices

Mandatory focus categories for FAZ 2A:

- `tmk_cross_law`
- `tbk_ceza_sarti`
- `tbk_kefalet`
- `tbk_vekaletname`
- `tbk_hizmet`

## Exit Bars

FAZ 2A should not claim success without family-level evidence.

Recommended exit bars:

- `faz1-50`
  - no meaningful regression against preserved baseline
- `v2-95`
  - clear improvement over preserved baseline
- `v3-170`
  - `correct_source >= 70%` or a clear and stable improvement over baseline
  - `hallucination <= 7%`
  - `error_count = 0`
  - visible drop in `wrong source despite retrieved evidence`
  - visible drop in `cross_law_confusion`

## Non-Goals

FAZ 2A does not reopen:

- production cutover
- general training-first iteration
- productization claims

Those only reopen after FAZ 2A re-qualification closes.
