# Phase 24HY-C Replacement Guard Trace Report

Generated: 2026-05-08

## Scope

Phase24HY-C adds trace instrumentation only. It does not change retrieval, source selection, answer synthesis, live `8000`, productization, internal eval, fine-tuning, model, prompt, top-k, or collections.

## Implemented Trace Surface

Added `api-gateway/src/rag/phase24hy_replacement_guard.py` with a data-only guard contract and trace builder.

The chat trace now emits:

```text
trace.phase24hy_replacement_guard
trace.parsed_query.phase24hy_replacement_guard
```

The trace object includes the required Phase24HY fields:

```text
phase24hy_replacement_guard
base_primary_source_key
candidate_primary_source_key
replacement_attempted
replacement_allowed
replacement_block_reason
candidate_role
candidate_metadata_lock_strength
candidate_domain_score
base_domain_score
identifier_drift_blocked
article_drift_blocked
supporting_only_added
primary_source_preserved
```

Additional diagnostic fields are included for slice analysis:

```text
family_slice
base_family
candidate_family
requested_family
metadata_lookup_source
metadata_lookup_confidence
```

## Behavior Boundary

`ENABLE_PHASE24HY_REPLACEMENT_GUARD` is read by the helper, but Phase24HY-C does not yet mediate or reorder candidates. The helper reports whether a replacement would be allowed under the guard contract. Runtime enforcement is deferred to Phase24HY-D.

## Verification

Required verification command:

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m py_compile api-gateway/src/rag/phase24hy_replacement_guard.py api-gateway/src/routers/chat.py
```

Status: passed.
