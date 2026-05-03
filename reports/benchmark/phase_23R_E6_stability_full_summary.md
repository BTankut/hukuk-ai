# Phase 23R-E6 Stability Full Benchmark Summary

Generated: 2026-05-03T10:16:11Z

Scope: second full 100-question benchmark on live `8000` after E5 PASS, used for post-cutover stability confirmation.

Run dir: `reports/benchmark/runs/20260503T091350Z_phase23R_E6_stability_full`

## Runtime

| Field | Value |
|---|---|
| API URL | `http://127.0.0.1:8000/v1` |
| Model | `hukuk-ai-poc` |
| Runtime git SHA | `b68ce3c3c8a573d5d5a598f2714ec774dca027d0` |
| DGX model | `/models/merged_model_fabric_stage_20260321` |
| Milvus collection | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` |
| Lane | `phase22f_s7_full_shadow` |
| API version | `2026-05-03-phase23R-E-benchmark-only-cutover` |
| Guardrails | disabled |
| Verification | disabled |

## Contract / Runtime Result

| Metric | Observed | Required | Result |
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

## Score Result

| Metric | Observed |
|---|---:|
| raw_score_proxy | 816.86 |
| average_score_0_10_proxy | 8.17 |
| pass_proxy | 91 |
| fail_proxy | 9 |
| wrong_family | 6 |
| wrong_document | 4 |
| hallucinated_identifier / source | 4 |
| unsupported_confident_answer_count | 0 |
| answer_contract_invalid_count | 0 |

## Decision

Phase 23R-E6 stability full benchmark: PASS.

No runtime, contract, collision, or score regression was observed. No rollback triggered.
