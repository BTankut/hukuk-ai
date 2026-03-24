# FAZ7 Redis Session Acceptance

Tarih: 2026-03-24

Scope:
- hedef lane: `rc_h`
- backend: `redis`

Env / signature:
- `SESSION_STORE_BACKEND=redis`
- `SESSION_STORE_REDIS_REQUIRED=true`
- `REDIS_URL=redis://127.0.0.1:6379/0`

Komut / kanıt:
- `bash scripts/faz7/launch_local_redis.sh`
- `python3 scripts/faz7/run_release_smoke_suite.py --base-url http://127.0.0.1:8005 --api-key faz7-internal-key --output-path runtime_logs/faz7_release_smoke_rc_h.json`
- `python3 scripts/faz2b/ensure_release_lane.py ... > runtime_logs/faz7_rc_h_supervision.json`

Gözlem:
- smoke session continuity `history_length = 4`
- delete sonrası session cleanup dönüyor
- supervision health/metrics/audit birlikte `healthy = true`
- alerts yüzeyinde `redis_unavailable = false`

Fresh evidence:
- `evaluation/reports/faz7-release-smoke-acceptance-2026-03-24.json`
- `coordination/faz7-process-supervision-snapshot-2026-03-24.json`
- `evaluation/reports/faz7-rc-h-alerts-snapshot-2026-03-24.json`

Sonuç:
- `PASS`
