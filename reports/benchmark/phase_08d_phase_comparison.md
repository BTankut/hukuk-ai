# Phase 8D vs Phase 7 Delta

- phase7_summary: `reports/benchmark/phase_07_score_summary.json`
- phase8_run_dir: `reports/benchmark/runs/20260422T140047Z_phase8d_full`

## Metric Delta
| metric | phase7 | phase8d | delta |
|---|---:|---:|---:|
| raw_score_proxy | 692.02 | 692.72 | 0.7 |
| pass_proxy | 57 | 58 | 1.0 |
| wrong_document | 15 | 14 | -1.0 |
| wrong_family | 33 | 35 | 2.0 |
| hallucinated_identifier | 44 | 43 | -1.0 |
| unsupported_confident_claim | 16 | 8 | -8.0 |
| selector_exact_article_hit_rate | 0.0 | 0.84 | 0.84 |
| selected_article_equals_claimed_article_count | 34 | 77 | 43.0 |
| avg_selector_support_span_count | 2.66 | 2.65 | -0.01 |

## Promotion Targets
| target | value | status |
|---|---:|---|
| raw_score_proxy >= 700 | 692.72 | FAIL |
| pass_proxy >= 60 | 58 | FAIL |
| wrong_document <= 14 | 14 | PASS |
| wrong_family <= 30 | 35 | FAIL |
| hallucinated_identifier <= 40 | 43 | FAIL |
| unsupported_confident_claim <= 15 | 8 | PASS |
| needs_corpus_acquisition <= 1 | 1 | PASS |
| selector_exact_article_hit_rate >= 0.25 | 0.84 | PASS |
| selected_article equals claimed >= 50/100 | 77 | PASS |
| right-document wrong-span backlog <= 50 | 48 | PASS |

Promotion target count: **6/10**.
Fine-tuning gate: **CLOSED** because Phase 8 did not reach 7/10 promotion targets and missed raw/pass/wrong_family/hallucinated_identifier gates.
