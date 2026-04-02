# RC-R Gercek Dunya Testi Final Kabul Raporu 2026-04-01

## Yonetici Ozeti

- official_decision = `PASS - RC-R Observed Real-World Acceptance Closed`
- next_official_work = `rc-s coverage readiness forensics under canonical current authority`
- total_session_count = `30`
- supported_session_count = `25`
- refusal_expected_session_count = `5`
- approve_count = `23`
- revise_count = `7`
- reject_count = `0`
- approval_rate = `0.7667`
- usable_count = `30`
- usable_rate = `1.0000`
- hard_reject_rate = `0.0000`
- supported_source_correct_count = `24`
- citation_readable_count = `25`
- answer_usable_count = `23`
- refusal_correct_count = `5`
- human_escalation_needed_count = `2`
- total_rejected_session_count = `2`
- any_authority_breach = `0`
- any_model_visible_delta = `0`
- any_runtime_error = `0`
- any_unexplained = `0`
- human_pass = `true`
- technical_pass = `true`
- overall_pass = `true`

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
- human_review_csv_source = `docs/LAWYER-REVIEW-KANONIK-reviewed.csv`
- technical_integrity_source = `reports/FAZ49-RC-R-KONTROLLU-GERCEK-DUNYA-DOGRULAMA-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md`

## BT Canli Gozlem Sonuclari

- observer_id = `BT`
- session_count = `12`
- direct_citation_session_count = `6`
- citation_heavy_session_count = `4`
- refusal_expected_session_count = `2`
- completed_session_count = `12`
- rejected_session_count = `0`
- notes = `10 APPROVE, 2 REVISE, 0 REJECT. Revise verilen satirlar bt_live_q11 ve bt_live_q12 oldu.`

## Ic Operator Sonuclari

- operator_count = `3`
- operator_ids = `[internal_operator_001, internal_operator_002, internal_operator_003]`
- total_session_count = `18`
- sessions_per_operator = `6`
- completed_session_count = `18`
- rejected_session_count = `0`
- notes = `13 APPROVE, 5 REVISE, 0 REJECT. internal_operator_001 = 5/1/0, internal_operator_002 = 3/3/0, internal_operator_003 = 5/1/0.`

## Tum Oturumlar Tablosu

- session_level_human_source = `docs/LAWYER-REVIEW-KANONIK-reviewed.csv`
- session_level_technical_source = `reports/FAZ49-RC-R-KONTROLLU-GERCEK-DUNYA-DOGRULAMA-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-04-01.md`
- exact_session_row_count = `30`
- exact_shadow_match_session_count = `30`
- exact_incident_opened_count = `0`

| actor_id | total_session_count | approve_count | revise_count | reject_count | notes |
| --- | --- | --- | --- | --- | --- |
| BT | 12 | 10 | 2 | 0 | revise satirlari refusal bandinda kaldi |
| internal_operator_001 | 6 | 5 | 1 | 0 | tek revise refusal/local doc sinifinda |
| internal_operator_002 | 6 | 3 | 3 | 0 | kira bedeli, evlat edinme ve refusal/web satirlari revize edildi |
| internal_operator_003 | 6 | 5 | 1 | 0 | tek revise refusal/private message satirinda |

## Insan Degerlendirme Skorkarti

- reviewed_csv_source = `docs/LAWYER-REVIEW-KANONIK-reviewed.csv`
- total_row_count = `30`
- approve_count = `23`
- revise_count = `7`
- reject_count = `0`
- approval_rate = `0.7667`
- usable_count = `30`
- usable_rate = `1.0000`
- hard_reject_rate = `0.0000`
- refusal_expected_row_count = `5`
- refusal_rows_approve_count = `0`
- refusal_rows_revise_count = `5`
- refusal_rows_reject_count = `0`
- allowed_value_only = `true`
- revised_question_ids = `[bt_live_q11, bt_live_q12, op001_q06, op002_q01, op002_q05, op002_q06, op003_q06]`
- revised_rows_common_pattern = `refusal phrasing, source anchoring ve madde baglama netlestirmesi`
- human_pass = `true`

## Shadow Control Fark Ozeti

- model_request_payload_hash_mismatch_count = `0`
- retrieval_request_hash_mismatch_count = `0`
- assembled_context_hash_mismatch_count = `0`
- preprojection_hash_mismatch_count = `0`
- raw_answer_hash_mismatch_count = `0`
- response_envelope_hash_mismatch_count = `0`

## Incident / Rollback / Kill-Switch Ozeti

- incident_count = `0`
- kill_switch_invocation_count = `0`
- rollback_invocation_count = `0`
- rollback_target = `RC-G canonical answer lane`
- notes = `Live run boyunca authority, model-visible ve runtime hard-fail tetiklenmedi.`

## Post-Run Full-Family Parity

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

## Post-Run Retention

- must_close_release_controls_pass = `true`
- retained_after_family_eval = `true`
- retained_after_restart = `true`
- retained_after_restore = `true`
- runtime_error_count = `0`
- unexplained_count = `0`

## Resmi Karar

- official_decision = `PASS - RC-R Observed Real-World Acceptance Closed`
- human_pass = `true`
- technical_pass = `true`
- pass_condition_human_csv_completed = `true`
- pass_condition_human_csv_allowed_values_only = `true`
- pass_condition_supported_source_correct_count_ge_24 = `true`
- pass_condition_citation_readable_count_eq_25 = `true`
- pass_condition_answer_usable_count_ge_23 = `true`
- pass_condition_refusal_correct_count_eq_5 = `true`
- pass_condition_human_escalation_needed_count_le_2 = `true`
- pass_condition_total_rejected_session_count_le_2 = `true`
- pass_condition_any_authority_breach_eq_0 = `true`
- pass_condition_any_model_visible_delta_eq_0 = `true`
- pass_condition_any_runtime_error_eq_0 = `true`
- pass_condition_any_unexplained_eq_0 = `true`

## Bir Sonraki Is

- next_official_work = `rc-s coverage readiness forensics under canonical current authority`
