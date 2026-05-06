# Verification Policy

## Scope
Verification must run after retrieval and answer synthesis, before the response is accepted for internal eval, serving candidate, or productization.

## Required Checks
| check | requirement |
|---|---|
| Answer contract schema | Response must satisfy the configured chat answer contract. |
| Claim to evidence map | Each material legal claim must map to selected evidence. |
| Citation consistency | Cited source, article, family, and identifier must match retrieved material. |
| `source_key_v2` collision | Collision count must be 0. |
| Binding source key collision | Collision count must be 0. |
| Source family consistency | `KANUN`, `YONETMELIK`, `TUZUK`, `CB_YONETMELIK`, `TEBLIG`, and related families must not be substituted without an accepted taxonomy rule. |
| Effective state | Current, amended, repealed, historical, and supporting-source status must be explicit. |
| Unsupported claim detector | Unsupported confident answer count must be 0. |
| Hallucinated source detector | Hallucinated source count must be 0 or formally waived before productization. |

## Acceptance Rules
- Internal eval cannot open if verification is absent and residual legal/source blockers remain open.
- Serving candidate cannot open if verification is disabled.
- Productization cannot open if verification is disabled or if any hard verification metric is non-zero.

## Current Runtime State
- Live health reports `verification=disabled`.
- Productization is blocked until verification is enabled and validated through a full benchmark.
- No live runtime change was made by this policy artifact.

