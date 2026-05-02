# Phase 23R-A Live Baseline Health Restore

Generated: 2026-05-02T21:28:16Z

Scope: restore/diagnose current baseline `8000`; no candidate cutover.

## Result

Baseline `8000` was restored successfully.

| Check | Result |
|---|---|
| Initial `8000` listener | absent |
| Baseline restore attempted | yes |
| Restored `8000` listener | present |
| `/v1/health` | OK |
| `/v1/models` | OK |
| Lane | `current_serving_lane` |
| API version | `2026-03-24-rc-h` |
| Model alias | `hukuk-ai-poc` |
| DGX model | `/models/merged_model_fabric_stage_20260321` |
| Milvus collection | `mevzuat_faz1_shadow_20260418_compat1024` |
| Entity count | `349191` |
| Vector dimension | `1024` |
| Guardrails | disabled |
| Verification | disabled |
| Presidio | disabled |

## Process / Dependency Status

| Component | Observation |
|---|---|
| `tmux ls` | no server running |
| Docker | available |
| `hukuk-ai-milvus` | running |
| Embedding endpoint `127.0.0.1:8081` | OK, `intfloat/multilingual-e5-large-instruct` |
| DGX endpoint `192.168.12.243:30000` | OK, `/models/merged_model_fabric_stage_20260321` |
| Restored baseline process PID | `93023` |

## Restore Command

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

## Acceptance

`8000 healthy on baseline`: PASS.

No live cutover was performed. Productization and fine-tuning remain closed.
