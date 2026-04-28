# Hukuk-AI Phase 19 R8-D Evidence Bundle Extraction Report

Date: 2026-04-28

## Scope

R8-D moved pure evidence/context packaging helpers into:

```text
api-gateway/src/rag/evidence_bundle.py
```

Moved helpers:

- `_build_chunk_evidence_span`
- `_resolve_trace_source_id`
- `_resolve_chunk_source_identifier`
- `_serialize_trace_chunk`
- `_build_assembled_evidence`
- `_build_fallback_assembled_evidence`
- `_build_allowed_source_whitelist`

Supporting local helpers were included in the new module only to preserve serialization behavior:

- `_chunk_recall_lane_sources`
- `_chunk_is_historical_current_counterpart`
- `_metadata_flag_is_true`

Not changed:

- Source identity rerank
- Article/span selection
- Retrieval planning or call order
- Answer hardening
- Answer slot extraction
- Prompt / model request payload
- Final response schema

## File Size

| File / block | Before R8-D | After R8-D |
|---|---:|---:|
| `api-gateway/src/routers/chat.py` | 9345 | 9169 |
| `chat_completions(...)` | 1270 | 1270 |
| `api-gateway/src/rag/evidence_bundle.py` | 0 | 246 |
| `api-gateway/src/rag/retrieval_orchestration.py` | 199 | 199 |
| `api-gateway/src/rag/retrieval_planning.py` | 16 | 16 |

`chat_completions(...)` did not shrink because this extraction moved route-adjacent helpers, not the endpoint body.

## Pre-Change Fixture

Fixture files:

```text
reports/benchmark/phase_19_R8D_evidence_bundle_fixture.md
reports/benchmark/phase_19_R8D_evidence_bundle_fixture.csv
```

Source run:

```text
reports/benchmark/runs/20260428T_phase19_R8C_fixture_post_envparity
```

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
reports/benchmark/runs/20260428T_phase19_R8D_evidence_bundle_fixture_post_envparity
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
evidence_fixture_diff_lines = 0
```

Trace diff vs R8-C fixture:

```text
degraded_qids = 0
raw_score_proxy_delta = 0.00
pass_proxy_delta = 0
```

## Focused Tests

```text
api-gateway/.venv/bin/python -m py_compile \
  api-gateway/src/routers/chat.py \
  api-gateway/src/rag/evidence_bundle.py \
  api-gateway/src/rag/retrieval_orchestration.py \
  api-gateway/src/rag/retrieval_planning.py

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_faz8_parity_trace.py -q

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_answer_contract_v2.py -q

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_chat_router.py::TestLawSignalParsing::test_allowed_source_whitelist_includes_source_identifier_aliases \
  api-gateway/tests/test_chat_router.py::TestLawSignalParsing::test_assembled_evidence_exposes_phase4_canonical_span_fields -q
```

Results:

| Gate | Result |
|---|---:|
| `py_compile` | PASS |
| `test_faz8_parity_trace.py` | 5 passed |
| `test_answer_contract_v2.py` | 30 passed |
| evidence helper router tests | 2 passed |

## 20-QID Smoke

Run directory:

```text
reports/benchmark/runs/20260428T_phase19_R8D_evidence_bundle_smoke20_envparity
```

Smoke metrics:

| Metric | R8-D | R8-D minimum | Status |
|---|---:|---:|---|
| `raw_score_proxy` | 140.23 / 200 | >= 130 | PASS |
| `pass_proxy` | 15 / 20 | >= 12 | PASS |
| `contract_valid` | 20 / 20 | 20 / 20 | PASS |
| `unsupported_confident_answer` | 0 | 0 | PASS |
| `answer_contract_invalid_count` | 0 | 0 | PASS |
| `source_key_v2_collision_detected_count` | 0 | 0 | PASS |
| `binding_source_key_collision_detected_count` | 0 | 0 | PASS |

Delta vs R8-C smoke:

```text
reports/benchmark/runs/20260428T_phase19_R8D_evidence_bundle_smoke20_envparity/trace_delta_vs_R8C.md
```

| Metric | R8-C | R8-D | Delta |
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

R8-D passes.

Next step is R8-E only after prompt/request payload fixture discovery. Since prompt construction is delegated through `RAGOrchestrator.answer(...)`, R8-E must first locate the exact model request payload boundary before moving any generation input code.
