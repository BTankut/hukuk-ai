# Hat-B Official Bulk Export Veya Feed Feasibility Raporu 2026-04-07

## Bulk Export Or Feed Feasibility Table

| source_name | official_bulk_export_evidence_found | official_api_or_feed_evidence_found | repo_local_full_materialization_possible_without_bulk_feed | institutional_permission_required | recommended_next_method |
| --- | --- | --- | --- | --- | --- |
| Yargitay | `false` | `false` | `false` | `true` | `official bulk feed/export or institution-authorized high-volume acquisition track` |
| Danistay | `false` | `false` | `false` | `true` | `official bulk feed/export or institution-authorized high-volume acquisition track` |
| Anayasa Mahkemesi | `false` | `false` | `true` | `false` | `continue official multi-portal paginated acquisition under current mechanism` |

## Method Notes

- Yargitay ve Danistay bundle'larinda ordinary page JSON transport izleri var, ancak bunlar official bulk feed/export kaniti sayilmadi.
- Uc kaynakta da corpus-wide resmi export/feed yuzeyi repo-local bundle kanitinda bulunmadi.
- Bu nedenle Yargitay ve Danistay icin current public mechanism source-wide kapanis vermedigi surece resmi bulk/access track zorunlu sayildi.
- Anayasa Mahkemesi icin bulk/feed yuzeyi bulunmamis olsa da public multi-portal current mechanism source-wide acquisition methodi olarak kapanabilir gorunuyor.

## Evidence Paths

- `data/case_law/full_acquisition/yargitay/official_source_bundle.html`
- `data/case_law/full_acquisition/danistay/official_source_bundle.html`
- `data/case_law/full_acquisition/anayasa_mahkemesi/official_source_bundle.html`
