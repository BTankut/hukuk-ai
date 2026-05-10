# Phase25M-D Mainline Product Controls Implementation Readiness

Generated: 2026-05-10

## Decision

```text
implementation_may_start_from_main = true
implementation_must_not_start_from_hardening = true
live_enablement = false
```

The next product-control implementation may start from `origin/main` on a new purpose-specific branch. It must not start from the hardening branch and must not copy failed runtime recovery code into mainline.

Recommended branch:

```text
bt/mainline-product-controls-prototype
```

## Readiness Matrix

Detailed matrix:

```text
reports/benchmark/productization/phase_25M_mainline_D_product_controls_implementation_readiness.csv
```

Control components:

- product_guardrails
- claim_verification
- privacy_pii_redaction
- audit_event_schema
- access_control_decision
- non_live_smoke_harness

## Main Policy Baseline

Policy docs available on main:

- `guardrails_policy.md`
- `verification_policy.md`
- `privacy_pii_policy.md`
- `audit_logging_policy.md`
- `access_control_policy.md`
- `trace_exposure_policy.md`
- `manual_review_workflow.md`
- `confidence_ux_policy.md`
- `artifact_retention_and_trace_exclusion_policy.md`

## Required Default-Off Flags

```text
ENABLE_PRODUCT_GUARDRAILS=false
ENABLE_PRODUCT_CLAIM_VERIFICATION=false
ENABLE_PRODUCT_PRIVACY_PII=false
ENABLE_PRODUCT_AUDIT_LOGGING=false
ENABLE_PRODUCT_ACCESS_CONTROL=false
ENABLE_PRODUCT_CONTROLS_DRY_RUN=false
```

These flags must default to false in code. They must not be enabled in live config during the prototype phase.

## Implementation Boundary

Allowed in the future implementation branch:

- new `api-gateway/src/product_controls/` modules
- new unit tests for decision modules
- internal dry-run router behind `ENABLE_PRODUCT_CONTROLS_DRY_RUN=false`
- config additions for default-false flags
- non-live smoke tests

Forbidden:

- live `8000` behavior change
- public/OpenAI-compatible route change
- model, prompt, top-k, retriever, or collection change
- source-selection residual patch
- hardening recovery code import
- judicial live retrieval
- mevzuat/yargı collection merge
- production index
- trace/run/raw artifact commit

## Minimum Test Gate for Implementation Branch

Future implementation branch must include:

- unit tests for guardrail decision enum and fallback modes
- unit tests for claim-to-evidence verification outcomes
- unit tests for PII redaction/minimization
- unit tests for audit event schema with no raw prompt persistence
- unit tests for access decision matrix
- smoke test proving internal dry-run route is disabled by default
- smoke test proving no public route changes when flags are false

## Readiness Result

Mainline product controls implementation is ready to start as a new branch from `origin/main`, but live enablement and eval entry remain closed.
