# FAZ19 Current Authority Reference Contrast

- historical_authority_restored = `false`
- current_instability_snapshot_confirmed = `false`
- current_authority_contract_breach = `false`

## Historical Contrast

| family | match | mismatched_fields | stable_mismatch_count | reference_mismatch_count |
| --- | --- | --- | --- | --- |
| faz1-50 | True | [] | 0 | 0 |
| v2-95 | True | [] | 0 | 0 |
| v3-170 | False | ['mismatch_count', 'mismatch_stage_histogram', 'mismatch_question_ids', 'mismatch_ordinals'] | 0 | 6 |

## Current Instability Snapshot Contrast

| family | match | mismatched_fields | stable_mismatch_count | reference_mismatch_count |
| --- | --- | --- | --- | --- |
| faz1-50 | False | ['mismatch_count', 'mismatch_stage_histogram', 'mismatch_question_ids', 'mismatch_ordinals'] | 0 | 1 |
| v2-95 | True | [] | 0 | 0 |
| v3-170 | True | [] | 0 | 0 |
