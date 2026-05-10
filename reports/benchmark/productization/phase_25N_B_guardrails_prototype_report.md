# Phase25N-B Product Guardrails Prototype Report

Generated: 2026-05-10

## Decision

PASS - default-off, non-live product guardrails prototype added.

## Files

```text
api-gateway/src/config.py
api-gateway/src/product_controls/__init__.py
api-gateway/src/product_controls/guardrails.py
api-gateway/tests/test_product_guardrails.py
```

## Default-Off Flag

```text
ENABLE_PRODUCT_GUARDRAILS=false
```

`Settings().enable_product_guardrails` defaults to `False`.

## Behaviors Covered

- unsupported_confident_answer
- insufficient_evidence
- source_unavailable
- current_law_uncertainty
- repealed_or_historical_warning
- manual_review_required
- legal_disclaimer_required
- confidence_threshold

## Tests

Command:

```text
cd api-gateway && python3 -m pytest tests/test_product_guardrails.py
```

Result:

```text
5 passed
```

Covered required tests:

- guardrails_default_off
- unsupported_confident_blocks_when_enabled
- insufficient_evidence_returns_safe_mode
- repealed_source_adds_warning
- manual_review_trigger_set

## Live State

The prototype is not imported into the live chat path and no live `8000` config was changed.
