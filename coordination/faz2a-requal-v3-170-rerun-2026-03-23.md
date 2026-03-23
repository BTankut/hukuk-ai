# FAZ 2A Re-Qualification — matched `v3-170` rerun

## Scope
- Objective: reopen family-level steering on the preserved hardest family only after both diagnostic focus slices (`tbk_critical`, `tmk_cross_law`) cleared their gates.
- Strategy:
  - keep the current Wave 15 code unchanged,
  - rerun preserved baseline and promoted candidate on the canonical `v3-170` family,
  - compare against the previous FAZ 1.5 source-of-record reports.

## Official matched reports
- Baseline:
  - `evaluation/reports/eval_baseline_v3-170_matched_dgxnode2_base_wave15_20260323.json`
- Candidate:
  - `evaluation/reports/eval_post_train_v3-170_matched_dgx1_merged_wave15_20260323.json`

## Result
- Baseline summary:
  - citation `96.5%`
  - correct source `84.4%`
  - hallucination `5.3%`
  - refusal `94.7%`
  - avg response `11657.8 ms`
- Candidate summary:
  - citation `96.5%`
  - correct source `83.8%`
  - hallucination `4.7%`
  - refusal `94.1%`
  - avg response `16337.7 ms`

## Delta vs previous source-of-record
- Baseline old -> new:
  - citation `84.7% -> 96.5%`
  - correct source `65.6% -> 84.4%`
  - hallucination `7.1% -> 5.3%`
  - refusal `91.2% -> 94.7%`
  - avg response `17687.6 ms -> 11657.8 ms`
- Candidate old -> new:
  - citation `89.1% -> 96.5%`
  - correct source `65.1% -> 83.8%`
  - hallucination `7.9% -> 4.7%`
  - refusal `91.5% -> 94.1%`
  - avg response `27119.7 ms -> 16337.7 ms`

## Category view
- Fully closed or near-closed:
  - `tbk_kefalet`
  - `tbk_hizmet`
  - `tbk_vekaletname`
  - `tbk_ceza_sarti`
  - `tmk_cross_law`
- Residual weak family:
  - `tbk_genel`

## Decision
- `v3-170` family-level gate is now open for both lanes.
- This is the first hard-family confirmation that FAZ 2A focus-slice repair generalized beyond the diagnostic subsets.
- FAZ 2A is not yet closed because `v2-95` and `faz1-50` matched reruns are still pending.

## Next active target
- Continue the matched re-qualification chain in order:
  - `v2-95`
  - `faz1-50`
- If both also clear, convert the rerun package into the next FAZ 2A steering/closure report.
