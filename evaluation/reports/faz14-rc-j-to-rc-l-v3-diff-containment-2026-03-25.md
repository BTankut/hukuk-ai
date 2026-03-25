# FAZ14 RC-J to RC-L V3 Diff Containment

- run_id = `faz14-rc-j-to-rc-l-v3-170-diff-t180`
- family_id = `v3-170`
- question_count = `6`
- mismatch_count = `6`
- runtime_error_count = `0`
- changed_field_outside_contract_count = `0`
- family_metric_delta_zero = `true`
- output_parity_repair_cleared = `false`

## Mismatch Counts

- `normalized_request_hash_mismatch_count` = `0`
- `model_request_payload_hash_mismatch_count` = `0`
- `generation_contract_hash_mismatch_count` = `0`
- `preprojection_anchor_mismatch_count` = `0`
- `cited_projection_hash_mismatch_count` = `0`
- `citation_set_projection_hash_mismatch_count` = `0`
- `final_mode_mapping_hash_mismatch_count` = `6`
- `blocked_reason_set_mismatch_count` = `6`
- `final_answer_payload_hash_mismatch_count` = `0`
- `response_envelope_hash_mismatch_count` = `6`
- `serialized_output_hash_mismatch_count` = `0`
- `answer_body_hash_mismatch_count` = `0`
- `citation_body_hash_mismatch_count` = `0`
- `refusal_body_hash_mismatch_count` = `0`

## Diff Containment

- `allowed_changed_field_set` = `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'response_envelope_hash']`
- `changed_field_outside_contract_count` = `0`

## Metric Delta

- `citation_delta` = `0.0`
- `correct_source_delta` = `0.0`
- `hallucination_delta` = `0.0`
- `refusal_delta` = `0.0`
- `error_delta` = `0.0`

## Frontier Sample

- `TBK-051` stage `final_mode_mapping_hash` reason `final_mode_mapping_delta` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'response_envelope_hash']`
- `TBK-054` stage `final_mode_mapping_hash` reason `final_mode_mapping_delta` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'response_envelope_hash']`
- `TBK-055` stage `final_mode_mapping_hash` reason `final_mode_mapping_delta` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'response_envelope_hash']`
- `TBK-057` stage `final_mode_mapping_hash` reason `final_mode_mapping_delta` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'response_envelope_hash']`
- `TBK-058` stage `final_mode_mapping_hash` reason `final_mode_mapping_delta` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'response_envelope_hash']`
- `TBK-061` stage `final_mode_mapping_hash` reason `final_mode_mapping_delta` changed `['blocked_reason_set_hash', 'final_mode_mapping_hash', 'response_envelope_hash']`
