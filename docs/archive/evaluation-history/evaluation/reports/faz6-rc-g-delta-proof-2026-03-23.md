# FAZ 6 RC-G Delta Proof

- tracked_record_count: `108`
- changed_output_count: `100`
- beneficial_change_count: `34`
- harmful_change_count: `0`
- citation_omission_baseline: `45`
- citation_omission_rc_g: `27`
- citation_omission_reduction_rate: `40.0%`
- post_generation_primary_flip_baseline: `0`
- post_generation_primary_flip_rc_g: `0`
- overall_pass: `true`

## Current Reason Histogram

- `assembly_primary_miss`: `28`
- `canonical_normalization_mismatch`: `3`
- `citation_omission_with_correct_primary_present`: `27`
- `evaluator_alignment_mismatch`: `43`
- `guardrail_mode_drop`: `4`
- `retrieval_source_absent`: `3`

## Sample

- faz1-50 TBK-003: citation `False -> False`, correct_source `0.0000 -> 0.0000`, mode `refusal -> refusal`
- faz1-50 TBK-006: citation `True -> True`, correct_source `0.0000 -> 0.6667`, mode `answer -> answer`
- faz1-50 TBK-007: citation `True -> True`, correct_source `0.3333 -> 1.0000`, mode `answer -> answer`
- faz1-50 TBK-008: citation `True -> True`, correct_source `0.5000 -> 0.5000`, mode `answer -> answer`
- faz1-50 TBK-009: citation `True -> True`, correct_source `0.5000 -> 1.0000`, mode `answer -> answer`
- faz1-50 TBK-011: citation `False -> False`, correct_source `0.0000 -> 0.0000`, mode `refusal -> refusal`
- faz1-50 TBK-016: citation `True -> True`, correct_source `0.0000 -> 1.0000`, mode `answer -> answer`
- faz1-50 TBK-033: citation `True -> True`, correct_source `1.0000 -> 1.0000`, mode `answer -> answer`
- faz1-50 TBK-035: citation `True -> True`, correct_source `0.5000 -> 1.0000`, mode `answer -> answer`
- faz1-50 TBK-039: citation `False -> False`, correct_source `0.0000 -> 0.0000`, mode `refusal -> refusal`
- faz1-50 TBK-042: citation `True -> True`, correct_source `0.0000 -> 0.0000`, mode `answer -> answer`
- faz1-50 TBK-043: citation `True -> True`, correct_source `1.0000 -> 1.0000`, mode `answer -> answer`
- v2-95 HAL-003: citation `True -> True`, correct_source `0.6667 -> 1.0000`, mode `answer -> answer`
- v2-95 HAL-004: citation `True -> True`, correct_source `1.0000 -> 1.0000`, mode `answer -> answer`
- v2-95 HAL-005: citation `True -> True`, correct_source `1.0000 -> 1.0000`, mode `answer -> answer`
- v2-95 HAL-006: citation `True -> True`, correct_source `1.0000 -> 1.0000`, mode `answer -> answer`
- v2-95 HAL-007: citation `True -> True`, correct_source `1.0000 -> 1.0000`, mode `partial -> partial`
- v2-95 HAL-009: citation `True -> True`, correct_source `0.0000 -> 0.5000`, mode `answer -> answer`
- v2-95 TBK-051: citation `True -> True`, correct_source `0.0000 -> 0.0000`, mode `answer -> answer`
- v2-95 TBK-052: citation `True -> True`, correct_source `0.5000 -> 1.0000`, mode `answer -> answer`