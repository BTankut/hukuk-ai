# Phase 24D Internal-Eval Blocker Closure Plan

Generated: 2026-05-03T10:48:00Z

Scope: define minimum closure requirements for the five residual rows marked `blocks_internal_eval` in Phase 23R-E7 / Phase 24A.

Inputs:

- `reports/benchmark/phase_23R_E7_residual_risk_register_post_cutover.csv`
- `reports/benchmark/phase_24A_residual_triage.csv`
- `reports/benchmark/phase_24B_legal_scorer_review_packet.csv`
- `reports/benchmark/phase_24C_residual_corpus_backfill_plan.csv`

No runtime behavior was changed.

## Closure Plan

| QID | Current Blocker | Minimum Closure Condition | Owner | Estimated Path | Can Be Accepted As Residual For Internal Eval | Must Fix Before Internal Eval |
|---|---|---|---|---|---|---|
| KANUN-12 | Wrong family/document; selected nuclear regulation instead of internet/BTK legal source chain; answer suppressed for evidence gap. | Shadow run selects 5651/legal source chain with article/span support, or legal review explicitly accepts a different source chain. | corpus_engineer + legal_reviewer | source identity repair in shadow, residual diagnostic, full benchmark rerun | false | true |
| KKY-03 | Wrong family/document; selected nuclear regulation instead of banking/KVKK/public-info-security source chain; answer suppressed. | Shadow run selects banking information systems regulation and required companion sources with grounded spans, or legal review narrows expected source. | corpus_engineer + legal_reviewer | source identity repair in shadow, KKY/YONETMELIK taxonomy review, residual diagnostic | false | true |
| TEB-04 | Auto-fail despite selecting KDV Genel Uygulama Tebliği; rubric/completeness policy unresolved. | Legal/scorer review determines whether consolidated KDV tebliğ m.0 is acceptable and auto-fail condition is removed or accepted by documented rubric decision. | scorer_owner + legal_reviewer | legal/scorer packet return, rubric decision, shadow score check | false | true |
| TUZUK-05 | Wrong document/article-zero fallback for hierarchy-conflict tüzük question; expected source not safely established. | Legal review identifies expected valid tüzük/hierarchy rule source and shadow run retrieves/materializes the correct source/span. | legal_reviewer + corpus_engineer | legal source confirmation, official source check, shadow materialization, residual diagnostic | false | true |
| YON-04 | Wrong nuclear regulation selected for personal-data destruction/periodic deletion question; answer suppressed. | Shadow run selects Kişisel Verilerin Silinmesi/Yok Edilmesi/Anonim Hale Getirilmesi Yönetmeliği with required article/span support. | corpus_engineer + legal_reviewer | source identity repair in shadow, span recall/materialization, residual diagnostic | false | true |

## Gate Implication

Current internal-eval blocker status: NOT CLOSED.

All five blocker rows require `must_fix_before_internal_eval=true`. No row is accepted as residual for internal_eval at this time.

## Acceptance Check

| Requirement | Evidence | Result |
|---|---|---|
| All five blocker rows covered | KANUN-12, KKY-03, TEB-04, TUZUK-05, YON-04 present | PASS |
| Each row has must_fix or accepted_with_risk decision | All five are `must_fix_before_internal_eval=true` | PASS |
| Runtime change absent | Report-only phase | PASS |

## Decision

Phase 24D closure plan status: PASS.

Internal eval is not ready until these five blockers are closed or separately accepted by an explicit legal/master-planner decision.
