# Phase 23 Cutover Candidate Manifest

Generated: 2026-05-02T20:21:54Z

Scope: controlled cutover readiness only. No live cutover was executed.

## Candidate

| Field | Value |
|---|---|
| candidate_git_sha | `6a85a5178d5dbd9e88677fd0acf6b92bdfdd0e76` |
| candidate_api_url | `http://127.0.0.1:8028/v1` |
| candidate_lane | `phase22f_s7_full_shadow` |
| candidate_model | `hukuk-ai-poc` |
| candidate_dgx_model_env | `/models/merged_model_fabric_stage_20260321` |
| candidate_milvus_collection | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` |
| candidate_milvus_entity_count | `349403` |
| candidate_vector_dimension | `1024` |
| candidate_source_catalog_hash | `composite_sha256:19ad43bcd9f1c636ad05588cb42ad37e84f47a3e8671e53ba117c14863cc96d2` |
| candidate_source_supplement_hash | `composite_sha256:eb61e773b85e791d068d8a25aacb33c3ed3f88ae0f469fccbe6b129ae61070c0` |
| candidate_guardrails_state | `disabled` |
| candidate_verification_state | `disabled` |
| candidate_benchmark_run_dir | `reports/benchmark/runs/20260502T1858Z_phase22F_S7_full_shadow_benchmark` |
| candidate_green_lane_dir | `reports/benchmark/runs/20260502T1831Z_phase22F_S7_combined_guard_smoke` |

`candidate_git_sha` is taken from `runtime_provenance.git_sha` for the validated Phase 22F-S7 full shadow benchmark run. The repository head before creating Phase 23 artifacts was `3cbe2a6b18069ae3acdfcc85a03861eb7114af59`.

## Current Live Baseline

| Field | Value |
|---|---|
| baseline_live_api_url | `http://127.0.0.1:8000/v1` |
| baseline_live_collection | `mevzuat_faz1_shadow_20260418_compat1024` |
| baseline_live_entity_count | `349191` |
| baseline_live_git_sha | `not_runtime_exposed` |
| baseline_live_model | `hukuk-ai-poc` |
| baseline_live_dgx_model_env | `/models/merged_model_fabric_stage_20260321` |
| baseline_live_lane | `current_serving_lane` |
| baseline_live_guardrails_state | `disabled` |
| baseline_live_verification_state | `disabled` |

The live `8000` process exposes model and collection identity through health/process probes but does not expose a bound git SHA. Live `8000` was not modified while preparing this manifest.

## Validated Candidate Result

| Metric | Value |
|---|---:|
| raw_score_proxy | 816.86 |
| pass_proxy | 91/100 |
| wrong_family | 6 |
| wrong_document | 4 |
| hallucinated_identifier | 4 |
| contract_valid | 100/100 |
| unsupported_confident_answer | 0 |
| answer_contract_invalid | 0 |
| repealed_as_active_count | 0 |
| source_key_v2_collision | 0 |
| binding_collision | 0 |
| green_lane | PASS |

Minimum shadow gate passed. Preferred gate remains one row short on `wrong_family <= 5`.

## Separation Note

The candidate runtime is a benchmark/internal evaluation lane with guardrails, verification, and Presidio disabled. This manifest does not authorize public serving or productization.
