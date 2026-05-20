# FAZ10 V3 Runtime Parity Taxonomy v1

Tarih: 2026-03-24

Yalniz kabul edilen reason kumesi:

- `raw_generation_nondeterminism`
- `process_reinit_dependency`
- `shared_runner_state_bleed`
- `post_payload_release_control_bleed`
- `request_order_accumulation_drift`
- `worker_affinity_or_parallelism_drift`
- `generation_cache_namespace_drift`
- `raw_answer_object_hash_drift`
- `response_envelope_mapping_drift`
- `eval_client_parse_drift`
- `parity_runtime_error`

Zorunlu first-break eslemesi:

- `L0` -> `raw_generation_nondeterminism`
- `L2` -> `process_reinit_dependency`
- `L3` -> `shared_runner_state_bleed`
- `L4` -> `post_payload_release_control_bleed`
- `L5` -> `request_order_accumulation_drift`
- `L6` -> `worker_affinity_or_parallelism_drift`
- `L7` -> `generation_cache_namespace_drift`
- runtime error -> `parity_runtime_error`

Ek kurallar:

- `unexplained` kayit birakilmaz
- `response_envelope_mapping_drift` ve `eval_client_parse_drift` yalniz stage-first-break bu katmanlarda ise atanir
- `raw_answer_object_hash_drift`, upstream generation stage'leri esit kalip drift `raw_answer_object` katmaninda kalirsa kullanilir
