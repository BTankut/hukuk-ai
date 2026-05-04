# Phase 24N Source Bundle Verification

- generated_at_utc: `2026-05-04T08:22:20.477973+00:00`
- source_checklist: `reports/benchmark/legal_review_returns/filled_phase_24I_official_source_acquisition_checklist.csv`
- eligible_shadow_backfill_count: `3`
- expected_eligible_count: `3`
- acceptance: `PASS`
- live_8000_modified: `false`

| qid | classification | parser | legal | effective_state | allowed | blocking_reason |
|---|---|---|---|---|---:|---|
| KANUN-12 | eligible_shadow_backfill | yes | confirmed | amended | true |  |
| KKY-03 | eligible_shadow_backfill | yes | confirmed | amended | true |  |
| YON-04 | eligible_shadow_backfill | yes | confirmed | amended | true |  |
| TUZUK-04 | limited_historical_guard_only | yes | confirmed | repealed | false | historical_repealed_only_not_current_law_primary |
| TUZUK-05 | excluded_open_residual | no | needs_more_review | unknown | false | not_found_needs_more_review_no_synthetic_backfill |

## Decision

Phase 24N source bundle verification passes for `KANUN-12`, `KKY-03`, and `YON-04`.
`TUZUK-04` is retained only as a historical/repealed guard and is not inserted into the Phase 24N target collection.
`TUZUK-05` remains excluded.
