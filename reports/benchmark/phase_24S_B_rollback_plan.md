# Phase 24S-B Rollback Plan

Generated at UTC: `2026-05-05T07:04:35Z`

## Rollback Target

- API URL: `http://127.0.0.1:8000/v1`
- Collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- Expected row count: `349403`
- Lane: `phase22f_s7_full_shadow`
- API version: `2026-05-03-phase23R-E-benchmark-only-cutover`
- Model id: `hukuk-ai-poc`
- DGX model: `/models/merged_model_fabric_stage_20260321`

## Hard Rollback Triggers

- `/v1/health` is not `ok` after cutover.
- `/v1/models` does not expose `hukuk-ai-poc` with benchmark auth.
- Runtime env does not bind to the intended collection/lane/api_version.
- Milvus row count does not match the expected collection count.
- Phase 24S-D targeted smoke fails.
- Phase 24S-E minimum full benchmark gate fails.

## Rollback Command

```zsh
kill <current_8000_pid>
cd /Users/btmacstudio/Projects/hukuk-ai
DGX_BASE_URL=http://192.168.12.243:30000/v1 \
DGX_MODEL=/models/merged_model_fabric_stage_20260321 \
MILVUS_ENABLED=true \
MILVUS_URI=http://localhost:19530 \
MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024_p0_backfill \
EMBEDDING_BACKEND=remote \
EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1 \
EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct \
RELEASE_LANE_ID=phase22f_s7_full_shadow \
RELEASE_CONTROLS_STRICT=true \
API_VERSION_LABEL=2026-05-03-phase23R-E-benchmark-only-cutover \
API_AUTH_ENABLED=false \
API_AUTH_KEYS=benchmark \
AUDIT_LOG_ENABLED=false \
ALLOW_ANONYMOUS_INTERNAL_SMOKE=false \
SESSION_STORE_BACKEND=memory \
SESSION_STORE_REDIS_REQUIRED=false \
SESSION_STORE_REDIS_PING_ON_STARTUP=false \
TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK=true \
PARITY_TRACE_ENABLED=false \
RERANKER_ENABLED=false \
GUARDRAILS_ENABLED=false \
PRESIDIO_ENABLED=false \
USE_VERIFICATION=false \
nohup api-gateway/.venv/bin/python -m uvicorn api-gateway.src.main:app --host 127.0.0.1 --port 8000 --log-level info > runtime_logs/phase24S/live_8000_rollback_base.log 2>&1 &
```

## Post-Rollback Verification

Run:

```zsh
curl -sS http://127.0.0.1:8000/v1/health
curl -sS -H 'Authorization: Bearer benchmark' http://127.0.0.1:8000/v1/models
```

Expected health lane is `phase22f_s7_full_shadow`; expected collection row count is `349403`.
