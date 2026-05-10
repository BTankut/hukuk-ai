# Phase25L-E Audit Logging and Access-Control Runtime Design

Generated: 2026-05-10

## Decision

Design only. Do not enable product audit logging or product access control on live `8000`.

Recommended product flags:

```text
ENABLE_PRODUCT_AUDIT_LOGGING=false
ENABLE_PRODUCT_ACCESS_CONTROL=false
```

Existing `AUDIT_LOG_ENABLED` and `API_AUTH_ENABLED` support release-control style behavior, but product controls need a role-aware contract, minimized audit schema, and route-level access matrix before eval or serving-candidate phases can open.

## Runtime Position

Proposed insertion points for Phase25M:

```text
request -> access-control middleware -> handler -> product controls -> audit event builder -> minimized audit sink
```

The access-control decision must run before product-control dry-run routes. The audit event builder must run after product-control modules so guardrail, verification, privacy, and manual-review outcomes are logged consistently.

## Required Audit Fields

```text
request_id
timestamp
actor_role
endpoint
model_id
collection_id
retrieved_source_keys
selected_source_keys
guardrail_result
verification_result
privacy_result
manual_review_flag
latency
error_state
```

Recommended additional fields:

```text
api_version
lane
route_class
response_mode
audit_schema_version
redaction_version
retention_class
```

## Audit Event Shape

```json
{
  "audit_schema_version": "product-controls-v1",
  "request_id": "req-...",
  "timestamp": "2026-05-10T00:00:00Z",
  "actor_role": "developer_operator",
  "endpoint": "/internal/product-controls/guardrails/dry-run",
  "model_id": "hukuk-ai-poc",
  "collection_id": "mevzuat-live-or-shadow-id",
  "retrieved_source_keys": [],
  "selected_source_keys": [],
  "guardrail_result": "disabled|allow|block_*",
  "verification_result": "disabled|pass|warn|fail_*",
  "privacy_result": "disabled|pass_no_pii|pass_redacted|block_*",
  "manual_review_flag": false,
  "latency": 0.0,
  "error_state": null
}
```

The audit sink must persist minimized and redacted records only. Raw prompts, raw answers, full traces, raw retrieved chunks, and uploaded judicial documents must not be stored in the audit log.

## Roles

```text
system_admin
legal_reviewer
product_reviewer
developer_operator
read_only_auditor
external_user
```

## Access Matrix

| Route class | system_admin | legal_reviewer | product_reviewer | developer_operator | read_only_auditor | external_user |
|---|---:|---:|---:|---:|---:|---:|
| live chat | yes | yes | yes | yes | no | future_only |
| product-control dry-run | yes | no | no | yes | no | no |
| reviewer-only eval | yes | yes | yes | yes | no | no |
| manual review packet | yes | yes | limited | no | no | no |
| audit summary read | yes | no | no | yes | yes | no |
| raw trace read | break_glass_only | no | no | no | no | no |
| judicial dry-run tooling | yes | no | no | yes | no | no |

## Access Decision Enum

```text
disabled
allow
deny_missing_auth
deny_unknown_role
deny_route_not_allowed
deny_break_glass_required
error_fail_closed
```

## Trace Fields

```text
product_access_control_enabled
actor_role
route_class
access_decision
access_denial_reason
product_audit_logging_enabled
audit_event_id
audit_sink
audit_minimized
audit_redacted
```

## Non-Live Test Routes

Phase25M should add dry-run routes only:

```text
POST /internal/product-controls/access/dry-run
POST /internal/product-controls/audit/dry-run
```

They must require operator-only access, return a preview of the access/audit decision, and avoid live config mutation.

## Gate Result

Reviewer-only eval remains blocked by access control. Internal eval and serving candidate remain blocked by both audit logging and access control until default-off product modules pass non-live tests.
