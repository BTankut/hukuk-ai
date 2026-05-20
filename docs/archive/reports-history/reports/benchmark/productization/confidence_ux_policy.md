# Confidence UX Policy

## Scope
The user-facing answer must expose uncertainty honestly while preserving useful legal information when evidence is sufficient.

## Confidence Bands
| band | threshold | required UX |
|---|---|---|
| High | `confidence >= 75` and fully grounded | Direct answer with citations and legal-information disclaimer. |
| Qualified | `40 <= confidence < 75` or partial uncertainty | Answer only supported parts, state uncertainty, and cite evidence. |
| Insufficient evidence | `confidence < 40` or evidence mismatch | Decline to answer substantively and explain missing support. |
| Manual review required | Legal/source identity unresolved | State that the issue requires legal/source review. |
| Source unavailable | Official source missing or not acquired | State source unavailable and do not infer citation. |
| Current-law uncertainty | Repealed or historical material detected | State current-law uncertainty and avoid presenting historical law as current law. |

## Hard Overrides
- Unsupported confident answers are forbidden regardless of numeric confidence.
- Hallucinated legal citations are forbidden regardless of numeric confidence.
- If verification is disabled, product serving cannot rely on confidence UX alone.

## Current State
- Confidence UX is a required product policy but is not evidenced as fully enforced in live runtime.
- Productization remains blocked until enforcement is implemented and validated.
- No live runtime change was made by this policy artifact.
