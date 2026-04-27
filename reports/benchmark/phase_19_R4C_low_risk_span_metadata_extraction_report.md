# Phase 19 R4C Low-Risk Article / Span Metadata Helper Extraction Report

## Status

R4C is accepted as behavior-preserving.

Scope was limited to low-risk article/span metadata and classification helper extraction. No selector ranking, candidate completeness threshold, materialization policy, answer synthesis, prompt, routing, or QID-specific logic was changed.

## Runtime Provenance

- `DGX_BASE_URL=http://192.168.12.243:30000/v1`
- `DGX_MODEL=/models/merged_model_fabric_stage_20260321`
- `MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024`
- `EMBEDDING_BACKEND=remote`
- `EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1`
- `EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct`
- `GUARDRAILS_ENABLED=false`
- `PRESIDIO_ENABLED=false`
- `VERIFICATION_ENABLED=false`

## Moved Helpers

New module:

```text
api-gateway/src/rag/article_span_selection.py
```

Moved behind compatibility wrappers in `chat.py`:

- `_resolve_chunk_span_id`
- `_extract_query_clause_tokens`
- `_extract_query_article_tokens`
- `_chunk_article_matches`
- `_article_numeric_value`
- `_article_window_distance`
- `_query_article_alignment`
- `_support_contains_temporal_clause`
- `_support_contains_exception_signal`
- `_contains_temporal_clause_signal`
- `_contains_exception_signal`
- `_strip_chunk_citation_prefix`
- `_chunk_body_text_for_quality`
- `_chunk_body_text_quality`
- `_chunk_has_selectable_body_span`
- `_chunk_has_non_title_body_span`

## Verification

Focused static/test gates:

```bash
api-gateway/.venv/bin/python -m py_compile \
  api-gateway/src/routers/chat.py \
  api-gateway/src/rag/article_span_selection.py

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_chat_router.py \
  -k "canonical_span_materialization or title_only or candidate_completeness or article_span" -q
```

Result:

- `py_compile`: PASS
- focused pytest: `22 passed`

## Fixture Diff

Before fixture:

```text
reports/benchmark/phase_19_R4_article_span_fixture.csv
```

After fixture:

```text
reports/benchmark/phase_19_R4C_article_span_after_extraction_fixture.csv
```

Diff:

```text
reports/benchmark/phase_19_R4C_article_span_after_extraction_fixture_diff.md
reports/benchmark/phase_19_R4C_article_span_after_extraction_fixture_diff.csv
```

Result:

- compared_qids: `11`
- compared_fields_per_qid: `24`
- material_diff_count: `0`
- hard_stop_diff_count: `0`

## Smoke Results

| Run | raw_score_proxy | pass_proxy | contract_invalid | unsupported_confident | wrong_family | wrong_document | canonical_span_materialized | corpus_materialization_required | title_only_degraded | insufficient_canonical_span_evidence | source_key_v2_collision | binding_collision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| R3G baseline smoke20 | 140.23 / 200 | 15 / 20 | 0 | 0 | 0 | 1 | 18 | 2 | 2 | 2 | 0 | 0 |
| R4C smoke20 | 140.23 / 200 | 15 / 20 | 0 | 0 | 0 | 1 | 18 | 2 | 2 | 2 | 0 | 0 |
| R4C CBKAR-08/KANUN-06 mini | 15.79 / 20 | 1 / 2 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |

Run directories:

```text
reports/benchmark/runs/20260427T_phase19_R4C_article_span_fixture_after_extraction_envparity
reports/benchmark/runs/20260427T_phase19_R4C_low_risk_smoke20_envparity
reports/benchmark/runs/20260427T_phase19_R4C_cbkar08_kanun06_mini_smoke_envparity
```

## Acceptance

- Fixture hard-stop drift: PASS (`0`)
- `raw_score_proxy >= 130/200`: PASS (`140.23/200`)
- `pass_proxy >= 12/20`: PASS (`15/20`)
- `wrong_family <= 3`: PASS (`0`)
- `wrong_document <= 5`: PASS (`1`)
- `contract_valid = 20/20`: PASS
- `canonical_span_materialized_count` did not decrease: PASS (`18 -> 18`)
- `corpus_materialization_required_count` did not increase: PASS (`2 -> 2`)
- unsupported confident did not increase: PASS (`0 -> 0`)
- source-key v2 collision: PASS (`0`)
- binding source-key collision: PASS (`0`)

## Decision

R4C may be committed and R4D may proceed. R4D remains high risk and must keep `_select_article_span_evidence` behavior mechanically identical, with fixture hard-stop diff as the stop gate.
