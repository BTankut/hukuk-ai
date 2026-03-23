# FAZ 2A Re-Qualification — matched `faz1-50` rerun

## Scope
- Objective: close the final family-level rerun required by the FAZ 2A measurement contract after `v3-170` and `v2-95` reopened the steering gate.
- Strategy:
  - reuse the preserved baseline lane on `8055`,
  - reuse the promoted candidate lane on `8056`,
  - keep the Wave 15 retrieval/source-locking code unchanged,
  - accept only the clean zero-error reruns as source-of-record.

## Official matched reports
- Baseline:
  - `evaluation/reports/eval_baseline_faz1-50_matched_dgxnode2_base_wave15_20260323.json`
- Candidate:
  - `evaluation/reports/eval_post_train_faz1-50_matched_dgx1_merged_wave15_20260323.json`

## Result
- Baseline summary:
  - citation `88.0%`
  - correct source `76.7%`
  - hallucination `10.0%`
  - refusal `100.0%`
  - avg response `9374.8 ms`
  - error count `0`
- Candidate summary:
  - citation `88.0%`
  - correct source `77.7%`
  - hallucination `10.0%`
  - refusal `100.0%`
  - avg response `10264.2 ms`
  - error count `0`

## Decision
- `faz1-50` family-level gate is open for both lanes.
- Candidate shows no meaningful regression against preserved baseline on the acceptance family.
- This closes the last mandatory family rerun in the FAZ 2A measurement contract.

## Next active target
- Convert the completed rerun package into the FAZ 2A steering/closure report.
- Use the matched `faz1-50`, `v2-95`, `v3-170` trio plus the refreshed category breakdown as the only decision surface.
