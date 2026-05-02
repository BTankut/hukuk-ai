# Phase 22F-S3 Implementation Readiness Decision

This is an audit/design decision artifact only. No runtime code, answer synthesis, source identity, retrieval, prompt, model, benchmark, live cutover, productization, or fine-tuning change was performed.

## Decision

```text
Option A: Open Phase 22F-S4 split temporal claim implementation.
```

## Basis

The S3 audit/design criteria are satisfied:

| Criterion | Status | Evidence |
|---|---:|---|
| S2 revert state verified | PASS | `phase_22F_S3_revert_state_verification.md` |
| 13/13 relevant rows classified | PASS | `phase_22F_S3_two_permission_policy_audit.md` |
| Active non-MULGA rewrite denial defined | PASS | 7 active non-MULGA rows have `claim_family_rewrite_allowed = false` |
| MULGA historical surface path defined | PASS | 5 MULGA rows have a historical surface path |
| Two independent permissions designed | PASS | `claim_family_rewrite_allowed` and `historical_claim_surface_allowed` |
| QID-specific implementation requirement | PASS | No QID-specific branch is required by the design |
| Smoke plan clear | PASS | Policy unit, targeted 13-row, P0 relation, regression, and full benchmark gates are defined |

## S4 Scope Allowed

S4 may implement only deterministic split temporal claim policy:

```text
claim_family_rewrite_allowed
historical_claim_surface_allowed
```

Implementation must be metadata/rule based. It may use source family, selected evidence state, relation-chain state, query/task historical intent, and selected evidence identity.

## S4 Scope Closed

S4 must not change:

```text
retrieval
top-k
source acquisition
corpus materialization
model
prompt strategy
live 8000 serving
base/live collections
productization state
fine-tuning state
```

S4 must not use QID-specific logic or benchmark answer-key leakage.

## Required S4 Gates

S4 implementation must run in this order:

| Gate | Required result |
|---|---|
| Policy unit tests | All split-policy buckets produce expected permissions. |
| 13-row targeted smoke | Active non-MULGA rows do not claim `MULGA`; MULGA rows retain historical surface path. |
| P0 relation guard smoke | `MULGA >= 4/5`, `TEBLIGLER >= 6/8`, `TEB-06 = PASS`, `repealed_as_active_count = 0`. |
| Regression guard | Safety counters remain zero and no source/binding collision appears. |
| Full benchmark | Allowed only if all earlier gates pass. |

## Stop Rules

S4 must stop immediately if:

```text
active non-MULGA overapplication returns
MULGA guard falls below 4/5
TEBLIGLER guard falls below 6/8
TEB-06 fails
repealed_as_active_count > 0
unsupported/confident/contract/collision safety counters become non-zero
source/binding collision appears
QID-specific branch is needed to pass
```

## Productization Gate Decision

```text
Productization remains closed.
```

Reason: S2 failed P0 relation guard, and S3 is only a policy design phase. No live cutover or productization action is justified by S3.

## Fine-Tuning Gate Decision

```text
Fine-tuning remains closed.
```

Reason: The failure mode is deterministic temporal claim-policy conflation. It should be fixed in policy logic before any model-training discussion.

## Final Readiness Statement

Phase 22F-S4 is ready to open as a narrowly scoped split-policy implementation phase. It is not ready for productization, live cutover, retrieval changes, or fine-tuning.
