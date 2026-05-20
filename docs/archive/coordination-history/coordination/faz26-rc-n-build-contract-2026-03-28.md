# FAZ26 RC-N Build Contract

- candidate_id = `RC-N`
- base_candidate = `RC-G`
- control_candidate = `RC-J`
- next_phase_scope = `release_controls_closure_only_under_canonical_current_authority`
- allowed_diff_surface = `release_controls_boundary_only`
- answer_path_delta_allowed = `false`
- parity_gate_required = `true`
- release_controls_retention_required = `true`
- must_close_release_controls_exact_set = `['mandatory auth', 'immutable audit logging', 'persisted PII redaction', 'Redis session persistence', 'tokenizer-backed accounting', 'observability / alerting', 'API versioning', 'process supervision', 'backup / restore', 'one-command release smoke']`
