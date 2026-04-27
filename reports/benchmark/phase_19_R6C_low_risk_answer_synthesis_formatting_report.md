# Phase 19 R6C Low-Risk Answer Synthesis Formatting Extraction Report

## Scope

R6C created `api-gateway/src/rag/answer_synthesis.py` and moved only low-risk formatting/serialization helpers behind compatibility wrappers in `api-gateway/src/routers/chat.py`.

Moved helpers:

- `_build_native_dialog_fallback_answer` -> `build_native_dialog_fallback_answer`
- `_build_persisted_raw_answer_snapshot` -> `build_persisted_raw_answer_snapshot`
- `_build_persisted_response_envelope_snapshot` -> `build_persisted_response_envelope_snapshot`
- `_sanitize_public_final_mode` -> `sanitize_public_final_mode`
- `_sanitize_public_answer_contract` -> `sanitize_public_answer_contract`
- `_verified_answer_plan_slot_value` -> `verified_answer_plan_slot_value`

Not moved in R6C:

- verified answer replacement decision
- answer mode decision
- confidence ceiling application
- insufficient evidence policy
- final answer selection between generated and verified answer
- answer contract repair
- evidence-slot synthesis
- OpenAI response construction

## Tests

- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/rag/answer_synthesis.py` -> PASS
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_answer_contract_v2.py -q` -> PASS, `30 passed`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "final_reason or insufficient_evidence or verified_answer_slot_plan or confidence" -q` -> PASS, `3 passed`

## Fixture Diff

- before_fixture: `reports/benchmark/phase_19_R6_answer_synthesis_fixture.csv`
- after_run: `reports/benchmark/runs/20260427T_phase19_R6C_answer_synthesis_fixture_after_extraction_envparity/candidate_answers.csv`
- after_fixture_csv: `reports/benchmark/phase_19_R6C_answer_synthesis_after_extraction_fixture.csv`
- diff_csv: `reports/benchmark/phase_19_R6C_answer_synthesis_after_extraction_fixture_diff.csv`
- diff_report: `reports/benchmark/phase_19_R6C_answer_synthesis_after_extraction_fixture_diff.md`
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
- `missing_slots`
- `contract_valid`

## Smoke20 Comparison

| Metric | R5E baseline | R6C smoke20 |
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

R6C fixture and smoke runs both used:

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

Note: provenance records `git_sha=7a53f38...` with a dirty worktree because R6C runtime was intentionally tested before committing the R6C extraction.

## Acceptance Decision

R6C is accepted.

- Fixture material drift: `0`
- Fixture hard-stop drift: `0`
- Smoke20 metrics preserved
- Contract validity preserved
- Unsupported confident answers did not increase
- No QID-specific or question-specific behavior was added

R6D can proceed under the verified answer plan / replacement helper extraction gate.
