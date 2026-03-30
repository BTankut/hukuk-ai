# FAZ30 Control-Set Isolation Matrix Contract

| control_set_id | controls |
| --- | --- |
| C0 | mandatory auth, immutable audit logging, Redis session persistence |
| C1 | mandatory auth, immutable audit logging, Redis session persistence, persisted PII redaction |
| C2 | mandatory auth, immutable audit logging, Redis session persistence, tokenizer-backed accounting |
| C3 | mandatory auth, immutable audit logging, Redis session persistence, API versioning |
| C4 | mandatory auth, immutable audit logging, Redis session persistence, one-command release smoke |
| C5 | mandatory auth, immutable audit logging, Redis session persistence, persisted PII redaction, tokenizer-backed accounting |
| C6 | mandatory auth, immutable audit logging, Redis session persistence, persisted PII redaction, one-command release smoke |
| C7 | mandatory auth, immutable audit logging, Redis session persistence, API versioning, one-command release smoke |
| C8 | mandatory auth, immutable audit logging, persisted PII redaction, Redis session persistence, tokenizer-backed accounting, observability / alerting, API versioning, process supervision, backup / restore, one-command release smoke |
