# Phase 23R-C Candidate Verification Smoke

Generated: 2026-05-02T21:30:55Z

Scope: candidate `8028` verification only. Live `8000` remained baseline `current_serving_lane`.

Run dir: `reports/benchmark/runs/phase23R_candidate_verification_smoke_20260502T213055Z`

## Runtime

| Field | Value |
|---|---|
| API URL | `http://127.0.0.1:8028/v1` |
| Lane | `phase22f_s7_full_shadow` |
| Model | `hukuk-ai-poc` |
| DGX model | `/models/merged_model_fabric_stage_20260321` |
| Milvus collection | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` |
| Guardrails | disabled |
| Verification | disabled |
| Live `8000` untouched | true |

## Smoke QIDs

```text
MULGA-01
MULGA-05
TEB-04
TEB-06
CBG-01
CBKAR-08
YON-05
UY-01
KANUN-12
KKY-03
```

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

Legacy `source_key_collision_detected_count = 1` was observed, matching the Phase 23 pre-cutover smoke watchlist. This is not a Phase 23R-C blocker because `source_key_v2_collision_detected_count = 0` and `binding_source_key_collision_detected_count = 0`.

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

Phase 23R-C candidate verification smoke: PASS.

This does not authorize live cutover. Live cutover remains approval-gated.
