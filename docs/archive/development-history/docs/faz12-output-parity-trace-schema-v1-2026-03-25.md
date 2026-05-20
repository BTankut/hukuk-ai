# FAZ12 Output Parity Trace Schema v1

Tarih: 2026-03-25

Bu schema FAZ12 output parity builder'larinin per-record zorunlu alanlarini tanimlar.

## Zorunlu Alanlar

- `family_id`
- `question_id`
- `ordinal_index`
- `reference_candidate_pair`
- `reference_first_run_authoritative`
- `candidate_first_run_authoritative`
- `reference_runtime_error`
- `candidate_runtime_error`
- `reference_error_rerun_used`
- `candidate_error_rerun_used`
- `preprojection_hash`
- `cited_projection_hash`
- `citation_set_projection_hash`
- `final_mode_mapping_hash`
- `final_answer_payload_hash`
- `response_envelope_hash`
- `serialized_output_hash`
- `answer_body_hash`
- `citation_body_hash`
- `refusal_mode`
- `refusal_body_hash`
- `blocked_reason_set`
- `first_divergence_stage`
- `primary_reason`

## Surface Ladder

- `P0 = preprojection_hash`
- `P1 = cited_projection_hash`
- `P2 = citation_set_projection_hash`
- `P3 = final_mode_mapping_hash`
- `P4 = final_answer_payload_hash`
- `P5 = response_envelope_hash`
- `P6 = serialized_output_hash`

`P0` anchor alanidir. FAZ12 icinde tamir yuzeyi degildir.
