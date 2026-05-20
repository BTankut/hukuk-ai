# Mevzuat Faz-3 Controlled Cutover Readiness Contract 2026-04-18

## Phase Boundary
- `authoritative_runtime_candidate = true`
- `runtime_switch_executed = false`
- `cutover_authorized_in_this_phase = false`
- `customer_facing_rollout_authorized = false`
- `active_production_collection_changed = false`

## Current Binding Preservation
- `current_active_runtime_collection = mevzuat_e5_shadow`
- `current_active_runtime_binding_preserved = true`
- `candidate_collection_name = mevzuat_faz1_shadow_20260416`
- `candidate_serving_status = inactive_until_next_gate`

## Controlled Cutover Readiness Requirements
- `acceptance_baseline_frozen = true`
- `human_acceptance_closed = true`
- `rollback_plan_defined = true`
- `backout_plan_defined = true`
- `pre_cutover_candidate_identity_frozen = true`
- `runtime_topology_change_in_this_phase = false`

## Rollback Plan
- `rollback_target_collection = mevzuat_e5_shadow`
- `rollback_trigger_class = parity_regression_or_wrong_source_or_runtime_error_or_unexplained_behavior`
- `rollback_effect = active runtime binding returns to preserved pre-cutover collection without topology rewrite`

## Backout Plan
- `backout_trigger_class = cutover_gate_fail_or_authorization_withdrawn_or_readiness_contract_breach`
- `backout_effect = candidate remains frozen but non-serving; active runtime stays on preserved current binding`
- `candidate_discard_required_in_this_phase = false`

## Explicit Non-Authorizations
- `case_law_enablement_authorized = false`
- `secondary_source_enablement_authorized = false`
- `retrieval_logic_change_authorized = false`
- `reranker_change_authorized = false`
- `guardrail_change_authorized = false`
- `release_controls_topology_change_authorized = false`

## Contract Note
- Bu faz yalnız controlled cutover readiness sınırını ve geri dönüş yollarını exact tanımlar.
- Gerçek runtime switch ve production cutover yalnız sonraki resmi gate ile değerlendirilebilir.
