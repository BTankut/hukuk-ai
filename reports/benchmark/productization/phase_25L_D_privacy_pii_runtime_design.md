# Phase25L-D Privacy / PII Runtime Design

Generated: 2026-05-10

## Decision

Design only. Do not enable product PII enforcement on live `8000`.

Recommended product flag:

```text
ENABLE_PRODUCT_PRIVACY_PII=false
```

Existing PII-related code exists in `guardrails.actions.PresidioMasker` and `release_controls.redact_persisted_payload`, but product runtime needs an explicit privacy decision boundary for query, answer, trace, audit, reviewer access, retention, deletion, and metrics.

## Runtime Position

Proposed insertion points for Phase25M:

```text
request intake -> query PII scan/redaction preview
draft answer -> answer PII scan
trace export -> trace redaction/minimization
audit logging -> audit minimization/redaction
review packet export -> reviewer access filter
```

The module must not alter live `8000` behavior while disabled.

## Required Capabilities

| Capability | Product requirement |
|---|---|
| PII detection | detect TR ID, email, phone, address-like data, names where safe, IP, free-text sensitive personal data signals |
| query redaction | redact persisted query snapshots; preserve minimal routing-safe metadata only |
| trace redaction | remove or hash raw user text and generated raw answer unless explicitly allowed in non-live packet |
| audit log minimization | store only request/accounting/control outcomes; avoid full prompts/answers by default |
| reviewer access limits | legal/product reviewers see only redacted review packets; system admin can access raw only under break-glass process |
| retention policy | default short retention for dry-run traces; no raw trace commit |
| deletion process | request_id/session_id based deletion marker and audit event |
| PII event metrics | count detected/redacted events without exposing values |

## Privacy Decision Enum

```text
disabled
pass_no_pii
pass_redacted
warn_review_redaction
block_sensitive_data_request
block_raw_export
error_fail_closed
```

## Trace Fields

```text
product_privacy_enabled
privacy_decision
pii_detected
pii_entity_types
query_redacted
answer_redacted
trace_redacted
audit_minimized
reviewer_view_redacted
retention_class
deletion_marker_id
```

## Audit Log Fields

```text
request_id
timestamp
actor_role
endpoint
privacy_enabled
privacy_decision
pii_detected
pii_entity_type_counts
redaction_applied
raw_export_blocked
retention_class
deletion_marker_id
error_state
```

Audit logs must not persist raw PII values.

## Reviewer Access Model

| Role | Raw query | Redacted query | Raw trace | Redacted trace | Audit summary |
|---|---:|---:|---:|---:|---:|
| system_admin | break_glass_only | yes | break_glass_only | yes | yes |
| legal_reviewer | no | yes | no | yes | limited |
| product_reviewer | no | yes | no | yes | limited |
| developer_operator | no | yes | no | yes | yes |
| read_only_auditor | no | no | no | no | yes |
| external_user | no | own_response_only | no | no | no |

## Retention Classes

```text
transient_request_only
non_live_redacted_trace_short
product_audit_minimized
manual_review_redacted_packet
break_glass_raw_export
```

Default for Phase25M prototype should be `non_live_redacted_trace_short`.

## Deletion Process

Phase25M should design a non-live deletion marker flow:

1. Locate records by `request_id`, `trace_id`, or `session_id`.
2. Delete or cryptographically tombstone redacted trace artifacts.
3. Preserve minimized audit deletion event without raw content.
4. Emit `privacy_deletion_completed` metric.

## Non-Live Test Route

```text
POST /internal/product-controls/privacy/dry-run
```

This route should accept a query/answer/trace sample and return redaction preview plus privacy trace fields. It must not write raw artifacts unless a test fixture directory is explicitly configured and excluded from commit.

## Gate Result

Reviewer-only eval, internal eval, and serving candidate remain blocked until product PII enforcement exists behind `ENABLE_PRODUCT_PRIVACY_PII=false`, passes dry-run tests, and proves no raw trace/run artifact will be committed.
