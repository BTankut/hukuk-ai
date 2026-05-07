# Phase 24HU-C Exception Slot Evidence Guard Design

## Goal

Prevent exception/procedure slots from being filled by unrelated same-family or private-law spans when the query asks for implementation, exception, procedure, or norm-chain analysis and a supporting secondary-family route is expected.

## Feature Flag

`ENABLE_PHASE24HU_EXCEPTION_SLOT_GUARD=true`

Default is off.

## Guarded Slots

- `exception_or_limitation`
- `procedure_or_consequence`
- `scenario_applicability` when the query is an exception/procedure task and the candidate evidence is only an unrelated cross-document same-family span

## Rule

For guarded slots:

- Prefer chunks tagged by Phase 24HU as `supporting_source` with a compatible `secondary_family_recall_role`.
- Allow primary-document evidence if it is from the selected primary document and explicitly supports the slot.
- Reject an untagged same-family span from a different document if it is selected only by semantic similarity and no role/domain match exists.
- If no suitable support exists, emit a missing slot with `phase24hu_exception_slot_guard_no_role_matching_evidence`.

## Why This Is Systemic

The guard does not mention QID, expected answer, TKHK, or any specific regulation title. It uses:

- query role signals
- source family metadata
- selected primary document identity
- Phase 24HU supporting-role metadata
- slot-specific text support

## Expected Trace Fields

Each guarded evidence row should include:

- `phase24hu_exception_slot_guard_applied`
- `phase24hu_exception_slot_guard_reason`
- `evidence_source_family`
- `evidence_source_role`

Top-level trace should include:

- `exception_slot_source_key`
- `exception_slot_role`

## Acceptance

For KANUN-08, TBK/private-law spans should not verify the exception slot unless they are explicitly role/domain-matched. If supporting `YONETMELIK` evidence is present, it should be preferred. If it is absent, the exception slot must be missing rather than falsely verified.
