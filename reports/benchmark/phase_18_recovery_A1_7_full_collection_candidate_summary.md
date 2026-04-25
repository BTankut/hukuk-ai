# Phase 18 Recovery A1.7 Full Collection Candidate Summary

## Runtime

- run_dir: `reports/benchmark/runs/20260425T_phase18_recovery_A1_7_full_collection_candidate`
- api_url: `http://127.0.0.1:8018/v1`
- model: `hukuk-ai-poc`
- dgx_model_env: `/models/merged_model_fabric_stage_20260321`
- milvus_collection: `mevzuat_faz1_shadow_20260418_compat1024`
- milvus_entity_count: `349191`
- vector_dimension: `1024`
- live_8000_untouched: `True`
- live_8000_collection: `mevzuat_e5_shadow`

## Score

- raw_score_proxy: `729.1`
- pass_proxy: `71`
- fail_proxy: `29`
- wrong_family: `17`
- wrong_document: `17`
- hallucinated_identifier: `24`
- unsupported_confident_claim: `0`
- contract_valid: `100/100`
- green_lane: `pass`
- corpus_materialization_required_count: `1`
- canonical_span_materialized_count: `99`

## Acceptance Gate

| Metric | Actual | Required | Status |
|---|---:|---:|---|
| `raw_score_proxy` | `729.1` | `>= 735` | `FAIL` |
| `pass_proxy` | `71` | `>= 73` | `FAIL` |
| `wrong_family` | `17` | `<= 15` | `FAIL` |
| `wrong_document` | `17` | `<= 15` | `FAIL` |
| `hallucinated_identifier` | `24` | `<= 23` | `FAIL` |
| `unsupported_confident_claim` | `0` | `<= 8` | `PASS` |
| `contract_valid` | `100/100 invalid=0` | `100/100` | `PASS` |
| `green_lane` | `pass` | `PASS` | `PASS` |
| `corpus_materialization_required_count` | `1` | `<= 6` | `PASS` |
| `canonical_span_materialized_count` | `99` | `>= 90` | `PASS` |

- overall_candidate_gate: `FAIL`
- decision: `NO_CUTOVER`
