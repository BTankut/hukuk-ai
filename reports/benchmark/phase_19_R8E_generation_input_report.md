# Hukuk-AI Phase 19 R8-E Generation Input Builder Extraction Report

Date: 2026-04-28

## Scope

R8-E moved model generation request payload construction into:

```text
api-gateway/src/rag/generation_inputs.py
```

Moved helpers:

- `build_generation_contract`
- `build_request_payload`

`LLMClient._build_generation_contract(...)` and `LLMClient._build_request_payload(...)` remain as compatibility wrappers and delegate to the new module.

Not changed:

- Prompt text
- Message order
- Retrieval, routing, or source selection
- Milvus parameters
- Answer synthesis or finalization
- Confidence/final_reason policy
- Model parameters

## Import Boundary Note

Importing `rag.generation_inputs` from `llm.client` exposed an existing package-level cycle because `rag/__init__.py` eagerly imported `rag.orchestrator`, which imports `llm.client`.

`api-gateway/src/rag/__init__.py` was converted to lazy exports while preserving the existing `from rag import ...` API surface. This avoids the cycle without changing runtime retrieval or generation behavior.

## File Size

| File / block | Before R8-E | After R8-E |
|---|---:|---:|
| `api-gateway/src/routers/chat.py` | 9169 | 9169 |
| `chat_completions(...)` | 1270 | 1270 |
| `api-gateway/src/llm/client.py` | 428 | 414 |
| `api-gateway/src/rag/generation_inputs.py` | 0 | 46 |
| `api-gateway/src/rag/__init__.py` | 60 | 50 |
| `api-gateway/src/rag/evidence_bundle.py` | 246 | 246 |
| `api-gateway/src/rag/retrieval_orchestration.py` | 199 | 199 |
| `api-gateway/src/rag/retrieval_planning.py` | 16 | 16 |

`chat_completions(...)` did not shrink in R8-E because this extraction moved generation request helpers, not route-handler body blocks.

## Pre-Change Fixture

Fixture files:

```text
reports/benchmark/phase_19_R8E_generation_input_fixture.md
reports/benchmark/phase_19_R8E_generation_input_fixture.csv
```

Source run:

```text
reports/benchmark/runs/20260428T_phase19_R8E_generation_input_fixture_pre_envparity
```

Parity trace was enabled for this fixture only to expose `model_request_payload` and `generation_contract`.

Pre-change metrics:

| Metric | Value |
|---|---:|
| total | 8 |
| answered | 8 |
| errors | 0 |
| missing_trace | 0 |
| contract_valid | 8 / 8 |
| unsupported_confident_answer | 0 |
| raw_score_proxy | 59.33 / 80 |
| pass_proxy | 6 / 8 |

## Post-Change Fixture

Post-change run:

```text
reports/benchmark/runs/20260428T_phase19_R8E_generation_input_fixture_post_envparity
```

Post-change metrics:

| Metric | Value |
|---|---:|
| total | 8 |
| answered | 8 |
| errors | 0 |
| missing_trace | 0 |
| contract_valid | 8 / 8 |
| unsupported_confident_answer | 0 |
| raw_score_proxy | 59.33 / 80 |
| pass_proxy | 6 / 8 |

Fixture diff:

```text
generation_input_fixture_diff_lines = 0
```

Diff file:

```text
reports/benchmark/runs/20260428T_phase19_R8E_generation_input_fixture_post_envparity/generation_input_fixture.diff
```

## Focused Tests

```text
api-gateway/.venv/bin/python -m py_compile \
  api-gateway/src/rag/__init__.py \
  api-gateway/src/llm/client.py \
  api-gateway/src/rag/generation_inputs.py \
  api-gateway/src/main.py \
  api-gateway/src/routers/chat.py

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_faz8_parity_trace.py -q

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_answer_contract_v2.py -q

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python - <<'PY'
from rag import RAGOrchestrator, RetrievedChunk, MilvusRetriever
from rag.generation_inputs import build_generation_contract, build_request_payload
print(RAGOrchestrator.__name__, RetrievedChunk.__name__, MilvusRetriever.__name__)
print(build_generation_contract is not None, build_request_payload is not None)
PY
```

Results:

| Gate | Result |
|---|---:|
| `py_compile` | PASS |
| `test_faz8_parity_trace.py` | 5 passed |
| `test_answer_contract_v2.py` | 30 passed |
| lazy `rag` export/import probe | PASS |

## 20-QID Smoke

Run directory:

```text
reports/benchmark/runs/20260428T_phase19_R8E_generation_input_smoke20_envparity
```

Smoke metrics:

| Metric | R8-E | R8-E minimum | Status |
|---|---:|---:|---|
| `raw_score_proxy` | 140.23 / 200 | >= 130 | PASS |
| `pass_proxy` | 15 / 20 | >= 12 | PASS |
| `contract_valid` | 20 / 20 | 20 / 20 | PASS |
| `unsupported_confident_answer` | 0 | 0 | PASS |
| `answer_contract_invalid_count` | 0 | 0 | PASS |
| `source_key_v2_collision_detected_count` | 0 | 0 | PASS |
| `binding_source_key_collision_detected_count` | 0 | 0 | PASS |

Delta vs R8-D smoke:

```text
reports/benchmark/runs/20260428T_phase19_R8E_generation_input_smoke20_envparity/trace_delta_vs_R8D.md
```

| Metric | R8-D | R8-E | Delta |
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
| Parity trace | `true` for R8-E fixture/smoke trace observability |

## Decision

R8-E passes.

Next step is R8-F route handler boundary slimming. That step is higher risk because it touches route body call ordering, response rendering, exception handling, and audit/token-accounting boundaries.
