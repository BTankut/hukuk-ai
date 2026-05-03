# Phase 23R-E4 Post-Cutover Smoke

Generated: 2026-05-03T08:00:35Z

Scope: smoke on live `8000` after approved benchmark-only cutover.

Run dir: `reports/benchmark/runs/phase23R_E4_post_cutover_smoke_20260503T080035Z`

## Runtime

| Field | Value |
|---|---|
| API URL | `http://127.0.0.1:8000/v1` |
| Lane | `phase22f_s7_full_shadow` |
| API version | `2026-05-03-phase23R-E-benchmark-only-cutover` |
| Model | `hukuk-ai-poc` |
| DGX model | `/models/merged_model_fabric_stage_20260321` |
| Milvus collection | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` |
| Guardrails | disabled |
| Verification | disabled |

## Acceptance

| Check | Required | Observed | Result |
|---|---:|---:|---|
| answered | 10/10 | 10/10 | PASS |
| contract_valid | 10/10 | 10/10 | PASS |
| API errors | 0 | 0 | PASS |
| refused_or_empty | 0 | 0 | PASS |
| unsupported_confident_answer | 0 | 0 | PASS |
| answer_contract_invalid | 0 | 0 | PASS |
| source_key_v2_collision | 0 | 0 | PASS |
| binding_collision | 0 | 0 | PASS |
| `TEB-06` | PASS | PASS, score 8.90 | PASS |
| `MULGA-01` | PASS | PASS, score 8.37 | PASS |
| `MULGA-05` | PASS | PASS, score 7.10 | PASS |

Legacy `source_key_collision_detected_count = 1` was observed and remains watchlist-only because `source_key_v2_collision_detected_count = 0` and `binding_source_key_collision_detected_count = 0`.

## Score Summary

| Metric | Value |
|---|---:|
| total | 10 |
| raw_score_proxy | 62.54 / 100 |
| average_score_0_10_proxy | 6.25 |
| pass_proxy | 7 |
| fail_proxy | 3 |
| hallucinated_source_count | 2 |
| unsupported_confident_answer_count | 0 |
| answer_contract_invalid_count | 0 |
| contract_repaired_count | 0 |
| repealed_as_active_count | 0 |
| source_key_v2_collision_detected_count | 0 |
| binding_source_key_collision_detected_count | 0 |

## Per-QID Result

| QID | Score | Pass/Fail | Contract Valid | Unsupported Confident | V2 Collision | Binding Collision | Notes |
|---|---:|---|---|---|---|---|---|
| MULGA-01 | 8.37 | PASS | true | false | false | false | Required pass met |
| MULGA-05 | 7.10 | PASS | true | false | false | false | Required pass met |
| TEB-04 | 0.00 | FAIL | true | false | false | false | Known residual auto-fail |
| TEB-06 | 8.90 | PASS | true | false | false | false | Required pass met |
| CBG-01 | 8.65 | PASS | true | false | false | false | Pass |
| CBKAR-08 | 9.25 | PASS | true | false | false | false | Pass |
| YON-05 | 9.55 | PASS | true | false | false | false | Pass |
| UY-01 | 7.82 | PASS | true | false | false | false | Pass |
| KANUN-12 | 1.45 | FAIL | true | false | false | false | Known residual |
| KKY-03 | 1.45 | FAIL | true | false | false | false | Known residual |

## Decision

Phase 23R-E4 post-cutover smoke: PASS.

No rollback triggered. Proceed to Phase 23R-E5 full benchmark on live `8000`.
