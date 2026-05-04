# Phase 24P-R Full Shadow Benchmark Summary

Run:

```text
reports/benchmark/runs/phase_24P_R_full_shadow_20260504T1340Z
```

Runtime:

```text
api_url = http://127.0.0.1:8034/v1
model = hukuk-ai-poc
DGX_MODEL = /models/merged_model_fabric_stage_20260321
MILVUS_COLLECTION = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06
EMBEDDING_BACKEND = remote
EMBEDDING_BASE_URL = http://127.0.0.1:8081/v1
live_8000_untouched = true
```

## Run Contract

```text
total = 100
answered = 100
refused_or_empty = 0
errors = 0
missing_trace = 0
missing_contract_fields = 0
contract_valid = 100
unsupported_confident_answer = 0
answer_contract_invalid = 0
```

## Proxy Score

```text
raw_score_proxy = 806.87 / 1000
average_score_0_10_proxy = 8.07
pass_proxy = 90
fail_proxy = 10
hallucinated_source_count = 3
hallucinated_identifier = 7
wrong_family = 8
wrong_document = 3
source_key_v2_collision_detected_count = 0
binding_source_key_collision_detected_count = 0
```

## Minimum Gate

```text
required raw_score_proxy >= 816       observed 806.87 FAIL
required pass_proxy >= 91             observed 90     FAIL
required wrong_family <= 6            observed 8      FAIL
required wrong_document <= 4          observed 3      PASS
required hallucinated_identifier <= 4 observed 7      FAIL
required contract_valid = 100/100     observed 100/100 PASS
required unsupported_confident = 0    observed 0      PASS
required answer_contract_invalid = 0  observed 0      PASS
required source_key_v2_collision = 0  observed 0      PASS
required binding_collision = 0        observed 0      PASS
```

## Targeted Outcome

```text
CBY-06 = 8.58 PASS
TEB-04 = 0.00 FAIL
```

CBY-06 improved from the Phase 24O residual failure and is now PASS. TEB-04 remains blocked because the official KDV GUT raw source could not be captured reproducibly and no section materialization was performed.

## Failed Rows

| qid | score | main failure |
|---|---:|---|
| KANUN-02 | 3.25 | wrong document / hallucinated identifier proxy |
| KANUN-08 | 1.45 | wrong family / wrong document proxy |
| KKY-01 | 6.65 | taxonomy family residual / hallucinated identifier proxy |
| KKY-03 | 5.38 | family residual |
| MULGA-04 | 0.00 | auto-fail residual |
| TEB-04 | 0.00 | KDV GUT selected but section-level materialization missing |
| TUZUK-04 | 4.63 | repealed correctly, but proxy still marks family/identifier mismatch |
| TUZUK-05 | 3.25 | stop-loss source ambiguity |
| YON-05 | 5.75 | taxonomy/source-family residual |
| YON-08 | 6.80 | missing required content signal |

## Decision

Phase 24P-R full shadow is `FAIL` for green-lane cutover. Keep live `8000` on the existing Phase23R-E benchmark-only lane.
