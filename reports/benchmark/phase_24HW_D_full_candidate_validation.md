# Phase 24HW-D Full Candidate Validation

Generated: 2026-05-07

## Scope

Phase24HW-C found one minimal smoke-safe combination: `HS_HT_HU_recall`.

The full benchmark was run on a non-live candidate gateway only.

- Candidate endpoint: `127.0.0.1:8045`.
- Candidate lane: `phase24hw_HS_HT_HU_recall_full`.
- Candidate collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`.
- Flags: `ENABLE_PHASE24HS_FAMILY_DOMAIN_GATE=true`, `ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING=true`, `ENABLE_PHASE24HU_SECONDARY_FAMILY_RECALL=true`, `ENABLE_PHASE24HU_EXCEPTION_SLOT_GUARD=false`.
- Full run dir: `reports/benchmark/runs/phase_24HW_D_HS_HT_HU_recall_full_candidate`.
- Live endpoint was not modified: `127.0.0.1:8000`, lane `phase22f_s7_full_shadow`, api_version `2026-05-03-phase23R-E-benchmark-only-cutover`.

## Result

| Run | Score | Pass | Wrong document | Hallucinated identifier | Hallucinated source | Contract invalid | Unsupported confident | Source key collision | Binding collision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Phase24U base | 805.09/1000 | 89/100 | 3 | 7 | 3 | 0 | 0 | 0 | 0 |
| Phase24HV all flags | 727.39/1000 | 74/100 | 18 | 22 | 18 | 0 | 0 | 0 | 0 |
| Phase24HW selected | 742.50/1000 | 77/100 | 15 | 19 | 15 | 0 | 0 | 0 | 0 |

## Gate Decision

Full gate fails. Do not integrate or cut over the selected Phase24HW feature subset.

Rationale:

- The selected subset improves over Phase24HV all-flags by `+15.11` score and `+3` pass, but remains below Phase24U base by `-62.59` score and `-12` pass.
- It produces `16` pass-to-fail regressions versus base and only `4` fail-to-pass recoveries.
- Wrong-document count remains `15`, versus `3` on base.
- Hallucinated-identifier count remains `19`, versus `7` on base.
- Hard safety counters remain clean, but quality and source-identity regressions are too large for integration.

## Pass/Fail Delta

The detailed QID delta list is in `reports/benchmark/phase_24HW_D_full_candidate_qid_deltas.csv`.

Fail-to-pass versus base:

- `KANUN-08`
- `TEB-04`
- `TUZUK-05`
- `YON-05`

Pass-to-fail versus base:

- `CBKAR-06`
- `CBY-01`
- `CBY-02`
- `CBY-04`
- `KANUN-04`
- `KANUN-05`
- `KANUN-06`
- `KANUN-11`
- `KANUN-14`
- `KANUN-16`
- `KANUN-17`
- `KANUN-18`
- `KANUN-20`
- `KKY-11`
- `TEB-03`
- `UY-07`

## Interpretation

Targeted smoke was necessary but not sufficient. `HS_HT_HU_recall` correctly recovers the known target rows, but the same family/source-identity behavior broadly degrades unrelated full-corpus rows, especially legal code and institutional/regulatory families.

The next step is a redesign decision, not integration.

