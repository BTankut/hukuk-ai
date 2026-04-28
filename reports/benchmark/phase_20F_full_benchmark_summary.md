# Phase 20F Full Benchmark Summary

Date: 2026-04-28

Status: MEASURED

Run: `reports/benchmark/runs/20260428T_phase20F_full_after_C_D`

## Runtime Provenance

- model: `hukuk-ai-poc`
- dgx_model: `/models/merged_model_fabric_stage_20260321`
- milvus_collection: `mevzuat_faz1_shadow_20260418_compat1024`
- milvus_entity_count: `349191`
- vector_dimension: `1024`
- embedding_backend/model: `remote` / `intfloat/multilingual-e5-large-instruct`
- embedding_base_url: `http://127.0.0.1:8081/v1`
- guardrails: `false`
- presidio: `false`
- git_sha: `cdb6a404f29d59d7b27e7ea1434a233492110f7f`
- dirty_worktree: `True`

## Metrics

| Metric | Value | R8 baseline | Delta |
| --- | ---: | ---: | ---: |
| `raw_score_proxy` | 755.6 | 756.61 | -1.01 |
| `pass_proxy` | 79 | 79 | 0 |
| `fail_proxy` | 21 | 21 | 0 |
| `unsupported_confident_answer_count` | 0 | 0 | 0 |
| `answer_contract_invalid_count` | 0 | 0 | 0 |
| `source_key_v2_collision_detected_count` | 0 | 0 | 0 |
| `binding_source_key_collision_detected_count` | 0 | 0 | 0 |
| `hallucinated_source_count` | 9 | 9 | 0 |
| `canonical_missing_required_content_signal` | 95 | 95 | 0 |
| `canonical_partial_grounding_only` | 95 | 95 | 0 |
| `evidence_required_slot_value_count_total` | 1456 | 544 | 912 |
| `avg_evidence_required_slot_value_count` | 14.56 | 5.44 | 9.12 |
| `avg_answer_slot_coverage_score` | 0.883 | 0.836 | 0.047 |
| `confidence_policy_adjusted_count` | 42 | 42 | 0 |

## Green Lane

- status: `pass`
- run_validation: `pass`

## Interpretation

Phase 20F preserves pass no-regression and hard safety gates, but it misses the strict raw no-regression target (`755.6 < 756`) and the preferred raw target (`>= 760`). Treat this as a measurement/backlog gate, not a promotion gate.

## Target Check

| Target | Observed | Pass |
| --- | ---: | --- |
| raw_score_proxy >= 760 preferred | 755.6 | FAIL |
| raw_score_proxy >= 756 no regression | 755.6 | FAIL |
| pass_proxy >= 79 no regression | 79 | PASS |
| unsupported_confident_claim <= 2 | 0 | PASS |
| contract_valid = 100/100 | 100/100 | PASS |
| green_lane = PASS | pass | PASS |
| source_key_v2_collision = 0 | 0 | PASS |
| binding_source_key_collision = 0 | 0 | PASS |
| CB_GENELGE = 4/4 | 4/4 | PASS |
| UY >= 9/10 | 10/10 | PASS |
| MULGA >= 3/5 | 3/5 | PASS |
| YONETMELIK >= 6/10 | 6/10 | PASS |
| wrong_family <= 10 | 10 | PASS |
| wrong_document <= 9 | 9 | PASS |
| hallucinated_identifier <= 11 | 9 | PASS |
