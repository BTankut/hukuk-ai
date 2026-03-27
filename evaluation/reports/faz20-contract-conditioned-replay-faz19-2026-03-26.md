# FAZ20 Contract Conditioned Replay FAZ19

- replay_name = `faz19`
- reference_name = `faz19`
- runtime_error_count = `0`
- family_metric_delta_zero = `true`
- breach_in_h0_h9 = `false`
- breach_in_h10_h11 = `true`
- reference_match = `true`
- reference_mismatch_count = `0`
- first_divergence_stage = `H10`
- primary_reason = `stable_current_truth_canonical`
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
| v3-170 | True | [] | ['H10', 'H11'] |
