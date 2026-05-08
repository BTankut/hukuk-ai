# Phase 24HX-G Integration Decision

Generated: 2026-05-08

## Decision

Decision: Option B/C hybrid.

Keep the constrained routing work as a diagnostic candidate, but do not integrate it. Continue scoped redesign only if the next phase can address source-selection over-application directly.

No live cutover. No productization. No internal eval. No fine-tuning.

## Basis

Phase24HX-D produced a safe fail-closed prototype and passed focused tests.

Phase24HX-E family-slice smoke did not pass the gate:

- `TEB-04` recovery retained.
- `TUZUK-05` recovery retained.
- `YON-05` recovery not retained.
- `KANUN-08` recovery not retained.
- Regression-slice pass improved only from `0/16` to `2/16`.
- Wrong-document count stayed at `13`, versus base `2`.
- Hallucinated-identifier count increased to `16`, versus base `4`.

## Integration Status

Do not open controlled benchmark-only integration.

Reasons:

- Family-slice gate failed.
- Full candidate benchmark was not run.
- The source-selection failure mode remains unresolved.

## Productization Status

Closed.

## Internal Eval Status

Closed.

## Fine-Tuning Status

Closed.

## Next Phase

Recommended next phase: Phase24HY source-selection replacement guard redesign.

The next phase should not broaden HS/HT/HU. It should instead build a deterministic primary-source retention guard that prevents a lower-confidence candidate from changing the primary source or claimed identifier/article when the base document already has adequate support.

