# Phase 20F Full Benchmark And Phase 21 Recommendation

Status: CONDITIONAL_ACCEPT_PHASE20_C_D_AND_OPEN_PHASE21

## 1. Full Benchmark Metrics

- run: `reports/benchmark/runs/20260428T_phase20F_full_after_C_D`
- green lane: `pass`
- raw_score_proxy: `755.6`
- pass_proxy: `79/100`
- unsupported_confident_answer_count: `0`
- contract_valid: `100/100`
- source_key_v2_collision_detected_count: `0`
- binding_source_key_collision_detected_count: `0`

## 2. Family-Level Table

| Family | Pass/Total | Raw | Wrong Family | Wrong Document | Hallucinated | Avg Slot Coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| CB_GENELGE | 4/4 | 35.2 | 0 | 0 | 0 | 0.856 |
| CB_KARAR | 6/8 | 63.69 | 1 | 0 | 1 | 0.89 |
| CB_KARARNAME | 6/6 | 52.07 | 0 | 0 | 0 | 0.869 |
| CB_YONETMELIK | 3/6 | 39.1 | 2 | 0 | 2 | 0.89 |
| KANUN | 19/21 | 164.18 | 1 | 1 | 0 | 0.888 |
| KHK | 6/6 | 53.15 | 0 | 0 | 0 | 0.874 |
| KKY | 9/11 | 90.03 | 2 | 1 | 1 | 0.883 |
| MULGA | 3/5 | 24.87 | 0 | 1 | 1 | 0.89 |
| TEBLIGLER | 4/8 | 44.49 | 2 | 2 | 3 | 0.89 |
| TUZUK | 3/5 | 37.58 | 0 | 1 | 0 | 0.89 |
| UY | 10/10 | 90.23 | 0 | 0 | 0 | 0.872 |
| YONETMELIK | 6/10 | 61.01 | 2 | 3 | 3 | 0.89 |

## 3. Delta vs R8 Baseline

| Metric | R8 | Phase 20F | Delta |
| --- | ---: | ---: | ---: |
| `raw_score_proxy` | 756.61 | 755.6 | -1.01 |
| `pass_proxy` | 79 | 79 | 0 |
| `unsupported_confident_answer_count` | 0 | 0 | 0 |
| `answer_contract_invalid_count` | 0 | 0 | 0 |
| `hallucinated_source_count` | 9 | 9 | 0 |
| `canonical_missing_required_content_signal` | 95 | 95 | 0 |
| `canonical_partial_grounding_only` | 95 | 95 | 0 |
| `evidence_required_slot_value_count_total` | 544 | 1456 | 912 |
| `avg_answer_slot_coverage_score` | 0.836 | 0.883 | 0.047 |

## 4. Delta vs Phase 20C/D Smoke Expectations

- Phase 20C/D smoke expectation held for safety: unsupported confident stayed `0`, contract remained valid, and source-key/binding collisions stayed `0`.
- Full-run score did not materially improve: pass stayed `79`; raw moved `756.61 -> 755.60`.
- Slot metrics did improve materially: evidence count `544 -> 1456`, average slot coverage `0.836 -> 0.883`.

## 5. Missing / Partial Grounding Delta

- R8 missing_required_content_signal: `95`
- Phase20F missing_required_content_signal: `95`
- R8 partial_grounding_only: `95`
- Phase20F partial_grounding_only: `95`

## 6. Slot Coverage Delta

- evidence_required_slot_value_count_total: `544 -> 1456`
- avg_evidence_required_slot_value_count: `5.44 -> 14.56`
- avg_answer_slot_coverage_score: `0.836 -> 0.883`

## 7. Source / Span Blocker Backlog

- total source/span blockers: `17`
- detailed backlog: `reports/benchmark/phase_20F_source_span_blocker_backlog.md`

Priority order:

- `21A_TEBLIGLER`: tebliğ identifier/document arbitration and family guard.
- `21B_YONETMELIK`: exact title/institution matching and supporting-law demotion.
- `21C_MULGA`: historical document identity and canonical span evidence.
- `21D_CB_KARAR`: generalized transition/exception/operative-clause span audit.

## 8. Recommendation

Recommendation: `open Phase 21 source/span-family remediation`.

Phase 20C/D should be retained because they improved contract-visible slot coverage without breaking safety gates. Phase 20F is not a promotion/no-regression success because raw score missed the strict `>=756` no-regression target by `0.40`. Further Phase 20 slot/synthesis tuning should stop; the remaining benchmark gap is source/span-family remediation.

## 9. Productization / Fine-Tuning Gate

- Productization: CLOSED.
- Fine-tuning: CLOSED.
- Reconsider only after two stable full runs with source/span blockers reduced and family slice targets met.
