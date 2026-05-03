# Phase 24J-R2 Collection Load Verification

- generated_at_utc: `2026-05-03T16:47:03.662590+00:00`
- milvus_uri: `http://localhost:19530`
- acceptance: `PASS`

| collection | expected | actual | load_before | load_after | dim | index_available | acceptance |
|---|---:|---:|---|---|---:|---:|---:|
| mevzuat_faz1_shadow_20260418_compat1024_p0_backfill | 349403 | 349403 | Loaded | Loaded | 1024 | `True` | `PASS` |
| mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24j | 349420 | 349420 | NotLoad | Loaded | 1024 | `True` | `PASS` |
