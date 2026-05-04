# Phase 24N Closure Decision Normalization

- generated_at_utc: `2026-05-04T08:18:37.509058+00:00`
- normalized_csv: `reports/benchmark/phase_24N_closure_decision_normalization.csv`
- legal_scorer_source: `reports/benchmark/legal_review_returns/filled_phase_24H_legal_scorer_review_return.csv`
- source_acquisition_source: `reports/benchmark/legal_review_returns/filled_phase_24I_official_source_acquisition_checklist.csv`
- live_8000_modified: `false`
- productization_status: `CLOSED`
- internal_eval_status: `CLOSED`
- fine_tuning_status: `CLOSED`

## Summary

| category | qids |
|---|---|
| shadow_backfill_allowed | KANUN-12, KKY-03, YON-04 |
| historical_limited_only | TUZUK-04 |
| scorer_or_taxonomy_required | CBY-04, KKY-01, KKY-03, TEB-04, TUZUK-05 |
| corpus_backfill_required | CBY-06, TEB-04, TUZUK-04, KANUN-12, KKY-03, YON-04 |
| productization_blocked | all normalized residual rows |
| internal_eval_blocked | all except possible later limited shadow-smoke reassessment |

## Normalized Decisions

| qid | source_status | shadow | internal_eval | productization | next_action |
|---|---|---:|---|---|---|
| CBY-04 | not_in_24I_scope | false | blocked | blocked | source_identity_design_for_CB_YONETMELIK_primary_CB_KARARNAME_supporting |
| CBY-06 | needs_current_amendment_source_materialization | false | blocked | blocked | materialize_2026_m11_added_paragraph_systemically |
| KKY-01 | not_in_24I_scope | false | blocked | blocked | normalize_KKY_as_internal_alias_for_YONETMELIK_not_legal_family |
| TEB-04 | not_in_24I_scope | false | blocked | blocked | align_scorer_to_official_consolidated_KDV_GUT_and_materialized_exact_span |
| TUZUK-04 | confirmed_historical_repealed_only | false | blocked | blocked | apply_systemic_effective_state_handling_and_acquire_current_law_companion_sources |
| KANUN-12 | confirmed_parser_ready | true | blocked_until_shadow_smoke | blocked | shadow_backfill_5651_articles_5_6_7_11 |
| KKY-03 | confirmed_parser_ready_YONETMELIK | true | blocked_until_shadow_smoke | blocked | shadow_backfill_BDDK_YONETMELIK_articles_13_29_34_37_46 |
| YON-04 | confirmed_parser_ready | true | blocked_until_shadow_smoke | blocked | shadow_backfill_KVKK_deletion_regulation_articles_7_8_9_10_11_12 |
| TUZUK-05 | needs_more_review_not_found_benchmark_ambiguous | false | blocked | blocked | leave_open_residual_no_synthetic_source_no_backfill |

## Decision

Only `KANUN-12`, `KKY-03`, and `YON-04` are eligible for Phase 24N shadow-only remediation. `TUZUK-04` is confirmed only as historical/repealed and must not be promoted to current-law authority. `TUZUK-05` remains unresolved and excluded.
