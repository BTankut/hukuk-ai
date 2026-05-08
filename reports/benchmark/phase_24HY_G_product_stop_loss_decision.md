# Phase 24HY-G Product Stop-Loss Decision

Generated: 2026-05-08

## Decision

Option C: stop the runtime recovery line and move to product policy / residual acceptance.

## Basis

Phase24HY replacement guard did not produce a safe full-candidate path.

Phase24HY-E result:

- all 29 score/pass: `152.42 / 11`
- target recovery: `3/4`
- regression-slice pass: `1/16`
- wrong_document: `13`, unchanged vs Phase24HX
- hallucinated_identifier: `16`, unchanged vs Phase24HX
- hard counters clean: contract invalid `0`, unsupported confident `0`, source-key collision `0`, binding collision `0`
- critical guard rows `MULGA-01`, `MULGA-05`, `TEB-06`: no regression

The target slice improved, but broad wrong-document and hallucinated-identifier classes did not improve. Regression-slice recovery worsened from Phase24HX `2/16` to Phase24HY `1/16`.

## Stop-Loss Interpretation

The Phase24HY trace showed:

- replacement_attempted: `0/29`
- replacement_allowed: `0/29`
- primary_source_preserved: `29/29`
- dominant block reason: `primary_source_unchanged`

This means the remaining failure is not primarily a candidate replacing a correct base primary source. The problem has moved earlier or deeper: primary source selection, selected span choice, and answer claim-surface drift. Continuing source-selection replacement patches is unlikely to be systemic or safe.

## Closed Paths

- No full benchmark from this candidate.
- No live `8000` cutover.
- No productization opening.
- No internal eval opening.
- No fine-tuning.
- No model, prompt, top-k, or collection change.
- No further source-selection feature work unless the product owner explicitly reopens the line with a new acceptance policy.

## Allowed Next Path

Move to product policy / residual acceptance:

- define which residual failures are acceptable with visible confidence/manual-review policy
- separate product-readiness blockers from benchmark-only residuals
- decide whether remaining wrong-document/hallucinated-identifier classes block pilot use
- if human legal review is required, prepare a targeted packet instead of another runtime patch
