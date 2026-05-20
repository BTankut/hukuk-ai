# FAZ 2A Steering Decision Table

**Date:** 2026-03-23  
**Basis:** `docs/FAZ2A-RETRIEVAL-COVERAGE-REQUALIFICATION-YOL-HARITASI-2026-03-22.md` + current coordination artefacts

## 1) Decision Options

| Option | Decision meaning | Gate basis | Required evidence | Status |
| --- | --- | --- | --- | --- |
| `Re-Qualify Pass -> Cutover Readiness Closure` | Retrieval/source-precision phase succeeded; next official phase may reopen cutover-readiness discussion | Gates `A-C` closed, family reruns complete, dominant retrieval blockers reduced | Full-family matched reruns, refreshed category breakdown, zero-error family reports | selected |
| `Partial Pass -> Coverage extension wave` | Some focus slices improved but family-level evidence is still mixed | Gate `C` unresolved or family reruns mixed | Focus-slice wins but incomplete family support | rejected |
| `Fail -> Targeted behavior fine-tune after retrieval closure` | Retrieval/source-locking is no longer the blocker, but model behavior still prevents requalification | Gate `C` fail with retrieval largely closed | Full-family evidence showing remaining blocker is model behavior | rejected |

## 2) Required Evidence Checklist

| Item | Source-of-record placeholder | Status |
| --- | --- | --- |
| Failure freeze and measurement contract | [faz2a-failure-freeze-2026-03-22.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz2a-failure-freeze-2026-03-22.md), [faz2a-measurement-contract-2026-03-22.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2a-measurement-contract-2026-03-22.md) | closed |
| Focus-slice repair evidence | wave notes under [coordination](/Users/btmacstudio/Projects/hukuk-ai/coordination), especially [faz2a-wave15-tmk-family-home-rerun-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2a-wave15-tmk-family-home-rerun-2026-03-23.md) | closed |
| Full-family matched baseline reports | [eval_baseline_faz1-50_matched_dgxnode2_base_wave15_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_baseline_faz1-50_matched_dgxnode2_base_wave15_20260323.json), [eval_baseline_v2-95_matched_dgxnode2_base_wave15_r2_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_baseline_v2-95_matched_dgxnode2_base_wave15_r2_20260323.json), [eval_baseline_v3-170_matched_dgxnode2_base_wave15_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_baseline_v3-170_matched_dgxnode2_base_wave15_20260323.json) | closed |
| Full-family matched candidate reports | [eval_post_train_faz1-50_matched_dgx1_merged_wave15_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_post_train_faz1-50_matched_dgx1_merged_wave15_20260323.json), [eval_post_train_v2-95_matched_dgx1_merged_wave15_r2_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_post_train_v2-95_matched_dgx1_merged_wave15_r2_20260323.json), [eval_post_train_v3-170_matched_dgx1_merged_wave15_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_post_train_v3-170_matched_dgx1_merged_wave15_20260323.json) | closed |
| Refreshed category/error taxonomy | [faz2a-category-breakdown-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz2a-category-breakdown-2026-03-23.md), [faz2a-category-breakdown-2026-03-23.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz2a-category-breakdown-2026-03-23.json) | closed |
| Final decision package | [FAZ2A-RETRIEVAL-COVERAGE-REQUALIFICATION-RAPORU-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ2A-RETRIEVAL-COVERAGE-REQUALIFICATION-RAPORU-2026-03-23.md) | closed |

## 3) Official Decision

Official decision: **`Re-Qualify Pass -> Cutover Readiness Closure.`** FAZ 2A retrieval/source-precision work closed the dominant blocker class enough to reopen steering; the next official phase should move to cutover-readiness closure rather than more retrieval-first repair.
