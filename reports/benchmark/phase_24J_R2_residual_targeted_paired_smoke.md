# Phase 24J-R2 Residual Targeted Paired Smoke

- generated_at_utc: `2026-05-03T17:11:57.749303+00:00`
- base_run: `reports/benchmark/runs/20260503T165451Z_phase24J_R2_base_residual_targeted`
- target_run: `reports/benchmark/runs/20260503T165451Z_phase24J_R2_target_residual_targeted`
- qid_count: `12`
- acceptance: `PASS`

| qid | base | target | base_span | target_span | target_rerank | target_evidence |
|---|---|---|---|---|---:|---:|
| KANUN-12 | FAIL 1.45 | FAIL 1.45 | `12879 m.15/f.0` | `12879 m.15/f.0` | 12 | 12 |
| KKY-03 | FAIL 1.45 | FAIL 1.45 | `12879 m.4/f.0` | `12879 m.4/f.0` | 12 | 12 |
| TUZUK-04 | FAIL 6.43 | FAIL 4.63 | `859727 m.4/f.0` | `RADYASYON_GUVENLIGI_TUZUGU m.7/f.0` | 18 | 18 |
| YON-04 | FAIL 3.25 | FAIL 3.25 | `12536 m.23/f.0` | `12536 m.23/f.0` | 12 | 12 |
| MULGA-01 | PASS 8.37 | PASS 8.37 | `YOK_DISIPLIN_2012 m.22/f.0` | `YOK_DISIPLIN_2012 m.22/f.0` | 22 | 22 |
| MULGA-05 | PASS 7.10 | PASS 7.10 | `6570 m.GEC1/f.0` | `6570 m.GEC1/f.0` | 18 | 18 |
| TEB-04 | FAIL 0.00 | FAIL 0.00 | `19631 m.0/f.0` | `19631 m.0/f.0` | 6 | 6 |
| TEB-06 | PASS 8.90 | PASS 8.90 | `23093 m.13/f.0` | `23093 m.13/f.0` | 10 | 10 |
| CBG-01 | PASS 8.65 | PASS 8.65 | `2024/7 m.0/f.0` | `2024/7 m.0/f.0` | 1 | 1 |
| CBKAR-08 | PASS 9.25 | PASS 9.25 | `9903 geçici m.1/f.0` | `9903 geçici m.1/f.0` | 2 | 2 |
| UY-01 | PASS 7.82 | PASS 7.82 | `12420 m.4/f.0` | `12420 m.4/f.0` | 10 | 10 |
| YON-05 | PASS 9.55 | PASS 9.55 | `23722 m.5/f.0` | `23722 m.5/f.0` | 8 | 8 |

## Gate Summary

- target_contract_valid_all: `True`
- target_unsupported_confident_answer_zero: `True`
- target_source_key_v2_collision_zero: `True`
- target_binding_collision_zero: `True`
- target_rerank_and_evidence_non_empty: `True`
- no_critical_regression_vs_base: `True`
- affected_residual_improved_count: `0`
- affected_residual_worse_count: `1`

## Affected Residual Delta

| qid | base_score | target_score | delta | note |
|---|---:|---:|---:|---|
| KANUN-12 | 1.45 | 1.45 | 0.00 | unchanged |
| KKY-03 | 1.45 | 1.45 | 0.00 | unchanged |
| TUZUK-04 | 6.43 | 4.63 | -1.80 | worse |
| YON-04 | 3.25 | 3.25 | 0.00 | unchanged |

No affected residual row improved. `TUZUK-04` changed source/span and scored lower; the others stayed unchanged. This satisfies the documentation requirement but does not justify opening full shadow benchmark.
