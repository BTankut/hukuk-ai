# FAZ7 Audit Logging Acceptance

Tarih: 2026-03-24

Scope:
- hedef lane: `rc_h`
- append-only redacted JSONL audit

Komut / kanıt:
- smoke suite: `runtime_logs/faz7_release_smoke_rc_h.json`
- audit surface: `runtime_logs/rc_h_audit_faz7_acceptance.jsonl`

Doğrulanan alanlar:
- `request_id`
- `trace_id`
- `session_id`
- `auth_subject`
- `selected_lane`
- `api_version`
- `final_mode`
- `refusal_reason`
- `citations`
- `source_ids`
- `latency_ms`
- `token_accounting`
- `decision_timestamps`
- `prev_event_sha256`
- `event_sha256`

Gözlem:
- hash chain mevcut
- `prev_event_sha256 -> event_sha256` zinciri fresh file içinde bozulmadan ilerliyor
- lane ve version sabit: `rc_h`, `2026-03-24-rc-h`
- usage source `upstream` ve `tokenizer` vakaları audit içine düşüyor

Fresh evidence:
- `runtime_logs/rc_h_audit_faz7_acceptance.jsonl`

Sonuç:
- `PASS`
