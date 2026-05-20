# Hat-B Rate Limit Ve Erisim Bloker Raporu 2026-04-07

## Rate Limit And Access Blocker Table

| source_name | http_429_seen | session_or_pagination_limit_seen | portal_visible_total_signal | observed_materialization_ceiling | blocker_class |
| --- | --- | --- | ---: | --- | --- |
| Yargitay | `true` | `true` | `9851892` | `3940 repo-local row; sampled shard reprobe 429/null-response ceilingine carpti` | `AUTHORIZATION_OR_ACCESS_BLOCKER_PRESENT` |
| Danistay | `true` | `true` | `382739` | `2007 repo-local row; broader shard continuation 429/502 ceilingine carpti` | `AUTHORIZATION_OR_ACCESS_BLOCKER_PRESENT` |
| Anayasa Mahkemesi | `false` | `false` | `22271` | `no access ceiling observed; current bounded proof window = 60 visible row across page 1..3 on both portals` | `NO_ACCESS_BLOCKER_OBSERVED_WITH_CURRENT_MECHANISM` |

## Notes

- Yargitay icin blocker duplicate/id sorunu degil; source-wide shard continuation kamuya acik mekanizmada rate-limit ve response instability ile kiriliyor.
- Danistay icin blocker ilk sayfa gorunurlugu degil; daha genis shard devaminda ayni kamuya acik mekanizma stabil kapanis vermiyor.
- Anayasa Mahkemesi icin bu fazda resmi access blocker gozlenmedi; kalan problem completeness execution acilmamis olmasi, yani method-level access kaybi degil.

## Evidence Paths

- `runtime_logs/hat_b_full_materialization_v3_20260407/yargitay_shard_materialization_summary_v3.json`
- `runtime_logs/hat_b_full_materialization_v3_20260407/danistay_shard_materialization_summary_v3.json`
- `runtime_logs/hat_b_case_law_remediation_20260407/hat_b_case_law_canonical_remediation_summary.json`
