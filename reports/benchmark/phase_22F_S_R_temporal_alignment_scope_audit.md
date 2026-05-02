# Phase 22F-S-R-C Temporal Alignment Scope Audit
Audit-only scope review of temporal claim alignment. No runtime behavior was changed.
## Summary
- Rows audited: 100
- Temporal alignment applied: 14
- Relation-chain expansion applied: 1
- Overapplication / wrong-role candidates: 9
- Underapplication candidates: 0
## Scope Decision Counts
- `not_applicable`: 86
- `should_not_have_applied`: 9
- `correctly_applied`: 5
## Overapplication Candidates
- `KANUN-05` (KANUN): selected_effective=active, claimed_effective=repealed, reason=non-MULGA query/source was rewritten to MULGA/repealed without explicit relation-chain metadata
- `KANUN-10` (KANUN): selected_effective=active, claimed_effective=repealed, reason=non-MULGA query/source was rewritten to MULGA/repealed without explicit relation-chain metadata
- `KANUN-14` (KANUN): selected_effective=active, claimed_effective=repealed, reason=non-MULGA query/source was rewritten to MULGA/repealed without explicit relation-chain metadata
- `KANUN-15` (KANUN): selected_effective=active, claimed_effective=repealed, reason=non-MULGA query/source was rewritten to MULGA/repealed without explicit relation-chain metadata
- `KHK-03` (KHK): selected_effective=active, claimed_effective=repealed, reason=non-MULGA query/source was rewritten to MULGA/repealed without explicit relation-chain metadata
- `TEB-03` (TEBLIGLER): selected_effective=active, claimed_effective=repealed, reason=non-MULGA query/source was rewritten to MULGA/repealed without explicit relation-chain metadata
- `TEB-04` (TEBLIGLER): selected_effective=active, claimed_effective=repealed, reason=non-MULGA query/source was rewritten to MULGA/repealed without explicit relation-chain metadata
- `TUZUK-03` (TUZUK): selected_effective=active, claimed_effective=repealed, reason=non-MULGA query/source was rewritten to MULGA/repealed without explicit relation-chain metadata
- `TUZUK-04` (TUZUK): selected_effective=active, claimed_effective=repealed, reason=non-MULGA query/source was rewritten to MULGA/repealed without explicit relation-chain metadata
## Underapplication Candidates
- None under the audit rule.
## Scope Decision
The only explicit relation-chain expansion found in the full shadow run is `MULGA-01`. Most non-MULGA temporal rows had no relation-chain metadata but were still rewritten to `MULGA/repealed`; those should be remediated before any cutover.
