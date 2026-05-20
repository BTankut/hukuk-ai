# RC-S Raw Storage Map 2026-04-01

| source_class | raw_root_path | raw_file_set | update_authority | checksum_policy | immutability_rule |
| --- | --- | --- | --- | --- | --- |
| TMK core corpus | `data/primary_sources/raw/tmk_core_corpus/` | `kanun_source.xml, article_index.jsonl, source_manifest.json, checksums.sha256` | `official_primary_source_registry` | `sha256 per-file + manifest aggregate hash` | `append-only snapshot, no in-place overwrite` |
| TCK | `data/primary_sources/raw/tck/` | `kanun_source.xml, article_index.jsonl, source_manifest.json, checksums.sha256` | `official_primary_source_registry` | `sha256 per-file + manifest aggregate hash` | `append-only snapshot, no in-place overwrite` |
| HMK | `data/primary_sources/raw/hmk/` | `kanun_source.xml, article_index.jsonl, source_manifest.json, checksums.sha256` | `official_primary_source_registry` | `sha256 per-file + manifest aggregate hash` | `append-only snapshot, no in-place overwrite` |
| CMK | `data/primary_sources/raw/cmk/` | `kanun_source.xml, article_index.jsonl, source_manifest.json, checksums.sha256` | `official_primary_source_registry` | `sha256 per-file + manifest aggregate hash` | `append-only snapshot, no in-place overwrite` |
| TTK | `data/primary_sources/raw/ttk/` | `kanun_source.xml, article_index.jsonl, source_manifest.json, checksums.sha256` | `official_primary_source_registry` | `sha256 per-file + manifest aggregate hash` | `append-only snapshot, no in-place overwrite` |
| İK | `data/primary_sources/raw/ik/` | `kanun_source.xml, article_index.jsonl, source_manifest.json, checksums.sha256` | `official_primary_source_registry` | `sha256 per-file + manifest aggregate hash` | `append-only snapshot, no in-place overwrite` |

## Summary

- raw_storage_locations_defined_for_all_primary_sources = `true`
- missing_primary_raw_storage_location_count = `0`
- actual_source_ingestion_started = `false`
- vector_db_write_started = `false`
