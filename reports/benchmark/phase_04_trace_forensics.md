# Phase 3 Retrieval Trace Forensics

- source_run_dir: `reports/benchmark/runs/20260421T211914Z_phase4_verification_first_final_v4`
- rows_analyzed: 100
- failing_rows_with_failure_classes: 97
- weak_family_failing_rows: 62

## Dominant Failure Mechanisms
- right-document wrong-article/span: 30 (30.9%)
- generation overreach: 22 (22.7%)
- evidence insufficiency: 15 (15.5%)
- right-family wrong-document: 13 (13.4%)
- wrong-family retrieval: 12 (12.4%)
- temporal_miss: 5 (5.2%)

## Failure Classes
- missing_required_content_signal: 97
- partial_grounding_only: 97
- hallucinated_identifier: 51
- wrong_family: 38
- unsupported_confident_claim: 33
- missing_gold_document_signal: 22
- wrong_document: 22
- repealed_source_used_as_active: 5
- wrong_article: 3
- auto_fail_triggered: 2

## Failing Rows by Expected Family
- KANUN: 21
- KKY: 11
- UY: 10
- YONETMELIK: 10
- CB_KARAR: 8
- TEBLIGLER: 8
- CB_KARARNAME: 6
- CB_YONETMELIK: 6
- MULGA: 5
- CB_GENELGE: 4
- KHK: 4
- TUZUK: 4

## Weak Family Mechanisms
- right-document wrong-article/span: 15
- generation overreach: 14
- wrong-family retrieval: 11
- right-family wrong-document: 10
- evidence insufficiency: 7
- temporal_miss: 5

## Worst Failure Examples
- KANUN-18: expected=KANUN, claimed=KANUN, mechanism=evidence insufficiency, post_top=KANUN `TBK:6098:m425:f0:from2011-02-04:to9999-12-31`
- MULGA-03: expected=MULGA, claimed=TUZUK, mechanism=temporal_miss, post_top=TUZUK `20135150:20135150:m90:f0:from1900-01-01:to9999-12-31`
- CBKAR-08: expected=CB_KARAR, claimed=MULGA, mechanism=wrong-family retrieval, post_top=MULGA `6763:6763:m20:f0:from1900-01-01:to1900-01-01`
- MULGA-04: expected=MULGA, claimed=KHK, mechanism=temporal_miss, post_top=KANUN `551:551:m174:f0:from1995-06-27:to9999-12-31`
- CBY-01: expected=CB_YONETMELIK, claimed=YONETMELIK, mechanism=wrong-family retrieval, post_top=YONETMELIK `20146289:20146289:m15:f0:from1900-01-01:to9999-12-31`
- CBY-02: expected=CB_YONETMELIK, claimed=KKY, mechanism=generation overreach, post_top=KKY `39610:39610:m6:f0:from2022-06-29:to9999-12-31`
- KANUN-06: expected=KANUN, claimed=MULGA, mechanism=generation overreach, post_top=MULGA `6762:6762:m511:f0:from1956-07-09:to1900-01-01`
- UY-07: expected=UY, claimed=YONETMELIK, mechanism=wrong-family retrieval, post_top=YONETMELIK `836622:836622:m12:f0:from1983-07-02:to9999-12-31`
- YON-02: expected=YONETMELIK, claimed=CB_YONETMELIK, mechanism=generation overreach, post_top=CB_YONETMELIK `9:9:m4:f0:from2018-08-03:to9999-12-31`
- YON-06: expected=YONETMELIK, claimed=KKY, mechanism=generation overreach, post_top=KKY `34208:34208:m6:f0:from2020-01-21:to9999-12-31`
- CBKAR-04: expected=CB_KARAR, claimed=CB_GENELGE, mechanism=generation overreach, post_top=CB_GENELGE `15:15:m0:f0:from2022-09-14:to9999-12-31`
- CBG-04: expected=CB_GENELGE, claimed=CB_GENELGE, mechanism=right-family wrong-document, post_top=CB_GENELGE `18:18:m0:f0:from2022-12-03:to9999-12-31`
- TEB-04: expected=TEBLIGLER, claimed=TEBLIGLER, mechanism=right-family wrong-document, post_top=TEBLIGLER `34913:34913:m0:f0:from2020-10-07:to9999-12-31`
- CBG-01: expected=CB_GENELGE, claimed=CB_GENELGE, mechanism=right-family wrong-document, post_top=CB_GENELGE `14:14:m0:f0:from1900-01-01:to9999-12-31`
- CBG-03: expected=CB_GENELGE, claimed=CB_GENELGE, mechanism=right-family wrong-document, post_top=CB_GENELGE `18:18:m0:f0:from2022-12-03:to9999-12-31`
- CBKAR-06: expected=CB_KARAR, claimed=CB_KARAR, mechanism=right-family wrong-document, post_top=CB_KARAR `767:767:m2:f0:from2019-02-18:to9999-12-31`
- KANUN-21: expected=KANUN, claimed=KANUN, mechanism=right-family wrong-document, post_top=KANUN `6325:6325:m18:f0:from2012-06-22:to9999-12-31`
- KKY-10: expected=KKY, claimed=KKY, mechanism=right-family wrong-document, post_top=KKY `13540:13540:m4:f0:from2009-11-12:to9999-12-31`
- TUZUK-05: expected=TUZUK, claimed=TUZUK, mechanism=right-family wrong-document, post_top=TUZUK `315481:315481:m0:f0:from1900-01-01:to9999-12-31`
- UY-10: expected=UY, claimed=UY, mechanism=right-family wrong-document, post_top=UY `13219:13219:m5:f0:from2009-07-14:to9999-12-31`

## Phase 3 Routing Implications
- Wrong-family retrieval and right-family wrong-document clusters should be handled before generation by source-family prior, identifier/title lexical boosts, and issuer-aware tie-breakers.
- Generation overreach rows need a post-generation evidence/source consistency gate rather than prompt-only fixes.
- Temporal miss rows require active/repealed state to be propagated into evidence selection and answer contract confidence.
