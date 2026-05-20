# FAZ35-RC-P-RELEASE-CONTROLS-PERIMETER-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30

## Yonetici Ozeti

- official_decision = `PASS - RC-P Perimeter Root Cause Localized`
- next_official_work = `rc-q release-controls perimeter repair gate under canonical current authority`
- preprojection_hash_mismatch_count = `174`
- raw_answer_hash_mismatch_count = `174`
- response_envelope_hash_mismatch_count = `109`
- faz1_50_mismatch_count = `18`
- v2_95_mismatch_count = `57`
- v3_170_mismatch_count = `99`
- runtime_error_count = `0`
- dominant_stage = `P11`
- dominant_reason = `preprojection_hash_drift`
- minimal_failing_control_set = `S1 = mandatory_auth + immutable_audit_logging + redis_session_persistence`
- dominant_interaction_class = `multi_control_interaction_runtime_mutation`

## Reference Pack Ozeti

- reference_pack_integrity_pass = `true`
- reference_pack_contradiction_count = `0`
- canonical_current_authority_ref = `FAZ21`
- post_rc_m_steering_ref = `FAZ25`
- rc_n_release_controls_legacy_ref = `FAZ26`
- rc_n_boundary_root_cause_ref = `FAZ27`
- rc_o_repair_truth_ref = `FAZ31`
- rc_o_archival_closure_ref = `FAZ32`
- post_rc_o_steering_ref = `FAZ33`
- rc_p_perimeter_truth_ref = `FAZ34`

## Canonical Topology Re-Freeze Ozeti

- RC-G = `accepted_quality_reference`
- RC-J = `canonical_control_diagnostic`
- RC-N = `forensic_reference_candidate`
- RC-M = `discard_archived / historical_summary_archive / diagnostic_only`
- RC-O = `discard_archived / historical_repair_archive / diagnostic_only`
- RC-P = `release_controls_perimeter_candidate`
- new_candidate_allowed = `false`
- rc_q_reserved = `false`
- cutover_allowed = `false`
- pilot_allowed = `false`
- database_expansion_allowed = `false`

## Current Authority ve Upstream Equality Ozeti

- control_pair_authority_match = `true`
- current_authority_contract_breach = `false`
- surface_breach_from_history_reintroduced = `false`
- control_pair_runtime_error_count = `0`
- model_request_payload_hash_mismatch_count = `0`
- retrieval_request_hash_mismatch_count = `0`
- assembled_context_hash_mismatch_count = `0`
- runtime_error_count = `0`

## Perimeter Frontier 174 Ozeti

- frontier_record_count = `174`
- preprojection_hash_mismatch_count = `174`
- raw_answer_hash_mismatch_count = `174`
- runtime_error_count = `0`
- faz1_50_mismatch_count = `18`
- v2_95_mismatch_count = `57`
- v3_170_mismatch_count = `99`
- unexplained_count = `0`

## Response Envelope Subfrontier 109 Ozeti

- response_envelope_subfrontier_record_count = `109`
- response_envelope_hash_mismatch_count = `109`
- runtime_error_count = `0`
- unexplained_count = `0`
- faz1_50_mismatch_count = `9`
- v2_95_mismatch_count = `36`
- v3_170_mismatch_count = `64`

## Targeted Acceptance Authoritative Recapture Ozeti

- must_close_release_controls_count = `10`
- mandatory_auth_pass = `true`
- immutable_audit_logging_pass = `true`
- persisted_pii_redaction_pass = `false`
- redis_session_persistence_pass = `true`
- tokenizer_backed_accounting_pass = `false`
- observability_alerting_pass = `true`
- api_versioning_pass = `true`
- process_supervision_pass = `true`
- backup_restore_pass = `false`
- one_command_release_smoke_pass = `false`
- pii_leak_found = `true`
- token_accounting_fallback_found = `true`
- backup_restore_gap_found = `true`
- release_smoke_gap_found = `true`
- auth_bypass_found = `false`
- audit_write_loss_found = `false`
- redis_continuity_break_found = `false`
- observability_gap_found = `false`
- api_versioning_gap_found = `false`
- supervision_gap_found = `false`
- runtime_error_count = `0`
- unexplained_count = `0`
- refusal_smoke_status_code = `500`
- restart_refusal_smoke_status_code = `500`
- tokenizer_usage_total = `0.0`
- estimated_usage_total = `0.0`
- token_accounting_failure_total = `0.0`
- backup_restore_missing_file_count = `3`

