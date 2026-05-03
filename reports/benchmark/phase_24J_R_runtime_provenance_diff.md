# Phase 24J-R Runtime Provenance Diff

- generated_at_utc: `2026-05-03T16:29:27.170852+00:00`
- base_run: `reports/benchmark/runs/phase23R_candidate_verification_smoke_20260502T213055Z`
- target_run: `reports/benchmark/runs/phase_24J_targeted_shadow_smoke_20260503T145613Z`
- status: `PASS`

## Material Differences

| key | BASE | TARGET |
|---|---|---|
| api_url | `http://127.0.0.1:8028/v1` | `http://127.0.0.1:8031/v1` |
| git_sha | `6015c2d48d201d941b761477d19b8a188fd3c465` | `090a77ce971b8d03c99a5ea89e8d97935efe5678` |
| milvus_collection | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24j` |
| gateway_health.lane | `phase22f_s7_full_shadow` | `phase24j_residual_shadow` |
| gateway_health.api_version | `2026-05-02-phase22f-s7-full-shadow` | `2026-05-03-phase24j-residual-shadow` |

## Hash Equality

| key | equal |
|---|---:|
| benchmark_question_file_hash_equal | `True` |
| config_hashes_equal | `True` |
| source_catalog_hashes_equal | `True` |
| source_supplement_hashes_equal | `True` |

## Decision

Phase 24J-R-C status: `PASS`.

The captured provenance differs beyond collection identity because `api_url`, `git_sha`, lane, and API version differ. Catalog/config/source supplement hashes are equal, so the stronger immediate suspect is runtime lane/collection availability rather than source catalog content drift.
