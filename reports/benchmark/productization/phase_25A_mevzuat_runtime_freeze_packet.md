# Phase 25A Mevzuat Runtime Freeze Packet

Generated: 2026-05-08T09:09:11.382917+00:00

## Freeze Decision

| field | value |
| --- | --- |
| runtime_recovery_line | `closed` |
| baseline_status | `benchmark_only_frozen` |
| productization_status | `closed` |
| internal_eval_status | `closed` |
| fine_tuning_status | `closed` |

## Live Runtime Baseline

| field | value |
| --- | --- |
| git_sha | `1a1251d922f2ab746ad81f2929c927fe3f057d78` |
| live_api_url | `http://127.0.0.1:8000/v1` |
| live_lane | `phase22f_s7_full_shadow` |
| live_api_version | `2026-05-03-phase23R-E-benchmark-only-cutover` |
| model | `hukuk-ai-poc` |
| DGX_MODEL | `/models/merged_model_fabric_stage_20260321` |
| collection | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` |
| entity_count | `349403` |
| embedding_model | `intfloat/multilingual-e5-large-instruct` |
| guardrails_state | `disabled` |
| verification_state | `disabled` |

## Latest Accepted Benchmark Runs

| run | raw_score_proxy | pass_proxy | wrong_document | hallucinated_identifier | hard counters |
| --- | ---: | ---: | ---: | ---: | --- |
| `Phase23R-E6 stability full` | 816.86 | 91 | 4 | 4 | contract_invalid=0; unsupported=0; source_key_v2_collision=0; binding_collision=0 |
| `Phase24U-B base trace-on full` | 805.09 | 89 | 3 | 7 | contract_invalid=0; unsupported=0; source_key_v2_collision=0; binding_collision=0 |

## Known Residuals

| qid | root_cause | current_status | internal_eval | serving | productization | owner |
| --- | --- | --- | --- | --- | --- | --- |
| `CBY-04` | wrong_family_and_hallucinated_identifier | source_identity_design_blocker | `no` | `no` | `no` | legal_scorer_plus_source_identity |
| `CBY-06` | missing_current_2026_amendment_span | current_amendment_span_blocker | `no` | `no` | `no` | source_acquisition_corpus |
| `KANUN-12` | confirmed_5651_source_but_retrieval_runtime_not_recovered | confirmed_source_no_runtime_improvement | `no` | `no` | `no` | source_acquisition_legal_review |
| `KKY-01` | kky_yonetmelik_family_normalization_gap | taxonomy_mapping_blocker | `conditional` | `no` | `no` | legal_scorer_taxonomy |
| `KKY-03` | source_family_confirmed_yonetmelik_but_runtime_not_recovered | confirmed_source_no_runtime_improvement | `no` | `no` | `no` | legal_scorer_source_acquisition |
| `TEB-04` | active_teblig_selected_but_answer_claimed_mulga_repealed_and_auto_failed | option_c_targeted_smoke_failed | `no` | `no` | `no` | corpus_materialization_owner |
| `TUZUK-04` | repealed_tuzuk_not_current_law_primary | current_law_vs_repealed_source_blocker | `no` | `no` | `no` | source_acquisition_legal_review |
| `TUZUK-05` | concrete_irrelevant_tuzuk_selected_as_primary_despite_general_hierarchy_policy | option_c_targeted_smoke_failed_stop_condition | `no` | `no` | `no` | scorer_policy_runtime_owner |
| `YON-04` | confirmed_kvkk_regulation_source_but_runtime_not_recovered | confirmed_source_no_runtime_improvement | `no` | `no` | `no` | legal_scorer_source_acquisition |

## Known Closed Paths

- `runtime_source_selection_residual_patching`
- `global_feature_flag_recovery`
- `qid_specific_runtime_fixes`
- `new_full_corpus_selector_reranker_heuristics`
- `fine_tuning`
- `productization`
- `public_serving`
- `internal_eval_opening`

## Rollback Target

Rollback target is the current frozen benchmark-only runtime: lane `phase22f_s7_full_shadow`, api version `2026-05-03-phase23R-E-benchmark-only-cutover`, collection `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`, model `/models/merged_model_fabric_stage_20260321`.

No new live cutover target is authorized by Phase25A.

Manifest: `reports/benchmark/productization/phase_25A_mevzuat_runtime_freeze_manifest.json`
