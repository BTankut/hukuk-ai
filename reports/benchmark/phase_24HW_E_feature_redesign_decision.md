# Phase 24HW-E Feature Redesign Decision

Generated: 2026-05-07

## Decision

Decision: scoped redesign required. No integration, no cutover, no productization.

The selected targeted-smoke subset `HS_HT_HU_recall` recovered the known target rows, but failed the full benchmark gate:

- Phase24U base: `805.09/1000`, `89/100 pass`.
- Phase24HV all-flags candidate: `727.39/1000`, `74/100 pass`.
- Phase24HW selected subset: `742.50/1000`, `77/100 pass`.

The selected subset improves over the prior all-flags failure, but remains materially below base with `16` pass-to-fail regressions versus only `4` fail-to-pass recoveries.

## What Was Isolated

- `ENABLE_PHASE24HS_FAMILY_DOMAIN_GATE` is necessary for `YON-05` recovery in the targeted smoke.
- `ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING` is not independently useful on the targeted smoke, but contributes to the `KANUN-08` path when combined with HS and HU recall.
- `ENABLE_PHASE24HU_SECONDARY_FAMILY_RECALL` is only useful in the `HS_HT_HU_recall` interaction.
- `ENABLE_PHASE24HU_EXCEPTION_SLOT_GUARD` is not needed for the measured target recovery and should remain disabled.

## Failure Mode

The problem is not a hard contract failure:

- `answer_contract_invalid_count=0`.
- `unsupported_confident_answer_count=0`.
- `source_key_v2_collision_detected_count=0`.
- `binding_source_key_collision_detected_count=0`.

The failure is source-identity and document-selection over-application:

- Wrong-document count rises from `3` on base to `15` on Phase24HW selected.
- Hallucinated-identifier count rises from `7` on base to `19`.
- The regressions concentrate in rows unrelated to the targeted recovery set, especially `KANUN-*`, `CBY-*`, `KKY-11`, `TEB-03`, and `UY-07`.

## Redesign Direction

Do not ship the current flags globally.

The next implementation should redesign the recovery as a constrained routing rule instead of a broad runtime feature:

- Apply HS/HT/HU-recall only when the query has explicit source-role or same-family intent and the metadata identity lock is strong.
- Fail closed when the feature would replace a base-selected canonical document with a lower-confidence document.
- Add a per-family guard that blocks code-family regressions unless the candidate improves canonical source identity and article/span support simultaneously.
- Track feature attribution in trace fields so full regressions can be tied to the exact gate, score boost, or recall expansion.
- Require family-slice validation before any full benchmark candidate is considered eligible.

## Human Legal Review

Human legal review is not required for this decision.

The blocker is technical source selection, not uncertainty about legal correctness of a specific source or provision.

