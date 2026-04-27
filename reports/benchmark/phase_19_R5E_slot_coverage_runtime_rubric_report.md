# Phase 19 R5E Slot Coverage / Runtime Rubric Extraction Report

## Scope

R5E extracted the top-level answer completeness and runtime rubric feature synthesis into `api-gateway/src/rag/answer_slots.py` without changing the runtime answer contract behavior.

Moved helpers:

- `_INLINE_CITATION_RE`
- `_count_answer_fact_units` -> `count_answer_fact_units`
- `_build_completeness_synthesis_features` -> `build_completeness_synthesis_features`

`api-gateway/src/routers/chat.py` now keeps compatibility wrappers and passes router-local selector callbacks into the extracted module.

Conservative boundary retained in `chat.py`:

- Low-level evidence-to-slot selector/ranking helpers remain router-local callbacks.
- Source/chunk routing callbacks remain router-local.
- Answer synthesis and prompt/runtime orchestration remain router-local and are not part of R5E.

This keeps R5E as a mechanical extraction step, not a quality-tuning step.

## Verification

Static and focused tests:

- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/rag/answer_slots.py` -> PASS
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "slot_coverage or minimum_answer_facts or rubric_sufficient or evidence_required_slot" -q` -> PASS, `1 passed`

Runtime was restarted on port `8000` with the R5E code path before fixture and smoke runs.

## Runtime Provenance

R5E smoke run:

- run_dir: `reports/benchmark/runs/20260427T_phase19_R5E_slot_coverage_smoke20_envparity`
- api_url: `http://127.0.0.1:8000/v1`
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

Note: runtime provenance records `git_sha=7b80621...` with `dirty_worktree=True` because R5E code was intentionally tested before the R5E commit.

## Fixture Diff

Fixture diff:

- before_fixture: `reports/benchmark/phase_19_R5_answer_slot_fixture.csv`
- after_fixture_csv: `reports/benchmark/phase_19_R5E_answer_slot_after_extraction_fixture.csv`
- diff_csv: `reports/benchmark/phase_19_R5E_answer_slot_after_extraction_fixture_diff.csv`
- diff_report: `reports/benchmark/phase_19_R5E_answer_slot_after_extraction_fixture_diff.md`
- compared_qids: `12`
- compared_fields_per_qid: `21`
- material_diff_count: `0`
- hard_stop_diff_count: `0`

Hard-stop fields covered:

- `required_slots`
- `filled_slots`
- `missing_slots`
- `answer_slot_map`
- `evidence_slot_synthesis_count`
- `minimum_answer_facts_present`
- `minimum_answer_facts_present_count`
- `runtime_rubric_sufficient`
- `answer_slot_coverage_score`
- `evidence_required_slot_value_count`
- `slot_missing_reasons`
- `confidence_0_100`
- `answer_mode`
- `grounding_status`

## Smoke20 Comparison

| Metric | R5D smoke20 | R5E smoke20 |
| --- | ---: | ---: |
| total | 20 | 20 |
| raw_score_proxy | 140.23 | 140.23 |
| pass_proxy | 15 | 15 |
| answer_contract_invalid_count | 0 | 0 |
| unsupported_confident_answer_count | 0 | 0 |
| wrong_family | 0 | 0 |
| wrong_document | 1 | 1 |
| canonical_span_materialized_count | 18 | 18 |
| corpus_materialization_required_count | 2 | 2 |
| title_only_answer_degraded_count | 2 | 2 |
| insufficient_canonical_span_evidence_count | 2 | 2 |
| source_key_v2_collision_detected_count | 0 | 0 |
| binding_source_key_collision_detected_count | 0 | 0 |
| minimum_answer_facts_present_count | 18 | 18 |
| evidence_slot_synthesis_count | 14 | 14 |
| evidence_required_slot_value_count_total | 118 | 118 |
| avg_answer_slot_coverage_score | 0.828 | 0.828 |

## Answer Slot / Rubric Metrics

R5E smoke20 answer-slot metrics:

- runtime_rubric_sufficient / rubric_sufficient: `18 / 20`
- legally_aligned_but_partial: `2 / 20`
- minimum_answer_facts_present_count: `18`
- evidence_slot_reentry_count: `1`
- evidence_slot_synthesis_count: `14`
- evidence_required_slot_value_count_total: `118`
- avg_evidence_required_slot_value_count: `5.9`
- avg_answer_slot_coverage_score: `0.828`
- answer_slot_evidence_below_threshold: `2`

## Acceptance Decision

R5E is accepted.

- No fixture drift was detected.
- No smoke20 metric drift was detected.
- No answer contract invalidation was introduced.
- No unsupported confident answer was introduced.
- The code change is mechanical extraction only; it does not add QID-specific or question-specific behavior.

R5F completion reporting can proceed under the R5 brief.
