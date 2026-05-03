# Phase 24M Residual Blocker Consolidation

- generated_at_utc: `2026-05-03T17:51:51Z`
- residual_row_count: `9`
- status: `BLOCKED_BY_EXTERNAL_LEGAL_SCORER_SOURCE_CLOSURE`

## Source Runs

Scores for rows included in Phase 24J-R2 residual targeted smoke use:

```text
reports/benchmark/runs/20260503T165451Z_phase24J_R2_target_residual_targeted/scored.csv
```

Rows not included in that targeted smoke use the latest full stability run:

```text
reports/benchmark/runs/20260503T091350Z_phase23R_E6_stability_full/scored.csv
```

## Consolidated Table

| qid | score | current_status | blocks_internal_eval | blocks_productization | safe_next_action | owner |
|---|---:|---|---|---|---|---|
| CBY-04 | 6.85 | source identity design blocker | true | true | scorer_rubric_review_required | legal_scorer_plus_source_identity |
| CBY-06 | 6.80 | current amendment span blocker | true | true | corpus_backfill_required | source_acquisition_corpus |
| KANUN-12 | 1.45 | confirmed source but no runtime improvement | true | true | await_source_acquisition | source_acquisition_legal_review |
| KKY-01 | 6.65 | taxonomy mapping blocker | conditional | conditional | scorer_rubric_review_required | legal_scorer_taxonomy |
| KKY-03 | 1.45 | confirmed source but no runtime improvement | true | true | await_legal_scorer_review | legal_scorer_source_acquisition |
| TEB-04 | 0.00 | consolidated tebliğ source/span blocker | false | conditional | scorer_rubric_review_required | legal_scorer_corpus |
| TUZUK-04 | 4.63 | current-law vs repealed-source blocker | true | true | await_source_acquisition | source_acquisition_legal_review |
| TUZUK-05 | 3.25 | unidentified source blocker | true | true | await_source_acquisition | source_acquisition_legal_review |
| YON-04 | 3.25 | confirmed source but no runtime improvement | true | true | await_legal_scorer_review | legal_scorer_source_acquisition |

## Decision

No safe runtime patch is authorized from this table. The remaining work is legal/scorer/source/corpus closure, not another prompt, top-k, source identity shortcut, or QID-specific runtime branch.
