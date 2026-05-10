# Phase25L-B Guardrails Enforcement Design

Generated: 2026-05-10

## Decision

Design only. Do not enable guardrails on live `8000`.

Recommended product flag:

```text
ENABLE_PRODUCT_GUARDRAILS=false
```

The existing `GUARDRAILS_ENABLED` path is not sufficient as the product control boundary. Product guardrails need a separate default-off decision module so benchmark/runtime hardening guardrails are not confused with product launch controls.

## Runtime Position

Proposed insertion point for Phase25M:

```text
request -> retrieval -> draft answer -> claim verification candidate -> product guardrails decision -> response envelope
```

No model, prompt, top-k, collection, or live route change is part of Phase25L.

## Required Guardrail Cases

| Case | Product decision | Response mode |
|---|---|---|
| unsupported confident answer block | block when answer asserts a legal conclusion without selected evidence | fallback_insufficient_evidence |
| insufficient evidence response | allow only qualified non-confident answer | fallback_insufficient_evidence |
| source unavailable response | block fabricated citation/source references | fallback_source_unavailable |
| current-law uncertainty response | require current-law uncertainty caveat when effective state is not resolved | fallback_current_law_uncertain |
| repealed/historical source warning | allow only with explicit historical/repealed warning | allow_with_warning |
| manual review trigger | flag when legal answer is useful but product evidence gate is incomplete | allow_with_manual_review or block_manual_review |
| legal disclaimer | append stable product disclaimer outside legal reasoning | allow_with_disclaimer |
| confidence threshold policy | abstain below configured confidence threshold | fallback_low_confidence |

## Decision Enum

```text
allow
allow_with_warning
allow_with_disclaimer
allow_with_manual_review
block_insufficient_evidence
block_source_unavailable
block_current_law_uncertain
block_unsupported_confident_answer
block_low_confidence
block_manual_review
error_fail_closed
```

## Fallback Answer Modes

```text
fallback_insufficient_evidence
fallback_source_unavailable
fallback_current_law_uncertain
fallback_low_confidence
fallback_manual_review
fallback_system_error
```

Fallback text must be deterministic, short, non-confident, and citation-safe. It must not invent source names, article numbers, court decisions, or current-law status.

## Non-Live Test Route

Phase25M should add a non-live route only:

```text
POST /internal/product-controls/guardrails/dry-run
```

Constraints:

- requires local/operator access
- not mounted on public/OpenAI-compatible route
- does not mutate live config
- does not call judicial live retrieval
- returns decision enum, fallback mode, trace fields, and audit preview

## Trace Fields

```text
product_guardrails_enabled
product_guardrail_decision
product_guardrail_reasons
product_guardrail_fallback_mode
unsupported_confident_answer_detected
insufficient_evidence_detected
source_unavailable_detected
current_law_uncertainty_detected
historical_repealed_warning_required
manual_review_triggered
legal_disclaimer_applied
confidence_threshold_result
```

## Audit Log Fields

```text
request_id
timestamp
actor_role
endpoint
model_id
collection_id
guardrail_enabled
guardrail_decision
guardrail_reasons
fallback_mode
manual_review_flag
final_mode
latency_ms
error_state
```

## Fail Behavior

Default-off behavior:

- if `ENABLE_PRODUCT_GUARDRAILS=false`, the module does not affect live answers
- dry-run output may be captured only in non-live tests

Enabled product behavior for future Phase25M:

- fail closed for product reviewer/internal eval routes
- never fail closed on current live `8000` unless explicitly authorized in a later cutover phase

## Gate Result

Reviewer-only eval remains blocked until the default-off guardrails module exists, passes non-live smoke tests, and produces trace/audit artifacts without changing live `8000`.
