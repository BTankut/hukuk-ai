# RC-S TCK Narrow Controlled Expansion Contract 2026-04-03

## Contract Scope

- official_base = `RC-R`
- source_class = `TCK`
- contract_status = `prepared_not_executed`
- execution_authorized_in_this_phase = `false`

## Future Execution Boundary

- execution_scope = `TCK-only narrow controlled primary-source expansion`
- source_set_if_opened = `existing accepted source set + TCK`
- rollback_target = `RC-R frozen canonical serving base`
- customer_user_allowed = `false`
- external_user_allowed = `false`
- pilot_scope = `internal_only`

## Mutability Rules

- model_change_allowed = `false`
- prompt_change_allowed = `false`
- retrieval_logic_change_allowed = `false`
- reranker_change_allowed = `false`
- guardrail_change_allowed = `false`
- release_controls_topology_change_allowed = `false`

## Execution State In This Phase

- actual_ingest_started = `false`
- embedding_generation_started = `false`
- index_build_started = `false`
- vector_db_write_started = `false`
- canary_lane_started = `false`

## Handoff

- future_gate_name = `rc-s tck narrow controlled primary-source expansion gate under canonical current authority`
- previous_accepted_source = `TMK core corpus`
- next_source_class = `TCK`
