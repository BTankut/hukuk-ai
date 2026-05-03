# Phase 23R-E5 Post-Cutover Full Benchmark Summary

Generated: 2026-05-03T09:12:43Z

Scope: approved benchmark-only full 100-question run on live `8000` after Phase 23R-E cutover.

Run dir: `reports/benchmark/runs/20260503T080937Z_phase23R_E5_post_cutover_full`

## Runtime

| Field | Value |
|---|---|
| API URL | `http://127.0.0.1:8000/v1` |
| Model | `hukuk-ai-poc` |
| Runtime git SHA | `b34ed1c8c72cd9c1108282eda50d53dd4d35c032` |
| DGX model | `/models/merged_model_fabric_stage_20260321` |
| Milvus collection | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` |
| Lane | `phase22f_s7_full_shadow` |
| API version | `2026-05-03-phase23R-E-benchmark-only-cutover` |
| Guardrails | disabled |
| Verification | disabled |

## Contract / Runtime Result

| Metric | Observed | Gate | Result |
|---|---:|---:|---|
| total | 100 | 100 | PASS |
| answered | 100 | 100 | PASS |
| refused_or_empty | 0 | 0 | PASS |
| API errors | 0 | 0 | PASS |
| contract_valid | 100/100 | 100/100 | PASS |
| unsupported_confident_answer | 0 | 0 | PASS |
| answer_contract_invalid | 0 | 0 | PASS |
| source_key_v2_collision | 0 | 0 | PASS |
| binding_collision | 0 | 0 | PASS |

## Score Gate

| Metric | Minimum Gate | Preferred Gate | Observed | Result |
|---|---:|---:|---:|---|
| raw_score_proxy | >= 800 | >= 816 | 816.86 | PASS |
| pass_proxy | >= 89 | >= 91 | 91 | PASS |
| wrong_family | <= 6 | <= 6 | 6 | PASS |
| wrong_document | <= 5 | <= 4 | 4 | PASS |
| hallucinated_identifier / source | <= 5 | <= 4 | 4 | PASS |
| unsupported_confident_answer | 0 | 0 | 0 | PASS |
| answer_contract_invalid | 0 | 0 | 0 | PASS |

## Additional Observations

| Metric | Value |
|---|---:|
| fail_proxy | 9 |
| average_score_0_10_proxy | 8.17 |
| selector_exact_article_hit_rate | 0.86 |
| selector_same_document_hit_rate | 1.0 |
| contract_completeness_rate | 1.0 |
| repealed_as_active_count | 0 |
| temporal_validity_miss_count | 0 |

## Decision

Phase 23R-E5 full benchmark: PASS.

Minimum gate and preferred gate are both satisfied. No rollback triggered. Proceed to Phase 23R-E6 stability rerun on live `8000`.
