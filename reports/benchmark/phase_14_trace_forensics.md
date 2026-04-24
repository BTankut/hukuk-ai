# Phase 3 Retrieval Trace Forensics

- source_run_dir: `reports/benchmark/runs/20260424T060640Z_phase14_full_diagnostic`
- rows_analyzed: 100
- failing_rows_with_failure_classes: 96
- weak_family_failing_rows: 61

## Canonical Metric Counts
- right_document_wrong_article_or_span: 70
- missing_required_content_signal: 96
- partial_grounding_only: 96
- minimum_answer_facts_present_count: 75
- avg_required_fact_coverage_score: 0.882
- selected_article_equals_claimed_article_count: 80

## Dominant Failure Mechanisms
- right-document wrong-article/span: 70 (72.9%)
- right-family wrong-document: 10 (10.4%)
- wrong-family retrieval: 10 (10.4%)
- temporal_miss: 3 (3.1%)
- generation overreach: 2 (2.1%)
- retrieval miss: 1 (1.0%)

## Failure Classes
- missing_required_content_signal: 96
- partial_grounding_only: 96
- unsupported_confident_claim: 25
- hallucinated_identifier: 21
- wrong_family: 15
- missing_gold_document_signal: 13
- wrong_document: 13
- insufficient_canonical_span_evidence: 13
- repealed_source_used_as_active: 3
- wrong_article: 2
- auto_fail_triggered: 2

## Article Alignment
- exact: 70
- none: 16
- title_only: 12
- neighbor: 2

## Query Article Alignment
- unknown: 88
- title_only: 12

## Failing Rows by Expected Family
- KANUN: 21
- KKY: 11
- YONETMELIK: 10
- UY: 9
- CB_KARAR: 8
- TEBLIGLER: 8
- CB_YONETMELIK: 6
- CB_KARARNAME: 5
- KHK: 5
- MULGA: 5
- CB_GENELGE: 4
- TUZUK: 4

## Weak Family Mechanisms
- right-document wrong-article/span: 41
- wrong-family retrieval: 8
- right-family wrong-document: 6
- temporal_miss: 3
- generation overreach: 2
- retrieval miss: 1

## Worst Failure Examples
- MULGA-02: expected=MULGA, claimed=YONETMELIK, mechanism=temporal_miss, post_top=KKY `33899:33899:m1:f0:from2019-10-18:to9999-12-31`
- MULGA-03: expected=MULGA, claimed=TUZUK, mechanism=wrong-family retrieval, post_top=TUZUK `20135150:20135150:m90:f0:from1900-01-01:to9999-12-31`
- KANUN-04: expected=KANUN, claimed=TEBLIGLER, mechanism=wrong-family retrieval, post_top=TEBLIGLER `15677:15677:m1:f0:from2011-12-29:to9999-12-31`
- MULGA-04: expected=MULGA, claimed=KHK, mechanism=wrong-family retrieval, post_top=KANUN `555:555:m18:f0:from1995-06-27:to9999-12-31`
- CBG-04: expected=CB_GENELGE, claimed=CB_GENELGE, mechanism=right-family wrong-document, post_top=CB_GENELGE `3:3:m0:f0:from2023-01-28:to9999-12-31`
- TUZUK-04: expected=TUZUK, claimed=TUZUK, mechanism=right-family wrong-document, post_top=TUZUK `315481:315481:m626:f0:from1900-01-01:to9999-12-31`
- TEB-01: expected=TEBLIGLER, claimed=TEBLIGLER, mechanism=right-family wrong-document, post_top=TEBLIGLER `44999:44999:m0:f0:from2026-01-22:to9999-12-31`
- CBG-01: expected=CB_GENELGE, claimed=CB_GENELGE, mechanism=right-family wrong-document, post_top=CB_GENELGE `14:14:m0:f0:from1900-01-01:to9999-12-31`
- CBG-02: expected=CB_GENELGE, claimed=CB_GENELGE, mechanism=right-family wrong-document, post_top=CB_GENELGE `29:29:m0:f0:from2019-12-24:to9999-12-31`
- CBG-03: expected=CB_GENELGE, claimed=CB_GENELGE, mechanism=right-family wrong-document, post_top=CB_GENELGE `18:18:m0:f0:from2022-12-03:to9999-12-31`
- KANUN-18: expected=KANUN, claimed=KANUN, mechanism=right-family wrong-document, post_top=KANUN `TBK:6098:m424:f0:from2011-02-04:to9999-12-31`
- TEB-06: expected=TEBLIGLER, claimed=TEBLIGLER, mechanism=right-family wrong-document, post_top=TEBLIGLER `16558:16558:m11:f0:from2012-08-29:to9999-12-31`
- TUZUK-05: expected=TUZUK, claimed=TUZUK, mechanism=right-family wrong-document, post_top=TUZUK `315481:315481:m0:f0:from1900-01-01:to9999-12-31`
- KANUN-02: expected=KANUN, claimed=KANUN, mechanism=right-family wrong-document, post_top=KANUN `TBK:6098:m398:f0:from2011-02-04:to9999-12-31`
- YON-06: expected=YONETMELIK, claimed=YONETMELIK, mechanism=retrieval miss, post_top=KKY `10128:10128:m3:f0:from1982-08-03:to9999-12-31`
- MULGA-05: expected=MULGA, claimed=KANUN, mechanism=temporal_miss, post_top=KANUN `6585:6585:m25:f0:from1900-01-01:to9999-12-31`
- MULGA-01: expected=MULGA, claimed=UY, mechanism=temporal_miss, post_top=UY `34263:34263:m31:f0:from2020-02-10:to9999-12-31`
- YON-08: expected=YONETMELIK, claimed=UY, mechanism=wrong-family retrieval, post_top=UY `24445:24445:m21:f0:from2018-03-07:to9999-12-31`
- CBY-04: expected=CB_YONETMELIK, claimed=CB_KARARNAME, mechanism=wrong-family retrieval, post_top=CB_KARARNAME `11:11:m9:f0:from2018-07-16:to9999-12-31`
- YON-05: expected=YONETMELIK, claimed=KANUN, mechanism=wrong-family retrieval, post_top=KANUN `3194:3194:m18:f0:from1900-01-01:to9999-12-31`

## Phase 3 Routing Implications
- Wrong-family retrieval and right-family wrong-document clusters should be handled before generation by source-family prior, identifier/title lexical boosts, and issuer-aware tie-breakers.
- Generation overreach rows need a post-generation evidence/source consistency gate rather than prompt-only fixes.
- Temporal miss rows require active/repealed state to be propagated into evidence selection and answer contract confidence.
