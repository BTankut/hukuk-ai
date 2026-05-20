# FAZ27 RC-N Runtime Boundary Bind Order

| step_id | label | bound_control_set |
| --- | --- | --- |
| B0 | RC-G canonical baseline |  |
| B1 | mandatory auth | mandatory auth |
| B2 | immutable audit logging | mandatory auth, immutable audit logging |
| B3 | persisted PII redaction | mandatory auth, immutable audit logging, persisted PII redaction |
| B4 | Redis session persistence | mandatory auth, immutable audit logging, persisted PII redaction, Redis session persistence |
| B5 | tokenizer-backed accounting | mandatory auth, immutable audit logging, persisted PII redaction, Redis session persistence, tokenizer-backed accounting |
| B6 | observability / alerting | mandatory auth, immutable audit logging, persisted PII redaction, Redis session persistence, tokenizer-backed accounting, observability / alerting |
| B7 | API versioning | mandatory auth, immutable audit logging, persisted PII redaction, Redis session persistence, tokenizer-backed accounting, observability / alerting, API versioning |
| B8 | process supervision | mandatory auth, immutable audit logging, persisted PII redaction, Redis session persistence, tokenizer-backed accounting, observability / alerting, API versioning, process supervision |
