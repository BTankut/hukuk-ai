# Access-Control Policy

Generated: 2026-05-09

## Scope

This policy defines minimum access-control requirements for reviewer-only eval preparation, future internal eval, serving-candidate review, productization review, benchmark artifacts, traces, and judicial corpus dry-run artifacts.

This policy does not open reviewer-only eval, internal eval, serving candidate, productization, or public access.

## Roles

| role | description | default access |
| --- | --- | --- |
| `system_admin` | Infrastructure owner responsible for service/network/secrets operations. | Administrative system access; no unrestricted legal-review data export by default. |
| `legal_reviewer` | Human legal reviewer for source identity, current-law status, and legal correctness. | Redacted reviewer packets and cited source excerpts required for assigned review rows. |
| `product_reviewer` | Product/risk reviewer for UX, residual acceptance, and manual-review decisions. | Redacted product reports and reviewer queue summaries. |
| `developer_operator` | Developer/operator maintaining non-live tooling and docs. | Repo/docs/test artifacts; no raw traces or PII unless explicitly approved. |
| `read_only_auditor` | Audit/release reviewer verifying governance artifacts and decisions. | Read-only access to committed governance artifacts and redacted summaries. |
| `external_user` | Any user outside controlled reviewer/operator group. | No access to reviewer-only eval, traces, raw source packages, or internal endpoints. |

## Permissions

| permission | system_admin | legal_reviewer | product_reviewer | developer_operator | read_only_auditor | external_user |
| --- | --- | --- | --- | --- | --- | --- |
| read committed product policy docs | yes | yes | yes | yes | yes | no unless published |
| read redacted reviewer packets | approval_required | assigned_only | assigned_only | no by default | read_only_if_approved | no |
| read raw traces | approval_required | approval_required | no by default | approval_required | no by default | no |
| read raw source packages | approval_required | assigned_only | no by default | approval_required | no by default | no |
| run non-live dry-run scripts | yes | no | no | yes | no | no |
| change live `8000` | separate release approval | no | no | no by default | no | no |
| open eval/serving/product gates | no alone | no | no | no | no | no |
| approve reviewer-only eval opening | no alone | no alone | no alone | no | no | no |

## Allowed Endpoints

Reviewer-only and internal review work may use only explicitly approved non-public endpoints and artifact locations.

Allowed by default:

- committed docs in `reports/benchmark/productization/`
- redacted reviewer packet locations approved by release owner
- non-live dry-run outputs created for judicial intake, if redacted and access scoped

Allowed only with explicit release owner approval:

- non-live candidate endpoints
- raw trace storage
- raw source-acquisition storage
- internal benchmark dashboards

## Forbidden Endpoints

- public product endpoints for unfinished evaluation
- live `8000` for reviewer-only experiments that change routing or configuration
- production Milvus mutation endpoints
- judicial live retrieval endpoints before explicit product approval
- any endpoint that exposes raw traces, raw source packages, or PII to unauthorized users

## Trace Access Rules

- Raw traces are not general review material.
- Reviewers receive redacted row-level packets unless raw trace access is specifically required.
- Raw trace access requires release owner and privacy owner approval.
- Trace excerpts must remove secrets, unrelated prompt text, private tokens, unnecessary host/process data, and PII.
- `trace.jsonl` must not be committed to main PRs.

## Reviewer Access

Reviewer access must be:

- named user only
- role-scoped
- row- or packet-scoped
- time-limited where practical
- logged when raw or sensitive material is accessed
- revoked when review is complete

## Admin Access

System admins may operate infrastructure but must not use admin access as approval to expose legal-review packets, raw traces, or source packages. Admin access to sensitive data requires a task-specific need and audit trail.

## Service Account Access

Service accounts must:

- have least-privilege permissions
- be scoped to a single workload
- avoid broad read access to raw traces/source packages
- rotate secrets according to infra policy
- never be used for human review activity

## Data Export Limits

- Export only redacted rows needed for the review task.
- Do not export full trace files to reviewers by default.
- Do not export raw source packages unless legal/source review requires them.
- Do not export PII-bearing data outside approved storage.
- External sharing requires release owner and privacy owner approval.

## Audit Requirements

Access audit records should capture:

```text
actor
role
timestamp
artifact_or_endpoint
action
approval_reference
data_sensitivity
revocation_due_date
```

## Revocation Process

Access must be revoked when:

- review assignment is complete
- reviewer role changes
- accidental PII exposure is detected
- owner decision closes the review queue
- suspected misuse or credential leakage occurs

Revocation must be recorded with actor, scope, reason, and timestamp.

## Current State

Access-control policy status: `defined`.

Runtime enforcement status: `not_evidenced`.

Reviewer-only eval status: `not_opened`.

Internal eval status: `closed`.

Serving candidate status: `closed`.

Productization status: `closed`.
