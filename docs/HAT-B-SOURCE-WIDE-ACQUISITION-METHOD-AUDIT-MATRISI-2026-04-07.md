# Hat-B Source-Wide Acquisition Method Audit Matrisi 2026-04-07

## Acquisition Method Audit Matrix

| source_name | official_total_signal | current_method | current_method_failure_mode | rate_limit_or_access_blocker | source_wide_completion_possible_with_current_method | required_replacement_method | official_status_judgment |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| Yargitay | `9851892` | `public session-aware paginated search + unit-sharded crawl` | `source-wide shard continuation collapses under HTTP 429 and null-response surfaces before full row closure` | `true` | `false` | `official bulk feed/export or institution-authorized high-volume acquisition track` | `AUTHORIZATION_OR_ACCESS_BLOCKER_PRESENT` |
| Danistay | `382739` | `public session-aware paginated search + daire/kurul-sharded crawl` | `broader shard continuation becomes unstable; HTTP 429 and 502 surfaces appear before source-wide closure` | `true` | `false` | `official bulk feed/export or institution-authorized high-volume acquisition track` | `AUTHORIZATION_OR_ACCESS_BLOCKER_PRESENT` |
| Anayasa Mahkemesi | `22271` | `official multi-portal paginated crawl (bireysel basvuru + norm denetimi)` | `no access/rate-limit blocker observed in current mechanism; bounded runs stayed partial but did not show method-level closure loss` | `false` | `true` | `continue official multi-portal paginated acquisition with canonical row materialization` | `SOURCE_WIDE_ACQUIRABLE_WITH_CURRENT_MECHANISM` |

## Official Basis

- `Yargitay materialized_row_count = 3940`, `official_total_signal = 9851892`, `coverage_ratio = 0.00039992`
- `Danistay materialized_row_count = 2007`, `official_total_signal = 382739`, `coverage_ratio = 0.00524378`
- `Anayasa Mahkemesi materialized_row_count = 60`, `official_total_signal = 22271`, `coverage_ratio = 0.00269409`
- `Yargitay` tarafinda official `HTTP 429` yuzeyi gozlendi.
- uc kaynakta da `canonical_parse_complete = false` ve `completeness_status = PARTIAL_OR_UNPROVEN`

## Evidence Paths

- `runtime_logs/hat_b_full_materialization_v3_20260407/yargitay_shard_materialization_summary_v3.json`
- `runtime_logs/hat_b_full_materialization_v3_20260407/danistay_shard_materialization_summary_v3.json`
- `runtime_logs/hat_b_case_law_remediation_20260407/hat_b_case_law_canonical_remediation_summary.json`
- `data/case_law/full_acquisition/yargitay/official_source_bundle.html`
- `data/case_law/full_acquisition/danistay/official_source_bundle.html`
- `data/case_law/full_acquisition/anayasa_mahkemesi/official_source_bundle.html`
