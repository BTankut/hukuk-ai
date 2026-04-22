# Phase 10 vs Phase 9 Comparison

- phase9_run_dir: `reports/benchmark/runs/20260422T153521Z_phase9_full`
- phase10_run_dir: `reports/benchmark/runs/20260422T180225Z_phase10_full`

## Metric Delta

| metric | phase9 | phase10 | delta |
|---|---:|---:|---:|
| raw_score_proxy | 700.91 | 687.52 | -13.39 |
| pass_proxy | 59 | 55 | -4 |
| wrong_family | 35 | 36 | +1 |
| wrong_document | 16 | 15 | -1 |
| hallucinated_identifier | 44 | 32 | -12 |
| unsupported_confident_claim | 8 | 7 | -1 |
| hallucinated_source_count | 16 | 15 | -1 |
| selector_exact_article_hit_rate | 0.84 | 0.84 | +0 |
| selected_article_equals_claimed_article_count | 75 | 64 | -11 |
| right_document_wrong_article_or_span | 52 | 51 | -1 |
| missing_required_content_signal | 97 | 97 | +0 |
| partial_grounding_only | 97 | 97 | +0 |

## Promotion Targets

| target | result | status |
|---|---:|---|
| raw_score_proxy >= 705 | 687.52 | FAIL |
| pass_proxy >= 60 | 55 | FAIL |
| wrong_family <= 30 | 36 | FAIL |
| wrong_document <= 14 | 15 | FAIL |
| hallucinated_identifier <= 40 | 32 | PASS |
| unsupported_confident_claim <= 10 | 7 | PASS |
| selector_exact_article_hit_rate >= 0.8 | 0.84 | PASS |
| selected_article_equals_claimed_article_count >= 75 | 64 | FAIL |
| right_document_wrong_article_or_span <= 50 | 51 | FAIL |
| missing_required_content_signal <= 90 | 97 | FAIL |
| partial_grounding_only <= 90 | 97 | FAIL |
| needs_corpus_acquisition <= 1 | 21 | FAIL |

- targets_met: 3/12
- promotion_decision: REJECT
- fine_tuning_gate: CLOSED
