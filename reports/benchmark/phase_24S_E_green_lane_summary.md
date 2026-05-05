# Phase 24S-E Green Lane Summary

```text
raw_score_proxy_gte_816_86 = false
pass_proxy_gte_91 = false
wrong_family_lte_6 = false
wrong_document_lte_4 = false
hallucinated_identifier_lte_4 = false
contract_valid_100_100 = true
unsupported_confident_answer_zero = true
answer_contract_invalid_zero = true
source_key_v2_collision_zero = true
binding_collision_zero = true
green_lane = FAIL
```

| Check | Result |
| --- | --- |
| raw_score_proxy >= 816.86 | FAIL |
| pass_proxy >= 91 | FAIL |
| wrong_family <= 6 | FAIL |
| wrong_document <= 4 | FAIL |
| hallucinated_identifier <= 4 | FAIL |
| contract_valid = 100/100 | PASS |
| unsupported_confident_answer = 0 | PASS |
| answer_contract_invalid = 0 | PASS |
| source_key_v2_collision = 0 | PASS |
| binding_collision = 0 | PASS |
| green_lane = PASS | FAIL |

Green lane is `FAIL`. Phase 24S-E requires rollback because the minimum gate failed.
