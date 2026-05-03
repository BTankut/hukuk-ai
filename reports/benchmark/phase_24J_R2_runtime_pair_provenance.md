# Phase 24J-R2 Runtime Pair Provenance

- generated_at_utc: `2026-05-03T16:48:19.326464+00:00`
- git_sha: `d0c1a7c6bd7ca6b01f1e30dd2a6140970f97bd5c`
- acceptance: `PASS`

| runtime | api_url | pid | health | models | lane | api_version | collection |
|---|---|---:|---:|---:|---|---|---|
| BASE | `http://127.0.0.1:8032/v1` | `39841` | `True` | `True` | `phase24j_r2_normalized_pair` | `2026-05-03-phase24j-r2-normalized` | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` |
| TARGET | `http://127.0.0.1:8033/v1` | `39900` | `True` | `True` | `phase24j_r2_normalized_pair` | `2026-05-03-phase24j-r2-normalized` | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24j` |

## Env Diffs

```json
{
  "MILVUS_COLLECTION": {
    "base": "mevzuat_faz1_shadow_20260418_compat1024_p0_backfill",
    "target": "mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24j"
  }
}
```

## Health Diffs

```json
{}
```
