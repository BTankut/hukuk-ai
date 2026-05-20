# FAZ20 Contract Conditioned Replay FAZ13

- replay_name = `faz13`
- reference_name = `faz13`
- runtime_error_count = `0`
- family_metric_delta_zero = `true`
- breach_in_h0_h9 = `false`
- breach_in_h10_h11 = `true`
- reference_match = `false`
- reference_mismatch_count = `1`
- first_divergence_stage = `H10`
- primary_reason = `authority_summary_materialization_delta`
- unexplained_count = `0`

## Family Summary

| family | mismatch_count | runtime_error_count | family_metric_delta_zero | mismatch_stage_histogram | mismatch_question_ids |
| --- | --- | --- | --- | --- | --- |
| faz1-50 | 0 | 0 | True | {} | [] |
| v2-95 | 0 | 0 | True | {} | [] |
| v3-170 | 0 | 0 | True | {} | [] |

## Reference Contrast

| family | match | mismatched_fields | breach_in_h10_h11 |
| --- | --- | --- | --- |
| faz1-50 | True | [] | ['H10', 'H11'] |
| v2-95 | True | [] | ['H10', 'H11'] |
| v3-170 | False | ['first_divergence_stage_set', 'mismatch_count', 'mismatch_ordinals', 'mismatch_question_ids', 'mismatch_stage_histogram', 'reason_histogram'] | ['H10', 'H11'] |
