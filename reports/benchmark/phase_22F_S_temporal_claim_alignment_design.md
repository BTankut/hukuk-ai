# Phase 22F-S Temporal Claim Alignment Design

Date: 2026-05-01

## Scope

This design covers historical/repealed claim alignment after Phase 22F-R proved that relation-chain retrieval can add historical rule, repeal instrument, and current-law basis spans to the evidence surface.

No retrieval, corpus, model, prompt, source acquisition, or live runtime change is authorized by this design.

## Problem

The current runtime can retrieve the correct chain for `MULGA-01`, but final answer and answer contract collapse the chain into a single claim. This creates mismatches such as:

```text
selected evidence: historical rule span
claimed source: repeal instrument
claimed article: repeal article
missing claim: current-law basis
```

For historical/repealed questions, a single `claimed_source_identifier` is not enough unless the runtime first chooses the correct role for the claim.

## Role Model

When relation-chain metadata is present, the answer contract must preserve three roles:

```text
historical_rule_source
repeal_or_currentness_source
current_law_basis_source
```

Role semantics:

| Role | Effective state | Claim wording | Claim surface |
|---|---|---|---|
| historical_rule | historical/repealed/historical_repealed | tarihsel olarak / yürürlükte olduğu dönemde / önceki düzenlemede | never active |
| repeal_evidence | repeal_instrument or active repeal provision | yürürlükten kaldırma / geçiş / güncellik notu | not substantive rule |
| current_law_basis | active | güncel dayanak / 2026 itibarıyla temel kaynak | active current source |

## Claim Policy

If `relation_chain_expansion_applied=true` and both repeal and current-law basis exist:

```text
primary_role = current_law_basis
historical_rule_source = selected historical source
repeal_or_currentness_source = relation_chain_repeal_source_key
current_law_basis_source = relation_chain_current_basis_source_key
answer_mode = qualified_answer or repealed_transition_answer
grounding_status must not be confident if role evidence is incomplete
```

The public answer should explain:

```text
1. Historical rule: what the old provision said while in force.
2. Repeal/currentness: why it cannot be relied on as active law now.
3. Current-law basis: what source is the current anchor.
```

If relation-chain is incomplete:

```text
primary_role = historical_rule
answer must be qualified
claim must not mark historical/repealed evidence active
missing relation role must be surfaced in temporal_claim_missing_reason
```

If no relation-chain metadata is available:

```text
primary_role = historical_rule
answer must be explicitly historical/limited
effective_state_claimed must remain repealed/historical when selected evidence is repealed
claimed source/article must be copied from selected evidence, not hallucinated
current-law basis must not be invented
```

## Forbidden Behavior

The alignment layer must prevent:

```text
historical source claimed active
repeal instrument claimed as the substantive historical rule
current-law basis erasing the historical rule when the question asks whether the old source can be relied on
claimed source identifier from one role with article from another role
unknown source with a specific article when selected evidence has a concrete source/span
```

## Output Fields

Existing answer contract fields to align:

```text
source_family_claimed
source_title_claimed
source_identifier_claimed
article_or_section_claimed
effective_state_claimed
answer_mode
grounding_status
confidence_0_100
needs_manual_review
temporal_qualification
```

New trace/contract fields:

```text
temporal_claim_alignment_applied
temporal_claim_primary_role
temporal_claim_historical_source_key
temporal_claim_repeal_source_key
temporal_claim_current_basis_source_key
temporal_claim_consistency_status
temporal_claim_missing_reason
```

## Implementation Placement

Primary module:

```text
api-gateway/src/rag/answer_synthesis.py
```

Responsibilities:

```text
detect historical/repealed/relation-chain evidence
derive temporal claim roles
build role-aware answer contract patch
build optional role-aware answer prefix when answer omits required role wording
```

Secondary module:

```text
api-gateway/src/rag/evidence_bundle.py
```

Responsibilities:

```text
ensure relation_chain_* and temporal_claim_* fields are serializable in assembled evidence and trace
```

Optional module:

```text
api-gateway/src/rag/answer_slots.py
```

Responsibilities:

```text
only if tests prove required slot extraction blocks the new chain from surfacing
```

Avoid:

```text
retrieval_orchestration.py
source_identity.py
article_span_selection.py
```

## Trace Semantics

`temporal_claim_alignment_applied=true` only when the runtime changed or validated the claim surface for a historical/repealed chain.

`temporal_claim_consistency_status` values:

```text
aligned
qualified_missing_relation
corrected_repealed_not_active
corrected_role_mismatch
no_historical_context
```

`temporal_claim_missing_reason` values:

```text
none
missing_repeal_source
missing_current_basis_source
no_relation_chain
no_historical_or_repealed_evidence
```

## Test Plan

Focused tests:

```text
test_historical_chain_synthesis_uses_three_roles
test_repeal_instrument_not_primary_substantive_rule
test_current_basis_claim_matches_current_source
test_repealed_source_not_claimed_active
test_no_qid_specific_temporal_alignment
```

The tests must construct generic historical/repealed evidence and relation-chain metadata. They must not mention `MULGA-01` as a branch condition.

## Acceptance For Implementation

The implementation is acceptable only if:

```text
all new unit tests pass
TEB-06 remains pass in targeted smoke
TEBLIGLER remains >= 6/8, preferred >= 7/8
MULGA reaches >= 4/5
repealed_as_active_count becomes 0
unsupported_confident_answer remains 0
answer_contract_invalid remains 0
```

## Decision

Proceed to Phase 22F-S-C implementation.
