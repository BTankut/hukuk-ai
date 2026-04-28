# Hukuk-AI Phase 19 R8-F Route Handler Boundary Report

Date: 2026-04-28

## Scope

R8-F reduced `chat_completions(...)` by extracting retrieval runtime/context preparation into:

```text
_prepare_retrieval_runtime_context(...)
ChatRetrievalRuntimeContext
```

The extracted block prepares the same route-local variables used by the retrieval call stack:

- enriched/routing/retrieval query
- mentioned laws and article refs
- requested source families
- retrieval plan and metadata lookup selector
- domain supporting source selector state
- exact article refs and source-lock target count
- answer query

Not changed:

- Retrieval call order
- Retriever filters or top-k values
- Source routing/selection logic
- Reranker/selector execution
- Orchestrator call
- Prompt/model payload
- Answer hardening/finalization
- Response rendering
- Audit/token accounting

## File Size

| File / block | Before R8-F | After R8-F |
|---|---:|---:|
| `api-gateway/src/routers/chat.py` | 9169 | 9256 |
| `chat_completions(...)` | 1270 | 891 |
| `api-gateway/tests/test_chat_endpoint.py` | 0 | 94 |
| `api-gateway/tests/test_chat_router.py` | 7226 | 7226 |
| `api-gateway/src/rag/generation_inputs.py` | 46 | 46 |
| `api-gateway/src/rag/evidence_bundle.py` | 246 | 246 |
| `api-gateway/src/rag/retrieval_orchestration.py` | 199 | 199 |
| `api-gateway/src/rag/retrieval_planning.py` | 16 | 16 |

R8-F meets the `<900` route-handler target.

## Endpoint Tests

New endpoint-focused test file:

```text
api-gateway/tests/test_chat_endpoint.py
```

Coverage started:

- non-streaming response schema
- model field
- choices/message field
- answer contract presence
- trace presence when requested
- error response shape

## Focused Tests

```text
api-gateway/.venv/bin/python -m py_compile \
  api-gateway/src/routers/chat.py \
  api-gateway/tests/test_chat_endpoint.py

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_chat_endpoint.py -q

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_faz8_parity_trace.py \
  api-gateway/tests/test_answer_contract_v2.py -q
```

Results:

| Gate | Result |
|---|---:|
| `py_compile` | PASS |
| `test_chat_endpoint.py` | 3 passed |
| `test_faz8_parity_trace.py` + `test_answer_contract_v2.py` | 35 passed |

## 20-QID Smoke

Run directory:

```text
reports/benchmark/runs/20260428T_phase19_R8F_route_boundary_smoke20_envparity
```

Smoke metrics:

| Metric | R8-F | R8-F minimum | Status |
|---|---:|---:|---|
| `raw_score_proxy` | 140.23 / 200 | >= 130 | PASS |
| `pass_proxy` | 15 / 20 | >= 12 | PASS |
| `contract_valid` | 20 / 20 | 20 / 20 | PASS |
| `unsupported_confident_answer` | 0 | 0 | PASS |
| `answer_contract_invalid_count` | 0 | 0 | PASS |
| `source_key_v2_collision_detected_count` | 0 | 0 | PASS |
| `binding_source_key_collision_detected_count` | 0 | 0 | PASS |

Delta vs R8-E smoke:

```text
reports/benchmark/runs/20260428T_phase19_R8F_route_boundary_smoke20_envparity/trace_delta_vs_R8E.md
```

| Metric | R8-E | R8-F | Delta |
|---|---:|---:|---:|
| `raw_score_proxy` | 140.23 | 140.23 | 0.00 |
| `pass_proxy` | 15 / 20 | 15 / 20 | 0 |
| degraded QIDs | 0 | 0 | 0 |

## Runtime Provenance

| Field | Value |
|---|---|
| Gateway model | `hukuk-ai-poc` |
| DGX base URL | `http://192.168.12.243:30000/v1` |
| DGX model | `/models/merged_model_fabric_stage_20260321` |
| Milvus collection | `mevzuat_faz1_shadow_20260418_compat1024` |
| Milvus entity count | `349191` |
| Vector dimension | `1024` |
| Embedding backend | `remote` |
| Embedding base URL | `http://127.0.0.1:8081/v1` |
| Embedding model | `intfloat/multilingual-e5-large-instruct` |
| Guardrails | `false` / health `disabled` |
| Presidio | `false` |
| Verification | `false` / health `disabled` |
| Parity trace | `true` for R8-F smoke trace observability |

## Decision

R8-F passes.

Next step is R8-G full benchmark gate.
