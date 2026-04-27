# Phase 19 R4 Article / Span Selection Extraction Completion Report

## Status

R4 is complete and accepted as behavior-preserving.

The article/span selection surface was extracted into `api-gateway/src/rag/article_span_selection.py` in gated steps. No benchmark-quality logic, selector priority, materialization threshold, title-only policy, confidence policy, answer synthesis, prompt construction, retrieval orchestration, or QID-specific logic was changed.

## Commit List

| Step | Commit | Scope |
|---|---|---|
| R4A | `0a4ebcd` | Article/span selection inventory |
| R4B | `11e6670` | Article/span fixture creation |
| R4C | `8110ea7` | Low-risk span metadata helper extraction |
| R4D | `5033986` | Main article/span selector extraction |
| R4E | `d44205716f45e0d75a3089d994766e1eddbe7298` | Candidate completeness/materialization gate extraction |

## Extracted Helper Surface

`article_span_selection.py` now owns:

- Low-risk span metadata helpers: `_resolve_chunk_span_id`, `_extract_query_clause_tokens`, `_extract_query_article_tokens`, `_chunk_article_matches`, `_article_numeric_value`, `_article_window_distance`, `_query_article_alignment`.
- Body quality helpers: `_strip_chunk_citation_prefix`, `_chunk_body_text_for_quality`, `_chunk_body_text_quality`, `_chunk_has_selectable_body_span`, `_chunk_has_non_title_body_span`.
- Signal helpers: `_support_contains_temporal_clause`, `_support_contains_exception_signal`, `_contains_temporal_clause_signal`, `_contains_exception_signal`.
- Main selector helpers: `_select_article_span_evidence`, `_apply_selected_document_only_bundle`, `_annotate_article_span_selector_priority`.
- Candidate/materialization helpers: `_chunk_allows_document_level_body_span`, `_article_zero_body_query_allows_extraction`, `_chunk_allows_article_zero_body_extraction`, `_annotate_canonical_span_materialization`.

## Remaining Router Logic

`chat.py` intentionally retains compatibility wrappers and router-local dependencies that cross into source identity, temporal routing, retrieval orchestration, answer slots, and answer synthesis. The major article/span entrypoints still exist as wrappers so downstream call sites remain stable while implementation lives in `rag.article_span_selection`.

Known remaining article/span-adjacent router surface includes source-key resolution wrappers, collision profile wrappers, excerpt construction, temporal/current-validity policy, answer slot extraction, final answer rendering, and retrieval orchestration. These are outside R4 and should only move under a separate R5 or later brief.

## Fixture Summary

| Step | Before | After | Compared QIDs | Compared fields/QID | Material diff | Hard-stop diff |
|---|---|---|---:|---:|---:|---:|
| R4C | `phase_19_R4_article_span_fixture.csv` | `phase_19_R4C_article_span_after_extraction_fixture.csv` | 11 | 24 | 0 | 0 |
| R4D | `phase_19_R4C_article_span_after_extraction_fixture.csv` | `phase_19_R4D_article_span_after_extraction_fixture.csv` | 11 | 24 | 0 | 0 |
| R4E | `R4D candidate_answers.csv` | `phase_19_R4E_candidate_completeness_after_extraction_fixture.csv` | 11 | 18 | 0 | 0 |

R4E used the R4D candidate-answer output for fields introduced by the R4E hard-stop list that were not present in the narrower R4D fixture CSV. No fixture field drift was detected.

## Smoke Delta

| Run | raw_score_proxy | pass_proxy | contract_invalid | unsupported_confident | wrong_family | wrong_document | canonical_span_materialized | corpus_materialization_required | title_only_degraded | insufficient_canonical_span_evidence | source_key_v2_collision | binding_collision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| R4C smoke20 | 140.23 / 200 | 15 / 20 | 0 | 0 | 0 | 1 | 18 | 2 | 2 | 2 | 0 | 0 |
| R4D smoke20 | 140.23 / 200 | 15 / 20 | 0 | 0 | 0 | 1 | 18 | 2 | 2 | 2 | 0 | 0 |
| R4E smoke20 | 140.23 / 200 | 15 / 20 | 0 | 0 | 0 | 1 | 18 | 2 | 2 | 2 | 0 | 0 |

R4C, R4D, and R4E are materially identical on the 20-QID smoke set.

## Focused Materialization Smoke

R4E focused materialization fixture:

- total: `11`
- raw_score_proxy: `78.48 / 110`
- pass_proxy: `8 / 11`
- wrong_family: `0`
- wrong_document: `1`
- contract_invalid: `0`
- unsupported_confident: `0`
- canonical_span_materialized: `11`
- corpus_materialization_required: `0`
- title_only_degraded: `0`
- insufficient_canonical_span_evidence: `0`
- source_key_v2_collision: `0`
- binding_collision: `0`

Run directory:

```text
reports/benchmark/runs/20260427T_phase19_R4E_candidate_completeness_fixture_after_extraction_envparity
```

## Runtime Provenance

Final R4E smoke provenance:

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
- gateway model: `hukuk-ai-poc`

## Known Stale Tests

The broad router test set was not used as the R4 acceptance gate because the R4D/R4E briefs identify it as stale for this phase. Acceptance used compile, focused router tests, fixture hard-stop diff, 20-QID smoke, focused materialization smoke, and runtime provenance checks.

## R5 Readiness

R5 may proceed under a separate brief.

Recommended R5 boundary: extract answer slot logic into `api-gateway/src/rag/answer_slots.py`, limited to required slot matrix lookup, evidence-to-slot trace helpers, missing slot reasons, runtime rubric sufficiency helpers, and slot coverage calculations. R5 should preserve the same no-QID-specific and behavior-preserving gate discipline.
