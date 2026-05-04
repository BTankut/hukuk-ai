# Phase 24R-D Matched A/B Delta

## Summary

```text
base_run = reports/benchmark/runs/phase_24R_D_base_full_20260504T2035Z
cby_run = reports/benchmark/runs/phase_24R_D_cby_full_20260504T2130Z
base_raw_score_proxy = 725.4
cby_raw_score_proxy = 727.18
raw_score_delta = 1.78
base_pass_proxy = 72
cby_pass_proxy = 73
pass_delta = 1
base_wrong_family = 6
cby_wrong_family = 6
base_wrong_document = 21
cby_wrong_document = 21
base_hallucinated_identifier = 9
cby_hallucinated_identifier = 9
```

## Changed Rows

| qid | base | cby | delta | base_pass | cby_pass | note |
|---|---:|---:|---:|---|---|---|
| CBY-06 | 6.80 | 8.58 | 1.78 | FAIL | PASS | CBY materialization improves target row |

## Acceptance

```text
cby_raw_score_proxy_gte_base = true
cby_pass_proxy_gte_base = true
cby_wrong_family_lte_base = true
cby_wrong_document_lte_base = true
cby_hallucinated_identifier_lte_base = true
cby_contract_valid_100_100 = true
cby_unsupported_confident_answer_zero = true
cby_answer_contract_invalid_zero = true
cby_source_key_v2_collision_zero = true
cby_binding_collision_zero = true
matched_ab_green_lane_pass = true
```

CBY is matched-A/B merge-safe relative to the current BASE lane. This does not reopen productization, internal eval, or fine-tuning.
