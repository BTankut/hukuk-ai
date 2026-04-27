# Phase 19 R4E Candidate Completeness / Materialization Gate Extraction Report

## Status

R4E is accepted as behavior-preserving.

Candidate completeness and canonical span materialization gate helpers were moved from `chat.py` to `rag.article_span_selection` behind router compatibility wrappers. No candidate completeness threshold, title-only degradation policy, insufficient evidence mode, corpus materialization policy, confidence ceiling, answer synthesis, selector priority, or QID-specific logic was changed.

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

- `_DOCUMENT_LEVEL_BODY_SPAN_FAMILIES`
- `_ARTICLE_ZERO_BODY_EXTRACTION_FAMILIES`
- `_chunk_allows_document_level_body_span`
- `_article_zero_body_query_allows_extraction`
- `_chunk_allows_article_zero_body_extraction`
- `_annotate_canonical_span_materialization`

The moved helpers use explicit runtime dependency binding for router-local helpers that remain in `chat.py`. This keeps the extraction mechanical and avoids changing source identity, family routing, evidence sufficiency, materialization classification, or answer-contract behavior in the same patch.

## Tests

Compile:

```bash
api-gateway/.venv/bin/python -m py_compile \
  api-gateway/src/routers/chat.py \
  api-gateway/src/rag/article_span_selection.py
```

Result: PASS

Focused candidate completeness/materialization tests:

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_chat_router.py \
  -k "candidate_completeness or insufficient_canonical_span_evidence or title_only_answer_degraded or corpus_materialization" -q
```

Result: `1 passed`

R4C/R4D selector regression tests:

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_chat_router.py \
  -k "canonical_span_materialization or title_only or article_span or selector_exact_span_priority or selected_document_only_bundle" -q
```

Result: `25 passed`

## Fixture Diff

Before baseline:

```text
reports/benchmark/runs/20260427T_phase19_R4D_article_span_fixture_after_extraction_envparity/candidate_answers.csv
```

After fixture:

```text
reports/benchmark/phase_19_R4E_candidate_completeness_after_extraction_fixture.csv
```

Diff:

```text
reports/benchmark/phase_19_R4E_candidate_completeness_after_extraction_fixture_diff.md
reports/benchmark/phase_19_R4E_candidate_completeness_after_extraction_fixture_diff.csv
```

Result:

- compared_qids: `11`
- compared_fields_per_qid: `18`
- material_diff_count: `0`
- hard_stop_diff_count: `0`

## Smoke Results

| Run | raw_score_proxy | pass_proxy | contract_invalid | unsupported_confident | wrong_family | wrong_document | canonical_span_materialized | corpus_materialization_required | title_only_degraded | insufficient_canonical_span_evidence | source_key_v2_collision | binding_collision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| R4D baseline smoke20 | 140.23 / 200 | 15 / 20 | 0 | 0 | 0 | 1 | 18 | 2 | 2 | 2 | 0 | 0 |
| R4E smoke20 | 140.23 / 200 | 15 / 20 | 0 | 0 | 0 | 1 | 18 | 2 | 2 | 2 | 0 | 0 |
| R4E focused materialization fixture | 78.48 / 110 | 8 / 11 | 0 | 0 | 0 | 1 | 11 | 0 | 0 | 0 | 0 | 0 |

Run directories:

```text
reports/benchmark/runs/20260427T_phase19_R4E_candidate_completeness_fixture_after_extraction_envparity
reports/benchmark/runs/20260427T_phase19_R4E_candidate_completeness_smoke20_envparity
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
- `canonical_span_materialized >= 18`: PASS (`18`)
- `corpus_materialization_required <= 2`: PASS (`2`)
- `title_only_degraded <= 2`: PASS (`2`)
- `insufficient_canonical_span_evidence <= 2`: PASS (`2`)

## Decision

R4E may be committed. R4 article/span selection extraction completion report may proceed.
