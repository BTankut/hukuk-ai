# Phase 22F-S4 Delta vs Phase 22A

Date: 2026-05-02

## Compared Runs

Baseline:

```text
reports/benchmark/runs/20260430T112106Z_phase22A_stability_full
```

Candidate:

```text
reports/benchmark/runs/20260502T0657Z_phase22F_S4_full_shadow_benchmark
```

## Summary Delta

| Metric | Phase 22A | Phase 22F-S4 | Delta |
| --- | ---: | ---: | ---: |
| raw_score_proxy | 800.55 | 811.16 | +10.61 |
| pass_proxy | 89 | 89 | 0 |
| fail_proxy | 11 | 11 | 0 |
| wrong_family | 6 | 8 | +2 |
| wrong_document | 5 | 4 | -1 |
| hallucinated_identifier | 5 | 6 | +1 |
| unsupported_confident_answer | 0 | 0 | 0 |
| answer_contract_invalid | 0 | 0 | 0 |
| repealed_as_active_count | 0 | 0 | 0 |
| source_key_v2_collision | 0 | 0 | 0 |
| binding_collision | 0 | 0 | 0 |
| green_lane | PASS | PASS | 0 |

## Pass/Fail Movement

New regressions:

| QID | Phase 22A | Phase 22F-S4 | Delta note |
| --- | ---: | ---: | --- |
| MULGA-05 | PASS 7.25 | FAIL 5.45 | wrong_article residual |
| TEB-04 | PASS 7.25 | FAIL 0.00 | auto_fail / grounding completeness residual |
| UY-01 | PASS 8.09 | FAIL 6.02 | wrong_family and hallucinated_identifier residual |

Recovered:

| QID | Phase 22A | Phase 22F-S4 | Delta note |
| --- | ---: | ---: | --- |
| KANUN-15 | FAIL 6.32 | PASS 7.82 | answer completeness improved |
| MULGA-01 | FAIL 0.00 | PASS 8.37 | relation-chain historical claim fixed |
| TEB-06 | FAIL 3.25 | PASS 8.90 | TEB guard recovered |

## Interpretation

S4 improves the raw score and restores important targeted rows, especially `MULGA-01` and `TEB-06`.

However, it does not satisfy the full restore gate because:

```text
wrong_family: 8 > 6
hallucinated_identifier: 6 > 5
```

The safety gates remain clean:

```text
unsupported_confident_answer = 0
answer_contract_invalid = 0
repealed_as_active_count = 0
source_key_v2_collision = 0
binding_collision = 0
green_lane = PASS
```

## Decision Impact

Phase 22F-S4 is a safe shadow candidate but not a cutover candidate.

Recommended next work is residual family/identifier remediation focused on:

```text
CBY-04
KANUN-12
KKY-01
KKY-03
TUZUK-04
UY-01
```

No productization or fine-tuning should open from this result.
