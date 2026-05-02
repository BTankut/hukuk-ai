# Phase 23 Pre-Cutover Candidate Smoke

Generated: 2026-05-02T20:28:39Z

Scope: candidate `8028` smoke only. Live `8000` was not modified.

## Runtime

| Field | Value |
|---|---|
| API URL | `http://127.0.0.1:8028/v1` |
| Lane | `phase22f_s7_full_shadow` |
| Model | `hukuk-ai-poc` |
| DGX model | `/models/merged_model_fabric_stage_20260321` |
| Milvus collection | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` |
| Milvus entity count | `349403` |
| Vector dimension | `1024` |
| Guardrails | `disabled` |
| Verification | `disabled` |
| Presidio | `disabled` |
| Run dir | `reports/benchmark/runs/phase23_pre_cutover_candidate_smoke_20260502T202839Z` |

The candidate shadow process on `8028` was stopped after the smoke run. Live `8000` remained untouched.

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
| source_key_v2_collision | 0 | 0 | PASS |
| binding_collision | 0 | 0 | PASS |
| `TEB-06` | PASS | PASS, score 8.90 | PASS |
| `MULGA-01` | expected candidate behavior | PASS, score 8.37 | PASS |
| `MULGA-05` | expected candidate behavior | PASS, score 7.10 | PASS |
| health/runtime error | none | none | PASS |

Note: the deterministic scorer reported `source_key_collision_detected_count = 1` for a legacy source-key collision class, while `source_key_v2_collision_detected_count = 0` and `binding_source_key_collision_detected_count = 0`. The Phase 23-E acceptance criterion is the v2/binding collision gate, which passed. Keep the legacy collision as a watchlist item if approval scope expands beyond benchmark/internal eval.

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
| manual_review_count | 10 |

## Per-QID Result

| QID | Score | Pass/Fail | Contract Valid | Unsupported Confident | V2 Collision | Binding Collision | Notes |
|---|---:|---|---|---|---|---|---|
| MULGA-01 | 8.37 | PASS | true | false | false | false | Expected candidate behavior preserved |
| MULGA-05 | 7.10 | PASS | true | false | false | false | Expected candidate behavior preserved |
| TEB-04 | 0.00 | FAIL | true | false | false | false | Known residual auto-fail from risk register |
| TEB-06 | 8.90 | PASS | true | false | false | false | Required smoke pass met |
| CBG-01 | 8.65 | PASS | true | false | false | false | Pass |
| CBKAR-08 | 9.25 | PASS | true | false | false | false | Pass |
| YON-05 | 9.55 | PASS | true | false | false | false | Pass |
| UY-01 | 7.82 | PASS | true | false | false | false | Pass |
| KANUN-12 | 1.45 | FAIL | true | false | false | false | Known residual from risk register |
| KKY-03 | 1.45 | FAIL | true | false | false | false | Known residual from risk register |

## Decision

Phase 23-E pre-cutover candidate smoke: PASS for benchmark/internal eval readiness.

This does not authorize live cutover. Explicit approval and rollback ownership are still required before any live `8000` change.
