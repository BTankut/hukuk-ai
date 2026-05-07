# Phase 24HV-E Integration Readiness Decision

## Decision

Option C: Candidate regresses.

No integration, no cutover, no productization, no internal eval enablement.

## Basis

Full candidate result:

```text
candidate_raw_score_proxy = 727.39 / 1000
candidate_pass_proxy = 74 / 100
base_trace_on_raw_score_proxy = 805.09 / 1000
base_trace_on_pass_proxy = 89 / 100
raw_delta = -77.70
pass_delta = -15
```

Hard counters:

```text
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
green_lane = pass
```

Regression counters:

```text
pass_to_fail = 19
fail_to_pass = 4
wrong_document = 18 vs base 3
hallucinated_identifier = 22 vs base 7
```

The candidate successfully recovers target rows (`KANUN-08`, `TEB-04`, `TUZUK-05`, `YON-05`), but broad full-benchmark regression dominates.

## Required Action

Keep Phase24HU/HV feature flags non-live and default-off. Do not integrate into live or productization paths.

Open a regression audit focused on why target-row recovery creates broad full-corpus degradation under the base `p0_backfill` collection. Priority areas:

- source-role recall over-application outside target legal-task patterns
- same-family/source-domain gating interaction with general KANUN rows
- hallucinated identifier increase on KANUN/UY/KKY rows
- candidate runtime parity against Phase24U base trace-on run

## Decisions

- controlled benchmark-only cutover: `blocked`
- productization: `closed`
- internal eval: `closed`
- fine-tuning: `closed`
- next phase: `Phase 24HW regression audit / feature isolation`, not cutover
