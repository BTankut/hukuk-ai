# Mevzuat Faz-1 Gate Raporu 2026-04-16

## Official Decision
- decision = `PASS - Mevzuat Faz-1 Shadow Integration Closed`

## PASS Criteria Contrast

| criterion | required | observed | result |
| --- | --- | --- | --- |
| source files discovered | `true` | `true` | PASS |
| checksum chain clean | `true or explainable` | `true` | PASS |
| schema mapping deterministic | `true` | `true` | PASS |
| article_rows stream ingestion completed | `true` | `true` | PASS |
| shadow collection/index created | `true` | `true` | PASS |
| active runtime changed = false | `true` | `true` | PASS |
| old eval reused = false | `true` | `true` | PASS |
| dataset-specific smoke executed | `true` | `true` | PASS |
| wrong_source_count = 0 | `true` | `0` | PASS |
| runtime_error_count = 0 | `true` | `0` | PASS |
| unexplained_count = 0 | `true` | `0` | PASS |

## Decisive Findings
- `shadow_collection_name = mevzuat_faz1_shadow_20260416`
- `ingested_row_count = 349191`
- `shadow_text_truncation_count = 326`
- `smoke_case_count = 6`
- `citation_readable_count = 5`
- `source_correct_count = 5`
- `mulga_filter_behavior = PASS`
