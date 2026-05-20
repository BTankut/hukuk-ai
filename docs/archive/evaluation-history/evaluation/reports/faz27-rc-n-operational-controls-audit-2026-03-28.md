# FAZ27 RC-N Operational Controls Audit

- must_close_release_controls_count = `10`
- unexplained_control_count = `0`

| control_name | control_class | should_touch_answer_path | answer_path_touch_observed | closure_status | primary_reason |
| --- | --- | --- | --- | --- | --- |
| mandatory auth | runtime-boundary | true | true | pass | effective_control_first_break=preprojection_hash |
| immutable audit logging | runtime-boundary | true | true | pass | effective_control_first_break=preprojection_hash |
| persisted PII redaction | runtime-boundary | true | false | fail | persisted_redaction_retention_open |
| Redis session persistence | runtime-boundary | true | true | pass | effective_control_first_break=preprojection_hash |
| tokenizer-backed accounting | runtime-boundary | true | false | pass | no_incremental_answer_path_delta_observed |
| observability / alerting | runtime-boundary | true | false | pass | no_incremental_answer_path_delta_observed |
| API versioning | runtime-boundary | true | false | pass | no_incremental_answer_path_delta_observed |
| process supervision | runtime-boundary | true | false | pass | no_incremental_answer_path_delta_observed |
| backup / restore | operational-only | false | false | pass | no_incremental_answer_path_delta_observed |
| one-command release smoke | operational-only | false | false | fail | release_smoke_refusal_probe_gap |
