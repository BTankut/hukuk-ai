# Phase 19 R5C Low-Risk Answer Slot Serialization Extraction Report

## Status

R5C is accepted as behavior-preserving.

Low-risk answer slot serialization helpers were moved from `chat.py` to `rag.answer_slots` behind router compatibility wrappers. No required slot matrix logic, slot coverage scoring, minimum answer facts calculation, runtime rubric sufficient calculation, confidence policy, answer synthesis, source identity, article/span selector, prompt, or QID-specific logic was changed.

## Runtime Provenance

- `DGX_BASE_URL=http://192.168.12.243:30000/v1`
- `DGX_MODEL=/models/merged_model_fabric_stage_20260321`
- `MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024`
- `MILVUS_ENTITY_COUNT=349191`
- `VECTOR_DIMENSION=1024`
- `EMBEDDING_BACKEND=remote`
- `EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1`
- `EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct`
- `GUARDRAILS_ENABLED=false`
- `PRESIDIO_ENABLED=false`
- `VERIFICATION_ENABLED=false`

## Moved Code

Created:

```text
api-gateway/src/rag/answer_slots.py
```

Moved behind compatibility wrappers in `chat.py`:

- `_REQUIRED_SLOT_SCHEMA`
- `_required_slot_schema`
- `_compact_slot_value`
- `_slot_quote_hash`
- `_ANSWER_SLOT_EXTRACTION_VERSION`
- `_DETERMINISTIC_MATRIX_SLOTS`
- `_answer_slot_extraction_method`
- `_best_evidence_row_for_matrix_slot`
- `_build_verified_answer_slots`

The moved functions do not own required slot selection, coverage scoring, minimum fact sufficiency, final answer shaping, or confidence policy. Those remain in `chat.py` for later R5D/R5E steps.

## Tests

Compile:

```bash
api-gateway/.venv/bin/python -m py_compile \
  api-gateway/src/routers/chat.py \
  api-gateway/src/rag/answer_slots.py
```

Result: PASS

Focused answer-slot tests:

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_chat_router.py \
  -k "answer_slot or evidence_slot or slot_coverage" -q
```

Result: `13 passed`

## Fixture Diff

Before fixture:

```text
reports/benchmark/phase_19_R5_answer_slot_fixture.csv
```

After fixture:

```text
reports/benchmark/phase_19_R5C_answer_slot_after_extraction_fixture.csv
```

Diff:

```text
reports/benchmark/phase_19_R5C_answer_slot_after_extraction_fixture_diff.md
reports/benchmark/phase_19_R5C_answer_slot_after_extraction_fixture_diff.csv
```

Result:

- compared_qids: `12`
- compared_fields_per_qid: `21`
- material_diff_count: `0`
- hard_stop_diff_count: `0`

## Smoke Results

| Run | raw_score_proxy | pass_proxy | contract_invalid | unsupported_confident | wrong_family | wrong_document | canonical_span_materialized | corpus_materialization_required | title_only_degraded | insufficient_canonical_span_evidence | min_answer_facts | evidence_slot_synthesis | evidence_required_slot_values | avg_answer_slot_coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| R4E baseline smoke20 | 140.23 / 200 | 15 / 20 | 0 | 0 | 0 | 1 | 18 | 2 | 2 | 2 | 18 | 14 | 118 | 0.828 |
| R5C smoke20 | 140.23 / 200 | 15 / 20 | 0 | 0 | 0 | 1 | 18 | 2 | 2 | 2 | 18 | 14 | 118 | 0.828 |
| R5B fixture | 79.36 / 120 | 8 / 12 | 0 | 0 | 0 | 1 | 10 | 2 | 2 | 2 | 10 | 9 | 72 | 0.827 |
| R5C fixture | 79.36 / 120 | 8 / 12 | 0 | 0 | 0 | 1 | 10 | 2 | 2 | 2 | 10 | 9 | 72 | 0.827 |

Run directories:

```text
reports/benchmark/runs/20260427T_phase19_R5C_answer_slot_fixture_after_extraction_envparity
reports/benchmark/runs/20260427T_phase19_R5C_answer_slot_smoke20_envparity
```

## Acceptance

- fixture material drift: PASS (`0`)
- fixture hard-stop drift: PASS (`0`)
- `raw_score_proxy >= 130/200`: PASS (`140.23/200`)
- `pass_proxy >= 12/20`: PASS (`15/20`)
- `wrong_family <= 3`: PASS (`0`)
- `wrong_document <= 5`: PASS (`1`)
- `contract_valid = 20/20`: PASS
- `unsupported_confident_answer = 0`: PASS
- `source_key_v2_collision = 0`: PASS
- `binding_source_key_collision = 0`: PASS
- answer slot metrics preserved: PASS

## Decision

R5C may be committed. R5D may proceed under the required slot matrix / resolver extraction boundary.
