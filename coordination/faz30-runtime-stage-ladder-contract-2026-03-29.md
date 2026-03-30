# FAZ30 Runtime Stage Ladder Contract

- `R0_bootstrap`
- `R1_auth_context_bind`
- `R2_audit_logger_bind`
- `R3_pii_redaction_bind`
- `R4_redis_session_bind`
- `R5_tokenizer_accounting_bind`
- `R6_api_versioning_bind`
- `R7_release_smoke_bind`
- `R8_request_envelope_materialization`
- `R9_model_request_dispatch`
- `R10_stream_open`
- `R11_stream_finalize`
- `R12_evaluator_write`
- `R13_retention_write`

## Allowed Primary Reasons

- `multi_control_interaction_runtime_mutation`
- `persisted_pii_redaction_runtime_mutation`
- `tokenizer_accounting_runtime_mutation`
- `api_versioning_runtime_mutation`
- `one_command_release_smoke_runtime_mutation`
- `boundary_pack_orchestration_runtime_mutation`
- `evaluator_boundary_materialization_runtime_mutation`
- `retention_side_effect_runtime_mutation`
