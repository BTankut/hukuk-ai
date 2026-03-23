# FAZ 2A Re-Qualification — matched `v2-95` rerun

## Scope
- Objective: confirm that the Wave 15 retrieval/source-precision repairs generalize beyond `v3-170` and hold on the mid-sized preserved family.
- Strategy:
  - keep the current Wave 15 code unchanged,
  - invalidate the earlier detached `v2-95` attempts because they did not close reliably,
  - accept only the monitored `r2` reruns as source-of-record.

## Official matched reports
- Baseline:
  - `evaluation/reports/eval_baseline_v2-95_matched_dgxnode2_base_wave15_r2_20260323.json`
- Candidate:
  - `evaluation/reports/eval_post_train_v2-95_matched_dgx1_merged_wave15_r2_20260323.json`

## Invalidated detached attempts
- Baseline detached draft:
  - `evaluation/reports/eval_baseline_v2-95_matched_dgxnode2_base_wave15_20260323.json`
- Candidate detached draft:
  - `evaluation/reports/eval_post_train_v2-95_matched_dgx1_merged_wave15_20260323.json`
- Reason:
  - both detached runs were dropped in favor of monitored `r2` executions after they failed to provide a trustworthy close-out signal.

## Result
- Baseline summary:
  - citation `94.7%`
  - correct source `82.1%`
  - hallucination `9.5%`
  - refusal `93.7%`
  - avg response `14752.2 ms`
  - error count `0`
- Candidate summary:
  - citation `94.7%`
  - correct source `82.8%`
  - hallucination `8.4%`
  - refusal `92.6%`
  - avg response `22825.2 ms`
  - error count `0`

## Decision
- `v2-95` family-level gate is now open for both lanes.
- Candidate preserves baseline on citation and improves on correct source and hallucination, with a small refusal deficit that remains above the FAZ gate floor.
- FAZ 2A is still not closed because the last matched family rerun, `faz1-50`, is still pending.

## Next active target
- Run the official matched `faz1-50` reruns on the same preserved baseline and promoted candidate lanes.
- If `faz1-50` also clears, convert the rerun package into the FAZ 2A steering/closure report.
