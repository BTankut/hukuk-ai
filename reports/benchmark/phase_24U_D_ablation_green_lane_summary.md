# Phase 24U-D Ablation Green Lane Summary

Generated UTC: `2026-05-05T15:31:56Z`

## Result

```text
run_clean_green_lane = PASS
phase23RE_restored = FAIL
source_supplement_drift_confirmed = NO
recommended_decision_option = Option D — commit-level code regression audit
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

## Restoration Gate

| Gate | Phase23R-E threshold | Ablation actual | Result |
|---|---:|---:|---|
| raw_score_proxy | >= 816.86 | 804.42 | FAIL |
| pass_proxy | >= 91 | 89 | FAIL |

## Decision

The ablation run is clean, but it fails the restoration gate. Do not disable source supplements as a fix. Proceed with row attribution and then record Option D unless Phase24U-E uncovers contradictory evidence.
