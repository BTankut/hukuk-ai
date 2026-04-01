# FAZ46 RC-R NARROW INTERNAL PILOT EXECUTION UNDER CANONICAL CURRENT AUTHORITY RAPORU

## Yonetici Ozeti

- official_decision = `PASS - RC-R Narrow Internal Pilot Executed Under Canonical Current Authority`
- next_official_work = `post-rc-r narrow internal pilot closure and next-track steering under canonical current authority`
- admitted_operator_count = `3`
- selected_operator_count = `3`
- planned_session_count = `9`
- completed_session_count = `9`
- session_success_count = `9`
- session_fail_count = `0`
- authority_breach_count = `0`
- model_visible_delta_count = `0`
- runtime_error_count = `0`
- unexplained_count = `0`
- kill_switch_invocation_count = `0`
- rollback_invocation_count = `0`
- incident_count = `0`

## Reference Pack Ozeti

- reference_pack_integrity_pass = `true`
- reference_pack_contradiction_count = `0`
- current_authority_ref = `FAZ21 canonical current authority`
- active_quality_reference = `RC-G`
- active_control_pair = `RC-G vs RC-J`
- active_forensic_reference = `RC-N`
- active_internal_pilot_base_candidate = `RC-R`
- comparison_order = `current_canonical -> historical_archive`

## Prepilot Authority / Parity / Retention Ozeti

- control_pair_authority_match = `true`
- current_authority_contract_breach = `false`
- surface_breach_from_history_reintroduced = `false`
- faz1_50_mismatch_count = `0`
- v2_95_mismatch_count = `0`
- v3_170_mismatch_count = `0`
- model_request_payload_hash_mismatch_count = `0`
- retrieval_request_hash_mismatch_count = `0`
- assembled_context_hash_mismatch_count = `0`
- preprojection_hash_mismatch_count = `0`
- raw_answer_hash_mismatch_count = `0`
- response_envelope_hash_mismatch_count = `0`
- family_metric_delta_zero = `true`
- must_close_release_controls_pass = `true`
- retained_after_family_eval = `true`
- retained_after_restart = `true`
- retained_after_restore = `true`
- runtime_error_count = `0`
- unexplained_count = `0`

## Admission Freeze Ozeti

- admitted_operator_count = `3`
- admitted_operator_ids = `[internal_operator_001, internal_operator_002, internal_operator_003]`
- selected_operator_count = `3`
- selected_operator_ids = `[internal_operator_001, internal_operator_002, internal_operator_003]`
- selected_operator_selection_rule = `first_3_in_canonical_allowlist_order`
- selected_operator_order_canonical = `true`

## Session Plan Ozeti

- sessions_per_operator = `3`
- total_session_count = `9`
- session_mode = `single_turn_only`
- parallel_shadow_control_required = `true`
- session_class_1 = `in_scope_supported_direct_citation`
- session_class_2 = `in_scope_supported_citation_heavy`
- session_class_3 = `refusal_expected_out_of_scope_or_unsupported`

## Per-Session Summary Table

| session_id | operator_id | session_class | admission_pass | rc_r_vs_rc_g_model_request_payload_hash_match | rc_r_vs_rc_g_retrieval_request_hash_match | rc_r_vs_rc_g_assembled_context_hash_match | rc_r_vs_rc_g_preprojection_hash_match | rc_r_vs_rc_g_raw_answer_hash_match | rc_r_vs_rc_g_response_envelope_hash_match | citation_visible | refusal_visible_when_expected | audit_capture_pass | session_export_pass | session_replay_pass | incident_opened |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| faz46-rc-r-session-001 | internal_operator_001 | in_scope_supported_direct_citation | true | true | true | true | true | true | true | true | true | true | true | true | false |
| faz46-rc-r-session-002 | internal_operator_001 | in_scope_supported_citation_heavy | true | true | true | true | true | true | true | true | true | true | true | true | false |
| faz46-rc-r-session-003 | internal_operator_001 | refusal_expected_out_of_scope_or_unsupported | true | true | true | true | true | true | true | true | true | true | true | true | false |
| faz46-rc-r-session-004 | internal_operator_002 | in_scope_supported_direct_citation | true | true | true | true | true | true | true | true | true | true | true | true | false |
| faz46-rc-r-session-005 | internal_operator_002 | in_scope_supported_citation_heavy | true | true | true | true | true | true | true | true | true | true | true | true | false |
| faz46-rc-r-session-006 | internal_operator_002 | refusal_expected_out_of_scope_or_unsupported | true | true | true | true | true | true | true | true | true | true | true | true | false |
| faz46-rc-r-session-007 | internal_operator_003 | in_scope_supported_direct_citation | true | true | true | true | true | true | true | true | true | true | true | true | false |
| faz46-rc-r-session-008 | internal_operator_003 | in_scope_supported_citation_heavy | true | true | true | true | true | true | true | true | true | true | true | true | false |
| faz46-rc-r-session-009 | internal_operator_003 | refusal_expected_out_of_scope_or_unsupported | true | true | true | true | true | true | true | true | true | true | true | true | false |

