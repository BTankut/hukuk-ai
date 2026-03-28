# FAZ27 RC-N Release Controls Retention Matrix

- must_close_release_controls_pass = `false`
- must_close_release_controls_count = `10`
- retained_after_family_eval = `false`
- retained_after_restart = `false`
- retained_after_restore = `true`
- pii_leak_found = `true`
- token_accounting_fallback_found = `false`
- release_smoke_gap_found = `true`
- auth_bypass_found = `false`
- audit_write_loss_found = `false`
- redis_continuity_break_found = `false`
- observability_gap_found = `false`
- api_versioning_gap_found = `false`
- supervision_gap_found = `false`
- backup_restore_gap_found = `false`

| control | pass |
| --- | --- |
| mandatory auth | true |
| immutable audit logging | true |
| persisted PII redaction | false |
| Redis session persistence | true |
| tokenizer-backed accounting | true |
| observability / alerting | true |
| API versioning | true |
| process supervision | true |
| backup / restore | true |
| one-command release smoke | false |
