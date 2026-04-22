# Phase 10 Metric Reconciliation Audit

- source_run_dir: `reports/benchmark/runs/20260422T204628Z_phase11_full`
- validation_valid: true
- mismatches: 0

## Canonical Metrics
- total: 100
- right_document_wrong_article_or_span: 51
- missing_required_content_signal: 97
- partial_grounding_only: 97
- minimum_answer_facts_present_count: 71
- avg_required_fact_coverage_score: 0.943
- selected_article_equals_claimed_article_count: 63
- selected_article_equals_claimed_article_rate: 0.63

## Rubric Completeness Classes
- insufficient_both: 29
- rubric_sufficient: 3
- structurally_full_but_legally_misaligned: 68

## Artifact Consistency
- all checked artifacts match canonical metric counts

## 25-QID Row-Level Audit
- KANUN-09: score=6.70, pass=FAIL, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=structurally_full_but_legally_misaligned
- CBKAR-02: score=6.80, pass=FAIL, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=insufficient_both
- CBKAR-03: score=6.80, pass=FAIL, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=insufficient_both
- KANUN-07: score=7.18, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=structurally_full_but_legally_misaligned
- KANUN-21: score=7.55, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=structurally_full_but_legally_misaligned
- TEB-05: score=7.89, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=structurally_full_but_legally_misaligned
- CBK-03: score=7.90, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=structurally_full_but_legally_misaligned
- CBY-03: score=7.90, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=structurally_full_but_legally_misaligned
- KHK-06: score=7.90, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=structurally_full_but_legally_misaligned
- TUZUK-03: score=7.90, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=structurally_full_but_legally_misaligned
- KKY-01: score=8.00, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=insufficient_both
- TEB-01: score=8.35, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=insufficient_both
- KKY-08: score=8.45, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=structurally_full_but_legally_misaligned
- KANUN-14: score=8.58, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=structurally_full_but_legally_misaligned
- CBY-02: score=8.65, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=structurally_full_but_legally_misaligned
- KANUN-08: score=8.65, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=structurally_full_but_legally_misaligned
- KANUN-11: score=8.65, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=structurally_full_but_legally_misaligned
- KANUN-12: score=8.65, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=insufficient_both
- KANUN-16: score=8.65, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=structurally_full_but_legally_misaligned
- KANUN-17: score=8.65, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=insufficient_both
- KANUN-18: score=8.65, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=structurally_full_but_legally_misaligned
- KKY-03: score=8.65, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=structurally_full_but_legally_misaligned
- TEB-02: score=8.65, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=structurally_full_but_legally_misaligned
- UY-02: score=8.65, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=structurally_full_but_legally_misaligned
- UY-04: score=8.65, pass=PASS, coverage=right_doc_wrong_article_or_span, trace=right-document wrong-article/span, right_doc_wrong_span=true, completeness=structurally_full_but_legally_misaligned
