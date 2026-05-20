# Canonical Full Primary Law Eval Pack Contract 2026-04-06

## Official Pack Shape

- canonical_pack_total_row_count = `300`
- source_local_total = `216`
- cross_law_wrong_primary_total = `60`
- refusal_excluded_source_total = `24`
- current_57_row_pack_status = `regression_only`

## Exact Per-Source Distribution

| source_class | source_local_rows | cross_law_rows | total_rows |
| --- | ---: | ---: | ---: |
| TMK core corpus | 36 | 12 | 48 |
| TCK | 36 | 12 | 48 |
| HMK | 36 | 12 | 48 |
| CMK | 36 | 0 | 36 |
| TTK | 36 | 12 | 48 |
| İK | 36 | 12 | 48 |

## Mandatory Row Contract

- every row includes `id`, `question`, `category`, `expected_sources`, `refusal_expected`, `source_class`, `coverage_tags`.
- every supported row is article-anchored and bound to one official primary-law source.
- every cross-law row carries `cross_law_disambiguation = true`.
- every refusal row is bound to excluded-source / unsupported-law behavior only.

## Canonicalization Decision

- official_hat = `Hat-A`
- canonical_primary_law_acceptance_pack_ready = `true`
- old_source_level_lawyer_batches_only_regression = `true`
