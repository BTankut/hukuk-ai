# Phase25L-F Non-Live Controls Prototype Plan

Generated: 2026-05-10

## Decision

Plan only. Phase25L does not implement the prototype.

Phase25M may implement non-invasive, default-off, non-live product-control modules. No module may change live `8000`, public chat behavior, model selection, prompt, top-k, retriever, collection binding, source selection, or judicial corpus routing.

## Prototype Components

The component plan is in:

```text
reports/benchmark/productization/phase_25L_F_non_live_controls_prototype_plan.csv
```

Required components:

- guardrails decision module
- claim verification module
- privacy redaction module
- audit event schema
- access-control middleware
- non-live smoke harness

## Proposed File Boundary for Phase25M

```text
api-gateway/src/product_controls/__init__.py
api-gateway/src/product_controls/guardrails.py
api-gateway/src/product_controls/claim_verification.py
api-gateway/src/product_controls/privacy.py
api-gateway/src/product_controls/audit.py
api-gateway/src/product_controls/access.py
api-gateway/src/routers/product_controls.py
api-gateway/tests/test_product_guardrails.py
api-gateway/tests/test_product_claim_verification.py
api-gateway/tests/test_product_privacy.py
api-gateway/tests/test_product_audit.py
api-gateway/tests/test_product_access.py
api-gateway/tests/test_product_controls_dry_run.py
```

This is a future write set only. Phase25L adds no code under these paths.

## Required Feature Flags

```text
ENABLE_PRODUCT_GUARDRAILS=false
ENABLE_PRODUCT_CLAIM_VERIFICATION=false
ENABLE_PRODUCT_PRIVACY_PII=false
ENABLE_PRODUCT_AUDIT_LOGGING=false
ENABLE_PRODUCT_ACCESS_CONTROL=false
ENABLE_PRODUCT_CONTROLS_DRY_RUN=false
```

All flags must default to false in code and environment examples.

## Non-Live Route Plan

If Phase25M implements routes, they must be internal-only:

```text
POST /internal/product-controls/guardrails/dry-run
POST /internal/product-controls/verification/dry-run
POST /internal/product-controls/privacy/dry-run
POST /internal/product-controls/audit/dry-run
POST /internal/product-controls/access/dry-run
POST /internal/product-controls/smoke
```

Route constraints:

- not OpenAI-compatible
- not public
- operator-only
- no live config mutation
- no production index
- no judicial live retrieval
- no mevzuat/yargı merge
- no trace/run/raw artifact commit

## Smoke Harness Requirements

Minimum Phase25M smoke cases:

| Smoke case | Expected result |
|---|---|
| unsupported answer without selected evidence | guardrails block preview |
| selected source mismatch | verification fail preview |
| repealed source with no warning | guardrails warning/block preview |
| query with TR ID number | privacy redaction preview |
| reviewer role accesses dry-run route | access deny preview |
| operator role accesses dry-run route | access allow preview |
| audit preview event | minimized schema with no raw prompt |

## Blocking Status

Reviewer-only eval remains blocked until:

1. default-off modules exist
2. dry-run routes are internal-only
3. all non-live smoke tests pass
4. trace and audit outputs are redacted/minimized
5. owner explicitly authorizes reviewer-only eval entry

Internal eval and serving candidate remain blocked until the same controls are promoted through a later explicit gate.
