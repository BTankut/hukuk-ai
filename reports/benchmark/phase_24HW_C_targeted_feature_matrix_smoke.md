# Phase 24HW-C Targeted Feature Matrix Smoke

Generated: 2026-05-07

## Scope

This report isolates the Phase24HS/HT/HU feature flags on a non-live candidate gateway.

- Live serving endpoint was not modified: `127.0.0.1:8000`, lane `phase22f_s7_full_shadow`, api_version `2026-05-03-phase23R-E-benchmark-only-cutover`.
- Candidate endpoint: `127.0.0.1:8045`.
- Candidate collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`.
- Target QIDs: `TEB-04`, `TUZUK-05`, `YON-05`, `KANUN-08`.
- Guard QIDs: `MULGA-01`, `MULGA-05`, `TEB-06`, `CBY-06`, `KANUN-12`, `YON-04`, `TUZUK-04`, `CBG-01`, `CBKAR-08`.
- A false-start smoke loop produced zero-question run directories because zsh did not split a scalar QID variable. Those directories were removed and replaced by the valid bash-array runs summarized here.

## Matrix Summary

| Combination | HS | HT | HU recall | HU guard | Raw score | Pass | Target score | Target pass | Guard score | Guard pass | Guard regressions | Safety counters | Decision |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| BASE | false | false | false | false | 96.26/130 | 9/13 | 25.35 | 2/4 | 70.91 | 7/9 | 0 | clean | reference only |
| HS_only | true | false | false | false | 99.86/130 | 10/13 | 28.95 | 3/4 | 70.91 | 7/9 | 0 | clean | not eligible, partial target recovery |
| HT_only | false | true | false | false | 96.26/130 | 9/13 | 25.35 | 2/4 | 70.91 | 7/9 | 0 | clean | not eligible, no target improvement |
| HU_recall_only | false | false | true | false | 96.26/130 | 9/13 | 25.35 | 2/4 | 70.91 | 7/9 | 0 | clean | not eligible, no target improvement |
| HU_guard_only | false | false | false | true | 96.26/130 | 9/13 | 25.35 | 2/4 | 70.91 | 7/9 | 0 | clean | not eligible, no target improvement |
| HS_HT | true | true | false | false | 100.54/130 | 10/13 | 29.63 | 3/4 | 70.91 | 7/9 | 0 | clean | not eligible, partial target recovery |
| HS_HT_HU_recall | true | true | true | false | 104.83/130 | 11/13 | 33.92 | 4/4 | 70.91 | 7/9 | 0 | clean | eligible for full, selected |
| HS_HT_HU_guard | true | true | false | true | 100.54/130 | 10/13 | 29.63 | 3/4 | 70.91 | 7/9 | 0 | clean | not eligible, partial target recovery |
| ALL | true | true | true | true | 104.83/130 | 11/13 | 33.92 | 4/4 | 70.91 | 7/9 | 0 | clean | eligible by smoke, not selected because Phase24HV all-flags full failed |

Safety counters are `answer_contract_invalid_count`, `unsupported_confident_answer_count`, `source_key_v2_collision_detected_count`, and `binding_source_key_collision_detected_count`.

## Findings

- `HS_only` fixes `YON-05` from fail to pass without guard regression, but leaves `KANUN-08` failing.
- `HT_only`, `HU_recall_only`, and `HU_guard_only` have no independent effect on this smoke set.
- `HS_HT` improves `KANUN-08` but still fails it.
- `HS_HT_HU_recall` is the minimal safe subset that makes all 4 target QIDs pass while preserving all guard scores.
- `ALL` matches `HS_HT_HU_recall` on this targeted smoke, but it includes `ENABLE_PHASE24HU_EXCEPTION_SLOT_GUARD`, which is not needed for the measured recovery and was part of the Phase24HV all-flags full-candidate failure.

## Full-Run Decision

Proceed to Phase24HW-D full benchmark on `HS_HT_HU_recall` only.

The selected combination is the smallest observed safe recovery path:

- Target score improves from `25.35/40` to `33.92/40`.
- Target pass improves from `2/4` to `4/4`.
- Guard score remains `70.91/90`.
- Guard pass remains `7/9`.
- Safety counters remain zero.

