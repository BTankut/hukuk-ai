# FAZ29 RC-O Failing Control Triplet

- `persisted PII redaction`
- `tokenizer-backed accounting`
- `one-command release smoke`

- must_close_release_controls_count = `10`

| control | pass |
| --- | --- |
| mandatory auth | true |
| immutable audit logging | true |
| persisted PII redaction | false |
| Redis session persistence | true |
| tokenizer-backed accounting | false |
| observability / alerting | true |
| API versioning | true |
| process supervision | true |
| backup / restore | true |
| one-command release smoke | false |
