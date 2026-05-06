# Residual Closure Matrix

## Scope
- Rows: `CBY-04`, `CBY-06`, `KANUN-12`, `KKY-01`, `KKY-03`, `TEB-04`, `TUZUK-04`, `TUZUK-05`, `YON-04`.
- Runtime changes: none.
- Productization safe default: `accepted_for_productization=no`.
- Output CSV: `reports/benchmark/productization/residual_closure_matrix.csv`

## Matrix Summary
| qid | current_status | legal_review_status | source_acquisition_status | scorer_rubric_status | internal_eval | serving_candidate | productization | owner | next_action |
|---|---|---|---|---|---|---|---|---|---|
| CBY-04 | source_identity_design_blocker | legal_taxonomy_confirmed_blocks | not_required | scorer_review_required | no | no | no | legal_scorer_plus_source_identity | systemic_source_identity_design_no_qid_branch |
| CBY-06 | current_amendment_span_blocker | runtime_fix_allowed_blocks | source_acquisition_required | no_scorer_review_required | no | no | no | source_acquisition_corpus | corpus_backfill_and_article_span_materialization |
| KANUN-12 | confirmed_source_no_runtime_improvement | legal_confirmation_available | raw_verified_ready | no_scorer_review_required | no | no | no | source_acquisition_legal_review | systemic_runtime_materialization_and_retrieval_revalidation |
| KKY-01 | taxonomy_mapping_blocker | legal_taxonomy_confirmed_conditional | not_required | scorer_review_required | conditional | no | no | legal_scorer_taxonomy | systemic_family_normalization_required |
| KKY-03 | confirmed_source_no_runtime_improvement | legal_confirmation_available | raw_verified_ready | scorer_review_required | no | no | no | legal_scorer_source_acquisition | systemic_family_materialization_and_retrieval_revalidation |
| TEB-04 | verified_kdv_gut_spans_materialized_non_live | product_span_confirmed | raw_pdf_verified_and_spans_materialized | product_span_confirmed | yes | no | no | corpus_materialization_owner | run_gated_non_live_teb04_retrieval_selector_smoke_then_shadow_integration_plan |
| TUZUK-04 | current_law_vs_repealed_source_blocker | legal_taxonomy_confirmed_blocks | raw_verified_historical_repealed_ready | no_scorer_review_required | no | no | no | source_acquisition_legal_review | current_law_repealed_source_demotion_and_revalidation |
| TUZUK-05 | general_hierarchy_scorer_policy_implemented_runtime_pending | human_review_closed_accept_general_hierarchy_rule | exact_tuzuk_source_not_identifiable | rubric_policy_implemented_offline_scorer | yes_if_no_wrong_candidate_source | no | no | scorer_policy_runtime_owner | wire_systemic_hierarchy_source_policy_into_runtime_then_non_live_smoke |
| YON-04 | confirmed_source_no_runtime_improvement | legal_confirmation_available | raw_verified_ready | no_scorer_review_required | no | no | no | legal_scorer_source_acquisition | systemic_runtime_materialization_and_retrieval_revalidation |

## Source Basis
- `reports/benchmark/phase_24M_residual_blocker_consolidation.csv`
- `reports/benchmark/phase_24H_legal_scorer_review_normalization.csv`
- `reports/benchmark/phase_24I_official_source_acquisition_return_validation.csv`
- `reports/benchmark/productization/human_legal_review_packet_20260506/intake/human_legal_review_intake_report.md`

## Human Review Intake Update
- `TUZUK-05`: human review closed the source ambiguity as `rubric_should_accept_general_hierarchy_rule`. Offline scorer policy now accepts the abstract hierarchy source-policy class and rejects concrete irrelevant tüzük titles for that class. Runtime/source-policy validation is still pending.
- `TEB-04`: human review confirmed `product_span_confirmed`; official GIB KDV GUT PDF was SHA-256 verified and 6 deterministic non-live spans were materialized from PDFKit extraction. Productization still requires gated non-live retrieval/selector smoke and shadow/runtime integration.
- `CBY-04`, `CBY-06`, `TUZUK-04`: reviewed evidence still blocks internal/product progression until systemic source/corpus fixes are completed and revalidated.

## Decision
- Residual closure status: **not closed**.
- Human legal/scorer review blocker is closed for `TUZUK-05` and `TEB-04`.
- Productization remains blocked because `TEB-04` materialization is artifact-only, `TUZUK-05` runtime/source-policy validation is pending, and the other residual rows remain open or conditional.
- Serving candidate remains blocked because no residual row is accepted for serving-candidate without implementation and non-live validation.
