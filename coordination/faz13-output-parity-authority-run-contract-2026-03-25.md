# FAZ13 Output Parity Authority Run Contract

Tarih: 2026-03-25

`faz1-50` ve `v2-95` authoritative recapture aşağıdaki sabit forensic runtime contract ile yürütülür:

- `family_serial_execution = true`
- `ordinal_order_preserved = true`
- `single_worker = true`
- `single_process_per_candidate_family = true`
- `process_reuse_between_rc_g_and_rc_j = false`
- `session_namespace_isolated = true`
- `cache_namespace_isolated = true`
- `family_interleave = false`
- `release_controls_bind = false`
- `projection_order_frozen = true`
- `parity_instrumentation_only = true`

`v3-170` için ek kilit:

- yeni upstream authority toplama = `forbidden`
- replay basis = `FAZ11 authority input`
- frozen upstream mismatch alanları = `normalized_request_hash`, `model_request_payload_hash`, `generation_contract_hash`, `preprojection_hash`, `raw_answer_hash`
