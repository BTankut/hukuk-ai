# Phase 24HY-E Family-Slice Validation Smoke

Generated: 2026-05-08

## Scope

Non-live candidate smoke was run on `127.0.0.1:8045` with `ENABLE_PHASE24HY_REPLACEMENT_GUARD=true`. Live `8000` was not modified.

Candidate collection:

```text
mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
```

Run directory:

```text
reports/benchmark/runs/phase_24HY_E_family_slice_validation_smoke
```

## Result

| Slice | Base | Phase24HW selected | Phase24HX constrained | Phase24HY guard |
| --- | ---: | ---: | ---: | ---: |
| All 29 rows score/pass | 214.40 / 23 | 153.59 / 11 | 160.64 / 11 | 152.42 / 11 |
| Target 4 rows score/pass | 10.45 / 0 | 33.92 / 4 | 25.35 / 2 | 28.25 / 3 |
| Regression 16 rows score/pass | 133.04 / 16 | 48.76 / 0 | 64.38 / 2 | 55.06 / 1 |
| Guard 9 rows score/pass | 70.91 / 7 | 70.91 / 7 | 70.91 / 7 | 69.11 / 7 |

Hard counters:

- `contract_invalid=0`
- `unsupported_confident_answer=0`
- `source_key_v2_collision=0`
- `binding_collision=0`

Source-selection counters:

- wrong_document: base `2`, Phase24HX `13`, Phase24HY `13`
- hallucinated_identifier: base `4`, Phase24HX `16`, Phase24HY `16`

Guard trace summary:

- replacement_attempted: `0/29`
- replacement_allowed: `0/29`
- primary_source_preserved: `29/29`
- dominant block reason: `primary_source_unchanged`

Critical guard rows:

- `MULGA-01`: no regression; score `8.37`.
- `MULGA-05`: no regression; score `7.10`.
- `TEB-06`: no regression; score `8.90`.

## Acceptance Check

Passed:

- contract-valid all and API errors 0
- unsupported_confident_answer=0
- answer_contract_invalid=0
- source_key_v2_collision=0
- binding_collision=0
- target recovery count >= 2/4: `3/4`
- MULGA-01/MULGA-05/TEB-06 no regression
- TEB-04 not MULGA/repealed
- TUZUK-05 no arbitrary concrete tüzük

Failed:

- wrong_document not lower: Phase24HX `13`, Phase24HY `13`
- hallucinated_identifier not lower: Phase24HX `16`, Phase24HY `16`
- regression-slice pass count not improved: Phase24HX `2/16`, Phase24HY `1/16`

## Gate Decision

Phase24HY-E fails the family-slice gate.

Do not run Phase24HY-F full candidate benchmark.

Reason: the stop rules `wrong_document explosion persists in family-slice smoke` and `pass-to-fail regressions not reduced vs Phase24HX` are met. The guard improved target recovery from `2/4` to `3/4`, but it did not reduce the full slice wrong-document or hallucinated-identifier classes and it reduced regression-slice pass count from `2/16` to `1/16`.

The trace also shows `replacement_attempted=0/29`; the residual failure is not a classic candidate-over-base replacement. It is primary source selection and answer claim-surface drift before/inside source selection, so another replacement-only runtime iteration is not justified without a different product-policy decision.

Detailed row-level CSV: `reports/benchmark/phase_24HY_E_family_slice_validation_smoke.csv`
