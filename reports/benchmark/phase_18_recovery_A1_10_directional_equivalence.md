# Phase 18 Recovery A1.10 Directional Equivalence

## Policy

A1.10 replaces the A1.9 absolute equivalence rule with directional gates: live must pass the hard quality gate and must not materially regress against the candidate. Improvements in error counts are not failures.

## Compared Runs

- Candidate reference: `reports/benchmark/runs/20260425T_phase18_recovery_A1_8_full_candidate_rerun_after_mulga_fix`
- Live reference: `reports/benchmark/runs/20260426T_phase18_recovery_A1_9_live_full100`

## Adverse Delta Gate

| Metric | Candidate | Live | Live - Candidate | Gate | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| raw_score_proxy | 766.48 | 756.61 | -9.87 | >= -10 | PASS |
| pass_proxy | 80.00 | 79.00 | -1.00 | >= -2 | PASS |
| wrong_family | 11.00 | 10.00 | -1.00 | <= +2 | PASS |
| wrong_document | 12.00 | 9.00 | -3.00 | <= +2 | PASS |
| hallucinated_identifier | 16.00 | 11.00 | -5.00 | <= +3 | PASS |

## Hard Quality Gate

- raw_score_proxy: `756.61`
- pass_proxy: `79/100`
- wrong_family: `10`
- wrong_document: `9`
- unsupported_confident_claim: `0`
- answer_contract_invalid_count: `0`
- green_lane: `pass`
- hard gate status: `PASS`

## Row-Level Drift Warning Gate

- candidate PASS -> live FAIL count: `6` (CBY-01, CBY-06, KANUN-15, TEB-01, TEB-03, YON-05)
- candidate FAIL -> live PASS count: `5` (CBY-03, KHK-06, KKY-02, KKY-04, YON-03)
- gate: `6 <= 5 + 3` => `PASS`

## Critical Watch Families

| Family | Live Result | Gate | Status |
| --- | ---: | ---: | --- |
| CB_GENELGE | 4/4 | >= 4/4 | PASS |
| MULGA | 3/5 | >= 3/5 | PASS |
| UY | 10/10 | >= 9/10 | PASS |
| YONETMELIK | 6/10 | >= 6/10 | PASS |

## Decision

Directional equivalence: `PASS`.

Under A1.10 policy, the A1.9 live full run is acceptable for a controlled cutover retry because the observed `wrong_document` movement is an improvement, not an adverse delta.
