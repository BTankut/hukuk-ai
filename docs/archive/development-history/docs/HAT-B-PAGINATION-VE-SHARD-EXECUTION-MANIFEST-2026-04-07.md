# Hat-B Pagination Ve Shard Execution Manifest 2026-04-07

| source_name | partition_count | page_span_materialized | row_materialization_completed | materialized_row_count | official_total_signal | coverage_ratio |
| --- | --- | --- | --- | --- | --- | --- |
| Yargitay | `51` | `sampled shard reprobe blocked by 429 before source-wide pagination could advance` | `false` | `3940` | `9851892` | `0.00039992` |
| Danistay | `29` | `sampled 8 shard on page 1..5; 1. Daire full 1..6` | `false` | `2007` | `382739` | `0.00524378` |
| Anayasa Mahkemesi | `2` | `bireysel=1..3 ; norm=1..3` | `false` | `60` | `22271` | `0.00269409` |

## Execution Notes

- Yargitay current remediation re-probe official runtime surface tarafinda genis 429 rate-limit verdi; materialization count onceki repo-local rowset seviyesinde kaldi.
- Danistay current remediation run'da sampled shard pagination first-page disina cikti ve rowset `1365 -> 2007` seviyesine yukseltilmis kanit uretildi; source-wide closure yine de acik kaldi.
- Anayasa Mahkemesi current remediation run'da bundle-visible sinirdan cikilip her iki portal icin page `1..3` materialize edildi; rowset `20 -> 60` seviyesine cikti.
