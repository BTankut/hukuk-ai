# Phase 24S-B Pre-Cutover Live Backup

Generated at UTC: `2026-05-05T07:04:35Z`  
Git HEAD: `51a629d5ef74eccb43128173ff0af442b7557c72`  
Live API: `http://127.0.0.1:8000/v1`  
Live PID: `69376`

## Live Runtime

- Lane: `phase22f_s7_full_shadow`
- API version: `2026-05-03-phase23R-E-benchmark-only-cutover`
- Health status: `200`
- Model id: `hukuk-ai-poc` (validated with `Authorization: Bearer benchmark`)
- DGX model: `/models/merged_model_fabric_stage_20260321`
- DGX base URL: `http://192.168.12.243:30000/v1`
- Guardrails: `false`
- Verification: `false`
- Reranker: `false`

## Live Collection

- `MILVUS_COLLECTION`: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- Base row count: `349403`
- Base load state: `Loaded`
- CBY candidate row count: `349405`
- CBY candidate load state: `Loaded`

## Contract Observations

- `/v1/health` returned `200`.
- `/v1/models` without auth returned `401`.
- `/v1/models` with `Authorization: Bearer benchmark` returned `200` and exposed `hukuk-ai-poc`.

## Backup Decision

This backup confirms live `8000` is still on the base benchmark-only collection before Phase 24S-C. No runtime state was changed in this step.
