# FAZ26 Release Controls Boundary Spec

- candidate_id = `RC-N`
- allowed_diff_surface = `release_controls_boundary_only`
- answer_path_delta_allowed = `false`
- retrieval_change_allowed = `false`
- prompt_change_allowed = `false`
- model_change_allowed = `false`
- guardrail_change_allowed = `false`
- boundary_surface = gateway auth / audit / persisted PII / Redis sessions / tokenizer accounting / observability / API versioning / supervision / backup-restore / release smoke
- model_visible_surface_forbidden = auth_principal, user id, session id, trace id, request id, audit id, timestamp, token count, health-debug metadata, observability metadata, backup metadata, supervision metadata, alerting metadata, version negotiation metadata
