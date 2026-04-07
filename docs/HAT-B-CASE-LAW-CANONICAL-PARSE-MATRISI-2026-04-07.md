# Hat-B Case-Law Canonical Parse Matrisi 2026-04-07

## Canonical Parse Matrix

| source_name | raw_source_file_path | canonical_parse_surface | parse_error_count | duplicate_record_count | id_integrity_status | canonical_parse_complete | unexplained_gap_count | completeness_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Yargitay | `data/case_law/full_acquisition/yargitay/official_source_bundle.html` | `portal_search_shell_with_recordsTotal_and_data.id_hooks` | `0` | `0` | `true` | `false` | `1` | `PARTIAL_OR_UNPROVEN` |
| Danistay | `data/case_law/full_acquisition/danistay/official_source_bundle.html` | `portal_search_shell_with_explicit_total_and_detail_id_hooks` | `0` | `0` | `true` | `false` | `1` | `PARTIAL_OR_UNPROVEN` |
| Anayasa Mahkemesi | `data/case_law/full_acquisition/anayasa_mahkemesi/official_source_bundle.html` | `multi_portal_shell_with_decision_links_pagination_and_official_statistics` | `0` | `0` | `true` | `false` | `1` | `PARTIAL_OR_UNPROVEN` |

## Matrix Notes

- `parse_error_count = 0` because acquired official bundles were structurally readable and the decisive metadata signals were extractable.
- `duplicate_record_count = 0` because this gate did not materialize a full decision rowset; no duplicate canonical row emission was observed in the extracted audit surface.
- `id_integrity_status = true` because each minimum source exposed stable document-level addressing signals:
  - Yargitay: `data.id` and `openKararIceregi(...)`
  - Danistay: `data.id` and `openKararIceregiWindow(...)`
  - Anayasa Mahkemesi: stable decision links and paged portal references
- `canonical_parse_complete = false` because none of the three sources has yet been materialized into a full canonical decision corpus under repo-local canonical parse outputs.
