# FAZ26 RC-N Release Controls Closure Reopen Under Canonical Current Authority Raporu

## Yonetici Ozeti

- resmi_karar = `NO-GO - Release Controls`
- sonraki_resmi_is = `rc-n release-controls boundary forensics under canonical current authority`

## Reference Pack Ozeti

- reference_pack_integrity_pass = `true`
- reference_pack_contradiction_count = `0`
- quality_reference_ref = `FAZ6`
- canonical_current_authority_ref = `FAZ21`
- release_controls_legacy_ref = `FAZ7`
- archival_closure_ref = `FAZ24`

## RC-N Build Contract Ozeti

- candidate_id = `RC-N`
- base_candidate = `RC-G`
- control_candidate = `RC-J`
- allowed_diff_surface = `release_controls_boundary_only`
- answer_path_delta_allowed = `false`

## Must-Close Release Controls Closure Tablosu

| control | result |
| --- | --- |
| mandatory auth | `PASS` |
| immutable audit logging | `PASS` |
| persisted PII redaction | `FAIL` |
| Redis session persistence | `PASS` |
| tokenizer-backed accounting | `FAIL` |
| observability / alerting | `PASS` |
| API versioning | `PASS` |
| process supervision | `PASS` |
| backup / restore | `PASS` |
| one-command release smoke | `FAIL` |

## Current Authority Check Ozeti

- control_pair_authority_match = `true`
- current_authority_contract_breach = `false`
- surface_breach_from_history_reintroduced = `false`
- current_canonical_authority_adopted = `true`
- control_pair_runtime_error_count = `0`

## Model-Visible Surface Gate Ozeti

- model_request_payload_hash_mismatch_count = `0`
- retrieval_request_hash_mismatch_count = `0`
- assembled_context_hash_mismatch_count = `0`
- preprojection_hash_mismatch_count = `166`
- raw_answer_hash_mismatch_count = `166`
- runtime_error_count = `0`
- first_break_stage_assigned_count = `166`
- primary_reason_assigned_count = `166`
- unexplained_count = `0`

## Output Parity Ozeti

- faz1_50_mismatch_count = `16`
- v2_95_mismatch_count = `56`
- v3_170_mismatch_count = `94`
- family_metric_delta_zero = `false`
- runtime_error_count = `0`
- unexplained_count = `0`

## Release Controls Retention Ozeti

- must_close_release_controls_pass = `false`
- must_close_release_controls_count = `10`
- retained_after_family_eval = `false`
- retained_after_restart = `false`
- retained_after_restore = `true`
- auth_bypass_found = `false`
- audit_write_loss_found = `false`
- pii_leak_found = `true`
- redis_continuity_break_found = `false`
- token_accounting_fallback_found = `false`
- observability_gap_found = `false`
- api_versioning_gap_found = `false`
- supervision_gap_found = `false`
- backup_restore_gap_found = `false`
- release_smoke_gap_found = `true`

## WP Sonuclari

- WP-1 = `PASS`
- WP-2 = `FAIL`
- WP-3 = `FAIL`
- WP-4 = `FAIL`
- WP-5 = `FAIL`

## Resmi Karar

- `NO-GO - Release Controls`

## Sonraki Resmi Is

- `rc-n release-controls boundary forensics under canonical current authority`
