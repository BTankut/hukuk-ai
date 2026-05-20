# FAZ18 RC-G vs RC-J Control Authority Summary

- family_count = `3`
- control_pair_runtime_error_count = `0`
- control_pair_authority_match = `false`
- control_pair_breach_in_f0_f12 = `false`
- family_metric_delta_zero = `true`
- wp3_pass = `false`

| family | pass | mismatch_count | runtime_error_count | family_metric_delta_zero | mismatch_stage_histogram |
| --- | --- | --- | --- | --- | --- |
| faz1-50 | False | 1 | 0 | True | {'final_answer_payload_hash': 1} |
| v2-95 | True | 0 | 0 | True | {} |
| v3-170 | False | 0 | 0 | True | {} |

## faz1-50 failure set

- `mismatch_count: expected=0 actual=1`
- `response_envelope_hash_mismatch_count: expected=0 actual=1`

## v3-170 failure set

- `mismatch_count: expected=6 actual=0`
- `final_mode_mapping_hash_mismatch_count: expected=6 actual=0`
- `blocked_reason_set_mismatch_count: expected=6 actual=0`
- `response_envelope_hash_mismatch_count: expected=6 actual=0`
