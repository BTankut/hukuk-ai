# Phase 23R-E2 Cutover Execution Log

Generated: 2026-05-03T07:58:48Z

Scope: approved `benchmark_only` cutover of live `8000` to S7 p0_backfill candidate configuration.

## Approval

```text
CUTOVER_APPROVED_BY: BT via master planner delegation
APPROVAL_DATE: 2026-05-03
APPROVED_SCOPE: benchmark_only
ROLLBACK_OWNER: BT / code assistant operator
```

## Commands Used

Stopped prior baseline listener:

```bash
OLD_PID=$(lsof -ti tcp:8000 || true)
echo "old_pid=$OLD_PID"
if [ -n "$OLD_PID" ]; then kill "$OLD_PID"; fi
sleep 1
lsof -nP -iTCP:8000 -sTCP:LISTEN || true
```

Observed old PID:

```text
old_pid=93023
```

Started live `8000` with S7 p0_backfill benchmark-only configuration:

```bash
cd /Users/btmacstudio/Projects/hukuk-ai
env \
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
  api-gateway/.venv/bin/python -m uvicorn api-gateway.src.main:app --host 127.0.0.1 --port 8000 --log-level info
```

Startup log excerpt:

```text
MilvusRetriever.from_env: uri=http://localhost:19530 collection=mevzuat_faz1_shadow_20260418_compat1024_p0_backfill embedding_backend=remote
Milvus health OK: collection=mevzuat_faz1_shadow_20260418_compat1024_p0_backfill entities=349403
Uvicorn running on http://127.0.0.1:8000
```

New live PID:

```text
69376
```

## Non-Actions

- No public serving opened.
- No productization opened.
- No fine-tuning performed.
- No model switch.
- No prompt/retrieval/top-k change.
- No source acquisition.
- No corpus materialization.
- No QID-specific runtime rule.
- No benchmark answer key used.

## Next Required Step

Proceed immediately to Phase 23R-E3 post-cutover health and provenance verification.
