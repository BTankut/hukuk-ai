# FAZ35 RC-P Control Isolation Summary

- matrix_row_count = `16`
- minimal_failing_control_set = `S1 = mandatory_auth + immutable_audit_logging + redis_session_persistence`
- single_control_root_cause_found = `false`
- interaction_root_cause_found = `true`
- dominant_interaction_class = `multi_control_interaction_runtime_mutation`
- primary_reason = `single-control or quartet-only surfaces do not explain the RC-P 174-row breach; the smallest failing answer-path-adjacent set remains the auth/audit/session interaction localized in FAZ27, while the failing quartet stays aligned with acceptance and retention truth.`
- unexplained_count = `0`
