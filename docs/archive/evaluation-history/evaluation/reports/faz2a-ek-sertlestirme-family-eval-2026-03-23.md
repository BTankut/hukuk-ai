# FAZ 2A Ek Sertleştirme — Family Eval

| set | n | error | citation | correct_source | hallucination | refusal | avg_latency_ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| faz1-50 | 50 | 0 | 68.0% | 66.0% | 4.0% | 72.0% | 12706 |
| v2-95 | 95 | 0 | 63.2% | 64.0% | 4.2% | 68.4% | 21162 |
| v3-170 | 170 | 0 | 62.9% | 61.5% | 1.2% | 65.9% | 17358 |

## Source Selection Breakdown

| set | retrieved@k | assembled_present | model_selected | whitelist_violation | law_scope_mismatch | temporal_mismatch |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| faz1-50 | 56.0% | 88.0% | 70.0% | 0.0% | 6.0% | 0.0% |
| v2-95 | 72.6% | 87.4% | 75.8% | 0.0% | 7.4% | 0.0% |
| v3-170 | 61.8% | 92.3% | 84.1% | 0.0% | 6.5% | 0.0% |

## Smoke Gate Snapshot

- trace_coverage_rate: `100.0%`
- schema_validation_pass_rate: `100.0%`
- external_whitelist_violation_rate: `0.0%`
- law_scope_answer_leaks: `0`
- temporal_answer_leaks: `0`
- narrow_claim_answer_leaks: `0`
