# FAZ 1.5 - Post-Train Stabilization and Cutover Readiness Report

**Date:** 2026-03-22  
**Reference:** `docs/FAZ1_5-PLANLAMA-2026-03-22.md`  
**Status:** Final steering decision report

## Executive Summary

FAZ 1.5 is now closed as a decision gate.

The final steering outcome is:

- `NO-GO - Retrieval/Coverage first`

Reason:

- the promoted `dgx1` merged candidate does not materially outperform the preserved `dgxnode2` baseline on the decision-critical `v3-170` family
- both lanes fail the formal `correct_source` acceptance line on `v3-170`
- the dominant failure pattern is not a narrow training regression but a broader `wrong source despite retrieved evidence` plus `cross-law confusion` problem

Operationally, FAZ 1.5 did prove that the pilot topology can be cut over and rolled back safely. That proof is real, but it is not enough to approve either `GO` or `NARROW GO` because Gate 2 fails before Gate 3 can justify rollout.

## What Closed In FAZ 1.5

- eval freeze closed
- train lineage audit closed
- scope contract closed
- full-family matched eval closed for baseline and candidate
- category / error taxonomy published
- cutover + rollback rehearsal succeeded
- steering decision can now be stated in one sentence

## Full-Family Decision Table

| Family | Baseline | Candidate | Steering Read |
| --- | --- | --- | --- |
| `faz1-50` | citation `88.0%`, source `86.7%`, hal `0.0%`, refusal `100.0%` | citation `86.0%`, source `84.7%`, hal `0.0%`, refusal `100.0%` | candidate is slightly weaker but still within a safe narrow family band |
| `v2-95` | citation `84.2%`, source `74.9%`, hal `5.3%`, refusal `87.4%` | citation `86.3%`, source `72.8%`, hal `8.4%`, refusal `92.6%` | candidate beats baseline on citation/refusal, but misses the stricter FAZ 1.5 minimum regression bar |
| `v3-170` | citation `84.7%`, source `65.6%`, hal `7.1%`, refusal `91.2%`, error `0` | citation `89.1%`, source `65.1%`, hal `7.9%`, refusal `91.5%`, error `5` | candidate is not meaningfully better on the hardest family and does not justify cutover |

## Root-Cause Read

The full-family category breakdown shows the main blocker is not a simple serving failure and not a single isolated slice.

On `v3-170`, the candidate taxonomy is:

- `wrong source despite retrieved evidence`: `56`
- `cross-law confusion`: `20`
- `over-refusal`: `9`
- `infrastructure / timeout / serving error`: `5`
- `retrieval miss`: `5`
- `unsupported question answered`: `5`

The most decision-relevant category deltas are:

- `tmk_cross_law`: baseline `src 32.5% / hal 10.0%`, candidate `src 38.3% / hal 16.7%`
- `tbk_ceza_sarti`: baseline `src 69.7%`, candidate `src 60.0%`
- `tbk_kefalet`: baseline `src 65.4%`, candidate `src 61.5%`
- `tbk_vekaletname`: baseline `src 67.6%`, candidate `src 62.7%`
- `tbk_hizmet`: baseline `src 64.0%`, candidate `src 58.8%`

Interpretation:

- the hardest-family failure is dominated by source precision and coverage assembly problems
- the candidate slightly improves some cross-law source selection, but not enough to change the steering outcome
- the candidate also gives back performance in several TBK-heavy slices and carries `5` serving errors

## Release Readiness Read

FAZ 1.5 also closes the operational question more clearly than before.

- the pilot topology is now proven reversible
- cutover + rollback rehearsal passed
- baseline and candidate lanes both returned cited smoke success before and after rollback

But release readiness is still not closed for production use:

- auth is missing
- immutable audit logging is missing
- Redis-backed session persistence is missing
- tokenizer-backed accounting is missing
- observability and alerting are partial/missing
- backup / restore proof is missing

These release-control gaps remain real, but they are not the primary steering blocker. The primary blocker is still Gate 2 quality on the hardest family.

