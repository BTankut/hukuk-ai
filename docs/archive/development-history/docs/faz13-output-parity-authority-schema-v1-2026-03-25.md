# FAZ13 Output Parity Authority Schema v1

Tarih: 2026-03-25

Zorunlu alanlar:

- `run_id`
- `family_id`
- `question_id`
- `ordinal_index`
- `candidate_id`
- `lane_id`
- `worker_id`
- `process_id`
- `session_namespace`
- `cache_namespace`
- `first_run_authoritative`
- `runtime_error`
- `error_type`
- `error_rerun_used`
- `effective_view_member`
- `normalized_request_hash`
- `model_request_payload_hash`
- `generation_contract_hash`
- `preprojection_anchor_hash`
- `cited_projection_hash`
- `citation_set_projection_hash`
- `final_mode_mapping_hash`
- `blocked_reason_set_hash`
- `final_answer_payload_hash`
- `response_envelope_hash`
- `serialized_output_hash`
- `refusal_mode`
- `refusal_body_hash`
- `answer_body_hash`
- `citation_body_hash`

Not:

- authoritative row, candidate-effective view yüzeyini taşır.
- reference tarafı aynı row içinde `reference_*` prefiksi ile saklanır.
- `effective_view_member = 1` olan satırlar gate hesabına girer.
