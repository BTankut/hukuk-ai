# Phase 24K Full Shadow Benchmark Not Run

- generated_at_utc: `2026-05-03T15:05:05Z`
- decision: `NOT_RUN`
- reason: `Phase 24J targeted shadow smoke failed`

## Precondition

Phase 24K may run only if Phase 24J targeted shadow smoke passes.

Phase 24J-D result:

```text
status = FAIL
run_dir = reports/benchmark/runs/phase_24J_targeted_shadow_smoke_20260503T145613Z
```

## Blocking Evidence

| Gate | Required | Observed | Result |
|---|---|---:|---|
| answered | all | 12/12 | PASS |
| contract_valid | all | 12/12 | PASS |
| unsupported_confident_answer | 0 | 0 | PASS |
| answer_contract_invalid | 0 | 0 | PASS |
| source_key_v2_collision | 0 | 0 | PASS |
| binding_collision | 0 | 0 | PASS |
| no regression in MULGA-01 | no regression | FAIL vs prior PASS | FAIL |
| no regression in MULGA-05 | no regression | FAIL vs prior PASS | FAIL |
| no regression in TEB-06 | no regression | FAIL vs prior PASS | FAIL |
| TUZUK-04 active-current-law claim | none | repealed_as_active_count = 0 | PASS |

## Minimum Gate Not Evaluated

The Phase 24K minimum full benchmark gate was not evaluated because the required targeted smoke gate failed:

```text
raw_score_proxy >= 816
pass_proxy >= 91
wrong_family <= 6
wrong_document <= 4
hallucinated_identifier <= 4
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
green_lane = PASS
```

## Safety Constraints Preserved

No full benchmark was run against the Phase 24J candidate after the targeted smoke failure. Live `8000` remains benchmark-only and unchanged.

## Decision

Phase 24K status: `NOT_RUN`.
