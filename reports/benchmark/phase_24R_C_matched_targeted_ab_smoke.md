# Phase 24R-C Matched Targeted A/B Smoke

## Outcome

```text
cby06_improves_or_stays_improved = true
critical_guards_no_regression = true
contract_valid_all = true
unsupported_confident_answer_zero = true
answer_contract_invalid_zero = true
source_key_v2_collision_zero = true
binding_collision_zero = true
tuzuk04_not_active_current_law_claim = true
passed = true
```

## Summary

```text
base_run = reports/benchmark/runs/phase_24R_C_base_targeted_20260504T2020Z
cby_run = reports/benchmark/runs/phase_24R_C_cby_targeted_20260504T2020Z
base_raw_score_proxy = 83.63
cby_raw_score_proxy = 85.41
base_pass_proxy = 8
cby_pass_proxy = 9
base_unsupported_confident_answer_count = 0
cby_unsupported_confident_answer_count = 0
base_answer_contract_invalid_count = 0
cby_answer_contract_invalid_count = 0
```

## Row Delta

| qid | base | cby | delta | base_pass | cby_pass | note |
|---|---:|---:|---:|---|---|---|
| CBY-06 | 6.80 | 8.58 | 1.78 | FAIL | PASS | target improved on CBY collection |
| CBY-05 | 8.00 | 8.00 | 0.00 | PASS | PASS | same-family neighbor unchanged |
| MULGA-01 | 8.37 | 8.37 | 0.00 | PASS | PASS | unchanged |
| MULGA-05 | 4.00 | 4.00 | 0.00 | FAIL | FAIL | unchanged |
| TEB-06 | 8.90 | 8.90 | 0.00 | PASS | PASS | unchanged |
| KANUN-12 | 8.99 | 8.99 | 0.00 | PASS | PASS | unchanged |
| YON-04 | 8.22 | 8.22 | 0.00 | PASS | PASS | unchanged |
| TUZUK-04 | 4.63 | 4.63 | 0.00 | FAIL | FAIL | repealed/MULGA claim preserved; no active-current-law claim |
| CBG-01 | 8.65 | 8.65 | 0.00 | PASS | PASS | unchanged |
| CBKAR-08 | 9.25 | 9.25 | 0.00 | PASS | PASS | unchanged |
| UY-01 | 7.82 | 7.82 | 0.00 | PASS | PASS | unchanged |

## Decision

Targeted A/B smoke passed. Phase24R-D matched full A/B benchmark may proceed under the existing no-trace/summary-only artifact policy.
