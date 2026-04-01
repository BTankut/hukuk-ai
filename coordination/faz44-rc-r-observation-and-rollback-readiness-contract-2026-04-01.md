# FAZ44 RC-R Observation and Rollback Readiness Contract

- prepilot_full_family_parity_zero_required = `true`
- prepilot_release_controls_retention_required = `true`
- prepilot_current_authority_match_required = `true`
- pilot_runtime_error_allowed = `false`
- pilot_unexplained_allowed = `false`
- pilot_response_capture_required = `true`
- pilot_citation_capture_required = `true`
- pilot_refusal_capture_required = `true`
- pilot_audit_capture_required = `true`
- pilot_restore_readiness_required = `true`
- pilot_restart_readiness_required = `true`
- pilot_rollback_readiness_required = `true`
- rollback_target = `RC-G canonical answer lane`
- rollback_trigger_class = `any_authority_breach_or_any_model_visible_delta_or_any_runtime_error`
- rollback_trigger_is_hard_fail = `true`
