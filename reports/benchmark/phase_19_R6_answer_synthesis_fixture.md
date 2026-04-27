# Phase 19 R6 Answer Synthesis Fixture

## Scope

Baseline fixture for R6 answer synthesis/finalization extraction. Runtime behavior was not changed before this fixture.

## Outputs

- run_dir: `reports/benchmark/runs/20260427T_phase19_R6B_answer_synthesis_fixture_envparity`
- fixture_csv: `reports/benchmark/phase_19_R6_answer_synthesis_fixture.csv`
- fixture_csv_sha256: `594cd0d5f8b2baa33c29615b6b4c2f18f69fed149adc9aec77f5d421cfc9d628`
- qid_count: `18`

## Fixture QIDs

CBG-01, CBG-02, CBG-03, CBG-04, MULGA-01, MULGA-03, KANUN-01, KANUN-19, CBKAR-08, TEB-01, YON-05, UY-07, KANUN-06, KKY-09, YON-07, MULGA-05, CBY-01, TEB-03

## Captured Fields

`qid`, `answer_text_hash`, `answer_text_normalized`, `final_answer_first_500_chars`, `answer_mode`, `confidence_0_100`, `final_reason`, `grounding_status`, `manual_review`, `unsupported_confident_answer`, `verified_answer_plan_present`, `verified_answer_plan_hash`, `direct_answer_slot`, `legal_basis_slots`, `temporal_validity_slot`, `scenario_application_slot`, `exception_or_limitation_slot`, `transition_or_replacement_slot`, `missing_slots`, `required_slots`, `filled_slots`, `answer_slot_map_hash`, `source_family_claimed`, `source_identifier_claimed`, `selected_document_id`, `selected_main_span_id`, `citation_labels`, `contract_valid`

## Runtime Provenance

- git_sha: `93b6ebf43e7481e323a494a7c40f95429eb191f6`
- branch: `bt/hukuk-ai-100-benchmark-hardening`
- api_url: `http://127.0.0.1:8000/v1`
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

## Score Summary

- raw_score_proxy: `111.58 / 180`
- pass_proxy: `11 / 18`
- answer_contract_invalid_count: `0`
- unsupported_confident_answer_count: `0`
- contract_valid_count: `18 / 18`
- unsupported_confident_answer_fixture_count: `0`
- verified_answer_plan_present_count: `16`
- manual_review_true_count: `18`
- wrong_family: `2`
- wrong_document: `2`
- minimum_answer_facts_present_count: `16`
- evidence_slot_synthesis_count: `13`
- avg_answer_slot_coverage_score: `0.834`

## Acceptance

- Fixture produced.
- Runtime behavior unchanged before fixture creation.
- Fields are sufficient for R6C/R6D/R6E hard-stop diff checks.
