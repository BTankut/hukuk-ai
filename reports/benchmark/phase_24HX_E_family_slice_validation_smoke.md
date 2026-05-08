# Phase 24HX-E Family-Slice Validation Smoke

Generated: 2026-05-08

## Scope

Non-live candidate smoke was run on `127.0.0.1:8045`.

Flags:

```text
ENABLE_PHASE24HX_CONSTRAINED_ROUTING=true
ENABLE_PHASE24HS_FAMILY_DOMAIN_GATE=false
ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING=false
ENABLE_PHASE24HU_SECONDARY_FAMILY_RECALL=false
ENABLE_PHASE24HU_EXCEPTION_SLOT_GUARD=false
```

Candidate collection:

```text
mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
```

Run directory:

```text
reports/benchmark/runs/phase_24HX_E_family_slice_validation_smoke
```

Live `8000` was not modified.

## Result

| Slice | Base | Phase24HW selected | Phase24HX constrained |
| --- | ---: | ---: | ---: |
| All 29 rows score/pass | 214.40 / 23 | 153.59 / 11 | 160.64 / 11 |
| Target 4 rows score/pass | 10.45 / 0 | 33.92 / 4 | 25.35 / 2 |
| Regression 16 rows score/pass | 133.04 / 16 | 48.76 / 0 | 64.38 / 2 |
| Guard 9 rows score/pass | 70.91 / 7 | 70.91 / 7 | 70.91 / 7 |

Hard counters:

- `contract_invalid=0`
- `unsupported_confident_answer=0`
- `source_key_v2_collision=0`
- `binding_collision=0`

Critical guard rows:

- `MULGA-01`: no regression.
- `MULGA-05`: no regression.
- `TEB-06`: no regression.

## Acceptance Check

Passed:

- Contract-valid and hard safety counters clean.
- `MULGA-01`, `MULGA-05`, and `TEB-06` did not regress.
- `TEB-04` recovery retained.
- `TUZUK-05` recovery retained.
- Regression-slice pass count improved from `0/16` in Phase24HW selected to `2/16`.

Failed:

- `YON-05` recovery was not retained.
- `KANUN-08` recovery was not retained.
- Wrong-document count in the 29-row smoke remained high: base `2`, Phase24HW `13`, Phase24HX `13`.
- Hallucinated-identifier count remained high: base `4`, Phase24HW `15`, Phase24HX `16`.
- Regression-slice recovery was too small: only `CBKAR-06` and `CBY-01` returned to pass.

## Gate Decision

Phase24HX-E fails the family-slice gate.

Do not run Phase24HX-F full candidate benchmark.

Reason: the stop rule `wrong_document explosion persists in family-slice smoke` is met. The constrained prototype is safer than global HS/HT/HU in target-independent guard rows, but it does not solve the source-selection over-application problem enough to justify a full 100-question candidate run.

Detailed row-level smoke results are in `reports/benchmark/phase_24HX_E_family_slice_validation_smoke.csv`.

