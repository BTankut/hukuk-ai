# Phase 18 Recovery A1.9 Live Full 100 Summary

## Scope

- Task brief: `reports/benchmark/hukuk_ai_phase18_recovery_A1_9_controlled_live_cutover_brief.md`
- Live endpoint during run: `http://127.0.0.1:8000/v1`
- Model: `hukuk-ai-poc`
- DGX model env: `/models/merged_model_fabric_stage_20260321`
- Live collection during run: `mevzuat_faz1_shadow_20260418_compat1024`
- Run directory: `reports/benchmark/runs/20260426T_phase18_recovery_A1_9_live_full100`
- Green lane directory: `reports/benchmark/green_lane/20260426T_phase18_recovery_A1_9_live_full100`
- Runtime provenance: `reports/benchmark/runs/20260426T_phase18_recovery_A1_9_live_full100/runtime_provenance.json`

## Runtime

- timestamp_utc: `2026-04-25T21:59:48.759708+00:00`
- git_sha: `8c93a54b77094caf40bca6681069b35b1641c3e2`
- branch: `bt/hukuk-ai-100-benchmark-hardening`
- dirty_worktree: `True`
- milvus_collection: `mevzuat_faz1_shadow_20260418_compat1024`
- milvus_entity_count: `349191`
- vector_dimension: `1024`
- embedding_backend: `remote`
- embedding_base_url: `http://127.0.0.1:8081/v1`
- guardrails_enabled: `false`
- presidio_enabled: `false`

## Hard Gate Result

The live full 100 run passed the A1.9 hard acceptance gate.

| Metric | Live Result | Gate | Status |
| --- | ---: | ---: | --- |
| raw_score_proxy | 756.61 | >= 735 | PASS |
| pass_proxy | 79 / 100 | >= 73 | PASS |
| wrong_family | 10 | <= 15 | PASS |
| wrong_document | 9 | <= 15 | PASS |
| hallucinated_identifier | 11 | <= 23 | PASS |
| unsupported_confident_claim | 0 | <= 8 | PASS |
| answer contract invalid | 0 | 0 | PASS |
| contract completeness | 100 / 100 | 100 / 100 | PASS |
| green_lane | pass | PASS | PASS |
| corpus_materialization_required_count | 2 | <= 6 | PASS |
| canonical_span_materialized_count | 98 | >= 90 | PASS |
| YONETMELIK pass | 6 / 10 | >= 6 / 10 | PASS |
| MULGA pass | 3 / 5 | >= 3 / 5 | PASS |
| repealed_as_active_count | 0 | 0 preferred | PASS |
| source_key_v2_collision_detected_count | 0 | 0 | PASS |
| binding_source_key_collision_detected_count | 0 | 0 | PASS |

## Family Results

| Family | Pass / Count | Average Score |
| --- | ---: | ---: |
| CB_GENELGE | 4 / 4 | 8.80 |
| CB_KARAR | 6 / 8 | 7.96 |
| CB_KARARNAME | 6 / 6 | 8.75 |
| CB_YONETMELIK | 3 / 6 | 6.52 |
| KANUN | 19 / 21 | 7.83 |
| KHK | 6 / 6 | 8.86 |
| KKY | 9 / 11 | 8.18 |
| MULGA | 3 / 5 | 4.97 |
| TEBLIGLER | 4 / 8 | 5.60 |
| TUZUK | 3 / 5 | 7.52 |
| UY | 10 / 10 | 9.02 |
| YONETMELIK | 6 / 10 | 6.10 |

## Failure Classes

- `wrong_family=10`
- `wrong_document=9`
- `hallucinated_identifier=11`
- `wrong_article=2`
- `missing_gold_document_signal=9`
- `auto_fail_triggered=4`
- `insufficient_canonical_span_evidence=2`
- `missing_required_content_signal=95`
- `partial_grounding_only=95`

## Decision Dependency

This hard gate pass is necessary but not sufficient for cutover completion. The separate candidate/live equivalence gate is evaluated in `reports/benchmark/phase_18_recovery_A1_9_candidate_live_comparison.md`.
