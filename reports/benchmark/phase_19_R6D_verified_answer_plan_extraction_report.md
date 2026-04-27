# Phase 19 R6D Verified Answer Plan / Replacement Helper Extraction Report

## Scope

R6D moved verified answer plan and controlled replacement helpers into `api-gateway/src/rag/answer_synthesis.py` behind compatibility wrappers in `api-gateway/src/routers/chat.py`.

Moved helpers:

- `_verified_slots_by_name` -> `verified_slots_by_name`
- `_first_verified_plan_value` -> `first_verified_plan_value`
- `_build_verified_answer_plan` -> `build_verified_answer_plan`
- `_verified_slot_controlled_replacement_allowed` -> `verified_slot_controlled_replacement_allowed`
- `_apply_verified_answer_slot_plan_to_answer_text` -> `apply_verified_answer_slot_plan_to_answer_text`

Still router-local:

- confidence/final_reason mutation after controlled replacement
- final answer orchestration in `_finalize_chat_response`
- evidence slot synthesis
- contract repair and controlled fallback
- insufficient canonical evidence policy
- OpenAI response construction

## Tests

- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/rag/answer_synthesis.py` -> PASS
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "verified_answer_slot_plan or verified_slot_replacement or completeness_synthesis or final_reason" -q` -> PASS, `12 passed`

## Fixture Diff

- before_fixture: `reports/benchmark/phase_19_R6_answer_synthesis_fixture.csv`
- after_run: `reports/benchmark/runs/20260427T_phase19_R6D_verified_answer_plan_fixture_after_extraction_envparity/candidate_answers.csv`
- after_fixture_csv: `reports/benchmark/phase_19_R6D_answer_synthesis_after_extraction_fixture.csv`
- diff_csv: `reports/benchmark/phase_19_R6D_answer_synthesis_after_extraction_fixture_diff.csv`
- diff_report: `reports/benchmark/phase_19_R6D_answer_synthesis_after_extraction_fixture_diff.md`
- compared_qids: `18`
- compared_fields_per_qid: `27`
- material_diff_count: `0`
- hard_stop_diff_count: `0`

Hard-stop fields:

- `answer_text_hash`
- `answer_mode`
- `confidence_0_100`
- `final_reason`
- `grounding_status`
- `manual_review`
- `unsupported_confident_answer`
- `verified_answer_plan_hash`
- `direct_answer_slot`
- `legal_basis_slots`
- `missing_slots`
- `contract_valid`

## Smoke20 Comparison

| Metric | R6C baseline | R6D smoke20 |
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

## Runtime Provenance

R6D fixture and smoke runs both used:

- gateway_model_name: `hukuk-ai-poc`
- dgx_base_url: `http://192.168.12.243:30000/v1`
- dgx_model_env: `/models/merged_model_fabric_stage_20260321`
- milvus_collection: `mevzuat_faz1_shadow_20260418_compat1024`
- milvus_entity_count: `349191`
- vector_dimension: `1024`
- embedding_backend: `remote`
- embedding_base_url: `http://127.0.0.1:8081/v1`
- embedding_model: `intfloat/multilingual-e5-large-instruct`
- guardrails_enabled: `false`
- presidio_enabled: `false`

Note: provenance records `git_sha=088526c...` with a dirty worktree because R6D runtime was intentionally tested before committing the R6D extraction.

## Acceptance Decision

R6D is accepted.

- Fixture diff: `0`
- Hard-stop diff: `0`
- Smoke20 baseline gate preserved
- Unsupported confident answers remained `0`
- No answer mode drift
- No confidence drift
- No final_reason drift
- No QID-specific or question-specific behavior was added

R6E can proceed under the insufficient evidence / qualified answer shaping extraction gate.
