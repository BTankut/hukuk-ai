# FAZ 2A - Retrieval/Coverage Re-Qualification Report

**Date:** 2026-03-23  
**Reference:** `docs/FAZ2A-RETRIEVAL-COVERAGE-REQUALIFICATION-YOL-HARITASI-2026-03-22.md`  
**Status:** Final steering decision report

## Executive Summary

FAZ 2A is now closed as a steering phase.

The final steering outcome is:

- `Re-Qualify Pass -> Cutover Readiness Closure`

Reason:

- the dominant FAZ 1.5 blocker classes, `wrong source despite retrieved evidence` and `cross-law confusion`, were reduced enough to reopen family-level steering
- the full matched family reruns for `faz1-50`, `v2-95`, and `v3-170` now all close with `error_count = 0`
- the promoted `dgx1` merged candidate no longer fails the hardest family gate; `v3-170` now closes at citation `96.5%`, correct source `83.8%`, hallucination `4.7%`, refusal `94.1%`
- FAZ 2A therefore succeeded at re-qualification, but it does not itself approve production cutover; it only reopens the next official phase

## What Closed In FAZ 2A

- failure freeze and measurement contract closed
- trace instrumentation closed
- query parsing and retrieval precision waves closed
- source-locking / evidence assembly wave closed
- targeted TBK/TMK coverage closure waves closed
- full-family matched reruns closed for baseline and candidate
- refreshed category / error taxonomy published
- a new steering decision can now be stated in one sentence

## Full-Family Decision Table

| Family | Baseline | Candidate | Steering Read |
| --- | --- | --- | --- |
| `faz1-50` | citation `88.0%`, source `76.7%`, hal `10.0%`, refusal `100.0%`, error `0` | citation `88.0%`, source `77.7%`, hal `10.0%`, refusal `100.0%`, error `0` | no meaningful regression; gate open |
| `v2-95` | citation `94.7%`, source `82.1%`, hal `9.5%`, refusal `93.7%`, error `0` | citation `94.7%`, source `82.8%`, hal `8.4%`, refusal `92.6%`, error `0` | family gate open; candidate improves source/hallucination |
| `v3-170` | citation `96.5%`, source `84.4%`, hal `5.3%`, refusal `94.7%`, error `0` | citation `96.5%`, source `83.8%`, hal `4.7%`, refusal `94.1%`, error `0` | hardest-family gate open; candidate no longer blocks steering |

## Focus-Slice Read

The focus slices that defined FAZ 2A are no longer the dominant blocker:

- `tmk_cross_law`: candidate `src 81.4%`, `hal 0.0%`
- `tbk_ceza_sarti`: candidate `src 100.0%`, `hal 0.0%` on `v3-170`
- `tbk_kefalet`: candidate `src 100.0%`, `hal 0.0%` on `v3-170`
- `tbk_vekaletname`: candidate `src 100.0%`, `hal 0.0%` on `v3-170`
- `tbk_hizmet`: candidate `src 100.0%`, `hal 0.0%` on `v3-170`

Interpretation:

- the TBK critical tails that drove the early FAZ 2A waves are now closed on the hardest family
- `tmk_cross_law` moved from a steering blocker to a passing family slice
- remaining quality debt is now narrower and no longer justifies another retrieval-first phase as the primary next move

## Root-Cause Delta

At FAZ 2A start, the opening candidate `v3-170` taxonomy was:

- `wrong source despite retrieved evidence`: `56`
- `cross-law confusion`: `20`
- `over-refusal`: `9`
- `serving_error`: `5`

The closing FAZ 2A candidate `v3-170` taxonomy is now:

- `wrong source despite retrieved evidence`: `34`
- `cross-law confusion`: `9`
- `unsupported question answered`: `6`
- `over-refusal`: `4`
- `serving_error`: `0`

Interpretation:

- the main blocker class dropped materially
- `cross-law confusion` was more than halved on the hardest family
- serving instability is no longer contaminating the decision surface
- the remaining issue set is real, but it is no longer a credible reason to keep the project in FAZ 2A

