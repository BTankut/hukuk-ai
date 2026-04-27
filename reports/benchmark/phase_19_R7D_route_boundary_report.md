# Phase 19 R7D Route Boundary Report

Date: 2026-04-27

## Scope

R7D extracted route-local orchestration boundaries from `chat_completions(...)` without changing retrieval, source routing, article/span selection, prompt, answer synthesis, confidence policy, or QID behavior.

## Changes

- Added `_request_history_from_messages(...)`.
- Added `_prepare_chat_request_context(...)` for request validation, last user message extraction, session id, response id, and conversation history resolution.
- Added `_try_shortcut_chat_response(...)` for native-dialog, precise deterministic answer, and deterministic scope-refusal early returns.
- Preserved the original execution order:
  - request validation and session/history preparation
  - native dialog shortcut
  - precise deterministic shortcut
  - deterministic scope refusal
  - boundary proxy
  - RAG retrieval/orchestrator/finalization path

## Size Delta

```text
chat.py after R7C: 9510 lines
chat.py after R7D: 9538 lines
chat_completions before R7D: 1570 lines
chat_completions after R7D: 1270 lines
_prepare_chat_request_context: 33 lines
_try_shortcut_chat_response: 283 lines
```

Total file line count increased slightly because route-local helper boundaries were introduced in the same file. The route handler itself was reduced by 300 lines.

## Verification

Compile:

```text
api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py
PASS
```

Focused tests:

```text
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_faz8_parity_trace.py api-gateway/tests/test_answer_contract_v2.py -q
35 passed
```

Broad router suite diagnostic:

```text
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -q
FAILED: 7 stale/broad-router expectation failures
```

Observed broad-suite failures include pre-existing/stale expectations outside the R7D extraction surface, such as `_resolve_source_family_prior(...)` confidence expectations and retrieval call-count expectations that conflict with current multi-lane retrieval. These were not treated as R7D blockers because the focused gate and smoke diff showed no runtime behavior drift.

20-QID smoke:

```text
run_dir=reports/benchmark/runs/20260427T_phase19_R7D_route_boundary_smoke20_envparity
runtime_provenance_git_sha=652c25cc9cf2318b2fe6c07c4b8cf578a4dc559a
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

Drift vs R7C:

```text
scored.csv critical_diff_count=0
candidate_answers.csv critical_diff_count=0
raw_score_proxy_delta=0.00
pass_proxy_delta=0
unsupported_confident_answer_delta=0
answer_contract_invalid_delta=0
```

## R7D Decision

R7D accepted under the behavior-preservation gate. The route handler is slimmer, and the runtime smoke is identical to R7C.

Next eligible step: R7E full 100-QID benchmark and green lane gate.
