# FAZ45 RC-R Incident Kill-Switch and Operator Runbook Contract

- kill_switch_invoke_contract = `hard_stop_on_any_trigger_class`
- incident_severity_classification_contract = `authority_or_model_visible_or_runtime_error_is_sev1`
- pilot_stop_condition_contract = `any_authority_breach_or_any_model_visible_delta_or_any_runtime_error`
- operator_handoff_contract = `explicit_named_operator_ownership_required`
- post_session_export_contract = `required_after_each_internal_pilot_session`
- session_replay_contract = `required_for_each_internal_pilot_session`
- kill_switch_contract_materialized = `true`
- incident_contract_materialized = `true`
- pilot_stop_condition_materialized = `true`
- operator_handoff_materialized = `true`
- post_session_export_materialized = `true`
- session_replay_materialized = `true`
