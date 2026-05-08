# Phase 24HX-B Constrained Routing Design

Generated: 2026-05-08

## Decision

The Phase24HW global feature set must not be shipped. The replacement design is a constrained, traceable, fail-closed routing layer controlled by:

```text
ENABLE_PHASE24HX_CONSTRAINED_ROUTING=true
```

The new router owns whether HS/HT/HU behavior activates. Old broad flags must remain globally off unless the new constrained router explicitly scopes the behavior for a single candidate decision.

## Design Goal

Preserve target recoveries where safe:

- `KANUN-08`
- `TEB-04`
- `TUZUK-05`
- `YON-05`

Prevent broad regressions observed in Phase24HW:

- `KANUN-*` same-document identifier/article drift.
- `CBY-*` cross-family or label drift.
- `KKY-11` KKY/YONETMELIK identity drift.
- `TEB-03` active teblig required-content collapse.
- `UY-07` procedural regulation identity drift.

## Rule 1: Explicit Source-Role Trigger

HS/HT/HU recall may run only when all conditions are true:

- The query, task type, or answer contract requires a distinct source role.
- The current base evidence lacks that required role.
- The candidate source family/domain is compatible with that missing role.

Allowed role triggers:

- `primary_source`
- `supporting_source`
- `exception_source`
- `procedure_source`
- `current_law_basis`
- `historical_source`

No source-role trigger means no replacement. At most, the candidate may be traced as a rejected diagnostic candidate.

## Rule 2: Strong Metadata Identity Lock

A feature candidate may override the base primary only if all conditions are true:

- Candidate metadata identity lock is `strong`.
- Candidate title, identifier, and domain match are stronger than the base primary source.
- Candidate family/domain is compatible with the expected answer role.
- Candidate has article/span support for the requested claim.
- Candidate does not introduce a source-key or binding-key collision.

If the candidate is only `medium` or `weak`, it cannot replace the base primary source.

## Rule 3: Fail-Closed Replacement

If a feature would replace a base-selected canonical document with a lower-confidence, weaker-domain, or cross-domain source:

- Do not replace the base primary source.
- Keep the base primary source in the answer contract.
- Optionally add the feature candidate as supporting evidence if it has a clear role.
- Emit a trace block with `replacement_allowed=false` and an explicit block reason.

Fail-closed is the default. Replacement must be earned by evidence; it is never automatic because a feature flag is enabled.

## Rule 4: Per-Family Guard

Family-specific guards:

- `KANUN`: do not replace one law with another unrelated law unless domain/title/identifier improve together and the article/span remains supported.
- `CBY`: do not allow a CBK or authority/supporting document to become primary `CBY`; supporting source only unless the expected primary family is explicitly CBK.
- `KKY`: do not relabel an ordinary legal `YONETMELIK` as `KKY`; KKY is an alias label unless exact KKY metadata lock exists.
- `TEB`: active teblig primary must not become MULGA or repealed; no replacement if active/repealed state is weaker than base.
- `UY/YON`: KANUN may support but must not overwrite procedural regulation unless the query asks for statutory basis.
- `MULGA`: historical source and current-law basis must remain separate roles.

## Rule 5: Role-Aware Evidence Separation

The answer contract and trace must keep these roles separate:

- `primary_source`
- `supporting_source`
- `exception_source`
- `procedure_source`
- `current_law_basis`
- `historical_source`

Role separation is mandatory because Phase24HW regressions were not only document-selection errors; several were primary/supporting or identifier/article role collapses.

## Replacement Decision Algorithm

For each feature candidate:

1. Start from the base primary source selected by current runtime.
2. Determine the expected role from query signals, task type, and answer contract slot requirements.
3. If no explicit missing role exists, block replacement.
4. Compute candidate family slice and domain compatibility.
5. Compute metadata identity lock strength.
6. Apply the family guard.
7. If candidate is stronger and compatible, allow replacement.
8. If candidate is useful but not replacement-safe, add it as supporting-only evidence.
9. Emit a single `phase24hx_feature_trace` object with the decision and reasons.

## Required Trace Fields

Each candidate evaluation must emit:

```text
phase24hx_feature_trace
source_identity_base_decision
source_identity_feature_candidate
replacement_decision
replacement_block_reason
supporting_evidence_added
family_slice
domain_slice
feature_flags_considered
feature_flags_applied
constrained_routing_applied
constrained_routing_reason
base_primary_source_key
candidate_primary_source_key
candidate_role
replacement_allowed
replacement_block_reason
supporting_only_added
family_slice_guard
domain_compatibility_score
metadata_identity_lock_strength
```

## Acceptance Before Full Benchmark

The prototype can advance to family-slice smoke only if unit tests prove:

- Routing requires an explicit source-role trigger.
- Weak or medium metadata identity cannot replace base primary.
- Cross-family candidates become supporting-only.
- Active teblig is not rewritten as MULGA/repealed.
- Ambiguous tüzük does not select an arbitrary concrete source.
- KANUN same-family replacement requires domain improvement.
- No QID-specific logic exists.

The prototype can advance to full benchmark only if family-slice smoke proves:

- Contract is valid for all rows.
- Unsupported confident answers remain zero.
- Source-key and binding collisions remain zero.
- Target recoveries are retained where possible.
- Regression-slice pass-to-fail count is reduced versus Phase24HW.
- `MULGA-01`, `MULGA-05`, and `TEB-06` do not regress.

## Non-Goals

- No live `8000` change.
- No productization.
- No internal eval.
- No fine-tuning.
- No prompt, model, top-k, answer-key, or QID-specific code changes.
- No large trace commit.

