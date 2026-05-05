# Phase 24V-C Row-Level Drift Focus

## Scope
- Reference run: `reports/benchmark/runs/20260503T080937Z_phase23R_E5_post_cutover_full` (`816.86 / 91`)
- Current trace-on BASE run: `reports/benchmark/runs/phase_24U_B_base_trace_on_full_20260505T121226Z` (`805.09 / 89`)
- Included rows: all pass/fail changes plus material score drops (`delta <= -1.00`).
- Diagnostic only. No answer-key-driven runtime patch, no live `8000` change, no QID-specific remediation.

## Summary
- Focus rows: 12
- Pass/fail changes: 8
- Material drops: 8
- PASS->FAIL regressions: KANUN-02, KANUN-08, MULGA-04, YON-05, YON-08
- FAIL->PASS positive drift rows: CBY-04, KANUN-12, YON-04
- Selected-source changed among focus rows: KANUN-08, KANUN-12, KKY-04, KKY-08, KKY-11, YON-04, YON-05
- Selected-source unchanged but regressed PASS->FAIL: KANUN-02, MULGA-04, YON-08

## Findings
- `KANUN-08` and `YON-05` are the clearest source identity/selector regressions. They align with the Phase24V-B primary candidate: `ddcadd2` changing `_chunk_matches_selected_source_key` in `source_identity.py`.
- `KANUN-02`, `MULGA-04`, and `YON-08` regressed with the same selected source key, so source selection alone does not explain them. These need trace/failure-class audit before any code revert.
- `KKY-04`, `KKY-08`, and `KKY-11` are material score drops but still PASS; they also show selected-source drift and should be monitored in any source identity ablation.
- `KANUN-12` and `YON-04` improved from FAIL to PASS and likely depend on Phase24N source acquisition/supplement changes. Any recovery must preserve these gains.

## CSV
- `reports/benchmark/phase_24V_C_row_level_drift_focus.csv`

## Focus Table
| qid | Phase23R-E | current | delta | transition | suspected_component | candidate_commit |
|---|---:|---:|---:|---|---|---|
| CBY-04 | 6.85 | 7.12 | 0.27 | FAIL->PASS | minor_positive_score_change | ddcadd2 or non-code artifact drift unproven |
| KANUN-02 | 8.65 | 3.25 | -5.40 | PASS->FAIL | answer_contract_or_failure_class_policy | ddcadd2 unproven; selected source unchanged |
| KANUN-08 | 7.55 | 1.45 | -6.10 | PASS->FAIL | source_identity_or_selector | ddcadd2 source_identity.py |
| KANUN-12 | 1.45 | 8.99 | 7.54 | FAIL->PASS | source_supplement_positive_change | de7c653 phase24N data + ddcadd2 source_supplements.py |
| KKY-04 | 9.32 | 7.55 | -1.77 | PASS->PASS | source_identity_or_selector | ddcadd2 source_identity.py |
| KKY-08 | 9.55 | 8.00 | -1.55 | PASS->PASS | source_identity_or_selector | ddcadd2 source_identity.py |
| KKY-11 | 9.66 | 7.89 | -1.77 | PASS->PASS | source_identity_or_selector | ddcadd2 source_identity.py |
| MULGA-04 | 7.55 | 0.00 | -7.55 | PASS->FAIL | answer_contract_auto_fail_or_temporal_policy | ddcadd2 answer_synthesis.py unproven; selected source unchanged |
| TUZUK-04 | 6.43 | 4.63 | -1.80 | FAIL->FAIL | temporal_family_claim_policy | ddcadd2 answer_synthesis.py possible |
| YON-04 | 3.25 | 8.22 | 4.97 | FAIL->PASS | source_supplement_positive_change | de7c653 phase24N data + ddcadd2 source_supplements.py |
| YON-05 | 9.55 | 5.75 | -3.80 | PASS->FAIL | source_identity_or_selector | ddcadd2 source_identity.py |
| YON-08 | 7.25 | 6.80 | -0.45 | PASS->FAIL | answer_slot_completeness_or_claim_article_policy | ddcadd2 unproven; selected source unchanged |

## Next
- Phase24V-D should plan a non-live source-identity ablation for the title-metadata selected-key broadening, with guard rows `KANUN-12`, `YON-04`, and `CBY-04` included to prevent losing positive drift.
