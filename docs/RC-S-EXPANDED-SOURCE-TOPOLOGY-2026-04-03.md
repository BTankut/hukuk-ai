# RC-S Expanded Source Topology 2026-04-03

## Canonical Order

1. `TMK core corpus`
2. `TCK`
3. `HMK`
4. `CMK`
5. `TTK`
6. `İK`

## Active Topology

- official_base = `RC-R`
- active_quality_reference = `RC-G`
- active_control_diagnostic = `RC-J`
- active_forensic_reference = `RC-N`
- active_perimeter_truth_reference = `RC-P`

## Expanded Source Status

- accepted_expanded_source_set = `[TMK core corpus, TCK, HMK]`
- accepted_expanded_source_count = `3`
- current_accepted_expanded_sources = `TMK core corpus; TCK; HMK`
- tmk_core_corpus_status = `accepted_expanded_source`
- tck_status = `accepted_expanded_source`
- hmk_status = `accepted_expanded_source`
- tmk_execution_complete = `true`
- tmk_human_review_closed = `true`
- tck_execution_complete = `true`
- tck_human_review_closed = `true`
- hmk_execution_complete = `true`
- hmk_human_review_closed = `true`

## Not Yet Executed Source Classes

- unexecuted_source_classes_in_canonical_order = `[CMK, TTK, İK]`
- next_unexecuted_source_class = `CMK`

## Boundary Invariants

- fourth_source_class_actual_execution_started = `false`
- embedding_generation_started_for_next_source = `false`
- index_build_started_for_next_source = `false`
- vector_db_write_started_for_next_source = `false`
- model_changed = `false`
- prompt_changed = `false`
- retrieval_logic_changed = `false`
- reranker_changed = `false`
- guardrail_changed = `false`
- release_controls_topology_changed = `false`
