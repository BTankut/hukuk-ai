# Phase 24HY-B Replacement Guard Design

Generated: 2026-05-08

## Objective

Phase24HY-B defines a systemic replacement guard for source-selection. The guard is fail-closed: a feature candidate may replace the current/base primary source only when the replacement is provably stronger on source identity, family/domain compatibility, role, and article/span support.

This design does not authorize live `8000` changes, productization, internal eval, fine-tuning, model changes, prompt changes, top-k changes, collection overwrite, answer-key use, or QID-specific runtime logic.

## Audit Basis

Phase24HY-A showed that the Phase24HX smoke failures are mostly claim-surface drift rather than clean selected-document replacement:

- audited rows: `29`
- source-replaced rows: `1`
- wrong-document rows: `13`
- hallucinated-identifier rows: `17`
- dominant class: `no_replacement_but_claim_surface_drift`

Therefore the guard must cover both:

- primary-source replacement attempts
- family/identifier/article claim drift when primary source is preserved

## Source Roles

Runtime trace and answer-contract preparation must distinguish these roles before final answer synthesis:

| role | allowed use |
| --- | --- |
| `primary_source` | May be the answer's governing source if all replacement conditions pass. |
| `supporting_source` | May support context, exceptions, procedure, or related-rule slots; must not rewrite primary identity. |
| `exception_source` | May fill exception/limitation slots only. |
| `procedure_source` | May fill procedure/consequence slots only. |
| `current_law_basis` | May explain current-law basis for historical/repealed questions; must not replace historical primary. |
| `historical_source` | May be primary only for explicit historical/repealed scope. |
| `scorer_policy_source` | May document scoring/product policy; must not enter legal answer synthesis as authority. |

## Core Replacement Rule

A candidate may replace the base primary source only if all conditions are true:

1. Candidate metadata identity lock is strong.
2. Candidate family/domain is compatible with the user query and resolved source-family prior.
3. Candidate title, identifier, or domain match is stronger than the base source.
4. Candidate role is `primary_source`, not merely supporting/current-law/historical/procedure/exception.
5. Replacement improves or preserves article/span support.
6. Replacement does not increase ambiguity in claimed family, identifier, or article.

## Fail-Closed Rule

If any condition is missing:

1. Keep the base primary source.
2. Add the candidate only as role-compatible supporting evidence if the role allows it.
3. Otherwise discard the candidate from primary-source selection.
4. Record the block reason in trace.

## Claimed Identifier And Article Preservation

If selected primary source is unchanged:

- claimed source family must remain tied to the selected primary source
- claimed identifier must remain tied to the selected primary source
- claimed article/span must remain tied to the selected primary source
- supporting/current-law/historical evidence may fill secondary slots, but may not mutate the governing-source claim

This directly targets the Phase24HY-A dominant class: `no_replacement_but_claim_surface_drift`.

## Family-Specific Guards

| family slice | guard |
| --- | --- |
| `KANUN` | Same-family replacement requires domain and identity improvement, not merely a generic kanun/family match. |
| `CBY` | Kanun/CB karar/authority material is supporting only unless the query explicitly asks for that source family as primary. |
| `KKY` | Institution-regulation aliases cannot relabel a different primary document without exact title/identifier lock. |
| `TEBLIGLER` | Active tebliğ primary cannot be rewritten by historical/repealed/mülga material. |
| `TUZUK` | Ambiguous hierarchy/norm-conflict questions must not force an arbitrary concrete tüzük identity. |
| `UY`/`YONETMELIK` | Statutory basis can support procedure/current-law slots but cannot become primary unless the query asks for kanun as primary. |
| `MULGA` | Historical primary and current-law basis must remain separated. |

## Trace Contract

Each guarded decision must expose:

```text
phase24hy_replacement_guard
base_primary_source_key
candidate_primary_source_key
replacement_attempted
replacement_allowed
replacement_block_reason
candidate_role
candidate_metadata_lock_strength
candidate_domain_score
base_domain_score
identifier_drift_blocked
article_drift_blocked
supporting_only_added
primary_source_preserved
```

The trace must also preserve the legacy Phase24HX feature trace so Phase24HY can be compared against prior HX/HW runs.

## Non-Live Prototype Boundary

The only runtime feature flag for this phase is:

```text
ENABLE_PHASE24HY_REPLACEMENT_GUARD=true
```

Old broad flags may still exist but must remain mediated by the guard. Phase24HY must not globally activate old broad behavior without the replacement guard evaluating the candidate role, metadata lock, domain score, and article/span preservation.

## Stop Conditions

Stop the prototype or keep it diagnostic-only if any of these occur:

- live `8000` would be modified
- QID-specific code is required
- benchmark answer key is required for code changes
- answer contract invalid appears
- unsupported confident answer appears
- source-key or binding collision appears
- `MULGA-01`, `MULGA-05`, or `TEB-06` regresses
- wrong-document explosion persists in family-slice smoke
- large trace artifacts are staged

## Expected Outcome

The guard should reduce wrong-document and hallucinated-identifier counts versus Phase24HX by blocking weak replacement and claim drift. If it does not, the correct Phase24HY outcome is not more runtime patching; it is a stop-loss decision to move from runtime recovery to product policy/residual acceptance.