## Official Steering Decision

Official decision:

> `NO-GO - Retrieval/Coverage first.` Promoted `dgx1` merged aday, `v3-170` zor sette preserved baseline’dan anlamlı biçimde üstün değildir; iki lane de `correct_source` barını kaçırdığı ve baskın hata kümesi `wrong source despite retrieved evidence` ile `cross-law confusion` olduğu için cutover açılmayacaktır.

## What This Decision Rejects

- `GO` rejected: full-family quality is not strong enough
- `NARROW GO` rejected: `v2-95` and `v3-170` do not support a defensible pilot cutover claim
- `NO-GO - Stabilization first` not selected as the primary lane: there are serving/timeouts issues, but they are secondary to the broader retrieval/source-precision failure pattern
- `NO-GO - Productization first` not selected as the primary lane: customer-appliance packaging remains a separate future question, but model qualification already fails earlier

## Next Official Work

The next official investment lane should target:

1. retrieval / source-precision improvement on `tmk_cross_law`
2. source selection quality on `tbk_kefalet`, `tbk_vekaletname`, `tbk_hizmet`, `tbk_ceza_sarti`
3. reduction of `wrong source despite retrieved evidence` before any new cutover claim

Secondary follow-up, but not the first steering lane:

1. serving timeout cleanup on the promoted lane
2. remaining release-control closure
3. customer-appliance / productization separation

## Evidence Package Reference

- [faz1_5-eval-freeze-2026-03-22.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz1_5-eval-freeze-2026-03-22.md)
- [faz1_5-baseline-rerun-reset-2026-03-22.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz1_5-baseline-rerun-reset-2026-03-22.md)
- [faz1_5-production-readiness-matrix-2026-03-22.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz1_5-production-readiness-matrix-2026-03-22.md)
- [faz1_5-cutover-rehearsal-2026-03-22.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz1_5-cutover-rehearsal-2026-03-22.md)
- [faz1_5-closure-matrix-2026-03-22.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz1_5-closure-matrix-2026-03-22.md)
- [faz1_5-steering-decision-table-2026-03-22.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz1_5-steering-decision-table-2026-03-22.md)
- [faz1_5-scope-contract-2026-03-22.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz1_5-scope-contract-2026-03-22.md)
- [faz1_5-train-lineage-audit-2026-03-22.md](/Users/btmacstudio/Projects/hukuk-ai/training/audits/faz1_5-train-lineage-audit-2026-03-22.md)
- [faz1_5-category-breakdown-2026-03-22.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz1_5-category-breakdown-2026-03-22.md)
- [eval_baseline_faz1-50_matched_dgxnode2_base_thinkingoff_r2_20260322.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_baseline_faz1-50_matched_dgxnode2_base_thinkingoff_r2_20260322.json)
- [eval_baseline_v2-95_matched_dgxnode2_base_thinkingoff_r2_20260322.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_baseline_v2-95_matched_dgxnode2_base_thinkingoff_r2_20260322.json)
- [eval_baseline_v3-170_matched_dgxnode2_base_thinkingoff_r2_20260322.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_baseline_v3-170_matched_dgxnode2_base_thinkingoff_r2_20260322.json)
- [eval_post_train_faz1-50_matched_dgx1_merged_post_promotion_cleanup_20260322.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_post_train_faz1-50_matched_dgx1_merged_post_promotion_cleanup_20260322.json)
- [eval_post_train_v2-95_matched_dgx1_merged_post_promotion_cleanup_20260322.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_post_train_v2-95_matched_dgx1_merged_post_promotion_cleanup_20260322.json)
- [eval_post_train_v3-170_matched_dgx1_merged_post_promotion_cleanup_20260322.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_post_train_v3-170_matched_dgx1_merged_post_promotion_cleanup_20260322.json)

## Conclusion

FAZ 1.5 succeeded as a decision phase because it produced a defensible answer. That answer is not cutover approval. The correct next move is a retrieval/coverage wave, not production rollout.
