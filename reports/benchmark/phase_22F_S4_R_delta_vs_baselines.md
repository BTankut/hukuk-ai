# Phase 22F-S4-R Delta vs Baselines

Date: 2026-05-02

## Scope

Audit-only 100-row comparison of Phase 22F-S4 full shadow against Phase 22A stability and Phase 21F live baseline artifacts. Runtime behavior was not changed.

## Compared Runs

- Phase 21F: `reports/benchmark/runs/20260429T174747Z_phase21F_full`
- Phase 22A: `reports/benchmark/runs/20260430T112106Z_phase22A_stability_full`
- Phase 22F-S4: `reports/benchmark/runs/20260502T0657Z_phase22F_S4_full_shadow_benchmark`

Phase 21F and Phase 22A scored rows are identical for score/pass/family/identifier/failure class fields in this audit, so Phase 22A is the primary baseline table.

## Acceptance

- Rows compared: `100/100`
- New regressions separated: `yes`
- Residual blockers separated: `yes`
- Runtime behavior changed: `no`

## Summary Metrics

| Metric | Phase21F | Phase22A | Phase22F-S4 | Delta vs 22A |
| --- | ---: | ---: | ---: | ---: |
| `raw_score_proxy` | 800.55 | 800.55 | 811.16 | +10.61 |
| `pass_proxy` | 89 | 89 | 89 | +0 |
| `fail_proxy` | 11 | 11 | 11 | +0 |
| `wrong_family` | 6 | 6 | 8 | +2 |
| `wrong_document` | 5 | 5 | 4 | -1 |
| `hallucinated_identifier` | 5 | 5 | 6 | +1 |
| `unsupported_confident_answer` | 0 | 0 | 0 | +0 |
| `answer_contract_invalid` | 0 | 0 | 0 | +0 |

## Delta Class Counts

- `new_regression`: 4
- `existing_failure_unchanged`: 7
- `existing_failure_worse`: 0
- `existing_failure_improved`: 0
- `new_improvement`: 3
- `neutral_change`: 86

## Pass/Fail Regressions

| QID | Phase22A | Phase22F-S4 | Delta | S4 failure classes |
| --- | ---: | ---: | ---: | --- |
| MULGA-05 | 7.25 PASS | 5.45 FAIL | -1.80 | missing_required_content_signal ; wrong_article ; partial_grounding_only |
| TEB-04 | 7.25 PASS | 0.00 FAIL | -7.25 | auto_fail_triggered ; missing_required_content_signal ; partial_grounding_only |
| UY-01 | 8.09 PASS | 6.02 FAIL | -2.07 | missing_required_content_signal ; wrong_family ; hallucinated_identifier ; partial_grounding_only |

## Pass/Fail Improvements

| QID | Phase22A | Phase22F-S4 | Delta | Baseline failure classes |
| --- | ---: | ---: | ---: | --- |
| KANUN-15 | 6.32 FAIL | 7.82 PASS | 1.50 | missing_required_content_signal ; partial_grounding_only |
| MULGA-01 | 0.00 FAIL | 8.37 PASS | 8.37 | auto_fail_triggered ; missing_required_content_signal ; wrong_article ; partial_grounding_only ; insufficient_canonical_span_evidence |
| TEB-06 | 3.25 FAIL | 8.90 PASS | 5.65 | missing_gold_document_signal ; missing_required_content_signal ; wrong_document ; hallucinated_identifier ; partial_grounding_only ; insufficient_canonical_span_evidence |

## Residual Family / Identifier Blockers

| QID | Delta class | Phase22A family/id | S4 family/id | S4 failure classes |
| --- | --- | --- | --- | --- |
| CBKAR-05 | neutral_change | TEBLIGLER / 2008 | TEBLIGLER / 2008 | missing_required_content_signal ; wrong_family ; hallucinated_identifier ; partial_grounding_only |
| CBY-01 | neutral_change | YONETMELIK / 7224 | YONETMELIK / 7224 | missing_required_content_signal ; wrong_family ; hallucinated_identifier ; partial_grounding_only |
| CBY-04 | existing_failure_unchanged | CB_KARARNAME / 11 | CB_KARARNAME / 11 | missing_required_content_signal ; wrong_family ; hallucinated_identifier ; partial_grounding_only |
| KANUN-12 | existing_failure_unchanged | KKY /  | KKY /  | missing_gold_document_signal ; missing_required_content_signal ; wrong_family ; wrong_document ; partial_grounding_only |
| KKY-01 | existing_failure_unchanged | YONETMELIK / 34360 | YONETMELIK / 34360 | missing_required_content_signal ; wrong_family ; hallucinated_identifier ; partial_grounding_only |
| KKY-03 | existing_failure_unchanged | YONETMELIK /  | YONETMELIK /  | missing_gold_document_signal ; missing_required_content_signal ; wrong_family ; wrong_document ; partial_grounding_only |
| TUZUK-04 | new_regression | TUZUK / 859727 m.26 | MULGA / 859727 m.4 | missing_required_content_signal ; wrong_family ; hallucinated_identifier ; partial_grounding_only |
| UY-01 | new_regression | UY / 18757 m.4 | YONETMELIK / 12420 m.4 | missing_required_content_signal ; wrong_family ; hallucinated_identifier ; partial_grounding_only |

## Interpretation

S4 improved raw score by `+10.61` and recovered `KANUN-15`, `MULGA-01`, and `TEB-06`, but introduced three pass-to-fail regressions: `MULGA-05`, `TEB-04`, and `UY-01`.

It also introduced one metric-level regression without a pass/fail transition: `TUZUK-04` gained wrong-family / hallucinated-identifier signals while remaining FAIL.

The full restore blocker is concentrated in family/identifier surface metrics:

```text
wrong_family: 6 -> 8
hallucinated_identifier: 5 -> 6
```

Hard safety counters remain clean; this is not an unsupported/confident-answer or contract-validity failure.
