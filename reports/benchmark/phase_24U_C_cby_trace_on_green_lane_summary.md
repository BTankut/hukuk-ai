# Phase 24U-C CBY Trace-On Green Lane Summary

Generated UTC: `2026-05-05T14:29:20Z`

## Result

```text
run_clean_green_lane = PASS
cby_consideration_gate = PASS
phase23RE_score_parity = FAIL
cutover_authorized = NO
```

## Clean-Run Gate

| Gate | Expected | Actual | Result |
|---|---:|---:|---|
| include_trace | true | true | PASS |
| answered | 100 | 100 | PASS |
| errors | 0 | 0 | PASS |
| refused_or_empty | 0 | 0 | PASS |
| missing_trace | 0 | 0 | PASS |
| contract_valid | 100 | 100 | PASS |
| unsupported_confident_answer | 0 | 0 | PASS |
| answer_contract_invalid | 0 | 0 | PASS |
| source_key_v2_collision | 0 | 0 | PASS |
| binding_collision | 0 | 0 | PASS |
| live_8000_untouched | true | true | PASS |

## CBY Consideration Gate

| Gate | BASE | CBY | Result |
|---|---:|---:|---|
| raw_score_proxy | 805.09 | 807.27 | PASS |
| pass_proxy | 89 | 90 | PASS |
| wrong_family | 8 | 8 | PASS |
| wrong_document | 3 | 3 | PASS |
| hallucinated_identifier | 7 | 7 | PASS |
| safety counters | 0 | 0 | PASS |

## Phase23R-E Parity

| Gate | Threshold | Actual | Result |
|---|---:|---:|---|
| raw_score_proxy | >= 816.86 | 807.27 | FAIL |
| pass_proxy | >= 91 | 90 | FAIL |

## Decision

CBY consideration passes inside Phase24U, but live cutover is not authorized because BASE drift is still unresolved and Phase23R-E parity is still failing. Continue to Phase24U-D source supplement ablation.
