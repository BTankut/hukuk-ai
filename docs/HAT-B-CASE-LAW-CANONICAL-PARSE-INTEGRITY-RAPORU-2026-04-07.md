# Hat-B Case-Law Canonical Parse Integrity Raporu 2026-04-07

## Integrity Findings

| source_name | id_integrity_status | id_integrity_evidence | parse_error_count | duplicate_record_count | canonical_parse_complete |
| --- | --- | --- | --- | --- | --- |
| Yargitay | `true` | `recordsTotal`, `pageNumber`, `data.id`, `openKararIceregi(...)` | `0` | `0` | `false` |
| Danistay | `true` | `382739 adet dokuman`, `recordsTotal`, `data.id`, `openKararIceregiWindow(...)` | `0` | `0` | `false` |
| Anayasa Mahkemesi | `true` | `stable portal links`, `5533 Karar Bulundu`, `page=1674`, `page=554` | `0` | `0` | `false` |

## Integrity Judgment

- id_integrity_positive = `true`
- transport_and_checksum_integrity_preserved = `true`
- canonical_parse_complete_for_all = `false`
- runtime_integration_authorized = `false`
- vector_write_authorized = `false`
- serving_authorized = `false`

## Why PASS Is Not Yet Available

- Integrity is not the blocker.
- The blocker is completeness and canonical corpus materialization.
- Source bundles prove official ownership and stable addressing, but they do not yet prove full parsed decision coverage.
