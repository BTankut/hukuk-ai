# Phase 18 Recovery A1.9 Candidate / Live Comparison

## Compared Runs

Candidate reference:

- run_dir: `reports/benchmark/runs/20260425T_phase18_recovery_A1_8_full_candidate_rerun_after_mulga_fix`
- api_url: `http://127.0.0.1:8018/v1`
- collection: `mevzuat_faz1_shadow_20260418_compat1024`
- model: `hukuk-ai-poc`
- dgx_model_env: `/models/merged_model_fabric_stage_20260321`

Live full:

- run_dir: `reports/benchmark/runs/20260426T_phase18_recovery_A1_9_live_full100`
- api_url: `http://127.0.0.1:8000/v1`
- collection: `mevzuat_faz1_shadow_20260418_compat1024`
- model: `hukuk-ai-poc`
- dgx_model_env: `/models/merged_model_fabric_stage_20260321`

## Equivalence Metrics

The A1.9 brief requires:

- `raw_score delta <= 10`
- `pass delta <= 2`
- `wrong_family delta <= 2`
- `wrong_document delta <= 2`

| Metric | A1.8 Candidate | A1.9 Live | Live - Candidate | Abs Delta | Tolerance | Status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| raw_score_proxy | 766.48 | 756.61 | -9.87 | 9.87 | <= 10 | PASS |
| pass_proxy | 80 | 79 | -1 | 1 | <= 2 | PASS |
| wrong_family | 11 | 10 | -1 | 1 | <= 2 | PASS |
| wrong_document | 12 | 9 | -3 | 3 | <= 2 | FAIL |

## Interpretation

The live run passed the hard quality gate, and the `wrong_document` count improved from `12` to `9`. However, the A1.9 brief defines the candidate/live comparison as an equivalence check, not only a regression check. The absolute `wrong_document` delta is `3`, above the allowed `<=2` tolerance.

This means the live `8000` behavior is materially different from the A1.8 candidate run even though the aggregate quality did not regress.

## Row-Level Drift

Observed PASS/FAIL flips:

| Direction | QIDs |
| --- | --- |
| Candidate PASS, live FAIL | `CBY-01`, `CBY-06`, `KANUN-15`, `TEB-01`, `TEB-03`, `YON-05` |
| Candidate FAIL, live PASS | `CBY-03`, `KHK-06`, `KKY-02`, `KKY-04`, `YON-03` |

Selected family-level movement:

| Family | Candidate Pass / Count | Live Pass / Count | Delta |
| --- | ---: | ---: | ---: |
| CB_YONETMELIK | 4 / 6 | 3 / 6 | -1 |
| KANUN | 20 / 21 | 19 / 21 | -1 |
| KHK | 5 / 6 | 6 / 6 | +1 |
| KKY | 7 / 11 | 9 / 11 | +2 |
| TEBLIGLER | 6 / 8 | 4 / 8 | -2 |
| YONETMELIK | 6 / 10 | 6 / 10 | 0 |
| MULGA | 3 / 5 | 3 / 5 | 0 |

## Comparison Decision

Candidate/live equivalence: `FAIL`.

Because the A1.9 brief requires rollback when candidate/live equivalence is broken, the live full collection cutover was not accepted as the new baseline.
