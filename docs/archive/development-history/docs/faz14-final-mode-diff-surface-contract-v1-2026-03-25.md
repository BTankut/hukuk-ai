# FAZ14 Final-Mode Diff Surface Contract v1

Tarih: 2026-03-25

Degisebilir alanlar:

- `final_mode_mapping_hash`
- `blocked_reason_set_hash`
- `response_envelope_hash`
- `serialized_output_hash`

Degismemesi zorunlu alanlar:

- `normalized_request_hash`
- `model_request_payload_hash`
- `generation_contract_hash`
- `preprojection_anchor_hash`
- `cited_projection_hash`
- `citation_set_projection_hash`
- `final_answer_payload_hash`
- `answer_body_hash`
- `citation_body_hash`
- `refusal_body_hash`

Kural:

- izinli alanlar disinda herhangi bir diff `repair_surface_breach` sayilir.
