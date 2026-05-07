# Phase 24HU-B Secondary-Family Recall Design

## Goal

Add a non-live, feature-flagged retrieval path that can bring role-tagged supporting `YONETMELIK` evidence into a primary `KANUN` answer without changing the primary source identity.

## Feature Flag

`ENABLE_PHASE24HU_SECONDARY_FAMILY_RECALL=true`

Default is off.

## Trigger

Run secondary-family recall only when all conditions hold:

- The request is not using `law_filter`.
- The query has source-role signals such as norm-chain, implementation, procedure, exception, limitation, applicability, or scope terms.
- The runtime source-family context contains or implies primary `KANUN`.
- Runtime metadata/query signals indicate `YONETMELIK` as a relevant supporting family. This can come from parsed source-family terms, metadata candidates, or generic query language such as online/distance-sale/procedure/detail wording.

This does not use benchmark `secondary_types`.

## Retrieval Lane

When triggered:

- Run a small scoped source-family retrieval lane for `yonetmelik`, `kky`, and `cb_yonetmelik`.
- Do not increase the normal dense top-k.
- Build the supporting query from the user query plus generic role terms inferred from the query, for example:
  - online sale terms -> distance/remote contract terms
  - exception terms -> exception/limitation terms
  - procedure/detail terms -> implementation/procedure terms
- Tag returned chunks with:
  - `phase24hu_secondary_family_recall=true`
  - `domain_law_supporting_source=true`
  - `source_role=supporting_source`
  - `secondary_family_recall_role=supporting_rule | exception_rule | implementation_detail | procedure_rule`
  - `retrieval_lane_sources += ["phase24hu_secondary_family_recall"]`

## Primary-Source Safety

Secondary chunks are supporting evidence only:

- They must not overwrite selected primary source identity.
- Article selection should keep the primary `KANUN` document lock and include secondary chunks through the existing `domain_law_supporting_source` support window.
- Trace must expose `primary_source_role` and `supporting_source_roles` separately.

## Trace Fields

Add these to `retrieval_verification_features` and retrieval trace:

- `secondary_family_recall_applied`
- `secondary_family_recall_types`
- `secondary_family_recall_candidates`
- `secondary_family_recall_selected`
- `secondary_family_recall_reason`
- `primary_source_role`
- `supporting_source_roles`

After answer-slot selection, expose:

- `exception_slot_source_key`
- `exception_slot_role`

## Acceptance

Focused non-live smoke should show for KANUN-08:

- `pre_filter_family_set` includes both primary `kanun` and supporting `yonetmelik`-family evidence, or an explicit trace explains why supporting recall produced no candidates.
- The selected primary source remains a `KANUN`.
- Exception/procedure slots are filled from role-matching supporting evidence, or left missing rather than filled with unrelated same-family private-law evidence.
