# FAZ19 Current Authority Equivalence Contract v1

`capture_a` ile `capture_b` arasında aynı family, aynı candidate ve aynı ordinal için eşit olması zorunlu alanlar:

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

Gate:
- bu alanlardan herhangi biri drift ederse `capture_stability_match = false`
