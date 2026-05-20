# Audit Logging Policy

## Scope
Audit logging must create a minimal, reviewable record for every accepted runtime answer and every blocked answer.

## Required Audit Fields
| field | requirement |
|---|---|
| `request_id` | Stable per request. |
| `timestamp` | UTC timestamp. |
| `model_id` | Served model identity, for example `hukuk-ai-poc` when applicable. |
| `collection_id` | Retrieval collection identity. |
| `retrieved_source_keys` | Source keys returned by retriever. |
| `selected_source_keys` | Source keys used in answer synthesis. |
| `source_key_v2` status | Collision and binding checks. |
| `confidence` | Final confidence and confidence band. |
| `manual_review_flag` | Whether manual review is required. |
| `guardrail_result` | pass, downgrade, block, or unavailable. |
| `verification_result` | pass, fail, or disabled. |
| `error_state` | Contract error, unsupported evidence, source unavailable, or runtime error. |

## Operational Rules
- Large trace files are diagnostic artifacts, not product audit logs.
- Audit logs must be append-only or otherwise tamper-evident before product serving.
- Audit logs must avoid raw PII unless explicitly required and protected by the privacy policy.

## Current Runtime State
- Runtime audit logging is not evidenced as enabled.
- Productization is blocked until audit logging is implemented and smoke-tested.
- No live runtime change was made by this policy artifact.

