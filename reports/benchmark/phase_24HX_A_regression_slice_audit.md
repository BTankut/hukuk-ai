# Phase 24HX-A Regression Slice Audit

Generated: 2026-05-08

## Scope

This audit classifies the `16` Phase24HW full-run pass-to-fail regressions versus the Phase24U base run.

Inputs:

- Base scored file: `reports/benchmark/runs/phase_24U_B_base_trace_on_full_20260505T121226Z/scored.csv`
- Phase24HW selected full scored file: `reports/benchmark/runs/phase_24HW_D_HS_HT_HU_recall_full_candidate/score/scored.csv`
- Phase24HW selected trace file: `reports/benchmark/runs/phase_24HW_D_HS_HT_HU_recall_full_candidate/trace.jsonl`

Live `8000` was not modified.

## Slice Summary

| Slice | Regression count | Dominant failure mode |
| --- | ---: | --- |
| KANUN | 9 | same-document identifier/article drift, plus one wrong-document replacement |
| CBY | 3 | cross-family/label drift and wrong-document replacement |
| KKY | 1 | same-document identifier/article drift |
| TEBLIGLER | 1 | same-document span or required-content loss |
| UY | 1 | same-document identifier/article drift |
| OTHER | 1 | same-document span or required-content loss |

## Feature Attribution From Existing Trace

The existing trace is sufficient to identify broad attribution, but not sufficient for the final Phase24HX requirement because it does not yet expose a single consolidated `phase24hx_feature_trace` object.

Observed regression attribution:

- `HS_family_domain_gate_or_metadata_selector`: 8 regressions.
- `HT_same_family_domain_lock`: 1 regression.
- `baseline_source_identity_interaction`: 7 regressions.
- `HU_secondary_family_recall`: 0 regressions directly applied in these pass-to-fail rows.
- `ENABLE_PHASE24HU_EXCEPTION_SLOT_GUARD`: disabled in the Phase24HW selected full run.

## Key Findings

- The largest regression slice is `KANUN`, with 9 of 16 pass-to-fail rows.
- Most KANUN regressions kept the same selected document but degraded claimed identifier/article or required content, so the redesign must guard not only document replacement but also role/article-level source identity.
- `CBY` regressions show the need to keep CBK/authority documents separate from CBY primary-source identity.
- `TEB-03` and `CBKAR-06` show same-document required-content collapse; a constrained router must not suppress or replace base evidence if it cannot preserve required span support.
- Existing broad flags are too coarse for safe integration; the redesign must be explicit-role-triggered, metadata-lock-gated, and fail-closed.

## Required Blocking Conditions

- `KANUN`: block replacement unless the candidate has strong identity lock plus title/identifier/domain improvement over the base law document.
- `CBY`: block CBK/supporting authority documents from becoming primary CBY source; add them as supporting evidence only.
- `KKY`: preserve base legal regulation identity; use KKY as an alias label only unless exact KKY metadata lock exists.
- `TEBLIGLER`: preserve active teblig primary source; require article/span support before replacement or auto-fail suppression.
- `UY`: require institution/title domain match; do not replace procedural regulation with unrelated university regulation.
- `OTHER`: keep base primary when candidate identity lock is weak or domain compatibility is not stronger.

Detailed row-level audit is in `reports/benchmark/phase_24HX_A_regression_slice_audit.csv`.

