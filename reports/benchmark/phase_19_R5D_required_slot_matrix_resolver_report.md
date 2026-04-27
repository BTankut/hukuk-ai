# Phase 19 R5D Required Slot Matrix / Resolver Extraction Report

## Status

R5D is accepted as behavior-preserving.

Required slot matrix / resolver helpers were moved from `chat.py` to `rag.answer_slots` behind router compatibility wrappers. No slot matrix content, task classification, family-specific slot list, required slot set, missing slot policy, rubric policy, confidence policy, answer synthesis, article/span selector, or QID-specific logic was changed.

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

Moved to:

```text
api-gateway/src/rag/answer_slots.py
```

Moved behind compatibility wrappers in `chat.py`:

- `_answer_template_for_query`
- `_query_contains_any`
- `_source_family_resolution_slot_values`
- `_source_families_for_required_slot_matrix`
- `_resolve_required_slot_matrix_for_query`
- `_must_have_fact_slots_for_query`
- `_query_needs_historical_transition_slots`
- `_query_needs_current_applicability_slot`

The source-family helper receives router-local source identity callbacks from `chat.py`. This keeps the extraction mechanical and avoids changing source identity or retrieval behavior in the same patch.

## Tests

Compile:

```bash
api-gateway/.venv/bin/python -m py_compile \
  api-gateway/src/routers/chat.py \
  api-gateway/src/rag/answer_slots.py
```

Result: PASS

Focused required-slot tests:

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_chat_router.py \
  -k "required_slot or task_type or family_slot or mulga or cb_genelge" -q
```

Result: `22 passed`

## Fixture Diff

Before fixture:

```text
reports/benchmark/phase_19_R5_answer_slot_fixture.csv
```

After fixture:

```text
reports/benchmark/phase_19_R5D_answer_slot_after_extraction_fixture.csv
```

Diff:

```text
reports/benchmark/phase_19_R5D_answer_slot_after_extraction_fixture_diff.md
reports/benchmark/phase_19_R5D_answer_slot_after_extraction_fixture_diff.csv
```

Result:

- compared_qids: `12`
- compared_fields_per_qid: `21`
- material_diff_count: `0`
- hard_stop_diff_count: `0`

## Smoke Results

| Run | raw_score_proxy | pass_proxy | contract_invalid | unsupported_confident | wrong_family | wrong_document | canonical_span_materialized | corpus_materialization_required | title_only_degraded | insufficient_canonical_span_evidence | min_answer_facts | evidence_slot_synthesis | evidence_required_slot_values | avg_answer_slot_coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| R5C smoke20 | 140.23 / 200 | 15 / 20 | 0 | 0 | 0 | 1 | 18 | 2 | 2 | 2 | 18 | 14 | 118 | 0.828 |
| R5D smoke20 | 140.23 / 200 | 15 / 20 | 0 | 0 | 0 | 1 | 18 | 2 | 2 | 2 | 18 | 14 | 118 | 0.828 |
| R5C fixture | 79.36 / 120 | 8 / 12 | 0 | 0 | 0 | 1 | 10 | 2 | 2 | 2 | 10 | 9 | 72 | 0.827 |
| R5D fixture | 79.36 / 120 | 8 / 12 | 0 | 0 | 0 | 1 | 10 | 2 | 2 | 2 | 10 | 9 | 72 | 0.827 |

Run directories:

```text
reports/benchmark/runs/20260427T_phase19_R5D_required_slot_fixture_after_extraction_envparity
reports/benchmark/runs/20260427T_phase19_R5D_required_slot_smoke20_envparity
```

## Acceptance

- required slot set drift: PASS (`0`)
- missing slot drift: PASS (`0`)
- fixture material drift: PASS (`0`)
- fixture hard-stop drift: PASS (`0`)
- `raw_score_proxy >= 130/200`: PASS (`140.23/200`)
- `pass_proxy >= 12/20`: PASS (`15/20`)
- `wrong_family <= 3`: PASS (`0`)
- `wrong_document <= 5`: PASS (`1`)
- `contract_valid = 20/20`: PASS
- `unsupported_confident_answer = 0`: PASS
- answer slot metrics preserved: PASS

## Decision

R5D may be committed. R5E may proceed under the slot coverage / runtime rubric helper extraction boundary.
