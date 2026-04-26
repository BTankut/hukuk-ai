# Phase 18 Recovery A1.10 Live Full Summary

## Scope

- Run directory: `reports/benchmark/runs/20260426T_phase18_recovery_A1_10_live_full100_retry`
- Green lane directory: `reports/benchmark/green_lane/20260426T_phase18_recovery_A1_10_live_full100_retry`
- Endpoint: `http://127.0.0.1:8000/v1`
- Model: `hukuk-ai-poc`
- Runtime logic changed: `no`

## Runtime Provenance

- timestamp_utc: `2026-04-26T07:38:37.202781+00:00`
- git_sha: `ea3f6ad94591e008d53dc1c732c33e5efbb6a0c3`
- branch: `bt/hukuk-ai-100-benchmark-hardening`
- dirty_worktree: `True`
- api_url: `http://127.0.0.1:8000/v1`
- gateway_model_name: `hukuk-ai-poc`
- dgx_model_env: `/models/merged_model_fabric_stage_20260321`
- milvus_collection: `mevzuat_faz1_shadow_20260418_compat1024`
- milvus_entity_count: `349191`
- vector_dimension: `1024`
- embedding_backend: `remote`
- embedding_base_url: `http://127.0.0.1:8081/v1`
- guardrails_enabled: `false`
- presidio_enabled: `false`

## Hard Gate

| Metric | Result | Gate | Status |
| --- | ---: | ---: | --- |
| raw_score_proxy | 756.61 | >= 735 | PASS |
| pass_proxy | 79 | >= 73 | PASS |
| wrong_family | 10 | <= 15 | PASS |
| wrong_document | 9 | <= 15 | PASS |
| hallucinated_identifier | 11 | <= 23 | PASS |
| unsupported_confident_claim | 0 | <= 8 | PASS |
| answer_contract_invalid_count | 0 | 0 | PASS |
| green_lane | pass | pass | PASS |
| corpus_materialization_required_count | 2 | <= 6 | PASS |
| canonical_span_materialized_count | 98 | >= 90 | PASS |
| repealed_as_active_count | 0 | 0 preferred | PASS |
| source_key_v2_collision_detected_count | 0 | 0 | PASS |
| binding_source_key_collision_detected_count | 0 | 0 | PASS |

## Family Results

| Family | Pass / Count | Average Score |
| --- | ---: | ---: |
| CB_GENELGE | 4/4 | 8.80 |
| CB_KARAR | 6/8 | 7.96 |
| CB_KARARNAME | 6/6 | 8.75 |
| CB_YONETMELIK | 3/6 | 6.52 |
| KANUN | 19/21 | 7.83 |
| KHK | 6/6 | 8.86 |
| KKY | 9/11 | 8.18 |
| MULGA | 3/5 | 4.97 |
| TEBLIGLER | 4/8 | 5.60 |
| TUZUK | 3/5 | 7.52 |
| UY | 10/10 | 9.02 |
| YONETMELIK | 6/10 | 6.10 |

## Decision

Live full hard gate: `PASS`.
