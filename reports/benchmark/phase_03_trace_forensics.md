# Phase 3 Retrieval Trace Forensics

- source_run_dir: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260421T134133Z_phase2_answer_contract_rerun`
- rows_analyzed: 100
- failing_rows_with_failure_classes: 97
- weak_family_failing_rows: 62

## Dominant Failure Mechanisms
- right-document wrong-article/span: 32 (33.0%)
- evidence insufficiency: 21 (21.6%)
- wrong-family retrieval: 16 (16.5%)
- generation overreach: 15 (15.5%)
- right-family wrong-document: 8 (8.2%)
- temporal_miss: 5 (5.2%)

## Failure Classes
- missing_required_content_signal: 97
- partial_grounding_only: 97
- unsupported_confident_claim: 62
- hallucinated_identifier: 44
- wrong_family: 36
- missing_gold_document_signal: 22
- wrong_document: 22
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
- MULGA: 5
- CB_GENELGE: 4
- KHK: 4
- TUZUK: 4

## Weak Family Mechanisms
- right-document wrong-article/span: 18
- wrong-family retrieval: 15
- generation overreach: 11
- evidence insufficiency: 9
- temporal_miss: 5
- right-family wrong-document: 4

## Worst Failure Examples
- MULGA-03: expected=MULGA, claimed=TUZUK, mechanism=temporal_miss, post_top=TUZUK `20135150:20135150:m90:f0:from1900-01-01:to9999-12-31`
- CBKAR-03: expected=CB_KARAR, claimed=KKY, mechanism=wrong-family retrieval, post_top=KKY `4396:4396:m19:f0:from2003-08-20:to9999-12-31`
- CBKAR-08: expected=CB_KARAR, claimed=MULGA, mechanism=wrong-family retrieval, post_top=MULGA `6763:6763:m12:f0:from1900-01-01:to1900-01-01`
- CBY-03: expected=CB_YONETMELIK, claimed=KANUN, mechanism=wrong-family retrieval, post_top=KANUN `TBK:6098:m0:f0:from2011-02-04:to9999-12-31`
- MULGA-01: expected=MULGA, claimed=KKY, mechanism=temporal_miss, post_top=KKY `16532:16532:m18:f0:from2012-08-18:to9999-12-31`
- MULGA-04: expected=MULGA, claimed=KANUN, mechanism=temporal_miss, post_top=KANUN `551:551:m174:f0:from1995-06-27:to9999-12-31`
- MULGA-05: expected=MULGA, claimed=KANUN, mechanism=temporal_miss, post_top=KANUN `TBK:6098:m0:f0:from2011-02-04:to9999-12-31`
- CBG-01: expected=CB_GENELGE, claimed=KKY, mechanism=wrong-family retrieval, post_top=KKY `10647:10647:m5:f0:from2006-09-15:to9999-12-31`
- CBG-03: expected=CB_GENELGE, claimed=KKY, mechanism=generation overreach, post_top=KKY `15614:15614:m15:f0:from2011-12-17:to9999-12-31`
- CBKAR-04: expected=CB_KARAR, claimed=KANUN, mechanism=wrong-family retrieval, post_top=KANUN `127:127:m4:f0:from2023-03-03:to9999-12-31`
- CBKAR-05: expected=CB_KARAR, claimed=TEBLIGLER, mechanism=wrong-family retrieval, post_top=TEBLIGLER `11990:11990:m8:f0:from2008-02-28:to9999-12-31`
- CBY-02: expected=CB_YONETMELIK, claimed=KKY, mechanism=wrong-family retrieval, post_top=KKY `18812:18812:m220:f0:from2013-09-07:to9999-12-31`
- CBY-05: expected=CB_YONETMELIK, claimed=CB_GENELGE, mechanism=wrong-family retrieval, post_top=CB_GENELGE `25:25:m0:f0:from2019-11-12:to9999-12-31`
- TUZUK-05: expected=TUZUK, claimed=UY, mechanism=generation overreach, post_top=UY `34649:34649:m44:f0:from2020-06-28:to9999-12-31`
- YON-06: expected=YONETMELIK, claimed=UY, mechanism=generation overreach, post_top=UY `29029:29029:m7:f0:from2018-12-03:to9999-12-31`
- CBG-04: expected=CB_GENELGE, claimed=CB_GENELGE, mechanism=right-family wrong-document, post_top=CB_GENELGE `5:5:m0:f0:from1900-01-01:to9999-12-31`
- CBY-01: expected=CB_YONETMELIK, claimed=CB_YONETMELIK, mechanism=right-family wrong-document, post_top=CB_YONETMELIK `5434:5434:m3:f0:from2022-04-19:to9999-12-31`
- KANUN-04: expected=KANUN, claimed=KANUN, mechanism=right-family wrong-document, post_top=KANUN `KVKK:6698:m9:f0:from2016-04-07:to9999-12-31`
- KANUN-18: expected=KANUN, claimed=KANUN, mechanism=right-family wrong-document, post_top=KANUN `IK:4857:m56:f0:from1900-01-01:to9999-12-31`
- KANUN-21: expected=KANUN, claimed=KANUN, mechanism=right-family wrong-document, post_top=KANUN `6325:6325:m18:f0:from2012-06-22:to9999-12-31`

## Phase 3 Routing Implications
- Wrong-family retrieval and right-family wrong-document clusters should be handled before generation by source-family prior, identifier/title lexical boosts, and issuer-aware tie-breakers.
- Generation overreach rows need a post-generation evidence/source consistency gate rather than prompt-only fixes.
- Temporal miss rows require active/repealed state to be propagated into evidence selection and answer contract confidence.
