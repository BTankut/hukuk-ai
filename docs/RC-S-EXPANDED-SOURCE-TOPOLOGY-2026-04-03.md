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

- accepted_expanded_source_set = `[TMK core corpus]`
- accepted_expanded_source_count = `1`
- current_accepted_expanded_source = `TMK core corpus`
- current_accepted_expanded_source_status = `active_for_source_steering`
- current_accepted_expanded_source_execution_complete = `true`
- current_accepted_expanded_source_human_review_closed = `true`

## Not Yet Executed Source Classes

- unexecuted_source_classes_in_canonical_order = `[TCK, HMK, CMK, TTK, İK]`
- next_unexecuted_source_class = `TCK`

## Boundary Invariants

- second_source_class_actual_execution_started = `false`
- embedding_generation_started_for_next_source = `false`
- index_build_started_for_next_source = `false`
- vector_db_write_started_for_next_source = `false`
- model_changed = `false`
- prompt_changed = `false`
- retrieval_logic_changed = `false`
- reranker_changed = `false`
- guardrail_changed = `false`
- release_controls_topology_changed = `false`
