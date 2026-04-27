# Phase 19 R7C Import Cleanup Report

Date: 2026-04-27

## Scope

R7C moved safe collision-profile helper imports from `routers.chat` to the owning `rag.source_identity` module.

Runtime endpoint code was not changed in this step. Router-local collision wrappers remain in `chat.py` because `rag.article_span_selection` binds them dynamically through `runtime_namespace=globals()` and the wrappers preserve the route-local routing family resolver.

## Changes

- `api-gateway/tests/test_chat_router.py`
  - `_source_key_v2_collision_profile` now imports from `rag.source_identity`.
- `scripts/benchmark/phase16_source_key_v2_collision_report.py`
  - `_source_key_collision_profile` and `_source_key_v2_collision_profile` now import from `rag.source_identity`.
  - `_resolve_chunk_canonical_source_key_v2` remains imported from `routers.chat` because the script intentionally uses the router wrapper for route-local canonical key behavior.

## Retained Router Wrappers

- `_resolve_chunk_source_display_label`
- `_chunk_uses_legacy_source_key_alias`
- `_source_key_collision_profile`
- `_source_key_v2_collision_profile`

Reason: these names are runtime namespace dependencies for article/span selector behavior. Removing them from `chat.py` would risk changing selector materialization/collision behavior.

## Verification

Compile/import checks:

```text
api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py scripts/benchmark/phase16_source_key_v2_collision_report.py
PASS

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python scripts/benchmark/phase16_source_key_v2_collision_report.py --help
PASS
```

Focused tests:

```text
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -q -k source_key
8 selected tests passed

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_faz8_parity_trace.py api-gateway/tests/test_answer_contract_v2.py -q
35 passed
```

20-QID smoke:

```text
run_dir=reports/benchmark/runs/20260427T_phase19_R7C_import_cleanup_smoke20_envparity
runtime_provenance_git_sha=e0f93d6379f31d79f69cb328e616bb118a5bfc87
DGX_MODEL=/models/merged_model_fabric_stage_20260321
MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024
MILVUS_ENTITY_COUNT=349191
VECTOR_DIMENSION=1024
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

Drift vs R7B:

```text
scored.csv critical_diff_count=0
candidate_answers.csv critical_diff_count=0
raw_score_proxy_delta=0.00
pass_proxy_delta=0
unsupported_confident_answer_delta=0
answer_contract_invalid_delta=0
```

## R7C Decision

R7C accepted. Safe test/script import cleanup completed with no endpoint behavior drift.

Next eligible step: R7D slim route handler/orchestration boundary.
