# Phase 3 Retrieval Trace Forensics

- source_run_dir: `reports/benchmark/runs/20260422T204628Z_phase11_full`
- rows_analyzed: 100
- failing_rows_with_failure_classes: 97
- weak_family_failing_rows: 61

## Canonical Metric Counts
- right_document_wrong_article_or_span: 51
- missing_required_content_signal: 97
- partial_grounding_only: 97
- minimum_answer_facts_present_count: 71
- avg_required_fact_coverage_score: 0.943
- selected_article_equals_claimed_article_count: 63

## Dominant Failure Mechanisms
- right-document wrong-article/span: 51 (52.6%)
- generation overreach: 18 (18.6%)
- wrong-family retrieval: 13 (13.4%)
- right-family wrong-document: 9 (9.3%)
- temporal_miss: 5 (5.2%)
- retrieval miss: 1 (1.0%)

## Failure Classes
- missing_required_content_signal: 97
- partial_grounding_only: 97
- wrong_family: 35
- hallucinated_identifier: 32
- missing_gold_document_signal: 15
- wrong_document: 15
- unsupported_confident_claim: 6
- repealed_source_used_as_active: 5
- wrong_article: 3
- auto_fail_triggered: 2

## Article Alignment
- exact: 53
- none: 28
- title_only: 14
- neighbor: 5

## Query Article Alignment
- unknown: 87
- title_only: 13

## Failing Rows by Expected Family
- KANUN: 21
- KKY: 10
- UY: 10
- YONETMELIK: 10
- CB_KARAR: 8
- TEBLIGLER: 8
- CB_KARARNAME: 6
- CB_YONETMELIK: 6
- KHK: 5
- MULGA: 5
- CB_GENELGE: 4
- TUZUK: 4

## Weak Family Mechanisms
- right-document wrong-article/span: 26
- wrong-family retrieval: 12
- generation overreach: 9
- right-family wrong-document: 8
- temporal_miss: 5
- retrieval miss: 1

## Worst Failure Examples
- KANUN-01: expected=KANUN, claimed=TEBLIGLER, mechanism=generation overreach, post_top=TEBLIGLER `24083:24083:m20:f0:from2017-11-11:to9999-12-31`
- MULGA-03: expected=MULGA, claimed=TUZUK, mechanism=temporal_miss, post_top=TUZUK `20135150:20135150:m90:f0:from1900-01-01:to9999-12-31`
- CBY-05: expected=CB_YONETMELIK, claimed=CB_GENELGE, mechanism=wrong-family retrieval, post_top=CB_GENELGE `8:8:m0:f0:from2022-06-07:to9999-12-31`
- KANUN-06: expected=KANUN, claimed=MULGA, mechanism=generation overreach, post_top=MULGA `6762:6762:m511:f0:from1956-07-09:to1900-01-01`
- UY-07: expected=UY, claimed=KANUN, mechanism=wrong-family retrieval, post_top=KANUN `KVKK:6698:m9:f0:from2016-04-07:to9999-12-31`
- YON-02: expected=YONETMELIK, claimed=CB_YONETMELIK, mechanism=generation overreach, post_top=CB_YONETMELIK `9:9:m4:f0:from2018-08-03:to9999-12-31`
- YON-06: expected=YONETMELIK, claimed=KKY, mechanism=generation overreach, post_top=KKY `34208:34208:m6:f0:from2020-01-21:to9999-12-31`
- CBG-04: expected=CB_GENELGE, claimed=CB_GENELGE, mechanism=right-family wrong-document, post_top=CB_GENELGE `18:18:m0:f0:from2022-12-03:to9999-12-31`
- TEB-04: expected=TEBLIGLER, claimed=TEBLIGLER, mechanism=right-family wrong-document, post_top=TEBLIGLER `34913:34913:m0:f0:from2020-10-07:to9999-12-31`
- CBG-01: expected=CB_GENELGE, claimed=CB_GENELGE, mechanism=right-family wrong-document, post_top=CB_GENELGE `14:14:m0:f0:from1900-01-01:to9999-12-31`
- CBG-02: expected=CB_GENELGE, claimed=CB_GENELGE, mechanism=right-family wrong-document, post_top=CB_GENELGE `28:28:m0:f0:from2019-12-11:to9999-12-31`
- CBG-03: expected=CB_GENELGE, claimed=CB_GENELGE, mechanism=right-family wrong-document, post_top=CB_GENELGE `18:18:m0:f0:from2022-12-03:to9999-12-31`
- CBKAR-04: expected=CB_KARAR, claimed=CB_KARAR, mechanism=retrieval miss, post_top=CB_YONETMELIK `5997:5997:m9:f0:from2022-09-02:to9999-12-31`
- KKY-02: expected=KKY, claimed=KKY, mechanism=right-family wrong-document, post_top=KKY `10746:10746:m4:f0:from2006-11-01:to9999-12-31`
- KKY-10: expected=KKY, claimed=KKY, mechanism=right-family wrong-document, post_top=KKY `13540:13540:m4:f0:from2009-11-12:to9999-12-31`
- TUZUK-05: expected=TUZUK, claimed=TUZUK, mechanism=right-family wrong-document, post_top=TUZUK `315481:315481:m0:f0:from1900-01-01:to9999-12-31`
- MULGA-01: expected=MULGA, claimed=UY, mechanism=temporal_miss, post_top=UY `23092:23092:m36:f0:from2016-12-06:to9999-12-31`
- UY-10: expected=UY, claimed=UY, mechanism=right-family wrong-document, post_top=UY `22946:22946:m19:f0:from2016-10-17:to9999-12-31`
- TUZUK-04: expected=TUZUK, claimed=UY, mechanism=generation overreach, post_top=UY `19146:19146:m6:f0:from2013-12-20:to9999-12-31`
- CBKAR-01: expected=CB_KARAR, claimed=TEBLIGLER, mechanism=wrong-family retrieval, post_top=TEBLIGLER `42854:42854:m0:f0:from2025-12-31:to9999-12-31`

## Phase 3 Routing Implications
- Wrong-family retrieval and right-family wrong-document clusters should be handled before generation by source-family prior, identifier/title lexical boosts, and issuer-aware tie-breakers.
- Generation overreach rows need a post-generation evidence/source consistency gate rather than prompt-only fixes.
- Temporal miss rows require active/repealed state to be propagated into evidence selection and answer contract confidence.
