# FAZ26 Production Readiness Matrix v3

| control | lane | fresh evidence | result |
| --- | --- | --- | --- |
| mandatory auth | `rc_n` | `release smoke` | `PASS` |
| immutable audit logging | `rc_n` | `audit log + metrics` | `PASS` |
| persisted PII redaction | `rc_n` | `persisted pii probe` | `FAIL` |
| Redis session persistence | `rc_n` | `release smoke + restart smoke` | `PASS` |
| tokenizer-backed accounting | `rc_n` | `metrics + retention gate` | `FAIL` |
| observability / alerting | `rc_n` | `alerts + metrics` | `PASS` |
| API versioning | `rc_n` | `models headers` | `PASS` |
| process supervision | `rc_n` | `ensure_release_lane snapshots` | `PASS` |
| backup / restore | `rc_n` | `backup manifest + restore summary` | `PASS` |
| one-command release smoke | `rc_n` | `release smoke runner` | `FAIL` |

- WP-2 must-close release controls = `FAIL`
