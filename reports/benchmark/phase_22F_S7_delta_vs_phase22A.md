# Phase 22F-S7 Delta vs Phase 22A

## Baselines

- Phase 22A baseline run: `reports/benchmark/runs/20260430T112106Z_phase22A_stability_full`
- Phase 22A metrics source: `reports/benchmark/phase_22F_S_delta_vs_phase22A.md`
- Phase 22F-S7 run: `reports/benchmark/runs/20260502T1858Z_phase22F_S7_full_shadow_benchmark`

## Delta

| Metric | Phase 22A | Phase 22F-S7 | Delta |
| --- | ---: | ---: | ---: |
| raw_score_proxy | 800.55 | 816.86 | +16.31 |
| pass_proxy | 89 | 91 | +2 |
| wrong_family | 6 | 6 | 0 |
| wrong_document | 5 | 4 | -1 |
| hallucinated_identifier | 5 | 4 | -1 |
| unsupported_confident_answer | 0 | 0 | 0 |
| answer_contract_invalid | 0 | 0 | 0 |
| source_key_v2_collision | 0 | 0 | 0 |
| binding_collision | 0 | 0 | 0 |
| repealed_as_active_count | 0 | 0 | 0 |

## Interpretation

Phase 22F-S7 recovers and exceeds Phase 22A on score and pass count while preserving the core safety counters. The remaining limitation is not a hard gate failure: `wrong_family` is unchanged at `6`, which passes the minimum threshold but misses the preferred threshold by one row.

## Residual Focus

- `CBY-04`, `KANUN-12`, `KKY-01`, and `KKY-03` carry the current `wrong_family` burden.
- `TEB-04` now has the intended KDV source identity (`19631`) but still fails proxy due answer-content auto-fail.
- `YON-04`, `TUZUK-05`, `KANUN-12`, and `KKY-03` remain document/source selection residuals.
