# FAZ19 Current Authority Stage Ladder Contract v1

Lokalizasyon yalnız bu O-ladder üzerinde yapılır:

- `O0 = normalized_request_hash`
- `O1 = model_request_payload_hash`
- `O2 = generation_contract_hash`
- `O3 = preprojection_anchor_hash`
- `O4 = cited_projection_hash`
- `O5 = citation_set_projection_hash`
- `O6 = final_mode_mapping_hash`
- `O7 = blocked_reason_set_hash`
- `O8 = final_answer_payload_hash`
- `O9 = response_envelope_hash`
- `O10 = serialized_output_hash`

Contract breach sayılan yüzey:
- `O0` ile `O5` arası herhangi bir drift
- herhangi bir family’de `family_metric_delta_zero = false`
