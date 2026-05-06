# Residual Closure Matrix

## Scope
- Rows: `CBY-04`, `CBY-06`, `KANUN-12`, `KKY-01`, `KKY-03`, `TEB-04`, `TUZUK-04`, `TUZUK-05`, `YON-04`.
- Live runtime changes: none; option-B non-live candidate gateway started on `127.0.0.1:8010` after owner approval.
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
| TEB-04 | shadow_collection_build_verified_candidate_smoke_pending | product_span_confirmed | raw_pdf_verified_spans_materialized_shadow_collection_verified | product_span_confirmed | yes | no | no | corpus_materialization_owner | run_trace_smoke_only_if_option_C_authorized |
| TUZUK-04 | current_law_vs_repealed_source_blocker | legal_taxonomy_confirmed_blocks | raw_verified_historical_repealed_ready | no_scorer_review_required | no | no | no | source_acquisition_legal_review | current_law_repealed_source_demotion_and_revalidation |
| TUZUK-05 | shadow_collection_available_candidate_smoke_pending | human_review_closed_accept_general_hierarchy_rule | exact_tuzuk_source_not_identifiable | rubric_policy_implemented_offline_scorer_and_smoke_passed | yes_if_no_wrong_candidate_source | no | no | scorer_policy_runtime_owner | run_trace_smoke_only_if_option_C_authorized |
| YON-04 | confirmed_source_no_runtime_improvement | legal_confirmation_available | raw_verified_ready | no_scorer_review_required | no | no | no | legal_scorer_source_acquisition | systemic_runtime_materialization_and_retrieval_revalidation |

## Source Basis
- `reports/benchmark/phase_24M_residual_blocker_consolidation.csv`
- `reports/benchmark/phase_24H_legal_scorer_review_normalization.csv`
- `reports/benchmark/phase_24I_official_source_acquisition_return_validation.csv`
- `reports/benchmark/productization/human_legal_review_packet_20260506/intake/human_legal_review_intake_report.md`

## Human Review Intake Update
- `TUZUK-05`: human review closed the source ambiguity as `rubric_should_accept_general_hierarchy_rule`. Offline scorer policy accepts the abstract hierarchy source-policy class and rejects concrete irrelevant tüzük titles for that class; artifact-level non-live runtime priority/scorer smoke passed; option-B non-live candidate health is `ok`. Targeted/full trace-on benchmark validation is still pending.
- `TEB-04`: human review confirmed `product_span_confirmed`; official GIB KDV GUT PDF was SHA-256 verified, 6 deterministic non-live spans were materialized from PDFKit extraction, artifact-level non-live span/selector smoke passed, option-A shadow collection build/load verified 59 delta rows, and option-B non-live candidate health is `ok`. Productization still requires targeted/full trace-on benchmark validation.
- `CBY-04`, `CBY-06`, `TUZUK-04`: reviewed evidence still blocks internal/product progression until systemic source/corpus fixes are completed and revalidated.

## Decision
- Residual closure status: **not closed**.
- Human legal/scorer review blocker is closed for `TUZUK-05` and `TEB-04`.
- Productization remains blocked because `TEB-04` and `TUZUK-05` still need targeted/full trace-on benchmark validation, and the other residual rows remain open or conditional.
- Serving candidate remains blocked because no residual row is accepted for serving-candidate without implementation and non-live validation.
