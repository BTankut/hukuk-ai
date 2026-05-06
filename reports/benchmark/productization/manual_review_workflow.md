# Manual Review Workflow

## Scope
Manual review is required when legal source identity, current-law status, source family, article span, or scorer rubric alignment cannot be resolved automatically with trusted evidence.

## Roles
| role | responsibility |
|---|---|
| Legal reviewer | Confirms legal source identity, effective state, and current-law status. |
| Scorer reviewer | Confirms benchmark rubric, expected source family, and accepted answer criteria. |
| Runtime owner | Applies systemic non-QID-specific remediation after review acceptance. |
| Release owner | Decides whether internal eval, serving candidate, or productization can proceed. |

## Decision Enums
- `accepted`
- `accepted_with_review_note`
- `conditional_acceptance`
- `needs_more_review`
- `rejected`
- `source_not_acquired`
- `rubric_mismatch`
- `blocks_productization`

## Queue Rules
- Every review item must include QID, source family, expected source identifier, exact article/span when known, reviewer decision, evidence path, and SHA-256 when a raw official source file exists.
- Runtime changes must be systemic. QID-specific branches are not allowed.
- Review closure must be recorded before productization.

## Current Human Review Status
- `TUZUK-05`: human lawyer/source review was received on 2026-05-06. Decision: exact single tüzük source is not identifiable from the abstract prompt; scorer should accept the general norm-hierarchy rule and reject the prior `Gıda Maddelerinin... Tüzüğü` candidate.
- `TUZUK-05`: offline scorer policy was implemented after review. Runtime/source-policy validation remains required before any internal eval, serving candidate, or productization gate changes.
- `TEB-04`: human scorer/legal review was received on 2026-05-06. Decision: the current consolidated KDV General Implementation Communique is the product source; confirmed spans were deterministically materialized as non-live artifacts from the verified official GIB PDF and now require gated retrieval/selector validation.

## Current State
- Residual closure is not complete.
- Productization remains blocked.
- No live runtime change was made by this workflow artifact.
