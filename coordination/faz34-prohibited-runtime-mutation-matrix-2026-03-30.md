# FAZ34 Prohibited Runtime Mutation Matrix

| rule | allowed |
| --- | --- |
| auth_principal_in_model_request_allowed | false |
| user_id_in_model_request_allowed | false |
| session_id_context_injection_allowed | false |
| trace_id_in_prompt_path_allowed | false |
| request_id_in_prompt_path_allowed | false |
| audit_id_in_prompt_path_allowed | false |
| timestamp_feedback_into_answer_path_allowed | false |
| token_count_feedback_into_answer_path_allowed | false |
| health_debug_metadata_in_answer_path_allowed | false |
| observability_metadata_in_answer_path_allowed | false |
| backup_metadata_in_answer_path_allowed | false |
| supervision_metadata_in_answer_path_allowed | false |
| alerting_metadata_in_answer_path_allowed | false |
| version_negotiation_metadata_in_answer_path_allowed | false |
| transport_boundary_headers_in_answer_path_allowed | false |
| redis_runtime_state_in_answer_path_allowed | false |
| async_outbox_identifier_in_answer_path_allowed | false |
