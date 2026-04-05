# RC-S Full Corpus Integrated Requalification Gate Raporu 2026-04-05

## Official Decision

- decision = `NO-GO - RC-S Full-Corpus Integrated Requalification Gate`

## Gate Result

- accepted_expanded_source_set = `[TMK core corpus, TCK, HMK, CMK, TTK, İK]`
- remaining_unexecuted_source_class_count = `0`
- next_source_class = `NONE`
- total_eval_row_count = `48`
- reject_count = `24`
- runtime_error_count = `16`
- unexplained_count = `0`
- cross_law_confusion_count = `0`
- wrong_primary_source_count = `0`

## PASS Criteria Contrast

| criterion | required | observed | result |
| --- | --- | --- | --- |
| accepted full source set preserved | yes | yes | PASS |
| remaining_unexecuted_source_class_count | 0 | 0 | PASS |
| next_source_class | NONE | NONE | PASS |
| all 6 source classes covered | yes | yes | PASS |
| reject_count | 0 | 24 | FAIL |
| runtime_error_count | 0 | 16 | FAIL |
| unexplained_count | 0 | 0 | PASS |
| cross_law_confusion_count | 0 | 0 | PASS |
| wrong_primary_source_count | 0 | 0 | PASS |
| zero-delta flags all false | yes | yes | PASS |

## Decisive Findings

- HMK was the only source class that returned cited, usable, source-correct answers across all 8 rows.
- TMK core corpus, TCK, and TTK returned supported questions as refusal / empty-answer surfaces, producing `24` rejects.
- CMK and İK produced `16` runtime errors through HTTP 500 context-length overflow.
- Because PASS requires both `reject_count = 0` and `runtime_error_count = 0`, the gate cannot close.

## Freeze After Decision

- RC-R freeze preserved = `true`
- accepted_expanded_source_set preserved = `true`
- new_source_execution_opened = `false`
- new_candidate_opened = `false`

## Next State

- gate_status = `open`
- remediation_scope = `integrated requalification eksikleri`
- next_official_work = `new talimat required`
