# Phase 7 vs Phase 6 Comparison

- phase6_run: `reports/benchmark/runs/20260422T082522Z_phase6_selector_metadata_final_v2`
- phase7_final_run: `reports/benchmark/runs/20260422T101818Z_phase7_final`
- scoring_mode: `deterministic_proxy_phase_2_answer_contract_not_human_judge`
- acceptance: `NOT_ACCEPTED`

## Headline Metrics

| metric | phase6 | phase7 | delta | target | status |
| --- | ---: | ---: | ---: | ---: | --- |
| raw_score_proxy | 660.80 | 692.02 | +31.22 | >= 675 | PASS |
| average_score_0_10_proxy | 6.61 | 6.92 | +0.31 | n/a | INFO |
| pass_proxy | 52 | 57 | +5 | >= 56 | PASS |
| fail_proxy | 48 | 43 | -5 | n/a | INFO |
| right-document wrong-article/span backlog | 42 | 74 | +32 | <= 28 | FAIL |
| wrong_family | 34 | 33 | -1 | <= 30 | FAIL |
| wrong_document | 20 | 15 | -5 | <= 18 | PASS |
| hallucinated_identifier | 47 | 44 | -3 | <= 42 | FAIL |
| needs_corpus_acquisition refreshed | 18 | 1 | -17 | <= 8 | PASS |
| unsupported_confident_claim | 19 | 16 | -3 | <= 18 | PASS |
| hallucinated_source_count | 20 | 15 | -5 | n/a | INFO |
| contract_valid | 100 | 100 | +0 | 100 | PASS |
| refused_or_empty | 0 | 0 | +0 | 0 | PASS |
| trace_rows | 100 | 100 | +0 | 100 | PASS |

Phase 7 meets 5/8 hard target metrics under the backlog-compatible interpretation. The score target is now green, but the exact article/span selection gate is not green.

## Family-Level Deltas

| family | pass p6 | pass p7 | pass delta | avg p6 | avg p7 | avg delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| CB_GENELGE | 1/4 | 0/4 | -1 | 4.41 | 3.06 | -1.35 |
| CB_KARAR | 2/8 | 4/8 | +2 | 5.67 | 6.84 | +1.17 |
| CB_KARARNAME | 6/6 | 6/6 | +0 | 9.07 | 9.14 | +0.07 |
| CB_YONETMELIK | 3/6 | 3/6 | +0 | 5.83 | 6.20 | +0.37 |
| KANUN | 11/21 | 13/21 | +2 | 6.71 | 7.16 | +0.45 |
| KHK | 5/6 | 5/6 | +0 | 8.62 | 8.55 | -0.08 |
| KKY | 6/11 | 7/11 | +1 | 7.09 | 7.68 | +0.59 |
| MULGA | 0/5 | 0/5 | +0 | 2.13 | 2.90 | +0.77 |
| TEBLIGLER | 7/8 | 7/8 | +0 | 7.67 | 7.81 | +0.14 |
| TUZUK | 3/5 | 3/5 | +0 | 7.11 | 7.11 | +0.00 |
| UY | 7/10 | 8/10 | +1 | 7.67 | 8.07 | +0.41 |
| YONETMELIK | 1/10 | 1/10 | +0 | 5.35 | 5.35 | +0.00 |

## Interpretation

Phase 7 fixed two measurement/runtime visibility problems: Turkish source-term normalization now matches canonical source surfaces, and acquisition visibility shows only one true corpus-open row.

The remaining blocker is not raw corpus absence. The refreshed owner backlog moves 17 former acquisition rows into selector/metadata work, leaving `needs_selector_logic=53` and `needs_metadata_backfill=43`. Runtime still does not reliably lock the exact article/span, and the trace metric remains `selector_exact_article_hit_rate=0.0`.

Fine-tuning should remain blocked. The next phase should target selector/article-lock semantics, source-family compatibility, and claimed-source vs selected-evidence consistency before any training run.
