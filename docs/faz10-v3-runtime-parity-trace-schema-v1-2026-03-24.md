# FAZ10 V3 Runtime Parity Trace Schema v1

Tarih: 2026-03-24

Hash kurali:

- canonical JSON serialization
- UTF-8
- SHA-256

Zorunlu stage zinciri:

1. `normalized_request`
2. `model_request_payload`
3. `generation_contract`
4. `worker_assignment_tuple`
5. `session_namespace_after_payload_freeze`
6. `cache_namespace_or_cache_key`
7. `generation_start_ordinal`
8. `first_token_id_hash`
9. `raw_token_stream_hash`
10. `raw_answer_object`
11. `response_envelope`
12. `eval_client_parsed_object`
13. `normalized_parity_object`

Her stage payload'i:

- `stage`
- `hash`
- `payload`

Top-level alanlar:

- `schema_version = faz10-v3-runtime-parity-trace-schema-v1`
- `topology_label`
- `stages`
- `preprojection_hash`
- `normalized_parity_hash`

Not:

- `preprojection_hash`, `raw_answer_object` stage hash'ine esitlenir.
- `first_token_id_hash` ve `raw_token_stream_hash`, raw generation text'inin tokenizer-backed deterministic temsilinden uretilir.
