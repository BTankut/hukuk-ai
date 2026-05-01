# Phase 22M-R-B P0 Decision Normalization

## Scope

P0 rows:

- `MULGA-01`
- `TEB-06`

## Input State

The expected filled P0 legal review result file was not found:

```text
filled_phase_22M_P0_manual_legal_review_packet.csv
```

Therefore, no lawyer-confirmed value is available for:

- expected source
- expected article or clause
- official source URL
- effective-state decision
- current-law relation
- backfill requirement
- safe runtime behavior

## Normalized Decisions

| qid | Normalized decision | Shadow backfill allowed | Reason |
|---|---|---:|---|
| `MULGA-01` | `needs_more_legal_review` | false | The legal source chain, repeal/current-law relation, article/clause, and official source evidence are unconfirmed. |
| `TEB-06` | `needs_more_legal_review` | false | The exact expected teblig/source chain, article range, official body source, and parser-ready material are unconfirmed. |

## Decision

Neither P0 row is ready for Phase 22F shadow backfill. The correct next action is to obtain completed legal review results and official source acquisition evidence before any corpus materialization or runtime patch is considered.
