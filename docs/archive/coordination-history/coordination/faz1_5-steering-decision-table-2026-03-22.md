# FAZ 1.5 Steering Decision Table

**Date:** 2026-03-22  
**Basis:** `docs/FAZ1_5-PLANLAMA-2026-03-22.md` + current coordination artefacts

## 1) Decision Options

| Option | Decision meaning | Gate basis | Required evidence | Status |
| --- | --- | --- | --- | --- |
| `GO` | Production cutover | Gates `0-4` closed | Full-family matched eval, release-readiness closure, successful rehearsal, frozen decision package | rejected |
| `NARROW GO` | Dar kapsam pilot cutover | Gates `0-4` closed, but only pilot scope is safe | Matched eval closure plus scope-limited topology proof and rollback proof | rejected |
| `NO-GO - Stabilization` | Stabilization wave first | Gate `2` or `3` blocks release | Full-family results show fixable model/ops instability and release controls are not yet closed | secondary |
| `NO-GO - Retrieval/Coverage` | Retrieval/coverage phase first | Gate `2` shows coverage gap / retrieval miss dominates | Taxonomy shows retrieval miss, missing coverage, or article-assembly failure is the main blocker | selected |
| `NO-GO - Productization` | DGX-native productization becomes a separate phase | Gate `3` or topology contract blocks cutover | Pilot topology works but customer-appliance/productization evidence is absent | deferred |

## 2) Required Evidence Checklist

| Item | Source-of-record placeholder | Status |
| --- | --- | --- |
| Eval freeze for `faz1-50`, `v2-95`, `v3-170` | [faz1_5-eval-freeze-2026-03-22.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz1_5-eval-freeze-2026-03-22.md) | closed |
| Full-family matched baseline reports | [eval_baseline_faz1-50_matched_dgxnode2_base_thinkingoff_r2_20260322.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_baseline_faz1-50_matched_dgxnode2_base_thinkingoff_r2_20260322.json), [eval_baseline_v2-95_matched_dgxnode2_base_thinkingoff_r2_20260322.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_baseline_v2-95_matched_dgxnode2_base_thinkingoff_r2_20260322.json), [eval_baseline_v3-170_matched_dgxnode2_base_thinkingoff_r2_20260322.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_baseline_v3-170_matched_dgxnode2_base_thinkingoff_r2_20260322.json) | closed |
| Full-family matched candidate reports | [eval_post_train_faz1-50_matched_dgx1_merged_post_promotion_cleanup_20260322.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_post_train_faz1-50_matched_dgx1_merged_post_promotion_cleanup_20260322.json), [eval_post_train_v2-95_matched_dgx1_merged_post_promotion_cleanup_20260322.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_post_train_v2-95_matched_dgx1_merged_post_promotion_cleanup_20260322.json), [eval_post_train_v3-170_matched_dgx1_merged_post_promotion_cleanup_20260322.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_post_train_v3-170_matched_dgx1_merged_post_promotion_cleanup_20260322.json) | closed |
| Category / error taxonomy | [faz1_5-category-breakdown-2026-03-22.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz1_5-category-breakdown-2026-03-22.md) | closed |
| Train lineage audit (`1076 -> 807`) | [faz1_5-train-lineage-audit-2026-03-22.md](/Users/btmacstudio/Projects/hukuk-ai/training/audits/faz1_5-train-lineage-audit-2026-03-22.md) | closed |
| Production readiness matrix | [faz1_5-production-readiness-matrix-2026-03-22.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz1_5-production-readiness-matrix-2026-03-22.md) | partial |
| Cutover rehearsal + rollback proof | [faz1_5-cutover-rehearsal-2026-03-22.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz1_5-cutover-rehearsal-2026-03-22.md) | closed |
| Scope contract | [faz1_5-scope-contract-2026-03-22.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz1_5-scope-contract-2026-03-22.md) | closed |
| Final decision package | [FAZ1_5-POSTTRAIN-STABILIZATION-AND-CUTOVER-READINESS-RAPORU.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ1_5-POSTTRAIN-STABILIZATION-AND-CUTOVER-READINESS-RAPORU.md) | closed |

## 3) Official Decision

Official decision: **`NO-GO - Retrieval/Coverage first.`** Promoted `dgx1` merged aday, `v3-170` zor sette preserved baseline’dan anlamlı biçimde üstün değildir; baskın hata kümesi `wrong source despite retrieved evidence` ile `cross-law confusion` olduğundan cutover açılmayacaktır.
