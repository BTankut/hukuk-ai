# Phase 22F-S Historical Claim Alignment Final Report

Date: 2026-05-01

## Commit SHA List

```text
9cee170 Audit MULGA historical claim contract alignment
f2b45b5 Design historical repealed claim alignment policy
653e95d Implement historical repealed temporal claim alignment
c2ff13b Refine historical temporal alignment surface guard
e7a64b7 Run Phase 22F-S targeted temporal claim smoke
987cf4f Run Phase 22F-S regression guard smoke
087b656 Run Phase 22F-S full shadow benchmark
```

## Audit

Audit artifacts:

```text
reports/benchmark/phase_22F_S_mulga_claim_contract_audit.md
reports/benchmark/phase_22F_S_mulga_claim_contract_audit.csv
```

Audit classified `MULGA-01..05` failures and separated:

```text
relation-chain solvable: MULGA-01
legacy temporal policy / claim-surface solvable: MULGA-02, MULGA-03, MULGA-04, MULGA-05
new corpus/source acquisition required: none
```

## Design

Design artifact:

```text
reports/benchmark/phase_22F_S_temporal_claim_alignment_design.md
```

The design introduced role-aware historical claim handling:

```text
historical_rule_source
repeal_or_currentness_source
current_law_basis_source
```

## Implementation Summary

Runtime changes were limited to allowed Phase 22F-S surfaces:

```text
api-gateway/src/rag/answer_synthesis.py
api-gateway/src/rag/evidence_bundle.py
api-gateway/src/routers/chat.py
api-gateway/tests/test_temporal_claim_alignment.py
```

No retrieval source selection, corpus, model, fine-tuning, prompt top-k, live collection, or live `8000` cutover changes were made.

The implementation:

```text
adds metadata-driven temporal claim alignment
prevents historical/repealed answers from claiming active state
keeps repeal instrument separate from historical substantive rule
surfaces current-law basis only when relation-chain metadata exists
qualifies incomplete chains instead of producing confident current-law claims
avoids QID-specific branches
```

## Trace Fields Added

```text
temporal_claim_alignment_applied
temporal_claim_primary_role
temporal_claim_historical_source_key
temporal_claim_repeal_source_key
temporal_claim_current_basis_source_key
temporal_claim_consistency_status
temporal_claim_missing_reason
```

Additional diagnostic contract fields were also emitted:

```text
temporal_claim_historical_identifier
temporal_claim_repeal_identifier
temporal_claim_current_basis_identifier
```

## Targeted Smoke Result

Report:

```text
reports/benchmark/phase_22F_S_targeted_smoke_report.md
```

Accepted run:

```text
reports/benchmark/runs/phase_22F_S_targeted_smoke_rerun_20260501T203427Z
```

Result:

```text
S-D targeted smoke: PASS
MULGA: 4/5
TEBLIGLER: 6/8
TEB-06: PASS
unsupported_confident_answer_count: 0
answer_contract_invalid_count: 0
repealed_as_active_count: 0
source_key_v2_collision: 0
binding_collision: 0
auto_fail_triggered_count: 0
```

## Regression Guard Result

Report:

```text
reports/benchmark/phase_22F_S_regression_guard_report.md
```

Run:

```text
reports/benchmark/runs/phase_22F_S_regression_guard_20260501T204435Z
```

Result:

```text
S-E regression guard: PASS
CB_GENELGE: 4/4
CB_KARAR: 8/8
YONETMELIK: 9/10
UY focused: 2/2
KANUN relation focused: 3/3
unsupported_confident_answer_count: 0
answer_contract_invalid_count: 0
source_key_v2_collision: 0
binding_collision: 0
```

## Full Shadow Benchmark Result

Reports:

```text
reports/benchmark/phase_22F_S_full_shadow_benchmark_summary.md
reports/benchmark/phase_22F_S_delta_vs_phase22A.md
reports/benchmark/phase_22F_S_decision.md
```

Run:

```text
reports/benchmark/runs/phase_22F_S_full_shadow_20260501T210136Z
```

Result:

```text
S-F full shadow benchmark: FAIL
raw_score_proxy: 796.52 / 1000
pass_proxy: 82 / 100
wrong_family: 16
wrong_document: 4
hallucinated_identifier: 14
unsupported_confident_answer_count: 0
answer_contract_invalid_count: 0
source_key_v2_collision: 0
binding_collision: 0
```

Delta vs Phase 22A:

```text
raw_score_proxy: 800.55 -> 796.52 (-4.03)
pass_proxy: 89 -> 82 (-7)
wrong_family: 6 -> 16 (+10)
hallucinated_identifier: 5 -> 14 (+9)
wrong_document: 5 -> 4 (-1)
```

## Decision

```text
Option B — Targeted/regression pass, full benchmark below productization gate.
```

Phase 22F-S should remain a shadow candidate only.

## Productization Gate Decision

```text
Productization: CLOSED
Controlled cutover: NOT AUTHORIZED
Live 8000: UNCHANGED
Shadow candidate 8018: KEEP FOR ANALYSIS
```

## Fine-Tuning Gate Decision

```text
Fine-tuning: CLOSED
No model changes authorized by Phase 22F-S.
```

## Remaining Risks

Main residual risks:

```text
family over-normalization into MULGA on non-MULGA rows
hallucinated identifier surface increased in full run
TEB-03 and TEB-04 remain wrong-family failures
KANUN/TUZUK/KHK/KKY/UY rows can be over-converted to historical/MULGA claim family
MULGA-05 remains wrong-article despite no active/repealed safety issue
```

Recommended next phase:

```text
Phase 22F-S-R — residual family identity / hallucinated identifier audit
```

Constraints for next phase:

```text
no live cutover
no corpus backfill
no source acquisition
no retrieval top-k changes
no QID-specific branch
no answer-key use
```
