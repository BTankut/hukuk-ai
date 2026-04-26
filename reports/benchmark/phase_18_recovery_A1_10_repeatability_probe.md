# Phase 18 Recovery A1.10 Repeatability Probe

## Scope

- Candidate repeat runs: `reports/benchmark/runs/20260426T_phase18_recovery_A1_10_candidate_smoke20_r1`, `reports/benchmark/runs/20260426T_phase18_recovery_A1_10_candidate_smoke20_r2`
- Live repeat runs: `reports/benchmark/runs/20260426T_phase18_recovery_A1_10_live_smoke20_r1`, `reports/benchmark/runs/20260426T_phase18_recovery_A1_10_live_smoke20_r2`
- QID set: A1.9 20-QID smoke set.
- Runtime logic changed: `no`.
- Candidate and live run provenance git SHA: `542324fe1930ef19f342876f1045468166647f48`.
- Dirty worktree: `true`, justified by pre-existing unrelated dirty/untracked files documented in `phase_18_recovery_A1_10_provenance_lock.md`.

## Acceptance Criteria

- `same_endpoint_pass_delta <= 1`
- `same_endpoint_wrong_document_delta <= 1`
- `same_endpoint_selected_document_match_rate >= 90%`

## Results

| Endpoint | raw r1 | raw r2 | raw delta | pass r1 | pass r2 | pass delta | wrong_family r1 | wrong_family r2 | wrong_document r1 | wrong_document r2 | selected doc match | selected article match | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| candidate 8018 | 144.48 | 144.48 | 0.00 | 16 | 16 | 0 | 1 | 1 | 2 | 2 | 100% | 100% | PASS |
| live 8000 | 140.23 | 140.23 | 0.00 | 15 | 15 | 0 | 0 | 0 | 1 | 1 | 100% | 100% | PASS |

## Drift Detail

### candidate 8018

- PASS/FAIL flips: `none`
- selected_document_id diffs: `none`
- selected_main_article diffs: `none`

### live 8000

- PASS/FAIL flips: `none`
- selected_document_id diffs: `none`
- selected_main_article diffs: `none`

## Decision

Same-endpoint repeatability: `PASS`. Both candidate and live repeat probes were exact on aggregate metrics and selected document/article identity for the 20-QID smoke set.
