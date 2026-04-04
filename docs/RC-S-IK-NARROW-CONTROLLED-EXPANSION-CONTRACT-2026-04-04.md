# RC-S IK Narrow Controlled Expansion Contract 2026-04-04

## Official Contract

- official_base = `RC-R`
- accepted_expanded_source_set = `[TMK core corpus, TCK, HMK, CMK, TTK]`
- next_source_class = `İK`
- execution_authorized_in_this_phase = `false`
- steering_scope = `topology_closure_only`

## Source Readiness Prerequisites

- inventory_manifest_ready = `true`
- raw_storage_location_ready = `true`
- canonical_source_locator_ready = `true`
- metadata_mapping_complete = `true`
- source_id_contract_ready = `true`
- yururluk_contract_ready = `true`
- raw_storage_location = `data/primary_sources/raw/ik/`
- canonical_source_locator = `law://ik/2004/{source_id}`
- source_id_pattern = `IK:2004:m<madde_no>:f<fikra_no>:from<yururluk_baslangic>:to<yururluk_bitis>`

## Contamination Exclusions

- excluded_source_classes = `[Yargıtay İçtihat Merkezi (YİM), customer/private documents, external internet-derived ad hoc content]`
- excluded_source_contamination_found = `false`
- customer_or_private_data_found = `false`
- internet_ad_hoc_content_found = `false`

## Execution and Zero-Delta Boundary

- actual_execution_started_for_ik = `false`
- embedding_generation_started_for_ik = `false`
- index_build_started_for_ik = `false`
- vector_db_write_started_for_ik = `false`
- answer_path_changed = `false`
- model_changed = `false`
- prompt_changed = `false`
- retrieval_logic_changed = `false`
- reranker_changed = `false`
- guardrail_changed = `false`
- release_controls_topology_changed = `false`

## Next Official Work

- next_official_work = `rc-s ik narrow controlled primary-source expansion gate under canonical current authority`
