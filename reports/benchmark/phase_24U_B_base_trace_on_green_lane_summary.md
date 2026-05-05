# Phase 24U-B BASE Trace-On Green Lane Summary

Generated UTC: `2026-05-05T13:14:12Z`

## Result

```text
run_clean_green_lane = PASS
phase23RE_score_parity = FAIL
phase24u_c_allowed = YES
```

## Clean-Run Gate

| Gate | Expected | Actual | Result |
|---|---:|---:|---|
| include_trace | true | true | PASS |
| answered | 100 | 100 | PASS |
| errors | 0 | 0 | PASS |
| refused_or_empty | 0 | 0 | PASS |
| missing_trace | 0 | 0 | PASS |
| missing_contract_fields | 0 | 0 | PASS |
| contract_valid | 100 | 100 | PASS |
| unsupported_confident_answer | 0 | 0 | PASS |
| answer_contract_invalid | 0 | 0 | PASS |
| source_key_v2_collision | 0 | 0 | PASS |
| binding_collision | 0 | 0 | PASS |
| live_8000_untouched | true | true | PASS |

## Score-Parity Gate

| Gate | Threshold | Actual | Result |
|---|---:|---:|---|
| raw_score_proxy | >= 816.86 | 805.09 | FAIL |
| pass_proxy | >= 91 | 89 | FAIL |

## Decision

The clean-run gate passes, so Phase24U-C may run. The Phase23R-E score-parity gate fails, so BASE drift is still open and productization/internal eval/fine-tuning remain closed.
