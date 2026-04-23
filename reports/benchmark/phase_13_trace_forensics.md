# Phase 3 Retrieval Trace Forensics

- source_run_dir: `reports/benchmark/runs/20260423T124900Z_phase13_full`
- rows_analyzed: 100
- failing_rows_with_failure_classes: 96
- weak_family_failing_rows: 61

## Canonical Metric Counts
- right_document_wrong_article_or_span: 57
- missing_required_content_signal: 96
- partial_grounding_only: 96
- minimum_answer_facts_present_count: 81
- avg_required_fact_coverage_score: 0.859
- selected_article_equals_claimed_article_count: 55

## Dominant Failure Mechanisms
- right-document wrong-article/span: 57 (59.4%)
- wrong-family retrieval: 14 (14.6%)
- generation overreach: 14 (14.6%)
- right-family wrong-document: 8 (8.3%)
- temporal_miss: 3 (3.1%)

## Failure Classes
- missing_required_content_signal: 96
- partial_grounding_only: 96
- wrong_family: 31
- hallucinated_identifier: 24
- missing_gold_document_signal: 18
- wrong_document: 18
- unsupported_confident_claim: 3
- repealed_source_used_as_active: 3
- wrong_article: 2
- auto_fail_triggered: 2

## Article Alignment
- exact: 45
- none: 34
- title_only: 16
- neighbor: 5

## Query Article Alignment
- unknown: 86
- title_only: 14

## Failing Rows by Expected Family
- KANUN: 21
- KKY: 11
- YONETMELIK: 10
- UY: 9
- CB_KARAR: 8
- TEBLIGLER: 8
- CB_KARARNAME: 6
- CB_YONETMELIK: 6
- MULGA: 5
- CB_GENELGE: 4
- KHK: 4
- TUZUK: 4

## Weak Family Mechanisms
- right-document wrong-article/span: 31
- wrong-family retrieval: 11
- generation overreach: 10
- right-family wrong-document: 6
- temporal_miss: 3

## Worst Failure Examples
- MULGA-03: expected=MULGA, claimed=MULGA, mechanism=right-document wrong-article/span, post_top=TUZUK `20135150:20135150:m90:f0:from1900-01-01:to9999-12-31`
- TEB-04: expected=TEBLIGLER, claimed=MULGA, mechanism=generation overreach, post_top=MULGA `KDVK:3065:m60:f0:from1900-01-01:to1900-01-01`
- CBKAR-08: expected=CB_KARAR, claimed=CB_KARARNAME, mechanism=generation overreach, post_top=CB_KARAR `10019:10019:m0:f0:from2025-07-01:to9999-12-31`
- KHK-03: expected=KHK, claimed=CB_KARARNAME, mechanism=wrong-family retrieval, post_top=CB_KARARNAME `34:34:m16:f0:from2019-05-02:to9999-12-31`
- MULGA-01: expected=MULGA, claimed=UY, mechanism=temporal_miss, post_top=UY `34263:34263:m31:f0:from2020-02-10:to9999-12-31`
- CBKAR-06: expected=CB_KARAR, claimed=CB_GENELGE, mechanism=wrong-family retrieval, post_top=CB_GENELGE `15:15:m0:f0:from2022-09-14:to9999-12-31`
- KANUN-04: expected=KANUN, claimed=TEBLIGLER, mechanism=wrong-family retrieval, post_top=TEBLIGLER `15677:15677:m1:f0:from2011-12-29:to9999-12-31`
- KKY-02: expected=KKY, claimed=UY, mechanism=wrong-family retrieval, post_top=UY `19952:19952:m0:f0:from2014-08-07:to9999-12-31`
- KKY-09: expected=KKY, claimed=UY, mechanism=wrong-family retrieval, post_top=UY `28935:28935:m9:f0:from2018-11-04:to9999-12-31`
- YON-07: expected=YONETMELIK, claimed=UY, mechanism=wrong-family retrieval, post_top=UY `31497:31497:m2:f0:from2019-05-13:to9999-12-31`
- CBKAR-04: expected=CB_KARAR, claimed=CB_GENELGE, mechanism=wrong-family retrieval, post_top=CB_GENELGE `15:15:m0:f0:from2022-09-14:to9999-12-31`
- KKY-06: expected=KKY, claimed=UY, mechanism=wrong-family retrieval, post_top=UY `24477:24477:m0:f0:from2018-03-26:to9999-12-31`
- CBG-04: expected=CB_GENELGE, claimed=CB_GENELGE, mechanism=right-family wrong-document, post_top=CB_GENELGE `18:18:m0:f0:from2022-12-03:to9999-12-31`
- CBY-03: expected=CB_YONETMELIK, claimed=CB_YONETMELIK, mechanism=right-family wrong-document, post_top=CB_YONETMELIK `201811993:201811993:m8:f0:from2018-06-30:to9999-12-31`
- TUZUK-04: expected=TUZUK, claimed=TUZUK, mechanism=right-family wrong-document, post_top=TUZUK `315481:315481:m626:f0:from1900-01-01:to9999-12-31`
- CBG-01: expected=CB_GENELGE, claimed=CB_GENELGE, mechanism=right-family wrong-document, post_top=CB_GENELGE `14:14:m0:f0:from1900-01-01:to9999-12-31`
- CBG-02: expected=CB_GENELGE, claimed=CB_GENELGE, mechanism=right-family wrong-document, post_top=CB_GENELGE `29:29:m0:f0:from2019-12-24:to9999-12-31`
- CBG-03: expected=CB_GENELGE, claimed=CB_GENELGE, mechanism=right-family wrong-document, post_top=CB_GENELGE `18:18:m0:f0:from2022-12-03:to9999-12-31`
- TEB-06: expected=TEBLIGLER, claimed=TEBLIGLER, mechanism=right-family wrong-document, post_top=TEBLIGLER `16558:16558:m11:f0:from2012-08-29:to9999-12-31`
- TUZUK-05: expected=TUZUK, claimed=TUZUK, mechanism=right-family wrong-document, post_top=TUZUK `315481:315481:m0:f0:from1900-01-01:to9999-12-31`

## Phase 3 Routing Implications
- Wrong-family retrieval and right-family wrong-document clusters should be handled before generation by source-family prior, identifier/title lexical boosts, and issuer-aware tie-breakers.
- Generation overreach rows need a post-generation evidence/source consistency gate rather than prompt-only fixes.
- Temporal miss rows require active/repealed state to be propagated into evidence selection and answer contract confidence.
