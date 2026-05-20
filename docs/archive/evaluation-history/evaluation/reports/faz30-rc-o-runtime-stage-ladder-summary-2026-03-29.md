# FAZ30 RC-O Runtime Stage Ladder Summary

- boundary_runtime_error_count = `0`
- boundary_first_runtime_error_stage_assigned_count = `0`
- boundary_primary_reason_assigned_count = `0`
- boundary_unexplained_count = `0`
- boundary_dominant_stage = ``
- boundary_dominant_primary_reason = ``
- spillover_runtime_error_count = `0`
- spillover_first_runtime_error_stage_assigned_count = `0`
- spillover_primary_reason_assigned_count = `0`
- spillover_unexplained_count = `0`
- spillover_dominant_stage = ``
- spillover_dominant_primary_reason = ``

## Allowed Stage Set

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

## Allowed Primary Reason Set

- `multi_control_interaction_runtime_mutation`
- `persisted_pii_redaction_runtime_mutation`
- `tokenizer_accounting_runtime_mutation`
- `api_versioning_runtime_mutation`
- `one_command_release_smoke_runtime_mutation`
- `boundary_pack_orchestration_runtime_mutation`
- `evaluator_boundary_materialization_runtime_mutation`
- `retention_side_effect_runtime_mutation`
