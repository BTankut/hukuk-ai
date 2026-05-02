# Phase 22F-S4-R Residual Remediation Decision

Date: 2026-05-02

## 1. Commit SHA List

| Commit | Purpose |
| --- | --- |
| `9c14e49` | Audit Phase 22F-S4 family identifier residuals |
| `f80285f` | Audit Phase 22F-S4 delta against stable baseline |
| `ef0bc26` | Design Phase 22F-S4 residual remediation |

## 2. Residual Audit Summary

Audit outputs:

```text
reports/benchmark/phase_22F_S4_R_family_identifier_residual_audit.md
reports/benchmark/phase_22F_S4_R_family_identifier_residual_audit.csv
```

Acceptance:

- Rows classified: `11/11`
- Runtime behavior changed: `no`
- New regressions vs Phase22A: `3`
- Pre-existing fail-row residuals: `8`

New pass-to-fail regressions:

```text
MULGA-05
TEB-04
UY-01
```

Metric-level regression without pass/fail transition:

```text
TUZUK-04
```

## 3. Delta vs Baseline Summary

Delta outputs:

```text
reports/benchmark/phase_22F_S4_R_delta_vs_baselines.md
reports/benchmark/phase_22F_S4_R_delta_vs_baselines.csv
```

Compared runs:

```text
Phase21F: reports/benchmark/runs/20260429T174747Z_phase21F_full
Phase22A: reports/benchmark/runs/20260430T112106Z_phase22A_stability_full
S4:       reports/benchmark/runs/20260502T0657Z_phase22F_S4_full_shadow_benchmark
```

Phase21F and Phase22A scored rows are identical for score/pass/family/identifier/failure-class fields in this audit.

Key deltas vs Phase22A:

| Metric | Phase22A | S4 | Delta |
| --- | ---: | ---: | ---: |
| raw_score_proxy | 800.55 | 811.16 | +10.61 |
| pass_proxy | 89 | 89 | 0 |
| fail_proxy | 11 | 11 | 0 |
| wrong_family | 6 | 8 | +2 |
| wrong_document | 5 | 4 | -1 |
| hallucinated_identifier | 5 | 6 | +1 |
| unsupported_confident_answer | 0 | 0 | 0 |
| answer_contract_invalid | 0 | 0 | 0 |

## 4. Root Cause Counts

```text
family_taxonomy_boundary: 3
preexisting_residual: 1
s4_policy_side_effect: 2
source_identity_wrong_document: 5
```

## 5. Safe Action Counts

```text
defer_corpus_backfill: 3
defer_manual_legal_review: 1
defer_scorer_rubric_review: 2
fix_now_generalizable: 4
watch_only: 1
```

## 6. Recommended Next Phase

Decision option: `Option A — Safe deterministic implementation exists`.

Open:

```text
Phase 22F-S5 deterministic family / identifier fix
```

S5 should be narrow and ordered:

1. Active selected non-MULGA historical-surface clamp.
2. Historical article surface guard.
3. UY vs YONETMELIK family-boundary guard, only if trace proof confirms a viable UY candidate is available.
4. TEB domain mismatch guard, only after trace proof confirms the correct KDV tebliğ candidate is already in the candidate pool.

Do not patch these rows in S5 without legal/scorer/corpus review:

```text
CBY-04
KKY-01
KANUN-12
KKY-03
TUZUK-05
YON-04
CBY-06
```

## 7. Productization Gate Decision

Productization remains closed.

Reason:

```text
S4 full restore gate failed:
wrong_family = 8 > 6
hallucinated_identifier = 6 > 5
```

## 8. Fine-Tuning Gate Decision

Fine-tuning remains closed.

Reason:

```text
Residuals are deterministic source-family, identifier-surface, article-surface,
source-identity, legal taxonomy, scorer/rubric, or corpus/materialization issues.
```

No evidence supports opening a training phase.

## 9. Cutover Recommendation

No live cutover.

Keep live `8000` unchanged. Keep `8018` only as a shadow analysis candidate.

## 10. S5 Acceptance Gate

S5 must not attempt full benchmark until targeted gates pass.

Minimum full gate:

```text
raw_score_proxy >= 800
pass_proxy >= 89
wrong_family <= 6
wrong_document <= 5
hallucinated_identifier <= 5
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
green_lane = PASS
```

Hard stop:

```text
live 8000 modified
QID-specific branch introduced
benchmark answer key used
MULGA guard < 4/5
TEBLIGLER guard < 6/8
TEB-06 fails
unsupported_confident_answer > 0
answer_contract_invalid > 0
source_key_v2_collision > 0
binding_collision > 0
```

## Final Decision

S4-R is complete as an audit/design phase.

Proceed to a separate S5 deterministic fix brief. Do not implement fixes under S4-R.
