# Phase 22F-S3 Split Temporal Claim Policy Design

This is an audit/design artifact only. No runtime code, answer synthesis, source identity, retrieval, prompt, model, benchmark, live cutover, productization, or fine-tuning change was performed.

## Design Decision

Phase 22F-S4 may implement split temporal claim policy only if temporal logic produces two independent permissions:

| Permission | Meaning |
|---|---|
| `claim_family_rewrite_allowed` | Whether the answer contract may change the claimed source family/identifier away from the selected evidence family/identifier. |
| `historical_claim_surface_allowed` | Whether the answer may surface `MULGA`, repealed, or historical wording even when a complete relation chain is absent. |

S2 failed because one gate tried to solve two different requirements. Active non-MULGA rows need preservation of selected evidence identity. Genuine historical/MULGA rows need a controlled path to preserve historical surface even when relation metadata is incomplete.

## Rule 1: Active Non-MULGA Family Preservation

Condition:

```text
selected_source_family in [KANUN, KHK, TEBLIGLER, TUZUK, UY, KKY, YONETMELIK, CB_*]
AND selected_effective_state in [active, current, unknown_non_repealed]
AND relation_chain_expansion_applied = false
AND query/task is not genuinely MULGA-like historical
```

Policy:

```text
claim_family_rewrite_allowed = false
historical_claim_surface_allowed = false
should_preserve_selected_family = true
```

Behavior:

The answer must preserve the selected family, selected identifier, and selected effective state. A temporal note may be emitted only as supporting context. It must not rewrite the main claim into `MULGA`, repealed, or another family.

Primary S3-B rows:

```text
KANUN-05, KANUN-10, KANUN-14, KHK-03, TEB-03, TEB-04, TUZUK-03
```

## Rule 2: Relation-Chain Historical Three-Part Claim

Condition:

```text
relation_chain_expansion_applied = true
AND historical source is present
AND repeal/currentness instrument is present
AND current-law basis is present
```

Policy:

```text
claim_family_rewrite_allowed = controlled
historical_claim_surface_allowed = true
current_law_basis_required = true
repeal_instrument_required = true
```

Behavior:

The answer may surface a three-part historical chain:

```text
historical rule
repeal/currentness instrument
current-law basis
```

The repeal or current-law identifier cannot overwrite the substantive historical source identifier unless the answer mode explicitly asks only for currentness or repeal status.

Primary S3-B row:

```text
MULGA-01
```

## Rule 3: Legacy MULGA Historical Surface Without Relation Chain

Condition:

```text
query/task family indicates genuine MULGA-like historical intent
AND no safe active-source substitution is available
AND relation metadata is absent or incomplete
```

Policy:

```text
claim_family_rewrite_allowed = limited_to_historical_surface
historical_claim_surface_allowed = true
current_law_basis_required = false
repeal_instrument_required = false
```

Behavior:

The answer may preserve historical/MULGA surface, but it must be qualified. It must not claim current active applicability. It must not invent repeal instruments, current-law replacements, or relation-chain facts that are not supported by selected evidence.

Primary S3-B rows:

```text
MULGA-02, MULGA-03, MULGA-04, MULGA-05
```

## Rule 4: Repeal Identifier Surface Guard

Condition:

```text
repeal/currentness instrument exists as support
AND substantive selected source is historical
AND user did not ask only for repeal/currentness
```

Policy:

```text
claim_family_rewrite_allowed = controlled
historical_claim_surface_allowed = true
```

Behavior:

The support instrument may explain status, repeal, or current replacement. It cannot become the main cited source if the question asks for the historical rule itself.

## Rule 5: Current-Law Basis as Support

Condition:

```text
current-law basis exists
AND historical source remains the direct answer source
```

Policy:

```text
current_law_basis_required = depends_on_answer_mode
```

Behavior:

Current-law basis may appear as supporting evidence. It must not erase the historical source unless the user asks only for current law.

## Manual Review Bucket

`UY-01` is not a temporal overapplication design target by itself. Its S3-B state is a document/family boundary issue:

```text
benchmark_family = UY
selected_source_family = KKY
claimed_source_family_current = YONETMELIK
```

It should remain `manual_review_required` until a separate family/document identity remediation determines whether `UY`, `KKY`, or `YONETMELIK` is the correct canonical surface.

## S4 Implementation Constraints

S4 implementation must not use QID-specific branches. The rules must be expressed through source metadata, relation-chain state, query/task family, and selected evidence state.

S4 must not change retrieval, top-k, model, prompt, live `8000`, base collections, productization state, or fine-tuning state unless a later brief explicitly opens those scopes.

S4 should expose policy trace fields only for observability. Trace fields must not become acceptance shortcuts.

## S4 Smoke Plan

Recommended gate sequence:

| Gate | Scope | Required outcome |
|---|---|---|
| Policy unit tests | Rule 1 through Rule 5 | Expected permission booleans for each bucket. |
| 13-row targeted policy smoke | S3-B row set | Active non-MULGA rows cannot claim `MULGA`; MULGA rows retain a historical surface path. |
| P0 relation guard smoke | Existing P0 relation set | `MULGA >= 4/5`, `TEBLIGLER >= 6/8`, `TEB-06 = PASS`, `repealed_as_active_count = 0`. |
| Regression guard | Prior successful families | No new source/binding collisions, unsupported/confident counters remain zero. |
| Full benchmark | Only after earlier gates pass | Report pass/fail without productization. |

## Stop Rules

S4 must stop before full benchmark if any of these fail:

```text
active non-MULGA overapplication row claims MULGA
MULGA guard falls below 4/5
TEBLIGLER guard falls below 6/8
TEB-06 fails
repealed_as_active_count > 0
unsupported/confident/contract/collision safety counters are non-zero
source/binding collision appears
QID-specific branch is required to pass
```

## Productization and Fine-Tuning

Productization remains closed. Fine-tuning remains closed.

Reason:

```text
This is deterministic claim-policy logic. S2 failed because policy permissions were conflated, not because the model needed additional training.
```

## Design Conclusion

Open S4 only as a scoped implementation of the split-policy design above. Do not reopen productization, live cutover, retrieval changes, or fine-tuning from S3.
