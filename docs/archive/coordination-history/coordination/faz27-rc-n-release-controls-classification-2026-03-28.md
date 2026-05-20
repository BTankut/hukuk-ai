# FAZ27 RC-N Release Controls Classification

| control_name | control_class | bind_step | has_distinct_runtime_handle | runtime_surface_delegate | should_touch_answer_path |
| --- | --- | --- | --- | --- | --- |
| mandatory auth | runtime-boundary | B1 | true |  | true |
| immutable audit logging | runtime-boundary | B2 | true |  | true |
| persisted PII redaction | runtime-boundary | B3 | false | immutable audit logging | true |
| Redis session persistence | runtime-boundary | B4 | true |  | true |
| tokenizer-backed accounting | runtime-boundary | B5 | true |  | true |
| observability / alerting | runtime-boundary | B6 | false | tokenizer-backed accounting | true |
| API versioning | runtime-boundary | B7 | false | tokenizer-backed accounting | true |
| process supervision | runtime-boundary | B8 | false | tokenizer-backed accounting | true |
| backup / restore | operational-only |  | false |  | false |
| one-command release smoke | operational-only |  | false |  | false |