## Pilot Governance Boundary Compliance Ozeti

- internal_named_allowlist_only = `true`
- customer_user_allowed = `false`
- external_user_allowed = `false`
- customer_case_input_allowed = `false`
- customer_data_ingestion_allowed = `false`
- production_business_decision_usage_allowed = `false`
- advisory_only_label_required = `true`
- human_review_required = `true`
- citation_visible_required = `true`
- refusal_visible_required = `true`
- immutable_audit_required = `true`
- rollback_ready_required = `true`
- incident_register_required = `true`
- kill_switch_required = `true`
- operator_runbook_required = `true`
- post_session_export_required = `true`
- session_replay_required = `true`
- offline_only_operation_allowed = `true`
- internet_dependency_allowed = `false`

## Incident / Kill-Switch / Rollback Ozeti

- incident_count = `0`
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

## Postpilot Authority / Parity / Retention Ozeti

- control_pair_authority_match = `true`
- current_authority_contract_breach = `false`
- faz1_50_mismatch_count = `0`
- v2_95_mismatch_count = `0`
- v3_170_mismatch_count = `0`
- model_request_payload_hash_mismatch_count = `0`
- retrieval_request_hash_mismatch_count = `0`
- assembled_context_hash_mismatch_count = `0`
- preprojection_hash_mismatch_count = `0`
- raw_answer_hash_mismatch_count = `0`
- response_envelope_hash_mismatch_count = `0`
- family_metric_delta_zero = `true`
- must_close_release_controls_pass = `true`
- retained_after_family_eval = `true`
- retained_after_restart = `true`
- retained_after_restore = `true`
- runtime_error_count = `0`
- unexplained_count = `0`

## WP Sonuclari

- WP-1 = `PASS`
- WP-2 = `PASS`
- WP-3 = `PASS`
- WP-4 = `PASS`
- WP-5 = `PASS`
- WP-6 = `PASS`
- WP-7 = `PASS`

## Resmi Karar

- official_decision = `PASS - RC-R Narrow Internal Pilot Executed Under Canonical Current Authority`
- admitted_operator_count = `3`
- selected_operator_count = `3`
- planned_session_count = `9`
- completed_session_count = `9`
- session_success_count = `9`
- session_fail_count = `0`
- authority_breach_count = `0`
- model_visible_delta_count = `0`
- runtime_error_count = `0`
- unexplained_count = `0`
- kill_switch_invocation_count = `0`
- rollback_invocation_count = `0`
- incident_count = `0`

## Sonraki Resmi Is

- next_official_work = `post-rc-r narrow internal pilot closure and next-track steering under canonical current authority`

## Artefact Listesi

- coordination/faz46-reference-pack-2026-04-01.md
- evaluation/reports/faz46-rc-g-vs-rc-j-prepilot-current-authority-check-2026-04-01.md
- evaluation/reports/faz46-rc-g-vs-rc-r-prepilot-full-family-model-visible-surface-parity-2026-04-01.md
- evaluation/reports/faz46-rc-r-prepilot-release-controls-retention-2026-04-01.md
- coordination/faz46-rc-r-admitted-operator-freeze-2026-04-01.md
- coordination/faz46-rc-r-session-plan-2026-04-01.md
- pilot/faz46-rc-r-session-001-export-2026-04-01.md
- pilot/faz46-rc-r-session-002-export-2026-04-01.md
- pilot/faz46-rc-r-session-003-export-2026-04-01.md
- pilot/faz46-rc-r-session-004-export-2026-04-01.md
- pilot/faz46-rc-r-session-005-export-2026-04-01.md
- pilot/faz46-rc-r-session-006-export-2026-04-01.md
- pilot/faz46-rc-r-session-007-export-2026-04-01.md
- pilot/faz46-rc-r-session-008-export-2026-04-01.md
- pilot/faz46-rc-r-session-009-export-2026-04-01.md
- coordination/faz46-rc-r-incident-register-2026-04-01.md
- coordination/faz46-rc-r-kill-switch-and-rollback-log-2026-04-01.md
- evaluation/reports/faz46-rc-g-vs-rc-j-postpilot-current-authority-check-2026-04-01.md
- evaluation/reports/faz46-rc-g-vs-rc-r-postpilot-full-family-model-visible-surface-parity-2026-04-01.md
- evaluation/reports/faz46-rc-r-postpilot-release-controls-retention-2026-04-01.md
- coordination/faz46-final-reconciliation-summary-2026-04-01.md
- reports/FAZ46-RC-R-NARROW-INTERNAL-PILOT-EXECUTION-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md
