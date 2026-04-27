# Phase 19 R5 Answer Slot Extraction Completion Report

## Execution Scope

R5 extracted answer-slot and runtime completeness/rubric logic from `api-gateway/src/routers/chat.py` into `api-gateway/src/rag/answer_slots.py` through bounded, acceptance-gated steps. No QID-specific or question-specific behavior was added.

Commits:

- R5A inventory: `ea410b897ce3101b86d10539c63784c6fb0283d9`
- R5B fixture: `42ba7c42fe48d3abc5af418723fadbd15cc195dd`
- R5C answer slot serialization extraction: `d079e77d808d55e9a8d2810578bce9f85af8400c`
- R5D required slot matrix/resolver extraction: `7b806216ba9519b6a2bf7b52d8ba78ad71b1004c`
- R5E slot coverage/runtime rubric extraction: `41a6b854fc6e9addfe9bce04409a4209f00d9e88`

Reports:

- R5A: `reports/benchmark/phase_19_R5_answer_slot_inventory.md`
- R5B: `reports/benchmark/phase_19_R5_answer_slot_fixture.md`
- R5C: `reports/benchmark/phase_19_R5C_low_risk_answer_slot_serialization_report.md`
- R5D: `reports/benchmark/phase_19_R5D_required_slot_matrix_resolver_report.md`
- R5E: `reports/benchmark/phase_19_R5E_slot_coverage_runtime_rubric_report.md`

## Extracted Module Surface

`api-gateway/src/rag/answer_slots.py` now owns these answer-slot helpers:

- `answer_template_for_query`
- `query_contains_any`
- `source_family_resolution_slot_values`
- `source_families_for_required_slot_matrix`
- `resolve_required_slot_matrix_for_query`
- `must_have_fact_slots_for_query`
- `query_needs_historical_transition_slots`
- `query_needs_current_applicability_slot`
- `required_slot_schema`
- `compact_slot_value`
- `slot_quote_hash`
- `answer_slot_extraction_method`
- `best_evidence_row_for_matrix_slot`
- `build_verified_answer_slots`
- `count_answer_fact_units`
- `build_completeness_synthesis_features`

`chat.py` retains compatibility wrappers for the moved helpers and passes router-local callbacks where the extracted code still needs runtime selector context.

Router-local answer-slot logic intentionally retained:

- `_satisfied_completeness_slots`
- `_evidence_supported_completeness_slots`
- `_slot_keyword_hints`
- `_slot_hint_in_surface`
- `_slot_hint_score`
- `_chunk_is_historical_current_counterpart`
- `_chunk_span_id`
- `_chunk_article`
- `_chunk_supports_slot`
- `_select_chunk_for_slot`
- `_selector_primary_chunk`
- `_chunk_source_identity_label`
- `_effective_state_label`
- `_best_slot_excerpt`
- `_slot_value_from_chunk`
- `_build_evidence_required_slot_values`
- `_build_answer_slot_evidence_map`

These remaining helpers depend heavily on `RetrievedChunk`, selector trace shape, and router-side evidence/ranking state. They should move only under a later, separately gated selector/evidence extraction phase. Answer synthesis and runtime orchestration also remain in `chat.py` for R6.

## Acceptance Evidence

Fixture baseline:

- fixture_csv: `reports/benchmark/phase_19_R5_answer_slot_fixture.csv`
- fixture_sha256: `607117e0c86207421c7aee560cf0c1f16452c40e92f854d989108aca114bac17`
- qids: `12`
- raw_score_proxy: `79.36 / 120`
- pass_proxy: `8 / 12`
- answer_contract_invalid_count: `0`
- unsupported_confident_answer_count: `0`
- minimum_answer_facts_present_count: `10`
- runtime_rubric_sufficient_count: `10`
- avg_answer_slot_coverage_score: `0.827`
- evidence_required_slot_value_count_total: `72`

Fixture drift gates:

| Step | Compared QIDs | Fields / QID | Material Diff | Hard Stop Diff |
| --- | ---: | ---: | ---: | ---: |
| R5C | 12 | 21 | 0 | 0 |
| R5D | 12 | 21 | 0 | 0 |
| R5E | 12 | 21 | 0 | 0 |

Smoke20 regression gates:

| Metric | R5C | R5D | R5E |
| --- | ---: | ---: | ---: |
| total | 20 | 20 | 20 |
| raw_score_proxy | 140.23 | 140.23 | 140.23 |
| pass_proxy | 15 | 15 | 15 |
| answer_contract_invalid_count | 0 | 0 | 0 |
| unsupported_confident_answer_count | 0 | 0 | 0 |
| canonical_span_materialized_count | 18 | 18 | 18 |
| corpus_materialization_required_count | 2 | 2 | 2 |
| title_only_answer_degraded_count | 2 | 2 | 2 |
| insufficient_canonical_span_evidence_count | 2 | 2 | 2 |
| minimum_answer_facts_present_count | 18 | 18 | 18 |
| evidence_slot_synthesis_count | 14 | 14 | 14 |
| evidence_required_slot_value_count_total | 118 | 118 | 118 |
| avg_answer_slot_coverage_score | 0.828 | 0.828 | 0.828 |

R5E runtime provenance:

- gateway_model_name: `hukuk-ai-poc`
- dgx_base_url: `http://192.168.12.243:30000/v1`
- dgx_model_env: `/models/merged_model_fabric_stage_20260321`
- milvus_collection: `mevzuat_faz1_shadow_20260418_compat1024`
- milvus_entity_count: `349191`
- vector_dimension: `1024`
- embedding_backend: `remote`
- embedding_base_url: `http://127.0.0.1:8081/v1`
- guardrails_enabled: `false`
- presidio_enabled: `false`

## Verification Commands

Executed during R5:

- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/rag/answer_slots.py`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "answer_slot or evidence_slot or slot_coverage" -q`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "required_slot or task_type or family_slot or mulga or cb_genelge" -q`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "slot_coverage or minimum_answer_facts or rubric_sufficient or evidence_required_slot" -q`
- R5B/R5C/R5D/R5E 12-QID fixture runs
- R5C/R5D/R5E 20-QID smoke runs

Known stale test status:

- The broad router test suite remains outside the R5 acceptance gate because it contains stale expectations unrelated to this mechanical extraction path.
- Focused answer-slot, required-slot, and runtime-rubric tests passed.
- Runtime fixture and smoke gates are the binding acceptance evidence for R5.

## Completion Decision

R5 is complete.

- The answer-slot extraction module exists and is wired.
- Fixture hard-stop fields stayed unchanged across R5C/R5D/R5E.
- Smoke20 metrics stayed unchanged across R5C/R5D/R5E.
- The active runtime path was tested against `hukuk-ai-poc` on the dgxnode1 merged model endpoint.
- No QID-specific or question-specific changes were introduced.

R6 can proceed under a separate brief. The recommended R6 boundary is to keep answer synthesis/runtime orchestration separate from the selector/evidence-ranking helpers unless the next brief explicitly gates those moves with the same fixture and smoke discipline.
