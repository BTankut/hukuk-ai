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
- `first_divergence_stage`
- `primary_reason`

Not:

- candidate-effective view aynı row içinde tutulur.
- referans tarafı `reference_*` alanları ile aynı row içinde taşınır.
- targeted ve full-family gate yalnız authoritative effective view üzerinden hesaplanır.
