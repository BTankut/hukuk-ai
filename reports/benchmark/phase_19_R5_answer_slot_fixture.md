# Phase 19 R5 Answer Slot Fixture

## Status

R5B fixture generated. Runtime code was not changed in this step.

## Run

- run_dir: `reports/benchmark/runs/20260427T_phase19_R5B_answer_slot_fixture_envparity`
- fixture_csv: `reports/benchmark/phase_19_R5_answer_slot_fixture.csv`
- fixture_sha256: `607117e0c86207421c7aee560cf0c1f16452c40e92f854d989108aca114bac17`
- qids: `12`

## Runtime Provenance

- `DGX_MODEL=/models/merged_model_fabric_stage_20260321`
- `MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024`
- `MILVUS_ENTITY_COUNT=349191`
- `VECTOR_DIMENSION=1024`
- `EMBEDDING_BACKEND=remote`
- `EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1`
- `EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct`
- `GUARDRAILS_ENABLED=false`
- `PRESIDIO_ENABLED=false`

## Fixture Fields

`qid`, `task_type`, `source_family_claimed`, `selected_document_id`, `selected_main_span_id`, `required_slots`, `filled_slots`, `missing_slots`, `answer_slot_map`, `evidence_slot_synthesis_count`, `minimum_answer_facts_present`, `minimum_answer_facts_present_count`, `runtime_rubric_sufficient`, `answer_slot_coverage_score`, `evidence_required_slot_value_count`, `slot_missing_reasons`, `verified_answer_plan_present`, `final_reason`, `confidence_0_100`, `answer_mode`, `grounding_status`, `unsupported_confident_answer`

## Metrics

- raw_score_proxy: `79.36 / 120`
- pass_proxy: `8 / 12`
- answer_contract_invalid_count: `0`
- unsupported_confident_answer_count: `0`
- minimum_answer_facts_present_count: `10`
- runtime_rubric_sufficient_count: `10`
- verified_answer_plan_present_count: `10`
- unsupported_confident_answer_fixture_count: `0`
- avg_answer_slot_coverage_score: `0.827`
- evidence_slot_synthesis_count_total: `18`
- evidence_required_slot_value_count_total: `72`

## Acceptance

- Fixture CSV generated: PASS
- Fixture report generated: PASS
- Runtime behavior unchanged: PASS
- Provenance captured: PASS
