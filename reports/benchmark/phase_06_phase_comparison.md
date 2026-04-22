# Phase 6 vs Phase 5 Comparison

- phase5_run: `reports/benchmark/runs/20260422T050311Z_phase5_corpus_identity_final`
- phase6_final_run: `reports/benchmark/runs/20260422T082522Z_phase6_selector_metadata_final_v2`
- scoring_mode: `deterministic_proxy_phase_2_answer_contract_not_human_judge`
- acceptance: `NOT_ACCEPTED`

## Headline Metrics

| metric | phase5 | phase6 | delta | target | status |
| --- | ---: | ---: | ---: | ---: | --- |
| raw_score_proxy | 658.22 | 660.80 | +2.58 | >= 670 | FAIL |
| average_score_0_10_proxy | 6.58 | 6.61 | +0.03 | n/a | INFO |
| pass_proxy | 51 | 52 | +1 | >= 56 | FAIL |
| fail_proxy | 49 | 48 | -1 | n/a | INFO |
| right-document wrong-article/span | 34 | 42 | +8 | <= 24 | FAIL |
| unsupported_confident_claim | 33 | 19 | -14 | <= 24 | PASS |
| wrong_family | 35 | 34 | -1 | <= 28 | FAIL |
| wrong_document | 20 | 20 | +0 | <= 17 | FAIL |
| hallucinated_identifier | 48 | 47 | -1 | <= 40 | FAIL |
| hallucinated_source_count | 20 | 20 | +0 | n/a | INFO |
| repealed_source_used_as_active | 5 | 5 | +0 | n/a | INFO |
| contract_valid | 100 | 100 | +0 | 100 | PASS |
| refused_or_empty | 0 | 0 | +0 | 0 | PASS |
| trace_rows | 100 | 100 | +0 | 100 | PASS |

## Family-Level Deltas

| family | pass p5 | pass p6 | pass delta | avg p5 | avg p6 | avg delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| CB_GENELGE | 1/4 | 1/4 | +0 | 4.41 | 4.41 | +0.00 |
| CB_KARAR | 3/8 | 2/8 | -1 | 6.12 | 5.67 | -0.45 |
| CB_KARARNAME | 6/6 | 6/6 | +0 | 9.07 | 9.07 | +0.00 |
| CB_YONETMELIK | 2/6 | 3/6 | +1 | 5.83 | 5.83 | +0.00 |
| KANUN | 10/21 | 11/21 | +1 | 6.44 | 6.71 | +0.27 |
| KHK | 5/6 | 5/6 | +0 | 8.55 | 8.62 | +0.07 |
| KKY | 7/11 | 6/11 | -1 | 7.25 | 7.09 | -0.16 |
| MULGA | 0/5 | 0/5 | +0 | 2.49 | 2.13 | -0.36 |
| TEBLIGLER | 7/8 | 7/8 | +0 | 7.67 | 7.67 | +0.00 |
| TUZUK | 3/5 | 3/5 | +0 | 7.11 | 7.11 | +0.00 |
| UY | 7/10 | 7/10 | +0 | 7.67 | 7.67 | +0.00 |
| YONETMELIK | 0/10 | 1/10 | +1 | 4.99 | 5.35 | +0.36 |

## Interpretation

Phase 6 produced a real confidence-safety gain: `unsupported_confident_claim` dropped from 33 to 19 while contract validity stayed 100/100.

The phase did not solve the dominant retrieval/selection problem. `right-document wrong-article/span` increased from 34 to 42, and the owner backlog stayed structurally unchanged at 40 selector, 39 metadata, 18 corpus acquisition rows.

The next work item should not be fine-tuning. The current blocker is still deterministic evidence selection and corpus visibility, not model knowledge.
