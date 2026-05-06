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

## Current Human Review Requirements
- `TUZUK-05`: exact official source identity is not acquired. Human lawyer/source review is required before any runtime remediation or productization acceptance.
- `TEB-04`: productization requires human/scorer confirmation that the current consolidated KDV General Implementation Communique span is correctly materialized and accepted.

## Current State
- Residual closure is not complete.
- Productization remains blocked.
- No live runtime change was made by this workflow artifact.

