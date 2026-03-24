# FAZ7 Observability and Alerting Acceptance

Tarih: 2026-03-24

Scope:
- `/v1/metrics`
- `/v1/alerts`

Komut / kanıt:
- `curl -H 'X-API-Key: faz7-internal-key' http://127.0.0.1:8005/v1/alerts > runtime_logs/faz7_rc_h_alerts.json`
- `curl -H 'X-API-Key: faz7-internal-key' http://127.0.0.1:8005/v1/metrics > runtime_logs/faz7_rc_h_metrics.txt`

Gözlem:
- alert yüzeyinde tüm failure flag’leri `false`
- `lane = rc_h`
- `api_version = 2026-03-24-rc-h`
- metrics yüzeyinde:
  - `hukuk_ai_audit_events_total`
  - `hukuk_ai_auth_failure_total`
  - `hukuk_ai_usage_source_total`
  - `hukuk_ai_lane_health_state{lane="rc_h"} 1`

Fresh evidence:
- `evaluation/reports/faz7-rc-h-alerts-snapshot-2026-03-24.json`
- `evaluation/reports/faz7-rc-h-metrics-excerpt-2026-03-24.txt`

Sonuç:
- `PASS`
