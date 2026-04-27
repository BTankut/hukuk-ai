# Phase 19 R4D Main Article / Span Selector Extraction Report

## Status

R4D is accepted as behavior-preserving.

The main article/span selector body was moved from `chat.py` to `rag.article_span_selection` behind router compatibility wrappers. No selector ranking, article priority, support span ordering, same-document lock behavior, materialization threshold, answer synthesis, prompt, routing, or QID-specific logic was changed.

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
api-gateway/src/rag/article_span_selection.py
```

Moved behind compatibility wrappers in `chat.py`:

- `_select_article_span_evidence`
- `_apply_selected_document_only_bundle`
- `_annotate_article_span_selector_priority`

The moved selector uses explicit runtime dependency binding for router-local helpers that remain in `chat.py`. This keeps the extraction mechanical and avoids changing source identity, family gate, temporal, and answer-contract behavior in the same patch.

## Tests

Compile:

```bash
api-gateway/.venv/bin/python -m py_compile \
  api-gateway/src/routers/chat.py \
  api-gateway/src/rag/article_span_selection.py
```

Result: PASS

Focused selector tests:

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_chat_router.py \
  -k "selector_exact_span_priority or article_span_selector or selected_document_only_bundle or focus_chunks" -q
```

Result: `24 passed`

R4C regression tests:

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_chat_router.py \
  -k "canonical_span_materialization or title_only or candidate_completeness or article_span" -q
```

Result: `22 passed`

## Fixture Diff

Before fixture:

```text
reports/benchmark/phase_19_R4C_article_span_after_extraction_fixture.csv
```

After fixture:

```text
reports/benchmark/phase_19_R4D_article_span_after_extraction_fixture.csv
```

Diff:

```text
reports/benchmark/phase_19_R4D_article_span_after_extraction_fixture_diff.md
reports/benchmark/phase_19_R4D_article_span_after_extraction_fixture_diff.csv
```

Result:

- compared_qids: `11`
- compared_fields_per_qid: `24`
- material_diff_count: `0`
- hard_stop_diff_count: `0`

## Smoke Results

| Run | raw_score_proxy | pass_proxy | contract_invalid | unsupported_confident | wrong_family | wrong_document | canonical_span_materialized | corpus_materialization_required | title_only_degraded | insufficient_canonical_span_evidence | source_key_v2_collision | binding_collision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| R4C baseline smoke20 | 140.23 / 200 | 15 / 20 | 0 | 0 | 0 | 1 | 18 | 2 | 2 | 2 | 0 | 0 |
| R4D smoke20 | 140.23 / 200 | 15 / 20 | 0 | 0 | 0 | 1 | 18 | 2 | 2 | 2 | 0 | 0 |
| R4D focused span/materialization fixture | 78.48 / 110 | 8 / 11 | 0 | 0 | 0 | 1 | 11 | 0 | 0 | 0 | 0 | 0 |

Run directories:

```text
reports/benchmark/runs/20260427T_phase19_R4D_article_span_fixture_after_extraction_envparity
reports/benchmark/runs/20260427T_phase19_R4D_main_selector_smoke20_envparity
```

## Acceptance

- fixture material drift: PASS (`0`)
- fixture hard-stop drift: PASS (`0`)
- selected main span drift: PASS (`0`)
- selected document drift: PASS (`0`)
- selected support span material drift: PASS (`0`)
- `raw_score_proxy >= 130/200`: PASS (`140.23/200`)
- `pass_proxy >= 12/20`: PASS (`15/20`)
- `wrong_family <= 3`: PASS (`0`)
- `wrong_document <= 5`: PASS (`1`)
- `contract_valid = 20/20`: PASS
- `unsupported_confident_answer = 0`: PASS
- `source_key_v2_collision = 0`: PASS
- `binding_source_key_collision = 0`: PASS
- `canonical_span_materialized >= 18`: PASS (`18`)
- `corpus_materialization_required <= 2`: PASS (`2`)
- `title_only_degraded <= 2`: PASS (`2`)
- `insufficient_canonical_span_evidence <= 2`: PASS (`2`)

## Decision

R4D may be committed and R4E may proceed. R4E should be limited to candidate completeness and materialization gate extraction, with the same fixture and smoke gates preserved.
