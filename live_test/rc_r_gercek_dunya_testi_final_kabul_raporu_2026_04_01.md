# RC-R Gercek Dunya Testi Final Kabul Raporu 2026-04-01

## Yonetici Ozeti

- official_decision = `PASS - RC-R Observed Real-World Acceptance Closed / NO-GO - RC-R Observed Real-World Acceptance Failed`
- next_official_work = `rc-s coverage readiness forensics under canonical current authority / defect-specific remediation pack only`
- total_session_count = ``
- supported_session_count = ``
- refusal_expected_session_count = ``
- supported_source_correct_count = ``
- citation_readable_count = ``
- answer_usable_count = ``
- refusal_correct_count = ``
- human_escalation_needed_count = ``
- total_rejected_session_count = ``
- any_authority_breach = ``
- any_model_visible_delta = ``
- any_runtime_error = ``
- any_unexplained = ``

## Test Kontrati

- candidate_under_test = `RC-R`
- shadow_control = `RC-G`
- diagnostic_control = `RC-J`
- operation_mode = `offline_only`
- human_review_required = `true`
- citation_visible_required = `true`
- refusal_visible_required = `true`
- immutable_audit_required = `true`
- rollback_target = `RC-G canonical answer lane`
- hard_fail_trigger = `any_authority_breach_or_any_model_visible_delta_or_any_runtime_error`

## BT Canli Gozlem Sonuclari

- observer_id = `BT`
- session_count = `12`
- direct_citation_session_count = `6`
- citation_heavy_session_count = `4`
- refusal_expected_session_count = `2`
- completed_session_count = ``
- rejected_session_count = ``
- notes = ``

## Ic Operator Sonuclari

- operator_count = `3`
- operator_ids = `[internal_operator_001, internal_operator_002, internal_operator_003]`
- total_session_count = `18`
- sessions_per_operator = `6`
- completed_session_count = ``
- rejected_session_count = ``
- notes = ``

## Tum Oturumlar Tablosu

| session_id | actor_id | question_id | question_class | rc_r_response_export_path | rc_g_shadow_export_path | model_request_payload_hash_match | retrieval_request_hash_match | assembled_context_hash_match | preprojection_hash_match | raw_answer_hash_match | response_envelope_hash_match | citation_visible | refusal_visible_when_expected | immutable_audit_record_id | session_export_pass | session_replay_pass | incident_opened |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  | true/false | true/false | true/false | true/false | true/false | true/false | true/false | true/false |  | true/false | true/false | true/false |

## Insan Degerlendirme Skorkarti

- scorecard_source = `live_test/rc_r_insan_skorkarti_2026_04_01.md`
- supported_source_correct_count = ``
- citation_readable_count = ``
- answer_usable_count = ``
- refusal_correct_count = ``
- legal_overreach_present_count = ``
- human_escalation_needed_count = ``
- total_rejected_session_count = ``

## Shadow Control Fark Ozeti

- model_request_payload_hash_mismatch_count = ``
- retrieval_request_hash_mismatch_count = ``
- assembled_context_hash_mismatch_count = ``
- preprojection_hash_mismatch_count = ``
- raw_answer_hash_mismatch_count = ``
- response_envelope_hash_mismatch_count = ``

## Incident / Rollback / Kill-Switch Ozeti

- incident_count = ``
- kill_switch_invocation_count = ``
- rollback_invocation_count = ``
- rollback_target = `RC-G canonical answer lane`
- notes = ``

## Post-Run Full-Family Parity

- faz1_50_mismatch_count = ``
- v2_95_mismatch_count = ``
- v3_170_mismatch_count = ``
- model_request_payload_hash_mismatch_count = ``
- retrieval_request_hash_mismatch_count = ``
- assembled_context_hash_mismatch_count = ``
- preprojection_hash_mismatch_count = ``
- raw_answer_hash_mismatch_count = ``
- response_envelope_hash_mismatch_count = ``
- family_metric_delta_zero = ``

## Post-Run Retention

- must_close_release_controls_pass = ``
- retained_after_family_eval = ``
- retained_after_restart = ``
- retained_after_restore = ``
- runtime_error_count = ``
- unexplained_count = ``

## Resmi Karar

- official_decision = `PASS - RC-R Observed Real-World Acceptance Closed / NO-GO - RC-R Observed Real-World Acceptance Failed`
- pass_condition_supported_source_correct_count_ge_24 = ``
- pass_condition_citation_readable_count_eq_25 = ``
- pass_condition_answer_usable_count_ge_23 = ``
- pass_condition_refusal_correct_count_eq_5 = ``
- pass_condition_human_escalation_needed_count_le_2 = ``
- pass_condition_total_rejected_session_count_le_2 = ``
- pass_condition_any_authority_breach_eq_0 = ``
- pass_condition_any_model_visible_delta_eq_0 = ``
- pass_condition_any_runtime_error_eq_0 = ``
- pass_condition_any_unexplained_eq_0 = ``

## Bir Sonraki Is

- next_official_work = `rc-s coverage readiness forensics under canonical current authority / defect-specific remediation pack only`
