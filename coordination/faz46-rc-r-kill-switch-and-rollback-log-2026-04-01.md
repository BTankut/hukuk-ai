# FAZ46 RC-R Kill-Switch and Rollback Log

- kill_switch_invocation_count = `0`
- rollback_invocation_count = `0`
- rollback_target = `RC-G canonical answer lane`
- rollback_trigger_class = `any_authority_breach_or_any_model_visible_delta_or_any_runtime_error`
- rollback_trigger_is_hard_fail = `true`
- kill_switch_invoke_contract = `hard_stop_on_any_trigger_class`
- incident_severity_classification_contract = `authority_or_model_visible_or_runtime_error_is_sev1`
- pilot_stop_condition_contract = `any_authority_breach_or_any_model_visible_delta_or_any_runtime_error`
- operator_handoff_contract = `explicit_named_operator_ownership_required`
- post_session_export_contract = `required_after_each_internal_pilot_session`
- session_replay_contract = `required_for_each_internal_pilot_session`
