# Phase 24HX-C Feature Attribution Trace Instrumentation

Generated: 2026-05-08

## Scope

Phase24HX-C adds trace instrumentation only. It does not change source selection, retrieval, prompt, model, top-k, collection, or live serving behavior.

Modified files:

- `api-gateway/src/rag/phase24hx_constrained_routing.py`
- `api-gateway/src/routers/chat.py`

## Implementation

Added a side-effect-free helper:

```text
rag.phase24hx_constrained_routing.build_phase24hx_feature_trace(...)
```

The helper consolidates existing Phase24HS/HT/HU trace fields into one stable attribution object:

```text
phase24hx_feature_trace
source_identity_base_decision
source_identity_feature_candidate
replacement_decision
replacement_block_reason
supporting_evidence_added
family_slice
domain_slice
feature_flags_considered
feature_flags_applied
constrained_routing_applied
constrained_routing_reason
base_primary_source_key
candidate_primary_source_key
candidate_role
replacement_allowed
supporting_only_added
family_slice_guard
domain_compatibility_score
metadata_identity_lock_strength
```

The trace object is attached at:

- top-level `trace.phase24hx_feature_trace`
- `trace.parsed_query.phase24hx_feature_trace`
- `trace.query_signals.phase24hx_feature_trace`
- `trace.retrieval.phase24hx_feature_trace`
- `trace.context_assembly.phase24hx_feature_trace`

## Prototype-Ready Decision Contract

The same module also defines the data-only decision contract:

```text
evaluate_phase24hx_replacement(...)
```

This is fail-closed by default and is used by Phase24HX-D tests/prototype. It does not affect runtime behavior until `ENABLE_PHASE24HX_CONSTRAINED_ROUTING=true` is explicitly used by a candidate.

## Verification

Syntax/import verification:

```text
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m py_compile \
  api-gateway/src/rag/phase24hx_constrained_routing.py \
  api-gateway/src/routers/chat.py
```

Result: PASS.

## Live State

Live `8000` was not modified.

