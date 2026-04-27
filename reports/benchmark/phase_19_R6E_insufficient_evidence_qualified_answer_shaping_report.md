# Phase 19 R6E Insufficient Evidence / Qualified Answer Shaping Extraction Report

## Scope

R6E moved insufficient evidence / qualified answer shaping helpers into `api-gateway/src/rag/answer_synthesis.py` behind compatibility wrappers in `api-gateway/src/routers/chat.py`.

Moved helpers:

- `_resolve_contract_suppressed_answer_text` -> `resolve_contract_suppressed_answer_text`
- `_apply_evidence_slot_synthesis_to_answer_text` -> `apply_evidence_slot_synthesis_to_answer_text`
- `_resolve_public_answer_text` -> `resolve_public_answer_text`

Still router-local:

- finalization orchestration in `_finalize_chat_response`
- answer contract repair
- confidence/final_reason mutation
- controlled replacement side effects after verified plan replacement
- trace/audit/OpenAI response construction

## Tests

- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/rag/answer_synthesis.py` -> PASS
- Brief-specified pattern `-k "insufficient_evidence or title_only_answer_degraded or manual_review or partial_grounding or confidence"` selected no tests in `test_chat_router.py` and exited with pytest code `5`.
- Substitute existing focused coverage: `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_answer_contract_v2.py -q` -> PASS, `30 passed`
- Substitute router coverage: `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "evidence_slot_synthesis or verified_answer_slot_plan or insufficient_canonical_span_evidence or title_only_answer_degraded or manual_review_trigger_reason or selector_insufficient_support" -q` -> PASS, `6 passed`

## Fixture Diff

- before_fixture: `reports/benchmark/phase_19_R6_answer_synthesis_fixture.csv`
- after_run: `reports/benchmark/runs/20260427T_phase19_R6E_insufficient_evidence_fixture_after_extraction_envparity/candidate_answers.csv`
- after_fixture_csv: `reports/benchmark/phase_19_R6E_answer_synthesis_after_extraction_fixture.csv`
- diff_csv: `reports/benchmark/phase_19_R6E_answer_synthesis_after_extraction_fixture_diff.csv`
- diff_report: `reports/benchmark/phase_19_R6E_answer_synthesis_after_extraction_fixture_diff.md`
- compared_qids: `18`
- compared_fields_per_qid: `27`
- material_diff_count: `0`
- hard_stop_diff_count: `0`

Focused R6E QIDs:

- `CBKAR-08`
- `KANUN-06`
- `MULGA-01`
- `MULGA-05`

All focused QIDs had no fixture field drift.

## Smoke20 Comparison

| Metric | R6D baseline | R6E smoke20 |
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

Focused smoke:

- CB_GENELGE: `4 / 4` PASS
- MULGA: `3 / 5` PASS
- KANUN focused subset: `2 / 3` PASS
- insufficient/title-only focused subset: `1 / 4` PASS by deterministic proxy, with no behavior drift from baseline

## Runtime Provenance

R6E fixture and smoke runs both used:

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

Note: provenance records `git_sha=edb763a...` with a dirty worktree because R6E runtime was intentionally tested before committing the R6E extraction.

## Acceptance Decision

R6E is accepted.

- Fixture diff: `0`
- Hard-stop diff: `0`
- 20-QID smoke baseline gate preserved
- Unsupported confident answers remained `0`
- Title-only / insufficient canonical evidence counts preserved
- No answer text, answer mode, confidence, final_reason, grounding, manual_review, verified plan, or contract-validity drift
- No QID-specific or question-specific behavior was added

R6F completion reporting can proceed.
