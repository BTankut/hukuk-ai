# Phase 24HR Shadow Collection Verify

- generated_at_utc: `2026-05-06T16:06:39.674787+00:00`
- status: `PASS`
- row_count: `9`
- pass_count: `9`
- warn_count: `0`
- fail_count: `0`
- base_collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- target_collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24hr`
- base_entity_count: `349403`
- target_entity_count: `349462`
- delta_row_count: `59`
- target_delta_rows_found: `59`
- base_delta_id_collision_count: `0`
- load_state: `{'state': <LoadState: Loaded>}`
- live_8000_modified: `false`
- candidate_gateway_started: `false`
- model_inference_called: `false`

| check | status | expected | observed |
|---|---|---|---|
| `base_collection_exists` | `PASS` | exists | True |
| `target_collection_exists` | `PASS` | exists | True |
| `base_entity_count` | `PASS` | >0 | 349403 |
| `target_entity_count` | `PASS` | >= 349462 | 349462 |
| `target_delta_rows_found` | `PASS` | 59 | 59 |
| `base_delta_id_collision` | `PASS` | 0 | 0 |
| `delta_metadata_integrity` | `PASS` | all expected metadata values | ok |
| `delta_text_not_truncated` | `PASS` | no truncation and expected text lengths | ok |
| `target_load_state_observed` | `PASS` | loaded if server exposes load state | {'state': <LoadState: Loaded>} |
