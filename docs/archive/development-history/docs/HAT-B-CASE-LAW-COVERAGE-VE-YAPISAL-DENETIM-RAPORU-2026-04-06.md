# Hat-B Case-Law Coverage Ve Yapisal Denetim Raporu 2026-04-06

## Structural Audit Table

| source_name | decision_record_count | structural_parse_readiness | document_id_integrity | duplicate_record_count | parse_error_count | coverage_status |
| --- | --- | --- | --- | --- | --- | --- |
| Yargitay | `official paged search endpoint exposes recordsTotal and pageNumber metadata at query time` | `READY_HTML_PORTAL_WITH_PAGED_RESULT_METADATA` | `detail access bound to data.id via openKararIceregi` | `0 observed in acquired bundle` | `0` | `FULL_OR_LIKELY_FULL` |
| Danistay | `382739` | `READY_HTML_PORTAL_WITH_EXPLICIT_TOTAL_AND_RESULT_API` | `detail access bound to data.id via openKararIceregiWindow` | `0 observed in acquired bundle` | `0` | `FULL_OR_LIKELY_FULL` |
| Anayasa Mahkemesi | `norm=5533 visible decisions; bireysel=1674 page frontier; bireysel_stats_applications=714774; norm_stats_total=2436` | `READY_MULTI_PORTAL_WITH_OFFICIAL_STATS_AND_STABLE_DECISION_LINKS` | `stable portal ids and ND/year/no style canonical links present` | `0 observed in acquired bundle` | `0` | `FULL_OR_LIKELY_FULL` |

## Audit Notes

- Yargitay bundle icinde official search clientinin `recordsTotal`, `pageNumber` ve `data.id` alanlarini kullandigi goruldu; bu nedenle portalin paged corpus yuzeyi acquisition/provenance seviyesinde yeterli kabul edildi.
- Danistay bundle icinde landing page uzerinde `382739` adet dokuman bilgisi ve ayni zamanda paged result API ve detail id zinciri goruldu.
- Anayasa Mahkemesi bundle icinde ana karar bankasi giris sayfasi, bireysel basvuru karar bankasi, norm denetimi karar bankasi ve iki resmi istatistik yuzeyi birlikte acquire edildi; norm portalinda `5533 Karar Bulundu` sinyali ve bireysel portalinda `1674` sayfalik frontier goruldu.
- Bu denetim canonical parse/completeness fazi degildir; yalniz acquisition/provenance ve yapisal parse-readiness fazidir.

## Result

- structural_audit_status = `closed`
