# Phase 19 R7B Safe Wrapper Cleanup Report

Date: 2026-04-27

## Scope

R7B was limited to behavior-preserving router slimming in `api-gateway/src/routers/chat.py`.

No retrieval heuristic, source routing, source identity, article/span selection, answer slot matrix, answer synthesis policy, prompt, confidence policy, or QID-specific logic was changed.

## Static Audit

- `chat.py` after R6/R7A: `9718` lines.
- `chat.py` after R7B: `9510` lines.
- `test_chat_router.py` after R7B: `7226` lines, unchanged.
- Top-level class/function count after R7B: `222`.
- AST check: removed wrapper definitions still present: `[]`.
- AST check: retained runtime/public compatibility wrappers missing: `[]`.

## Safe Delete List

The following wrappers had no `chat.py` load references and no external `api-gateway/tests`, `scripts`, `evaluation`, or `configs` dependency on `chat.py` exports:

- `_extract_query_clause_tokens`
- `_chunk_article_matches`
- `_article_numeric_value`
- `_article_window_distance`
- `_support_contains_temporal_clause`
- `_support_contains_exception_signal`
- `_contains_temporal_clause_signal`
- `_contains_exception_signal`
- `_chunk_has_non_title_body_span`
- `_chunk_allows_document_level_body_span`
- `_article_zero_body_query_allows_extraction`
- `_chunk_allows_article_zero_body_extraction`
- `_chunk_matches_selected_source_key`
- `_query_contains_any`
- `_source_family_resolution_slot_values`
- `_source_families_for_required_slot_matrix`
- `_resolve_required_slot_matrix_for_query`
- `_required_slot_schema`
- `_answer_slot_extraction_method`
- `_best_evidence_row_for_matrix_slot`
- `_build_verified_answer_slots`
- `_count_answer_fact_units`
- `_verified_answer_plan_slot_value`
- `_verified_slots_by_name`
- `_first_verified_plan_value`
- `_build_verified_answer_plan`
- `_verified_slot_controlled_replacement_allowed`

Removed implementation-only imports tied exclusively to these wrappers.

## Retained Wrapper List

- `_resolve_chunk_source_display_label`: retained because `rag.article_span_selection` binds this name dynamically through `runtime_namespace=globals()`.
- `_chunk_uses_legacy_source_key_alias`: retained because `rag.article_span_selection` binds this name dynamically and the router wrapper preserves the route-local binding source key resolver.
- `_source_key_collision_profile`: retained because `rag.article_span_selection` binds this name dynamically and `scripts/benchmark/phase16_source_key_v2_collision_report.py` imports it from `chat.py`.
- `_source_key_v2_collision_profile`: retained because `rag.article_span_selection` binds this name dynamically, `api-gateway/tests/test_chat_router.py` imports it from `chat.py`, and `scripts/benchmark/phase16_source_key_v2_collision_report.py` imports it from `chat.py`.

## Verification

Compile:

```text
api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py
PASS
```

Focused tests:

```text
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_faz8_parity_trace.py -q
5 passed

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_answer_contract_v2.py -q
30 passed
```

Runtime provenance:

```text
DGX_MODEL=/models/merged_model_fabric_stage_20260321
MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024
MILVUS_ENTITY_COUNT=349191
VECTOR_DIMENSION=1024
EMBEDDING_BACKEND=remote
EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1
EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct
GUARDRAILS_ENABLED=false
PRESIDIO_ENABLED=false
VERIFICATION_ENABLED=false
```

20-QID smoke:

```text
run_dir=reports/benchmark/runs/20260427T_phase19_R7B_wrapper_cleanup_smoke20_envparity
answered=20/20
errors=0
missing_trace=0
contract_valid=20/20
unsupported_confident_answer=0
raw_score_proxy=140.23/200
pass_proxy=15/20
source_key_v2_collision_detected_count=0
binding_source_key_collision_detected_count=0
```

Drift vs R6F smoke:

```text
raw_score_proxy_delta=0.00
pass_proxy_delta=0
unsupported_confident_answer_delta=0
answer_contract_invalid_delta=0
source_key_v2_collision_delta=0
binding_source_key_collision_delta=0
scored.csv critical field diff_count=0
candidate_answers.csv critical field diff_count=0
```

## R7B Decision

R7B accepted. The cleanup is behavior-preserving under focused tests and 20-QID smoke.

Next eligible step: R7C safe wrapper re-export/test import cleanup.
