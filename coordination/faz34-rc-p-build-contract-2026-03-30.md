# FAZ34 RC-P Build Contract

- next_candidate_id = `RC-P`
- next_candidate_base = `RC-G`
- next_candidate_control = `RC-J`
- next_candidate_forensic_reference = `RC-N`
- next_phase_scope = `release_controls_perimeter_isolation_only_under_canonical_current_authority`
- allowed_diff_surface = `non_model_visible_release_controls_perimeter_only`
- answer_path_delta_allowed = `false`
- model_request_payload_delta_allowed = `false`
- retrieval_request_delta_allowed = `false`
- assembled_context_delta_allowed = `false`
- preprojection_delta_allowed = `false`
- raw_answer_delta_allowed = `false`
- response_envelope_delta_allowed = `false`
- runtime_error_delta_allowed = `false`
- parity_gate_required = `true`
- release_controls_retention_required = `true`
- must_close_release_controls_exact_set = `['mandatory auth', 'immutable audit logging', 'persisted PII redaction', 'Redis session persistence', 'tokenizer-backed accounting', 'observability / alerting', 'API versioning', 'process supervision', 'backup / restore', 'one-command release smoke']`
