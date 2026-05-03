# Phase 23R-E1 Pre-Cutover Live Backup

Generated: 2026-05-03T07:57:15Z

Scope: backup current live `8000` before approved benchmark-only cutover.

## Approval

```text
CUTOVER_APPROVED_BY: BT via master planner delegation
APPROVAL_DATE: 2026-05-03
APPROVED_SCOPE: benchmark_only
ROLLBACK_OWNER: BT / code assistant operator
```

## Current Live State

| Field | Value |
|---|---|
| live_api_url | `http://127.0.0.1:8000/v1` |
| live_pid | `93023` |
| live_lane | `current_serving_lane` |
| live_git_sha | `53a96a157f10dfb0b05dc8548fa96badab729850` |
| live_model_alias | `hukuk-ai-poc` |
| live_dgx_model_env | `/models/merged_model_fabric_stage_20260321` |
| live_milvus_collection | `mevzuat_faz1_shadow_20260418_compat1024` |
| live_entity_count | `349191` |
| live_vector_dimension | `1024` |
| live_guardrails_state | `disabled` |
| live_verification_state | `disabled` |
| live_health_status | `ok` |

`/v1/models` returned model alias `hukuk-ai-poc` on lane `current_serving_lane`.

## Exact Baseline Restart Command

```bash
cd /Users/btmacstudio/Projects/hukuk-ai
env \
  DGX_BASE_URL=http://192.168.12.243:30000/v1 \
  DGX_MODEL=/models/merged_model_fabric_stage_20260321 \
  MILVUS_ENABLED=true \
  MILVUS_URI=http://localhost:19530 \
  MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024 \
  EMBEDDING_BACKEND=remote \
  EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1 \
  EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct \
  RELEASE_LANE_ID=current_serving_lane \
  API_VERSION_LABEL=2026-03-24-rc-h \
  API_AUTH_ENABLED=false \
  AUDIT_LOG_ENABLED=false \
  SESSION_STORE_BACKEND=memory \
  SESSION_STORE_REDIS_REQUIRED=false \
  SESSION_STORE_REDIS_PING_ON_STARTUP=false \
  TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK=true \
  PARITY_TRACE_ENABLED=true \
  RERANKER_ENABLED=false \
  GUARDRAILS_ENABLED=false \
  PRESIDIO_ENABLED=false \
  USE_VERIFICATION=false \
  VERIFICATION_ENABLED=false \
  api-gateway/.venv/bin/python -m uvicorn api-gateway.src.main:app --host 127.0.0.1 --port 8000 --log-level info
```

No tmux session was present for this runtime; the process was running under the current operator session.

## Rollback Command

```bash
kill $(lsof -ti tcp:8000)
cd /Users/btmacstudio/Projects/hukuk-ai
env \
  DGX_BASE_URL=http://192.168.12.243:30000/v1 \
  DGX_MODEL=/models/merged_model_fabric_stage_20260321 \
  MILVUS_ENABLED=true \
  MILVUS_URI=http://localhost:19530 \
  MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024 \
  EMBEDDING_BACKEND=remote \
  EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1 \
  EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct \
  RELEASE_LANE_ID=current_serving_lane \
  API_VERSION_LABEL=2026-03-24-rc-h \
  API_AUTH_ENABLED=false \
  AUDIT_LOG_ENABLED=false \
  SESSION_STORE_BACKEND=memory \
  SESSION_STORE_REDIS_REQUIRED=false \
  SESSION_STORE_REDIS_PING_ON_STARTUP=false \
  TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK=true \
  PARITY_TRACE_ENABLED=true \
  RERANKER_ENABLED=false \
  GUARDRAILS_ENABLED=false \
  PRESIDIO_ENABLED=false \
  USE_VERIFICATION=false \
  VERIFICATION_ENABLED=false \
  api-gateway/.venv/bin/python -m uvicorn api-gateway.src.main:app --host 127.0.0.1 --port 8000 --log-level info
```

## Candidate Target For E2

| Field | Value |
|---|---|
| lane | `phase22f_s7_full_shadow` |
| collection | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` |
| entity_count | `349403` |
| vector_dimension | `1024` |
| model | `/models/merged_model_fabric_stage_20260321` |
| scope | `benchmark_only` |

## Dependency Checks

| Check | Result |
|---|---|
| embedding endpoint | OK, `intfloat/multilingual-e5-large-instruct` |
| DGX endpoint | OK, `/models/merged_model_fabric_stage_20260321` |
| baseline collection | OK, `349191`, dim `1024` |
| candidate collection | OK, `349403`, dim `1024` |
