# Phase 24N Shadow Remediation Report

- generated_at_utc: `2026-05-04T08:25:04.958253+00:00`
- base_collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- target_collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24n`
- base_entity_count: `349403`
- target_entity_count: `349418`
- delta_entity_count: `15`
- backfill_source_count: `3`
- backfill_span_count: `15`
- canonical_key_collision_count: `0`
- binding_key_collision_count: `0`
- load_after_build: `false`
- live_8000_cutover: `false`
- build_status: `PASS`
- runtime_provenance: `reports/benchmark/phase_24N_shadow_runtime_provenance.json`

## Scope

Inserted only the Phase 24N active confirmed rows: `KANUN-12`, `KKY-03`, and `YON-04`.
`TUZUK-04` and `TUZUK-05` were not inserted into the target collection.
