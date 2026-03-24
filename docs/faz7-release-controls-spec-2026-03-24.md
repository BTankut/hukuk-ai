# FAZ7 Release Controls Spec

Tarih: 2026-03-24

Referans:
- [FAZ7-ROTASYON-RC-G-RELEASE-CONTROLS-CLOSURE-VE-NARROW-PILOT-STEERING-TALIMATI-2026-03-24.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ7-ROTASYON-RC-G-RELEASE-CONTROLS-CLOSURE-VE-NARROW-PILOT-STEERING-TALIMATI-2026-03-24.md)
- [faz7-official-implementation-plan-2026-03-24.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz7-official-implementation-plan-2026-03-24.md)

## Amaç

`RC-H`, `RC-G` answer-path’i ile birebir aynı kalırken yalnız aşağıdaki release-control diff’lerini taşır:

- auth
- immutable audit logging
- persisted trace / audit redaction
- Redis-backed session persistence
- tokenizer-backed token accounting
- observability / alerting
- API versioning
- supervision / keepalive
- backup / restore
- rollout smoke / rehearsal orchestration

## Env Contract

### RC-G Referans Lane

- `RELEASE_LANE_ID=rc_g`
- `RELEASE_CONTROLS_STRICT=false`
- `API_AUTH_ENABLED=false`
- `AUDIT_LOG_ENABLED=false`
- `SESSION_STORE_BACKEND=memory`
- `TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK=true`

Launcher:
- [launch_local_rc_g_reference_gateway.sh](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz7/launch_local_rc_g_reference_gateway.sh)

### RC-H Candidate Lane

- `RELEASE_LANE_ID=rc_h`
- `RELEASE_CONTROLS_STRICT=true`
- `API_VERSION_LABEL=2026-03-24-rc-h`
- `API_AUTH_ENABLED=true`
- `AUDIT_LOG_ENABLED=true`
- `SESSION_STORE_BACKEND=redis`
- `SESSION_STORE_REDIS_REQUIRED=true`
- `SESSION_STORE_REDIS_PING_ON_STARTUP=true`
- `REDIS_URL=redis://127.0.0.1:6379/0`
- `TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK=false`
- `TOKEN_ACCOUNTING_TOKENIZER_PATH=<local tokenizer path>`

Launcher:
- [launch_local_rc_h_candidate_gateway.sh](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz7/launch_local_rc_h_candidate_gateway.sh)

## Auth Contract

- auth strict lane’de zorunlu
- anonymous istek varsayılan olarak kapalı
- opsiyonel internal smoke açılımı:
  - `ALLOW_ANONYMOUS_INTERNAL_SMOKE=true`
  - yalnız loopback istemciden

## Audit Contract

Her kayıt append-only JSONL yazılır ve en az şu alanları taşır:

- `request_id`
- `trace_id`
- `session_id`
- `auth_subject`
- `selected_lane`
- `final_mode`
- `refusal_reason`
- `citations`
- `source_ids`
- `latency_ms`
- `usage`
- `token_accounting`
- `decision_timestamps`
- `prev_event_sha256`
- `event_sha256`

## Redaction Contract

Persist katmanında ham değer tutulmaz:

- TC kimlik no
- email
- telefon
- IP

Deterministic placeholder’lar:

- `[TR_ID_REDACTED]`
- `[EMAIL_REDACTED]`
- `[PHONE_REDACTED]`
- `[IP_REDACTED]`

Bu redaction answer text’e değil, yalnız persisted audit / trace yüzeyine uygulanır.

## Session Contract

- `RC-H` lane memory backend ile açılamaz
- Redis unavailable ise backend error metriği artar
- restart continuity proof Redis session store üzerinden yürütülür

## Token Accounting Contract

- upstream usage varsa onu kullan
- yoksa tokenizer-backed accounting kullan
- strict lane’de approximate word fallback yasak
- audit, metrics ve response usage aynı token sayısını taşıyacak

## Observability Contract

Yayınlanan ana yüzeyler:

- request count
- auth failure count
- refusal count
- hallucination-related fail count
- citation count
- latency `p50/p95/p99`
- Redis session error count
- audit write error count
- backup error count
- rollback event count
- token accounting failure count
- lane health state

Alert snapshot yüzeyleri:

- `lane_unhealthy`
- `audit_write_failure`
- `redis_unavailable`
- `token_accounting_failure`
- `backup_failure`
- `auth_failure_spike`
- `latency_regression_spike`
- `rollback_event`

## API Versioning Contract

Header’lar:

- `X-Hukuk-AI-API-Version`
- `X-Hukuk-AI-Lane`
- `X-Request-ID`

`/v1/models` gövdesi de:

- `api_version`
- `lane`

alanlarını taşır.

## Reuse Rules

Teknik reuse serbest, resmi closure değil:

- [ensure_release_lane.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz2b/ensure_release_lane.py)
- [backup_release_state.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz2b/backup_release_state.py)
- [restore_release_state.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz2b/restore_release_state.py)
- [run_controlled_cutover.sh](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz2c/run_controlled_cutover.sh)
- [run_controlled_rollback.sh](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz2c/run_controlled_rollback.sh)

Bu fazda resmi truth yalnız FAZ7 artefact’larıdır.
