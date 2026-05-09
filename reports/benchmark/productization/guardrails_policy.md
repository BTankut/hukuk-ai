# Guardrails Policy

## Scope
This policy defines the minimum runtime guardrails required before any internal-eval, serving-candidate, or productization cutover for the mevzuat answer pipeline.

## Required Runtime Behavior
| condition | required behavior |
|---|---|
| Legal advice risk | Add a legal-information disclaimer and avoid attorney-client style advice. |
| Insufficient supported evidence | Return an explicit insufficient-evidence answer instead of a confident answer. |
| Unsupported confident answer | Block or downgrade the answer. Product gate requires count = 0. |
| Hallucinated citation or source | Block the answer and expose a review-safe error state. |
| Source unavailable | State that the source is unavailable and do not invent a citation. |
| Current-law uncertainty | Qualify the answer and identify effective-state uncertainty. |
| Confidence below threshold | Use qualified or insufficient-evidence UX. |
| Manual review trigger | Route the request to manual review when source identity or legal status is unresolved. |

## Confidence And Evidence Rules
- Evidence checks dominate model confidence.
- A high-confidence answer is allowed only when the answer contract is valid, every material claim is supported, and source identity is consistent.
- If retrieval finds candidate material but the material does not support the answer, the correct behavior is abstention or manual review, not answer synthesis.
- Repealed or historical material cannot be presented as current law unless the user explicitly asks for historical law.

## Current Runtime State
- Live health reports `guardrails=disabled`.
- Productization is blocked until guardrails are enabled and a full benchmark shows:
  - `answer_contract_invalid_count = 0`
  - `unsupported_confident_answer_count = 0`
  - no dangerous hallucinated citation accepted as supported evidence
- No live runtime change was made by this policy artifact.

