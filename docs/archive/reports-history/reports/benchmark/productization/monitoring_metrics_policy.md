# Monitoring / Metrics Policy

Generated: 2026-05-09

## Scope

This policy defines minimum observability requirements before reviewer-only eval expansion, broad internal eval, serving candidate, or productization.

This policy does not enable monitoring in runtime and does not open reviewer-only eval, internal eval, serving candidate, or productization.

## Required Metrics

| metric | definition | required before reviewer eval | required before internal eval | required before serving candidate |
| --- | --- | --- | --- | --- |
| `request_volume` | Count of requests by endpoint, lane, model, and reviewer/eval mode. | yes | yes | yes |
| `latency_ms` | p50/p95/p99 latency by endpoint and stage where available. | yes | yes | yes |
| `error_rate` | Runtime errors, gateway errors, model errors, and retriever errors. | yes | yes | yes |
| `retrieval_failure_rate` | Requests where retrieval fails, returns empty, or misses required source family. | yes | yes | yes |
| `unsupported_confident_answer_count` | Count of answers that are confident but not sufficiently supported. | yes | yes | yes |
| `answer_contract_invalid_count` | Count of invalid answer contract outputs. | yes | yes | yes |
| `source_collision_count` | `source_key_v2` or binding source key collision count. | yes | yes | yes |
| `manual_review_count` | Count of requests routed or flagged for manual review. | yes | yes | yes |
| `low_confidence_count` | Count of low-confidence/qualified/insufficient-evidence outcomes. | yes | yes | yes |
| `rollback_trigger_metrics` | Events that meet rollback or stop-loss thresholds. | no | yes | yes |
| `privacy_pii_event_count` | PII detected, redaction required, or accidental exposure event count. | yes | yes | yes |
| `verification_fail_count` | Claim-level verification failures by reason. | yes | yes | yes |

## Required Dimensions

Metrics should include these dimensions where practical:

```text
timestamp
request_id
lane
api_version
model_id
collection_id
retrieval_lane
eval_mode
reviewer_mode
source_family
answer_mode
guardrail_result
verification_result
manual_review_flag
privacy_risk_band
```

## Stop / Alert Thresholds

| condition | required response |
| --- | --- |
| `answer_contract_invalid_count > 0` in candidate/eval run | stop run, inspect contract output, do not promote. |
| `unsupported_confident_answer_count > 0` | block promotion and route examples to verification owner. |
| `source_collision_count > 0` | stop promotion and inspect source-key binding. |
| `privacy_pii_event_count > 0` involving unredacted export | stop reviewer/export flow and notify privacy owner. |
| material increase in wrong-source/manual-review rate | hold release and require product/legal review. |
| p95 latency exceeds agreed service threshold | do not open serving candidate until capacity/root cause is reviewed. |
| rollback trigger event fires | execute rollback/incident runbook or no-op rehearsal path as applicable. |

## Dashboard Requirements

Before serving candidate or broad internal eval, a dashboard or equivalent report must show:

- request volume
- latency
- error rate
- retrieval failure rate
- answer contract invalid count
- unsupported confident answer count
- source collision count
- verification fail count
- manual review count
- privacy/PII event count
- rollback trigger events

## Audit Logging Link

Monitoring metrics must be reconcilable with audit log records. The metric aggregate should never be the only evidence for a legally material event; request-level audit records must exist for accepted, downgraded, blocked, and manual-review answers.

## Privacy Rules

Metrics must avoid raw prompt/answer storage unless explicitly approved. Metric labels must not include PII. Use stable IDs and redacted summaries where possible.

## Current State

Monitoring policy status: `defined`.

Runtime enforcement status: `not_evidenced`.

Dashboard status: `not_evidenced`.

Reviewer-only eval status: `not_opened`.

Internal eval status: `closed`.

Serving candidate status: `closed`.

Productization status: `closed`.
