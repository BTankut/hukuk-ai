# Phase 24HW-B Feature Isolation Matrix Plan

## Scope

Non-live feature-flag ablation only. Live `8000` remains untouched. No model, prompt, top-k, collection, productization, internal eval, fine-tuning, or code changes are authorized by this plan.

## Matrix

| Combination | Flags | Expected Target Rows Recovered | Expected Risk | Run Targeted Smoke | Full Run Rule |
| --- | --- | --- | --- | --- | --- |
| BASE | all flags off | none | lowest risk; should reproduce current default behavior on focused set | yes | no |
| HS_only | ENABLE_PHASE24HS_FAMILY_DOMAIN_GATE=true | TEB-04; TUZUK-05; YON-05 | risk: broad family/domain lock over-application | yes | if target rows improve and guards stable |
| HT_only | ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING=true | partial KANUN-08 primary identity support | risk: same-family replacement over-selection | yes | if no guard regression |
| HU_recall_only | ENABLE_PHASE24HU_SECONDARY_FAMILY_RECALL=true | unlikely alone; recall policy requires primary/family signals but no HT support | risk: secondary-family over-recall on general procedure queries | yes | if no guard regression |
| HU_guard_only | ENABLE_PHASE24HU_EXCEPTION_SLOT_GUARD=true | unlikely alone; guard only affects slot filling | low-medium risk: missing slots instead of wrong slots | yes | if no guard regression |
| HS_HT | ENABLE_PHASE24HS_FAMILY_DOMAIN_GATE=true<br>ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING=true | TEB-04; TUZUK-05; YON-05; partial KANUN-08 | risk: HS/HT document-selection interaction | yes | if target rows improve and guards stable |
| HS_HT_HU_recall | ENABLE_PHASE24HS_FAMILY_DOMAIN_GATE=true<br>ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING=true<br>ENABLE_PHASE24HU_SECONDARY_FAMILY_RECALL=true | KANUN-08 plus HS target rows | risk: HU secondary recall over-application | yes | if target rows improve and guards stable |
| HS_HT_HU_guard | ENABLE_PHASE24HS_FAMILY_DOMAIN_GATE=true<br>ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING=true<br>ENABLE_PHASE24HU_EXCEPTION_SLOT_GUARD=true | HS target rows plus guarded exception slots; may not recover KANUN-08 fully | risk: lower than recall; slot-only interaction | yes | if target rows improve and guards stable |
| ALL | ENABLE_PHASE24HS_FAMILY_DOMAIN_GATE=true<br>ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING=true<br>ENABLE_PHASE24HU_SECONDARY_FAMILY_RECALL=true<br>ENABLE_PHASE24HU_EXCEPTION_SLOT_GUARD=true | TEB-04; TUZUK-05; YON-05; KANUN-08 | known risk: full-corpus regression in Phase24HV | yes | no unless used as reference only |

## Targeted Smoke Rows

- Target rows: `TEB-04`, `TUZUK-05`, `YON-05`, `KANUN-08`.
- Guard rows: `MULGA-01`, `MULGA-05`, `TEB-06`, `CBY-06`, `KANUN-12`, `YON-04`, `TUZUK-04`, `CBG-01`, `CBKAR-08`.

## Full-Run Eligibility

A combination is full-run eligible only if targeted rows improve vs BASE/default, critical guards do not regress, contract/safety/collision counters remain zero, and no stop rule triggers.

## Expected Interpretation

If HS-only reproduces broad target recovery without KANUN-08 and no guard regressions, HS may be separable. If KANUN-08 requires HU recall but HU recall causes guard regressions, HU needs redesign before any integration. If ALL is the only target-recovering combination, Phase24HW should reject integration and open scoped redesign.
