# Phase 22F-S Delta vs Phase 22A

Date: 2026-05-01

## Compared Runs

Baseline:

```text
reports/benchmark/runs/20260430T112106Z_phase22A_stability_full
```

Candidate:

```text
reports/benchmark/runs/phase_22F_S_full_shadow_20260501T210136Z
```

## Summary Delta

| Metric | Phase 22A | Phase 22F-S | Delta |
|---|---:|---:|---:|
| raw_score_proxy | 800.55 | 796.52 | -4.03 |
| pass_proxy | 89 | 82 | -7 |
| fail_proxy | 11 | 18 | +7 |
| wrong_family | 6 | 16 | +10 |
| wrong_document | 5 | 4 | -1 |
| hallucinated_identifier | 5 | 14 | +9 |
| unsupported_confident_answer | 0 | 0 | 0 |
| answer_contract_invalid | 0 | 0 | 0 |
| repealed_as_active_count | 0 | 0 | 0 |
| source_key_v2_collision | 0 | 0 | 0 |
| binding_collision | 0 | 0 | 0 |

## Interpretation

Phase 22F-S achieved the targeted MULGA temporal safety objective:

```text
MULGA targeted: 4/5
repealed_as_active_count: 0
unsupported_confident_answer: 0
answer_contract_invalid: 0
```

But it regressed full-run family identity and identifier surface:

```text
wrong_family: +10
hallucinated_identifier: +9
pass_proxy: -7
raw_score_proxy: -4.03
```

The regression pattern is not a safety failure. It is a productization blocker because the full benchmark falls below the minimum full-run gate.

## Decision Impact

Phase 22F-S should not be cut over.

The candidate can remain available on `8018` for shadow analysis, but live `8000` must stay unchanged.

Recommended next work:

```text
Residual scorer/legal audit focused on family over-normalization into MULGA and non-law family identity preservation.
```
