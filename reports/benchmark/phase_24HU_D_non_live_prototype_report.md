# Phase 24HU-D Non-Live Prototype Report

## Scope

Phase 24HU was implemented as a feature-flagged, non-live candidate prototype. Live `8000` was not modified.

Candidate endpoint:

```text
http://127.0.0.1:8043/v1
```

Candidate runtime identity:

```text
lane=phase24hu_source_role_retrieval_candidate
api_version=2026-05-07-phase24hu-source-role-retrieval-candidate
collection=mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24hr
guardrails=disabled
retriever=milvus
```

Live `8000` state during validation:

```text
lane=phase22f_s7_full_shadow
api_version=2026-05-03-phase23R-E-benchmark-only-cutover
guardrails=disabled
retriever=milvus
verification=disabled
```

## Feature Flags

The candidate was started with:

```text
ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING=true
ENABLE_PHASE24HS_FAMILY_DOMAIN_GATE=true
ENABLE_PHASE24HU_SECONDARY_FAMILY_RECALL=true
ENABLE_PHASE24HU_EXCEPTION_SLOT_GUARD=true
```

Phase 24HU flags default to off in code, so the prototype is fail-closed unless explicitly enabled.

## Implementation Summary

The prototype adds a source-role retrieval path for questions where the primary source family remains `KANUN` but runtime query/source-role signals indicate supporting secondary-family evidence is needed.

Implemented behavior:

- Primary source identity is not rewritten by secondary recall.
- Supporting retrieval is scoped to secondary family candidates inferred from runtime metadata/query signals.
- Supporting chunks are role-tagged with `source_role=supporting_source` and `secondary_family_recall_role`.
- Secondary chunks are penalized as primary article candidates unless they have an explicit source match, selected-source match, or identifier match.
- Exception/procedure/scenario slots prefer role-compatible supporting evidence and stop filling unrelated same-family/private-law spans merely by semantic similarity.

Trace fields added:

```text
secondary_family_recall_applied
secondary_family_recall_types
secondary_family_recall_candidates
secondary_family_recall_selected
secondary_family_recall_reason
primary_source_role
supporting_source_roles
exception_slot_source_key
exception_slot_role
phase24hu_exception_slot_guard_applied
phase24hu_exception_slot_guard_reason
```

## Touched Runtime Surfaces

```text
api-gateway/src/routers/chat.py
api-gateway/src/rag/article_span_selection.py
api-gateway/src/rag/evidence_bundle.py
```

Test surface:

```text
api-gateway/tests/test_chat_router.py
```

## Validation

Targeted unit tests:

```text
api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k 'phase24hu or phase24ht or article_span_selector_keeps_requested_family_ahead_of_cross_family_article_hit'
```

Result:

```text
7 passed, 326 deselected, 1 warning
```

Syntax check:

```text
python3 -m py_compile api-gateway/src/routers/chat.py api-gateway/src/rag/article_span_selection.py api-gateway/src/rag/evidence_bundle.py
```

Result:

```text
passed
```

Production hardcode scan:

```text
rg -n "KANUN-08|TÜKETİCİNİN KORUNMASI|TKHK|MESAFELİ SÖZLEŞMELER|Mesafeli Sözleşmeler" api-gateway/src
```

Result:

```text
no production hits
```

## Prototype Safety Decision

Safe for non-live focused smoke. Not approved for live cutover or productization in this phase.

