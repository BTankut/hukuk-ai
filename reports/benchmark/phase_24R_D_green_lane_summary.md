# Phase 24R-D Green Lane Summary

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

Matched A/B green lane is `PASS` for CBY merge consideration because CBY is non-regressive versus BASE on score, pass count, wrong-family, wrong-document, hallucinated-identifier, contract, unsupported-confidence, and collision checks.

This is not a productization green lane. Live `8000` remains unchanged.
