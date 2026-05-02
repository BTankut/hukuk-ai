# Phase 23R-B Candidate S7 Runtime Rehydration

Generated: 2026-05-02T21:29:50Z

Scope: S7 shadow candidate runtime on `8028`; no live cutover.

## Result

Candidate `8028` was rehydrated successfully.

| Check | Result |
|---|---|
| Initial `8028` listener | absent |
| Candidate rehydration attempted | yes |
| Restored `8028` listener | present |
| `/v1/health` | OK |
| `/v1/models` | OK with `Authorization: Bearer benchmark` |
| `/v1/models` without auth | 401, expected under `RELEASE_CONTROLS_STRICT=true` |
| Lane | `phase22f_s7_full_shadow` |
| API version | `2026-05-02-phase22f-s7-full-shadow` |
| Model alias | `hukuk-ai-poc` |
| DGX model | `/models/merged_model_fabric_stage_20260321` |
| Milvus collection | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` |
| Entity count | `349403` |
| Vector dimension | `1024` |
| Guardrails | disabled |
| Verification | disabled |
| Presidio | disabled |
| Candidate process PID | `93548` |

## Rehydration Command

```bash
cd /Users/btmacstudio/Projects/hukuk-ai/api-gateway
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
  API_VERSION_LABEL=2026-05-02-phase22f-s7-full-shadow \
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
  .venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8028 --log-level info
```

## Acceptance

Candidate S7 runtime rehydration: PASS.

The candidate is ready for Phase 23R-C verification smoke.
