# Phase 24HU-G Recovery Decision

## Decision

Option A: KANUN-08 recovered safely for non-live focused scope.

This is not a live cutover decision.

## Basis

Focused non-live smoke:

```text
KANUN-08: 3.93 FAIL -> 8.22 PASS
Focused pass count: 10/13 -> 11/13
Focused raw score: 100.54 -> 104.83
Guard-row score regressions: 0
contract_invalid: 0
unsupported_confident_answer: 0
source_key_v2_collision: 0
binding_source_key_collision: 0
```

The source-role lane restored secondary-family supporting evidence while preserving primary KANUN identity.

## Productization Decision

Do not productize in Phase 24HU.

## Internal Eval Decision

Do not enable internal eval in Phase 24HU.

## Fine-Tuning Decision

Do not fine-tune. This was a retrieval/evidence-role issue, not a model-weight issue.

## Next Phase

Open a controlled full-candidate validation and integration brief for the Phase 24HU feature flags. The next phase should decide whether the candidate is eligible for broader benchmark validation, not live cutover by default.

