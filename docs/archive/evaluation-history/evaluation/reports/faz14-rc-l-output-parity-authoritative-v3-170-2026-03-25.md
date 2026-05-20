# FAZ14 RC-L Output Parity Authoritative v3-170

- run_id = `faz14-rc-l-v3-170-authoritative`
- family_id = `v3-170`
- question_count = `170`
- mismatch_count = `112`
- runtime_error_count = `0`
- changed_field_outside_contract_count = `483`
- family_metric_delta_zero = `false`
- output_parity_repair_cleared = `false`

## Mismatch Counts

- `normalized_request_hash_mismatch_count` = `0`
- `model_request_payload_hash_mismatch_count` = `112`
- `generation_contract_hash_mismatch_count` = `112`
- `preprojection_anchor_mismatch_count` = `90`
- `cited_projection_hash_mismatch_count` = `22`
- `citation_set_projection_hash_mismatch_count` = `15`
- `final_mode_mapping_hash_mismatch_count` = `45`
- `blocked_reason_set_mismatch_count` = `41`
- `final_answer_payload_hash_mismatch_count` = `55`
- `response_envelope_hash_mismatch_count` = `89`
- `serialized_output_hash_mismatch_count` = `55`
- `answer_body_hash_mismatch_count` = `55`
- `citation_body_hash_mismatch_count` = `22`
- `refusal_body_hash_mismatch_count` = `0`

## Diff Containment

- `allowed_changed_field_set` = `['answer_body_hash', 'blocked_reason_set_hash', 'citation_body_hash', 'citation_set_projection_hash', 'cited_projection_hash', 'final_answer_payload_hash', 'final_mode_mapping_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash', 'serialized_output_hash']`
- `changed_field_outside_contract_count` = `483`

## Metric Delta

- `citation_delta` = `0.0`
- `correct_source_delta` = `-0.0025488235`
- `hallucination_delta` = `0.0`
- `refusal_delta` = `-0.0058823529`
- `error_delta` = `0.0`

## Frontier Sample

- `TBK-051` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash']`
- `TBK-052` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['answer_body_hash', 'final_answer_payload_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash', 'serialized_output_hash']`
- `TBK-053` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['generation_contract_hash', 'model_request_payload_hash']`
- `TBK-054` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash']`
- `TBK-055` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['answer_body_hash', 'citation_body_hash', 'citation_set_projection_hash', 'cited_projection_hash', 'final_answer_payload_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash', 'serialized_output_hash']`
- `TBK-056` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['answer_body_hash', 'final_answer_payload_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash', 'serialized_output_hash']`
- `TBK-057` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash']`
- `TBK-058` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['answer_body_hash', 'citation_body_hash', 'citation_set_projection_hash', 'cited_projection_hash', 'final_answer_payload_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash', 'serialized_output_hash']`
- `TBK-059` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['answer_body_hash', 'citation_body_hash', 'cited_projection_hash', 'final_answer_payload_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash', 'serialized_output_hash']`
- `TBK-060` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['answer_body_hash', 'citation_body_hash', 'cited_projection_hash', 'final_answer_payload_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash', 'serialized_output_hash']`
- `TBK-061` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'generation_contract_hash', 'model_request_payload_hash', 'response_envelope_hash']`
- `TBK-062` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['answer_body_hash', 'blocked_reason_set_hash', 'citation_body_hash', 'citation_set_projection_hash', 'cited_projection_hash', 'final_answer_payload_hash', 'final_mode_mapping_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash', 'serialized_output_hash']`
- `TBK-063` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash']`
- `TBK-064` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash']`
- `TBK-065` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['answer_body_hash', 'final_answer_payload_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash', 'serialized_output_hash']`
- `TBK-066` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['answer_body_hash', 'final_answer_payload_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash', 'serialized_output_hash']`
- `TBK-067` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['generation_contract_hash', 'model_request_payload_hash']`
- `TBK-068` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['answer_body_hash', 'final_answer_payload_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash', 'serialized_output_hash']`
- `TBK-069` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['answer_body_hash', 'final_answer_payload_hash', 'generation_contract_hash', 'model_request_payload_hash', 'preprojection_anchor_hash', 'response_envelope_hash', 'serialized_output_hash']`
- `TBK-070` stage `model_request_payload_hash` reason `repair_surface_breach` changed `['generation_contract_hash', 'model_request_payload_hash']`
