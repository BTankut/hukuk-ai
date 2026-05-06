# Phase 24HR Shadow Collection Dry-Run Manifest

- generated_at_utc: `2026-05-06T15:59:05.202251+00:00`
- status: `PASS`
- base_collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- target_collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24hr`
- delta_row_count: `59`
- expected_delta_row_count: `59`
- embedding_model: `intfloat/multilingual-e5-large-instruct`
- vector_dimension: `1024`
- canonical_key_collision_count: `0`
- binding_key_collision_count: `0`
- proposed_id_collision_count: `0`
- max_proposed_id_length: `79`
- max_proposed_text_length: `6462`
- max_chunk_body_text_length: `6410`
- max_full_span_body_text_length: `76818`
- raw_sha256: `bdea3737f421203d3814fce7c4b72c617dacd03878d4d8e655cacc9e19d0df68`
- source_identifier: `19631`
- source_family: `teblig`
- runtime_locator_coverage_pass: `true`
- live_8000_modified: `false`
- milvus_modified: `false`
- candidate_gateway_started: `false`
- embedding_called: `false`
- model_inference_called: `false`
- base_collection_collision_check_executed: `false`
- full_spans_used_for_delta: `false`
- chunked_subspans_used_for_delta: `true`

## Outputs

- manifest_csv: `reports/benchmark/phase_24HR_shadow_collection_dry_run_manifest.csv`
- manifest_jsonl: `reports/benchmark/phase_24HR_shadow_collection_dry_run_manifest.jsonl`
- summary_json: `reports/benchmark/phase_24HR_shadow_collection_dry_run_summary.json`

## Delta Rows By Parent Locator

| parent_locator | delta_rows |
|---|---:|
| `I/C-2.1.3` | 55 |
| `I/C-2.1.5` | 4 |

## Decision

- Dry-run manifest is local-only evidence for option A authorization readiness.
- It does not prove base collection collision absence because Milvus collision queries were intentionally not executed.
- Building/loading the shadow collection still requires explicit authorization via `reports/benchmark/productization/phase_24HR_shadow_validation_authorization_packet.md`.