## Perimeter Stage Ladder Localization Ozeti

- frontier_record_count = `174`
- first_divergence_assigned_count = `174`
- primary_reason_assigned_count = `174`
- unexplained_count = `0`
- dominant_stage = `P11`
- dominant_reason = `preprojection_hash_drift`

## Control-Set Isolation Matrix Ozeti

- matrix_row_count = `16`
- minimal_failing_control_set = `S1 = mandatory_auth + immutable_audit_logging + redis_session_persistence`
- single_control_root_cause_found = `false`
- interaction_root_cause_found = `true`
- dominant_interaction_class = `multi_control_interaction_runtime_mutation`
- primary_reason = `single-control or quartet-only surfaces do not explain the RC-P 174-row breach; the smallest failing answer-path-adjacent set remains the auth/audit/session interaction localized in FAZ27, while the failing quartet stays aligned with acceptance and retention truth.`
- unexplained_count = `0`

## Retention Contrast Ozeti

- must_close_release_controls_pass = `false`
- retained_after_family_eval = `false`
- retained_after_restart = `false`
- retained_after_restore = `false`
- answer_path_delta_reintroduced = `true`
- runtime_error_count = `0`
- unexplained_count = `0`
- retention_truth_matches_frontier_174 = `true`
- retention_truth_matches_failing_control_quartet = `true`

## WP Sonuclari

- WP-1 = `PASS`
- WP-2 = `PASS`
- WP-3 = `PASS`
- WP-4 = `PASS`
- WP-5 = `PASS`
- WP-6 = `PASS`
- WP-7 = `PASS`
- WP-8 = `PASS`
- WP-9 = `PASS`

## Resmi Karar

- official_decision = `PASS - RC-P Perimeter Root Cause Localized`

## Sonraki Resmi Is

- next_official_work = `rc-q release-controls perimeter repair gate under canonical current authority`

## Artefact Listesi

- `coordination/faz35-reference-pack-2026-03-30.md`
- `coordination/faz35-canonical-topology-refreeze-2026-03-30.md`
- `evaluation/reports/faz35-rc-g-vs-rc-j-current-authority-check-2026-03-30.md`
- `evaluation/reports/faz35-rc-g-vs-rc-p-upstream-equality-check-2026-03-30.md`
- `coordination/faz35-rc-p-perimeter-frontier-174-freeze-2026-03-30.md`
- `coordination/faz35-rc-p-response-envelope-subfrontier-109-freeze-2026-03-30.md`
- `coordination/faz35-rc-p-failing-control-quartet-freeze-2026-03-30.md`
- `coordination/faz35-rc-p-retention-truth-freeze-2026-03-30.md`
- `evaluation/reports/faz35-rc-g-vs-rc-p-frontier-174-summary-2026-03-30.md`
- `evaluation/reports/faz35-rc-g-vs-rc-p-response-envelope-109-summary-2026-03-30.md`
- `evaluation/reports/faz35-rc-p-targeted-acceptance-recheck-2026-03-30.md`
- `coordination/faz35-rc-p-perimeter-stage-ladder-contract-2026-03-30.md`
- `evaluation/reports/faz35-rc-p-stage-ladder-summary-2026-03-30.md`
- `coordination/faz35-rc-p-control-set-isolation-matrix-2026-03-30.md`
- `evaluation/reports/faz35-rc-p-control-isolation-summary-2026-03-30.md`
- `evaluation/reports/faz35-rc-p-retention-contrast-summary-2026-03-30.md`
- `coordination/faz35-rc-p-perimeter-forensics-reconciliation-2026-03-30.md`
- `coordination/faz35-steering-decision-table-2026-03-30.md`
- `coordination/faz35-final-reconciliation-summary-2026-03-30.md`
- `reports/FAZ35-RC-P-RELEASE-CONTROLS-PERIMETER-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md`
- `docs/FAZ35-RC-P-RELEASE-CONTROLS-PERIMETER-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-30.md`
