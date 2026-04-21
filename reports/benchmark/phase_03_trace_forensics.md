# Phase 3 Retrieval Trace Forensics

- source_run_dir: `reports/benchmark/runs/20260421T174105Z_phase3_retrieval_routing_final_v2`
- rows_analyzed: 100
- failing_rows_with_failure_classes: 98
- weak_family_failing_rows: 62

## Dominant Failure Mechanisms
- right-document wrong-article/span: 36 (36.7%)
- evidence insufficiency: 16 (16.3%)
- generation overreach: 16 (16.3%)
- wrong-family retrieval: 13 (13.3%)
- right-family wrong-document: 12 (12.2%)
- temporal_miss: 5 (5.1%)

## Failure Classes
- missing_required_content_signal: 98
- partial_grounding_only: 98
- unsupported_confident_claim: 49
- hallucinated_identifier: 46
- wrong_family: 34
- missing_gold_document_signal: 23
- wrong_document: 23
- repealed_source_used_as_active: 5
- wrong_article: 3
- auto_fail_triggered: 1

## Failing Rows by Expected Family
- KANUN: 21
- KKY: 11
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
- right-document wrong-article/span: 19
- wrong-family retrieval: 12
- generation overreach: 11
- right-family wrong-document: 8
- evidence insufficiency: 7
- temporal_miss: 5

## Worst Failure Examples
- MULGA-03: expected=MULGA, claimed=TUZUK, mechanism=temporal_miss, post_top=TUZUK `20135150:20135150:m90:f0:from1900-01-01:to9999-12-31`
- CBKAR-03: expected=CB_KARAR, claimed=YONETMELIK, mechanism=wrong-family retrieval, post_top=YONETMELIK `20047114:20047114:m0:f0:from2004-04-21:to9999-12-31`
- CBKAR-08: expected=CB_KARAR, claimed=MULGA, mechanism=wrong-family retrieval, post_top=MULGA `6763:6763:m20:f0:from1900-01-01:to1900-01-01`
- CBY-03: expected=CB_YONETMELIK, claimed=KANUN, mechanism=wrong-family retrieval, post_top=KANUN `TBK:6098:m0:f0:from2011-02-04:to9999-12-31`
- MULGA-01: expected=MULGA, claimed=UY, mechanism=temporal_miss, post_top=UY `15308:15308:m21:f0:from2011-09-18:to9999-12-31`
- MULGA-04: expected=MULGA, claimed=KHK, mechanism=temporal_miss, post_top=KANUN `551:551:m174:f0:from1995-06-27:to9999-12-31`
- MULGA-05: expected=MULGA, claimed=KANUN, mechanism=temporal_miss, post_top=KANUN `TBK:6098:m0:f0:from2011-02-04:to9999-12-31`
- CBY-01: expected=CB_YONETMELIK, claimed=YONETMELIK, mechanism=wrong-family retrieval, post_top=YONETMELIK `20146289:20146289:m15:f0:from1900-01-01:to9999-12-31`
- CBY-02: expected=CB_YONETMELIK, claimed=KKY, mechanism=wrong-family retrieval, post_top=KKY `18812:18812:m220:f0:from2013-09-07:to9999-12-31`
- TUZUK-05: expected=TUZUK, claimed=UY, mechanism=generation overreach, post_top=UY `34766:34766:m3:f0:from2020-08-16:to9999-12-31`
- YON-06: expected=YONETMELIK, claimed=UY, mechanism=generation overreach, post_top=UY `29029:29029:m7:f0:from2018-12-03:to9999-12-31`
- CBKAR-04: expected=CB_KARAR, claimed=CB_GENELGE, mechanism=generation overreach, post_top=CB_GENELGE `15:15:m0:f0:from2022-09-14:to9999-12-31`
- CBG-04: expected=CB_GENELGE, claimed=CB_GENELGE, mechanism=right-family wrong-document, post_top=CB_GENELGE `5:5:m0:f0:from1900-01-01:to9999-12-31`
- CBG-01: expected=CB_GENELGE, claimed=CB_GENELGE, mechanism=right-family wrong-document, post_top=CB_GENELGE `14:14:m0:f0:from1900-01-01:to9999-12-31`
- CBG-03: expected=CB_GENELGE, claimed=CB_GENELGE, mechanism=right-family wrong-document, post_top=CB_GENELGE `18:18:m0:f0:from2022-12-03:to9999-12-31`
- KANUN-04: expected=KANUN, claimed=KANUN, mechanism=right-family wrong-document, post_top=KANUN `KVKK:6698:m9:f0:from2016-04-07:to9999-12-31`
- KANUN-18: expected=KANUN, claimed=KANUN, mechanism=right-family wrong-document, post_top=KANUN `IK:4857:m56:f0:from1900-01-01:to9999-12-31`
- KANUN-21: expected=KANUN, claimed=KANUN, mechanism=right-family wrong-document, post_top=KANUN `6325:6325:m18:f0:from2012-06-22:to9999-12-31`
- KKY-10: expected=KKY, claimed=KKY, mechanism=right-family wrong-document, post_top=KKY `13540:13540:m4:f0:from2009-11-12:to9999-12-31`
- YON-02: expected=YONETMELIK, claimed=YONETMELIK, mechanism=right-family wrong-document, post_top=YONETMELIK `20146282:20146282:m54:f0:from2014-05-09:to9999-12-31`

## Phase 3 Routing Implications
- Wrong-family retrieval and right-family wrong-document clusters should be handled before generation by source-family prior, identifier/title lexical boosts, and issuer-aware tie-breakers.
- Generation overreach rows need a post-generation evidence/source consistency gate rather than prompt-only fixes.
- Temporal miss rows require active/repealed state to be propagated into evidence selection and answer contract confidence.
