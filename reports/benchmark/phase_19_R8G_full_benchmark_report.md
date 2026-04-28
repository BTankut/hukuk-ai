# Hukuk-AI Phase 19 R8-G Full Benchmark Gate Report

Date: 2026-04-28

## Scope

R8-G is the final full-benchmark gate for the R8 retrieval/orchestration
decomposition work.

Runtime behavior was intended to remain unchanged during R8:

- no retrieval heuristic change
- no source routing change
- no query expansion change
- no Milvus/top-k change
- no prompt/request payload change
- no answer synthesis or confidence policy change
- no QID-specific logic
- no fine-tuning or productization change

The full run was executed after R8-F route-boundary slimming.

Run directory:

```text
reports/benchmark/runs/20260428T_phase19_R8G_full_benchmark_envparity
```

## Full Benchmark Gate

| Metric | R8-G result | Gate | Status |
|---|---:|---:|---|
| `raw_score_proxy` | 756.61 / 1000 | >= 745 | PASS |
| `pass_proxy` | 79 / 100 | >= 77 | PASS |
| `wrong_family` | 10 | <= 12 | PASS |
| `wrong_document` | 9 | <= 12 | PASS |
| `hallucinated_identifier` | 11 | <= 15 | PASS |
| `unsupported_confident_claim` | 0 | 0 or <= 2 | PASS |
| `contract_valid` | 100 / 100 | 100 / 100 | PASS |
| `green_lane` | PASS | PASS | PASS |
| `CB_GENELGE` | 4 / 4 | >= 4 / 4 | PASS |
| `UY` | 10 / 10 | >= 9 / 10 | PASS |
| `MULGA` | 3 / 5 | >= 3 / 5 | PASS |
| `YONETMELIK` | 6 / 10 | >= 6 / 10 | PASS |

Additional collision controls:

| Metric | R8-G result | Expected | Status |
|---|---:|---:|---|
| `source_key_v2_collision_detected_count` | 0 | 0 | PASS |
| `binding_source_key_collision_detected_count` | 0 | 0 | PASS |
| `answer_contract_invalid_count` | 0 | 0 | PASS |
| `contract_repaired_count` | 0 | 0 | PASS |
| `temporal_validity_miss_count` | 0 | 0 | PASS |

## Runtime Summary

From `summary.md`:

| Field | Value |
|---|---:|
| total | 100 |
| answered | 100 |
| refused_or_empty | 0 |
| errors | 0 |
| missing_trace | 0 |
| missing_confidence_0_100 | 0 |
| missing_final_reason | 0 |
| missing_contract_fields | 0 |
| unsupported_confident_answer | 0 |

The R8-G full run matches the accepted R7/A1.10 quality baseline:

```text
raw_score_proxy_delta = 0.00
pass_proxy_delta = 0
wrong_family_delta = 0
wrong_document_delta = 0
hallucinated_identifier_delta = 0
unsupported_confident_answer_delta = 0
answer_contract_invalid_delta = 0
```

## File Size After R8

| File / block | Lines |
|---|---:|
| `api-gateway/src/routers/chat.py` | 9256 |
| `chat_completions(...)` | 890 |
| `api-gateway/src/rag/retrieval_planning.py` | 16 |
| `api-gateway/src/rag/retrieval_orchestration.py` | 199 |
| `api-gateway/src/rag/evidence_bundle.py` | 246 |
| `api-gateway/src/rag/generation_inputs.py` | 46 |
| `api-gateway/src/llm/client.py` | 414 |
| `api-gateway/tests/test_chat_router.py` | 7226 |
| `api-gateway/tests/test_chat_endpoint.py` | 94 |

R8-F met the route-handler target:

```text
chat_completions(...) after R8 = 890 lines
target = < 900 lines
```

## Focused Verification

Commands:

```text
api-gateway/.venv/bin/python -m py_compile \
  api-gateway/src/routers/chat.py \
  api-gateway/src/rag/retrieval_planning.py \
  api-gateway/src/rag/retrieval_orchestration.py \
  api-gateway/src/rag/evidence_bundle.py \
  api-gateway/src/rag/generation_inputs.py \
  api-gateway/src/llm/client.py \
  api-gateway/tests/test_chat_endpoint.py

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_chat_endpoint.py \
  api-gateway/tests/test_faz8_parity_trace.py \
  api-gateway/tests/test_answer_contract_v2.py -q
```

Results:

| Gate | Result |
|---|---:|
| `py_compile` | PASS |
| endpoint + parity + answer-contract tests | 38 passed |

## Runtime Provenance

| Field | Value |
|---|---|
| Gateway API URL | `http://127.0.0.1:8000/v1` |
| Gateway model | `hukuk-ai-poc` |
| Runtime git SHA | `6e8f2e0f1cfd410d22164442e77431459838423a` |
| Branch | `bt/hukuk-ai-100-benchmark-hardening` |
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
| Parity trace | `true` |

`dirty_worktree` was `True` in runtime provenance because the repository already
contained unrelated untracked/modified/deleted files. R8-G did not stage or
modify those files.

## Decision

R8-G passes.

R8 retrieval/orchestration decomposition is complete and remains behavior
preserving against the accepted R7/A1.10 full-benchmark baseline.
