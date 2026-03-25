# FAZ14 Authoritative Output Repair Schema v1

Tarih: 2026-03-25

Zorunlu alanlar:

- `run_id`
- `family_id`
- `question_id`
- `ordinal_index`
- `candidate_id`
- `lane_id`
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
- `answer_body_hash`
- `citation_body_hash`
- `refusal_body_hash`
- `changed_field_set`
- `changed_field_outside_contract`

Not:

- authoritative row candidate-effective view yuzeyini tasir.
- reference tarafi ayni row icinde `reference_*` prefiksi ile saklanir.
- `changed_field_set` yalniz `RC-J -> RC-L` containment kontrolu icin kullanilir.
