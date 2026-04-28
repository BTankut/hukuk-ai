# Hukuk-AI Phase 19 R8-B Retrieval Planning Extraction Report

Date: 2026-04-28

## Scope

R8-B was kept intentionally narrow.

Moved behavior-preserving helper group:

- `request_history_from_messages(...)` added in `api-gateway/src/rag/retrieval_planning.py`
- `chat.py` now imports and calls that helper from the new module

Not changed:

- Retrieval query construction
- Query expansion rules
- `top_k` / `top_k_effective`
- Milvus filters
- Retriever call count or call order
- Source family routing
- Metadata-first source selection
- Article/span selection
- Prompt or generation input
- Answer synthesis / hardening / final response policy

## File Size

| File / block | Before R8-B | After R8-B |
|---|---:|---:|
| `api-gateway/src/routers/chat.py` | 9538 | 9531 |
| `chat_completions(...)` | 1270 | 1270 |
| `api-gateway/src/rag/retrieval_planning.py` | 0 | 16 |

`chat_completions(...)` did not shrink in this step because the moved helper was route-adjacent, not inside the endpoint body.

## Focused Tests

```text
api-gateway/.venv/bin/python -m py_compile \
  api-gateway/src/routers/chat.py \
  api-gateway/src/rag/retrieval_planning.py

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_faz8_parity_trace.py -q

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_answer_contract_v2.py -q
```

Results:

| Gate | Result |
|---|---:|
| `py_compile` | PASS |
| `test_faz8_parity_trace.py` | 5 passed |
| `test_answer_contract_v2.py` | 30 passed |

## Smoke Run

Run directory:

```text
reports/benchmark/runs/20260428T_phase19_R8B_retrieval_planning_smoke20_envparity
```

Runtime provenance:

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

Smoke result:

| Metric | R8-B | R8-B minimum | Status |
|---|---:|---:|---|
| `raw_score_proxy` | 140.23 / 200 | >= 130 | PASS |
| `pass_proxy` | 15 / 20 | >= 12 | PASS |
| `contract_valid` | 20 / 20 | 20 / 20 | PASS |
| `unsupported_confident_answer` | 0 | 0 | PASS |
| `source_key_v2_collision_detected_count` | 0 | 0 | PASS |
| `binding_source_key_collision_detected_count` | 0 | 0 | PASS |

Failure-class controls:

| Metric | R8-B |
|---|---:|
| `wrong_document` | 1 |
| `hallucinated_identifier` | 1 |
| `answer_contract_invalid_count` | 0 |

## Delta vs R7D Smoke

Baseline:

```text
reports/benchmark/runs/20260427T_phase19_R7D_route_boundary_smoke20_envparity
```

Trace comparison:

```text
reports/benchmark/runs/20260428T_phase19_R8B_retrieval_planning_smoke20_envparity/trace_delta_vs_R7D.md
```

Summary:

| Metric | R7D | R8-B | Delta |
|---|---:|---:|---:|
| `raw_score_proxy` | 140.23 | 140.23 | 0.00 |
| `pass_proxy` | 15 / 20 | 15 / 20 | 0 |
| degraded QIDs | 0 | 0 | 0 |

No material drift was detected.

## Decision

R8-B passes.

Next safe step is R8-C fixture capture before moving any retriever call orchestration. No R8-C code extraction should start without freezing the required retrieval fixture fields.