## Gate Read

Against the FAZ 2A measurement contract:

- `faz1-50`: no meaningful regression against preserved baseline -> closed
- `v2-95`: clear family-level support with candidate source/hallucination improvement -> closed
- `v3-170`:
  - `correct_source >= 70%` -> closed at `83.8%`
  - `hallucination <= 7%` -> closed at `4.7%`
  - `error_count = 0` -> closed
  - visible drop in `wrong source despite retrieved evidence` -> closed
  - visible drop in `cross-law confusion` -> closed

Therefore Gate C is closed as `pass`.

## What This Decision Means

This decision does mean:

- retrieval/source-precision re-qualification succeeded
- the project can leave FAZ 2A
- the next official phase should move to cutover-readiness closure

This decision does not mean:

- production cutover is approved
- release-control gaps are irrelevant
- no further quality cleanup is needed

Production/cutover claims remain a separate next-phase decision.

## Official Steering Decision

Official decision:

> `Re-Qualify Pass -> Cutover Readiness Closure.` FAZ 2A retrieval/source-precision work reduced the dominant blocker class enough to reopen steering; the next official phase should move from retrieval-first repair to cutover-readiness closure.

## Next Official Work

The next official phase should target:

1. cutover-readiness closure on the re-qualified promoted lane
2. must-close release controls and production-readiness classification
3. narrow-pilot scope, rollout gate, rollback proof, and monitoring package

Secondary follow-up, but not the primary next phase:

1. residual `tbk_genel` / `hal_prone` cleanup
2. refusal and unsupported-answer tails
3. latency optimization where it does not change family-level quality

## Evidence Package Reference

- [faz2a-implementation-plan-2026-03-22.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2a-implementation-plan-2026-03-22.md)
- [faz2a-measurement-contract-2026-03-22.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2a-measurement-contract-2026-03-22.md)
- [faz2a-failure-freeze-2026-03-22.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz2a-failure-freeze-2026-03-22.md)
- [faz2a-wave15-tmk-family-home-rerun-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2a-wave15-tmk-family-home-rerun-2026-03-23.md)
- [faz2a-requal-v3-170-rerun-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2a-requal-v3-170-rerun-2026-03-23.md)
- [faz2a-requal-v2-95-rerun-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2a-requal-v2-95-rerun-2026-03-23.md)
- [faz2a-requal-faz1-50-rerun-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2a-requal-faz1-50-rerun-2026-03-23.md)
- [faz2a-category-breakdown-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz2a-category-breakdown-2026-03-23.md)
- [faz2a-closure-matrix-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2a-closure-matrix-2026-03-23.md)
- [faz2a-steering-decision-table-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2a-steering-decision-table-2026-03-23.md)
- [eval_baseline_faz1-50_matched_dgxnode2_base_wave15_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_baseline_faz1-50_matched_dgxnode2_base_wave15_20260323.json)
- [eval_post_train_faz1-50_matched_dgx1_merged_wave15_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_post_train_faz1-50_matched_dgx1_merged_wave15_20260323.json)
- [eval_baseline_v2-95_matched_dgxnode2_base_wave15_r2_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_baseline_v2-95_matched_dgxnode2_base_wave15_r2_20260323.json)
- [eval_post_train_v2-95_matched_dgx1_merged_wave15_r2_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_post_train_v2-95_matched_dgx1_merged_wave15_r2_20260323.json)
- [eval_baseline_v3-170_matched_dgxnode2_base_wave15_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_baseline_v3-170_matched_dgxnode2_base_wave15_20260323.json)
- [eval_post_train_v3-170_matched_dgx1_merged_wave15_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_post_train_v3-170_matched_dgx1_merged_wave15_20260323.json)

## Conclusion

FAZ 2A succeeded as a retrieval/source-precision re-qualification phase because it produced a defensible answer. That answer is not direct cutover approval. The correct next move is to leave FAZ 2A and open a cutover-readiness closure phase on the re-qualified promoted lane.
