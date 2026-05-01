# Phase 22F-R Source-Chain Retrieval Design

Date: 2026-05-01

## Scope

This design defines a shadow-only remediation for historical/repealed applicability questions where the corpus already contains a relation graph but runtime evidence assembly does not promote the full chain.

Target runtime:

```text
http://127.0.0.1:8018/v1
```

Target collection:

```text
mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
```

Live `8000` remains untouched.

## Problem Statement

Phase 22F proved that the required official spans exist:

```text
historical source: 16532
repeal instrument: rg20230311-4
current-law basis: 2547 m.54
```

The remaining failure is runtime assembly:

```text
retrieved historical source
  -> relation metadata present
  -> related repeal/current basis spans not deterministically added to evidence bundle
```

Therefore this phase must add relation-metadata source-chain retrieval, not new corpus materialization and not prompt/model changes.

## Trigger Contract

The expansion may run only when corpus metadata proves a relation-chain context.

Allowed trigger inputs:

```text
metadata.effective_state in [historical, repealed, historical_repealed]
metadata.bridge_role in [historical_repealed_source, repeal_instrument, current_law_basis]
metadata.relation_metadata relation_type values:
  historical_repealed_to_current_bridge
  repeals_historical_regulation
  current_law_basis_for_repealed_discipline_regulation
source_family_resolution.historical_or_repealed_question
source_family_resolution.repealed_scope_detected
query language that asks current applicability / still-valid / reliance / yürürlükte status
```

Forbidden trigger inputs:

```text
qid
benchmark expected answer/source
hardcoded MULGA-01 branch
hardcoded source-title-only branch
private benchmark answer key
```

## Retrieval Strategy

The runtime should scan the candidate chunk set after normal retrieval and before article-span/evidence selection. Any chunk with historical/repealed relation metadata can act as a relation-chain anchor.

For each anchor:

1. Read `metadata.relation_metadata`.
2. Resolve relation-local IDs from metadata rather than assuming they are public `source_identifier` values.
3. Query Milvus nested JSON metadata for the matching current-law basis and repeal instrument rows.
4. Convert related rows into `RetrievedChunk` objects.
5. Annotate all chain chunks with deterministic relation-chain trace metadata.
6. Merge the relation-chain chunks into the retrieved candidate pool with dedupe by stable span key.

Required relation lookup pattern:

```text
anchor.relation_metadata.repealed_by_source_id
  -> query current-law basis rows where relation_metadata.repeal_source_id matches
  -> derive historical_source_id from current-law basis relation_metadata
  -> query repeal instrument rows where relation_metadata.repealed_source_id matches
```

Fallback relation lookup pattern:

```text
anchor.relation_metadata.current_law_basis_source_id
  -> query bridge_role == current_law_basis and relation metadata intersects anchor relation ids
```

This avoids relying on the public source identifier because Phase 22F-R-A showed relation IDs such as `yok_disc_2023_repeal` and `law_2547_current` are relation-local IDs.

## Evidence Roles

Relation-chain chunks must be marked with one of these roles:

```text
historical_rule
repeal_instrument
current_law_basis
transition_rule
```

The selected historical source must not be marked active. A repealed/historical source remains historical evidence; the current-law basis is a separate active supporting source.

## Trace Contract

The following fields must be available on relation-chain candidate metadata and surfaced in trace/evidence serialization when present:

```text
relation_chain_expansion_applied
relation_chain_source_key
relation_chain_repeal_source_key
relation_chain_current_basis_source_key
relation_chain_span_keys
relation_chain_missing_reason
historical_source_effective_state
current_law_basis_added
repeal_instrument_added
historical_source_not_marked_active
repealed_as_active_count
```

Minimum semantics:

```text
relation_chain_expansion_applied=true only when at least one related chain span is added
current_law_basis_added=true only when an active current-law basis chunk is added
repeal_instrument_added=true only when a repeal instrument chunk is added
historical_source_effective_state preserves the anchor effective_state
historical_source_not_marked_active=true when the historical anchor remains non-active
relation_chain_missing_reason explains no-op cases without failing normal retrieval
```

## Module Placement

Primary implementation target:

```text
api-gateway/src/rag/retrieval_orchestration.py
```

Responsibilities:

```text
relation metadata parsing
nested Milvus metadata lookup
RetrievedChunk construction
chain chunk annotation
dedupe keys
expansion policy trace object
```

Secondary touch points:

```text
api-gateway/src/routers/chat.py
```

Responsibilities:

```text
call the expansion after initial retrieval and before article-span selection
merge returned chunks into the candidate pool
merge relation-chain trace fields into runtime trace
```

Serialization touch point if needed:

```text
api-gateway/src/rag/evidence_bundle.py
```

Responsibilities:

```text
include relation_chain_* metadata fields in assembled evidence trace
```

The design intentionally avoids `answer_synthesis.py` and `answer_slots.py`; the answer layer should consume better evidence, not contain special-case routing logic.

## Dedupe And Safety

Relation-chain chunks must be deduped against existing chunks by stable keys in this order:

```text
metadata.span_id
metadata.canonical_span_key
metadata.source_key_v2
metadata.source_identifier + madde_no + fikra_no
chunk.citation
```

Existing candidate chunks must not be removed by this expansion. The expansion is additive and capped.

Recommended caps:

```text
max anchors: 4
max repeal instrument chunks per chain: 3
max current-law basis chunks per chain: 3
max total added relation-chain chunks: 8
```

No relation-chain row should alter corpus metadata in-place except transient runtime annotations copied onto the chunk metadata.

## Acceptance Tests

Required unit tests:

```text
historical_repealed_source_adds_repeal_and_current_basis_spans
relation_chain_does_not_mark_repealed_source_active
relation_chain_requires_metadata_not_qid
relation_chain_preserves_teblig_and_yonetmelik_guard_rows
```

Behavioral smoke requirements for Phase 22F-R-D:

```text
MULGA >= 4/5
TEBLIGLER >= 6/8, preferred >= 7/8
MULGA-01 improves or passes
TEB-06 remains pass
unsupported=0
contract invalid=0
canonical/source-key collisions=0
repealed_as_active_count=0
relation_chain_expansion_applied for applicable historical/repealed questions
```

## Decision

Proceed to Phase 22F-R-C implementation.

The implementation must be metadata-driven, shadow-only, additive, and independent of benchmark QIDs.
