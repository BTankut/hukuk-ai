# Phase 24HW Feature Isolation Report

Generated: 2026-05-07

## Executive Result

Phase24HW is complete. The feature isolation work found a targeted-smoke-safe subset, but the full benchmark failed against base. No feature integration, no cutover, and no productization should proceed.

Selected full candidate:

- Combination: `HS_HT_HU_recall`.
- Flags: HS `true`, HT `true`, HU recall `true`, HU guard `false`.
- Full score: `742.50/1000`, `77/100 pass`.
- Base reference: `805.09/1000`, `89/100 pass`.
- Decision: fail full gate, redesign required.

## Outputs

Phase outputs:

- A audit: `reports/benchmark/phase_24HW_A_pass_to_fail_regression_audit.md`
- A audit CSV: `reports/benchmark/phase_24HW_A_pass_to_fail_regression_audit.csv`
- B matrix plan: `reports/benchmark/phase_24HW_B_feature_isolation_matrix_plan.md`
- B matrix CSV: `reports/benchmark/phase_24HW_B_feature_isolation_matrix_plan.csv`
- C targeted matrix: `reports/benchmark/phase_24HW_C_targeted_feature_matrix_smoke.md`
- C targeted matrix CSV: `reports/benchmark/phase_24HW_C_targeted_feature_matrix_smoke.csv`
- D full validation: `reports/benchmark/phase_24HW_D_full_candidate_validation.md`
- D full validation CSV: `reports/benchmark/phase_24HW_D_full_candidate_validation.csv`
- D QID deltas: `reports/benchmark/phase_24HW_D_full_candidate_qid_deltas.csv`
- E decision: `reports/benchmark/phase_24HW_E_feature_redesign_decision.md`

Benchmark run directories:

- Targeted matrix runs: `reports/benchmark/runs/phase_24HW_C_*_targeted_smoke`
- Full selected run: `reports/benchmark/runs/phase_24HW_D_HS_HT_HU_recall_full_candidate`

## Key Findings

Targeted smoke:

- `BASE`: `96.26/130`, `9/13 pass`.
- `HS_HT_HU_recall`: `104.83/130`, `11/13 pass`.
- Target rows improved from `2/4 pass` to `4/4 pass`.
- Guard rows stayed flat at `70.91/90`, `7/9 pass`.
- Safety counters stayed zero.

Full run:

- Phase24HW selected improved over Phase24HV all-flags by `+15.11` score and `+3` pass.
- Phase24HW selected remained below Phase24U base by `-62.59` score and `-12` pass.
- It created `16` pass-to-fail regressions versus `4` fail-to-pass recoveries.
- Wrong-document count stayed too high: `15` versus `3` on base.
- Hallucinated-identifier count stayed too high: `19` versus `7` on base.

## Operational State

Live serving was not modified.

- Live health after runs: `127.0.0.1:8000`, lane `phase22f_s7_full_shadow`, api_version `2026-05-03-phase23R-E-benchmark-only-cutover`.
- Candidate port `127.0.0.1:8045` was stopped after matrix and full runs.
- No model, prompt, top-k, answer-key, live lane, or productization changes were made.

## Commits

- `159ff67` Audit Phase 24HW pass-to-fail regressions.
- `1fa5601` Plan Phase 24HW feature isolation matrix.
- `03cc809` Report Phase 24HW targeted feature matrix.
- `883149b` Report Phase 24HW full candidate validation.

## Next Step

Open a redesign phase for constrained source-identity routing. Do not continue with global feature flags.

The redesign should preserve the target recoveries (`KANUN-08`, `TEB-04`, `TUZUK-05`, `YON-05`) without introducing broad full-corpus source-selection regressions.

