# FAZ28 RC-O Release Controls Targeted Acceptance

- must_close_release_controls_count = `10`
- mandatory_auth_pass = `true`
- immutable_audit_logging_pass = `true`
- persisted_pii_redaction_pass = `false`
- redis_session_persistence_pass = `true`
- tokenizer_backed_accounting_pass = `false`
- observability_alerting_pass = `true`
- api_versioning_pass = `true`
- process_supervision_pass = `true`
- backup_restore_pass = `true`
- one_command_release_smoke_pass = `false`
- auth_bypass_found = `false`
- audit_write_loss_found = `false`
- pii_leak_found = `true`
- redis_continuity_break_found = `false`
- token_accounting_fallback_found = `true`
- observability_gap_found = `false`
- api_versioning_gap_found = `false`
- supervision_gap_found = `false`
- backup_restore_gap_found = `false`
- release_smoke_gap_found = `true`
- runtime_error_count = `0`
- unexplained_count = `0`

| control | pass |
| --- | --- |
| mandatory auth | true |
| immutable audit logging | true |
| persisted PII redaction | false |
| Redis session persistence | true |
| tokenizer-backed accounting | false |
| observability / alerting | true |
| API versioning | true |
| process supervision | true |
| backup / restore | true |
| one-command release smoke | false |
