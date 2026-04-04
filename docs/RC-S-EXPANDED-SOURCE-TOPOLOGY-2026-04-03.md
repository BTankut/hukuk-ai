# RC-S Expanded Source Topology 2026-04-03

## Canonical Order

| source_class | canonical_order | accepted_expanded | next_candidate_eligible | currently_selected_for_execution | notes |
| --- | --- | --- | --- | --- | --- |
| TMK core corpus | 1 | true | false | false | accepted expanded source, execution and lawyer acceptance closed |
| TCK | 2 | true | false | false | accepted expanded source, execution and lawyer acceptance closed |
| HMK | 3 | true | false | false | accepted expanded source, execution and lawyer acceptance closed |
| CMK | 4 | true | false | false | accepted expanded source, execution and lawyer acceptance closed in this phase |
| TTK | 5 | false | true | false | next unexecuted source class, steering-selected next source |
| İK | 6 | false | false | false | waits behind TTK in canonical order |

## Active Topology

- official_base = `RC-R`
- active_quality_reference = `RC-G`
- active_control_diagnostic = `RC-J`
- active_forensic_reference = `RC-N`
- active_perimeter_truth_reference = `RC-P`

## Expanded Source Status

- accepted_expanded_source_set = `[TMK core corpus, TCK, HMK, CMK]`
- accepted_expanded_source_count = `4`
- current_accepted_expanded_sources = `TMK core corpus; TCK; HMK; CMK`
- tmk_core_corpus_status = `accepted_expanded_source`
- tck_status = `accepted_expanded_source`
- hmk_status = `accepted_expanded_source`
- cmk_status = `accepted_expanded_source`
- tmk_execution_complete = `true`
- tmk_human_review_closed = `true`
- tck_execution_complete = `true`
- tck_human_review_closed = `true`
- hmk_execution_complete = `true`
- hmk_human_review_closed = `true`
- cmk_execution_complete = `true`
- cmk_human_review_closed = `true`

## Not Yet Executed Source Classes

- unexecuted_source_classes_in_canonical_order = `[TTK, İK]`
- next_unexecuted_source_class = `TTK`

## Boundary Invariants

- next_source_actual_execution_started = `false`
- embedding_generation_started_for_next_source = `false`
- index_build_started_for_next_source = `false`
- vector_db_write_started_for_next_source = `false`
- answer_path_changed = `false`
- model_changed = `false`
- prompt_changed = `false`
- retrieval_logic_changed = `false`
- reranker_changed = `false`
- guardrail_changed = `false`
- release_controls_topology_changed = `false`
