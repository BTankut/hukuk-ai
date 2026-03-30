# FAZ35 RC-P Control-Set Isolation Matrix

| row_id | control_set | classification | interpretation |
| --- | --- | --- | --- |
| S0 | rc_g_baseline | clean_reference | reference lane has no perimeter breach |
| S1 | mandatory_auth + immutable_audit_logging + redis_session_persistence | minimal_failing_interaction | smallest answer-path-adjacent failing set inherits the FAZ27 auth/audit/session interaction |
| S2 | persisted_pii_redaction | single_control_non_root | isolated failing control does not become a standalone model-visible root cause |
| S3 | tokenizer_backed_accounting | single_control_non_root | isolated failing control does not become a standalone model-visible root cause |
| S4 | backup_restore | single_control_non_root | isolated failing control does not become a standalone model-visible root cause |
| S5 | one_command_release_smoke | single_control_non_root | isolated failing control does not become a standalone model-visible root cause |
| S6 | mandatory_auth + immutable_audit_logging + redis_session_persistence + persisted_pii_redaction | interaction_extension | adding a single failing quartet member does not create a smaller explanation than S1 |
| S7 | mandatory_auth + immutable_audit_logging + redis_session_persistence + tokenizer_backed_accounting | interaction_extension | adding a single failing quartet member does not create a smaller explanation than S1 |
| S8 | mandatory_auth + immutable_audit_logging + redis_session_persistence + backup_restore | interaction_extension | adding a single failing quartet member does not create a smaller explanation than S1 |
| S9 | mandatory_auth + immutable_audit_logging + redis_session_persistence + one_command_release_smoke | interaction_extension | adding a single failing quartet member does not create a smaller explanation than S1 |
| S10 | persisted_pii_redaction + tokenizer_backed_accounting + backup_restore + one_command_release_smoke | quartet_only_non_root | quartet without auth/audit/session does not explain the perimeter breach |
| S11 | full_rc_p_perimeter_surface | full_surface_retains_breach | full RC-P perimeter preserves the FAZ34 174-row truth |
| S12 | full_rc_p_perimeter_surface_minus_persisted_pii_redaction | subtractive_full_surface_retains_breach | removing one failing quartet member does not negate the auth/audit/session interaction class |
| S13 | full_rc_p_perimeter_surface_minus_tokenizer_backed_accounting | subtractive_full_surface_retains_breach | removing one failing quartet member does not negate the auth/audit/session interaction class |
| S14 | full_rc_p_perimeter_surface_minus_backup_restore | subtractive_full_surface_retains_breach | removing one failing quartet member does not negate the auth/audit/session interaction class |
| S15 | full_rc_p_perimeter_surface_minus_one_command_release_smoke | subtractive_full_surface_retains_breach | removing one failing quartet member does not negate the auth/audit/session interaction class |
