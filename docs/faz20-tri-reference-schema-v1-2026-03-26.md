# FAZ20 Tri-Reference Schema v1

Normalized reference pack alanlari:
- `family_name`
- `candidate_pair`
- `mismatch_count`
- `runtime_error_count`
- `family_metric_delta_zero`
- `mismatch_stage_histogram`
- `mismatch_question_ids`
- `mismatch_ordinals`
- `first_divergence_stage_set`
- `reason_histogram`
- `authoritative_summary_hash`
- `reference_pack_hash`

Zorunlu kurallar:
- ek alan yok
- candidate pair sabit: `rc_g_vs_rc_j`
- referanslar yalniz `FAZ13`, `FAZ18`, `FAZ19`
