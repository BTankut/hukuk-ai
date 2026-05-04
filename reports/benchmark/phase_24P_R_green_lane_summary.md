# Phase 24P-R Green Lane Summary

## Decision

```text
green_lane = FAIL
cutover_allowed = false
live_8000_modified = false
```

## Gate Matrix

| Metric | Gate | Observed | Result |
|---|---:|---:|---|
| raw_score_proxy | >= 816 | 806.87 | FAIL |
| pass_proxy | >= 91 | 90 | FAIL |
| wrong_family | <= 6 | 8 | FAIL |
| wrong_document | <= 4 | 3 | PASS |
| hallucinated_identifier | <= 4 | 7 | FAIL |
| contract_valid | 100/100 | 100/100 | PASS |
| unsupported_confident_answer | 0 | 0 | PASS |
| answer_contract_invalid | 0 | 0 | PASS |
| source_key_v2_collision | 0 | 0 | PASS |
| binding_collision | 0 | 0 | PASS |

## Safety Findings

```text
transport_contract = PASS
unsupported_confident_answer = PASS
collision_contract = PASS
TUZUK-04_active_current_law_claim = false
targeted_CBY06 = PASS
TEB04_section_materialization = blocked
```

## Cutover Decision

No cutover. The Phase 24P-R candidate remains shadow-only.
