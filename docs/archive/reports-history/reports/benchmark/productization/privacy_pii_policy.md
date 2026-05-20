# Privacy And PII Policy

## Scope
This policy defines minimum privacy controls for user prompts, generated answers, benchmark traces, manual review packets, and runtime logs.

## Required Controls
| area | requirement |
|---|---|
| PII detection | Detect obvious person, contact, identity, address, financial, and sensitive case data before storing or sharing traces. |
| Query logging | Minimize raw query retention. Store stable IDs and redacted summaries where possible. |
| Trace redaction | Redact PII before external sharing or legal/scorer review unless explicit review scope requires raw text. |
| Manual reviewer access | Limit access to named reviewers and only to rows required for review. |
| Retention | Define retention duration for raw queries, trace files, and review packets before productization. |
| Deletion | Provide a deletion path for user-provided data and review exports. |
| Secrets | API keys, hostnames with credentials, and internal tokens must not appear in committed artifacts. |

## Productization Rule
- Productization is blocked if privacy/PII controls are disabled or undocumented in runtime operation.
- Benchmark trace artifacts are not a substitute for privacy controls.

## Current Runtime State
- Presidio or equivalent PII enforcement is not evidenced as enabled in the live health contract.
- Productization is blocked until privacy controls are enabled or a formal written waiver exists.
- No live runtime change was made by this policy artifact.

