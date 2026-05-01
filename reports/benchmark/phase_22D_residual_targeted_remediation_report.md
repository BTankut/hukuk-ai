# Phase 22D Residual Targeted Remediation Report

## 1. Commit SHA List

| Commit | Purpose |
| --- | --- |
| `45079cf` | Phase 22D-A P0 materialization audit |
| `a861ad0` | Phase 22D-B/C runtime no-go and P1 classification reports |
| `current report commit` | Phase 22D-D full benchmark and final decision report |

## 2. P0 Audit

P0 audit artifacts:

- `reports/benchmark/phase_22D_P0_materialization_audit.md`
- `reports/benchmark/phase_22D_P0_materialization_audit.csv`

| QID | Audit Root Cause | Safe Action |
| --- | --- | --- |
| MULGA-01 | `source_visible_but_not_selected` | `runtime_fix_generalizable` was allowed for a narrow attempt, but the attempted selector bridge failed smoke and was reverted. |
| TEB-06 | `corpus_materialization_backfill_required` | `corpus_backfill_required`; selected 23093 tebliğ spans are title-only/body-missing. |

## 3. P0 Runtime Fix / Corpus Backlog Decision

P0 runtime smoke artifact:

- `reports/benchmark/phase_22D_P0_runtime_remediation_smoke_report.md`

Decision:

- `MULGA-01`: remains unresolved. A generalized `historical_body_title_bridge` selector attempt improved source visibility but produced a mixed source identity contract and still failed; it was reverted.
- `TEB-06`: accepted as corpus backfill required. Runtime must not synthesize from title-only tebliğ evidence.
- Commit 2 was skipped because no safe P0 runtime fix survived smoke.

## 4. P1 Remediation Result

P1 artifacts:

- `reports/benchmark/phase_22D_P1_remediation_report.md`
- `reports/benchmark/phase_22D_P1_remediation_audit.csv`
- Smoke run: `reports/benchmark/runs/20260501T061500Z_phase22D_p1_smoke_clean`

No P1 runtime code change was accepted. All six P1 residuals were classified as unsafe for narrow runtime patching:

| QID | Decision |
| --- | --- |
| CBY-04 | Family-boundary/manual legal review required. |
| KANUN-12 | Wrong document selection; broad KANUN promotion is unsafe. |
| KKY-01 | KKY/YONETMELIK boundary; runtime relabeling would weaken family gates. |
| KKY-03 | Wrong document selection; defer. |
| TUZUK-05 | Tüzük family correct but article-zero/wrong source area remains. |
| YON-04 | Wrong document selection; broad title/domain bias change is unsafe. |

## 5. Full Benchmark Delta vs Phase 22A

Phase 22D full run:

- run: `reports/benchmark/runs/20260501T062248Z_phase22D_full_clean`
- green lane: `reports/benchmark/green_lane/20260501T062248Z_phase22D_full_clean`

| Metric | Phase 22A | Phase 22D | Delta | Gate |
| --- | ---: | ---: | ---: | --- |
| raw_score_proxy | 800.55 | 800.55 | 0.00 | minimum pass, preferred fail |
| pass_proxy | 89/100 | 89/100 | 0 | minimum pass, preferred fail |
| wrong_family | 6 | 6 | 0 | fail target <= 5 |
| wrong_document | 5 | 5 | 0 | fail target <= 4 |
| hallucinated_identifier | 5 | 5 | 0 | fail target <= 4 |
| unsupported_confident_answer | 0 | 0 | 0 | pass |
| answer_contract_invalid | 0 | 0 | 0 | pass |
| source_key_v2_collision | 0 | 0 | 0 | pass |
| binding_source_key_collision | 0 | 0 | 0 | pass |
| green_lane | PASS | PASS | unchanged | pass |

## 6. Residual Backlog After Remediation

Failed rows in Phase 22D full run:

```text
CBY-04
CBY-06
KANUN-12
KANUN-15
KKY-01
KKY-03
MULGA-01
TEB-06
TUZUK-04
TUZUK-05
YON-04
```

P0 status:

- `MULGA-01`: unresolved source/span arbitration blocker.
- `TEB-06`: accepted corpus materialization/backfill backlog.

## 7. Safety Gate Table

| Gate | Result | Status |
| --- | ---: | --- |
| unsupported_confident_answer | 0 | PASS |
| answer_contract_invalid | 0 | PASS |
| green_lane | PASS | PASS |
| source_key_v2_collision | 0 | PASS |
| binding_source_key_collision | 0 | PASS |
| CB_GENELGE | 4/4 | PASS |
| UY | 10/10 | PASS |
| MULGA | 4/5 | PASS minimum |
| TEBLIGLER | 7/8 | PASS preferred |
| YONETMELIK | 9/10 | PASS |
| CB_KARAR | 8/8 | PASS |

## 8. Productization Readiness Recommendation

Do not open productization readiness yet.

Reason: Phase 22D preserved safety and stability, but did not reduce the residual error metrics. `MULGA-01` remains unresolved and target thresholds for wrong family/document/hallucinated identifier were not met.

Recommended next step:

- Open a narrow Phase 22E focused on `MULGA-01`, `TUZUK-04`, `TUZUK-05`, and the KKY/YONETMELIK boundary with explicit corpus/legal review support.

## 9. Fine-Tuning Gate Decision

Fine-tuning remains closed.

The remaining failures are source identity, document selection, corpus materialization, and family-boundary issues. They should not be treated as model-weight problems until corpus/runtime source selection is clean.

## 10. Remaining Risks

- `MULGA-01` requires a safer source identity contract before any historical regulation bridge can be accepted.
- `TEB-06` needs corpus materialization/backfill for body-bearing tebliğ spans.
- KKY/YONETMELIK and CBY/CBK family boundaries need legal taxonomy clarification before runtime relabeling.
- Broad document selection boosts are likely to regress precision; they should not be introduced without family guard smoke and full benchmark rerun.

