# Phase 24O Full Shadow Benchmark Summary

Run:

```text
reports/benchmark/runs/phase_24O_full_shadow_20260504T095702Z
```

Runtime:

```text
api_url = http://127.0.0.1:8031/v1
model = hukuk-ai-poc
DGX_MODEL = /models/merged_model_fabric_stage_20260321
MILVUS_COLLECTION = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24n
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
contract_valid = 100
unsupported_confident_answer = 0
answer_contract_invalid = 0
```

## Proxy Score

```text
raw_score_proxy = 805.09 / 1000
average_score_0_10_proxy = 8.05
pass_proxy = 89
fail_proxy = 11
hallucinated_source_count = 3
unsupported_confident_answer_count = 0
answer_contract_invalid_count = 0
repealed_as_active_count = 0
temporal_validity_miss_count = 0
source_key_v2_collision_detected_count = 0
binding_source_key_collision_detected_count = 0
```

## Minimum Gate

The full shadow benchmark did not meet the Phase 24O minimum gate:

```text
required raw_score_proxy >= 816      observed 805.09  FAIL
required pass_proxy >= 91            observed 89      FAIL
required wrong_family <= 6           observed 8       FAIL
required wrong_document <= 4         observed 3       PASS
required hallucinated_identifier <= 4 observed 7      FAIL
required contract_valid = 100/100    observed 100/100 PASS
required unsupported_confident = 0   observed 0       PASS
required answer_contract_invalid = 0 observed 0       PASS
required source_key_v2_collision = 0 observed 0       PASS
required binding_collision = 0       observed 0       PASS
```

## Failed Rows

| QID | Score | Main failure |
| --- | ---: | --- |
| CBY-06 | 6.80 | Missing 11153/m.11 amendment content. |
| KANUN-02 | 3.25 | Wrong document / hallucinated identifier proxy. |
| KANUN-08 | 1.45 | Wrong family/document proxy. |
| KKY-01 | 6.65 | Taxonomy family residual. |
| KKY-03 | 5.38 | Selected 34360 but answer identifier/citation materialization insufficient. |
| MULGA-04 | 0.00 | Auto-fail residual. |
| TEB-04 | 0.00 | KDV GUT selected but section-level materialization missing. |
| TUZUK-04 | 4.63 | Correctly no active-current-law claim; proxy still marks family mismatch. |
| TUZUK-05 | 3.25 | Stop-loss source ambiguity. |
| YON-05 | 5.75 | Taxonomy/source-family residual. |
| YON-08 | 6.80 | Missing required content signal. |

## Decision

No cutover. Phase 24O remains shadow-only. The implementation is useful for targeted residual closure, but the full shadow candidate is not green-lane ready.
