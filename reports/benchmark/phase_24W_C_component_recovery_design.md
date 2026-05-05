# Phase 24W-C Component Recovery Design

## Decision

A safe systemic prototype is possible for the source-selection drift subset, but it must be scoped to `source_identity.py` selected-source-key matching only. It is not expected to fix same-source rows (`KANUN-02`, `MULGA-04`, `YON-08`) by itself.

## Design 1 — Source Identity Recovery Flag

| item | decision |
|---|---|
| feature flag | `ENABLE_PHASE24W_SOURCE_IDENTITY_RECOVERY` |
| default | `false` / off |
| live effect by default | none; current behavior preserved unless flag is explicitly enabled in a non-live runtime |
| target file | `api-gateway/src/rag/source_identity.py` |
| target helper | `_chunk_matches_selected_source_key` |
| systemic behavior | canonical source/document/binding/span keys continue to match; title metadata fields must not satisfy selected-source-key matching in recovery mode |
| no-QID proof | flag affects the helper globally and contains no QID, source title, article, or benchmark row constants |

### Rationale

`ddcadd2` allowed `source_title`, `canonical_title`, `belge_adi`, and `law_name` to satisfy selected-source-key matching. Phase24W-A/B show this is the strongest systemic explanation for `KANUN-08` and `YON-05` source-selection drift. The safe prototype should therefore disable only title-metadata selected-source matches under a flag while preserving canonical/binding key identity.

## Design 2 — Supplement Support-Only Principle

| item | decision |
|---|---|
| feature flag | no new flag in Phase24W-C |
| default | keep current supplement loading unchanged |
| rationale | Phase24U supplement-disable did not restore Phase23R-E and `KANUN-12`/`YON-04` improved after Phase24N acquisition |
| safe rule | supplements may support evidence bundle; do not use Phase24W to broadly remove supplements from primary selection |

The first prototype must not revert `source_supplements.py` or Phase24N data. Positive rows must be guard rows.

## Design 3 — Family / Domain Compatibility Gate

| item | decision |
|---|---|
| phase | design-only for Phase24W unless source identity flag is insufficient |
| rule | title/domain boosts may not cross incompatible legal families unless explicit query/source identifier evidence exists |
| examples | no silent `YONETMELIK -> KANUN` primary rewrite from title/topic overlap; no family relabeling through aliases |
| implementation status | defer until SI-1 evidence says helper-level title gating is insufficient |

## Design 4 — Same-Source Contract Preservation

| item | decision |
|---|---|
| rows | `KANUN-02`, `MULGA-04`, `YON-08` |
| target | answer contract / trace extraction / answer slot completeness, not source identity first |
| rule | when selected source and selected span are unchanged, family/identifier/failure-class degradation must have trace-visible cause |
| implementation status | no Phase24W source_identity prototype should attempt to fix these rows |

## Non-Live Test Plan

| step | description |
|---|---|
| D prototype | Implement `ENABLE_PHASE24W_SOURCE_IDENTITY_RECOVERY` default off; under true, remove title metadata from selected-source-key matching. |
| Runtime | Non-live port only, recommended `8040`. |
| Collection | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`. |
| Model | `hukuk-ai-poc` / DGX merged model, unchanged. |
| Trace | `include_trace=true`. |
| Answer key | not used. |
| Safety | contract valid, no source key collisions, no binding collisions, no API errors, no empty/refused responses. |

## Focused Smoke Rows

Primary source-selection rows:

- `KANUN-08`
- `YON-05`

Same-source diagnostic rows:

- `KANUN-02`
- `MULGA-04`
- `YON-08`

Guard rows:

- `MULGA-01`
- `MULGA-05`
- `TEB-06`
- `CBY-06`
- `KANUN-12`
- `YON-04`

## Trace-Only Acceptance For Phase24W-E

Because answer-key use is forbidden, improvement must be measured trace-only:

- `KANUN-08` selected source should move away from `fam=yonetmelik|id=24039|...|article=0` and preferably toward `fam=kanun|id=6098|...|article=255`.
- `YON-05` selected source should move away from `fam=kanun|id=3194|...|article=18` and preferably toward `fam=yonetmelik|id=23722|...|article=5`.
- Guard rows must keep valid contracts and safety counters zero.
- If selected source does not improve on at least two primary rows, mark component insufficient and do not run full candidate.

## Rollback Plan

- Disable `ENABLE_PHASE24W_SOURCE_IDENTITY_RECOVERY`.
- Stop non-live candidate runtime.
- Do not touch live `8000`.
- Do not revert unrelated Phase24N source acquisition or supplement files.
- If the flag is accidentally enabled in a live command, stop before launch; this violates Phase24W stop rules.

## Prototype Safety Decision

Safe to prototype: **yes**, because the implementation can be feature-flagged, default-off, non-live, systemic, and limited to one helper function without answer-key usage or QID-specific logic.
