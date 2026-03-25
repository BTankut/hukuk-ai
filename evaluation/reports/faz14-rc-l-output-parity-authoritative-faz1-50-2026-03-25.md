# FAZ14 RC-L Output Parity Authoritative faz1-50

- run_id = `faz14-rc-l-faz1-50-authoritative`
- family_id = `faz1-50`
- question_count = `50`
- mismatch_count = `29`
- runtime_error_count = `0`
- changed_field_outside_contract_count = `101`
- family_metric_delta_zero = `false`
- output_parity_repair_cleared = `false`

## Mismatch Counts

- `normalized_request_hash_mismatch_count` = `0`
- `model_request_payload_hash_mismatch_count` = `28`
- `generation_contract_hash_mismatch_count` = `28`
- `preprojection_anchor_mismatch_count` = `15`
- `cited_projection_hash_mismatch_count` = `4`
- `citation_set_projection_hash_mismatch_count` = `5`
- `final_mode_mapping_hash_mismatch_count` = `17`
- `blocked_reason_set_mismatch_count` = `17`
- `final_answer_payload_hash_mismatch_count` = `9`
- `response_envelope_hash_mismatch_count` = `23`
- `serialized_output_hash_mismatch_count` = `9`
- `answer_body_hash_mismatch_count` = `8`
- `citation_body_hash_mismatch_count` = `4`
- `refusal_body_hash_mismatch_count` = `0`

## Diff Containment

- `allowed_changed_field_set` = `['answer_body_hash', 'blocked_reason_set_hash', 'citation_body_hash', 'citation_set_projection_hash', 'cited_projection_hash', 'final_answer_payload_hash', 'final_mode_mapping_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash', 'serialized_output_hash']`
- `changed_field_outside_contract_count` = `101`

## Metric Delta

- `citation_delta` = `0.0`
- `correct_source_delta` = `-0.03`
- `hallucination_delta` = `0.02`
- `refusal_delta` = `0.0`
- `error_delta` = `0.0`

## Frontier Sample

- `TBK-003` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'generation_contract_hash', 'model_request_payload_hash', 'response_envelope_hash']`
- `TBK-005` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash']`
- `TBK-006` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash']`
- `TBK-007` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'generation_contract_hash', 'model_request_payload_hash', 'response_envelope_hash']`
- `TBK-008` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'generation_contract_hash', 'model_request_payload_hash', 'response_envelope_hash']`
- `TBK-009` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash']`
- `TBK-011` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash']`
- `TBK-013` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash']`
- `TBK-014` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['answer_body_hash', 'final_answer_payload_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash', 'serialized_output_hash']`
- `TBK-016` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'generation_contract_hash', 'model_request_payload_hash', 'response_envelope_hash']`
- `TBK-017` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['generation_contract_hash', 'model_request_payload_hash']`
- `TBK-020` stage `final_mode_mapping_hash` reason `final_mode_mapping_delta` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'response_envelope_hash']`
- `TBK-022` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['generation_contract_hash', 'model_request_payload_hash']`
- `TBK-023` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['answer_body_hash', 'final_answer_payload_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash', 'serialized_output_hash']`
- `TBK-024` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['answer_body_hash', 'final_answer_payload_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash', 'serialized_output_hash']`
- `TBK-027` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['generation_contract_hash', 'model_request_payload_hash']`
- `TBK-028` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['answer_body_hash', 'final_answer_payload_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash', 'serialized_output_hash']`
- `TBK-029` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'generation_contract_hash', 'model_request_payload_hash', 'response_envelope_hash']`
- `TBK-030` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['generation_contract_hash', 'model_request_payload_hash']`
- `TBK-033` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['answer_body_hash', 'citation_body_hash', 'citation_set_projection_hash', 'cited_projection_hash', 'final_answer_payload_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash', 'serialized_output_hash']`
