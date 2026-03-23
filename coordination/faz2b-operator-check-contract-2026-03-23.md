# FAZ 2B Operator Check Contract

## Intent
- Give the release lane a minimal operator-facing check surface that does not rely on log tailing only.

## Runtime surfaces
- Health:
  - `GET /v1/health`
- Metrics:
  - `GET /v1/metrics`
  - protected by the same API auth gate when auth is enabled
- Audit trail:
  - `runtime_logs/api_audit.jsonl` by default
  - override with `AUDIT_LOG_PATH`

## Required env contract
- `API_AUTH_ENABLED=true`
- `API_AUTH_KEYS=...` or `API_AUTH_TOKEN=...`
- `AUDIT_LOG_ENABLED=true`
- `SESSION_STORE_BACKEND=redis` on the release lane
- `REDIS_URL=...` or `SESSION_STORE_REDIS_URL=...`
- optional:
  - `SESSION_STORE_NAMESPACE=hukuk-ai`
  - `AUDIT_LOG_PATH=...`

## Minimum operator checks
1. `GET /v1/health` returns `status=ok`.
2. `GET /v1/metrics` returns Prometheus text and is auth-protected.
3. `hukuk_ai_http_requests_total` advances under live traffic.
4. `hukuk_ai_audit_events_total` advances when audit logging is enabled.
5. At least one of:
   - `hukuk_ai_chat_blocked_total`
   - `hukuk_ai_chat_refusal_total`
   - `hukuk_ai_usage_source_total`
   is present after chat traffic.
6. Redis-backed session lane preserves shared session state across gateway instances.

## Alerting thresholds
- Immediate operator action:
  - `/v1/health` not `ok`
  - `/v1/metrics` unavailable
  - audit events stop growing while request counters grow
- Investigate within same release window:
  - repeated spikes in blocked/refusal counters inconsistent with expected workload
  - usage source unexpectedly falling back away from upstream-backed accounting

## Release position
- This contract is sufficient for FAZ 2B operator visibility closure.
- It is not a substitute for keepalive/supervision or backup/restore proof.
