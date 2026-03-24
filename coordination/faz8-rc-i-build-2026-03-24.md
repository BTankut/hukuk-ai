# FAZ8 RC-I Build

Tarih: 2026-03-24

## Build Temeli

- base lane: `RC-G`
- candidate lane: `RC-I`
- answer_path_delta = `[]`
- retained release controls aktif
- parity trace aktif

## Witness Run

- reference report: `evaluation/reports/eval_faz8_rc_g_faz1_witness_20260324.json`
- candidate report: `evaluation/reports/eval_faz8_rc_i_faz1_witness_20260324.json`
- hash gate: `evaluation/reports/faz8-rc-i-preprojection-hash-gate-2026-03-24.md`
- parity witness: `evaluation/reports/faz8-rc-i-output-parity-witness-2026-03-24.md`

## Stage-Level Witness

`TBK-005`

- `raw_input_request`: ayni
- `normalized_request`: ayni
- `auth_session_trace_enriched_request`: farkli
  - beklenen fark: `auth_subject`
- `pre_answer_handler_payload`: ayni
- `raw_answer_object`: farkli
  - `RC-G` daha genis answer body ve `4` citation uretir
  - `RC-I` daralmis answer body ve `2` citation uretir

## Resmi Sonuc

- `preprojection_hash_mismatch_count = 1`
- `raw_answer_hash_mismatch = 1`
- `WP-4 = FAIL`
