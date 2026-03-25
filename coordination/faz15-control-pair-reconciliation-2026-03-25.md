# FAZ15 Control Pair Reconciliation

- control_pair_authority_match = `false`
- control_pair_breach_in_f0_f12 = `false`

## faz1-50

- durum = `fail`
- `mismatch_count: expected=0 actual=1`

## v2-95

- durum = `pass`

## v3-170

- durum = `fail`
- `mismatch_count: expected=6 actual=0`
- `final_mode_mapping_hash_mismatch_count: expected=6 actual=0`
- `blocked_reason_set_mismatch_count: expected=6 actual=0`
- `response_envelope_hash_mismatch_count: expected=6 actual=0`
