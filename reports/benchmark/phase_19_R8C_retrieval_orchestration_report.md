# Hukuk-AI Phase 19 R8-C Retrieval Orchestration Extraction Report

Date: 2026-04-28

## Scope

R8-C moved only low-level retriever call wrappers and chunk recall-lane normalization into a new module:

```text
api-gateway/src/rag/retrieval_orchestration.py
```

Moved helpers:

- `_build_retrieved_chunk`
- `_annotate_recall_lane_chunks`
- `_retrieve_explicit_article_chunks`
- `_retrieve_law_bucket_chunks`
- `_retrieve_source_key_chunks`
- `_retrieve_active_chunks`
- `_retrieve_source_family_chunks`

`chat.py` still imports these names and the route-level call order remains unchanged.

Not changed:

- Retrieval planning
- Query text construction
- Query expansion
- `top_k` / `top_k_effective`
- Milvus filters
- Retriever call order
- Source selector invocation
- Source identity rerank
- Article/span selector
- Answer synthesis / hardening
- Prompt / generation inputs
- Final response schema

## File Size

| File / block | Before R8-C | After R8-C |
|---|---:|---:|
| `api-gateway/src/routers/chat.py` | 9531 | 9345 |
| `chat_completions(...)` | 1270 | 1270 |
| `api-gateway/src/rag/retrieval_orchestration.py` | 0 | 199 |
| `api-gateway/src/rag/retrieval_planning.py` | 16 | 16 |

`chat_completions(...)` did not shrink in R8-C because this step moved route-adjacent wrapper functions, not the endpoint body.

## Pre-Change Fixture

Fixture files:

```text
reports/benchmark/phase_19_R8C_retrieval_orchestration_fixture.md
reports/benchmark/phase_19_R8C_retrieval_orchestration_fixture.csv
```

Pre-change fixture run:

```text
reports/benchmark/runs/20260428T_phase19_R8C_fixture_pre_envparity
```

Pre-change fixture metrics:

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

Post-change fixture run:

```text
reports/benchmark/runs/20260428T_phase19_R8C_fixture_post_envparity
```

Post-change fixture metrics:

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
fixture_diff_lines = 0
```

No material drift was detected for query hash, retrieval lanes, retriever-call-count proxy, metadata lookup hit, top candidate ids, source families, document ids, retrieval errors, or empty retrieval fallback.

## Focused Tests

```text
api-gateway/.venv/bin/python -m py_compile \
  api-gateway/src/routers/chat.py \
  api-gateway/src/rag/retrieval_orchestration.py \
  api-gateway/src/rag/retrieval_planning.py

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_faz8_parity_trace.py -q

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_answer_contract_v2.py -q

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_chat_router.py::TestLawSignalParsing::test_dedupe_retrieved_chunks_merges_recall_lane_sources \
  api-gateway/tests/test_chat_router.py::TestLawSignalParsing::test_source_key_recall_uses_general_belge_no_filter_for_non_numeric_catalog_keys \
  api-gateway/tests/test_chat_router.py::TestLawSignalParsing::test_source_key_recall_can_bind_family_to_avoid_cross_family_numeric_noise -q
```

Results:

| Gate | Result |
|---|---:|
| `py_compile` | PASS |
| `test_faz8_parity_trace.py` | 5 passed |
| `test_answer_contract_v2.py` | 30 passed |
| wrapper-focused router tests | 3 passed |

## 20-QID Smoke

Run directory:

```text
reports/benchmark/runs/20260428T_phase19_R8C_retrieval_orchestration_smoke20_envparity
```

Smoke metrics:

| Metric | R8-C | R8-C minimum | Status |
|---|---:|---:|---|
| `raw_score_proxy` | 140.23 / 200 | >= 130 | PASS |
| `pass_proxy` | 15 / 20 | >= 12 | PASS |
| `contract_valid` | 20 / 20 | 20 / 20 | PASS |
| `unsupported_confident_answer` | 0 | 0 | PASS |
| `answer_contract_invalid_count` | 0 | 0 | PASS |
| `source_key_v2_collision_detected_count` | 0 | 0 | PASS |
| `binding_source_key_collision_detected_count` | 0 | 0 | PASS |

Delta vs R8-B smoke:

```text
reports/benchmark/runs/20260428T_phase19_R8C_retrieval_orchestration_smoke20_envparity/trace_delta_vs_R8B.md
```

| Metric | R8-B | R8-C | Delta |
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

## Decision

R8-C passes.

Next step is R8-D only if an evidence bundle fixture is created first. Do not move source identity rerank, article/span selector, answer synthesis, prompt generation, or final response code under R8-C.
