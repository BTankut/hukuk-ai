# FAZ27 RC-N Runtime Boundary Bind Ladder

- first_break_control = `mandatory auth`
- first_break_step = `B1`
- first_break_stage = `preprojection_hash`
- first_break_count = `146`
- dominant_control = `Redis session persistence`
- dominant_stage = `preprojection_hash`
- effective_control_set = `mandatory auth, immutable audit logging, Redis session persistence`
- single_control_root_cause_found = `false`
- interaction_root_cause_found = `false`
- unexplained_count = `0`

| step_id | bound_control_set | source | inherited_from_step | preprojection | raw_answer | response_envelope | first_break_stage | first_break_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B0 |  | authoritative_rc_g_reference |  | 0 | 0 | 0 |  | 0 |
| B1 | mandatory auth | live_pair_report |  | 146 | 146 | 89 | preprojection_hash | 146 |
| B2 | mandatory auth, immutable audit logging | live_pair_report |  | 148 | 148 | 87 | preprojection_hash | 148 |
| B3 | mandatory auth, immutable audit logging, persisted PII redaction | inherited_runtime_surface | B2 | 148 | 148 | 87 | preprojection_hash | 148 |
| B4 | mandatory auth, immutable audit logging, persisted PII redaction, Redis session persistence | live_pair_report |  | 159 | 159 | 95 | preprojection_hash | 159 |
| B5 | mandatory auth, immutable audit logging, persisted PII redaction, Redis session persistence, tokenizer-backed accounting | live_pair_report |  | 159 | 159 | 92 | preprojection_hash | 159 |
| B6 | mandatory auth, immutable audit logging, persisted PII redaction, Redis session persistence, tokenizer-backed accounting, observability / alerting | inherited_runtime_surface | B5 | 159 | 159 | 92 | preprojection_hash | 159 |
| B7 | mandatory auth, immutable audit logging, persisted PII redaction, Redis session persistence, tokenizer-backed accounting, observability / alerting, API versioning | inherited_runtime_surface | B5 | 159 | 159 | 92 | preprojection_hash | 159 |
| B8 | mandatory auth, immutable audit logging, persisted PII redaction, Redis session persistence, tokenizer-backed accounting, observability / alerting, API versioning, process supervision | inherited_runtime_surface | B5 | 159 | 159 | 92 | preprojection_hash | 159 |
