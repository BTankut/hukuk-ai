# Phase 22D-B P0 Runtime Remediation Smoke Report

Clean baseline commit before attempted runtime remediation: `45079cf`.

Smoke run with attempted generalized `historical_body_title_bridge` selector patch:

`reports/benchmark/runs/20260501T060414Z_phase22D_p0_smoke`

## Summary

The attempted runtime selector change was rejected and reverted. It was not QID-specific, but it did not satisfy the Phase 22D-B acceptance gate.

| Metric | Result |
| --- | ---: |
| total | 13 |
| raw_score_proxy | 98.30 / 130 |
| pass_proxy | 11 / 13 |
| unsupported_confident_answer_count | 0 |
| answer_contract_invalid_count | 0 |
| source_key_v2_collision_detected_count | 0 |
| binding_source_key_collision_detected_count | 0 |

## P0 Rows

| QID | Result | Decision |
| --- | ---: | --- |
| MULGA-01 | FAIL, 4.17 | Runtime patch rejected. It moved selection to a body-bearing regulation span, but produced mixed claimed-source/family state and remained wrong-family / wrong-article / hallucinated-identifier under scoring. |
| TEB-06 | FAIL, 3.25 | No runtime patch attempted. Selected tebliğ source remains title-only/body-missing and is `corpus_backfill_required`. |

## Go / No-Go

- `MULGA-01`: no safe runtime fix accepted in Phase 22D-B. The attempted generalized bridge is unsafe because it creates a mixed source identity contract.
- `TEB-06`: corpus materialization/backfill required; title-only evidence must not be promoted.
- Commit 2 (`Remediate P0 residual source span blockers`) was intentionally skipped because no safe runtime fix survived smoke.

