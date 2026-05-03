# Phase 24J-R2 Provenance Normalization Plan

- generated_at_utc: `2026-05-03T16:46:56.751247+00:00`
- same_git_sha: `2680fff9809e61e83df5ee6dd56a13b42928d414`
- base_api: `http://127.0.0.1:8032/v1`
- target_api: `http://127.0.0.1:8033/v1`
- base_collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- target_collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24j`
- status: `PASS`

## Normalized Runtime Contract

| Field | Value |
|---|---|
| DGX_MODEL | `/models/merged_model_fabric_stage_20260321` |
| EMBEDDING_MODEL | `intfloat/multilingual-e5-large-instruct` |
| vector_dimension | `1024` |
| guardrails | `false` |
| verification | `false` |
| presidio | `false` |
| RELEASE_LANE_ID | `phase24j_r2_normalized_pair` |
| API_VERSION_LABEL | `2026-05-03-phase24j-r2-normalized` |

Only `MILVUS_COLLECTION` and API port may differ between BASE and TARGET candidate runtimes.

## Command Template

```bash
env <normalized_env> MILVUS_COLLECTION=<collection> api-gateway/.venv/bin/python -m uvicorn api-gateway.src.main:app --host 127.0.0.1 --port <port> --log-level info
```

## Verification Commands

```bash
api-gateway/.venv/bin/python scripts/benchmark/phase24j_r2_normalized_provenance.py verify-collections
curl -sS http://127.0.0.1:<port>/v1/health
curl -sS -H 'Authorization: Bearer benchmark' http://127.0.0.1:<port>/v1/models
```
