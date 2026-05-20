# FAZ8 Output Parity Taxonomy v1

Tarih: 2026-03-24

## First Divergence Stage

- `raw_input_request`
- `normalized_request`
- `auth_session_trace_enriched_request`
- `pre_answer_handler_payload`
- `raw_answer_object`
- `visible_response_projection`
- `api_response_envelope`
- `eval_client_parsed_object`
- `normalized_parity_object`

## Primary Reason

- `request_shape_drift`
- `auth_context_injection_drift`
- `session_context_injection_drift`
- `raw_answer_hash_mismatch`
- `response_projection_omission`
- `citation_projection_order_or_drop`
- `source_projection_order_or_drop`
- `canonical_norm_projection_drop`
- `refusal_body_projection_drift`
- `final_mode_projection_drift`
- `api_envelope_mapping_drift`
- `eval_client_parse_drift`
- `parity_runtime_error`

## Kural

- her frontier kaydina tam bir `first_divergence_stage` atanir
- her frontier kaydina tam bir `primary_reason` atanir
- `unexplained_count = 0`
